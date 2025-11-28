# Email Agent - Feature Specification

## Project Overview

**Email Agent** is a Gmail email classifier that uses Claude Code for zero-cost AI processing. It automatically classifies emails, generates personalized reply drafts, and integrates with Google Sheets for batch management.

## Current Version: v0.4.0 (Hybrid Approach)

### Core Philosophy

- **Zero API Costs**: All AI processing through Claude Code interactive prompts
- **Gmail-Centric**: Gmail drafts preserve rich formatting (HTML, signatures, styles)
- **Sheets as Dashboard**: Google Sheets for management, not content storage
- **User Control**: All drafts reviewed/edited before sending

---

## Feature: Hybrid Gmail Draft + Sheets Management

### Problem Statement

**Previous v0.3.0 Issues:**

1. ❌ Gmail drafts created as **plain text** → No formatting (bold, colors, signatures)
2. ❌ Batch sending **recreates emails from Sheets text** → User edits in Gmail lost
3. ❌ Sheets stores full email body → Formatting stripped, content duplicated

**User Impact:**
- Professional emails need formatting (signatures, emphasis, structure)
- Users edit drafts in Gmail app but batch send ignores their changes
- Confusing workflow: "Which version is the source of truth?"

### Solution: Hybrid Architecture

**Principle**: Gmail owns content, Sheets owns workflow state

```
┌─────────────────────────────────────────────────────────┐
│ GMAIL: Content Storage (HTML drafts)                    │
│  - Rich text formatting preserved                       │
│  - User edits in Gmail app                              │
│  - Drafts linked by Draft ID                            │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│ SHEETS: Workflow Dashboard                              │
│  - Email list (subject, sender, priority)               │
│  - Links to Gmail drafts                                │
│  - Checkboxes for batch actions                         │
│  - Status tracking (답장필요/완료)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Detailed Requirements

### R1: HTML Draft Creation

**User Story**: As a user, I want my reply drafts to include formatting (bold, signatures, colors) so they look professional.

**Acceptance Criteria**:
- ✅ Claude generates reply with basic HTML formatting
- ✅ Gmail drafts created with `text/html` MIME type
- ✅ User can add/edit formatting in Gmail app
- ✅ Common elements supported: `<b>`, `<i>`, `<u>`, `<br>`, `<p>`, signatures

**Technical Details**:
```python
# gmail_client.py::create_draft()
from email.mime.text import MIMEText

# Support HTML mode
message = MIMEText(body, 'html' if is_html else 'plain')
```

**Edge Cases**:
- Plain text preference: Support `is_html=False` parameter
- Invalid HTML: Gracefully fallback to plain text
- Large HTML: No size limit (Gmail handles)

---

### R2: Draft Link in Sheets

**User Story**: As a user, I want to click a link in Sheets to open the Gmail draft so I can review/edit it.

**Acceptance Criteria**:
- ✅ Sheets includes clickable "Gmail 초안" link
- ✅ Link format: `https://mail.google.com/mail/#drafts?compose={draft_id}`
- ✅ Clicking opens draft in new tab
- ✅ Draft ID stored in hidden column for API use

**Spreadsheet Schema**:
```
Column A: 상태 (답장필요/불필요/완료)
Column B: 우선순위 (1-5)
Column C: 제목
Column D: 발신자
Column E: 받은시간
Column F: 내용미리보기 (200자)
Column G: Gmail 초안 (Hyperlink)
Column H: 발송여부 (Checkbox)
Column I: Draft ID (Hidden)
Column J: Thread ID (Hidden)
```

**Link Format**:
```
=HYPERLINK("https://mail.google.com/mail/#drafts?compose=" & I2, "열기")
```

---

### R3: Send Existing Drafts (Not Recreate)

**User Story**: As a user, when I batch send emails, I want my Gmail edits to be sent (not the original Sheets text).

**Acceptance Criteria**:
- ✅ Batch send uses `drafts.send()` API (not `messages.send()`)
- ✅ User edits in Gmail app are preserved
- ✅ Only sends drafts with checkbox checked
- ✅ Status updated to "답장완료" after successful send
- ✅ Errors logged without stopping batch

**API Change**:
```python
# OLD (Wrong - recreates email)
def batch_send_emails(emails):
    for email in emails:
        send_email(to=email['to'], body=email['body'])  # ❌ Ignores Gmail edits

# NEW (Correct - sends existing draft)
def send_draft(draft_id: str):
    self.service.users().drafts().send(
        userId="me",
        body={"id": draft_id}
    ).execute()

def batch_send_drafts(draft_ids: list[str]):
    for draft_id in draft_ids:
        send_draft(draft_id)  # ✅ Preserves Gmail edits
```

**Error Handling**:
- Draft deleted by user → Log error, continue batch
- Network error → Retry once, then log and continue
- Invalid draft ID → Log error, mark as failed in Sheets

---

### R4: Simplified Sheets Columns

**User Story**: As a user, I don't want duplicate email content in Sheets; just show me what I need to manage my workflow.

**Rationale**:
- Full email body → Already in Gmail, clutters Sheets
- Draft body text → Loses formatting, outdated after user edits
- Preview (200 chars) → Enough to recognize email

**Removed Columns** (from v0.3.0):
- ❌ "메일내용" (full body)
- ❌ "답장초안" (draft body text)
- ❌ "답장수신자" (redundant - same as sender)
- ❌ "답장CC" (rarely used)

**Kept Columns**:
- ✅ "내용미리보기" (200 char preview)
- ✅ "Gmail 초안" (link to open in Gmail)
- ✅ Status, priority, metadata

---

## Workflow

### Step-by-Step User Flow

```
1. User runs: email-classify-sheets

2. Program:
   - Fetches emails from Gmail
   - Analyzes priority (first contact, sent weight)
   - Generates HTML reply drafts
   - Creates Gmail drafts (with formatting)
   - Records in Sheets with draft links

3. User in Google Sheets:
   - Sees all emails sorted by priority
   - Clicks "Gmail 초안" links to review

4. User in Gmail App:
   - Opens draft
   - Edits formatting, adds signatures, etc.
   - Closes tab (draft auto-saved)

5. User in Sheets:
   - Checks "발송여부" for emails to send
   - Re-runs program with "Batch send" option

6. Program:
   - Reads draft IDs from Sheets
   - Sends Gmail drafts via drafts.send()
   - Updates status to "답장완료"

7. Result:
   ✅ Sent emails include all user formatting edits
```

---

## Technical Architecture

### Components

**1. Gmail Client (`gmail_client.py`)**
- `create_draft(is_html=True)` - Create HTML drafts
- `send_draft(draft_id)` - Send existing draft
- `batch_send_drafts(draft_ids)` - Batch send by ID

**2. Sheets Client (`sheets_client.py`)**
- `create_email_tracker()` - Initialize spreadsheet with new schema
- `add_email_row(draft_id, draft_link)` - Store draft metadata
- `get_drafts_to_send()` - Get checked draft IDs
- `update_email_status()` - Mark as sent

**3. Main Workflow (`main_sheets.py`)**
- Connect draft creation → Sheets recording
- Connect Sheets checkboxes → Batch sending

### API Scopes Required

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",      # Read emails
    "https://www.googleapis.com/auth/gmail.compose",       # Create drafts
    "https://www.googleapis.com/auth/gmail.send",          # Send drafts
    "https://www.googleapis.com/auth/spreadsheets",        # Sheets R/W
]
```

---

## Non-Functional Requirements

### Performance
- Draft creation: < 2s per email
- Sheets update: Batch API (all rows in 1 request)
- Batch send: 1 email/sec (avoid rate limits)

### Security
- OAuth tokens stored locally only
- No draft content in logs
- Sheets permissions: User-only (not public)

### Compatibility
- Gmail API v1
- Google Sheets API v4
- Python 3.11+

---

## Future Enhancements (Out of Scope)

- ❌ Schedule sending (requires backend)
- ❌ Email templates library
- ❌ Undo sent emails (Gmail limitation)
- ❌ Multi-account support

---

## Success Metrics

- ✅ User edits in Gmail reflected in sent emails
- ✅ No formatting loss in professional emails
- ✅ Sheets remains clean and fast (< 100ms load)
- ✅ Zero duplicate content between Gmail/Sheets
