"""
보안 관련 설정
"""
import os

# 민감 정보 로그 마스킹
MASK_SENSITIVE_LOG = True

# 로컬 저장소 경로
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "jarvis.db")
SECRETS_PATH = os.path.join(DATA_DIR, ".secrets")

# 로그에 절대 출력하지 않을 키워드 패턴
SENSITIVE_PATTERNS = [
    "password", "token", "secret", "api_key", "credentials",
    "비밀번호", "토큰", "인증"
]
