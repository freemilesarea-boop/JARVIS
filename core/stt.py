"""
음성 → 텍스트 변환 모듈
웨이크워드 감지 후 명령어를 듣는다.

개선사항:
  - TTS 직후 마이크 버퍼 플러시 (잔여 소리 무시)
  - 최소 녹음 시간 보장 (너무 일찍 끊기지 않도록)
  - 침묵 감지를 발화 감지 이후에만 적용
  - Whisper에 vad_filter 사용하지 않음 (짧은 오디오에서 전부 제거될 수 있음)
"""
import numpy as np
import sounddevice as sd
import time
from faster_whisper import WhisperModel
from config.settings import WHISPER_MODEL, WHISPER_LANGUAGE
from config.audio_config import SAMPLE_RATE, CHANNELS
from utils.logger import log

# STT 전용 설정 (audio_config의 VAD 설정과 독립)
_SILENCE_THRESHOLD = 0.008     # 침묵 판정 RMS (낮을수록 민감)
_SILENCE_TIMEOUT = 2.0         # 발화 후 이 시간 침묵하면 녹음 종료
_MIN_RECORD_TIME = 2.5         # 최소 녹음 시간 (이전에 끊기지 않음)
_WARMUP_TIME = 0.5             # 녹음 시작 후 이 시간은 VAD 무시 (버퍼 플러시)


class STT:
    _shared_model = None

    def __init__(self):
        if STT._shared_model is None:
            log.info(f"Whisper 모델 로딩: {WHISPER_MODEL}")
            STT._shared_model = WhisperModel(
                WHISPER_MODEL, device="cpu", compute_type="int8"
            )
        self.model = STT._shared_model

    def listen(self, duration=8.0) -> str:
        """
        명령어를 듣는다.

        흐름:
          1. 녹음 시작 (최대 duration초)
          2. 처음 0.5초는 워밍업 — 침묵 판정 안 함
          3. 최소 2.5초까지는 무조건 녹음 계속
          4. 2.5초 이후 발화가 감지되었다가 2초간 침묵하면 녹음 종료
          5. Whisper로 변환
        """
        log.info("명령 대기 중...")

        audio_data = []
        has_speech = False
        silent_chunks = 0
        required_silent_chunks = int(_SILENCE_TIMEOUT / 0.1)  # 20 chunks

        record_start = time.time()

        def callback(indata, frames, time_info, status):
            nonlocal has_speech, silent_chunks
            audio_data.append(indata.copy())

            elapsed = time.time() - record_start

            # 워밍업 기간: VAD 무시
            if elapsed < _WARMUP_TIME:
                return

            rms = np.sqrt(np.mean(indata ** 2))

            if rms > _SILENCE_THRESHOLD:
                has_speech = True
                silent_chunks = 0
            else:
                silent_chunks += 1

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=callback,
            ):
                while True:
                    time.sleep(0.1)
                    elapsed = time.time() - record_start

                    # 최대 시간 초과
                    if elapsed >= duration:
                        break

                    # 최소 녹음 시간 미달이면 계속
                    if elapsed < _MIN_RECORD_TIME:
                        continue

                    # 발화가 있었고, 충분히 침묵했으면 종료
                    if has_speech and silent_chunks >= required_silent_chunks:
                        break

        except Exception as e:
            log.error(f"STT 오디오 입력 오류: {e}")
            return ""

        if not audio_data:
            return ""

        audio = np.concatenate(audio_data).flatten()
        record_duration = len(audio) / SAMPLE_RATE
        log.info(f"녹음 완료: {record_duration:.1f}초")

        # 너무 짧은 오디오는 무시
        if record_duration < 0.5:
            return ""

        try:
            # vad_filter=False: 짧은 오디오에서 전체를 제거하는 문제 방지
            segments, info = self.model.transcribe(
                audio,
                language=WHISPER_LANGUAGE,
                beam_size=5,
                vad_filter=False,
            )
            text = "".join([seg.text for seg in segments]).strip()
        except Exception as e:
            log.error(f"STT 변환 오류: {e}")
            return ""

        log.info(f"인식된 명령: '{text}'")
        return text
