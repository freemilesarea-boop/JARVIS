"""
Gmail 스킬 - 메일 읽기/요약/정리를 위한 프롬프트 생성
실제 Gmail API 호출은 Brain의 MCP를 통해 처리됨
"""

GMAIL_PROMPTS = {
    "unread": """
Gmail에서 읽지 않은 메일을 확인하고 중요도 순으로 상위 5개를 요약해줘.
각 메일에 대해: 발신자, 제목, 한줄 요약만 말해줘.
긴급한 것이 있으면 먼저 알려줘.
음성으로 읽을 것이니 번호 없이 자연스러운 한국어로 말해줘.
""",
    "organize": """
Gmail에서 읽지 않은 메일을 확인하고 다음으로 분류해서 보고해줘:
1. 즉시 처리 필요 (오늘 안에)
2. 이번 주 안에 처리
3. 참고만 하면 되는 것
각 항목당 2개 이하로만 말해줘. 간결하게.
""",
    "latest": """
Gmail에서 가장 최근에 온 메일 3개를 읽어줘.
발신자와 핵심 내용만 간단히.
"""
}


def get_gmail_prompt(intent: str) -> str:
    """의도에 따른 Gmail 프롬프트 반환"""
    if "정리" in intent or "분류" in intent:
        return GMAIL_PROMPTS["organize"]
    elif "최근" in intent or "방금" in intent:
        return GMAIL_PROMPTS["latest"]
    else:
        return GMAIL_PROMPTS["unread"]
