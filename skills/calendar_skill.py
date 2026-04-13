"""
Google Calendar 스킬
"""

CALENDAR_PROMPTS = {
    "today": """
Google Calendar에서 오늘 일정을 확인해줘.
시간 순서대로, 각 일정의 시간과 이름만 간결하게 말해줘.
일정이 없으면 그냥 없다고 해줘.
음성으로 읽을 것이니 자연스러운 한국어로.
""",
    "week": """
Google Calendar에서 이번 주 남은 주요 일정을 알려줘.
오늘부터 일요일까지. 날짜와 이름만.
""",
    "next": """
Google Calendar에서 다음 일정이 뭔지 알려줘.
시간과 제목만.
"""
}


def get_calendar_prompt(intent: str) -> str:
    if "주" in intent or "이번 주" in intent:
        return CALENDAR_PROMPTS["week"]
    elif "다음" in intent:
        return CALENDAR_PROMPTS["next"]
    else:
        return CALENDAR_PROMPTS["today"]
