"""
두뇌 모듈 - Claude API + MCP 연동
사용자 명령을 분석하고 적절한 스킬을 호출한다
"""
import anthropic
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS,
    GMAIL_MCP_URL, CALENDAR_MCP_URL, JARVIS_SYSTEM_PROMPT
)
from utils.logger import log


class Brain:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history = []

    def process(self, user_input: str, use_mcp: bool = True) -> str:
        """
        사용자 입력을 처리하고 응답을 반환한다
        MCP를 통해 Gmail, 캘린더에 실시간 접근
        """
        log.info(f"처리 중: {user_input}")

        # 대화 히스토리에 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # 최근 10턴만 유지
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        try:
            kwargs = {
                "model": CLAUDE_MODEL,
                "max_tokens": MAX_TOKENS,
                "system": JARVIS_SYSTEM_PROMPT,
                "messages": self.conversation_history
            }

            # MCP 서버 연결 (Gmail + 캘린더)
            if use_mcp:
                kwargs["mcp_servers"] = [
                    {
                        "type": "url",
                        "url": GMAIL_MCP_URL,
                        "name": "gmail"
                    },
                    {
                        "type": "url",
                        "url": CALENDAR_MCP_URL,
                        "name": "google-calendar"
                    }
                ]

            response = self.client.beta.messages.create(**kwargs)

            # 텍스트 응답 추출
            reply = ""
            for block in response.content:
                if block.type == "text":
                    reply += block.text

            # 대화 히스토리에 응답 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })

            log.info(f"응답 완료: {reply[:50]}...")
            return reply.strip()

        except Exception as e:
            log.error(f"Brain 처리 오류: {e}")
            return f"죄송합니다, 처리 중 오류가 발생했습니다. {str(e)}"

    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
        log.info("대화 히스토리 초기화")
