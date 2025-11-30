# 발신자 중요도 관리 시스템 설계

## 🎯 목표

발신자를 자동으로 1차 분류하고, 사용자가 수동으로 확정하여 이후 우선순위 계산에 반영.

---

## 📊 발신자 점수 계산 알고리즘

### 자동 점수 계산 (0-100점)

```python
sender_score = (
    high_priority_ratio × 40 +      # 높은 우선순위 메일 비율
    interaction_frequency × 30 +    # 교신 빈도
    sent_weight × 20 +              # 내가 보낸 비중
    recency × 10                    # 최근 활성도
)
```

#### 1. 높은 우선순위 메일 비율 (0-40점)

```python
# 과거 이 발신자의 메일이 얼마나 높은 우선순위였는가?
high_priority_emails = count(priority >= 4)
total_emails = count(all emails from this sender)
ratio = high_priority_emails / total_emails

점수 매핑:
- ratio >= 0.8 (80%+ P4-5): 40점
- ratio >= 0.6 (60%+ P4-5): 35점
- ratio >= 0.4 (40%+ P4-5): 30점
- ratio >= 0.2 (20%+ P4-5): 20점
- ratio < 0.2:              10점
```

#### 2. 교신 빈도 (0-30점)

```python
total_exchanges = sent + received
weighted_exchanges = (sent × 2) + received

점수 매핑:
- weighted >= 100: 30점 (핵심 관계)
- weighted >= 50:  25점
- weighted >= 20:  20점
- weighted >= 10:  15점
- weighted >= 5:   10점
- weighted < 5:    5점
```

#### 3. 내가 보낸 비중 (0-20점)

```python
# 내가 먼저/자주 보낸 사람 = 중요한 사람
sent_ratio = sent / (sent + received + 1)

점수 매핑:
- sent_ratio >= 0.7: 20점 (내가 주로 보냄 - VIP)
- sent_ratio >= 0.5: 15점 (균형)
- sent_ratio >= 0.3: 10점
- sent_ratio >= 0.1: 5점
- sent_ratio < 0.1:  0점 (수신만 - 공지 등)
```

#### 4. 최근 활성도 (0-10점)

```python
recent_7days = count_emails_last_7_days()

점수 매핑:
- recent >= 10: 10점 (매일 교신)
- recent >= 5:  8점
- recent >= 3:  6점
- recent >= 1:  4점
- recent == 0:  0점
```

---

## 📋 Sheets "발신자 관리" 탭 구조

### 컬럼 설계

```
A: 발신자 (Email)
B: 이름 (추출)
C: 자동점수 (0-100)
D: 수동등급 (VIP / 중요 / 보통 / 낮음 / 차단)
E: 확정점수 (0-100)
F: 총 교신 (sent + received)
G: 보낸 횟수
H: 받은 횟수
I: P4-5 비율 (%)
J: 최근7일
K: 마지막 교신일
L: 메모
```

### 자동 vs 수동 등급 매핑

```python
수동등급 확정점수:
- VIP:    100점 (강제 최고)
- 중요:   80점
- 보통:   50점
- 낮음:   20점
- 차단:   0점
- (비어있음): 자동점수 사용

최종 사용 점수:
if 수동등급 != 비어있음:
    확정점수 = 수동등급 점수
else:
    확정점수 = 자동점수
```

---

## 🔄 워크플로우

### 초기 실행 (첫 번째 사용)

```
1. 프로그램 실행
2. 모든 발신자 분석
   - 과거 이메일 기록 조회
   - 자동 점수 계산
3. "발신자 관리" 탭 생성
4. 모든 발신자 추가 (자동점수 순 정렬)
5. 사용자에게 알림:
   "📊 발신자 관리 탭에서 VIP/중요 발신자를 지정하세요"
```

### 이후 실행

```
1. 프로그램 실행
2. "발신자 관리" 탭 읽기
   - 수동등급이 지정된 발신자 확인
   - 확정점수 로드
3. 새 발신자 발견 시:
   - 자동 점수 계산
   - "발신자 관리" 탭에 추가
4. 기존 발신자:
   - 자동점수 업데이트 (참고용)
   - 확정점수는 수동등급이 있으면 유지
```

### 수동 조정 (사용자)

```
1. Sheets "발신자 관리" 탭 열기
2. 자동점수 확인
3. 중요한 발신자에 수동등급 지정:
   - CEO → "VIP"
   - 팀원들 → "중요"
   - 뉴스레터 → "차단"
4. 다음 실행 시 자동 반영
```

---

## 💻 구현 상세

### 1. SheetsClient에 발신자 탭 관리 추가

```python
def create_sender_management_tab(self, spreadsheet_id: str) -> None:
    """Create 'Senders' tab for sender importance management."""

    # Add new sheet
    requests = [{
        "addSheet": {
            "properties": {
                "title": "발신자 관리",
                "gridProperties": {
                    "rowCount": 1000,
                    "columnCount": 12
                }
            }
        }
    }]

    self.service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()

    # Headers
    headers = [
        "발신자",          # A
        "이름",            # B
        "자동점수",        # C
        "수동등급",        # D (VIP/중요/보통/낮음/차단)
        "확정점수",        # E
        "총교신",          # F
        "보낸횟수",        # G
        "받은횟수",        # H
        "P4-5비율(%)",    # I
        "최근7일",         # J
        "마지막교신",      # K
        "메모",            # L
    ]

    self.service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="발신자 관리!A1:L1",
        valueInputOption="RAW",
        body={"values": [headers]},
    ).execute()

    # Format headers (bold, colored)
    # ... formatting requests ...

    # Data validation for 수동등급 column
    validation_request = {
        "setDataValidation": {
            "range": {
                "sheetId": get_sheet_id("발신자 관리"),
                "startRowIndex": 1,  # Skip header
                "endRowIndex": 1000,
                "startColumnIndex": 3,  # Column D
                "endColumnIndex": 4
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "VIP"},
                        {"userEnteredValue": "중요"},
                        {"userEnteredValue": "보통"},
                        {"userEnteredValue": "낮음"},
                        {"userEnteredValue": "차단"}
                    ]
                },
                "showCustomUi": True
            }
        }
    }

    # Add conditional formatting for 확정점수
    # 80-100: Green
    # 50-79: Yellow
    # 0-49: Red


def add_or_update_sender(
    self,
    spreadsheet_id: str,
    sender_email: str,
    sender_stats: dict
) -> None:
    """Add or update sender in management tab."""

    # Check if sender exists
    existing = self.get_sender_row(spreadsheet_id, sender_email)

    # Calculate auto score
    auto_score = self._calculate_sender_auto_score(sender_stats)

    # Extract name from email
    name = sender_stats.get('name', sender_email.split('@')[0])

    if existing:
        # Update existing row (keep manual grade if set)
        row_number = existing['row_number']
        manual_grade = existing.get('manual_grade', '')

        # Update auto score and stats only
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"발신자 관리!C{row_number}:K{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [[
                auto_score,                           # C: 자동점수
                manual_grade,                         # D: 수동등급 (유지)
                self._get_final_score(auto_score, manual_grade),  # E: 확정점수
                sender_stats['total_exchanges'],      # F: 총교신
                sender_stats['total_sent'],           # G: 보낸횟수
                sender_stats['total_received'],       # H: 받은횟수
                sender_stats['high_priority_ratio'],  # I: P4-5비율
                sender_stats.get('recent_7days', 0),  # J: 최근7일
                sender_stats.get('last_contact', ''), # K: 마지막교신
            ]]},
        ).execute()
    else:
        # Add new row
        row = [
            sender_email,                         # A: 발신자
            name,                                 # B: 이름
            auto_score,                           # C: 자동점수
            '',                                   # D: 수동등급 (비어있음)
            auto_score,                           # E: 확정점수 (초기=자동)
            sender_stats['total_exchanges'],      # F: 총교신
            sender_stats['total_sent'],           # G: 보낸횟수
            sender_stats['total_received'],       # H: 받은횟수
            sender_stats['high_priority_ratio'],  # I: P4-5비율
            sender_stats.get('recent_7days', 0),  # J: 최근7일
            sender_stats.get('last_contact', ''), # K: 마지막교신
            '',                                   # L: 메모
        ]

        self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="발신자 관리!A:L",
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        ).execute()


def _calculate_sender_auto_score(self, stats: dict) -> int:
    """Calculate automatic sender importance score (0-100)."""

    # 1. High priority ratio (0-40)
    high_priority_ratio = stats.get('high_priority_ratio', 0)
    if high_priority_ratio >= 0.8:
        score_1 = 40
    elif high_priority_ratio >= 0.6:
        score_1 = 35
    elif high_priority_ratio >= 0.4:
        score_1 = 30
    elif high_priority_ratio >= 0.2:
        score_1 = 20
    else:
        score_1 = 10

    # 2. Interaction frequency (0-30)
    sent = stats.get('total_sent', 0)
    received = stats.get('total_received', 0)
    weighted = (sent * 2) + received

    if weighted >= 100:
        score_2 = 30
    elif weighted >= 50:
        score_2 = 25
    elif weighted >= 20:
        score_2 = 20
    elif weighted >= 10:
        score_2 = 15
    elif weighted >= 5:
        score_2 = 10
    else:
        score_2 = 5

    # 3. Sent weight (0-20)
    total = sent + received
    if total > 0:
        sent_ratio = sent / total
        if sent_ratio >= 0.7:
            score_3 = 20
        elif sent_ratio >= 0.5:
            score_3 = 15
        elif sent_ratio >= 0.3:
            score_3 = 10
        elif sent_ratio >= 0.1:
            score_3 = 5
        else:
            score_3 = 0
    else:
        score_3 = 0

    # 4. Recency (0-10)
    recent = stats.get('recent_7days', 0)
    if recent >= 10:
        score_4 = 10
    elif recent >= 5:
        score_4 = 8
    elif recent >= 3:
        score_4 = 6
    elif recent >= 1:
        score_4 = 4
    else:
        score_4 = 0

    total_score = score_1 + score_2 + score_3 + score_4
    return min(100, total_score)


def _get_final_score(self, auto_score: int, manual_grade: str) -> int:
    """Get final score based on manual grade or auto score."""

    grade_scores = {
        'VIP': 100,
        '중요': 80,
        '보통': 50,
        '낮음': 20,
        '차단': 0,
    }

    if manual_grade and manual_grade in grade_scores:
        return grade_scores[manual_grade]
    else:
        return auto_score


def get_sender_importance_scores(
    self,
    spreadsheet_id: str
) -> dict[str, int]:
    """
    Get final importance scores for all senders.

    Returns:
        Dict mapping sender email to final score (0-100)
    """
    result = self.service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="발신자 관리!A2:E",  # Email + Final Score
    ).execute()

    rows = result.get("values", [])
    scores = {}

    for row in rows:
        if len(row) >= 5:
            sender_email = row[0]
            final_score = int(row[4])  # Column E: 확정점수
            scores[sender_email] = final_score

    return scores
```

---

## 🔄 우선순위 계산에 통합

### skill에서 발신자 점수 사용

```python
# main_sheets.py에서
sender_scores = sheets.get_sender_importance_scores(spreadsheet_id)

# 프롬프트 생성 시 추가
for email in emails:
    sender = email['sender']

    # 확정된 발신자 점수 가져오기
    sender_importance_override = sender_scores.get(sender, None)

    prompt += f"""
    EMAIL #{i}
    Subject: {subject}
    From: {sender}

    SENDER IMPORTANCE OVERRIDE:
    - Final Score (from Sender Management): {sender_importance_override if sender_importance_override else "None (use auto calculation)"}

    If sender has a final score, use it directly for sender_importance.total.
    Otherwise, calculate automatically using conversation history.
    """
```

### skill 업데이트

```markdown
# In .claude/skills/prioritize-email.md

## SENDER IMPORTANCE OVERRIDE

If the prompt provides "SENDER IMPORTANCE OVERRIDE" with a final score:
- Use that score directly as sender_importance.total
- Still provide breakdown (estimate based on score)
- Mark as "Override from Sender Management"

Example:
If override = 100 (VIP):
  sender_importance.total = 100
  relationship_depth = 50 (estimate)
  role_position = 30 (estimate - VIP)
  recent_activity = 20 (estimate)
  Note: "Override from Sender Management (VIP)"
```

---

## 📈 사용자 경험

### 첫 실행

```
📊 발신자 분석 중...
   - 50명의 발신자 발견
   - 자동 점수 계산 완료

✨ 발신자 관리 탭 생성됨!
   https://docs.google.com/spreadsheets/d/ABC123.../edit#gid=123

💡 추천:
   1. "발신자 관리" 탭 열기
   2. 자동점수 확인
   3. VIP/중요 발신자 지정:
      - CEO, 상사 → "VIP"
      - 주요 팀원 → "중요"
      - 뉴스레터 → "차단"
   4. 다음 실행 시 자동 반영됩니다!

발신자 TOP 5 (자동점수):
  1. ceo@company.com (95점)
  2. manager@company.com (88점)
  3. teammate@company.com (72점)
  ...
```

### 이후 실행

```
📊 발신자 관리 로드...
   - 10명 VIP
   - 15명 중요
   - 3명 차단

✅ 확정 점수 적용됨
   VIP 발신자의 메일은 자동으로 높은 우선순위!
```

---

## 🎯 장점

1. **완전 자동 가능** - 수동 지정 없어도 작동
2. **수동 미세조정 가능** - 사용자가 VIP 지정
3. **학습 효과** - 시간이 지날수록 정확해짐
4. **투명성** - 자동점수 vs 수동등급 명확히 구분
5. **유연성** - 언제든 수동등급 변경 가능

---

이 설계가 마음에 드시나요? 바로 구현 시작할까요?
