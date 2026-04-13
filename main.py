"""
JARVIS - AI 음성 비서 메인 실행 파일
실행: python main.py
"""
import threading
import time
import sys
from rich.console import Console
from rich.panel import Panel

from core.tts import TTS
from core.stt import STT
from core.brain import Brain
from core.wake_word import WakeWordDetector
from core.clap_detector import ClapDetector
from skills.briefing_skill import get_full_briefing_with_github, get_morning_briefing_prompt
from skills.gmail_skill import get_gmail_prompt
from skills.calendar_skill import get_calendar_prompt
from skills.github_skill import GitHubSkill
from config import WAKE_WORD
from utils.logger import log

console = Console()

# 전역 컴포넌트 초기화
tts = TTS()
stt = STT()
brain = Brain()
github = GitHubSkill()

is_listening_for_command = False  # 웨이크워드 후 명령 수신 상태


def handle_command(text: str):
    """음성 명령 처리 로직"""
    text = text.lower()

    # 종료 명령
    if any(word in text for word in ["종료", "꺼줘", "그만", "잘자"]):
        tts.speak("알겠습니다. 종료합니다, 형님.")
        time.sleep(2)
        sys.exit(0)

    # 모닝 브리핑
    elif any(word in text for word in ["모닝", "브리핑", "전체", "총괄", "다 알려"]):
        tts.speak("네, 모닝 브리핑 시작합니다.")
        prompt, github_text = get_full_briefing_with_github(github)

        # Claude (Gmail + 캘린더)
        response = brain.process(prompt, use_mcp=True)
        tts.speak(response)

        # GitHub 별도 처리
        if "없습니다" not in github_text:
            tts.speak(github_text)

    # Gmail
    elif any(word in text for word in ["메일", "이메일", "메시지", "받은"]):
        prompt = get_gmail_prompt(text)
        tts.speak("메일 확인 중입니다.")
        response = brain.process(prompt, use_mcp=True)
        tts.speak(response)

    # 캘린더
    elif any(word in text for word in ["일정", "스케줄", "캘린더", "오늘", "약속"]):
        prompt = get_calendar_prompt(text)
        tts.speak("일정 확인 중입니다.")
        response = brain.process(prompt, use_mcp=True)
        tts.speak(response)

    # GitHub
    elif any(word in text for word in ["깃허브", "github", "pr", "풀 리퀘", "이슈", "커밋"]):
        tts.speak("GitHub 확인 중입니다.")
        result = github.get_briefing()
        tts.speak(result)

    # 대화 히스토리 초기화
    elif any(word in text for word in ["초기화", "리셋", "새로 시작"]):
        brain.clear_history()
        tts.speak("대화 히스토리를 초기화했습니다, 형님.")

    # 기타 일반 질문
    else:
        response = brain.process(text, use_mcp=False)
        tts.speak(response)


def on_wake_word_detected(trigger_text: str = ""):
    """웨이크워드 또는 박수 감지 시 호출"""
    global is_listening_for_command

    if is_listening_for_command:
        return

    is_listening_for_command = True

    try:
        tts.speak("네, 형님.")
        command = stt.listen(duration=6.0)

        if command:
            handle_command(command)
        else:
            tts.speak("명령을 인식하지 못했습니다.")
    except Exception as e:
        log.error(f"명령 처리 오류: {e}")
        tts.speak("처리 중 오류가 발생했습니다.")
    finally:
        is_listening_for_command = False


def main():
    console.print(Panel.fit(
        "[bold cyan]J.A.R.V.I.S[/bold cyan]\n"
        "[dim]Just A Rather Very Intelligent System[/dim]\n\n"
        f"[yellow]'{WAKE_WORD}'[/yellow] 라고 말하거나\n"
        "[yellow]박수를 두 번[/yellow] 치면 활성화됩니다\n\n"
        "[dim]종료: '자비스, 종료해줘'[/dim]",
        border_style="cyan"
    ))

    # 시작 인사
    tts.speak("자비스 온라인. 대기 중입니다, 형님.")

    # 박수 감지 스레드 시작
    clap = ClapDetector(callback=on_wake_word_detected)
    clap_thread = threading.Thread(target=clap.start, daemon=True)
    clap_thread.start()
    log.info("박수 감지 활성화")

    # 웨이크워드 감지 메인 루프
    try:
        detector = WakeWordDetector(callback=on_wake_word_detected)
        detector.start()
    except KeyboardInterrupt:
        tts.speak("자비스를 종료합니다. 수고하셨습니다, 형님.")
        log.info("JARVIS 종료")


if __name__ == "__main__":
    main()
