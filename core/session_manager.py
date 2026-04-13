"""
세션 관리자 모듈
음성 대화 세션의 수명주기를 관리한다.
- 세션 시작/종료
- 대화 모드 타임아웃
- 연속 대화 유지
"""
import threading
import time
from typing import Callable, Optional
from core.state_machine import StateMachine, State
from config.settings import CONVERSATION_TIMEOUT, LISTENING_TIMEOUT
from utils.logger import log


class SessionManager:
    """
    음성 대화 세션을 관리한다.
    - 박수/웨이크워드로 세션 시작
    - 응답 후 CONVERSATION_TIMEOUT 동안 후속 발화 대기
    - 타임아웃 시 자동으로 IDLE 복귀
    """

    def __init__(self, state_machine: StateMachine):
        self.sm = state_machine
        self._conversation_timer: Optional[threading.Timer] = None
        self._session_start_time: Optional[float] = None
        self._total_sessions = 0

    def start_session(self):
        """새 대화 세션을 시작한다."""
        self._cancel_timer()
        self._session_start_time = time.time()
        self._total_sessions += 1
        log.info(f"세션 시작 (#{self._total_sessions})")

        if self.sm.state == State.IDLE:
            self.sm.transition(State.LISTENING)

    def end_session(self, reason: str = "manual"):
        """대화 세션을 종료한다."""
        self._cancel_timer()
        duration = 0.0
        if self._session_start_time:
            duration = time.time() - self._session_start_time
            self._session_start_time = None

        log.info(f"세션 종료 (사유: {reason}, 지속: {duration:.1f}초)")

        if self.sm.state != State.IDLE:
            self.sm.transition(State.SUSPENDED, force=True)
            self.sm.transition(State.IDLE)

    def suspend_session(self):
        """세션을 일시 중단한다 (박수 2회)."""
        self._cancel_timer()
        log.info("세션 일시 중단")

        if self.sm.is_active():
            self.sm.transition(State.SUSPENDED, force=True)
            self.sm.transition(State.IDLE)

    def on_response_complete(self):
        """
        응답이 완료되면 호출.
        CONVERSATION 모드로 전환하고 타임아웃 타이머를 시작한다.
        """
        if self.sm.state == State.SPEAKING:
            self.sm.transition(State.CONVERSATION)
            self._start_conversation_timer()

    def on_followup_detected(self):
        """후속 발화가 감지되면 호출. 타이머를 취소하고 LISTENING으로."""
        self._cancel_timer()
        if self.sm.state == State.CONVERSATION:
            self.sm.transition(State.LISTENING)

    def _start_conversation_timer(self):
        """대화 모드 타임아웃 타이머 시작"""
        self._cancel_timer()
        self._conversation_timer = threading.Timer(
            CONVERSATION_TIMEOUT,
            self._on_conversation_timeout
        )
        self._conversation_timer.daemon = True
        self._conversation_timer.start()
        log.debug(f"대화 타임아웃 타이머 시작 ({CONVERSATION_TIMEOUT}초)")

    def _on_conversation_timeout(self):
        """대화 모드 타임아웃 발생"""
        if self.sm.state == State.CONVERSATION:
            log.info("대화 타임아웃 - IDLE 복귀")
            self.sm.transition(State.IDLE)
            self._session_start_time = None

    def _cancel_timer(self):
        """활성 타이머 취소"""
        if self._conversation_timer and self._conversation_timer.is_alive():
            self._conversation_timer.cancel()
        self._conversation_timer = None

    @property
    def session_duration(self) -> float:
        """현재 세션 지속 시간(초)"""
        if self._session_start_time:
            return time.time() - self._session_start_time
        return 0.0

    @property
    def is_in_session(self) -> bool:
        return self._session_start_time is not None
