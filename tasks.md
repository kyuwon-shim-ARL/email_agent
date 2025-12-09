# Implementation Tasks - v0.6.2 Auto-Draft Creation

## Overview

Gmail 초안 자동 생성 및 16열 스프레드시트 형식 구현.

### v0.6.2 Changes

- ✅ Gmail 초안 자동 생성 (/email-analyze 시)
- ✅ 16열 스키마 (답장여부 컬럼 추가)
- ✅ 내용미리보기 HTML 태그 제거
- ✅ 조건부 서식 범위 수정 (startRowIndex: 1)
- ✅ /email-analyze 슬래시 커맨드 업데이트
- ✅ /email-draft 슬래시 커맨드 업데이트

---

## Task 0: 16-Column Schema (v0.6.2)

### 0.1 Column Structure Update

**Status**: ✅ Completed

**Files Modified**:
- `email_classifier/sheets_client.py`

**New 16-Column Schema**:
```
A: 상태, B: 우선순위, C: 라벨, D: 제목, E: 발신자, F: 받은CC, G: 받은시간
H: 내용미리보기, I: AI요약, J: 초안(제목), K: 초안(내용), L: 보낼CC
M: 전송예정, N: 답장여부, O: Draft ID, P: Thread ID
```

### 0.2 strip_html() Function

**Status**: ✅ Completed

**File**: `email_classifier/sheets_client.py`

```python
def strip_html(text: str) -> str:
    """HTML 태그 및 스타일/스크립트 제거하고 텍스트만 추출."""
    # 1. script, style 태그와 내용 제거
    # 2. HTML 주석 제거
    # 3. 모든 HTML 태그 제거
    # 4. CSS 패턴 제거
    # 5. HTML 엔티티 변환
    # 6. 연속 공백 정리
```

### 0.3 Conditional Formatting Fix

**Status**: ✅ Completed

**Issue**: 조건부 서식 범위가 잘못됨 (startRowIndex: 17)
**Fix**: startRowIndex: 1로 수정하여 데이터 행에 적용

---

## Task 1: Auto-Draft Creation

### 1.1 /email-analyze Draft Auto-Creation

**Status**: ✅ Completed

**File**: `.claude/commands/email-analyze.md`

**Logic**:
```python
for email, cls in zip(emails, classifications):
    if cls['requires_response'] and cls.get('draft_body'):
        # 1. Gmail 초안 생성
        draft = gmail.create_draft(
            to=extract_email(email['sender']),
            subject=cls['draft_subject'],
            body=cls['draft_body'],
            thread_id=email['thread_id']
        )
        # 2. Draft ID 저장
        draft_id = draft.get('id', '')
        # 3. Sheets 업데이트 (O열)
```

### 1.2 /email-draft Sync Update

**Status**: ✅ Completed

**File**: `.claude/commands/email-draft.md`

**Updated Logic**:
1. config에서 spreadsheet_id 자동 로드
2. 신규 메일 탭에서 조건 검색:
   - 상태="답장필요"
   - 초안(내용) not empty
   - Draft ID is empty
3. Gmail 초안 생성 + Draft ID 업데이트

---

## Task 2: Spreadsheet Functions Update

### 2.1 add_to_history() / add_to_new_emails()

**Status**: ✅ Completed

- 16열 형식으로 업데이트
- strip_html() 적용
- 답장여부 컬럼 추가

### 2.2 _find_history_row()

**Status**: ✅ Completed

- Thread ID 검색 범위: A:P
- Thread ID 인덱스: 15 (P열)

### 2.3 clear_new_emails_tab()

**Status**: ✅ Completed

- Clear 범위: A2:P

---

## Task 3: Slash Commands Update

### 3.1 /email-analyze Update

**Status**: ✅ Completed

**Changes**:
1. 3단계에서 Gmail 초안 자동 생성 로직 추가
2. Draft ID를 Sheets에 저장
3. 보고서에 초안 생성 현황 포함

### 3.2 /email-draft Update

**Status**: ✅ Completed

**Changes**:
1. spreadsheet_id 자동 로드 (config에서)
2. 16열 형식 지원
3. 신규 메일/처리 이력 탭 선택 가능

---

## Completion Summary

| Task | Status |
|------|--------|
| 0.1 16-column schema | ✅ |
| 0.2 strip_html() | ✅ |
| 0.3 Conditional formatting fix | ✅ |
| 1.1 /email-analyze auto-draft | ✅ |
| 1.2 /email-draft sync | ✅ |
| 2.1 add_to_history update | ✅ |
| 2.2 _find_history_row update | ✅ |
| 2.3 clear_new_emails_tab update | ✅ |
| 3.1 /email-analyze command | ✅ |
| 3.2 /email-draft command | ✅ |

---

## User Workflow Summary (v0.6.2)

```
/email-analyze
     ↓
📊 스프레드시트 업데이트:
   - [신규 메일] 탭: 오늘 분석 결과
   - [처리 이력] 탭: 누적 이력
📝 Gmail 초안 자동 생성 (답장필요 + 초안 있음)
📧 요약 보고서 발송
     ↓
User reviews in Gmail:
  - 임시보관함에서 초안 확인/수정
  - 직접 발송 가능
     ↓
(Optional) Sheets에서 추가 초안 작성:
  - 상태를 "답장필요"로 변경
  - 초안(제목), 초안(내용) 입력
     ↓
(Optional) /email-draft → 추가 Gmail 초안 생성
     ↓
(Optional) /email-send → 일괄 발송
```

---

## Key URLs

- **스프레드시트**: `email_history_config.json`에서 ID 확인
- **Config**: `email_history_config.json`
