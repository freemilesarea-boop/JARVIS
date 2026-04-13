"""
음성 → 텍스트 변환 모듈
웨이크워드 감지 후 명령어를 듣는다
"""
import numpy as np
import sounddevice as sd
import time
from faster_whisper import WhisperModel
from config import SAMPLE_RATE, CHANNELS, WHISPER_MODEL, WHISPER_LANGUAGE
from utils.logger import log


class STT:
    def __init__(self):
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    def listen(self, duration=5.0, silence_threshold=0.01, silence_duration=1.5):
        """
        명령어를 듣는다.
        - 최대 duration초 동안 듣기
        - silence_duration초 이상 침묵하면 자동 종료
        """
        log.info("명령 대기 중...")

        audio_data = []
        required_silent_chunks = int(silence_duration / 0.1)

        def callback(indata, frames, time_info, status):
            audio_data.append(indata.copy())
            rms = np.sqrt(np.mean(indata**2))
            if rms < silence_threshold:
                silent_chunks_counter = getattr(callback, '_silent', 0) + 1
                callback._silent = silent_chunks_counter
            else:
                callback._silent = 0

        callback._silent = 0

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', callback=callback):
            start = time.time()
            while time.time() - start < duration:
                time.sleep(0.1)
                if callback._silent >= required_silent_chunks and len(audio_data) > 10:
                    break

        if not audio_data:
            return ""

        audio = np.concatenate(audio_data).flatten()
        segments, _ = self.model.transcribe(audio, language=WHISPER_LANGUAGE, beam_size=3)
        text = "".join([seg.text for seg in segments]).strip()

        log.info(f"인식된 명령: '{text}'")
        return text
