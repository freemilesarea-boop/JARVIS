"""
생산성 스킬
시간, 타이머, 메모 등 일상 생산성 기능.
"""
import time
import threading
from datetime import datetime
from typing import Optional, Callable
from utils.logger import log


class ProductivitySkill:
    """일상 생산성 도우미"""

    def __init__(self):
        self._timer_thread: Optional[threading.Timer] = None
        self._timer_callback: Optional[Callable] = None

    def get_current_time(self) -> str:
        """현재 시각 안내"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        period = "오전" if hour < 12 else "오후"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12

        if minute == 0:
            return f"현재 시각은 {period} {display_hour}시 정각입니다."
        else:
            return f"현재 시각은 {period} {display_hour}시 {minute}분입니다."

    def get_date(self) -> str:
        """오늘 날짜 안내"""
        now = datetime.now()
        weekday = ["월요일", "화요일", "수요일", "목요일",
                    "금요일", "토요일", "일요일"][now.weekday()]
        return f"오늘은 {now.year}년 {now.month}월 {now.day}일 {weekday}입니다."

    def set_timer(self, minutes: int, callback: Callable[[str], None]) -> str:
        """타이머 설정"""
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.cancel()

        self._timer_callback = callback

        def on_timer():
            if self._timer_callback:
                self._timer_callback(f"형님, {minutes}분 타이머가 완료되었습니다.")

        self._timer_thread = threading.Timer(minutes * 60, on_timer)
        self._timer_thread.daemon = True
        self._timer_thread.start()

        log.info(f"타이머 설정: {minutes}분")
        return f"{minutes}분 타이머를 설정했습니다."

    def cancel_timer(self) -> str:
        """타이머 취소"""
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.cancel()
            self._timer_thread = None
            return "타이머를 취소했습니다."
        return "설정된 타이머가 없습니다."

    def handle(self, text: str) -> str:
        """생산성 명령 처리"""
        text_lower = text.lower()

        if any(w in text_lower for w in ["몇 시", "시간", "시각"]):
            return self.get_current_time()

        if any(w in text_lower for w in ["날짜", "며칠", "오늘"]):
            return self.get_date()

        if "타이머" in text_lower:
            if "취소" in text_lower or "중지" in text_lower:
                return self.cancel_timer()
            # 분 추출
            minutes = self._extract_minutes(text_lower)
            if minutes:
                return self.set_timer(minutes, lambda msg: None)
            return "몇 분 타이머를 설정할까요?"

        return ""

    @staticmethod
    def _extract_minutes(text: str) -> Optional[int]:
        """텍스트에서 분 수 추출"""
        import re
        match = re.search(r"(\d+)\s*분", text)
        if match:
            return int(match.group(1))

        korean_nums = {
            "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
            "육": 6, "칠": 7, "팔": 8, "구": 9, "십": 10,
            "한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5,
        }
        for word, num in korean_nums.items():
            if f"{word}분" in text or f"{word} 분" in text:
                return num
        return None
