"""
상태 머신 모듈
JARVIS의 전체 동작 상태를 관리한다.

상태 정의:
  IDLE            - 상시 대기. 박수/웨이크워드 감지만 수행
  LISTENING       - 사용자 음성 명령 수신 중
  THINKING        - 명령 해석 및 작업 실행 중
  SPEAKING        - 응답 음성 출력 중
  CONVERSATION    - 연속 대화 모드. 후속 질문 대기
  SUSPENDED       - 음성 세션 중지 (박수 2회)

전이 규칙:
  IDLE → LISTENING          : 박수 1회 또는 웨이크워드
  LISTENING → THINKING      : 명령 수신 완료
  THINKING → SPEAKING       : 응답 생성 완료
  SPEAKING → CONVERSATION   : 응답 완료, 후속 대화 대기
  CONVERSATION → LISTENING  : 후속 발화 감지
  CONVERSATION → IDLE       : 타임아웃 (무응답)
  * → SUSPENDED             : 박수 2회
  SUSPENDED → IDLE          : 종료 처리 완료
  * → IDLE                  : 박수 3회 (긴급 정지)
"""
import enum
import threading
import time
from typing import Callable, Optional
from utils.logger import log


class State(enum.Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    CONVERSATION = "CONVERSATION"
    SUSPENDED = "SUSPENDED"


# 허용되는 상태 전이 정의
_VALID_TRANSITIONS = {
    State.IDLE: {State.LISTENING},
    State.LISTENING: {State.THINKING, State.IDLE, State.SUSPENDED},
    State.THINKING: {State.SPEAKING, State.IDLE, State.SUSPENDED},
    State.SPEAKING: {State.CONVERSATION, State.IDLE, State.SUSPENDED},
    State.CONVERSATION: {State.LISTENING, State.IDLE, State.SUSPENDED},
    State.SUSPENDED: {State.IDLE},
}


class StateMachine:
    """
    JARVIS 상태 머신.
    스레드 안전하게 상태 전이를 관리한다.
    """

    def __init__(self):
        self._state = State.IDLE
        self._lock = threading.RLock()
        self._listeners: list[Callable[[State, State], None]] = []
        self._state_enter_time = time.time()

    @property
    def state(self) -> State:
        with self._lock:
            return self._state

    @property
    def time_in_state(self) -> float:
        """현재 상태에 머문 시간(초)"""
        with self._lock:
            return time.time() - self._state_enter_time

    def add_listener(self, callback: Callable[[State, State], None]):
        """상태 변경 리스너 등록. callback(old_state, new_state)"""
        self._listeners.append(callback)

    def transition(self, new_state: State, force: bool = False) -> bool:
        """
        상태를 전이한다.
        force=True이면 유효성 검사 없이 전이 (긴급 정지용).
        Returns: 전이 성공 여부
        """
        with self._lock:
            old_state = self._state

            if old_state == new_state:
                return True

            if not force and new_state not in _VALID_TRANSITIONS.get(old_state, set()):
                log.warning(
                    f"잘못된 상태 전이: {old_state.value} → {new_state.value}"
                )
                return False

            self._state = new_state
            self._state_enter_time = time.time()
            log.info(f"상태 전이: {old_state.value} → {new_state.value}")

        # 리스너 호출은 lock 밖에서
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                log.error(f"상태 리스너 오류: {e}")

        return True

    def force_idle(self):
        """긴급 정지: 어떤 상태에서든 IDLE로 강제 전이"""
        self.transition(State.IDLE, force=True)

    def is_active(self) -> bool:
        """대화 세션이 활성 상태인지 여부"""
        return self.state in (
            State.LISTENING,
            State.THINKING,
            State.SPEAKING,
            State.CONVERSATION,
        )

    def is_idle(self) -> bool:
        return self.state == State.IDLE

    def __repr__(self):
        return f"StateMachine(state={self._state.value})"
