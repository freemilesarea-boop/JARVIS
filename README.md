# JARVIS - AI 음성 비서

아이언맨의 J.A.R.V.I.S 스타일 24시간 상시 대기형 AI 음성 비서

## 주요 기능

- **음성 활성화**: "자비스" 웨이크워드 또는 박수로 활성화
- **박수 제어**: 1회=활성화, 2회=대화종료, 3회=긴급정지
- **연속 대화**: 한 번 활성화 후 후속 질문 자동 대기
- **이메일**: 미읽음 확인, 요약, 음성 답장
- **일정**: Google Calendar 브리핑
- **GitHub**: PR/이슈/커밋 현황
- **OS 제어**: 앱 실행, 볼륨 조절, 브라우저 열기
- **모닝 브리핑**: 메일+일정+깃허브 통합 보고
- **24시간 대기**: 백그라운드 상시 실행, 자동 복구

## 설치

```bash
# 시스템 의존성 (Linux)
sudo apt-get install portaudio19-dev

# 시스템 의존성 (macOS)
brew install portaudio

# Python 패키지
pip install -r requirements.txt
```

## 설정

### 설정 마법사 (권장)

```bash
python launcher.py
```

### 수동 설정

1. `.env.example`을 `.env`로 복사
2. API 키 입력

```bash
cp .env.example .env
```

### API 키 발급

**Anthropic (필수)**
- https://console.anthropic.com 에서 발급

**GitHub (선택)**
- https://github.com/settings/tokens 에서 발급
- repo, notifications 권한 필요

**Email (선택 - 답장 기능)**
- Gmail 앱 비밀번호: https://myaccount.google.com/apppasswords

**Gmail + Calendar (MCP 연동)**
- Claude.ai 설정 -> Connectors에서 Gmail, Google Calendar 연결

## 실행

```bash
python main.py
```

## 사용법

### 활성화
- "자비스" 라고 말하기
- 박수 한 번 치기

### 대화 종료
- 박수 두 번 치기
- 15초 무응답 시 자동 종료

### 긴급 정지
- 박수 세 번 치기

### 명령어 예시

| 명령 | 동작 |
|------|------|
| "메일 확인해줘" | 미읽음 메일 요약 |
| "메일 답장해줘" | 음성 답장 워크플로 |
| "오늘 일정 알려줘" | 캘린더 브리핑 |
| "모닝 브리핑 해줘" | 통합 브리핑 |
| "깃허브 PR 상황" | GitHub 현황 |
| "크롬 열어줘" | 앱 실행 |
| "볼륨 올려줘" | 시스템 볼륨 제어 |
| "몇 시야?" | 현재 시각 |
| "5분 타이머" | 타이머 설정 |
| "자동 시작 설정해줘" | OS 시작 시 자동 실행 |
| "종료해줘" | JARVIS 종료 |

## 프로젝트 구조

```
jarvis/
├── main.py                    # 메인 실행 (상태 머신 통합)
├── launcher.py                # 설정 마법사
├── config/
│   ├── settings.py            # 전역 설정
│   ├── audio_config.py        # 오디오 설정
│   └── security.py            # 보안 설정
├── core/
│   ├── state_machine.py       # 상태 머신 (IDLE/LISTENING/...)
│   ├── session_manager.py     # 대화 세션 관리
│   ├── conversation_manager.py # 대화 맥락 관리
│   ├── interrupt_handler.py   # 인터럽트 처리
│   ├── wake_word.py           # 웨이크워드 감지
│   ├── clap_detector.py       # 박수 감지 (1/2/3회)
│   ├── stt.py                 # 음성 -> 텍스트
│   ├── tts.py                 # 텍스트 -> 음성
│   ├── brain.py               # Claude API + MCP
│   └── watchdog.py            # 장시간 안정성 감시
├── services/
│   ├── email_service.py       # IMAP/SMTP 이메일
│   ├── os_control_service.py  # OS 제어 (볼륨/파일/잠금)
│   ├── app_launcher_service.py # 앱 실행/종료
│   └── startup_service.py     # OS 자동 시작
├── skills/
│   ├── gmail_skill.py         # Gmail 프롬프트
│   ├── calendar_skill.py      # Calendar 프롬프트
│   ├── github_skill.py        # GitHub 연동
│   ├── briefing_skill.py      # 통합 브리핑
│   ├── mail_reply_skill.py    # 메일 답장 워크플로
│   ├── system_skill.py        # 시스템 제어 명령
│   └── productivity_skill.py  # 시간/타이머/메모
├── storage/
│   ├── db.py                  # SQLite 로컬 저장
│   ├── memory_store.py        # 인메모리 캐시
│   └── secrets_store.py       # 시크릿 저장
├── ui/
│   ├── overlay.py             # 상태 표시
│   ├── tray_app.py            # 시스템 트레이
│   └── sounds.py              # 효과음 생성
└── utils/
    ├── logger.py              # 로그 시스템
    ├── audio.py               # 오디오 유틸
    ├── retry.py               # 재시도 유틸
    └── validators.py          # 입력 검증
```
