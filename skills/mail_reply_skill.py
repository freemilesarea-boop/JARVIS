"""
메일 답장 스킬
음성으로 답장 초안을 작성하고 확인 후 전송한다.

시나리오:
  1. "최근 메일 읽어줘" → 메일 요약
  2. "두 번째 메일 답장해" → 컨텍스트 설정
  3. 사용자가 답장 내용 구술
  4. 자비스가 초안 낭독
  5. "보내" 명령 시 전송
"""
from typing import Optional
from services.email_service import EmailService, EmailMessage
from utils.logger import log


class MailReplySkill:
    """메일 답장 워크플로 관리"""

    def __init__(self, email_service: EmailService):
        self.email = email_service
        self._cached_mails: list[EmailMessage] = []
        self._reply_target: Optional[EmailMessage] = None
        self._draft: Optional[str] = None

    def fetch_and_summarize(self, count: int = 5) -> str:
        """미읽음 메일 조회 및 요약"""
        mails = self.email.get_unread_mails(count)
        self._cached_mails = mails

        if not mails:
            return "읽지 않은 메일이 없습니다."

        lines = [f"읽지 않은 메일이 {len(mails)}건 있습니다."]
        for i, m in enumerate(mails, 1):
            lines.append(
                f"{self._number_to_korean(i)}번째, "
                f"{m.sender}님으로부터, 제목: {m.subject}"
            )

        return " ".join(lines)

    def select_mail_for_reply(self, index: int) -> str:
        """답장할 메일 선택"""
        if not self._cached_mails:
            return "먼저 메일을 확인해주세요."

        if index < 1 or index > len(self._cached_mails):
            return f"잘못된 번호입니다. 하나에서 {len(self._cached_mails)} 사이의 번호를 말씀해주세요."

        self._reply_target = self._cached_mails[index - 1]
        self._draft = None
        return (
            f"{self._reply_target.sender}님의 "
            f"'{self._reply_target.subject}' 메일에 답장합니다. "
            f"답장할 내용을 말씀해주세요."
        )

    def set_draft(self, content: str) -> str:
        """답장 초안 설정"""
        if not self._reply_target:
            return "답장할 메일이 선택되지 않았습니다."

        self._draft = content
        return (
            f"초안을 읽어드리겠습니다. {content}. "
            f"이대로 보내시겠습니까? '보내' 또는 '다시' 라고 말씀해주세요."
        )

    def send_draft(self) -> str:
        """초안 전송"""
        if not self._reply_target or not self._draft:
            return "전송할 초안이 없습니다."

        success = self.email.send_reply(self._reply_target, self._draft)

        if success:
            target = self._reply_target.sender
            self._reply_target = None
            self._draft = None
            return f"{target}님에게 답장을 전송했습니다."
        else:
            return "답장 전송에 실패했습니다. 이메일 설정을 확인해주세요."

    def cancel_reply(self):
        """답장 취소"""
        self._reply_target = None
        self._draft = None

    @property
    def is_replying(self) -> bool:
        return self._reply_target is not None

    @property
    def has_draft(self) -> bool:
        return self._draft is not None

    @staticmethod
    def _number_to_korean(n: int) -> str:
        korean = ["", "첫", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열"]
        if 1 <= n <= 10:
            return korean[n]
        return str(n)
