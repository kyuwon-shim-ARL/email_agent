# 이메일 분석 및 Sheets 작성

Gmail 이메일을 분석하고 Google Sheets에 기록합니다. 초안 내용이 있으면 Gmail 초안을 자동 생성합니다.

## 실행 단계

### 1단계: 이메일 데이터 수집

```bash
python << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from email_classifier.gmail_client import GmailClient
import json

gmail = GmailClient()

# 최근 이메일 가져오기 (15-20개 권장, 처리완료 제외)
emails = gmail.get_recent_emails(max_results=15, skip_processed=True)
print(f"📬 {len(emails)}개 이메일 로드 (처리완료 제외)\n")

if len(emails) == 0:
    print("✅ 처리할 새 이메일이 없습니다!")
    # 새 이메일 없음 보고서 발송
    from datetime import datetime
    from email_classifier.sheets_client import SheetsClient
    label_ids = gmail.setup_email_labels()
    sheets = SheetsClient()
    history_url = sheets.get_history_spreadsheet_url()
    if not history_url:
        history_url = "#"  # 아직 이력 없음
    no_email_report = f"""
<html>
<head><style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
.info-box {{ background-color: #e8f0fe; padding: 20px; border-radius: 8px; text-align: center; }}
</style></head>
<body>
<h2>📬 이메일 분석 보고서</h2>
<p>분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<div class="info-box">
<h3>✅ 처리할 새 이메일이 없습니다</h3>
<p>모든 이메일이 이미 분석 완료되었습니다.</p>
<p style="margin-top: 20px;">
<a href="{history_url}" style="background-color: #34a853; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📚 전체 이력 보기</a>
</p>
</div>
</body>
</html>
"""
    gmail.send_summary_report(
        subject=f"📬 이메일 분석 보고서 - {datetime.now().strftime('%Y-%m-%d %H:%M')} (새 이메일 없음)",
        body=no_email_report,
        label_ids=label_ids
    )
    print("📧 '새 이메일 없음' 보고서 발송 완료")
    sys.exit(0)

# 대화 이력 수집
histories = {}
for email in emails:
    sender = email['sender']
    if sender not in histories:
        histories[sender] = gmail.get_conversation_history(sender, max_results=20)

# 데이터 저장
data = {"emails": emails, "histories": histories}
with open('/tmp/email_data.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 답장 여부 체크 및 이메일 목록 출력
recipient_type_icons = {"direct": "📩 직접수신", "cc": "📋 참조(CC)", "group": "👥 그룹메일"}
for i, email in enumerate(emails, 1):
    h = histories.get(email['sender'], {})
    body = email.get('body', '') or email.get('snippet', '')

    # 답장 여부 체크
    replied = gmail.check_if_replied(email['thread_id'])
    email['replied'] = replied

    # 수신 유형
    recv_type = email.get('recipient_type', 'direct')
    recv_icon = recipient_type_icons.get(recv_type, "📩 직접수신")
    priority_mod = email.get('priority_modifier', 0)
    mod_str = f" (우선순위 {priority_mod:+d})" if priority_mod != 0 else ""

    print(f"=== 이메일 {i} ===")
    print(f"제목: {email['subject']}")
    print(f"발신자: {email['sender']}")
    print(f"수신유형: {recv_icon}{mod_str}")
    print(f"교신이력: 보낸 {h.get('total_sent', 0)}회 / 받은 {h.get('total_received', 0)}회")
    print(f"답장여부: {'✅ 답장함' if replied else '❌ 미답장'}")
    print(f"내용: {body[:300]}")
    print()

# 데이터 저장 (답장 여부 포함)
data = {"emails": emails, "histories": histories}
with open('/tmp/email_data.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ /tmp/email_data.json 저장 완료")
EOF
```

### 2단계: Claude가 분석 수행

위 출력을 보고 각 이메일에 대해 다음을 분석:

1. **우선순위 (1-5)**: 맥락 기반 종합 판단 (아래 5가지 축 참고)
2. **답장 필요 여부**: true/false (이미 답장한 경우도 고려)
3. **AI 요약**: MECE 원칙으로 3줄 이내 요약
4. **마감일**: 이메일에서 언급된 마감일/일정 (없으면 null)
5. **액션 아이템**: 나에게 요구되는 행동/결과물 (마감일 없어도 추출)
6. **초안 (답장 필요시)**: 기존 어투 유지, 간결하게

**우선순위 판단 (5가지 축)**:
- **발신자 관계**: 어투/서명에서 상하관계 추론 (하드코딩 없음)
- **요청 강도**: 즉시 결정 > 명시적 요청 > 소프트 요청 > FYI
- **긴급 신호**: 오늘/ASAP > 이번 주 > 마감일 있음 > 여유
- **메일 유형**: 개인 1:1 > 팀 메일 > 전체 공지 > 자동발송
- **수신 방식**: To(직접) > CC(-1) > 그룹메일(-1)

**판단 힌트**:
- P5는 5-10%만 (정말 긴급한 것만)
- 애매하면 P3 (기본값)
- 첫 연락은 P3 이상

**액션 아이템 추출 기준**:
- "~해주세요", "확인 부탁", "제출 요청", "참석 요청" 등
- 명시적 마감일 없어도 행동이 요구되면 추출
- 예: "설문조사 참여", "문서 보완", "회의 참석", "검토 요청"

분석 결과를 `/tmp/email_classifications.json`에 저장:

```json
[
  {
    "priority": 4,
    "requires_response": true,
    "summary": "• 핵심 내용\n• 요청사항\n• 마감일",
    "deadline": "2024-12-19",
    "deadline_description": "혁신 아이디어 공모전 마감",
    "action_item": "아이디어 제안서 제출",
    "draft_subject": "Re: 제목",
    "draft_body": "답장 내용..."
  }
]
```

**중요**: `action_item`은 마감일 유무와 관계없이 나에게 요구되는 액션이 있으면 반드시 기재

### 3단계: Sheets 생성, 라벨 적용, 보고서 발송

```bash
python << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from email_classifier.gmail_client import GmailClient
from email_classifier.sheets_client import SheetsClient
from datetime import datetime
import json

gmail = GmailClient()
sheets = SheetsClient()

# 데이터 로드
with open('/tmp/email_data.json', 'r') as f:
    data = json.load(f)
emails = data['emails']

with open('/tmp/email_classifications.json', 'r') as f:
    classifications = json.load(f)

# 라벨 설정
label_ids = gmail.setup_email_labels()
print(f"🏷️ {len(label_ids)}개 라벨 준비")

# 히스토리 스프레드시트 (신규 메일 + 처리 이력)
spreadsheet_id = sheets.get_or_create_history_sheet()
print(f"📊 https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

# 신규 메일 탭 초기화 (매 분석 시)
sheets.clear_new_emails_tab(spreadsheet_id)
print("🔄 신규 메일 탭 초기화")

# 이메일 처리
history_stats = {'added': 0, 'updated': 0, 'unchanged': 0}
for i, (email, cls) in enumerate(zip(emails, classifications), 1):
    # 라벨 적용
    status = '답장필요' if cls['requires_response'] else '답장불필요'
    gmail.apply_labels_to_email(email['id'], status, cls['priority'], label_ids)

    # 두 탭에 추가 (신규 메일 + 처리 이력)
    result = sheets.add_email_to_both_tabs(
        email_data=email,
        classification=cls,
        replied=email.get('replied', False)
    )
    history_stats[result] = history_stats.get(result, 0) + 1

    icon = "📝" if cls['requires_response'] else "📌"
    print(f"{icon} {i}. P{cls['priority']} - {email['subject'][:40]}...")

# 처리완료 라벨 적용
message_ids = [e['id'] for e in emails]
gmail.mark_as_processed(message_ids, label_ids)
print(f"\n🏷️ {len(message_ids)}개 이메일에 '처리완료' 라벨 적용")

print(f"📚 이력: 신규 {history_stats['added']}개, 업데이트 {history_stats['updated']}개, 변경없음 {history_stats['unchanged']}개")

# ===== Gmail 초안 자동 생성 (v0.6.2) =====
import re
drafts_created = 0
draft_errors = []

for i, (email, cls) in enumerate(zip(emails, classifications), 1):
    # 답장 필요 + 초안 내용 있는 경우만 초안 생성
    if cls['requires_response'] and cls.get('draft_body', '').strip():
        try:
            # 발신자 이메일 추출
            sender = email.get('sender', '')
            email_match = re.search(r'<([^>]+)>', sender)
            to_email = email_match.group(1) if email_match else sender

            # Gmail 초안 생성
            draft = gmail.create_draft(
                to=to_email,
                subject=cls.get('draft_subject') or f"Re: {email.get('subject', '')}",
                body=cls['draft_body'],
                thread_id=email.get('thread_id'),
                cc=None,
            )
            draft_id = draft.get('id', '')

            # 신규 메일 탭에 Draft ID 업데이트 (O열 = 15번째 열)
            # 행 번호: 헤더 포함하므로 i+1
            sheets.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"신규 메일!O{i+1}",
                valueInputOption="RAW",
                body={"values": [[draft_id]]},
            ).execute()

            # 처리 이력 탭에도 Draft ID 업데이트 (Thread ID로 행 찾기)
            history_row = sheets._find_history_row(spreadsheet_id, email.get('thread_id', ''))
            if history_row:
                sheets.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"처리 이력!O{history_row['row_number']}",
                    valueInputOption="RAW",
                    body={"values": [[draft_id]]},
                ).execute()

            drafts_created += 1
            print(f"📝 초안 생성: {email['subject'][:30]}... → Draft ID: {draft_id[:10]}...")

        except Exception as e:
            draft_errors.append(f"{email['subject'][:30]}: {str(e)}")
            print(f"⚠️ 초안 생성 실패: {email['subject'][:30]}... - {e}")

if drafts_created > 0:
    print(f"\n✅ Gmail 초안 {drafts_created}개 생성 완료 (임시보관함에서 확인)")
if draft_errors:
    print(f"⚠️ 초안 생성 실패: {len(draft_errors)}개")

# 탭 ID 가져오기 (보고서 링크용)
tab_ids = sheets.get_tab_ids(spreadsheet_id)
new_emails_gid = tab_ids.get('신규 메일', 0)
history_gid = tab_ids.get('처리 이력', 0)

# ===== 요약 보고서 생성 =====
needs_response = sum(1 for c in classifications if c['requires_response'])
no_response = len(classifications) - needs_response
priority_counts = {}
for c in classifications:
    p = c['priority']
    priority_counts[p] = priority_counts.get(p, 0) + 1

# 답장 필요 + 미답장 목록 (중요!)
needs_reply_not_replied = []
for email, cls in zip(emails, classifications):
    if cls['requires_response'] and not email.get('replied', False):
        needs_reply_not_replied.append({
            'subject': email['subject'],
            'sender': email['sender'],
            'priority': cls['priority'],
            'summary': cls.get('summary', ''),
            'action_item': cls.get('action_item', ''),
        })

# 액션 아이템 수집 (마감일 유무 관계없이)
action_items = []
for email, cls in zip(emails, classifications):
    if cls.get('action_item'):
        action_items.append({
            'action': cls['action_item'],
            'deadline': cls.get('deadline'),
            'deadline_description': cls.get('deadline_description', ''),
            'subject': email['subject'][:40],
            'sender': email['sender'].split('<')[0].strip(),
            'priority': cls['priority'],
            'replied': email.get('replied', False),
        })

# 액션 아이템 정렬: 우선순위 높은순, 마감일 있는 것 먼저
action_items.sort(key=lambda x: (-x['priority'], x['deadline'] or '9999-99-99'))

# 마감일 일정표 수집 (기존 호환)
deadlines = []
for email, cls in zip(emails, classifications):
    if cls.get('deadline'):
        deadlines.append({
            'date': cls['deadline'],
            'description': cls.get('deadline_description', ''),
            'subject': email['subject'][:40],
            'priority': cls['priority'],
        })

# 마감일 순으로 정렬
deadlines.sort(key=lambda x: x['date'])

# HTML 보고서 생성
report_body = f"""
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
h2 {{ color: #333; border-bottom: 2px solid #4285f4; padding-bottom: 10px; }}
h3 {{ color: #1a73e8; margin-top: 25px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
th {{ background-color: #4285f4; color: white; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
.needs-response {{ color: #d93025; font-weight: bold; }}
.p5 {{ background-color: #fce8e6; }}
.p4 {{ background-color: #fef7e0; }}
.summary {{ background-color: #e8f0fe; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.deadline-urgent {{ background-color: #fce8e6; }}
.deadline-soon {{ background-color: #fef7e0; }}
.not-replied {{ background-color: #fce8e6; }}
.replied {{ background-color: #e6f4ea; color: #666; }}
.action-urgent {{ background-color: #fce8e6; font-weight: bold; }}
.warning-box {{ background-color: #fce8e6; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #d93025; }}
</style>
</head>
<body>
<h2>📬 이메일 분석 보고서</h2>
<p>분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="summary">
<h3>📊 요약</h3>
<ul>
<li>총 이메일: <strong>{len(classifications)}개</strong></li>
<li>답장 필요: <strong class="needs-response">{needs_response}개</strong></li>
<li>답장 불필요: {no_response}개</li>
</ul>
<p><strong>우선순위별:</strong>
P5(최우선): {priority_counts.get(5, 0)}개 |
P4(긴급): {priority_counts.get(4, 0)}개 |
P3(보통): {priority_counts.get(3, 0)}개 |
P2(낮음): {priority_counts.get(2, 0)}개 |
P1(최저): {priority_counts.get(1, 0)}개
</p>
</div>
"""

# ⚠️ 미답장 경고 섹션 (답장 필요 + 미답장)
if needs_reply_not_replied:
    report_body += f"""
<div class="warning-box">
<h3>⚠️ 답장 필요 (미답장) - {len(needs_reply_not_replied)}건</h3>
<table>
<tr><th>우선순위</th><th>제목</th><th>발신자</th><th>요구 액션</th></tr>
"""
    for item in sorted(needs_reply_not_replied, key=lambda x: -x['priority']):
        p_class = 'p5' if item['priority'] == 5 else ('p4' if item['priority'] == 4 else '')
        action = item.get('action_item', '-') or '-'
        report_body += f"""
<tr class="{p_class}">
<td><strong>P{item['priority']}</strong></td>
<td>{item['subject'][:45]}...</td>
<td>{item['sender'].split('<')[0].strip()}</td>
<td>{action}</td>
</tr>
"""
    report_body += "</table></div>"

# 📋 액션 아이템 섹션 (마감일 유무 관계없이)
if action_items:
    report_body += f"""
<h3>📋 액션 아이템 (우선순위순) - {len(action_items)}건</h3>
<table>
<tr><th>우선순위</th><th>액션</th><th>마감일</th><th>관련 메일</th><th>상태</th></tr>
"""
    today = datetime.now().strftime('%Y-%m-%d')
    for item in action_items:
        # 마감일 긴급도
        if item['deadline']:
            if item['deadline'] <= today:
                deadline_str = f"<strong style='color:#d93025'>{item['deadline']} ⚠️</strong>"
            else:
                deadline_str = item['deadline']
        else:
            deadline_str = "-"

        # 답장 상태
        if item['replied']:
            status = "✅ 답장함"
            row_class = "replied"
        else:
            status = "❌ 미답장"
            row_class = "not-replied" if item['priority'] >= 4 else ""

        p_class = 'p5' if item['priority'] == 5 else ('p4' if item['priority'] == 4 else '')
        final_class = f"{p_class} {row_class}".strip()

        report_body += f"""
<tr class="{final_class}">
<td><strong>P{item['priority']}</strong></td>
<td>{item['action']}</td>
<td>{deadline_str}</td>
<td>{item['subject']}... ({item['sender']})</td>
<td>{status}</td>
</tr>
"""
    report_body += "</table>"

# 마감일 일정표 섹션
if deadlines:
    report_body += """
<h3>📅 주요 일정 (마감일 순)</h3>
<table>
<tr><th>마감일</th><th>일정</th><th>관련 이메일</th><th>우선순위</th></tr>
"""
    today = datetime.now().strftime('%Y-%m-%d')
    for dl in deadlines:
        # 긴급도 표시
        if dl['date'] <= today:
            row_class = 'deadline-urgent'
            status = '⚠️ 마감!'
        elif dl['date'] <= (datetime.now().strftime('%Y-%m-%d')[:8] + str(int(datetime.now().strftime('%d')) + 7).zfill(2)):
            row_class = 'deadline-soon'
            status = '⏰ 임박'
        else:
            row_class = ''
            status = ''

        report_body += f"""
<tr class="{row_class}">
<td><strong>{dl['date']}</strong> {status}</td>
<td>{dl['description']}</td>
<td>{dl['subject']}...</td>
<td>P{dl['priority']}</td>
</tr>
"""
    report_body += "</table>"
else:
    report_body += "<p><em>📅 마감일이 있는 일정 없음</em></p>"

# 답장 필요 목록
report_body += """
<h3>📝 답장 필요 목록</h3>
<table>
<tr><th>우선순위</th><th>제목</th><th>발신자</th><th>AI 요약</th></tr>
"""

for email, cls in zip(emails, classifications):
    if cls['requires_response']:
        p_class = 'p5' if cls['priority'] == 5 else ('p4' if cls['priority'] == 4 else '')
        summary_html = cls['summary'].replace('\n', '<br>')
        report_body += f"""
<tr class="{p_class}">
<td><strong>P{cls['priority']}</strong></td>
<td>{email['subject'][:50]}...</td>
<td>{email['sender'].split('<')[0].strip()}</td>
<td>{summary_html}</td>
</tr>
"""

report_body += """
</table>

<h3>📌 참조용 (답장 불필요)</h3>
<table>
<tr><th>우선순위</th><th>제목</th><th>발신자</th><th>AI 요약</th></tr>
"""

for email, cls in zip(emails, classifications):
    if not cls['requires_response']:
        summary_html = cls['summary'].replace('\n', '<br>')
        report_body += f"""
<tr>
<td>P{cls['priority']}</td>
<td>{email['subject'][:50]}...</td>
<td>{email['sender'].split('<')[0].strip()}</td>
<td>{summary_html}</td>
</tr>
"""

report_body += f"""
</table>

<p style="margin-top: 30px;">
<a href="https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={new_emails_gid}" style="background-color: #1a73e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📊 오늘 분석 결과 (신규 메일)</a>
&nbsp;&nbsp;
<a href="https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={history_gid}" style="background-color: #34a853; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📚 전체 이력 보기</a>
</p>

<p style="color: #666; font-size: 12px; margin-top: 20px;">
이 보고서는 Claude Code Email Agent가 자동으로 생성했습니다.
</p>
</body>
</html>
"""

# 보고서 발송
report = gmail.send_summary_report(
    subject=f"📬 이메일 분석 보고서 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    body=report_body,
    label_ids=label_ids
)
print(f"📧 요약 보고서 발송 완료!")

print(f"\n✅ 완료!")
print(f"📊 스프레드시트: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
print(f"   - 신규 메일: 오늘 분석한 이메일")
print(f"   - 처리 이력: 전체 누적 이력")
print(f"📧 Gmail에서 '메일요약' 라벨 확인")
EOF
```

## 분석 기준

### 우선순위 (P1-P5) - 맥락 기반 판단

**핵심 원칙**: 하드코딩된 규칙 없이, 이메일 맥락에서 종합적으로 추론

**5가지 판단 축**:

| 축 | 높음 → 낮음 |
|----|-------------|
| 발신자 관계 | 상위 직급(어투/서명에서 추론) → 자동발송 |
| 요청 강도 | 즉시 결정 필요 → 명시적 요청 → FYI |
| 긴급 신호 | 오늘/ASAP → 이번 주 → 마감일 있음 → 여유 |
| 메일 유형 | 개인 1:1 → 팀 메일 → 전체 공지 → 뉴스레터 |
| 수신 방식 | To(직접) → CC(-1) → 그룹메일(-1) |

**우선순위 정의**:

| P | 기준 |
|---|------|
| **P5** | 상위 직급 추정 + 긴급 키워드 + 즉시 액션 (5-10%만) |
| **P4** | 마감일 1주 내 + 명시적 액션 요청 |
| **P3** | 일반 업무, 여유 있는 회신 (기본값, 애매하면 P3) |
| **P2** | 공지, FYI, 참고용 |
| **P1** | 자동발송, 뉴스레터, 마케팅 |

**판단 힌트**:
- 어투: "부탁드립니다" (동료) vs "확인 바랍니다" (상위 직급 가능성)
- 서명: 직급 표시 (팀장, 부장, Director 등)
- 첫 연락: 처음 받는 메일이면 P3 이상 (관계 파악 필요)

### 마감일 추출

이메일 본문에서 다음 패턴의 마감일 추출:
- "~까지", "마감", "deadline"
- "12월 19일", "2024-12-19" 등
- 설명회, 제출, 신청 기한 등

## 다음 단계

1. **Gmail 임시보관함**에서 자동 생성된 초안 확인/수정
2. (선택) 스프레드시트에서 추가 **초안(제목)**, **초안(내용)** 작성
3. (선택) `/email-draft` 실행하여 추가 초안 생성
4. Gmail에서 직접 발송 또는 `/email-send`로 일괄 발송
