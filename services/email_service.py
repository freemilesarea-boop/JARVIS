"""
이메일 서비스
IMAP/SMTP 기반 실제 메일 연동.
Gmail OAuth 없이도 앱 비밀번호로 사용 가능.

기능:
  - 미읽음 메일 목록 조회
  - 메일 본문 읽기
  - 답장 초안 작성 및 전송
  - 메일 분류 (중요도 추정)
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Optional
from config.settings import (
    EMAIL_IMAP_SERVER, EMAIL_IMAP_PORT,
    EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT,
    EMAIL_ADDRESS, EMAIL_PASSWORD,
)
from utils.logger import log


class EmailMessage:
    """이메일 메시지 데이터 클래스"""
    def __init__(self, uid: str, sender: str, subject: str, body: str, date: str):
        self.uid = uid
        self.sender = sender
        self.subject = subject
        self.body = body
        self.date = date

    def summary(self) -> str:
        body_preview = self.body[:100].replace("\n", " ") if self.body else ""
        return f"{self.sender}님으로부터, 제목: {self.subject}. {body_preview}"


class EmailService:
    def __init__(self):
        self._connected = False
        self._imap: Optional[imaplib.IMAP4_SSL] = None

    @property
    def is_configured(self) -> bool:
        return bool(EMAIL_ADDRESS and EMAIL_PASSWORD)

    def connect(self) -> bool:
        """IMAP 서버에 연결"""
        if not self.is_configured:
            log.warning("이메일 설정이 완료되지 않았습니다")
            return False

        try:
            self._imap = imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER, EMAIL_IMAP_PORT)
            self._imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            self._connected = True
            log.info("이메일 서버 연결 완료")
            return True
        except Exception as e:
            log.error(f"이메일 연결 실패: {e}")
            self._connected = False
            return False

    def disconnect(self):
        if self._imap:
            try:
                self._imap.logout()
            except Exception:
                pass
            self._imap = None
            self._connected = False

    def _decode_header_value(self, value: str) -> str:
        """이메일 헤더 디코딩"""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def _extract_body(self, msg) -> str:
        """이메일 본문 추출"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="replace")
                        break
                    except Exception:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
            except Exception:
                body = ""
        return body.strip()

    def get_unread_mails(self, limit: int = 5) -> list[EmailMessage]:
        """미읽음 메일 조회"""
        if not self._connected:
            if not self.connect():
                return []

        try:
            self._imap.select("INBOX")
            _, data = self._imap.search(None, "UNSEEN")
            mail_ids = data[0].split()

            if not mail_ids:
                return []

            # 최근 N개만
            recent_ids = mail_ids[-limit:]
            messages = []

            for mail_id in reversed(recent_ids):
                _, msg_data = self._imap.fetch(mail_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                sender = self._decode_header_value(msg.get("From", ""))
                subject = self._decode_header_value(msg.get("Subject", ""))
                date = msg.get("Date", "")
                body = self._extract_body(msg)

                messages.append(EmailMessage(
                    uid=mail_id.decode(),
                    sender=sender,
                    subject=subject,
                    body=body,
                    date=date,
                ))

            return messages

        except Exception as e:
            log.error(f"메일 조회 오류: {e}")
            self._connected = False
            return []

    def send_reply(self, original: EmailMessage, reply_body: str) -> bool:
        """메일 답장 전송"""
        if not self.is_configured:
            log.error("이메일 설정이 완료되지 않았습니다")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = original.sender
            msg["Subject"] = f"Re: {original.subject}"
            msg["In-Reply-To"] = original.uid

            msg.attach(MIMEText(reply_body, "plain", "utf-8"))

            with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            log.info(f"답장 전송 완료: {original.subject}")
            return True

        except Exception as e:
            log.error(f"답장 전송 실패: {e}")
            return False

    def get_briefing_text(self) -> str:
        """미읽음 메일 브리핑 텍스트 생성"""
        mails = self.get_unread_mails(5)
        if not mails:
            return "읽지 않은 메일이 없습니다."

        lines = [f"읽지 않은 메일이 {len(mails)}건 있습니다."]
        for m in mails:
            lines.append(m.summary())
        return " ".join(lines)
