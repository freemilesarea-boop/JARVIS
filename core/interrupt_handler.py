"""
인터럽트 핸들러 모듈
음성 출력 중 사용자의 개입(인터럽트)을 감지하고 처리한다.
- TTS 재생 중 사용자가 말하면 재생 중단
- 박수 감지 시 즉시 중단

주의: 스피커 출력이 마이크로 다시 들어오는 피드백을 방지하기 위해
  - 높은 임계값 사용 (TTS 볼륨보다 큰 소리만 감지)
  - TTS 시작 직후 일정 시간 무시 (워밍업)
  - 연속 프레임 수 높게 설정
"""
import threading
import time
import numpy as np
import sounddevice as sd
from typing import Callable, Optional
from config.audio_config import SAMPLE_RATE, CHANNELS, CLAP_THRESHOLD
from utils.logger import log


class InterruptHandler:
    """
    음성 출력 중 인터럽트를 감지한다.
    TTS 스피커 출력이 마이크에 피드백되는 것과
    실제 사용자 발화/박수를 구분한다.
    """

    def __init__(self):
        self._monitoring = False
        self._interrupt_callback: Optional[Callable] = None
        self._monitor_thread: Optional[threading.Thread] = None
        # TTS 스피커 피드백보다 높은 임계값 (박수 수준만 감지)
        self._speech_threshold = CLAP_THRESHOLD * 0.8

    def start_monitoring(self, on_interrupt: Callable):
        """인터럽트 모니터링 시작"""
        if self._monitoring:
            return

        self._interrupt_callback = on_interrupt
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitor_thread.start()
        log.debug("인터럽트 모니터링 시작")

    def stop_monitoring(self):
        """인터럽트 모니터링 중지"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None

    def _monitor_loop(self):
        """마이크 입력을 모니터링. 스피커 피드백과 실제 사용자 입력을 구분."""
        consecutive_speech_frames = 0
        # 연속 8프레임 (0.8초) 이상 큰 소리여야 인터럽트 (TTS 피드백 방지)
        required_frames = 8
        # TTS 시작 직후 1.5초는 무시 (스피커 워밍업 피드백)
        warmup_until = time.time() + 1.5

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=int(SAMPLE_RATE * 0.1),
            ) as stream:
                while self._monitoring:
                    data, overflowed = stream.read(int(SAMPLE_RATE * 0.1))
                    if overflowed:
                        continue

                    # 워밍업 기간 동안 무시
                    if time.time() < warmup_until:
                        continue

                    peak = np.max(np.abs(data))

                    if peak > self._speech_threshold:
                        consecutive_speech_frames += 1
                        if consecutive_speech_frames >= required_frames:
                            log.info("인터럽트 감지 - 사용자 발화")
                            if self._interrupt_callback:
                                self._interrupt_callback()
                            self._monitoring = False
                            return
                    else:
                        consecutive_speech_frames = 0

        except Exception as e:
            log.error(f"인터럽트 모니터링 오류: {e}")

    @property
    def is_monitoring(self) -> bool:
        return self._monitoring
