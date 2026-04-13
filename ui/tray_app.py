"""
시스템 트레이 앱 (선택적)
pystray를 사용한 시스템 트레이 아이콘.
설치되지 않은 경우 콘솔 모드로 폴백.
"""
from utils.logger import log


class TrayApp:
    """
    시스템 트레이 아이콘.
    pystray 미설치 시 콘솔 모드로 동작.
    """

    def __init__(self, on_quit=None, on_toggle=None):
        self._on_quit = on_quit
        self._on_toggle = on_toggle
        self._available = False

        try:
            import pystray
            from PIL import Image
            self._available = True
        except ImportError:
            log.debug("pystray 미설치 - 트레이 아이콘 비활성화")

    @property
    def is_available(self) -> bool:
        return self._available

    def start(self):
        """트레이 아이콘 시작 (사용 가능한 경우에만)"""
        if not self._available:
            log.info("시스템 트레이 아이콘 미지원 - 콘솔 모드로 실행")
            return

        try:
            import pystray
            from PIL import Image, ImageDraw

            # 간단한 아이콘 생성 (파란 원)
            image = Image.new("RGB", (64, 64), "black")
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill="cyan")

            menu = pystray.Menu(
                pystray.MenuItem("JARVIS 상태", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "활성화/비활성화",
                    lambda: self._on_toggle() if self._on_toggle else None,
                ),
                pystray.MenuItem(
                    "종료",
                    lambda: self._on_quit() if self._on_quit else None,
                ),
            )

            self._icon = pystray.Icon("JARVIS", image, "JARVIS", menu)
            self._icon.run_detached()
            log.info("시스템 트레이 아이콘 활성화")

        except Exception as e:
            log.debug(f"트레이 아이콘 시작 실패: {e}")

    def stop(self):
        if hasattr(self, "_icon"):
            try:
                self._icon.stop()
            except Exception:
                pass
