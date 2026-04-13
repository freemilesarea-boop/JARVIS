"""
인터럽트 핸들러 모듈
음성 출력 중 사용자의 개입(인터럽트)을 감지하고 처리한다.
- TTS 재생 중 사용자가 말하면 재생 중단
- 박수 감지 시 즉시 중단
"""
import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional
from config.audio_config import SAMPLE_RATE, CHANNELS, VAD_SILENCE_THRESHOLD
from utils.logger import log


class InterruptHandler:
    """
    음성 출력 중 인터럽트를 감지한다.
    TTS가 재생되는 동안 마이크 입력을 모니터링하여
    사용자가 말하기 시작하면 콜백을 호출한다.
    """

    def __init__(self):
        self._monitoring = False
        self._interrupt_callback: Optional[Callable] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._speech_threshold = VAD_SILENCE_THRESHOLD * 5  # 발화로 판단할 레벨

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
        log.debug("인터럽트 모니터링 중지")

    def _monitor_loop(self):
        """마이크 입력을 모니터링하여 발화/박수 감지"""
        consecutive_speech_frames = 0
        required_frames = 3  # 연속 3프레임 이상 발화 시 인터럽트

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

                    rms = np.sqrt(np.mean(data ** 2))

                    if rms > self._speech_threshold:
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
