# Gmail 초안 일괄 발송

Sheets에서 "전송예정" 체크된 초안들을 일괄 발송합니다.

## 실행 조건

- `/email-draft` 실행 완료 후
- Gmail 초안 최종 확인 완료
- Sheets에서 "전송예정" 체크 완료

## 실행 단계

### 1단계: 스프레드시트 ID 확인

사용자에게 스프레드시트 ID 또는 URL을 요청합니다.

### 2단계: 일괄 발송

```bash
~/.venv/bin/python << 'EOF'
import sys
sys.path.insert(0, '/home/kyuwon/projects/email_agent')

from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient

gmail = GmailClient()
sheets = SheetsClient()

# 스프레드시트 ID (사용자 입력값으로 교체)
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

# Sheets에서 데이터 읽기
result = sheets.service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Emails!A:O",
).execute()
rows = result.get("values", [])

if len(rows) < 2:
    print("❌ 데이터가 없습니다.")
    sys.exit(1)

print(f"📊 총 {len(rows)-1}개 행 로드\n")

# 발송 대상 수집
to_send = []
for row_idx, row in enumerate(rows[1:], start=2):
    while len(row) < 15:
        row.append("")

    subject = row[3]          # D: 제목
    draft_subject = row[9]    # J: 초안(제목)
    send_scheduled = row[12]  # M: 전송예정
    draft_id = row[13]        # N: Draft ID

    # 전송예정 체크 + Draft ID 있는 항목만
    if send_scheduled.upper() == "TRUE" and draft_id:
        to_send.append({
            "row_idx": row_idx,
            "draft_id": draft_id,
            "subject": draft_subject or subject,
        })

print(f"📬 발송 대상: {len(to_send)}개\n")

if not to_send:
    print("ℹ️ 발송할 항목이 없습니다.")
    print("   - Sheets에서 '전송예정' 체크박스를 선택했는지 확인하세요.")
    print("   - Draft ID가 있는지 확인하세요 (/email-draft 실행 필요).")
    sys.exit(0)

# 발송 전 확인
print("발송 예정 목록:")
for i, item in enumerate(to_send, 1):
    print(f"  {i}. {item['subject'][:50]}...")

print(f"\n⚠️ 위 {len(to_send)}개 메일을 발송합니다.")
print("계속하려면 Enter, 취소하려면 Ctrl+C")
input()

# 일괄 발송
sent_count = 0
failed_count = 0

for item in to_send:
    try:
        # Gmail 초안 발송
        gmail.service.users().drafts().send(
            userId='me',
            body={'id': item['draft_id']}
        ).execute()

        # Sheets 상태 업데이트
        sheets.service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Emails!A{item['row_idx']}",
            valueInputOption="RAW",
            body={"values": [["답장완료"]]},
        ).execute()

        # Draft ID 클리어 (발송 완료)
        sheets.service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Emails!N{item['row_idx']}",
            valueInputOption="RAW",
            body={"values": [[""]]},
        ).execute()

        sent_count += 1
        print(f"✅ 발송 완료: {item['subject'][:40]}...")

    except Exception as e:
        failed_count += 1
        print(f"❌ 발송 실패: {item['subject'][:40]}... - {e}")

print(f"\n📤 발송 완료!")
print(f"   성공: {sent_count}개")
if failed_count:
    print(f"   실패: {failed_count}개")
EOF
```

## 주의사항

- **발송 취소 불가**: Gmail API로 발송된 메일은 취소할 수 없습니다.
- 발송 전 확인 프롬프트가 표시됩니다.
- 발송 완료 후 상태가 "답장완료"로 자동 변경됩니다.
- Draft ID는 발송 후 클리어됩니다.

## 안전 기능

1. 발송 전 목록 표시
2. Enter 확인 필요
3. 실패 시 상세 오류 표시
