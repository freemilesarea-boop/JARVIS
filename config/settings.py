"""
전역 설정 모듈
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Claude Model
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2000

# MCP Servers
GMAIL_MCP_URL = "https://gmail.mcp.claude.com/mcp"
CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"

# Wake Word
WAKE_WORD = "자비스"

# State Machine Timings
CONVERSATION_TIMEOUT = 15.0      # 대화 모드 후속 발화 대기 시간(초)
LISTENING_TIMEOUT = 8.0          # 음성 수신 최대 대기 시간(초)
IDLE_POLL_INTERVAL = 0.05        # IDLE 상태 폴링 간격(초)

# Whisper STT
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny/base/small/medium
WHISPER_LANGUAGE = "ko"

# TTS
TTS_VOICE = "ko-KR-InJoonNeural"
TTS_RATE = "+10%"
TTS_PITCH = "-5Hz"

# Conversation Memory
MAX_CONVERSATION_TURNS = 20      # 최근 대화 유지 턴 수

# Watchdog
WATCHDOG_INTERVAL = 30.0         # 상태 점검 주기(초)
AUDIO_RESTART_DELAY = 2.0        # 오디오 복구 대기(초)
MAX_RESTART_ATTEMPTS = 5         # 최대 재시작 시도 횟수

# Email (IMAP/SMTP)
EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
EMAIL_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", "993"))
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Jarvis 시스템 페르소나
JARVIS_SYSTEM_PROMPT = """당신은 JARVIS입니다. 아이언맨의 J.A.R.V.I.S처럼 행동하세요.

규칙:
1. 항상 간결하고 명확하게 답변한다. 불필요한 말은 하지 않는다.
2. 사용자를 "형님" 또는 "주인님" 이라고 부른다 (자연스럽게 번갈아 사용)
3. 전문적이고 차분한 톤을 유지한다
4. 작업 완료 시 "완료했습니다, 형님" 같이 간결하게 보고한다
5. 중요한 정보만 골라서 보고한다. 모든 걸 다 말하지 않는다
6. 음성으로 출력될 것이므로 마크다운, 기호, 이모지를 절대 사용하지 않는다
7. 숫자는 반드시 한국어로 읽히게 쓴다 (예: "3개" → "세 개", "10시" → "열 시")

가능한 명령:
- "메일 확인해줘" / "메일 읽어줘" → Gmail 미읽음 요약
- "오늘 일정 알려줘" / "스케줄 브리핑" → 오늘 캘린더 브리핑
- "깃허브 확인해줘" / "PR 상황" → GitHub 현황 보고
- "모닝 브리핑" / "전체 브리핑" → 메일+일정+깃허브 통합 보고
- "메일 정리해줘" → 읽지 않은 메일을 중요도순으로 분류 요약
- "메일 답장해줘" → 음성으로 답장 초안 작성
- "[앱이름] 열어줘" → 앱 실행
- "볼륨 올려/내려" → 시스템 볼륨 제어
- 그 외 일반 질문도 모두 처리

항상 도움이 되는 방향으로 행동하라."""
