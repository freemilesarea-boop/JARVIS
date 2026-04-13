"""
워치독 모듈
장시간 실행 안정성을 위해 주기적으로 시스템 상태를 점검한다.
- 오디오 스트림 상태 확인
- 메모리 사용량 모니터링
- 상태 머신 교착 감지
"""
import threading
import time
import gc
from typing import Optional, Callable
from config.settings import WATCHDOG_INTERVAL
from utils.logger import log


class Watchdog:
    """
    주기적 상태 점검 및 자동 복구.
    """

    def __init__(self, health_check: Optional[Callable[[], bool]] = None):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._health_check = health_check
        self._consecutive_failures = 0
        self._max_failures = 3
        self._on_failure: Optional[Callable] = None

    def set_failure_handler(self, handler: Callable):
        """연속 실패 시 호출할 핸들러 설정"""
        self._on_failure = handler

    def start(self):
        """워치독 시작"""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log.info(f"워치독 시작 (점검 주기: {WATCHDOG_INTERVAL}초)")

    def stop(self):
        """워치독 중지"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def _run(self):
        while self._running:
            time.sleep(WATCHDOG_INTERVAL)
            if not self._running:
                break

            try:
                self._check_system()
            except Exception as e:
                log.error(f"워치독 점검 오류: {e}")

    def _check_system(self):
        """시스템 상태 점검"""
        # 메모리 정리
        gc.collect()

        # 커스텀 헬스 체크
        if self._health_check:
            healthy = self._health_check()
            if not healthy:
                self._consecutive_failures += 1
                log.warning(
                    f"헬스 체크 실패 ({self._consecutive_failures}/{self._max_failures})"
                )
                if self._consecutive_failures >= self._max_failures:
                    log.error("연속 헬스 체크 실패 - 복구 시도")
                    if self._on_failure:
                        self._on_failure()
                    self._consecutive_failures = 0
            else:
                if self._consecutive_failures > 0:
                    log.info("헬스 체크 정상 복구")
                self._consecutive_failures = 0

        # 메모리 사용량 로깅
        try:
            import psutil
            process = psutil.Process()
            mem_mb = process.memory_info().rss / 1024 / 1024
            if mem_mb > 500:
                log.warning(f"메모리 사용량 높음: {mem_mb:.0f}MB")
        except ImportError:
            pass  # psutil 미설치 시 스킵
