# 이메일 자동 분류 및 초안 생성

Gmail 이메일을 자동으로 분류하고 답장 초안을 생성합니다.

## 실행 단계

### 1단계: Gmail 연결 및 이메일 가져오기

```bash
~/.venv/bin/python -c "
from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
import json

gmail = GmailClient()
sheets = SheetsClient()

# 최근 이메일 가져오기
emails = gmail.get_recent_emails(max_results=20)
print('=== EMAILS ===')
for i, email in enumerate(emails, 1):
    print(f'{i}. {email[\"subject\"][:50]}')
    print(f'   From: {email[\"sender\"]}')
    print(f'   ID: {email[\"id\"]}')
    print()

# 발신자별 대화 이력 수집
print('=== CONVERSATION HISTORY ===')
sender_histories = {}
for email in emails:
    sender = email['sender']
    if sender not in sender_histories:
        history = gmail.get_conversation_history(sender, max_results=20)
        sender_histories[sender] = history
        print(f'{sender}: sent={history[\"total_sent\"]}, received={history[\"total_received\"]}')

# JSON으로 저장
with open('/tmp/email_data.json', 'w') as f:
    json.dump({'emails': emails, 'histories': sender_histories}, f, ensure_ascii=False, indent=2)

print()
print('✅ 이메일 데이터 저장: /tmp/email_data.json')
"
```

### 2단계: prioritize-email skill로 분류

`/tmp/email_data.json` 파일을 읽고 각 이메일에 대해 다음을 분석해주세요:

1. **Sender Importance (0-100)**: 관계 깊이 + 직급/역할 + 최근 활동
2. **Content Urgency (0-100)**: 시간 민감도 + 액션 필요도 + 내용 중요도
3. **Context Modifiers (-20~+20)**: 보너스/페널티
4. **Final Priority (1-5)**: 가중 계산 결과
5. **requires_response**: true/false

분석 결과를 `/tmp/email_classifications.json`에 저장해주세요.

### 3단계: Gmail 라벨 적용 및 Sheets 업데이트

```bash
~/.venv/bin/python -c "
from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
from datetime import datetime
import json

gmail = GmailClient()
sheets = SheetsClient()

# 분류 결과 로드
with open('/tmp/email_classifications.json', 'r') as f:
    classifications = json.load(f)

with open('/tmp/email_data.json', 'r') as f:
    data = json.load(f)
    emails = data['emails']

# Gmail 라벨 설정
print('🏷️ Gmail 라벨 설정...')
label_ids = gmail.setup_email_labels()
print(f'   ✅ {len(label_ids)}개 라벨 준비')

# 라벨 적용
print('🏷️ 라벨 적용...')
for email, classification in zip(emails, classifications):
    status = '답장필요' if classification['requires_response'] else '답장불필요'
    priority = classification['priority']
    gmail.apply_labels_to_email(email['id'], status, priority, label_ids)
    print(f'   ✅ {status} | P{priority} - {email[\"subject\"][:40]}...')

# Spreadsheet 생성
print()
print('📊 Spreadsheet 생성...')
spreadsheet_id = sheets.create_email_tracker(f'Email Tracker - {datetime.now().strftime(\"%Y-%m-%d\")}')
print(f'   ✅ https://docs.google.com/spreadsheets/d/{spreadsheet_id}')

# 이메일 추가 (답장 필요한 것만)
for email, classification in zip(emails, classifications):
    if classification['requires_response']:
        email_data = {
            'status': 'needs_response',
            'priority': classification['priority'],
            'subject': email['subject'],
            'sender': email['sender'],
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'body': email.get('body', email['snippet'])[:200],
            'thread_id': email['thread_id'],
        }
        sheets.add_email_row(spreadsheet_id, email_data)

print()
print('✅ 완료!')
print(f'📊 Spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}')
"
```

## 사용법

1. Claude Code에서 `/email-auto` 실행
2. 1단계 코드 실행 → 이메일 목록 확인
3. 2단계: Claude가 직접 분류 수행
4. 3단계 코드 실행 → Gmail 라벨 + Sheets 업데이트

## 결과

- Gmail에 8개 라벨 자동 생성 (답장필요/불필요/완료 + P1~P5)
- 각 이메일에 라벨 자동 적용
- Google Sheets에 답장 필요한 이메일 목록 생성
- 발신자 관리 탭에 발신자별 점수 기록
