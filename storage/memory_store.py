"""
인메모리 저장소
빈번하게 접근하는 상태 정보를 메모리에 캐시한다.
"""
import time
from typing import Any, Optional
from utils.logger import log


class MemoryStore:
    """
    키-값 인메모리 저장소.
    TTL(Time-To-Live) 지원으로 오래된 데이터 자동 만료.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        값 저장.
        ttl: 초 단위 만료 시간 (None이면 영구)
        """
        self._store[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl if ttl else None,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """값 조회. 만료된 항목은 삭제 후 default 반환."""
        entry = self._store.get(key)
        if entry is None:
            return default

        if entry["expires_at"] and time.time() > entry["expires_at"]:
            del self._store[key]
            return default

        return entry["value"]

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def cleanup_expired(self):
        """만료된 항목 일괄 정리"""
        now = time.time()
        expired = [
            k for k, v in self._store.items()
            if v["expires_at"] and now > v["expires_at"]
        ]
        for k in expired:
            del self._store[k]
        if expired:
            log.debug(f"만료 항목 {len(expired)}개 정리")

    @property
    def size(self) -> int:
        return len(self._store)
