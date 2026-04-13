"""
음성 → 텍스트 변환 모듈
웨이크워드 감지 후 명령어를 듣는다.

고도화:
  - VAD(Voice Activity Detection) 기반 발화 종료 감지
  - 최소 발화 시간 체크
  - 장시간 안정적 운영
"""
import numpy as np
import sounddevice as sd
import time
from faster_whisper import WhisperModel
from config.settings import WHISPER_MODEL, WHISPER_LANGUAGE
from config.audio_config import (
    SAMPLE_RATE, CHANNELS,
    VAD_SILENCE_THRESHOLD, VAD_SILENCE_DURATION, VAD_MIN_SPEECH_DURATION,
)
from utils.logger import log


class STT:
    _shared_model = None

    def __init__(self):
        # 모델을 클래스 레벨에서 공유하여 메모리 절약
        if STT._shared_model is None:
            log.info(f"Whisper 모델 로딩: {WHISPER_MODEL}")
            STT._shared_model = WhisperModel(
                WHISPER_MODEL, device="cpu", compute_type="int8"
            )
        self.model = STT._shared_model

    def listen(self, duration=8.0, silence_threshold=None, silence_duration=None):
        """
        명령어를 듣는다.
        - 최대 duration초 동안 듣기
        - VAD 기반 발화 종료 감지
        - 최소 발화 시간 미달 시 빈 문자열 반환
        """
        silence_threshold = silence_threshold or VAD_SILENCE_THRESHOLD
        silence_duration = silence_duration or VAD_SILENCE_DURATION

        log.info("명령 대기 중...")

        audio_data = []
        required_silent_chunks = int(silence_duration / 0.1)
        has_speech = False
        speech_start_time = None

        def callback(indata, frames, time_info, status):
            nonlocal has_speech, speech_start_time
            audio_data.append(indata.copy())
            rms = np.sqrt(np.mean(indata ** 2))

            if rms > silence_threshold:
                if not has_speech:
                    has_speech = True
                    speech_start_time = time.time()
                callback._silent = 0
            else:
                callback._silent = getattr(callback, '_silent', 0) + 1

        callback._silent = 0

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=callback,
            ):
                start = time.time()
                while time.time() - start < duration:
                    time.sleep(0.1)
                    if (
                        has_speech
                        and callback._silent >= required_silent_chunks
                        and len(audio_data) > 10
                    ):
                        break
        except Exception as e:
            log.error(f"STT 오디오 입력 오류: {e}")
            return ""

        if not audio_data:
            return ""

        # 최소 발화 시간 체크
        if speech_start_time:
            speech_duration = time.time() - speech_start_time
            if speech_duration < VAD_MIN_SPEECH_DURATION:
                log.debug("발화 시간 부족 - 무시")
                return ""

        audio = np.concatenate(audio_data).flatten()
        try:
            segments, _ = self.model.transcribe(
                audio, language=WHISPER_LANGUAGE, beam_size=3
            )
            text = "".join([seg.text for seg in segments]).strip()
        except Exception as e:
            log.error(f"STT 변환 오류: {e}")
            return ""

        log.info(f"인식된 명령: '{text}'")
        return text
