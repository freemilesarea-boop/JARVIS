"""
텍스트 → 음성 변환 모듈
edge-tts 사용 (완전 무료, 고품질 한국어 남성 음성)
ko-KR-InJoonNeural = Microsoft의 자연스러운 한국어 남성 음성
"""
import asyncio
import edge_tts
import pygame
import tempfile
import os
import re
from config import TTS_VOICE, TTS_RATE, TTS_PITCH
from utils.logger import log


class TTS:
    def __init__(self):
        pygame.mixer.init()

    def speak(self, text: str):
        """텍스트를 음성으로 출력 (동기 방식)"""
        if not text or not text.strip():
            return

        # 마크다운 제거
        text = re.sub(r'[*#`_\[\]()~>|]', '', text)
        text = re.sub(r'\n+', '. ', text).strip()

        log.info(f"TTS 출력: {text[:50]}...")
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str):
        """비동기 TTS 실행"""
        communicate = edge_tts.Communicate(
            text,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tmp_path = f.name

        try:
            await communicate.save(tmp_path)
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        finally:
            pygame.mixer.music.unload()
            os.unlink(tmp_path)
