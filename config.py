"""
호환성 심 - 기존 'from config import ...' 구문 지원
새 코드는 config.settings, config.audio_config, config.security를 직접 임포트.
"""
from config.settings import *
from config.audio_config import *
from config.security import *
