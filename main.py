"""
JARVIS - AI 음성 비서 메인 실행 파일
24시간 상시 대기형 데스크톱 음성 비서.

상태 머신 기반 제어:
  IDLE         → 박수 1회 / 웨이크워드  → LISTENING
  LISTENING    → 명령 수신 완료          → THINKING
  THINKING     → 응답 생성 완료          → SPEAKING
  SPEAKING     → 응답 완료              → CONVERSATION
  CONVERSATION → 후속 발화 / 타임아웃    → LISTENING / IDLE
  *            → 박수 2회               → SUSPENDED → IDLE
  *            → 박수 3회               → IDLE (긴급 정지)

실행: python main.py
"""
import threading
import time
import sys
import os
import signal

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel

from core.state_machine import StateMachine, State
from core.session_manager import SessionManager
from core.conversation_manager import ConversationManager
from core.interrupt_handler import InterruptHandler
from core.tts import TTS
from core.stt import STT
from core.brain import Brain
from core.wake_word import WakeWordDetector
from core.clap_detector import ClapDetector
from core.watchdog import Watchdog
from skills.briefing_skill import get_full_briefing_with_github, get_morning_briefing_prompt
from skills.gmail_skill import get_gmail_prompt
from skills.calendar_skill import get_calendar_prompt
from skills.github_skill import GitHubSkill
from skills.system_skill import SystemSkill
from skills.productivity_skill import ProductivitySkill
from skills.mail_reply_skill import MailReplySkill
from services.email_service import EmailService
from ui.overlay import StatusOverlay
from ui.sounds import ensure_sounds_exist
from config.settings import WAKE_WORD, CONVERSATION_TIMEOUT
from config.audio_config import ACTIVATION_SOUND, DEACTIVATION_SOUND, ERROR_SOUND
from utils.logger import log

console = Console()


class Jarvis:
    """JARVIS 메인 컨트롤러"""

    def __init__(self):
        # 효과음 생성
        ensure_sounds_exist()

        # 상태 머신 & 세션
        self.sm = StateMachine()
        self.conversation = ConversationManager()
        self.session = SessionManager(self.sm)

        # 코어 모듈
        self.tts = TTS()
        self.stt = STT()
        self.brain = Brain(conversation_manager=self.conversation)
        self.interrupt_handler = InterruptHandler()

        # 스킬 & 서비스
        self.github = GitHubSkill()
        self.system_skill = SystemSkill()
        self.productivity = ProductivitySkill()
        self.email_service = EmailService()
        self.mail_reply = MailReplySkill(self.email_service)

        # UI
        self.overlay = StatusOverlay()
        self.sm.add_listener(self.overlay.update_state)

        # 워치독
        self.watchdog = Watchdog(health_check=self._health_check)
        self.watchdog.set_failure_handler(self._on_watchdog_failure)

        # 입력 감지기 (나중에 start에서 초기화)
        self.wake_detector = None
        self.clap_detector = None

        # 프로젝트 루트 (효과음 경로용)
        self._root = os.path.dirname(os.path.abspath(__file__))

    # ─── 이벤트 핸들러 ───

    def on_single_clap(self):
        """박수 1회 → 활성화"""
        if self.sm.state == State.IDLE:
            self._activate()
        elif self.sm.state == State.CONVERSATION:
            # 대화 모드에서 박수 1회 → 후속 발화로 간주
            self.session.on_followup_detected()
            self._listen_and_process()

    def on_double_clap(self):
        """박수 2회 → 대화 종료"""
        if self.sm.is_active():
            self.tts.interrupt()
            self._play_sound(DEACTIVATION_SOUND)
            self.session.suspend_session()
            self.tts.speak("음성 대기 모드를 종료합니다.")

    def on_triple_clap(self):
        """박수 3회 → 긴급 정지"""
        self.tts.interrupt()
        self.sm.force_idle()
        self.session.end_session("emergency")
        self._play_sound(ERROR_SOUND)
        log.warning("긴급 정지 실행")

    def on_wake_word(self, trigger_text: str = ""):
        """웨이크워드 감지"""
        if self.sm.state == State.IDLE:
            self._activate()
        elif self.sm.state == State.CONVERSATION:
            self.session.on_followup_detected()
            self._listen_and_process()

    # ─── 핵심 로직 ───

    def _activate(self):
        """음성 세션 활성화"""
        self._play_sound(ACTIVATION_SOUND)
        self.session.start_session()
        self.conversation.start_new_session()

        # 웨이크워드 감지 일시 중지
        if self.wake_detector:
            self.wake_detector.enabled = False

        self.tts.speak("네, 형님.")
        # TTS 종료 후 마이크 안정화 대기
        time.sleep(0.3)
        self._listen_and_process()

    def _listen_and_process(self):
        """음성을 듣고 처리하는 핵심 루프"""
        if self.sm.state not in (State.LISTENING, State.CONVERSATION):
            if not self.sm.transition(State.LISTENING):
                self._return_to_idle()
                return

        # 음성 인식 (최대 10초, 최소 2.5초 녹음 보장)
        command = self.stt.listen(duration=10.0)

        if not command:
            if self.session.is_in_session and self.sm.state == State.LISTENING:
                # 첫 명령에서 인식 실패
                self.tts.speak("명령을 인식하지 못했습니다.")
                self._return_to_idle()
            return

        # 명령 처리
        if not self.sm.transition(State.THINKING):
            self._return_to_idle()
            return

        response = self.handle_command(command)

        if response:
            if not self.sm.transition(State.SPEAKING):
                self._return_to_idle()
                return

            # 인터럽트 모니터링 시작
            self.interrupt_handler.start_monitoring(
                on_interrupt=self._on_speech_interrupted
            )

            self.tts.speak(response, on_complete=self._on_speech_complete)

            self.interrupt_handler.stop_monitoring()
        else:
            self._return_to_idle()

    def _on_speech_complete(self):
        """음성 출력 완료 후 호출"""
        if self.sm.state == State.SPEAKING:
            self.session.on_response_complete()

            # CONVERSATION 모드 진입 시 웨이크워드 재활성화
            if self.wake_detector:
                self.wake_detector.enabled = True

            # 대화 모드에서 후속 발화 타이머 만료 대기
            # SessionManager가 타임아웃 시 자동으로 IDLE 전이

    def _on_speech_interrupted(self):
        """음성 출력 중 인터럽트"""
        self.tts.interrupt()
        log.info("사용자 인터럽트 - 음성 중단 후 재청취")
        if self.sm.state in (State.SPEAKING, State.CONVERSATION):
            self.sm.transition(State.LISTENING, force=True)
            self._listen_and_process()

    def _return_to_idle(self):
        """IDLE 상태로 복귀"""
        self.sm.force_idle()
        if self.wake_detector:
            self.wake_detector.enabled = True

    # ─── 명령 라우팅 ───

    def handle_command(self, text: str) -> str:
        """음성 명령을 분석하고 적절한 스킬로 라우팅"""
        text_lower = text.lower()

        # 종료 명령
        if any(w in text_lower for w in ["종료", "꺼줘", "그만", "잘자"]):
            self.tts.speak("알겠습니다. 종료합니다, 형님.")
            time.sleep(2)
            self.shutdown()
            return ""

        # 메일 답장 워크플로 중이라면
        if self.mail_reply.is_replying:
            if "보내" in text_lower or "전송" in text_lower:
                return self.mail_reply.send_draft()
            elif "취소" in text_lower or "그만" in text_lower:
                self.mail_reply.cancel_reply()
                return "답장을 취소했습니다."
            elif "다시" in text_lower:
                return "답장할 내용을 다시 말씀해주세요."
            elif self.mail_reply.has_draft:
                return self.mail_reply.set_draft(text)
            else:
                return self.mail_reply.set_draft(text)

        # 모닝 브리핑
        if any(w in text_lower for w in ["모닝", "브리핑", "전체", "총괄"]):
            self.tts.speak("네, 모닝 브리핑 시작합니다.")
            prompt, github_text = get_full_briefing_with_github(self.github)
            response = self.brain.process(prompt, use_mcp=True)
            if "없습니다" not in github_text:
                response += " " + github_text
            return response

        # Gmail
        if any(w in text_lower for w in ["메일", "이메일", "메시지", "받은"]):
            if "답장" in text_lower:
                # 메일 답장 시작
                if self.email_service.is_configured:
                    summary = self.mail_reply.fetch_and_summarize()
                    return summary + " 몇 번째 메일에 답장할까요?"
                else:
                    prompt = get_gmail_prompt(text)
                    return self.brain.process(prompt, use_mcp=True)
            prompt = get_gmail_prompt(text)
            return self.brain.process(prompt, use_mcp=True)

        # 캘린더
        if any(w in text_lower for w in ["일정", "스케줄", "캘린더", "약속"]):
            prompt = get_calendar_prompt(text)
            return self.brain.process(prompt, use_mcp=True)

        # GitHub
        if any(w in text_lower for w in ["깃허브", "github", "pr", "풀 리퀘", "이슈", "커밋"]):
            return self.github.get_briefing()

        # 시스템 제어
        system_result = self.system_skill.handle(text)
        if system_result:
            return system_result

        # 생산성 명령
        prod_result = self.productivity.handle(text)
        if prod_result:
            return prod_result

        # 대화 히스토리 초기화
        if any(w in text_lower for w in ["초기화", "리셋", "새로 시작"]):
            self.brain.clear_history()
            return "대화 히스토리를 초기화했습니다, 형님."

        # 자동 시작 설정
        if "자동 시작" in text_lower or "자동 실행" in text_lower:
            from services.startup_service import StartupService
            startup = StartupService()
            if "해제" in text_lower or "끄" in text_lower:
                return startup.disable_autostart()
            return startup.enable_autostart()

        # 기타 일반 질문 → Claude
        return self.brain.process(text, use_mcp=False)

    # ─── 시스템 관리 ───

    def _health_check(self) -> bool:
        """워치독 헬스 체크"""
        # 상태 머신이 특정 상태에 너무 오래 머물면 비정상
        if self.sm.state in (State.THINKING, State.SPEAKING):
            if self.sm.time_in_state > 120:  # 2분 이상
                log.warning(f"상태 교착 감지: {self.sm.state.value}")
                return False
        return True

    def _on_watchdog_failure(self):
        """워치독 실패 핸들러"""
        log.error("워치독 복구 실행 - 상태 초기화")
        self.tts.interrupt()
        self.sm.force_idle()
        if self.wake_detector:
            self.wake_detector.enabled = True

    def _play_sound(self, sound_name: str):
        """효과음 재생"""
        path = os.path.join(self._root, sound_name)
        self.tts.play_sound(path)

    def shutdown(self):
        """시스템 종료"""
        log.info("JARVIS 종료 중...")
        self.watchdog.stop()
        if self.wake_detector:
            self.wake_detector.stop()
        if self.clap_detector:
            self.clap_detector.stop()
        self.email_service.disconnect()
        sys.exit(0)

    # ─── 시작 ───

    def start(self):
        """JARVIS 시작"""
        console.print(Panel.fit(
            "[bold cyan]J.A.R.V.I.S[/bold cyan]\n"
            "[dim]Just A Rather Very Intelligent System[/dim]\n"
            "[dim]24시간 상시 대기형 AI 음성 비서[/dim]\n\n"
            f"[yellow]'{WAKE_WORD}'[/yellow] 라고 말하거나 "
            "[yellow]박수 한 번[/yellow]으로 활성화\n"
            "[yellow]박수 두 번[/yellow]으로 대화 종료\n"
            "[yellow]박수 세 번[/yellow]으로 긴급 정지\n\n"
            "[dim]종료: '자비스, 종료해줘'[/dim]",
            border_style="cyan",
        ))

        # SIGINT/SIGTERM 핸들링
        def signal_handler(sig, frame):
            self.tts.speak("자비스를 종료합니다. 수고하셨습니다, 형님.")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 워치독 시작
        self.watchdog.start()

        # 시작 인사
        self.tts.speak("자비스 온라인. 대기 중입니다, 형님.")

        # 박수 감지기 시작 (별도 스레드)
        self.clap_detector = ClapDetector(
            on_single_clap=self.on_single_clap,
            on_double_clap=self.on_double_clap,
            on_triple_clap=self.on_triple_clap,
        )
        clap_thread = threading.Thread(target=self.clap_detector.start, daemon=True)
        clap_thread.start()

        # 상태 변경 리스너: CONVERSATION → IDLE 전이 시 웨이크워드 재활성화
        def on_state_change(old: State, new: State):
            if new == State.IDLE and self.wake_detector:
                self.wake_detector.enabled = True
        self.sm.add_listener(on_state_change)

        # 웨이크워드 감지 메인 루프 (블로킹)
        self.wake_detector = WakeWordDetector(callback=self.on_wake_word)

        try:
            self.wake_detector.start()
        except KeyboardInterrupt:
            self.tts.speak("자비스를 종료합니다. 수고하셨습니다, 형님.")
            self.shutdown()


def main():
    # 첫 실행 체크 (data 디렉토리 없으면 설정 마법사 제안)
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        console.print("[yellow]첫 실행이 감지되었습니다.[/yellow]")
        console.print("설정 마법사를 실행하려면: [cyan]python launcher.py[/cyan]\n")
        os.makedirs(data_dir, exist_ok=True)

    jarvis = Jarvis()
    jarvis.start()


if __name__ == "__main__":
    main()
