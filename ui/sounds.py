"""
효과음 생성 모듈
설치 시 기본 효과음을 프로그래밍 방식으로 생성한다.
외부 wav 파일에 의존하지 않는다.
"""
import numpy as np
import os
from scipy.io import wavfile
from config.audio_config import ACTIVATION_SOUND, DEACTIVATION_SOUND, ERROR_SOUND
from utils.logger import log

_RATE = 44100


def _generate_tone(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
    """단일 톤 생성"""
    t = np.linspace(0, duration, int(_RATE * duration), False)
    tone = volume * np.sin(2 * np.pi * freq * t)
    # 페이드 인/아웃
    fade_len = int(_RATE * 0.02)
    tone[:fade_len] *= np.linspace(0, 1, fade_len)
    tone[-fade_len:] *= np.linspace(1, 0, fade_len)
    return tone


def _generate_activation_sound() -> np.ndarray:
    """활성화 효과음: 상승하는 두 음"""
    tone1 = _generate_tone(523.25, 0.1, 0.25)   # C5
    gap = np.zeros(int(_RATE * 0.05))
    tone2 = _generate_tone(659.25, 0.15, 0.3)   # E5
    return np.concatenate([tone1, gap, tone2])


def _generate_deactivation_sound() -> np.ndarray:
    """비활성화 효과음: 하강하는 두 음"""
    tone1 = _generate_tone(659.25, 0.1, 0.25)   # E5
    gap = np.zeros(int(_RATE * 0.05))
    tone2 = _generate_tone(523.25, 0.15, 0.2)   # C5
    return np.concatenate([tone1, gap, tone2])


def _generate_error_sound() -> np.ndarray:
    """에러 효과음: 낮은 두 음"""
    tone1 = _generate_tone(220, 0.15, 0.3)      # A3
    gap = np.zeros(int(_RATE * 0.1))
    tone2 = _generate_tone(196, 0.2, 0.25)      # G3
    return np.concatenate([tone1, gap, tone2])


def ensure_sounds_exist():
    """효과음 파일이 없으면 생성한다."""
    sounds = [
        (ACTIVATION_SOUND, _generate_activation_sound),
        (DEACTIVATION_SOUND, _generate_deactivation_sound),
        (ERROR_SOUND, _generate_error_sound),
    ]

    for path, generator in sounds:
        # 프로젝트 루트 기준 경로 해석
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), path
        )
        if not os.path.exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            audio = generator()
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(full_path, _RATE, audio_int16)
            log.info(f"효과음 생성: {path}")
