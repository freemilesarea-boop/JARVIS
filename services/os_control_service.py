"""
OS 제어 서비스
볼륨 조절, 파일 열기, 브라우저 제어 등 OS 수준 자동화.
크로스 플랫폼 지원 (macOS, Linux, Windows).
"""
import subprocess
import platform
import os
import webbrowser
from utils.logger import log


_SYSTEM = platform.system()  # "Darwin", "Linux", "Windows"


class OSControlService:
    """운영체제 수준의 제어 기능을 제공한다."""

    def volume_up(self, step: int = 10) -> str:
        """시스템 볼륨 올리기"""
        try:
            if _SYSTEM == "Darwin":
                current = self._get_mac_volume()
                new_vol = min(100, current + step)
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {new_vol}"],
                    check=True,
                )
            elif _SYSTEM == "Linux":
                subprocess.run(
                    ["amixer", "set", "Master", f"{step}%+"],
                    capture_output=True, check=True,
                )
            elif _SYSTEM == "Windows":
                # PowerShell로 볼륨 제어
                ps_cmd = (
                    f"$obj = new-object -com wscript.shell; "
                    f"1..{step // 2} | %{{ $obj.SendKeys([char]175) }}"
                )
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)
            return f"볼륨을 올렸습니다."
        except Exception as e:
            log.error(f"볼륨 올리기 실패: {e}")
            return "볼륨 조절에 실패했습니다."

    def volume_down(self, step: int = 10) -> str:
        """시스템 볼륨 내리기"""
        try:
            if _SYSTEM == "Darwin":
                current = self._get_mac_volume()
                new_vol = max(0, current - step)
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {new_vol}"],
                    check=True,
                )
            elif _SYSTEM == "Linux":
                subprocess.run(
                    ["amixer", "set", "Master", f"{step}%-"],
                    capture_output=True, check=True,
                )
            elif _SYSTEM == "Windows":
                ps_cmd = (
                    f"$obj = new-object -com wscript.shell; "
                    f"1..{step // 2} | %{{ $obj.SendKeys([char]174) }}"
                )
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)
            return f"볼륨을 내렸습니다."
        except Exception as e:
            log.error(f"볼륨 내리기 실패: {e}")
            return "볼륨 조절에 실패했습니다."

    def volume_mute(self) -> str:
        """음소거 토글"""
        try:
            if _SYSTEM == "Darwin":
                subprocess.run(
                    ["osascript", "-e",
                     "set volume with output muted"],
                    check=True,
                )
            elif _SYSTEM == "Linux":
                subprocess.run(
                    ["amixer", "set", "Master", "toggle"],
                    capture_output=True, check=True,
                )
            return "음소거 전환했습니다."
        except Exception as e:
            log.error(f"음소거 실패: {e}")
            return "음소거 전환에 실패했습니다."

    def _get_mac_volume(self) -> int:
        try:
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True,
            )
            return int(result.stdout.strip())
        except Exception:
            return 50

    def open_url(self, url: str) -> str:
        """브라우저에서 URL 열기"""
        try:
            webbrowser.open(url)
            return "브라우저를 열었습니다."
        except Exception as e:
            log.error(f"URL 열기 실패: {e}")
            return "브라우저 열기에 실패했습니다."

    def open_file(self, path: str) -> str:
        """파일 또는 폴더 열기"""
        if not os.path.exists(path):
            return f"경로를 찾을 수 없습니다: {path}"

        try:
            if _SYSTEM == "Darwin":
                subprocess.run(["open", path], check=True)
            elif _SYSTEM == "Linux":
                subprocess.run(["xdg-open", path], check=True)
            elif _SYSTEM == "Windows":
                os.startfile(path)
            return "파일을 열었습니다."
        except Exception as e:
            log.error(f"파일 열기 실패: {e}")
            return "파일 열기에 실패했습니다."

    def sleep_system(self) -> str:
        """시스템 절전 모드"""
        try:
            if _SYSTEM == "Darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
            elif _SYSTEM == "Linux":
                subprocess.run(["systemctl", "suspend"], check=True)
            elif _SYSTEM == "Windows":
                subprocess.run(
                    ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                    check=True,
                )
            return "절전 모드로 전환합니다."
        except Exception as e:
            log.error(f"절전 전환 실패: {e}")
            return "절전 모드 전환에 실패했습니다."

    def lock_screen(self) -> str:
        """화면 잠금"""
        try:
            if _SYSTEM == "Darwin":
                subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to keystroke "q" '
                     'using {command down, control down}'],
                    check=True,
                )
            elif _SYSTEM == "Linux":
                subprocess.run(["loginctl", "lock-session"], check=True)
            elif _SYSTEM == "Windows":
                subprocess.run(
                    ["rundll32.exe", "user32.dll,LockWorkStation"],
                    check=True,
                )
            return "화면을 잠겼습니다."
        except Exception as e:
            log.error(f"화면 잠금 실패: {e}")
            return "화면 잠금에 실패했습니다."
