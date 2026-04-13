"""
텍스트 → 음성 변환 모듈
edge-tts 사용 (완전 무료, 고품질 한국어 남성 음성)
ko-KR-InJoonNeural = Microsoft의 자연스러운 한국어 남성 음성

오디오 재생: subprocess 기반 (pygame 미사용)
  - macOS: afplay
  - Linux: mpg123 / aplay
  - Windows: PowerShell Media.SoundPlayer

고도화:
  - 인터럽트 지원 (재생 중 중단 가능)
  - 효과음 재생
  - 재생 상태 추적
"""
import asyncio
import edge_tts
import subprocess
import platform
import tempfile
import os
import re
import signal
import threading
from typing import Optional, Callable
from config.settings import TTS_VOICE, TTS_RATE, TTS_PITCH
from utils.logger import log

_SYSTEM = platform.system()


class TTS:
    def __init__(self):
        self._speaking = False
        self._interrupted = False
        self._process: Optional[subprocess.Popen] = None
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
            self._kill_player()
            log.info("TTS 인터럽트 - 재생 중단")

    def play_sound(self, sound_path: str):
        """효과음 재생 (짧은 wav 파일)"""
        if not os.path.exists(sound_path):
            return
        try:
            self._play_file(sound_path)
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

            self._play_file(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _play_file(self, path: str):
        """OS별 오디오 파일 재생 (블로킹, 인터럽트 가능)"""
        try:
            if _SYSTEM == "Darwin":
                self._process = subprocess.Popen(
                    ["afplay", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif _SYSTEM == "Linux":
                if path.endswith(".mp3"):
                    self._process = subprocess.Popen(
                        ["mpg123", "-q", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    self._process = subprocess.Popen(
                        ["aplay", "-q", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif _SYSTEM == "Windows":
                # PowerShell로 재생
                ps_cmd = (
                    f'(New-Object Media.SoundPlayer "{path}").PlaySync()'
                )
                self._process = subprocess.Popen(
                    ["powershell", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                log.warning(f"지원하지 않는 OS: {_SYSTEM}")
                return

            # 재생 완료 대기 (인터럽트 체크)
            while self._process.poll() is None:
                if self._interrupted:
                    self._kill_player()
                    return
                import time
                time.sleep(0.05)

        except FileNotFoundError as e:
            log.error(
                f"오디오 플레이어를 찾을 수 없습니다: {e}. "
                f"Linux의 경우 'sudo apt install mpg123'을 실행해주세요."
            )
        except Exception as e:
            log.error(f"오디오 재생 오류: {e}")
        finally:
            self._process = None

    def _kill_player(self):
        """재생 프로세스 강제 종료"""
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=1.0)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
