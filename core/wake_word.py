"""
웨이크워드 감지 모듈
faster-whisper로 실시간 오디오를 STT 변환하여 "자비스" 키워드를 감지한다
"""
import numpy as np
import sounddevice as sd
import queue
import threading
from faster_whisper import WhisperModel
from config import SAMPLE_RATE, CHANNELS, CHUNK_DURATION, WAKE_WORD, WHISPER_MODEL, WHISPER_LANGUAGE
from utils.logger import log


class WakeWordDetector:
    def __init__(self, callback):
        self.callback = callback  # 웨이크워드 감지 시 호출할 함수
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        log.info(f"웨이크워드 감지기 초기화 완료 - 모델: {WHISPER_MODEL}")

    def _audio_callback(self, indata, frames, time, status):
        """마이크에서 오디오 스트림 수신"""
        if status:
            log.warning(f"오디오 상태: {status}")
        self.audio_queue.put(indata.copy())

    def _process_audio(self):
        """오디오 청크를 모아 STT 처리"""
        buffer = np.array([], dtype=np.float32)

        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=1.0)
                buffer = np.concatenate([buffer, chunk.flatten()])

                # 1.5초 분량이 쌓이면 STT 처리
                if len(buffer) >= int(SAMPLE_RATE * 1.5):
                    segments, _ = self.model.transcribe(
                        buffer,
                        language=WHISPER_LANGUAGE,
                        beam_size=1,
                        vad_filter=True
                    )
                    text = "".join([seg.text for seg in segments]).strip()

                    if text:
                        log.debug(f"STT: {text}")
                        if WAKE_WORD in text:
                            log.info(f"웨이크워드 감지: '{text}'")
                            self.callback(text)

                    buffer = np.array([], dtype=np.float32)

            except queue.Empty:
                continue

    def start(self):
        self.is_running = True
        process_thread = threading.Thread(target=self._process_audio, daemon=True)
        process_thread.start()

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            callback=self._audio_callback
        ):
            log.info(f"'{WAKE_WORD}' 웨이크워드 대기 중...")
            while self.is_running:
                import time
                time.sleep(0.1)

    def stop(self):
        self.is_running = False
