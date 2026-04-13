"""
텍스트 → 음성 변환 모듈
edge-tts 사용 (완전 무료, 고품질 한국어 남성 음성)
ko-KR-InJoonNeural = Microsoft의 자연스러운 한국어 남성 음성

고도화:
  - 인터럽트 지원 (재생 중 중단 가능)
  - 효과음 재생
  - 재생 상태 추적
"""
import asyncio
import edge_tts
import pygame
import tempfile
import os
import re
import threading
from typing import Optional, Callable
from config.settings import TTS_VOICE, TTS_RATE, TTS_PITCH
from utils.logger import log


class TTS:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._speaking = False
        self._interrupted = False
        self._lock = threading.Lock()

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def speak(self, text: str, on_complete: Optional[Callable] = None):
        """
        텍스트를 음성으로 출력 (동기 방식).
        on_complete: 재생 완료 또는 인터럽트 시 호출.
        """
        if not text or not text.strip():
            return

        text = re.sub(r'[*#`_\[\]()~>|]', '', text)
        text = re.sub(r'\n+', '. ', text).strip()

        log.info(f"TTS 출력: {text[:50]}...")
        self._interrupted = False
        self._speaking = True

        try:
            asyncio.run(self._async_speak(text))
        except Exception as e:
            log.error(f"TTS 오류: {e}")
        finally:
            self._speaking = False
            if on_complete:
                on_complete()

    def interrupt(self):
        """재생 중단"""
        if self._speaking:
            self._interrupted = True
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            log.info("TTS 인터럽트 - 재생 중단")

    def play_sound(self, sound_path: str):
        """효과음 재생 (짧은 wav 파일)"""
        if not os.path.exists(sound_path):
            return
        try:
            sound = pygame.mixer.Sound(sound_path)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(50)
        except Exception as e:
            log.debug(f"효과음 재생 실패: {e}")

    async def _async_speak(self, text: str):
        """비동기 TTS 실행"""
        communicate = edge_tts.Communicate(
            text,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tmp_path = f.name

        try:
            await communicate.save(tmp_path)

            if self._interrupted:
                return

            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self._interrupted:
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.05)
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
