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
        log.info(
            f"  [{i}] {device['name']} "
            f"(in:{device['max_input_channels']}, out:{device['max_output_channels']})"
        )


def test_microphone() -> bool:
    """마이크 테스트"""
    import numpy as np
    log.info("마이크 테스트 중... 3초간 측정")
    try:
        data = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32')
        sd.wait()
        rms = np.sqrt(np.mean(data ** 2))
        log.info(f"마이크 RMS 레벨: {rms:.4f}")
        return rms > 0.001
    except Exception as e:
        log.error(f"마이크 테스트 실패: {e}")
        return False


def get_input_devices() -> list[dict]:
    """입력 장치 목록 반환"""
    devices = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
        for i, d in enumerate(devices)
        if d["max_input_channels"] > 0
    ]


def get_output_devices() -> list[dict]:
    """출력 장치 목록 반환"""
    devices = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "channels": d["max_output_channels"]}
        for i, d in enumerate(devices)
        if d["max_output_channels"] > 0
    ]
