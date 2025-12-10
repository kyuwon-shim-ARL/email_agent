# Gmail 초안 생성 (추가 분)

스프레드시트에서 수정 후 Draft ID가 없는 항목들의 Gmail 초안을 생성합니다.

## 사용 시점

- `/email-analyze` 실행 후 스프레드시트에서 초안 내용을 추가/수정한 경우
- 상태를 "답장불필요" → "답장필요"로 변경하고 초안 작성한 경우

## 실행 단계

### 1단계: Gmail 초안 생성

```bash
python << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
import json
import re

gmail = GmailClient()
sheets = SheetsClient()

# Config에서 스프레드시트 ID 자동 로드
try:
    with open('email_history_config.json', 'r') as f:
        config = json.load(f)
    SPREADSHEET_ID = config.get('history_spreadsheet_id')
    if not SPREADSHEET_ID:
        print("❌ email_history_config.json에 spreadsheet_id가 없습니다.")
        print("먼저 /email-analyze를 실행해주세요.")
        sys.exit(1)
except FileNotFoundError:
    print("❌ email_history_config.json 파일이 없습니다.")
    print("먼저 /email-analyze를 실행해주세요.")
    sys.exit(1)

print(f"📊 스프레드시트: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

# 두 탭에서 초안 필요 항목 찾기
tabs_to_check = ["신규 메일", "처리 이력"]
drafts_created = 0
draft_errors = []

for tab_name in tabs_to_check:
    try:
        result = sheets.service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{tab_name}!A:P",
        ).execute()
        rows = result.get("values", [])

        if len(rows) < 2:
            print(f"📋 [{tab_name}] 데이터 없음")
            continue

        print(f"\n📋 [{tab_name}] {len(rows)-1}개 행 검색 중...")

        for row_idx, row in enumerate(rows[1:], start=2):
            # 행 길이 맞추기 (16열)
            while len(row) < 16:
                row.append("")

            status = row[0]           # A: 상태
            subject = row[3]          # D: 제목
            sender = row[4]           # E: 발신자
            draft_subject = row[9]    # J: 초안(제목)
            draft_body = row[10]      # K: 초안(내용)
            send_cc = row[11]         # L: 보낼CC
            existing_draft = row[14]  # O: Draft ID
            thread_id = row[15]       # P: Thread ID

            # 조건 체크: 상태="답장필요" + 초안내용 있음 + Draft ID 없음
            if status != "답장필요":
                continue
            if not draft_body.strip():
                continue
            if existing_draft.strip():
                continue  # 이미 초안 있음

            # 발신자 이메일 추출
            email_match = re.search(r'<([^>]+)>', sender)
            to_email = email_match.group(1) if email_match else sender

            # CC 처리
            cc_list = [cc.strip() for cc in send_cc.split(',') if cc.strip()] if send_cc else None

            # Gmail 초안 생성
            try:
                draft = gmail.create_draft(
                    to=to_email,
                    subject=draft_subject or f"Re: {subject}",
                    body=draft_body,
                    thread_id=thread_id if thread_id else None,
                    cc=cc_list,
                )
                draft_id = draft.get('id', '')

                # 해당 탭에 Draft ID 업데이트 (O열)
                sheets.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{tab_name}!O{row_idx}",
                    valueInputOption="RAW",
                    body={"values": [[draft_id]]},
                ).execute()

                # 처리 이력 탭에서도 동일 Thread ID 찾아서 업데이트 (신규 메일에서 작업한 경우)
                if tab_name == "신규 메일" and thread_id:
                    history_row = sheets._find_history_row(SPREADSHEET_ID, thread_id)
                    if history_row:
                        sheets.service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f"처리 이력!O{history_row['row_number']}",
                            valueInputOption="RAW",
                            body={"values": [[draft_id]]},
                        ).execute()

                drafts_created += 1
                print(f"✅ [{tab_name}] 행 {row_idx}: {draft_subject[:35]}... → Draft ID: {draft_id[:10]}...")

            except Exception as e:
                draft_errors.append(f"[{tab_name}] 행 {row_idx}: {str(e)}")
                print(f"❌ [{tab_name}] 행 {row_idx} 오류: {e}")

    except Exception as e:
        print(f"⚠️ [{tab_name}] 탭 읽기 오류: {e}")

# 결과 출력
print(f"\n{'='*50}")
if drafts_created > 0:
    print(f"✅ Gmail 초안 {drafts_created}개 생성 완료!")
    print(f"📬 Gmail 임시보관함에서 확인하세요.")
else:
    print(f"ℹ️ 생성할 초안이 없습니다.")
    print(f"   (상태='답장필요' + 초안내용 있음 + Draft ID 없음)")

if draft_errors:
    print(f"\n⚠️ 오류 발생: {len(draft_errors)}건")
    for err in draft_errors:
        print(f"   - {err}")

print(f"\n다음 단계:")
print(f"1. Gmail 임시보관함에서 초안 확인/수정")
print(f"2. Sheets에서 '전송예정' 체크박스 선택")
print(f"3. /email-send 실행하여 일괄 발송")
EOF
```

## 조건 설명

다음 조건을 **모두** 만족하는 행에 대해서만 초안 생성:

| 조건 | 컬럼 | 값 |
|------|------|-----|
| 상태 | A열 | "답장필요" |
| 초안(내용) | K열 | 비어있지 않음 |
| Draft ID | O열 | **비어있음** |

이미 Draft ID가 있는 항목은 스킵됩니다 (중복 생성 방지).

## 다음 단계

1. Gmail **임시보관함**에서 초안 확인/수정
2. Sheets에서 **전송예정** 체크박스 선택
3. `/email-send` 실행하여 일괄 발송
