# Implementation Plan - Email Agent v0.6.3

## Overview

Streamlined workflow: Analyze emails, auto-create Gmail drafts, user reviews in Gmail.

**Goal**: 초안 내용 있으면 Gmail 초안 자동 생성하여 검토 준비 완료 상태로 제공.

### v0.6.3 New Features

- **맥락 기반 우선순위**: 하드코딩 없이 Claude가 이메일 맥락에서 종합 판단
- **5가지 판단 축**: 발신자 관계, 요청 강도, 긴급 신호, 메일 유형, 수신 방식
- **prioritize-email.md 스킬**: 우선순위 판단 가이드라인 분리

### v0.6.2 Features (Completed)

- **Gmail 초안 자동 생성**: /email-analyze 시 초안 내용 있으면 즉시 Gmail 초안 생성
- **Draft ID 자동 저장**: 스프레드시트에 Draft ID 자동 업데이트
- **16열 스키마**: Email Tracker 형식으로 확장 (답장여부 컬럼 추가)
- **내용미리보기 HTML 제거**: 순수 텍스트만 표시

### v0.6.1 Features (Completed)

- **수신유형 기반 우선순위**: To/CC/그룹메일에 따른 우선순위 자동 조정

### v0.6.0 Features (Completed)

- **통합 스프레드시트**: 하나의 스프레드시트에서 신규 메일 + 처리 이력 탭 관리
- **답장 여부 체크**: Gmail Thread API로 답장 상태 자동 확인
- **Cron 자동화**: 매일 8시 자동 분석

---

## Priority System (v0.6.3)

### 맥락 기반 판단 원칙

**하드코딩된 규칙 없이** Claude가 이메일 맥락에서 종합 추론:

```
Claude 자연어 이해 능력 활용:
- 어투 → 상하관계 추론 ("부탁드립니다" vs "확인 바랍니다")
- 서명 → 직급/부서 파악
- 내용 → 요청 강도, 긴급도 판단
```

### 5가지 판단 축

| 축 | 높음 | 낮음 |
|----|------|------|
| 발신자 관계 | 상위 직급 추정 | 자동발송, 마케팅 |
| 요청 강도 | 즉시 결정/승인 필요 | FYI, 참고 |
| 긴급 신호 | 오늘, ASAP, 긴급 | 시간 날 때, no rush |
| 메일 유형 | 개인 1:1 요청 | 전체 공지, 뉴스레터 |
| 수신 방식 | To (직접) | CC, 그룹 (-1) |

### 우선순위 정의

| P | 기준 |
|---|------|
| **P5** | 상위 직급 + 긴급 + 즉시 액션 (5-10%만) |
| **P4** | 마감일 1주 내 + 액션 필요 |
| **P3** | 일반 업무, 여유 있는 회신 (기본값) |
| **P2** | 공지, FYI, 참고용 |
| **P1** | 자동발송, 뉴스레터, 마케팅 |

### 스킬 파일

`.claude/skills/prioritize-email.md`에서 상세 가이드라인 참조

---

## Architecture (v0.6.3)

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ /email-analyze (메인 명령어)                                      │
│   1. Gmail에서 이메일 로드 (처리완료 제외)                          │
│   2. AI 분류 (우선순위, 요약, 초안 생성)                            │
│   3. Gmail 라벨 적용                                              │
│   4. Sheets에 기록 (신규 메일 + 처리 이력)                          │
│   5. ⭐ 초안 내용 있으면:                                          │
│      - Gmail 초안 자동 생성                                       │
│      - Draft ID를 Sheets에 저장                                   │
│   6. 요약 보고서 발송                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 사용자 검토 (Gmail + Sheets)                                      │
│   - Gmail 임시보관함에서 초안 직접 검토/수정                         │
│   - Sheets에서 상태/초안 내용 변경 가능                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ /email-draft (시트 수정 후 추가 초안 필요시)                        │
│   조건: 상태="답장필요" + 초안 내용 있음 + Draft ID 없음             │
│   → Gmail 초안 생성 + Draft ID 업데이트                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ /email-send (선택)                                               │
│   - 전송예정=TRUE인 항목 일괄 발송                                 │
│   - 또는 Gmail에서 직접 발송                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Spreadsheet Schema (v0.6.2)

### Unified Spreadsheet Structure

```
📚 Email History (누적 이력)
├── [신규 메일] - 오늘 분석한 이메일 (매 분석 시 초기화)
└── [처리 이력] - 전체 누적 이력 (중복 시 업데이트)
```

### 16 Columns (Email Tracker Format)

| Col | Name | Type | Description |
|-----|------|------|-------------|
| A | 상태 | Text | 답장필요/답장불필요/답장완료 |
| B | 우선순위 | Number | 1-5 with conditional color |
| C | 라벨 | Text | Gmail labels |
| D | 제목 | Text | Email subject |
| E | 발신자 | Text | Sender name <email> |
| F | 받은CC | Text | CC recipients |
| G | 받은시간 | Text | Gmail Date header |
| H | 내용미리보기 | Text | Body preview 300 chars (HTML stripped) |
| I | AI요약 | Text | 3-line MECE summary |
| J | 초안(제목) | Text | Draft reply subject |
| K | 초안(내용) | Text | Draft reply body |
| L | 보낼CC | Text | CC for reply (user input) |
| M | 전송예정 | Boolean | Checkbox for batch send |
| N | 답장여부 | Text | 답장함/미답장 |
| O | Draft ID | Hidden | Gmail draft ID |
| P | Thread ID | Hidden | Gmail thread ID |

### Conditional Formatting

| Column | Value | Color |
|--------|-------|-------|
| 상태 (A) | 답장필요 | 🔴 Light red |
| 상태 (A) | 답장완료 | 🟢 Light green |
| 우선순위 (B) | P4-5 (높음) | 🟢 Light green |
| 우선순위 (B) | P1-2 (낮음) | 🔴 Light red |
| 답장여부 (N) | 미답장 | 🔴 Light red |
| 답장여부 (N) | 답장함 | 🟢 Light green |

---

## Slash Commands

### /email-analyze

1. Load emails from Gmail (15-20 recommended, skip processed)
2. Collect conversation history for each sender
3. Check reply status for each email (check_if_replied)
4. AI analyzes each email:
   - Priority (1-5)
   - Requires response (true/false)
   - AI summary (3 lines MECE)
   - Action item (even without deadline)
   - Deadline & description (if mentioned)
   - Draft subject/body (if response needed)
5. Apply Gmail labels
6. Clear "신규 메일" tab, add new emails
7. Update "처리 이력" tab (add new / update existing)
8. **⭐ Auto-create Gmail drafts**:
   - For each email with `requires_response=true` AND `draft_body` not empty
   - Create Gmail draft via API
   - Save Draft ID to Sheets (column O)
9. Send HTML summary report

### /email-draft

1. Read unified spreadsheet (auto-detect from config)
2. Find rows where:
   - 상태="답장필요"
   - 초안(내용) not empty
   - Draft ID is empty
3. For each matching row:
   - Extract sender email, 초안(제목), 초안(내용), 보낼CC
   - Create Gmail draft
   - Update Draft ID in both tabs
4. Report created drafts count

### /email-send

1. Read spreadsheet
2. Find all rows where 전송예정=TRUE AND Draft ID exists
3. Confirm with user (show list)
4. Batch send all drafts
5. Update 상태 to "답장완료"

---

## Component Design

### Gmail Client (`gmail_client.py`)

```python
# Key functions
def get_recent_emails(max_results: int, skip_processed: bool = True) -> list[dict]
def get_recipient_type(headers: list, my_email: str) -> dict
def get_conversation_history(sender: str, max_results: int) -> dict
def check_if_replied(thread_id: str) -> bool
def create_draft(to: str, subject: str, body: str, thread_id: str, cc: list) -> dict
def send_draft(draft_id: str) -> dict
def setup_email_labels() -> dict[str, str]
def apply_labels_to_email(email_id: str, status: str, priority: int, label_ids: dict)
def mark_as_processed(message_ids: list[str], label_ids: dict) -> None
def send_summary_report(subject: str, body: str, label_ids: dict) -> dict
```

### Sheets Client (`sheets_client.py`)

```python
# Key functions
def strip_html(text: str) -> str  # NEW: Remove HTML tags from body preview
def get_or_create_history_sheet() -> str
def ensure_new_emails_tab_exists(spreadsheet_id: str) -> int
def clear_new_emails_tab(spreadsheet_id: str) -> None
def add_email_to_both_tabs(email_data, classification, replied) -> str
def add_to_history(email_data, classification, replied) -> str
def add_to_new_emails(email_data, classification, replied) -> None
def get_tab_ids(spreadsheet_id: str) -> dict[str, int]
def get_history_spreadsheet_url() -> str
def update_draft_id(spreadsheet_id: str, row: int, draft_id: str) -> None  # NEW
```

---

## Automation

### Cron Setup (Daily 8AM)

```bash
# crontab -e
0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh
```

### Script (scripts/daily_email_analyze.sh)

```bash
#!/bin/bash
# Get script directory (works even when called via cron)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
mkdir -p logs
LOG_FILE="logs/daily_analyze_$(date +%Y%m%d).log"
echo "=== Started: $(date) ===" >> "$LOG_FILE"
claude -p "이메일 분석해줘" --dangerously-skip-permissions >> "$LOG_FILE" 2>&1
echo "=== Completed: $(date) ===" >> "$LOG_FILE"
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 502 Gateway | Google API timeout | Retry with backoff |
| No new emails | All processed | Send "새 이메일 없음" report |
| Duplicate entry | Same email re-analyzed | Update existing row |
| Missing body | Nested multipart | Recursive extraction |
| Draft not found | Deleted in Gmail | Skip, log warning |
| Draft creation failed | API error | Log error, continue |
