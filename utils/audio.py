"""
오디오 유틸리티
"""
import sounddevice as sd
from utils.logger import log


def list_audio_devices():
    """사용 가능한 오디오 장치 목록"""
    devices = sd.query_devices()
    log.info("사용 가능한 오디오 장치:")
    for i, device in enumerate(devices):
        log.info(f"  [{i}] {device['name']} (in:{device['max_input_channels']}, out:{device['max_output_channels']})")


def test_microphone():
    """마이크 테스트"""
    import numpy as np
    log.info("마이크 테스트 중... 3초간 측정")
    data = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    rms = np.sqrt(np.mean(data**2))
    log.info(f"마이크 RMS 레벨: {rms:.4f}")
    return rms > 0.001
