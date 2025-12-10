# Email Agent - Feature Specification

## Project Overview

**Email Agent** is a Gmail email classifier that uses Claude Code for zero-cost AI processing. It automatically classifies emails, generates personalized reply drafts, and integrates with Google Sheets for batch management.

## Current Version: v0.6.3

### Core Philosophy

- **Zero API Costs**: All AI processing through Claude Code interactive prompts
- **Gmail-Centric**: Gmail drafts preserve rich formatting (HTML, signatures, styles)
- **Single Sheet Dashboard**: 하나의 스프레드시트에서 신규 메일 + 전체 이력 관리
- **User Control**: All drafts reviewed/edited before sending
- **Auto-Draft Creation**: 초안 내용 있으면 Gmail 초안 자동 생성
- **No Duplicate Processing**: Processed emails are labeled and skipped
- **Daily Automation**: 매일 8시 자동 분석 (cron)
- **Context-Based Priority**: 맥락 기반 우선순위 판단 (하드코딩 없음)

---

## Workflow Commands

### 사용자 명령어

```
/email-analyze    이메일 분석 + Sheets 작성 + Gmail 초안 자동 생성
/email-draft      추가 초안 생성 (시트 수정 후 Draft ID 없는 항목)
/email-send       Gmail 초안 일괄 발송
```

### 워크플로우 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│ /email-analyze (메인 명령어)                                      │
│   1. Gmail에서 이메일 로드 (처리완료 제외)                          │
│   2. AI 분류 (우선순위, 요약, 초안 생성)                            │
│   3. Gmail 라벨 적용                                              │
│   4. Sheets에 기록 (신규 메일 + 처리 이력)                          │
│   5. ⭐ 초안 내용 있으면 Gmail 초안 자동 생성 + Draft ID 저장        │
│   6. 요약 보고서 발송                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 사용자 작업: Google Sheets에서 검토/수정 (선택)                     │
│   - 초안(제목), 초안(내용) 수정                                    │
│   - 보낼CC 추가                                                  │
│   - 상태 변경 (답장불필요 → 답장필요)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ /email-draft (시트 수정 후 추가 초안 필요시)                        │
│   - 상태="답장필요" + 초안 내용 있음 + Draft ID 없음 → 초안 생성     │
│   - Draft ID 업데이트                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ /email-send (선택)                                               │
│   - 전송예정=TRUE인 항목 일괄 발송                                 │
│   - Gmail에서 직접 발송도 가능                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Spreadsheet Schema (v0.6.2)

### 통합 스프레드시트 구조

하나의 스프레드시트 (`📚 Email History (누적 이력)`)에서 두 개의 탭으로 관리:

```
┌─────────────────────────────────────────────────────────────────┐
│ 📚 Email History (누적 이력)                                      │
├─────────────────────────────────────────────────────────────────┤
│ [신규 메일] | [처리 이력]                                          │
│                                                                 │
│ 신규 메일: 오늘 분석한 이메일 (매 분석 시 초기화)                      │
│ 처리 이력: 전체 누적 이력 (중복 시 업데이트)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 컬럼 구조 (16열) - Email Tracker 형식

```
A: 상태         - 답장필요/답장불필요/답장완료
B: 우선순위      - 1-5
C: 라벨         - Gmail 라벨
D: 제목         - 이메일 제목
E: 발신자        - 발신자 이름 <email>
F: 받은CC       - CC 수신자
G: 받은시간      - Gmail Date 헤더
H: 내용미리보기   - 본문 300자 (HTML 제거)
I: AI요약       - 3줄 이내 MECE 요약
J: 초안(제목)    - 답장 초안 제목
K: 초안(내용)    - 답장 초안 본문
L: 보낼CC       - 발송 시 CC (사용자 입력)
M: 전송예정      - 체크박스 (일괄 발송용)
N: 답장여부      - 답장함/미답장
O: Draft ID     - Gmail 초안 ID (숨김)
P: Thread ID    - Gmail Thread ID (숨김)
```

### 조건부 색상 (Color Coding)

| 컬럼 | 값 | 색상 |
|------|-----|------|
| 상태 (A) | 답장필요 | 🔴 연빨강 |
| 상태 (A) | 답장완료 | 🟢 연초록 |
| 우선순위 (B) | P4-5 (높음) | 🟢 연초록 |
| 우선순위 (B) | P1-2 (낮음) | 🔴 연빨강 |
| 답장여부 (N) | 미답장 | 🔴 연빨강 |
| 답장여부 (N) | 답장함 | 🟢 연초록 |

---

## AI 분석 기준

### 우선순위 판단 (P1-P5) - 맥락 기반

**핵심 원칙**: 하드코딩된 규칙 없이, 이메일 맥락에서 종합적으로 추론

Claude가 자연스럽게 파악:
- 어투에서 상하관계 추론 ("부탁드립니다" vs "확인 바랍니다")
- 서명에서 직급/부서 파악
- 요청의 강도와 긴급도 판단

### 5가지 판단 축

| 축 | 판단 요소 |
|----|----------|
| **발신자-수신자 관계** | 어투, 서명 직급, 요청 방식에서 추론 |
| **요청 강도** | 즉시 결정 > 명시적 요청 > 소프트 요청 > FYI |
| **긴급 신호** | 오늘/ASAP > 이번 주 > 마감일 있음 > 여유 |
| **메일 유형** | 개인 1:1 > 팀 메일 > 전체 공지 > 자동발송 |
| **수신 방식** | To(직접) > CC(참조, -1) > 그룹(-1) |

### 우선순위 정의

| 등급 | 이름 | 기준 |
|------|------|------|
| **P5** | 최우선 | 상위 직급의 직접 요청 + 긴급 + 즉시 액션 필요 |
| **P4** | 긴급 | 명시적 마감일 + 액션 필요 OR 중요 발신자 요청 |
| **P3** | 보통 | 일반 업무 요청, 회신 필요하지만 여유 있음 |
| **P2** | 낮음 | 공지사항, 참고용, FYI |
| **P1** | 최저 | 자동발송, 뉴스레터, 마케팅, 스팸 |

### 판단 가이드라인

- **P5는 드물게**: 전체 메일의 5-10%만 (정말 긴급한 것만)
- **첫 연락은 주의**: 처음 받는 메일이면 P3 이상 (관계 파악 필요)
- **CC는 보수적으로**: 직접 액션 필요한지 먼저 확인
- **맥락 우선**: 키워드보다 전체 맥락이 중요
- **애매하면 P3**: 판단이 어려우면 기본값

### 마감일 추출

이메일 본문에서 다음 패턴의 마감일을 자동 추출:
- "~까지", "마감", "deadline", "due"
- 날짜 형식: "12월 19일", "2024-12-19" 등
- 설명회, 제출, 신청 기한 등

추출된 마감일은:
- 분류 결과 JSON에 `deadline`, `deadline_description` 필드로 저장
- 요약 보고서의 "주요 일정표" 섹션에 마감일순으로 정렬하여 표시
- 긴급도 표시: 오늘 이전=⚠️ 마감!, 7일 이내=⏰ 임박

### 액션 아이템 추출

마감일 유무와 관계없이 나에게 요구되는 행동/결과물 추출:
- "~해주세요", "확인 부탁", "제출 요청", "참석 요청" 등
- 예: "설문조사 참여", "문서 보완", "회의 참석", "검토 요청"

요약 보고서의 "📋 액션 아이템" 섹션에 우선순위순으로 표시

### AI 요약 형식

```
• 핵심 내용 1줄
• 요청사항 또는 액션 아이템
• 마감일/일정 (있는 경우)
```

### 답장 초안 가이드라인

- 기존 대화 어투 유지
- 간결하고 명확한 표현
- HTML 형식 지원 (`<p>`, `<br>`, `<b>` 등)

---

## API 스코프

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",   # 이메일 읽기
    "https://www.googleapis.com/auth/gmail.compose",    # 초안 작성
    "https://www.googleapis.com/auth/gmail.send",       # 발송
    "https://www.googleapis.com/auth/gmail.modify",     # 라벨 관리
    "https://www.googleapis.com/auth/spreadsheets",     # Sheets R/W
]
```

---

## 기술 구현

### 파일 구조

```
email_classifier/
├── gmail_client.py      # Gmail API 클라이언트
│   ├── get_recent_emails(skip_processed=True)
│   ├── get_conversation_history()
│   ├── check_if_replied()        # 답장 여부 확인
│   ├── create_draft()
│   ├── send_draft()
│   ├── setup_email_labels()      # 10개 라벨
│   ├── apply_labels_to_email()
│   ├── mark_as_processed()       # 처리완료 라벨
│   └── send_summary_report()     # 요약 보고서 발송
│
└── sheets_client.py     # Sheets API 클라이언트
    ├── get_or_create_history_sheet()   # 통합 스프레드시트
    ├── ensure_new_emails_tab_exists()  # 신규 메일 탭
    ├── clear_new_emails_tab()          # 탭 초기화
    ├── add_email_to_both_tabs()        # 두 탭에 추가
    ├── add_to_history()                # 처리 이력 추가/업데이트
    ├── get_tab_ids()                   # 탭 ID 조회
    └── get_history_spreadsheet_url()   # URL 조회
```

### Gmail 라벨 (10개)

```
상태 라벨:  답장필요    답장불필요    답장완료
우선순위:   P1-최저    P2-낮음      P3-보통    P4-긴급    P5-최우선
시스템:     처리완료   메일요약
```

- **처리완료**: 분석 완료된 이메일에 자동 적용 (중복 처리 방지)
- **메일요약**: 요약 보고서 이메일에 적용

### 요약 보고서

`/email-analyze` 완료 시 자동으로 HTML 형식의 요약 보고서를 자신에게 발송:

**보고서 구성**:
1. **요약 통계**: 총 이메일 수, 답장 필요/불필요 수, 우선순위별 분포
2. **⚠️ 미답장 경고**: 답장 필요 + 미답장 이메일 강조 표시
3. **📋 액션 아이템**: 요구되는 행동을 우선순위순으로 정렬, 답장 상태 표시
4. **📅 주요 일정표**: 마감일이 있는 이메일을 날짜순 정렬, 긴급도 표시
5. **답장 필요 목록**: 우선순위, 제목, 발신자, AI 요약
6. **참조용 목록**: 답장 불필요 이메일

**특징**:
- "메일요약" 라벨 자동 적용
- 스프레드시트 바로가기 링크 2개 (신규 메일 탭, 처리 이력 탭)
- CSS 스타일링된 HTML 형식
- 새 이메일 없을 시 "새 이메일 없음" 보고서 발송

---

## 성능 권장사항

### 배치 크기

| 이메일 수 | 컨텍스트 | 권장도 |
|----------|---------|--------|
| 15-20개 | ~30K 토큰 | ✅ 안전 |
| 30-40개 | ~60K 토큰 | ⚠️ 주의 |
| 50개+ | ~100K+ 토큰 | ❌ 배치 분할 필요 |

---

## 자동화

### Cron 설정 (매일 8시 자동 분석)

```bash
# crontab -e
0 8 * * * /path/to/email_agent/scripts/daily_email_analyze.sh
```

### 스크립트 (scripts/daily_email_analyze.sh)

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

## 향후 개선 (Out of Scope)

- ❌ 예약 발송 (백엔드 필요)
- ❌ 이메일 템플릿 라이브러리
- ❌ 다중 계정 지원
- ❌ 발송 취소 (Gmail 제한)
