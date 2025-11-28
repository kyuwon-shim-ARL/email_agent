# Implementation Plan - Hybrid Gmail Draft + Sheets

## Overview

Implement v0.4.0 hybrid architecture where Gmail stores rich-formatted drafts and Sheets manages workflow state.

**Goal**: Preserve user formatting edits in Gmail while using Sheets for batch management.

---

## Architecture Changes

### Before (v0.3.0 - Broken)
```
Program → Sheets (full text) → Batch send (recreate from text) ❌
                                ↳ User Gmail edits LOST
```

### After (v0.4.0 - Correct)
```
Program → Gmail (HTML drafts) ← User edits in Gmail app
            ↓
          Sheets (links + IDs)
            ↓
        Batch send (send draft by ID) ✅
            ↳ User Gmail edits PRESERVED
```

---

## Component Design

### 1. Gmail Client Enhancement (`gmail_client.py`)

#### 1.1 HTML Draft Support

**Current Code** (line 120-157):
```python
def create_draft(self, thread_id: str, to: str, subject: str, body: str):
    message = MIMEText(body)  # ❌ Plain text only
```

**New Implementation**:
```python
def create_draft(
    self,
    thread_id: str,
    to: str,
    subject: str,
    body: str,
    is_html: bool = True  # NEW parameter
) -> dict[str, Any]:
    """
    Create a draft reply in Gmail with HTML support.

    Args:
        thread_id: Thread ID to reply to
        to: Recipient email address
        subject: Email subject
        body: Draft email body (HTML or plain text)
        is_html: If True, body is treated as HTML

    Returns:
        Draft object with 'id' and 'message' fields
    """
    import base64
    from email.mime.text import MIMEText

    # Create message with appropriate content type
    message = MIMEText(body, 'html' if is_html else 'plain', 'utf-8')
    message["to"] = to
    message["subject"] = subject

    # Encode message
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Create draft
    draft = (
        self.service.users()
        .drafts()
        .create(
            userId="me",
            body={"message": {"raw": raw, "threadId": thread_id}},
        )
        .execute()
    )

    return draft  # Returns: {'id': 'r123...', 'message': {...}}
```

**Return Value Example**:
```json
{
  "id": "r1234567890abcdef",
  "message": {
    "id": "18c5f...",
    "threadId": "18c5e...",
    "labelIds": ["DRAFT"]
  }
}
```

---

#### 1.2 Send Existing Draft

**New Function** (insert after `create_draft()`):
```python
def send_draft(self, draft_id: str) -> dict[str, Any]:
    """
    Send an existing Gmail draft by ID.

    This preserves all user edits made in the Gmail app.

    Args:
        draft_id: Draft ID from create_draft() or Sheets

    Returns:
        Sent message information

    Raises:
        HttpError: If draft not found or send fails
    """
    sent = (
        self.service.users()
        .drafts()
        .send(userId="me", body={"id": draft_id})
        .execute()
    )

    return sent  # Returns: {'id': '18c5f...', 'threadId': '18c5e...', 'labelIds': ['SENT']}
```

---

#### 1.3 Batch Send Drafts (Replace Old Logic)

**Current Code** (line 202-238):
```python
def batch_send_emails(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for email in emails:
        sent = self.send_email(  # ❌ Recreates email from text
            to=email.get("to", ""),
            subject=email.get("subject", ""),
            body=email.get("body", ""),
            # ...
        )
```

**New Implementation**:
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

**Keep Old Function** (for backward compatibility):
```python
def batch_send_emails(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    DEPRECATED: Use batch_send_drafts() instead.

    This recreates emails from text and loses Gmail edits.
    """
    # ... existing code ...
```

---

### 2. Sheets Client Enhancement (`sheets_client.py`)

#### 2.1 Updated Spreadsheet Schema

**Current Columns** (line 85-99):
```python
headers = [
    "상태", "우선순위", "제목", "발신자",
    "수신(To)", "수신(CC)", "받은시간",
    "메일내용",      # ❌ Remove - clutters sheet
    "답장초안",      # ❌ Remove - loses formatting
    "답장수신자",    # ❌ Remove - redundant
    "답장CC",        # ❌ Remove - rarely used
    "발송여부", "Thread ID"
]
```

**New Schema**:
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

**Column Formatting**:
```python
# In create_email_tracker()
requests = [
    # ... existing header formatting ...

    # Hide columns I and J (Draft ID, Thread ID)
    {
        "updateDimensionProperties": {
            "range": {
                "sheetId": 0,
                "dimension": "COLUMNS",
                "startIndex": 8,  # Column I
                "endIndex": 10,   # Column J
            },
            "properties": {"hiddenByUser": True},
            "fields": "hiddenByUser",
        }
    },

    # Set column widths
    {
        "updateDimensionProperties": {
            "range": {
                "sheetId": 0,
                "dimension": "COLUMNS",
                "startIndex": 6,  # Gmail 초안
                "endIndex": 7,
            },
            "properties": {"pixelSize": 120},
            "fields": "pixelSize",
        }
    },
]
```

---

#### 2.2 Add Email Row with Draft Link

**Current Code** (line 137-179):
```python
def add_email_row(self, spreadsheet_id: str, email_data: dict[str, Any]) -> None:
    row = [
        status,
        email_data.get("priority", 3),
        email_data.get("subject", ""),
        email_data.get("sender", ""),
        email_data.get("to", ""),
        email_data.get("cc", ""),
        email_data.get("date", ""),
        email_data.get("body", "")[:500],  # Full body ❌
        email_data.get("draft_body", ""),  # Draft text ❌
        # ...
    ]
```

**New Implementation**:
```python
def add_email_row(
    self,
    spreadsheet_id: str,
    email_data: dict[str, Any],
    draft_id: str = "",      # NEW
    draft_link: str = "",    # NEW
) -> None:
    """
    Add email to spreadsheet with draft link.

    Args:
        spreadsheet_id: Target spreadsheet ID
        email_data: Email metadata
        draft_id: Gmail draft ID (e.g., 'r1234...')
        draft_link: Full Gmail draft URL
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
        email_data.get("body", "")[:200],                # F: Preview only
        draft_link,                                      # G: Clickable link
        False,                                           # H: Checkbox unchecked
        draft_id,                                        # I: Hidden
        email_data.get("thread_id", ""),                 # J: Hidden
    ]

    # Append row
    self.service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Emails!A:J",  # Updated range
        valueInputOption="USER_ENTERED",  # Changed from RAW to support formulas
        body={"values": [row]},
    ).execute()
```

**Draft Link Format**:
```python
# In main_sheets.py, generate link:
draft_id = draft['id']
draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'
```

---

#### 2.3 Get Drafts to Send

**New Function**:
```python
def get_drafts_to_send(self, spreadsheet_id: str) -> list[dict[str, Any]]:
    """
    Get draft IDs for emails marked for sending.

    Returns:
        List of dicts with draft_id, subject, sender, row_number

    Example:
        [
            {
                'draft_id': 'r1234...',
                'subject': 'Re: Meeting',
                'sender': 'boss@example.com',
                'row_number': 2
            }
        ]
    """
    result = self.service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Emails!A2:J",  # Skip header
    ).execute()

    rows = result.get("values", [])
    drafts_to_send = []

    for i, row in enumerate(rows, start=2):  # Row 2 = first data row
        if len(row) < 9:
            continue

        send_checkbox = row[7] if len(row) > 7 else ""  # Column H
        draft_id = row[8] if len(row) > 8 else ""       # Column I

        # Check if marked for sending
        if send_checkbox in ["TRUE", "True", True] and draft_id:
            drafts_to_send.append({
                "draft_id": draft_id,
                "subject": row[2] if len(row) > 2 else "",
                "sender": row[3] if len(row) > 3 else "",
                "row_number": i,
            })

    return drafts_to_send
```

---

#### 2.4 Update Row Status

**Modified Function**:
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
        row_number: Row number (2 = first data row)
        new_status: New status (e.g., '답장완료')
        uncheck_send_box: If True, uncheck '발송여부'
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

---

### 3. Main Workflow Changes (`main_sheets.py`)

#### 3.1 Draft Creation Step (Line ~212-227)

**Current Code**:
```python
# Create Gmail draft
try:
    gmail.create_draft(
        thread_id=email["thread_id"],
        to=email["sender"],
        subject=draft["subject"],
        body=draft["body"],  # Plain text
    )
```

**New Code**:
```python
# Create Gmail draft with HTML
try:
    draft_obj = gmail.create_draft(
        thread_id=email["thread_id"],
        to=email["sender"],
        subject=draft["subject"],
        body=draft["body"],
        is_html=True,  # NEW: Enable HTML formatting
    )

    # Extract draft ID
    draft_id = draft_obj.get("id", "")

    # Generate draft link
    draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'

    print(f"   ✅ Draft: {email['subject'][:50]}... (ID: {draft_id[:8]}...)")

except Exception as e:
    print(f"   ⚠️  Failed: {e}")
    draft_id = ""
    draft_link = ""
```

---

#### 3.2 Sheets Update Step (Line ~140-161)

**Current Code**:
```python
for email in emails:
    classification = email.get('classification', {})

    email_data = {
        "status": status,
        "priority": classification.get('priority', 3),
        "subject": email.get('subject', ''),
        "sender": email.get('sender', ''),
        "to": "me",
        "cc": "",
        "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "body": email.get('body', email.get('snippet', '')),
        "draft_body": "",  # Not yet generated
        # ...
    }

    sheets.add_email_row(spreadsheet_id, email_data)
```

**New Code**:
```python
# After draft generation, update Sheets with draft info
for email, draft, draft_obj in zip(emails_needing_response, drafts, draft_objects):
    classification = email.get('classification', {})
    draft_id = draft_obj.get("id", "")
    draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'

    email_data = {
        "status": "needs_response",
        "priority": classification.get('priority', 3),
        "subject": email.get('subject', ''),
        "sender": email.get('sender', ''),
        "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "body": email.get('body', email.get('snippet', '')),  # Preview
        "thread_id": email.get('thread_id', ''),
    }

    sheets.add_email_row(
        spreadsheet_id,
        email_data,
        draft_id=draft_id,       # NEW
        draft_link=draft_link,   # NEW
    )
```

---

#### 3.3 Batch Send Step (Line ~233-276)

**Current Code**:
```python
if send_choice == 'y':
    emails_to_send = sheets.get_emails_to_send(spreadsheet_id)

    send_data = [
        {
            "to": email['draft_to'] or email['sender'],
            "subject": email['subject'],
            "body": email['draft_body'],  # ❌ Text from Sheets
            "cc": email.get('draft_cc'),
            "thread_id": email.get('thread_id'),
        }
        for email in emails_to_send
    ]

    results = gmail.batch_send_emails(send_data)  # ❌ Recreates emails
```

**New Code**:
```python
if send_choice == 'y':
    print("\n🔍 Checking spreadsheet for drafts to send...")
    drafts_to_send = sheets.get_drafts_to_send(spreadsheet_id)

    if not drafts_to_send:
        print("   No drafts marked for sending")
    else:
        print(f"   Found {len(drafts_to_send)} drafts marked for sending")

        # Show what will be sent
        for draft in drafts_to_send:
            print(f"   - {draft['subject'][:50]} (to: {draft['sender']})")

        confirm = input(f"\n⚠️  Send {len(drafts_to_send)} drafts? (yes/no): ").strip().lower()

        if confirm == 'yes':
            print("\n📤 Sending drafts...")

            draft_ids = [d['draft_id'] for d in drafts_to_send]
            results = gmail.batch_send_drafts(draft_ids)  # ✅ Sends existing drafts

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
                    print(f"   ❌ Failed: {draft_info['subject'][:50]}... - {result['error']}")

            success_count = sum(1 for r in results if r['success'])
            print(f"\n📧 Sent {success_count}/{len(results)} drafts")
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1-4: Email Classification (unchanged)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Draft Generation (MODIFIED)                             │
│                                                                  │
│  Claude generates HTML reply                                    │
│       ↓                                                          │
│  gmail.create_draft(body=html, is_html=True)                    │
│       ↓                                                          │
│  Returns: draft_obj = {'id': 'r1234...', 'message': {...}}      │
│       ↓                                                          │
│  Extract draft_id = 'r1234...'                                  │
│       ↓                                                          │
│  Generate link = '=HYPERLINK("https://mail.google.com/...", ..)' │
│       ↓                                                          │
│  sheets.add_email_row(draft_id=..., draft_link=...)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTIONS (outside program)                                   │
│                                                                  │
│  1. Opens Google Sheets                                         │
│  2. Clicks "Gmail 초안" link → Opens draft in Gmail             │
│  3. Edits formatting (bold, colors, signature)                  │
│  4. Gmail auto-saves edits                                      │
│  5. Returns to Sheets, checks "발송여부"                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Batch Send (MODIFIED)                                   │
│                                                                  │
│  sheets.get_drafts_to_send(spreadsheet_id)                      │
│       ↓                                                          │
│  Returns: [{'draft_id': 'r1234...', row_number: 2}, ...]        │
│       ↓                                                          │
│  gmail.batch_send_drafts(draft_ids=['r1234...', ...])           │
│       ↓                                                          │
│  For each draft_id:                                             │
│    - gmail.send_draft(draft_id)  ← Sends existing Gmail draft  │
│    - sheets.update_email_status(row, "답장완료")                │
│       ↓                                                          │
│  ✅ User edits preserved in sent emails!                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Testing Plan

### Unit Tests

1. **Gmail Client**
   - `test_create_html_draft()` - Verify HTML MIME type
   - `test_send_draft_by_id()` - Verify draft sent, not recreated
   - `test_batch_send_preserves_edits()` - Mock user edits

2. **Sheets Client**
   - `test_add_row_with_draft_link()` - Verify HYPERLINK formula
   - `test_get_drafts_to_send()` - Verify checkbox filtering
   - `test_hidden_columns()` - Verify Draft ID column hidden

### Integration Tests

1. **End-to-End Workflow**
   ```python
   # Create draft
   draft = gmail.create_draft(..., is_html=True)
   draft_id = draft['id']

   # Add to Sheets
   sheets.add_email_row(..., draft_id=draft_id)

   # Simulate user edit in Gmail (manual step)
   input("Edit the draft in Gmail, then press Enter")

   # Send draft
   result = gmail.send_draft(draft_id)

   # Verify sent email contains edits (manual verification)
   ```

2. **Error Cases**
   - Draft deleted before send → Graceful error
   - Network timeout → Retry logic
   - Invalid HTML → Fallback to plain text

---

## Rollout Plan

### Phase 1: Code Changes (This PR)
- ✅ Update gmail_client.py (HTML + send_draft)
- ✅ Update sheets_client.py (new schema + draft links)
- ✅ Update main_sheets.py (connect components)
- ✅ Update README.md (new workflow docs)

### Phase 2: Testing
- Test HTML draft creation
- Test user edit preservation
- Test batch send with draft IDs

### Phase 3: Documentation
- Update INSTALLATION.md (no changes needed)
- Update GETTING_STARTED.md (new workflow screenshots)
- Create migration guide for v0.3.0 users

### Phase 4: Release
- Tag v0.4.0
- GitHub release notes
- Deprecation notice for old batch_send_emails()

---

## Migration Notes for v0.3.0 Users

**Breaking Changes:**
- Spreadsheet schema changed (columns removed/added)
- `batch_send_emails()` deprecated → use `batch_send_drafts()`

**Migration Steps:**
1. Delete old token.json (scopes unchanged, but good practice)
2. Run `email-classify-sheets` to create new spreadsheet
3. Old spreadsheets will still work (read-only)

**Backward Compatibility:**
- `email-classify` (non-Sheets) still works
- `batch_send_emails()` function kept but deprecated
