# Email Agent 설치 가이드

## 요구사항

- Python 3.10+
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Google Cloud Project (Gmail API, Sheets API 활성화)

## 설치 순서

### 1. 저장소 클론

```bash
git clone <repository-url>
cd email_agent
```

### 2. Python 환경 설정

**uv 사용 (권장):**
```bash
# uv 설치 (최초 1회)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치 (가상환경 자동 생성)
uv sync
```

**pip 사용:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Google API 인증

```bash
# credentials.json을 프로젝트 루트에 배치
# 최초 실행 시 브라우저에서 OAuth 인증

# uv 사용자
uv run python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"

# pip 사용자
python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"
```

### 4. 사용 방법

```bash
# 프로젝트 디렉토리에서 Claude Code 실행
cd /path/to/email_agent
claude

# 이메일 분석 + 초안 생성
> 이메일 분석하고 초안 만들어줘

# 또는 슬래시 명령어
> /email-analyze   # 분석만
> /email-draft     # 초안 생성
> /email-send      # 발송
```

### 5. 자동 실행 설정 (선택)

```bash
# cron에 등록 (매일 오전 8시)
crontab -e

# 아래 줄 추가
0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh
```

## 파일 구조

```
email_agent/
├── email_classifier/
│   ├── gmail_client.py    # Gmail API
│   └── sheets_client.py   # Sheets API
├── .claude/commands/
│   ├── email-analyze.md   # /email-analyze
│   ├── email-draft.md     # /email-draft
│   └── email-send.md      # /email-send
├── scripts/
│   └── daily_email_analyze.sh  # cron 스크립트
├── credentials.json       # Google OAuth (직접 생성)
└── token.json            # OAuth 토큰 (자동 생성)
```

## 주의사항

- `credentials.json`과 `token.json`은 git에 커밋하지 마세요
- 첫 실행 시 브라우저에서 Google 계정 인증 필요
- cron 실행 시 로그는 `logs/` 디렉토리에 저장됨
