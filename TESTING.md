# v0.4.0 테스트 가이드

## 🎯 테스트 목표

v0.4.0의 핵심 기능인 **하이브리드 아키텍처**가 제대로 작동하는지 확인:
- Gmail HTML 초안 생성
- Sheets에 초안 링크 기록
- 사용자가 Gmail에서 수정한 내용이 발송 시 반영되는지

---

## 📝 사전 준비

### 1. 패키지 재설치

```bash
cd email_agent

# 가상환경 활성화
source .venv/bin/activate

# 새 버전 설치
pip install -e .

# 버전 확인
python -c "import importlib.metadata; print(importlib.metadata.version('simple-email-classifier'))"
# 출력: 0.4.0
```

### 2. 권한 확인

기존 `token.json`이 있다면 그대로 사용 가능합니다. 필요한 스코프는 이미 포함되어 있습니다:
- `gmail.readonly`
- `gmail.compose`
- `gmail.send`
- `spreadsheets`

---

## 🧪 테스트 시나리오

### 시나리오 1: 기본 워크플로우 (추천)

**목표**: HTML 초안 생성 → Sheets 링크 → Gmail 수정 → 발송 전체 흐름 테스트

#### 1.1 프로그램 실행

```bash
email-classify-sheets
```

#### 1.2 STEP 1: 스타일 학습

```bash
cat /tmp/email_classifier/analyze_style.txt
```

- Claude Code에 붙여넣기
- JSON 응답 복사
- 프로그램에 붙여넣기

#### 1.3 STEP 2-3: 분류

- 최근 이메일 2-3개만 처리되도록 `max_results=3` 정도로 설정하는 것 권장
- Claude에게 분류 프롬프트 전달
- JSON 응답 받아서 붙여넣기

#### 1.4 STEP 4: 초안 생성 (중요!)

```bash
cat /tmp/email_classifier/generate_drafts.txt
```

- Claude에게 전달
- **JSON 응답을 받으면, `body` 필드에 HTML이 포함되어 있는지 확인!**

예시:
```json
[
  {
    "email_index": 1,
    "subject": "Re: 회의 일정",
    "body": "<p>안녕하세요,</p><p><b>회의 일정</b>에 대해 답변드립니다...</p>",
    "tone": "formal"
  }
]
```

- 프로그램에 붙여넣기
- **터미널 출력 확인**: `Draft: ... (ID: r1234567...)`

**✅ 확인사항**:
```
✅ Draft: 회의 일정... (ID: r12345678...)
✅ Draft: 프로젝트 진행... (ID: r87654321...)
```

Draft ID가 출력되면 성공!

#### 1.5 STEP 5: Sheets 확인

터미널에 출력된 Spreadsheet 링크 클릭:
```
📊 Spreadsheet: https://docs.google.com/spreadsheets/d/ABCD1234...
```

**✅ 확인사항**:
1. 컬럼 G ("Gmail 초안")에 **"열기"** 링크가 있는지
2. 컬럼 I, J가 **숨겨져 있는지** (보이면 안 됨)
3. 컬럼 F ("내용미리보기")가 **200자 정도**인지

#### 1.6 Gmail 초안 열기 및 수정 (핵심!)

1. Sheets에서 **"Gmail 초안"** 컬럼의 **"열기"** 클릭
2. Gmail 초안이 열리면:
   - 텍스트 **볼드** 추가
   - 색상 변경
   - 서명 추가
   - 중요한 문구 **강조**
3. 초안 저장 (Gmail 자동 저장됨)

**✅ 확인사항**:
- Gmail 초안 화면이 정상적으로 열림
- 서식 편집 가능 (볼드, 색상 등)

#### 1.7 발송 체크

1. Sheets로 돌아가기
2. **"발송여부"** 컬럼 (H) 체크박스 클릭

#### 1.8 일괄 발송

```bash
# 같은 터미널에서 계속
📧 Send drafts marked in spreadsheet? (y/N): y

# 확인
⚠️  Send 2 drafts? (yes/no): yes
```

**✅ 확인사항**:
```
📤 Sending drafts...
   ✅ Sent: 회의 일정...
   ✅ Sent: 프로젝트 진행...

📧 Successfully sent 2/2 drafts
```

#### 1.9 최종 확인 (가장 중요!)

1. Gmail **Sent** 폴더 열기
2. 방금 보낸 이메일 클릭
3. **Gmail에서 수정한 서식이 그대로 있는지 확인!**

**✅ 성공 기준**:
- 볼드 처리한 텍스트가 볼드로 보임
- 색상 변경한 부분이 색상 유지
- 추가한 서명이 포함됨

**❌ 실패 예시** (v0.3.0 문제):
- 모든 서식이 사라지고 평문으로만 보임
- 수정한 내용이 반영 안 됨

---

### 시나리오 2: HTML 생성 확인 (빠른 테스트)

**목표**: HTML이 제대로 생성되는지만 빠르게 확인

```bash
python3 << 'EOF'
from email_classifier.gmail_client import GmailClient

gmail = GmailClient()

# HTML 초안 생성
draft = gmail.create_draft(
    thread_id="test_thread",
    to="your_test_email@gmail.com",  # 본인 이메일 주소
    subject="Test HTML Draft",
    body="<p>안녕하세요,</p><p><b>볼드 텍스트</b>와 <i>이탤릭</i>입니다.</p><ul><li>항목 1</li><li>항목 2</li></ul>",
    is_html=True
)

print(f"✅ Draft created: {draft['id']}")
print(f"📧 Check: https://mail.google.com/mail/#drafts")
EOF
```

**✅ 확인**:
1. Gmail Drafts 폴더 열기
2. 가장 최근 초안 클릭
3. **볼드, 이탤릭, 리스트**가 서식으로 보이는지

---

### 시나리오 3: Draft 발송 테스트

**목표**: `send_draft()`가 기존 초안을 그대로 발송하는지 확인

```bash
python3 << 'EOF'
from email_classifier.gmail_client import GmailClient

gmail = GmailClient()

# 1. HTML 초안 생성
draft = gmail.create_draft(
    thread_id="test_thread",
    to="your_test_email@gmail.com",  # 본인 이메일
    subject="Test Draft Send",
    body="<p>Original text</p>",
    is_html=True
)

draft_id = draft['id']
print(f"✅ Created draft: {draft_id}")
print(f"📝 Open this draft and edit it:")
print(f"   https://mail.google.com/mail/#drafts?compose={draft_id}")

input("\n⏸️  Edit the draft in Gmail (add bold, colors, etc.), then press Enter...")

# 2. 초안 발송
confirm = input(f"\n⚠️  Send draft to yourself? (yes/no): ")
if confirm == 'yes':
    sent = gmail.send_draft(draft_id)
    print(f"✅ Sent: {sent['id']}")
    print(f"📬 Check sent email in Gmail to verify edits were preserved")
EOF
```

**✅ 확인**:
1. 프로그램 일시정지 시 Gmail에서 초안 수정
2. Enter 누르고 'yes' 입력
3. Sent 폴더에서 수정사항 반영 확인

---

### 시나리오 4: Sheets 통합 테스트

**목표**: Sheets 링크와 Draft ID 저장 확인

```bash
python3 << 'EOF'
from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
from datetime import datetime

gmail = GmailClient()
sheets = SheetsClient()

# 1. 스프레드시트 생성
spreadsheet_id = sheets.create_email_tracker(
    title=f"Test v0.4.0 - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
print(f"✅ Created: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

# 2. 테스트 초안 생성
draft = gmail.create_draft(
    thread_id="test_thread",
    to="test@example.com",
    subject="Test Email",
    body="<p>Test body with <b>bold</b></p>",
    is_html=True
)

draft_id = draft['id']
draft_link = f'=HYPERLINK("https://mail.google.com/mail/#drafts?compose={draft_id}", "열기")'

# 3. Sheets에 추가
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

print(f"\n✅ Added email row with draft link")
print(f"\n📊 Open spreadsheet:")
print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
print(f"\n✅ Verify:")
print(f"   - Column G has clickable '열기' link")
print(f"   - Clicking link opens Gmail draft")
print(f"   - Columns I and J are hidden")
EOF
```

**✅ 확인**:
1. 스프레드시트 열기
2. "Gmail 초안" 컬럼에 "열기" 링크 확인
3. 링크 클릭 시 Gmail 초안 열림
4. 컬럼 I, J 숨겨져 있는지 확인

---

## 🔍 문제 해결

### 문제 1: Draft ID가 출력 안 됨

**증상**:
```
✅ Draft: 회의 일정...
```
(ID 없음)

**원인**: `create_draft()`가 draft 객체를 반환 안 함

**해결**:
```bash
# 코드 확인
grep -A 5 "def create_draft" email_classifier/gmail_client.py

# return draft 구문이 있는지 확인
```

---

### 문제 2: Sheets에 링크가 텍스트로 보임

**증상**: "열기" 대신 `=HYPERLINK(...)` 텍스트가 그대로 보임

**원인**: `valueInputOption="RAW"` 사용

**해결**:
```bash
# sheets_client.py 확인
grep "valueInputOption" email_classifier/sheets_client.py

# USER_ENTERED여야 함 (HYPERLINK 함수 평가)
```

---

### 문제 3: 발송 시 서식이 사라짐

**증상**: Gmail Sent에서 평문으로만 보임

**원인**:
1. HTML 모드가 꺼짐 (`is_html=False`)
2. 또는 `batch_send_emails()`를 사용 (deprecated)

**확인**:
```bash
# main_sheets.py 확인
grep "is_html" email_classifier/main_sheets.py
# → is_html=True 있어야 함

grep "batch_send" email_classifier/main_sheets.py
# → batch_send_drafts 사용해야 함 (batch_send_emails 아님)
```

---

### 문제 4: Draft를 찾을 수 없음 (404)

**증상**:
```
❌ Failed: ... - 404 Not Found
```

**원인**: Draft ID가 잘못되었거나 이미 삭제됨

**해결**:
1. Sheets에서 Draft ID 확인 (컬럼 I 숨김 해제)
2. Gmail Drafts에 해당 초안이 있는지 확인

---

## 📊 테스트 체크리스트

### 필수 테스트

- [ ] HTML 초안 생성 시 Draft ID 출력됨
- [ ] Sheets "Gmail 초안" 컬럼에 "열기" 링크 있음
- [ ] 링크 클릭 시 Gmail 초안 열림
- [ ] Gmail에서 서식 수정 가능
- [ ] 발송 체크박스 작동
- [ ] 일괄 발송 시 수정사항 반영됨 (가장 중요!)
- [ ] 발송 후 상태 "답장완료"로 변경
- [ ] 체크박스 자동 해제

### 선택 테스트

- [ ] 컬럼 I, J가 숨겨져 있음
- [ ] Body preview가 200자로 제한됨
- [ ] 에러 시 graceful하게 처리됨
- [ ] Deprecated 함수 사용 시 경고 출력

---

## 🎓 테스트 팁

1. **소량 테스트**: 처음엔 이메일 2-3개만 처리
2. **본인에게 발송**: 테스트 발송은 본인 이메일로
3. **Gmail Drafts 확인**: 각 단계마다 Drafts 폴더 확인
4. **Sheets 새로고침**: 변경사항이 안 보이면 새로고침
5. **로그 확인**: 에러 발생 시 터미널 출력 확인

---

## ✅ 성공 기준

**v0.4.0이 제대로 작동하는 것**:

1. Gmail에서 초안을 수정했을 때
2. Sheets에서 발송여부 체크했을 때
3. 일괄 발송을 실행했을 때
4. **Sent 폴더의 이메일에 Gmail 수정사항이 100% 반영됨**

이것만 확인되면 v0.4.0 성공입니다! 🎉
