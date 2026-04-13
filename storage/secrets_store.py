"""
시크릿 저장소
API 키, 비밀번호 등 민감 정보를 안전하게 저장/로드한다.
base64 인코딩 + 파일 권한 제한 기반 기본 보호.
"""
import os
import json
import base64
from typing import Optional
from config.security import DATA_DIR, SECRETS_PATH
from utils.logger import log


class SecretsStore:
    """
    민감 정보를 로컬 파일에 저장한다.
    base64 인코딩으로 기본 난독화 적용.
    """

    def __init__(self, path: str = SECRETS_PATH):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._path = path
        self._data: dict = {}
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    encoded = f.read().strip()
                    if encoded:
                        decoded = base64.b64decode(encoded).decode("utf-8")
                        self._data = json.loads(decoded)
            except Exception as e:
                log.error(f"시크릿 로드 실패: {e}")
                self._data = {}

    def _save(self):
        try:
            raw = json.dumps(self._data, ensure_ascii=False)
            encoded = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
            with open(self._path, "w") as f:
                f.write(encoded)
            # 파일 권한 제한 (소유자만 읽기/쓰기)
            os.chmod(self._path, 0o600)
        except Exception as e:
            log.error(f"시크릿 저장 실패: {e}")

    def set(self, key: str, value: str):
        self._data[key] = value
        self._save()

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)

    def delete(self, key: str):
        if key in self._data:
            del self._data[key]
            self._save()

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> list[str]:
        return list(self._data.keys())
