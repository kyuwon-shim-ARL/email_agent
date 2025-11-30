# v0.5.0 테스트 가이드

## 🎯 테스트 목표

v0.5.0의 핵심 기능들이 제대로 작동하는지 확인:
- **3차원 우선순위 스코어링** (prioritize-email skill)
- **발신자 중요도 관리** (발신자 관리 탭)
- **Gmail 라벨 자동 관리** (8개 라벨)
- Gmail HTML 초안 생성 (v0.4.0)
- Sheets 하이브리드 아키텍처 (v0.4.0)

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
# 출력: 0.5.0
```

### 2. 권한 확인

기존 `token.json`이 있다면 그대로 사용 가능합니다. 필요한 스코프는 이미 포함되어 있습니다:
- `gmail.readonly`
- `gmail.compose`
- `gmail.send`
- `spreadsheets`

---

## 🧪 테스트 시나리오

### 시나리오 0: v0.5.0 신규 기능 테스트 (우선 추천)

**목표**: 3D 우선순위 스코어링, 발신자 관리, Gmail 라벨 확인

#### 0.1 프로그램 실행

```bash
email-classify-sheets
```

#### 0.2 STEP 1-2: 스타일 학습 및 이메일 분석

- 기존과 동일하게 진행
- 최근 이메일 5-10개 정도로 테스트 권장

#### 0.3 STEP 3: 3D 우선순위 스코어링 (핵심!)

```bash
cat /tmp/email_classifier/classify_batch.txt
```

**✅ 확인사항**: 프롬프트에 다음 내용이 포함되는지 확인
- "Use the 'prioritize-email' skill"
- "Sender Importance (0-100)"
- "Content Urgency (0-100)"
- "Context Modifiers (-20 to +20)"
- "CONVERSATION HISTORY" (각 이메일마다)

**Claude Code에 붙여넣기 후 응답 확인**:
```json
[
  {
    "email_index": 1,
    "requires_response": true,
    "confidence": 0.9,
    "sender_importance": {
      "relationship_depth": {"score": 30, "reason": "weighted=25 (보낸 5회, 받은 10회)"},
      "role_position": {"score": 25, "reason": "직속 상사 (이메일 서명 확인)"},
      "recent_activity": {"score": 5, "reason": "이번 주 1회"},
      "total": 60
    },
    "content_urgency": {
      "time_sensitivity": {"score": 40, "reason": "오늘 필요 ('by EOD today')"},
      "action_required": {"score": 35, "reason": "즉시 결정 필요 (승인 요청)"},
      "content_importance": {"score": 25, "reason": "비즈니스 크리티컬 (계약)"},
      "total": 100
    },
    "context_modifiers": {
      "bonuses": ["+10: 내가 마지막 발신"],
      "penalties": [],
      "total": 10
    },
    "calculation": {
      "formula": "(60 × 0.35) + (100 × 0.50) + 10",
      "final_score": 81,
      "normalized_score": 81
    },
    "priority": 4,
    "priority_label": "긴급",
    "summary": "상사의 긴급 승인 요청",
    "reason": "..."
  }
]
```

**✅ 성공 기준**:
- 모든 이메일에 `sender_importance`, `content_urgency`, `context_modifiers` 포함
- `calculation` 필드에 점수 계산 과정 표시
- `priority_label`이 한글로 표시 (최저/낮음/보통/긴급/최우선)

#### 0.4 Gmail 라벨 확인 (핵심!)

프로그램 진행하면 자동으로:
```
🏷️  Setting up Gmail labels...
   ✅ Created/verified 8 labels

🏷️  Applying labels to emails...
   ✅ 답장필요 | P4 - 회의 일정 조율 건...
   ✅ 답장필요 | P5 - 긴급: 계약서 검토 요청...
   ✅ 답장불필요 | P2 - 주간 뉴스레터...
```

**Gmail 확인**:
1. Gmail 웹 열기
2. 왼쪽 사이드바에서 라벨 확인:
   - 답장필요 (빨강)
   - 답장불필요 (회색)
   - 답장완료 (녹색)
   - P1-최저 (연한 회색)
   - P2-낮음 (연한 파랑)
   - P3-보통 (노랑)
   - P4-긴급 (주황-빨강)
   - P5-최우선 (진한 빨강)

3. 이메일 클릭해서 라벨 확인:
   - 각 이메일에 상태 라벨 1개 + 우선순위 라벨 1개 (총 2개)

**✅ 성공 기준**:
- 8개 라벨 모두 생성됨
- 각 이메일에 2개 라벨 적용됨
- 라벨 색상이 설정대로 표시됨

#### 0.5 발신자 관리 탭 확인 (핵심!)

**프로그램 계속 진행**:
```
STEP 5.5: UPDATE SENDER MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Collecting sender statistics...
   → Found 25 senders

📝 Updating 발신자 관리 tab...
   ✅ Updated 25 senders in 발신자 관리 tab
   💡 Review and manually grade senders (VIP/중요/보통/낮음/차단)
```

**Spreadsheet 열기**:
```
터미널에 출력된 링크 클릭:
📊 Spreadsheet: https://docs.google.com/spreadsheets/d/...
```

**"발신자 관리" 탭 클릭**

**✅ 확인사항**:

1. **컬럼 구조** (12개):
   ```
   A: 발신자 (이메일)
   B: 이름
   C: 자동점수 (0-100)
   D: 수동등급 (드롭다운)
   E: 확정점수 (0-100, 색상 그라데이션)
   F: 총 교신
   G: 보낸 횟수
   H: 받은 횟수
   I: P4-5 비율 (%)
   J: 최근7일
   K: 마지막 교신일
   L: 메모
   ```

2. **자동점수 계산**:
   - 자주 교신한 발신자 → 높은 점수
   - P4-5 비율이 높은 발신자 → 높은 점수
   - 최근 활동이 많은 발신자 → 높은 점수

3. **수동등급 드롭다운** (D 컬럼):
   - 셀 클릭 시 드롭다운 표시
   - 선택지: VIP, 중요, 보통, 낮음, 차단
   - 선택하면 확정점수(E)가 자동 변경
     - VIP → 100
     - 중요 → 80
     - 보통 → 50
     - 낮음 → 20
     - 차단 → 0

4. **확정점수 색상**:
   - 0-50: 회색 ~ 노랑
   - 50-100: 노랑 ~ 녹색

**✅ 성공 기준**:
- 발신자 관리 탭이 자동 생성됨
- 모든 발신자가 자동으로 추가됨
- 자동점수가 합리적으로 계산됨
- 드롭다운이 정상 작동함
- 수동등급 선택 시 확정점수가 변경됨

#### 0.6 수동 등급 설정 테스트

1. **VIP 설정**:
   - 중요한 발신자 1명 선택
   - D 컬럼 드롭다운에서 "VIP" 선택
   - E 컬럼 확정점수가 100으로 변경되는지 확인

2. **차단 설정**:
   - 스팸 발신자 1명 선택
   - "차단" 선택
   - 확정점수가 0으로 변경되는지 확인

**✅ 성공 기준**:
- 수동 선택이 확정점수에 즉시 반영됨
- 기존 자동점수는 유지됨 (C 컬럼)

---

### 시나리오 1: 전체 워크플로우 테스트 (v0.4.0 + v0.5.0)

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

### v0.5.0 필수 테스트

**3D 우선순위 스코어링**:
- [ ] prioritize-email skill 프롬프트 생성됨
- [ ] Claude 응답에 sender_importance, content_urgency, context_modifiers 포함
- [ ] calculation 필드에 점수 계산 과정 표시
- [ ] priority_label이 한글로 표시됨 (최저/낮음/보통/긴급/최우선)

**Gmail 라벨 관리**:
- [ ] 8개 라벨 자동 생성됨 (상태 3개 + 우선순위 5개)
- [ ] 라벨 색상이 올바르게 설정됨
- [ ] 각 이메일에 상태 + 우선순위 라벨 자동 적용
- [ ] 발송 후 라벨이 "답장완료"로 자동 변경됨

**발신자 관리**:
- [ ] "발신자 관리" 탭 자동 생성됨
- [ ] 12개 컬럼 구조가 올바름
- [ ] 모든 발신자 자동 추가됨
- [ ] 자동점수가 합리적으로 계산됨
- [ ] 수동등급 드롭다운 작동함 (VIP/중요/보통/낮음/차단)
- [ ] 수동등급 선택 시 확정점수 자동 변경
- [ ] 확정점수 색상 그라데이션 적용됨

### v0.4.0 필수 테스트

- [ ] HTML 초안 생성 시 Draft ID 출력됨
- [ ] Sheets "Gmail 초안" 컬럼에 "열기" 링크 있음
- [ ] 링크 클릭 시 Gmail 초안 열림
- [ ] Gmail에서 서식 수정 가능
- [ ] 발송 체크박스 작동
- [ ] 일괄 발송 시 수정사항 반영됨
- [ ] 발송 후 상태 "답장완료"로 변경
- [ ] 체크박스 자동 해제

### 선택 테스트

- [ ] 컬럼 I, J가 숨겨져 있음 (Emails 탭)
- [ ] Body preview가 200자로 제한됨
- [ ] 에러 시 graceful하게 처리됨
- [ ] Deprecated 함수 사용 시 경고 출력
- [ ] 발신자 관리 탭 재실행 시 기존 데이터 유지
- [ ] 수동등급 재실행 시 덮어쓰지 않음

---

## 🎓 테스트 팁

1. **소량 테스트**: 처음엔 이메일 2-3개만 처리
2. **본인에게 발송**: 테스트 발송은 본인 이메일로
3. **Gmail Drafts 확인**: 각 단계마다 Drafts 폴더 확인
4. **Sheets 새로고침**: 변경사항이 안 보이면 새로고침
5. **로그 확인**: 에러 발생 시 터미널 출력 확인

---

## ✅ 성공 기준

### v0.5.0이 제대로 작동하는 것:

**1. 3D 우선순위 스코어링**
- [ ] Claude가 prioritize-email skill을 사용함
- [ ] 모든 이메일에 3차원 점수 (Sender + Content + Context) 표시
- [ ] 점수 계산 과정이 투명하게 공개됨
- [ ] 우선순위가 직관적으로 합리적임

**2. Gmail 라벨 관리**
- [ ] 8개 라벨이 자동 생성됨 (색상 포함)
- [ ] 이메일 분류 시 라벨이 자동 적용됨
- [ ] Gmail에서 라벨로 필터링 가능 (예: `label:P5-최우선`)
- [ ] 발송 시 라벨이 "답장완료"로 자동 변경됨

**3. 발신자 관리**
- [ ] 발신자 관리 탭이 자동 생성됨
- [ ] 자동점수가 교신 패턴을 잘 반영함
- [ ] 수동등급 드롭다운이 작동함
- [ ] 수동등급이 확정점수에 즉시 반영됨
- [ ] 재실행 시 수동등급이 보존됨

### v0.4.0이 제대로 작동하는 것:

1. Gmail에서 초안을 수정했을 때
2. Sheets에서 발송여부 체크했을 때
3. 일괄 발송을 실행했을 때
4. **Sent 폴더의 이메일에 Gmail 수정사항이 100% 반영됨**

---

모든 기능이 확인되면 v0.5.0 성공입니다! 🎉
