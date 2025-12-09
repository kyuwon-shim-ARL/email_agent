# 📧 이메일 자동 분류

이 명령을 실행하면 Claude Code가 Gmail 이메일을 자동으로:
1. 가져와서 분석하고
2. 3D 우선순위 스코어링 적용
3. Gmail 라벨 자동 적용
4. Google Sheets에 정리

## 실행

아래 Python 코드를 실행하여 이메일 데이터를 가져온 후, 제가 직접 분류하겠습니다.

```python
# 1. 이메일 데이터 수집
import sys
sys.path.insert(0, '/home/kyuwon/projects/email_agent')

from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
import json

gmail = GmailClient()

# 최근 이메일 가져오기
emails = gmail.get_recent_emails(max_results=15)
print(f"📬 {len(emails)}개 이메일 로드")

# 대화 이력 수집
histories = {}
for email in emails:
    sender = email['sender']
    if sender not in histories:
        histories[sender] = gmail.get_conversation_history(sender, max_results=20)

# 데이터 저장
data = {"emails": emails, "histories": histories}
with open('/tmp/email_data.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False)

print("✅ /tmp/email_data.json 저장 완료")
print("\n이메일 목록:")
for i, e in enumerate(emails, 1):
    h = histories.get(e['sender'], {})
    print(f"{i}. [{h.get('total_sent',0)}↑/{h.get('total_received',0)}↓] {e['subject'][:50]}")
    print(f"   From: {e['sender'][:40]}")
```

위 코드 실행 후, 제가 `/tmp/email_data.json`을 읽고 prioritize-email skill로 분류합니다.

그 다음 아래 코드로 결과를 적용합니다:

```python
# 2. 분류 결과 적용 (Claude가 classifications 변수에 결과 저장 후 실행)
# classifications = [...] # Claude가 채움

from datetime import datetime
import sys
sys.path.insert(0, '/home/kyuwon/projects/email_agent')

from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
import json

gmail = GmailClient()
sheets = SheetsClient()

with open('/tmp/email_data.json', 'r') as f:
    data = json.load(f)
emails = data['emails']

# Gmail 라벨 설정
label_ids = gmail.setup_email_labels()
print(f"🏷️ {len(label_ids)}개 라벨 준비")

# 라벨 적용
for email, c in zip(emails, classifications):
    status = '답장필요' if c['requires_response'] else '답장불필요'
    gmail.apply_labels_to_email(email['id'], status, c['priority'], label_ids)
    print(f"✅ {status}|P{c['priority']} - {email['subject'][:35]}...")

# Sheets 생성
sid = sheets.create_email_tracker(f"Email Tracker - {datetime.now().strftime('%Y-%m-%d')}")
print(f"\n📊 https://docs.google.com/spreadsheets/d/{sid}")

# 답장 필요한 이메일 추가
needs = [e for e, c in zip(emails, classifications) if c['requires_response']]
for email in needs:
    c = next(x for x, e in zip(classifications, emails) if e['id'] == email['id'])
    sheets.add_email_row(sid, {
        'status': 'needs_response',
        'priority': c['priority'],
        'subject': email['subject'],
        'sender': email['sender'],
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'body': email.get('body', email['snippet'])[:200],
        'thread_id': email['thread_id'],
    })

# 발신자 관리 업데이트
stats = gmail.collect_all_sender_stats(max_emails=200, classified_emails=[
    {**e, 'priority': c['priority']} for e, c in zip(emails, classifications)
])
for sender_email, s in stats.items():
    sheets.add_or_update_sender(sid, sender_email, s)

print(f"✅ {len(needs)}개 이메일 + {len(stats)}명 발신자 저장 완료!")
```
