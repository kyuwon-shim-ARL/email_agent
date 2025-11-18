# Email Classifier for Claude Code (NO API COSTS!)

**✨ Claude Code에서 실행하는 무료 이메일 분류기**

## 🎯 주요 특징

- ✅ **Claude API 비용 없음** - Claude Code 세션 내에서 처리
- ✅ **Gmail 연동** - 이메일 읽기 + 초안 생성
- ✅ **작성 스타일 학습** - 과거 이메일에서 말투 학습
- ✅ **배치 처리** - 10개 이메일을 한 번에 처리
- ✅ **간단한 워크플로우** - 3단계로 완료

## 📊 비용 비교

| 방식 | 하루 3번 실행 | 한 달 비용 |
|------|-------------|----------|
| **Claude Code 방식** | 무제한 | **$0** |
| Claude API 직접 호출 | 90개 이메일 | $9-27 |

하루에 여러 번, 여러 이메일을 처리해도 **비용 걱정 없음!**

## 🚀 설치 및 설정

### 1. Gmail API 설정 (최초 1회만)

```bash
# Google Cloud Console 설정
1. https://console.cloud.google.com/ 접속
2. 프로젝트 생성
3. Gmail API 활성화
4. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
5. credentials.json 다운로드

# credentials.json 배치
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

### 2. 패키지 설치

```bash
cd /home/kyuwon/projects/email_agent
uv pip install -e .
```

## 📖 사용 방법

### 실행

```bash
email-classify
```

### 워크플로우 (3단계)

#### STEP 1: 작성 스타일 학습

```
✍️  Fetching your sent emails...
   → Found 30 sent emails

✅ Style analysis prompt ready!
   File: /tmp/email_classifier/analyze_style.txt

ACTION REQUIRED:
1. Open file: /tmp/email_classifier/analyze_style.txt
2. Copy the prompt
3. Paste it to Claude Code (in this conversation)
4. Copy Claude's JSON response
5. Paste it below
```

**예시**:
1. `cat /tmp/email_classifier/analyze_style.txt` 실행
2. 출력된 프롬프트를 Claude Code에 복붙
3. Claude의 JSON 응답을 복사
4. 터미널에 붙여넣기

#### STEP 2: 이메일 분류

```
📬 Fetching recent emails...
   → Found 10 emails

✅ Classification prompt ready!
   File: /tmp/email_classifier/classify_batch.txt

ACTION REQUIRED:
1. Open file: /tmp/email_classifier/classify_batch.txt
2. Copy the prompt
3. Paste it to Claude Code
4. Copy Claude's JSON array response
5. Paste it below
```

#### STEP 3: 초안 생성

```
📝 3 emails need responses

✅ Draft generation prompt ready!
   File: /tmp/email_classifier/generate_drafts.txt

ACTION REQUIRED:
1. Open file: /tmp/email_classifier/generate_drafts.txt
2. Copy the prompt
3. Paste it to Claude Code
4. Copy Claude's JSON array response
5. Paste it below
```

### 결과 확인

```
✨ Classification complete!

📝 Check your Gmail Drafts folder to review and send replies!
   → https://mail.google.com/mail/#drafts
```

## 🔄 실제 사용 예시

```bash
$ email-classify

🔍 Email Classifier (Claude Code Edition - FREE!)
   No API costs - runs in your Claude Code session

📧 Connecting to Gmail...
🤖 Initializing Claude Code classifier...

================================================================================
STEP 1: LEARN YOUR WRITING STYLE
================================================================================

✍️  Fetching your sent emails...
   → Found 30 sent emails

✅ Style analysis prompt ready!
   File: /tmp/email_classifier/analyze_style.txt
================================================================================
ACTION REQUIRED:
================================================================================
1. Open file: /tmp/email_classifier/analyze_style.txt
2. Copy the prompt
3. Paste it to Claude Code (in this conversation)
4. Copy Claude's JSON response
5. Paste it below
================================================================================

📋 Paste Claude's style analysis JSON: [여기에 Claude 응답 붙여넣기]

✅ Style learned!
   Greeting: Hi,
   Closing: Best regards,
   Formality: casual

================================================================================
STEP 2: CLASSIFY RECENT EMAILS
================================================================================

📬 Fetching recent emails...
   → Found 10 emails

✅ Classification prompt ready!
   File: /tmp/email_classifier/classify_batch.txt
================================================================================
ACTION REQUIRED:
================================================================================
1. Open file: /tmp/email_classifier/classify_batch.txt
2. Copy the prompt
3. Paste it to Claude Code
4. Copy Claude's JSON array response
5. Paste it below
================================================================================

📋 Paste Claude's classification JSON: [여기에 Claude 응답 붙여넣기]

================================================================================
STEP 3: GENERATE DRAFT REPLIES
================================================================================

📝 3 emails need responses

✅ Draft generation prompt ready!
   File: /tmp/email_classifier/generate_drafts.txt
================================================================================
ACTION REQUIRED:
================================================================================
1. Open file: /tmp/email_classifier/generate_drafts.txt
2. Copy the prompt
3. Paste it to Claude Code
4. Copy Claude's JSON array response
5. Paste it below
================================================================================

📋 Paste Claude's draft JSON: [여기에 Claude 응답 붙여넣기]

   ✅ Draft created for: 회의 일정 확인 부탁드립니다...
   ✅ Draft created for: 프로젝트 진행 상황 공유...
   ✅ Draft created for: 견적서 확인 요청...

📝 Created 3 drafts in Gmail!

================================================================================
RESULTS SUMMARY
================================================================================

🔴 NEEDS RESPONSE (3 emails)
================================================================================

1. 회의 일정 확인 부탁드립니다
   From: manager@company.com
   Confidence: 95%
   Reason: Direct question requiring response

2. 프로젝트 진행 상황 공유
   From: team@company.com
   Confidence: 85%
   Reason: Team update likely needs acknowledgment

3. 견적서 확인 요청
   From: client@example.com
   Confidence: 90%
   Reason: Client request requiring action


✅ NO RESPONSE NEEDED (7 emails)
================================================================================

1. GitHub Notification: PR merged
   From: notifications@github.com
   Confidence: 99%
   Reason: Automated notification

...

================================================================================
✨ Classification complete!

📝 Check your Gmail Drafts folder to review and send replies!
   → https://mail.google.com/mail/#drafts
```

## ⏱️ 소요 시간

- **STEP 1** (스타일 학습): ~30초
  - 파일 열기 → 복사 → Claude에 붙여넣기 → 응답 복사 → 붙여넣기
- **STEP 2** (분류): ~30초
- **STEP 3** (초안 생성): ~30초

**총 소요 시간**: ~2분

## 💡 팁

### 빠르게 파일 열기

```bash
# STEP 1
cat /tmp/email_classifier/analyze_style.txt

# STEP 2
cat /tmp/email_classifier/classify_batch.txt

# STEP 3
cat /tmp/email_classifier/generate_drafts.txt
```

### JSON 응답 복사 시

Claude의 응답에서 JSON 부분만 복사하세요:

**좋은 예**:
```json
{
  "greeting_style": "Hi,",
  "closing_style": "Best,",
  ...
}
```

**나쁜 예**:
```
Here's the analysis:

```json
...
```

Let me know if you need anything else.
```

→ 설명 제외하고 JSON만 복사!

## 🆚 기존 방식과 비교

### 기존 (API 호출)

```python
# anthropic 패키지 필요
# .env 파일에 CLAUDE_API_KEY 필요
# API 호출마다 비용 발생

from anthropic import Anthropic
client = Anthropic(api_key=api_key)
response = client.messages.create(...)  # 💰 비용 발생
```

### 새로운 방식 (Claude Code)

```python
# anthropic 패키지 불필요
# API 키 불필요
# 비용 없음

# 프롬프트 준비
prompt_file = classifier.prepare_classification_batch(emails)

# 사용자가 Claude Code에 붙여넣기
# 응답을 다시 받아서 파싱
```

## 🐛 문제 해결

### "credentials.json not found"

```bash
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

### JSON 파싱 에러

Claude의 응답에서 **JSON 부분만** 복사했는지 확인:
- ✅ `{` 또는 `[`로 시작
- ✅ `}` 또는 `]`로 끝
- ❌ 앞뒤 설명 포함 X

### 초안이 Gmail에 안 보임

1. Gmail 새로고침
2. "모든 초안" 탭 확인
3. 터미널에서 에러 메시지 확인

## 📝 Legacy 버전 (API 사용)

API 비용을 지불하고 자동화하려면:

```bash
# .env 파일에 CLAUDE_API_KEY 설정 필요
email-classify-legacy
```

## 🎉 결론

**하루에 여러 번, 여러 이메일을 처리해도 비용 $0!**

Claude Code 세션 내에서 실행하므로:
- ✅ API 키 불필요
- ✅ 비용 발생 없음
- ✅ 같은 기능
- ✅ 2분이면 완료

---

**Ready to save money?** 지금 바로 실행해보세요:

```bash
email-classify
```
