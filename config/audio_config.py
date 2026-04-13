"""
오디오 관련 설정
"""

# 마이크 입력
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5             # seconds per audio chunk

# 박수 감지
CLAP_THRESHOLD = 0.35            # 박수 감지 피크 임계값
CLAP_RMS_THRESHOLD = 0.15        # 박수 RMS 임계값 (추가 검증)
CLAP_MIN_INTERVAL = 0.15         # 박수 간 최소 간격(초) - 너무 빠르면 잡음
CLAP_MAX_INTERVAL = 0.8          # 박수 간 최대 간격(초)
CLAP_IMPULSE_MAX_DURATION = 0.08 # 임펄스 최대 지속 시간(초) - 박수는 짧다
CLAP_COOLDOWN = 1.5              # 박수 패턴 인식 후 쿨다운(초)

# 음성 활동 감지 (VAD)
VAD_SILENCE_THRESHOLD = 0.01     # 침묵 판정 RMS 임계값
VAD_SILENCE_DURATION = 1.5       # 발화 종료 판정 침묵 시간(초)
VAD_MIN_SPEECH_DURATION = 0.3    # 최소 발화 시간(초) - 이보다 짧으면 무시

# 오디오 출력
ACTIVATION_SOUND = "ui/sounds/activate.wav"
DEACTIVATION_SOUND = "ui/sounds/deactivate.wav"
ERROR_SOUND = "ui/sounds/error.wav"
