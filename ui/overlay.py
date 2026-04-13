"""
상태 오버레이 모듈
콘솔 기반 상태 표시 (선택적 GUI 오버레이).
현재 상태를 터미널에 실시간으로 표시한다.
"""
import threading
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from core.state_machine import State
from utils.logger import log


# 상태별 표시 설정
_STATE_DISPLAY = {
    State.IDLE: ("대기 중", "dim"),
    State.LISTENING: ("듣는 중...", "bold green"),
    State.THINKING: ("생각 중...", "bold yellow"),
    State.SPEAKING: ("말하는 중...", "bold cyan"),
    State.CONVERSATION: ("대화 모드", "bold blue"),
    State.SUSPENDED: ("일시 중지", "dim red"),
}


class StatusOverlay:
    """
    터미널 기반 상태 표시기.
    현재 JARVIS 상태를 리치 패널로 표시한다.
    """

    def __init__(self):
        self.console = Console()
        self._current_state = State.IDLE
        self._running = False
        self._thread = None

    def update_state(self, old_state: State, new_state: State):
        """상태 변경 시 호출 (StateMachine 리스너)"""
        self._current_state = new_state
        label, style = _STATE_DISPLAY.get(new_state, ("알 수 없음", "dim"))
        self.console.print(f"  [{style}][{label}][/{style}]")

    def show_feedback(self, message: str, style: str = "green"):
        """사용자 피드백 메시지 표시"""
        self.console.print(f"  [{style}]{message}[/{style}]")
