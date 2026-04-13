"""
입력 검증 유틸리티
"""
import re
import os
from typing import Optional


def validate_api_key(key: Optional[str], prefix: str = "sk-ant-") -> bool:
    """API 키 형식 검증"""
    if not key:
        return False
    return key.startswith(prefix) and len(key) > len(prefix) + 5


def validate_email(email: str) -> bool:
    """이메일 주소 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_file_path(path: str) -> bool:
    """파일 경로 존재 여부 검증"""
    return os.path.exists(path)


def sanitize_for_speech(text: str) -> str:
    """
    음성 출력을 위한 텍스트 정리.
    마크다운, 특수문자, URL 등을 제거.
    """
    # URL 제거
    text = re.sub(r'https?://\S+', '', text)
    # 마크다운 제거
    text = re.sub(r'[*#`_\[\]()~>|{}]', '', text)
    # 연속 공백 정리
    text = re.sub(r'\s+', ' ', text)
    # 연속 마침표 정리
    text = re.sub(r'\.{2,}', '.', text)
    return text.strip()
