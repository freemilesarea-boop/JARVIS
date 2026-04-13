"""
웨이크워드 감지 모듈
faster-whisper로 실시간 오디오를 STT 변환하여 "자비스" 키워드를 감지한다.

고도화:
  - STT 모델 공유 (메모리 절약)
  - 오디오 스트림 장애 시 자동 복구
  - 상태 머신 연동
"""
import numpy as np
import sounddevice as sd
import queue
import threading
import time as time_module
from core.stt import STT
from config.settings import WAKE_WORD, WHISPER_LANGUAGE
from config.audio_config import SAMPLE_RATE, CHANNELS
from utils.logger import log


class WakeWordDetector:
    def __init__(self, callback):
        self.callback = callback
        self.audio_queue = queue.Queue()
        self.is_running = False
        self._enabled = True  # 활성 세션 중에는 비활성화 가능

        # STT 클래스의 공유 모델 사용
        stt = STT()
        self.model = stt.model
        log.info("웨이크워드 감지기 초기화 완료 (공유 모델)")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        if value:
            log.debug("웨이크워드 감지 활성화")
        else:
            log.debug("웨이크워드 감지 비활성화")

    def _audio_callback(self, indata, frames, time, status):
        if status:
            log.warning(f"오디오 상태: {status}")
        if self._enabled:
            self.audio_queue.put(indata.copy())

    def _process_audio(self):
        buffer = np.array([], dtype=np.float32)

        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=1.0)
                if not self._enabled:
                    continue

                buffer = np.concatenate([buffer, chunk.flatten()])

                if len(buffer) >= int(SAMPLE_RATE * 1.5):
                    try:
                        segments, _ = self.model.transcribe(
                            buffer,
                            language=WHISPER_LANGUAGE,
                            beam_size=1,
                            vad_filter=True,
                        )
                        text = "".join([seg.text for seg in segments]).strip()

                        if text:
                            log.debug(f"STT: {text}")
                            if WAKE_WORD in text:
                                log.info(f"웨이크워드 감지: '{text}'")
                                self.callback(text)
                    except Exception as e:
                        log.error(f"웨이크워드 STT 오류: {e}")

                    buffer = np.array([], dtype=np.float32)

            except queue.Empty:
                continue

    def start(self):
        """웨이크워드 감지 시작 (블로킹). 오디오 스트림 장애 시 자동 재시작."""
        self.is_running = True
        process_thread = threading.Thread(target=self._process_audio, daemon=True)
        process_thread.start()

        while self.is_running:
            try:
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype="float32",
                    callback=self._audio_callback,
                ):
                    log.info(f"'{WAKE_WORD}' 웨이크워드 대기 중...")
                    while self.is_running:
                        time_module.sleep(0.1)
            except Exception as e:
                if self.is_running:
                    log.error(f"오디오 스트림 오류, 2초 후 재시도: {e}")
                    time_module.sleep(2.0)

    def stop(self):
        self.is_running = False
