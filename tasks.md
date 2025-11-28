# Implementation Tasks - v0.4.0 Hybrid Architecture

## Overview
Implement hybrid Gmail+Sheets architecture where Gmail preserves formatting and Sheets manages workflow.

---

## Task 1: Enhance Gmail Client with HTML Support

**File**: `email_classifier/gmail_client.py`

**Estimated Time**: 20 minutes

### 1.1 Modify `create_draft()` for HTML Support

**Location**: Line 120-157

**Changes**:
```python
# Add parameter
def create_draft(
    self, thread_id: str, to: str, subject: str, body: str,
    is_html: bool = True  # NEW
) -> dict[str, Any]:

# Change MIME type
message = MIMEText(body, 'html' if is_html else 'plain', 'utf-8')

# Return full draft object (not just execute)
return draft  # Contains 'id' field
```

**Acceptance Criteria**:
- ✅ Default is HTML mode (`is_html=True`)
- ✅ Plain text still supported (`is_html=False`)
- ✅ Returns draft object with 'id' field
- ✅ UTF-8 encoding for international characters

**Testing**:
```python
draft = gmail.create_draft(
    thread_id="123",
    to="test@example.com",
    subject="Test",
    body="<b>Bold text</b><br>Normal text",
    is_html=True
)
assert 'id' in draft
assert draft['id'].startswith('r')
```

---

### 1.2 Add `send_draft()` Function

**Location**: After `create_draft()` (insert at line ~158)

**Code**:
```python
def send_draft(self, draft_id: str) -> dict[str, Any]:
    """
    Send an existing Gmail draft by ID.

    This preserves all user edits made in the Gmail app.

    Args:
        draft_id: Draft ID from create_draft() return value

    Returns:
        Sent message information

    Raises:
        HttpError: If draft not found (404) or send fails
    """
    sent = (
        self.service.users()
        .drafts()
        .send(userId="me", body={"id": draft_id})
        .execute()
    )

    return sent
```

**Acceptance Criteria**:
- ✅ Sends existing draft without modification
- ✅ Raises HttpError if draft not found
- ✅ Returns sent message info with thread_id

**Testing**:
```python
# Create draft
draft = gmail.create_draft(...)
draft_id = draft['id']

# Edit draft manually in Gmail (manual step)

# Send draft
sent = gmail.send_draft(draft_id)
assert 'id' in sent
assert sent['labelIds'] == ['SENT']
```

---

### 1.3 Add `batch_send_drafts()` Function

**Location**: After `send_draft()` (insert at line ~180)

**Code**:
```python
def batch_send_drafts(self, draft_ids: list[str]) -> list[dict[str, Any]]:
    """
    Send multiple Gmail drafts by ID.

    Preserves all user edits made in Gmail app.

    Args:
        draft_ids: List of draft IDs to send

    Returns:
        List of results with success/failure status

    Example:
        results = gmail.batch_send_drafts(['r123...', 'r456...'])
        for result in results:
            if result['success']:
                print(f"Sent: {result['message_id']}")
            else:
                print(f"Failed: {result['error']}")
    """
    results = []

    for draft_id in draft_ids:
        try:
            sent = self.send_draft(draft_id)

            results.append({
                "draft_id": draft_id,
                "success": True,
                "message_id": sent.get("id"),
                "thread_id": sent.get("threadId"),
                "error": None,
            })
        except Exception as e:
            results.append({
                "draft_id": draft_id,
                "success": False,
                "message_id": None,
                "thread_id": None,
                "error": str(e),
            })

    return results
```

**Acceptance Criteria**:
- ✅ Sends drafts sequentially (avoid rate limits)
- ✅ Continues batch on individual failures
- ✅ Returns detailed results for each draft

**Testing**:
```python
draft_ids = ['r123...', 'r456...', 'invalid']
results = gmail.batch_send_drafts(draft_ids)

assert len(results) == 3
assert results[0]['success'] == True
assert results[1]['success'] == True
assert results[2]['success'] == False
assert 'not found' in results[2]['error'].lower()
```

---

### 1.4 Deprecate `batch_send_emails()`

**Location**: Line 202-238

**Changes**:
```python
def batch_send_emails(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    DEPRECATED: Use batch_send_drafts() instead.

    This function recreates emails from text and loses Gmail edits.
    Only kept for backward compatibility.
    """
    import warnings
    warnings.warn(
        "batch_send_emails() is deprecated. Use batch_send_drafts() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # ... existing implementation ...
```

**Acceptance Criteria**:
- ✅ Function still works (backward compatibility)
- ✅ Issues deprecation warning
- ✅ Documentation updated

---

## Task 2: Enhance Sheets Client with Draft Links

**File**: `email_classifier/sheets_client.py`

**Estimated Time**: 30 minutes

### 2.1 Update Spreadsheet Schema

**Location**: Line 85-99 (`create_email_tracker()`)

**Changes**:
```python
headers = [
    "상태",              # A: 답장필요/불필요/완료
    "우선순위",          # B: 1-5
    "제목",              # C: Email subject
    "발신자",            # D: Sender
    "받은시간",          # E: Received date
    "내용미리보기",      # F: Body preview (200 chars)
    "Gmail 초안",        # G: Hyperlink to draft
    "발송여부",          # H: Checkbox
    "Draft ID",          # I: Hidden (for API)
    "Thread ID",         # J: Hidden (for threading)
]
```

**Formatting Requests**:
```python
requests = [
    # Existing header formatting...

    # Hide columns I and J
    {
        "updateDimensionProperties": {
            "range": {
                "sheetId": 0,
                "dimension": "COLUMNS",
                "startIndex": 8,  # Column I (Draft ID)
                "endIndex": 10,   # Through Column J (Thread ID)
            },
            "properties": {"hiddenByUser": True},
            "fields": "hiddenByUser",
        }
    },

    # Set column G width (Gmail 초안 link)
    {
        "updateDimensionProperties": {
            "range": {
                "sheetId": 0,
                "dimension": "COLUMNS",
                "startIndex": 6,
                "endIndex": 7,
            },
            "properties": {"pixelSize": 120},
            "fields": "pixelSize",
        }
    },

    # Set column F width (preview)
    {
        "updateDimensionProperties": {
            "range": {
                "sheetId": 0,
                "dimension": "COLUMNS",
                "startIndex": 5,
                "endIndex": 6,
            },
            "properties": {"pixelSize": 300},
            "fields": "pixelSize",
        }
    },
]
```

**Acceptance Criteria**:
- ✅ 10 columns total (A-J)
- ✅ Columns I-J hidden by default
- ✅ Column widths optimized
- ✅ Range updated to A:J

---

### 2.2 Modify `add_email_row()`

**Location**: Line 137-179

**Changes**:
```python
def add_email_row(
    self,
    spreadsheet_id: str,
    email_data: dict[str, Any],
    draft_id: str = "",      # NEW parameter
    draft_link: str = "",    # NEW parameter
) -> None:
    """
    Add email to spreadsheet with draft link.

    Args:
        spreadsheet_id: Target spreadsheet ID
        email_data: Email metadata (subject, sender, body, etc.)
        draft_id: Gmail draft ID (e.g., 'r1234567890abcdef')
        draft_link: HYPERLINK formula for Gmail draft
    """
    status_map = {
        "needs_response": "답장필요",
        "no_response": "답장불필요",
        "sent": "답장완료",
    }

    status = status_map.get(email_data.get("status", "needs_response"), "답장필요")

    row = [
        status,                                          # A
        email_data.get("priority", 3),                   # B
        email_data.get("subject", ""),                   # C
        email_data.get("sender", ""),                    # D
        email_data.get("date", ""),                      # E
        email_data.get("body", "")[:200],                # F: Preview only (shortened)
        draft_link,                                      # G: Clickable link
        False,                                           # H: Checkbox unchecked
        draft_id,                                        # I: Hidden
        email_data.get("thread_id", ""),                 # J: Hidden
    ]

    self.service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Emails!A:J",                              # Updated range
        valueInputOption="USER_ENTERED",                 # Changed to support HYPERLINK formula
        body={"values": [row]},
    ).execute()
```

**Acceptance Criteria**:
- ✅ Accepts optional draft_id and draft_link
- ✅ Body preview limited to 200 chars
- ✅ Uses USER_ENTERED to evaluate HYPERLINK formula
- ✅ Range updated to A:J

---

### 2.3 Add `get_drafts_to_send()`

**Location**: After `add_email_row()` (insert at line ~210)

**Code**:
```python
def get_drafts_to_send(self, spreadsheet_id: str) -> list[dict[str, Any]]:
    """
    Get draft IDs for emails marked for sending.

    Returns only rows where:
    - Column H (발송여부) is checked (TRUE)
    - Column I (Draft ID) is not empty

    Returns:
        List of dicts with draft_id, subject, sender, row_number

    Example:
        [
            {
                'draft_id': 'r1234567890abcdef',
                'subject': 'Re: Meeting request',
                'sender': 'boss@example.com',
                'row_number': 2
            }
        ]
    """
    result = self.service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Emails!A2:J",  # Skip header row
    ).execute()

    rows = result.get("values", [])
    drafts_to_send = []

    for i, row in enumerate(rows, start=2):  # Row 2 = first data row
        # Ensure row has enough columns
        if len(row) < 9:
            continue

        send_checkbox = row[7] if len(row) > 7 else ""  # Column H
        draft_id = row[8] if len(row) > 8 else ""       # Column I

        # Check if marked for sending
        if send_checkbox in ["TRUE", "True", True, "true"] and draft_id:
            drafts_to_send.append({
                "draft_id": draft_id,
                "subject": row[2] if len(row) > 2 else "",
                "sender": row[3] if len(row) > 3 else "",
                "row_number": i,
            })

    return drafts_to_send
```

**Acceptance Criteria**:
- ✅ Returns only checked rows with valid draft IDs
- ✅ Handles various checkbox formats (TRUE/True/true)
- ✅ Returns row_number for status updates
- ✅ Gracefully handles short rows

**Testing**:
```python
# Setup: Create sheet with 3 rows
# Row 2: Checkbox=TRUE, Draft ID='r123'
# Row 3: Checkbox=FALSE, Draft ID='r456'
# Row 4: Checkbox=TRUE, Draft ID=''

drafts = sheets.get_drafts_to_send(spreadsheet_id)
assert len(drafts) == 1
assert drafts[0]['draft_id'] == 'r123'
assert drafts[0]['row_number'] == 2
```

---

### 2.4 Modify `update_email_status()`

**Location**: Existing function (find and modify)

**Changes**:
```python
def update_email_status(
    self,
    spreadsheet_id: str,
    row_number: int,
    new_status: str,
    uncheck_send_box: bool = True  # NEW parameter
) -> None:
    """
    Update email status after sending.

    Args:
        spreadsheet_id: Target spreadsheet ID
        row_number: Row number to update (2 = first data row)
        new_status: New status (e.g., '답장완료')
        uncheck_send_box: If True, uncheck '발송여부' checkbox
    """
    # Update status (column A)
    self.service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"Emails!A{row_number}",
        valueInputOption="RAW",
        body={"values": [[new_status]]},
    ).execute()

    # Uncheck send box (column H)
    if uncheck_send_box:
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"Emails!H{row_number}",
            valueInputOption="RAW",
            body={"values": [[False]]},
        ).execute()
```

**Acceptance Criteria**:
- ✅ Updates status column
- ✅ Optionally unchecks send box
- ✅ Single-row update (not batch)

---

## Task 3: Update Main Workflow

**File**: `email_classifier/main_sheets.py`

**Estimated Time**: 25 minutes

### 3.1 Modify Draft Creation Loop

**Location**: Line 212-227 (STEP 5)

**Current Code**:
```python
for email, draft in zip(emails_needing_response, drafts):
    try:
        gmail.create_draft(
            thread_id=email["thread_id"],
            to=email["sender"],
            subject=draft["subject"],
            body=draft["body"],
        )
        print(f"   ✅ Draft: {email['subject'][:50]}...")
```

**New Code**:
```python
draft_objects = []  # Store draft objects

for email, draft in zip(emails_needing_response, drafts):
    try:
        # Create HTML draft
        draft_obj = gmail.create_draft(
            thread_id=email["thread_id"],
            to=email["sender"],
            subject=draft["subject"],
            body=draft["body"],
            is_html=True,  # NEW: Enable HTML
        )

        draft_objects.append(draft_obj)

        # Extract draft ID
        draft_id = draft_obj.get("id", "")
        print(f"   ✅ Draft: {email['subject'][:50]}... (ID: {draft_id[:10]}...)")

    except Exception as e:
        print(f"   ⚠️  Failed: {e}")
        draft_objects.append(None)  # Placeholder for failed drafts
```

**Acceptance Criteria**:
- ✅ Enables HTML mode
- ✅ Stores draft objects for later use
- ✅ Prints draft ID for debugging

---

### 3.2 Update Sheets Recording

**Location**: Line 140-163 (STEP 4) - Move after draft generation

**Reorganize Steps**:
```python
# OLD ORDER:
# STEP 3: Classify
# STEP 4: Update Sheets (before drafts exist!)
# STEP 5: Generate Drafts

# NEW ORDER:
# STEP 3: Classify
# STEP 4: Generate Drafts
# STEP 5: Update Sheets (with draft links)
```

**New Code** (after draft generation):
```python
# === STEP 5: UPDATE GOOGLE SHEETS ===
print("\n" + "="*80)
print("STEP 5: UPDATE GOOGLE SHEETS")
print("="*80)

print("\n📊 Adding emails to spreadsheet...")

for email, draft_obj in zip(emails_needing_response, draft_objects):
    classification = email.get('classification', {})

    # Extract draft info
    if draft_obj:
        draft_id = draft_obj.get("id", "")
        draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'
    else:
        draft_id = ""
        draft_link = ""

    email_data = {
        "status": "needs_response",
        "priority": classification.get('priority', 3),
        "subject": email.get('subject', ''),
        "sender": email.get('sender', ''),
        "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "body": email.get('body', email.get('snippet', '')),
        "thread_id": email.get('thread_id', ''),
    }

    sheets.add_email_row(
        spreadsheet_id,
        email_data,
        draft_id=draft_id,
        draft_link=draft_link,
    )

print(f"✅ Added {len(emails_needing_response)} emails with draft links")
```

**Acceptance Criteria**:
- ✅ Drafts created before Sheets update
- ✅ Draft links included in Sheets
- ✅ Handles failed drafts gracefully (empty draft_id)

---

### 3.3 Modify Batch Send Logic

**Location**: Line 233-276 (STEP 6)

**Current Code**:
```python
emails_to_send = sheets.get_emails_to_send(spreadsheet_id)

send_data = [
    {
        "to": email['draft_to'] or email['sender'],
        "subject": email['subject'],
        "body": email['draft_body'],
        "cc": email.get('draft_cc'),
        "thread_id": email.get('thread_id'),
    }
    for email in emails_to_send
]

results = gmail.batch_send_emails(send_data)
```

**New Code**:
```python
print("\n🔍 Checking spreadsheet for drafts to send...")
drafts_to_send = sheets.get_drafts_to_send(spreadsheet_id)

if not drafts_to_send:
    print("   No drafts marked for sending")
else:
    print(f"   Found {len(drafts_to_send)} drafts marked:")

    for draft_info in drafts_to_send:
        print(f"   - {draft_info['subject'][:50]} (to: {draft_info['sender']})")

    confirm = input(f"\n⚠️  Send {len(drafts_to_send)} drafts? (yes/no): ").strip().lower()

    if confirm == 'yes':
        print("\n📤 Sending drafts...")

        draft_ids = [d['draft_id'] for d in drafts_to_send]
        results = gmail.batch_send_drafts(draft_ids)  # NEW function

        # Update spreadsheet status
        for result, draft_info in zip(results, drafts_to_send):
            if result['success']:
                sheets.update_email_status(
                    spreadsheet_id,
                    draft_info['row_number'],
                    "답장완료",
                    uncheck_send_box=True,
                )
                print(f"   ✅ Sent: {draft_info['subject'][:50]}...")
            else:
                error_msg = result['error']
                print(f"   ❌ Failed: {draft_info['subject'][:50]}... - {error_msg}")

        success_count = sum(1 for r in results if r['success'])
        print(f"\n📧 Successfully sent {success_count}/{len(results)} drafts")
```

**Acceptance Criteria**:
- ✅ Uses `get_drafts_to_send()` instead of `get_emails_to_send()`
- ✅ Calls `batch_send_drafts()` instead of `batch_send_emails()`
- ✅ Updates checkbox and status after send
- ✅ Shows detailed error messages

---

## Task 4: Update Documentation

**File**: `README.md`

**Estimated Time**: 15 minutes

### 4.1 Update Feature List

**Location**: Line 6-16

**Changes**:
```markdown
## 핵심 특징

- ✅ **API 비용 $0** - Claude Code 대화로 처리
- ✅ **Gmail HTML 초안** - 서식 유지 (볼드, 색상, 서명) (NEW!)
- ✅ **Google Sheets 통합** - 워크플로우 대시보드
- ✅ **개선된 우선순위 시스템**
  - 첫 연락 → 최고 우선순위
  - 발신 가중치 (내가 보낸 메일 2배 중요도)
  - 수신만 한 메일 → 낮은 우선순위
- ✅ **하이브리드 발송** - Gmail 수정사항 100% 반영 (NEW!)
  - Sheets에서 체크 → Gmail 초안 그대로 발송
  - 사용자 서식 편집 보존
```

---

### 4.2 Add Workflow Section

**Location**: After "빠른 시작" section

**New Section**:
```markdown
## 워크플로우

### Gmail + Sheets 하이브리드 방식

```
1. 프로그램 실행 → Gmail HTML 초안 생성
2. Sheets 업데이트 → 초안 링크 포함
3. Sheets에서 "Gmail 초안" 클릭
4. Gmail 앱에서 서식 수정 (볼드, 색상, 서명 등)
5. Sheets에서 "발송여부" 체크
6. 프로그램 재실행 → "Batch send" 선택
7. ✅ Gmail 수정사항 포함하여 발송!
```

**핵심 원칙:**
- Gmail = 콘텐츠 저장소 (서식 보존)
- Sheets = 워크플로우 대시보드 (관리)
- 발송 시 Gmail 초안을 그대로 전송
```

---

### 4.3 Update Spreadsheet Columns

**Location**: Line 189-197

**Changes**:
```markdown
### 3. Google Sheets 통합

**스프레드시트 컬럼:**
- 상태 (답장필요/불필요/완료)
- 우선순위 (1-5)
- 제목, 발신자, 받은시간
- 내용미리보기 (200자) ← 변경: 전체 내용 대신 미리보기
- **Gmail 초안 (클릭하여 열기)** ← NEW
- 발송여부 (체크박스)
- Draft ID, Thread ID (숨김)

**워크플로우:**
1. 프로그램 실행 → 이메일 자동 분류
2. Gmail HTML 초안 생성
3. Sheets에 초안 링크 기록
4. Sheets에서 "Gmail 초안" 클릭 → Gmail 앱에서 수정
5. 발송여부 체크박스 체크
6. 프로그램 재실행 → "Batch send"
7. Gmail 초안을 그대로 발송 (수정사항 보존)
8. 상태 "답장완료"로 자동 업데이트
```

---

## Task 5: Testing

**Estimated Time**: 30 minutes

### 5.1 Manual Test Script

Create `tests/test_hybrid_workflow.py`:

```python
"""
Manual test script for v0.4.0 hybrid workflow.

Run this after implementing all changes.
"""

def test_html_draft_creation():
    """Test 1: HTML draft creation"""
    print("\n=== Test 1: HTML Draft Creation ===")

    from email_classifier.gmail_client import GmailClient

    gmail = GmailClient()

    html_body = """
    <p>Hello,</p>
    <p>Thank you for your message. Here are my thoughts:</p>
    <ul>
        <li><b>Point 1:</b> This is important</li>
        <li><i>Point 2:</i> This is emphasized</li>
    </ul>
    <p>Best regards,<br>
    <span style="color: #666;">Your Name</span></p>
    """

    draft = gmail.create_draft(
        thread_id="test_thread_id",
        to="test@example.com",
        subject="Test HTML Draft",
        body=html_body,
        is_html=True,
    )

    assert 'id' in draft, "Draft should have ID"
    print(f"✅ Created HTML draft: {draft['id']}")

    # Manual verification
    print(f"\n📧 Open Gmail drafts and verify formatting:")
    print(f"   https://mail.google.com/mail/#drafts?compose={draft['id']}")
    input("   Press Enter after verifying in Gmail...")


def test_send_existing_draft():
    """Test 2: Send existing draft (preserves edits)"""
    print("\n=== Test 2: Send Existing Draft ===")

    from email_classifier.gmail_client import GmailClient

    gmail = GmailClient()

    # Create draft
    draft = gmail.create_draft(
        thread_id="test_thread_id",
        to="test@example.com",
        subject="Test Draft Send",
        body="<p>Original text</p>",
        is_html=True,
    )

    draft_id = draft['id']
    print(f"✅ Created draft: {draft_id}")

    # Manual edit step
    print(f"\n📝 Now edit this draft in Gmail:")
    print(f"   https://mail.google.com/mail/#drafts?compose={draft_id}")
    print(f"   - Add bold text")
    print(f"   - Add your signature")
    print(f"   - Change colors")
    input("   Press Enter after editing...")

    # Send draft
    confirm = input(f"\n⚠️  Send this draft to test@example.com? (yes/no): ")
    if confirm.lower() == 'yes':
        sent = gmail.send_draft(draft_id)
        print(f"✅ Sent: {sent.get('id')}")

        print(f"\n📬 Check sent email in Gmail to verify edits were preserved")
    else:
        print("❌ Skipped send test")


def test_sheets_draft_link():
    """Test 3: Sheets with draft link"""
    print("\n=== Test 3: Sheets Draft Link ===")

    from email_classifier.gmail_client import GmailClient
    from email_classifier.sheets_client import SheetsClient
    from datetime import datetime

    gmail = GmailClient()
    sheets = SheetsClient()

    # Create test spreadsheet
    spreadsheet_id = sheets.create_email_tracker(
        title=f"Test Hybrid Workflow - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    print(f"✅ Created spreadsheet: {spreadsheet_id}")

    # Create draft
    draft = gmail.create_draft(
        thread_id="test_thread",
        to="test@example.com",
        subject="Test Spreadsheet Link",
        body="<p>Test body</p>",
        is_html=True,
    )

    draft_id = draft['id']
    draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'

    # Add to spreadsheet
    email_data = {
        "status": "needs_response",
        "priority": 5,
        "subject": "Test Email",
        "sender": "test@example.com",
        "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "body": "Test email body for preview",
        "thread_id": "test_thread",
    }

    sheets.add_email_row(
        spreadsheet_id,
        email_data,
        draft_id=draft_id,
        draft_link=draft_link,
    )

    print(f"✅ Added email row with draft link")

    # Verification
    print(f"\n📊 Open spreadsheet and verify:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print(f"   - Column G should have clickable '열기' link")
    print(f"   - Clicking link should open Gmail draft")
    print(f"   - Columns I and J should be hidden")
    input("   Press Enter after verifying...")


def test_batch_send_with_edits():
    """Test 4: Batch send preserves Gmail edits"""
    print("\n=== Test 4: Batch Send with Gmail Edits ===")

    from email_classifier.gmail_client import GmailClient
    from email_classifier.sheets_client import SheetsClient
    from datetime import datetime

    gmail = GmailClient()
    sheets = SheetsClient()

    # Create spreadsheet
    spreadsheet_id = sheets.create_email_tracker(
        title=f"Test Batch Send - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # Create 2 drafts
    draft_ids = []
    for i in range(2):
        draft = gmail.create_draft(
            thread_id=f"test_thread_{i}",
            to="test@example.com",
            subject=f"Test Email {i+1}",
            body=f"<p>Original text {i+1}</p>",
            is_html=True,
        )

        draft_id = draft['id']
        draft_ids.append(draft_id)

        # Add to spreadsheet
        email_data = {
            "status": "needs_response",
            "priority": 3,
            "subject": f"Test Email {i+1}",
            "sender": "test@example.com",
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "body": f"Test body {i+1}",
            "thread_id": f"test_thread_{i}",
        }

        draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'

        sheets.add_email_row(
            spreadsheet_id,
            email_data,
            draft_id=draft_id,
            draft_link=draft_link,
        )

    print(f"✅ Created {len(draft_ids)} test drafts")

    # Manual edit step
    print(f"\n📝 Edit drafts in Gmail:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print(f"   - Click each '열기' link")
    print(f"   - Add different formatting to each draft")
    print(f"   - Then check the '발송여부' boxes")
    input("   Press Enter after editing and checking boxes...")

    # Batch send
    drafts_to_send = sheets.get_drafts_to_send(spreadsheet_id)
    print(f"\n📤 Found {len(drafts_to_send)} drafts to send")

    confirm = input(f"\n⚠️  Send {len(drafts_to_send)} drafts? (yes/no): ")
    if confirm.lower() == 'yes':
        draft_ids_to_send = [d['draft_id'] for d in drafts_to_send]
        results = gmail.batch_send_drafts(draft_ids_to_send)

        for result in results:
            if result['success']:
                print(f"   ✅ Sent: {result['draft_id'][:10]}...")
            else:
                print(f"   ❌ Failed: {result['error']}")

        print(f"\n📬 Check sent emails to verify formatting was preserved")
    else:
        print("❌ Skipped batch send test")


if __name__ == "__main__":
    print("=" * 80)
    print("v0.4.0 Hybrid Workflow Test Suite")
    print("=" * 80)

    tests = [
        test_html_draft_creation,
        test_send_existing_draft,
        test_sheets_draft_link,
        test_batch_send_with_edits,
    ]

    for i, test_func in enumerate(tests, 1):
        try:
            test_func()
            print(f"\n✅ Test {i}/{len(tests)} passed\n")
        except Exception as e:
            print(f"\n❌ Test {i}/{len(tests)} failed: {e}\n")
            import traceback
            traceback.print_exc()

            cont = input("Continue with remaining tests? (y/n): ")
            if cont.lower() != 'y':
                break

    print("\n" + "=" * 80)
    print("Test suite complete!")
    print("=" * 80)
```

**Run Tests**:
```bash
python -m tests.test_hybrid_workflow
```

---

## Task 6: Commit and Deploy

**Estimated Time**: 10 minutes

### 6.1 Git Commit

```bash
git add .
git commit -m "feat(v0.4.0): Implement hybrid Gmail+Sheets architecture

Major Changes:
✨ Gmail HTML Draft Support
  - create_draft() now supports HTML formatting
  - User edits in Gmail app preserved
  - send_draft() sends existing draft by ID

✨ Sheets Draft Links
  - Gmail draft hyperlinks in spreadsheet
  - Simplified schema (removed duplicate content)
  - Hidden Draft ID column for API operations

✨ Batch Send Enhancement
  - batch_send_drafts() sends Gmail drafts (not recreated emails)
  - Preserves all user formatting edits
  - Status auto-update after send

Breaking Changes:
  - Spreadsheet schema changed (new columns, removed old columns)
  - batch_send_emails() deprecated (use batch_send_drafts())

Migration:
  - Existing v0.3.0 spreadsheets still readable
  - Run email-classify-sheets to create new format spreadsheet

Files Changed:
  - email_classifier/gmail_client.py
  - email_classifier/sheets_client.py
  - email_classifier/main_sheets.py
  - README.md
  - spec.md (NEW)
  - plan.md (NEW)
  - tasks.md (NEW)
"
```

### 6.2 Version Bump

**File**: `pyproject.toml`

```toml
[project]
name = "simple-email-classifier"
version = "0.4.0"  # Bumped from 0.3.0
description = "Gmail email classifier with Claude Code + Hybrid Gmail+Sheets architecture (no API costs!)"
```

### 6.3 Push to GitHub

```bash
git push origin main
```

### 6.4 Create GitHub Release

```bash
gh release create v0.4.0 \
  --title "v0.4.0 - Hybrid Gmail+Sheets Architecture" \
  --notes "See CHANGELOG.md for details"
```

---

## Completion Checklist

- [ ] Task 1: Gmail client HTML support (3 functions)
- [ ] Task 2: Sheets client draft links (4 modifications)
- [ ] Task 3: Main workflow updates (3 sections)
- [ ] Task 4: README documentation (3 sections)
- [ ] Task 5: Manual testing (4 test scenarios)
- [ ] Task 6: Git commit and release

**Total Estimated Time**: ~2 hours

---

## Rollback Plan

If issues arise:

1. **Revert Code**:
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Deprecation Notice**:
   - v0.4.0 is opt-in (`email-classify-sheets`)
   - v0.3.0 still works (`email-classify` without Sheets)

3. **User Migration**:
   - No forced migration
   - Users can continue with v0.3.0 workflow
