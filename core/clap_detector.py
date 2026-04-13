"""
박수 감지 모듈
더블 클랩(박수 두 번)으로도 자비스를 깨울 수 있음
"""
import numpy as np
import sounddevice as sd
import time
import threading
from config import SAMPLE_RATE, CHANNELS, CLAP_THRESHOLD, CLAP_DOUBLE_WINDOW
from utils.logger import log


class ClapDetector:
    def __init__(self, callback):
        self.callback = callback
        self.is_running = False
        self.last_clap_time = 0
        self.clap_count = 0

    def _detect_clap(self, audio_chunk) -> bool:
        """볼륨 스파이크 = 박수"""
        peak = np.max(np.abs(audio_chunk))
        return peak > CLAP_THRESHOLD

    def start(self):
        self.is_running = True

        def audio_callback(indata, frames, time_info, status):
            if self._detect_clap(indata):
                now = time.time()
                if now - self.last_clap_time < CLAP_DOUBLE_WINDOW:
                    self.clap_count += 1
                    if self.clap_count >= 2:
                        log.info("더블 클랩 감지!")
                        self.clap_count = 0
                        threading.Thread(target=self.callback, daemon=True).start()
                else:
                    self.clap_count = 1
                self.last_clap_time = now

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=int(SAMPLE_RATE * 0.05),
            callback=audio_callback
        ):
            while self.is_running:
                time.sleep(0.1)

    def stop(self):
        self.is_running = False
