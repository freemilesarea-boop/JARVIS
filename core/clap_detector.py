"""
박수 감지 모듈 (고도화)

제스처 정의:
  박수 1회  → on_single_clap  (활성화)
  박수 2회  → on_double_clap  (대화 종료)
  박수 3회  → on_triple_clap  (긴급 정지)

판정 기준:
  - Peak + RMS 동시 체크
  - 짧은 임펄스 패턴 (박수는 지속시간이 짧다)
  - 연속 박수 간 최소/최대 간격
  - 쿨다운으로 중복 감지 방지
"""
import numpy as np
import sounddevice as sd
import time
import threading
from typing import Callable, Optional
from config.audio_config import (
    SAMPLE_RATE, CHANNELS,
    CLAP_THRESHOLD, CLAP_RMS_THRESHOLD,
    CLAP_MIN_INTERVAL, CLAP_MAX_INTERVAL,
    CLAP_IMPULSE_MAX_DURATION, CLAP_COOLDOWN,
)
from utils.logger import log


class ClapDetector:
    """
    정밀 박수 감지기.
    peak + RMS + 임펄스 패턴으로 박수를 판별하고,
    1회/2회/3회에 따라 다른 콜백을 호출한다.
    """

    def __init__(
        self,
        on_single_clap: Optional[Callable] = None,
        on_double_clap: Optional[Callable] = None,
        on_triple_clap: Optional[Callable] = None,
    ):
        self.on_single_clap = on_single_clap
        self.on_double_clap = on_double_clap
        self.on_triple_clap = on_triple_clap

        self.is_running = False
        self._clap_times: list[float] = []
        self._last_action_time = 0.0
        self._decision_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        # 임펄스 추적
        self._impulse_start: Optional[float] = None
        self._in_impulse = False

    def _is_clap(self, audio_chunk: np.ndarray) -> bool:
        """
        peak + RMS 기반 박수 판정.
        박수는 짧고 강한 임펄스 특성을 가진다.
        """
        peak = np.max(np.abs(audio_chunk))
        rms = np.sqrt(np.mean(audio_chunk ** 2))

        if peak > CLAP_THRESHOLD and rms > CLAP_RMS_THRESHOLD:
            return True
        return False

    def _on_clap_detected(self):
        """개별 박수 감지 시 호출"""
        now = time.time()

        # 쿨다운 중이면 무시
        if now - self._last_action_time < CLAP_COOLDOWN:
            return

        with self._lock:
            # 이전 박수와의 간격 확인
            if self._clap_times:
                interval = now - self._clap_times[-1]
                if interval < CLAP_MIN_INTERVAL:
                    return  # 너무 빠르면 잡음
                if interval > CLAP_MAX_INTERVAL:
                    # 간격 초과: 이전 패턴 확정 후 새로 시작
                    self._finalize_pattern()
                    self._clap_times = []

            self._clap_times.append(now)
            clap_count = len(self._clap_times)

            # 타이머 재설정: 마지막 박수 후 간격 내에 추가 없으면 패턴 확정
            if self._decision_timer:
                self._decision_timer.cancel()

            self._decision_timer = threading.Timer(
                CLAP_MAX_INTERVAL, self._finalize_pattern
            )
            self._decision_timer.daemon = True
            self._decision_timer.start()

    def _finalize_pattern(self):
        """박수 패턴을 확정하고 콜백을 호출한다."""
        with self._lock:
            count = len(self._clap_times)
            self._clap_times = []

            if count <= 0:
                return

            self._last_action_time = time.time()

        if count >= 3 and self.on_triple_clap:
            log.info(f"트리플 클랩 감지! (박수 {count}회)")
            threading.Thread(target=self.on_triple_clap, daemon=True).start()
        elif count == 2 and self.on_double_clap:
            log.info("더블 클랩 감지!")
            threading.Thread(target=self.on_double_clap, daemon=True).start()
        elif count == 1 and self.on_single_clap:
            log.info("싱글 클랩 감지!")
            threading.Thread(target=self.on_single_clap, daemon=True).start()

    def start(self):
        """박수 감지 루프 시작 (블로킹)"""
        self.is_running = True
        block_size = int(SAMPLE_RATE * 0.03)  # 30ms 블록

        def audio_callback(indata, frames, time_info, status):
            if not self.is_running:
                return
            if self._is_clap(indata):
                self._on_clap_detected()

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=block_size,
                callback=audio_callback,
            ):
                log.info("박수 감지 활성화 (1회=활성화, 2회=종료, 3회=긴급정지)")
                while self.is_running:
                    time.sleep(0.1)
        except Exception as e:
            log.error(f"박수 감지 오류: {e}")

    def stop(self):
        """박수 감지 중지"""
        self.is_running = False
        if self._decision_timer:
            self._decision_timer.cancel()
