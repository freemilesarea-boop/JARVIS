"""
자동 시작 서비스
OS 시작 시 JARVIS 자동 실행 설정.
절전 해제 후 자동 복구.
크로스 플랫폼 (macOS, Linux, Windows).
"""
import os
import sys
import platform
import subprocess
from utils.logger import log

_SYSTEM = platform.system()
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MAIN_PY = os.path.join(_PROJECT_DIR, "main.py")
_PYTHON = sys.executable


class StartupService:
    """OS 시작 시 JARVIS 자동 실행 관리"""

    def enable_autostart(self) -> str:
        """자동 시작 등록"""
        try:
            if _SYSTEM == "Darwin":
                return self._enable_macos()
            elif _SYSTEM == "Linux":
                return self._enable_linux()
            elif _SYSTEM == "Windows":
                return self._enable_windows()
            return "지원하지 않는 운영체제입니다."
        except Exception as e:
            log.error(f"자동 시작 등록 실패: {e}")
            return f"자동 시작 등록에 실패했습니다: {e}"

    def disable_autostart(self) -> str:
        """자동 시작 해제"""
        try:
            if _SYSTEM == "Darwin":
                return self._disable_macos()
            elif _SYSTEM == "Linux":
                return self._disable_linux()
            elif _SYSTEM == "Windows":
                return self._disable_windows()
            return "지원하지 않는 운영체제입니다."
        except Exception as e:
            log.error(f"자동 시작 해제 실패: {e}")
            return f"자동 시작 해제에 실패했습니다: {e}"

    def is_autostart_enabled(self) -> bool:
        """자동 시작 설정 여부 확인"""
        if _SYSTEM == "Darwin":
            plist = os.path.expanduser(
                "~/Library/LaunchAgents/com.jarvis.assistant.plist"
            )
            return os.path.exists(plist)
        elif _SYSTEM == "Linux":
            desktop = os.path.expanduser(
                "~/.config/autostart/jarvis.desktop"
            )
            return os.path.exists(desktop)
        elif _SYSTEM == "Windows":
            startup = os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs\Startup",
                "jarvis.bat",
            )
            return os.path.exists(startup)
        return False

    # -- macOS --

    def _enable_macos(self) -> str:
        plist_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(plist_dir, exist_ok=True)
        plist_path = os.path.join(plist_dir, "com.jarvis.assistant.plist")

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{_PYTHON}</string>
        <string>{_MAIN_PY}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{_PROJECT_DIR}</string>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/jarvis.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/jarvis.err.log</string>
</dict>
</plist>"""

        with open(plist_path, "w") as f:
            f.write(plist_content)

        subprocess.run(["launchctl", "load", plist_path], capture_output=True)
        log.info("macOS 자동 시작 등록 완료")
        return "자동 시작이 등록되었습니다."

    def _disable_macos(self) -> str:
        plist_path = os.path.expanduser(
            "~/Library/LaunchAgents/com.jarvis.assistant.plist"
        )
        if os.path.exists(plist_path):
            subprocess.run(["launchctl", "unload", plist_path], capture_output=True)
            os.remove(plist_path)
        log.info("macOS 자동 시작 해제")
        return "자동 시작이 해제되었습니다."

    # -- Linux --

    def _enable_linux(self) -> str:
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        desktop_path = os.path.join(autostart_dir, "jarvis.desktop")

        desktop_content = f"""[Desktop Entry]
Type=Application
Name=JARVIS
Exec={_PYTHON} {_MAIN_PY}
Path={_PROJECT_DIR}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
Comment=JARVIS AI Voice Assistant
"""
        with open(desktop_path, "w") as f:
            f.write(desktop_content)

        log.info("Linux 자동 시작 등록 완료")
        return "자동 시작이 등록되었습니다."

    def _disable_linux(self) -> str:
        desktop_path = os.path.expanduser(
            "~/.config/autostart/jarvis.desktop"
        )
        if os.path.exists(desktop_path):
            os.remove(desktop_path)
        log.info("Linux 자동 시작 해제")
        return "자동 시작이 해제되었습니다."

    # -- Windows --

    def _enable_windows(self) -> str:
        startup_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        bat_path = os.path.join(startup_dir, "jarvis.bat")

        bat_content = f'@echo off\ncd /d "{_PROJECT_DIR}"\n"{_PYTHON}" "{_MAIN_PY}"\n'

        with open(bat_path, "w") as f:
            f.write(bat_content)

        log.info("Windows 자동 시작 등록 완료")
        return "자동 시작이 등록되었습니다."

    def _disable_windows(self) -> str:
        bat_path = os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
            "jarvis.bat",
        )
        if os.path.exists(bat_path):
            os.remove(bat_path)
        log.info("Windows 자동 시작 해제")
        return "자동 시작이 해제되었습니다."
