"""
시스템 제어 스킬
음성 명령으로 OS/앱 제어를 수행한다.
"""
from services.os_control_service import OSControlService
from services.app_launcher_service import AppLauncherService
from utils.logger import log


class SystemSkill:
    """시스템 제어 음성 명령 처리"""

    def __init__(self):
        self.os_control = OSControlService()
        self.app_launcher = AppLauncherService()

    def handle(self, text: str) -> str:
        """
        시스템 명령을 분석하고 실행한다.
        Returns: 실행 결과 메시지
        """
        text_lower = text.lower()

        # 볼륨 제어
        if any(w in text_lower for w in ["볼륨 올", "소리 올", "소리 키", "볼륨 높"]):
            return self.os_control.volume_up()
        if any(w in text_lower for w in ["볼륨 내", "소리 내", "소리 줄", "볼륨 낮"]):
            return self.os_control.volume_down()
        if any(w in text_lower for w in ["음소거", "뮤트", "mute"]):
            return self.os_control.volume_mute()

        # 앱 실행
        if any(w in text_lower for w in ["열어", "실행", "켜줘", "시작"]):
            app_name = self._extract_app_name(text_lower, ["열어", "실행", "켜줘", "시작"])
            if app_name:
                return self.app_launcher.launch(app_name)
            return "어떤 앱을 열까요?"

        # 앱 종료
        if any(w in text_lower for w in ["닫아", "종료해", "꺼줘"]):
            app_name = self._extract_app_name(text_lower, ["닫아", "종료해", "꺼줘"])
            if app_name:
                return self.app_launcher.close(app_name)
            return "어떤 앱을 닫을까요?"

        # URL 열기
        if any(w in text_lower for w in ["검색", "구글", "네이버"]):
            if "구글" in text_lower:
                query = text_lower.split("구글")[-1].strip().rstrip("해줘 검색")
                if query:
                    url = f"https://www.google.com/search?q={query}"
                    return self.os_control.open_url(url)
                return self.os_control.open_url("https://www.google.com")
            if "네이버" in text_lower:
                query = text_lower.split("네이버")[-1].strip().rstrip("해줘 검색")
                if query:
                    url = f"https://search.naver.com/search.naver?query={query}"
                    return self.os_control.open_url(url)
                return self.os_control.open_url("https://www.naver.com")

        # 화면 잠금
        if any(w in text_lower for w in ["잠금", "잠가", "lock"]):
            return self.os_control.lock_screen()

        # 절전
        if any(w in text_lower for w in ["절전", "슬립", "sleep"]):
            return self.os_control.sleep_system()

        return ""

    def _extract_app_name(self, text: str, triggers: list[str]) -> str:
        """명령어에서 앱 이름 추출"""
        for trigger in triggers:
            if trigger in text:
                # 트리거 앞의 단어들을 앱 이름으로 추출
                idx = text.index(trigger)
                before = text[:idx].strip()
                # 일반적인 조사/접미사 제거
                for suffix in ["을", "를", "좀", " 좀", "도"]:
                    before = before.rstrip(suffix)
                before = before.strip()
                if before:
                    # 마지막 단어만 추출
                    words = before.split()
                    return words[-1] if words else ""
        return ""
