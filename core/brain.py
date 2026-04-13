"""
두뇌 모듈 - Claude API + MCP 연동
사용자 명령을 분석하고 적절한 스킬을 호출한다.
ConversationManager와 연동하여 대화 맥락을 유지한다.
"""
import os
import sys
import anthropic
from typing import Optional
from core.conversation_manager import ConversationManager
from config.settings import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS,
    GMAIL_MCP_URL, CALENDAR_MCP_URL, JARVIS_SYSTEM_PROMPT
)
from utils.logger import log

# Python 전역 인코딩을 UTF-8로 강제 (한국어 처리)
if sys.stdout.encoding != "utf-8":
    os.environ["PYTHONIOENCODING"] = "utf-8"


class Brain:
    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation = conversation_manager or ConversationManager()

    def process(self, user_input: str, use_mcp: bool = True) -> str:
        """
        사용자 입력을 처리하고 응답을 반환한다.
        - use_mcp=False: 표준 messages API 사용
        - use_mcp=True: beta messages API + MCP 서버
        """
        log.info(f"처리 중: {user_input}")

        self.conversation.add_user_message(user_input)

        try:
            kwargs = {
                "model": CLAUDE_MODEL,
                "max_tokens": MAX_TOKENS,
                "system": JARVIS_SYSTEM_PROMPT,
                "messages": self.conversation.get_messages_for_api(),
            }

            if use_mcp:
                # MCP 연동은 beta API 필요
                kwargs["mcp_servers"] = [
                    {
                        "type": "url",
                        "url": GMAIL_MCP_URL,
                        "name": "gmail",
                    },
                    {
                        "type": "url",
                        "url": CALENDAR_MCP_URL,
                        "name": "google-calendar",
                    },
                ]
                response = self.client.beta.messages.create(**kwargs)
            else:
                # 일반 대화는 표준 API 사용
                response = self.client.messages.create(**kwargs)

            reply = ""
            for block in response.content:
                if block.type == "text":
                    reply += block.text

            self.conversation.add_assistant_message(reply)

            log.info(f"응답 완료: {reply[:50]}...")
            return reply.strip()

        except anthropic.AuthenticationError:
            log.error("Anthropic API 키가 유효하지 않습니다.")
            return "API 키가 유효하지 않습니다. .env 파일을 확인해주세요, 형님."

        except anthropic.RateLimitError:
            log.error("API 요청 한도 초과")
            return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요, 형님."

        except Exception as e:
            log.error(f"Brain 처리 오류: {type(e).__name__}: {e}")
            return "죄송합니다, 처리 중 오류가 발생했습니다."

    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation.clear_history()
