# Email Agent v0.6.3

**Claude Code 슬래시 명령어로 Gmail 이메일을 자동 분류하고 답장 초안을 생성하는 도구**

## 핵심 특징

- **API 비용 $0** - Claude Code 대화로 AI 처리
- **슬래시 명령어** - `/email-analyze`, `/email-draft`, `/email-send`
- **Gmail 초안 자동 생성** - 분석 시 초안 자동 생성 → 임시보관함에서 바로 확인
- **통합 스프레드시트** - 신규 메일 + 처리 이력 탭으로 관리
- **맥락 기반 우선순위** - 하드코딩 없이 Claude가 이메일 맥락에서 종합 판단
- **답장 여부 자동 체크** - Gmail Thread API로 답장 상태 확인

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/email-agent.git
cd email-agent
```

### 2. Python 환경 설정

**uv 사용 (권장):**
```bash
# uv 설치 (최초 1회)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

**pip 사용:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
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
python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"
# 브라우저에서 Google 계정 로그인 → 권한 승인
```

### 5. Claude Code 실행

```bash
# Claude Code CLI 설치 (최초 1회)
npm install -g @anthropic-ai/claude-code

# 프로젝트 디렉토리에서 실행
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

## 우선순위 시스템 (v0.6.3)

### 맥락 기반 판단

하드코딩된 규칙 없이 Claude가 이메일 맥락에서 종합 추론:

- **어투** → 상하관계 추론 ("부탁드립니다" vs "확인 바랍니다")
- **서명** → 직급/부서 파악
- **내용** → 요청 강도, 긴급도 판단

### 5가지 판단 축

| 축 | 높음 | 낮음 |
|----|------|------|
| 발신자 관계 | 상위 직급 추정 | 자동발송, 마케팅 |
| 요청 강도 | 즉시 결정/승인 필요 | FYI, 참고 |
| 긴급 신호 | 오늘, ASAP, 긴급 | 시간 날 때, no rush |
| 메일 유형 | 개인 1:1 요청 | 전체 공지, 뉴스레터 |
| 수신 방식 | To (직접) | CC, 그룹 (-1) |

### 우선순위 정의

| 등급 | 기준 |
|------|------|
| **P5** | 상위 직급 + 긴급 + 즉시 액션 (5-10%만) |
| **P4** | 마감일 1주 내 + 액션 필요 |
| **P3** | 일반 업무, 여유 있는 회신 (기본값) |
| **P2** | 공지, FYI, 참고용 |
| **P1** | 자동발송, 뉴스레터, 마케팅 |

---

## 파일 구조

```
email_agent/
├── email_classifier/
│   ├── gmail_client.py       # Gmail API 클라이언트
│   └── sheets_client.py      # Sheets API 클라이언트
├── .claude/
│   ├── commands/
│   │   ├── email-analyze.md  # /email-analyze 명령어
│   │   ├── email-draft.md    # /email-draft 명령어
│   │   └── email-send.md     # /email-send 명령어
│   └── skills/
│       └── prioritize-email.md  # 우선순위 판단 가이드
├── scripts/
│   └── daily_email_analyze.sh   # cron 자동화 스크립트
├── credentials.json          # Google OAuth (직접 생성)
├── token.json               # OAuth 토큰 (자동 생성)
├── email_history_config.json # 스프레드시트 ID (자동 생성)
├── requirements.txt          # Python 의존성
└── README.md
```

---

## 업데이트 (기존 사용자)

```bash
cd email-agent
git pull

# uv 사용자
uv sync

# pip 사용자
pip install -r requirements.txt
```

---

## 자동화 (선택)

### Cron 설정 (매일 8시)

```bash
chmod +x scripts/daily_email_analyze.sh
crontab -e

# 아래 줄 추가
0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh
```

스크립트가 자동으로 프로젝트 경로를 감지하므로, 어느 위치에 설치해도 동작합니다.

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
python -c "from email_classifier.gmail_client import GmailClient; GmailClient()"
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
