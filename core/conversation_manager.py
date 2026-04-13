"""
대화 관리자 모듈
대화 맥락(컨텍스트)과 히스토리를 관리한다.
"""
import time
from typing import Optional
from config.settings import MAX_CONVERSATION_TURNS
from utils.logger import log


class ConversationManager:
    """
    대화 맥락을 관리한다.
    - 최근 N턴의 대화 히스토리 유지
    - 현재 작업 컨텍스트 추적 (예: 메일 답장 중)
    - 대화 요약 및 초기화
    """

    def __init__(self):
        self._history: list[dict] = []
        self._context: Optional[str] = None
        self._context_data: dict = {}
        self._session_id: int = 0

    def start_new_session(self):
        """새 대화 세션 시작. 히스토리는 유지하되 세션 ID 증가."""
        self._session_id += 1
        self._context = None
        self._context_data = {}
        log.debug(f"새 대화 세션 #{self._session_id}")

    def add_user_message(self, text: str):
        """사용자 메시지 추가"""
        self._history.append({
            "role": "user",
            "content": text,
            "timestamp": time.time(),
            "session_id": self._session_id,
        })
        self._trim_history()

    def add_assistant_message(self, text: str):
        """어시스턴트 응답 추가"""
        self._history.append({
            "role": "assistant",
            "content": text,
            "timestamp": time.time(),
            "session_id": self._session_id,
        })
        self._trim_history()

    def get_messages_for_api(self) -> list[dict]:
        """Claude API 호출용 메시지 리스트 반환"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self._history
        ]

    def set_context(self, context: str, data: Optional[dict] = None):
        """
        현재 작업 컨텍스트 설정.
        예: set_context("mail_reply", {"mail_id": 123, "subject": "..."})
        """
        self._context = context
        self._context_data = data or {}
        log.debug(f"컨텍스트 설정: {context}")

    def clear_context(self):
        """작업 컨텍스트 해제"""
        self._context = None
        self._context_data = {}

    @property
    def context(self) -> Optional[str]:
        return self._context

    @property
    def context_data(self) -> dict:
        return self._context_data

    def clear_history(self):
        """대화 히스토리 전체 초기화"""
        self._history.clear()
        self._context = None
        self._context_data = {}
        log.info("대화 히스토리 초기화")

    def _trim_history(self):
        """히스토리를 최대 턴 수로 제한"""
        max_messages = MAX_CONVERSATION_TURNS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    @property
    def turn_count(self) -> int:
        """현재 세션의 대화 턴 수"""
        return sum(
            1 for msg in self._history
            if msg.get("session_id") == self._session_id and msg["role"] == "user"
        )

    @property
    def last_user_message(self) -> Optional[str]:
        for msg in reversed(self._history):
            if msg["role"] == "user":
                return msg["content"]
        return None

    @property
    def last_assistant_message(self) -> Optional[str]:
        for msg in reversed(self._history):
            if msg["role"] == "assistant":
                return msg["content"]
        return None
