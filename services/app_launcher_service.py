"""
앱 실행 서비스
음성 명령으로 프로그램을 실행/종료한다.
크로스 플랫폼 (macOS, Linux, Windows).
"""
import subprocess
import platform
import shutil
from typing import Optional
from utils.logger import log

_SYSTEM = platform.system()

# 앱 이름 → 실행 명령 매핑 (한국어 + 영어)
_APP_MAP = {
    # 브라우저
    "크롬": {"Darwin": "Google Chrome", "Linux": "google-chrome", "Windows": "chrome"},
    "chrome": {"Darwin": "Google Chrome", "Linux": "google-chrome", "Windows": "chrome"},
    "파이어폭스": {"Darwin": "Firefox", "Linux": "firefox", "Windows": "firefox"},
    "firefox": {"Darwin": "Firefox", "Linux": "firefox", "Windows": "firefox"},
    "사파리": {"Darwin": "Safari"},
    "safari": {"Darwin": "Safari"},

    # 개발 도구
    "코드": {"Darwin": "Visual Studio Code", "Linux": "code", "Windows": "code"},
    "vscode": {"Darwin": "Visual Studio Code", "Linux": "code", "Windows": "code"},
    "터미널": {"Darwin": "Terminal", "Linux": "gnome-terminal", "Windows": "cmd"},
    "terminal": {"Darwin": "Terminal", "Linux": "gnome-terminal", "Windows": "cmd"},

    # 오피스/유틸
    "메모": {"Darwin": "TextEdit", "Linux": "gedit", "Windows": "notepad"},
    "notepad": {"Darwin": "TextEdit", "Linux": "gedit", "Windows": "notepad"},
    "계산기": {"Darwin": "Calculator", "Linux": "gnome-calculator", "Windows": "calc"},
    "calculator": {"Darwin": "Calculator", "Linux": "gnome-calculator", "Windows": "calc"},
    "파일": {"Darwin": "Finder", "Linux": "nautilus", "Windows": "explorer"},
    "탐색기": {"Darwin": "Finder", "Linux": "nautilus", "Windows": "explorer"},

    # 미디어
    "음악": {"Darwin": "Music", "Linux": "rhythmbox", "Windows": "wmplayer"},
    "스포티파이": {"Darwin": "Spotify", "Linux": "spotify", "Windows": "spotify"},
    "spotify": {"Darwin": "Spotify", "Linux": "spotify", "Windows": "spotify"},

    # 커뮤니케이션
    "슬랙": {"Darwin": "Slack", "Linux": "slack", "Windows": "slack"},
    "slack": {"Darwin": "Slack", "Linux": "slack", "Windows": "slack"},
    "디스코드": {"Darwin": "Discord", "Linux": "discord", "Windows": "discord"},
    "discord": {"Darwin": "Discord", "Linux": "discord", "Windows": "discord"},
}


class AppLauncherService:
    """앱 실행/종료 서비스"""

    def launch(self, app_name: str) -> str:
        """앱 실행"""
        app_name_lower = app_name.lower().strip()

        # 매핑에서 찾기
        app_info = _APP_MAP.get(app_name_lower)
        if app_info:
            cmd = app_info.get(_SYSTEM)
            if cmd:
                return self._open_app(cmd)
            return f"{app_name}은 현재 운영체제에서 지원하지 않습니다."

        # 매핑에 없으면 직접 시도
        return self._open_app(app_name)

    def _open_app(self, app_name: str) -> str:
        """OS별 앱 실행"""
        try:
            if _SYSTEM == "Darwin":
                subprocess.Popen(
                    ["open", "-a", app_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif _SYSTEM == "Linux":
                # 실행 파일이 PATH에 있는지 확인
                if shutil.which(app_name):
                    subprocess.Popen(
                        [app_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    return f"{app_name}을 찾을 수 없습니다."
            elif _SYSTEM == "Windows":
                subprocess.Popen(
                    ["start", "", app_name],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            log.info(f"앱 실행: {app_name}")
            return f"{app_name}을 실행했습니다."

        except Exception as e:
            log.error(f"앱 실행 실패 ({app_name}): {e}")
            return f"{app_name} 실행에 실패했습니다."

    def close(self, app_name: str) -> str:
        """앱 종료"""
        app_name_lower = app_name.lower().strip()
        app_info = _APP_MAP.get(app_name_lower)
        target = app_info.get(_SYSTEM, app_name) if app_info else app_name

        try:
            if _SYSTEM == "Darwin":
                subprocess.run(
                    ["osascript", "-e",
                     f'tell application "{target}" to quit'],
                    check=True,
                )
            elif _SYSTEM == "Linux":
                subprocess.run(
                    ["pkill", "-f", target],
                    capture_output=True,
                )
            elif _SYSTEM == "Windows":
                subprocess.run(
                    ["taskkill", "/IM", f"{target}.exe", "/F"],
                    capture_output=True,
                )

            log.info(f"앱 종료: {target}")
            return f"{app_name}을 종료했습니다."

        except Exception as e:
            log.error(f"앱 종료 실패 ({target}): {e}")
            return f"{app_name} 종료에 실패했습니다."

    def get_available_apps(self) -> list[str]:
        """현재 OS에서 사용 가능한 앱 목록"""
        available = []
        seen = set()
        for name, info in _APP_MAP.items():
            cmd = info.get(_SYSTEM)
            if cmd and cmd not in seen:
                available.append(name)
                seen.add(cmd)
        return available
