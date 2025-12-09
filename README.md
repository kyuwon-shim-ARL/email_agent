# Email Agent v0.6.2

**Claude Code 슬래시 명령어로 Gmail 이메일을 자동 분류하고 답장 초안을 생성하는 도구**

## 핵심 특징

- **API 비용 $0** - Claude Code 대화로 AI 처리
- **슬래시 명령어** - `/email-analyze`, `/email-draft`, `/email-send`
- **Gmail 초안 자동 생성** - 분석 시 초안 자동 생성 → 임시보관함에서 바로 확인
- **통합 스프레드시트** - 신규 메일 + 처리 이력 탭으로 관리
- **수신유형 기반 우선순위** - To/CC/그룹메일에 따른 자동 조정
- **답장 여부 자동 체크** - Gmail Thread API로 답장 상태 확인

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/email_agent.git
cd email_agent
```

### 2. Python 환경 설정

```bash
python -m venv ~/.venv
source ~/.venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Google API 설정

1. [Google Cloud Console](https://console.cloud.google.com)에서 프로젝트 생성
2. Gmail API + Google Sheets API 활성화
3. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
4. `credentials.json` 다운로드 → 프로젝트 루트에 배치

**필요한 OAuth 스코프:**
- `gmail.readonly` - 이메일 읽기
- `gmail.compose` - 초안 작성
- `gmail.send` - 발송
- `gmail.modify` - 라벨 관리
- `spreadsheets` - Sheets 읽기/쓰기

### 4. 최초 인증

```bash
~/.venv/bin/python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"
# 브라우저에서 Google 계정 로그인 → 권한 승인
```

### 5. Claude Code 실행

```bash
# Claude Code CLI 설치 (최초 1회)
npm install -g @anthropic-ai/claude-code

# 프로젝트 디렉토리에서 실행
cd email_agent
claude
```

---

## 사용 방법

### 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/email-analyze` | 이메일 분석 + Sheets 기록 + Gmail 초안 자동 생성 |
| `/email-draft` | 스프레드시트 수정 후 추가 초안 생성 |
| `/email-send` | 전송예정 체크된 항목 일괄 발송 |

### 기본 워크플로우

```
/email-analyze
    ↓
📊 스프레드시트 업데이트 (신규 메일 + 처리 이력)
📝 Gmail 초안 자동 생성 (답장필요 + 초안내용 있는 항목)
📧 요약 보고서 발송
    ↓
사용자: Gmail 임시보관함에서 초안 확인/수정 → 발송
    ↓
(선택) 스프레드시트에서 추가 초안 작성 → /email-draft
    ↓
(선택) /email-send → 일괄 발송
```

### 예시

```bash
# Claude Code에서
> /email-analyze

# 출력:
# 📬 8개 이메일 로드 (처리완료 제외)
# === 이메일 1 ===
# 제목: 회의 일정 확인
# 발신자: manager@company.com
# 수신유형: 📩 직접수신
# ...

# 분석 완료 후:
# ✅ Gmail 초안 3개 생성 완료 (임시보관함에서 확인)
# 📧 요약 보고서 발송 완료!
```

---

## 스프레드시트 구조

### 탭 구성

```
📚 Email History (누적 이력)
├── [신규 메일] - 오늘 분석한 이메일 (매 분석 시 초기화)
└── [처리 이력] - 전체 누적 이력 (중복 시 업데이트)
```

### 16열 컬럼

| 열 | 이름 | 설명 |
|----|------|------|
| A | 상태 | 답장필요/답장불필요/답장완료 |
| B | 우선순위 | 1-5 (조건부 색상) |
| C | 라벨 | Gmail 라벨 |
| D | 제목 | 이메일 제목 |
| E | 발신자 | 이름 <email> |
| F | 받은CC | CC 수신자 |
| G | 받은시간 | 수신 일시 |
| H | 내용미리보기 | 본문 300자 (HTML 제거) |
| I | AI요약 | 3줄 MECE 요약 |
| J | 초안(제목) | 답장 제목 |
| K | 초안(내용) | 답장 본문 |
| L | 보낼CC | 발송 시 CC |
| M | 전송예정 | 체크박스 |
| N | 답장여부 | 답장함/미답장 |
| O | Draft ID | Gmail 초안 ID |
| P | Thread ID | Gmail Thread ID |

---

## 우선순위 기준

| 점수 | 레벨 | 기준 |
|------|------|------|
| P5 | 최우선 | 직속상관, 긴급 키워드, 마감 24시간 내 |
| P4 | 긴급 | 중요 발신자, 액션 요청, 마감 1주 내 |
| P3 | 보통 | 일반 업무, 참조용 |
| P2 | 낮음 | 공지사항, FYI |
| P1 | 최저 | 자동메일, 뉴스레터, 광고 |

### 수신유형별 조정

| 수신유형 | 조정 |
|----------|------|
| 📩 직접수신 (To) | 유지 |
| 📋 참조 (CC) | -1 |
| 👥 그룹메일 | -1 |

---

## 파일 구조

```
email_agent/
├── email_classifier/
│   ├── gmail_client.py       # Gmail API 클라이언트
│   └── sheets_client.py      # Sheets API 클라이언트
├── .claude/commands/
│   ├── email-analyze.md      # /email-analyze 명령어
│   ├── email-draft.md        # /email-draft 명령어
│   └── email-send.md         # /email-send 명령어
├── scripts/
│   └── daily_email_analyze.sh  # cron 자동화 스크립트
├── credentials.json          # Google OAuth (직접 생성)
├── token.json               # OAuth 토큰 (자동 생성)
├── email_history_config.json # 스프레드시트 ID (자동 생성)
├── requirements.txt          # Python 의존성
└── README.md
```

---

## 자동화 (선택)

### Cron 설정 (매일 8시)

```bash
crontab -e

# 아래 줄 추가
0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh
```

### 스크립트 내용

```bash
#!/bin/bash
cd /path/to/email_agent
LOG_FILE="logs/daily_analyze_$(date +%Y%m%d).log"
mkdir -p logs
echo "=== Started: $(date) ===" >> "$LOG_FILE"
claude -p "이메일 분석해줘" --dangerously-skip-permissions >> "$LOG_FILE" 2>&1
echo "=== Completed: $(date) ===" >> "$LOG_FILE"
```

---

## 문제 해결

### credentials.json not found

```bash
# Google Cloud Console에서 다운로드 후 복사
cp ~/Downloads/client_secret_*.json ./credentials.json
```

### 권한 오류 (403)

```bash
# token.json 삭제 후 재인증
rm token.json
~/.venv/bin/python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"
```

### 스프레드시트가 안 보임

최초 `/email-analyze` 실행 시 자동 생성됩니다. 생성된 URL은 요약 보고서 이메일에서 확인 가능.

---

## 보안

- `credentials.json`, `token.json`, `email_history_config.json`은 `.gitignore`에 포함
- OAuth 토큰은 로컬에만 저장
- 초안은 자동 전송되지 않음 (직접 검토 후 발송)

---

## 라이선스

MIT License
