"""
통합 모닝 브리핑 스킬
Gmail + 캘린더 + GitHub를 합쳐서 브리핑
"""
from skills.github_skill import GitHubSkill
from datetime import datetime


def get_morning_briefing_prompt() -> str:
    """모닝 브리핑 통합 프롬프트"""
    now = datetime.now()
    weekday = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][now.weekday()]

    return f"""
오늘은 {now.month}월 {now.day}일 {weekday}입니다.

다음 순서로 간결한 모닝 브리핑을 해줘:

1. Gmail에서 읽지 않은 중요 메일 상위 3개 요약 (발신자와 핵심만)
2. Google Calendar에서 오늘 일정 전체 (시간과 이름만)
3. "이상입니다. 좋은 하루 되세요, 형님" 으로 마무리

전체 브리핑이 1분 이내로 끝나게 간결하게.
음성으로 읽을 것이니 마크다운, 기호, 숫자 목록 없이 자연스러운 한국어로.
"""


def get_full_briefing_with_github(github_skill: GitHubSkill) -> tuple[str, str]:
    """
    프롬프트와 GitHub 브리핑을 별도로 반환
    Returns: (claude_prompt, github_text)
    """
    github_text = github_skill.get_briefing()
    claude_prompt = get_morning_briefing_prompt()
    return claude_prompt, github_text
