# JARVIS - AI 음성 비서

아이언맨의 J.A.R.V.I.S 스타일 AI 음성 비서

## 설치

```bash
pip install -r requirements.txt
```

## 설정

1. `.env.example`을 복사해서 `.env` 생성
2. 각 API 키 입력

### API 키 발급

**Anthropic (필수)**
- https://console.anthropic.com 에서 발급

**GitHub (선택)**
- https://github.com/settings/tokens 에서 발급
- repo, notifications 권한 필요

**Gmail + 캘린더 (Claude.ai 계정 연결)**
- Claude.ai 설정 -> Connectors에서 Gmail, Google Calendar 연결
- 연결 후 자동으로 MCP를 통해 접근 가능

## 실행

```bash
python main.py
```

## 사용법

1. **"자비스"** 라고 말하면 활성화
2. **박수 두 번** 쳐도 활성화
3. 명령 후 자동으로 응답

## 명령어 예시

- "자비스, 메일 확인해줘"
- "자비스, 오늘 일정 알려줘"
- "자비스, 모닝 브리핑 해줘"
- "자비스, 깃허브 PR 상황 알려줘"
- "자비스, 종료해줘"
