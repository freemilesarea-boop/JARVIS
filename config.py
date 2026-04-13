import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5        # seconds per audio chunk
WAKE_WORD = "자비스"
CLAP_THRESHOLD = 0.35       # 박수 감지 민감도
CLAP_DOUBLE_WINDOW = 0.8    # 더블박수 인식 시간(초)

# STT
WHISPER_MODEL = "base"       # tiny/base/small/medium
WHISPER_LANGUAGE = "ko"

# TTS
TTS_VOICE = "ko-KR-InJoonNeural"   # 무료 남성 한국어 음성 (Microsoft Edge TTS)
TTS_RATE = "+10%"                   # 말하기 속도
TTS_PITCH = "-5Hz"                  # 낮고 중후한 톤

# MCP Servers
GMAIL_MCP_URL = "https://gmail.mcp.claude.com/mcp"
CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"

# Claude Model
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2000

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
- 그 외 일반 질문도 모두 처리

항상 도움이 되는 방향으로 행동하라."""
