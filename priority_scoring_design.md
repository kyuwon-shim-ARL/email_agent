# 우선순위 점수 시스템 설계 (v2)

## 🎯 설계 철학

### 문제점 분석
1. **교신 이력 ≠ 긴급도**
   - 교신 많다 = 중요한 사람 (발신자 중요도)
   - 교신 많다 ≠ 지금 급함 (내용 긴급도)

2. **3가지 독립적 차원**
   - **누가** (WHO): 발신자가 누구인가?
   - **무엇** (WHAT): 내용이 얼마나 중요/긴급한가?
   - **왜** (WHY): 왜 답장해야 하는가?

3. **점수 체계 복잡도**
   - 단순 합산 → 편향 발생
   - 가중 평균 필요
   - 상황별 가중치 조정

---

## 📊 새로운 3차원 점수 시스템

### 1️⃣ 발신자 중요도 (Sender Importance: 0-100)

**1.1 관계 깊이 (Relationship Depth: 0-50)**

```python
# 가중 교신 점수 계산
weighted_exchanges = (sent × 3) + (received × 1)
# 이유: 내가 보낸 메일 = 내가 관심 있는 사람

점수 매핑:
- weighted >= 100: 50점 (핵심 관계)
- weighted >= 50:  40점
- weighted >= 20:  30점
- weighted >= 10:  20점
- weighted >= 5:   10점
- weighted < 5:    5점
- first_contact:   0점 (관계 없음, 하지만 조사 필요)
```

**1.2 역할/직위 (Role/Position: 0-30)**

```
Claude가 이메일 내용/서명/도메인으로 추론:

30점: CEO, 임원, 이사회
25점: 직속 상사, 부서장
20점: 고객(유료), VIP 파트너
15점: 팀원, 동료, 프로젝트 멤버
10점: 외부 협력사, 일반 고객
5점:  외부 일반, 처음 연락
0점:  자동 시스템, 봇
```

**1.3 최근 교신 빈도 (Recent Activity: 0-20)**

```python
# 최근 7일 내 교신
recent_7days = count_exchanges_last_7_days()

20점: recent >= 10 (매일 교신)
15점: recent >= 5  (주 5회)
10점: recent >= 3  (주 3회)
5점:  recent >= 1  (주 1회)
0점:  recent == 0  (오랜만)
```

**발신자 중요도 총점 = 관계깊이(50) + 역할(30) + 최근빈도(20) = 100점**

---

### 2️⃣ 내용 긴급도 (Content Urgency: 0-100)

**2.1 시간 민감도 (Time Sensitivity: 0-40)**

```
Claude가 분석:

40점: 오늘/지금 필요 ("today", "ASAP", "urgent", "지금", "오늘 안")
35점: 이번 주 필요 ("this week", "EOW", "이번 주")
30점: 마감일 명시 ("deadline", "due date", "~까지")
20점: 곧 필요 ("soon", "upcoming")
10점: 여유 있음 ("when you can", "no rush")
0점:  시간 제약 없음
```

**2.2 액션 요구도 (Action Required: 0-35)**

```
Claude가 분석:

35점: 즉시 결정 필요 (승인, 거절, 선택)
      - "please approve"
      - "need your decision"
      - "confirm by"

30점: 즉시 작업 필요
      - "please send"
      - "can you provide"
      - "need you to"

25점: 직접 질문 (답변 필요)
      - "?" 포함
      - "what do you think"
      - "could you"

15점: 정보 제공 요청
      - "let me know"
      - "update me"

10점: 소프트 요청
      - "if possible"
      - "would appreciate"

5점:  참고 (FYI)
      - "for your information"
      - "heads up"

0점:  액션 불필요
      - 뉴스레터
      - 자동 알림
```

**2.3 내용 중요도 (Content Importance: 0-25)**

```
Claude가 판단:

25점: 비즈니스 크리티컬
      - 계약, 법적 문제
      - 보안 이슈
      - 재무 관련

20점: 프로젝트 크리티컬
      - 프로젝트 차단
      - 팀 블로커
      - 고객 이슈

15점: 업무 중요
      - 미팅 일정
      - 업무 협의
      - 리뷰 요청

10점: 업무 일반
      - 일반 문의
      - 정보 공유

5점:  참고용
      - 공지사항
      - 업데이트

0점:  광고/마케팅
      - 뉴스레터
      - 프로모션
```

**내용 긴급도 총점 = 시간민감도(40) + 액션요구도(35) + 내용중요도(25) = 100점**

---

### 3️⃣ 맥락 보너스/페널티 (Context Modifiers: -20 ~ +20)

**보너스 (+점수)**

```
+20: 첫 연락 (조사 필요)
     - is_first_contact = True
     - 잠재 기회일 수 있음

+15: 긴 대화 스레드 (5+ 왕복)
     - 진행 중인 논의
     - 답장 필요성 높음

+10: 여러 수신자 CC (5+ 명)
     - 가시성 높음
     - 팀 전체 관련

+10: 내가 마지막 발신
     - 내 질문에 대한 답변
     - 높은 관련성

+5:  읽지 않음 (unread)
     - 아직 확인 필요
```

**페널티 (-점수)**

```
-10: 수신만 한 발신자 (sent = 0, received > 5)
     - 일방적 브로드캐스트
     - 회사 공지 등

-15: 자동 발송 감지
     - "Do not reply"
     - "noreply@"
     - "automated message"

-20: 긴 미확인 기간 (14일+)
     - 오래된 메일
     - 우선순위 낮음
```

**맥락 점수 = 보너스 합계 - 페널티 합계 (범위: -20 ~ +20)**

---

## 🧮 최종 우선순위 계산

### 가중 평균 공식

```python
# 3가지 차원에 가중치 적용
final_score = (
    sender_importance × 0.35 +    # 35% - 누가
    content_urgency × 0.50 +      # 50% - 무엇 (가장 중요)
    context_modifiers × 1.0       # 직접 가감
)

# 범위: 0-120 (100 + context 최대 20)
# 정규화: 0-100으로 변환
normalized_score = min(100, max(0, final_score))
```

### 우선순위 매핑

```python
Priority 5 (90-100점): 최우선
  - 긴급 + 중요한 사람
  - 첫 연락 (조사 필요)
  - 비즈니스 크리티컬

Priority 4 (70-89점): 긴급
  - 시간 제약 있음
  - VIP 발신자
  - 액션 필요

Priority 3 (40-69점): 보통
  - 일반 업무
  - 팀원 교신
  - 정보 요청

Priority 2 (20-39점): 낮음
  - FYI 메일
  - 참고용
  - 여유 있음

Priority 1 (0-19점): 최저
  - 뉴스레터
  - 자동 알림
  - 광고
```

---

## 📈 예시 계산

### 예시 1: CEO의 긴급 승인 요청

```
1. 발신자 중요도:
   - 관계 깊이: 20점 (보낸 5회, 받은 10회 → weighted=25)
   - 역할/직위: 30점 (CEO)
   - 최근 빈도: 5점 (이번 주 1회)
   총: 55점

2. 내용 긴급도:
   - 시간 민감도: 40점 ("need approval by EOD today")
   - 액션 요구도: 35점 (즉시 결정 필요)
   - 내용 중요도: 25점 (계약 승인)
   총: 100점

3. 맥락:
   - 내가 마지막 발신: +10
   총: +10

최종 점수:
= (55 × 0.35) + (100 × 0.50) + 10
= 19.25 + 50 + 10
= 79.25 → Priority 4 (긴급)
```

### 예시 2: 처음 연락 온 잠재 고객

```
1. 발신자 중요도:
   - 관계 깊이: 0점 (첫 연락)
   - 역할/직위: 20점 (잠재 고객)
   - 최근 빈도: 0점
   총: 20점

2. 내용 긴급도:
   - 시간 민감도: 10점 ("soon")
   - 액션 요구도: 25점 (직접 질문)
   - 내용 중요도: 20점 (비즈니스 기회)
   총: 55점

3. 맥락:
   - 첫 연락: +20
   총: +20

최종 점수:
= (20 × 0.35) + (55 × 0.50) + 20
= 7 + 27.5 + 20
= 54.5 → Priority 3 (보통)

하지만! 첫 연락 보너스로 인해 Priority 4로 승격 가능
(정책: 첫 연락은 최소 Priority 3 보장)
```

### 예시 3: 회사 공지 (수신만 함)

```
1. 발신자 중요도:
   - 관계 깊이: 5점 (보낸 0회, 받은 50회 → weighted=50)
   - 역할/직위: 15점 (HR 부서)
   - 최근 빈도: 10점 (주 3회)
   총: 30점

2. 내용 긴급도:
   - 시간 민감도: 0점 (시간 제약 없음)
   - 액션 요구도: 5점 (FYI)
   - 내용 중요도: 5점 (공지사항)
   총: 10점

3. 맥락:
   - 수신만 함: -10
   총: -10

최종 점수:
= (30 × 0.35) + (10 × 0.50) + (-10)
= 10.5 + 5 - 10
= 5.5 → Priority 1 (최저)
```

### 예시 4: 팀원의 프로젝트 차단 이슈

```
1. 발신자 중요도:
   - 관계 깊이: 40점 (보낸 20회, 받은 15회 → weighted=75)
   - 역할/직위: 15점 (팀원)
   - 최근 빈도: 20점 (매일 교신)
   총: 75점

2. 내용 긴급도:
   - 시간 민감도: 35점 (this week)
   - 액션 요구도: 30점 (즉시 작업 필요)
   - 내용 중요도: 20점 (프로젝트 차단)
   총: 85점

3. 맥락:
   - 긴 대화 스레드: +15
   - 읽지 않음: +5
   총: +20

최종 점수:
= (75 × 0.35) + (85 × 0.50) + 20
= 26.25 + 42.5 + 20
= 88.75 → Priority 4 (긴급)
```

### 예시 5: 뉴스레터

```
1. 발신자 중요도:
   - 관계 깊이: 5점 (받은 3회)
   - 역할/직위: 0점 (자동 시스템)
   - 최근 빈도: 5점 (주 1회)
   총: 10점

2. 내용 긴급도:
   - 시간 민감도: 0점
   - 액션 요구도: 0점
   - 내용 중요도: 0점
   총: 0점

3. 맥락:
   - 자동 발송: -15
   총: -15

최종 점수:
= (10 × 0.35) + (0 × 0.50) + (-15)
= 3.5 + 0 - 15
= -11.5 → 0점 (최소값) → Priority 1 (최저)
```

---

## 🎯 특수 규칙 (Override Rules)

점수 계산 후 적용:

```python
# 1. 첫 연락 최소 보장
if is_first_contact and priority < 3:
    priority = 3  # 최소 Priority 3 보장
    reason += " (첫 연락 - 조사 필요)"

# 2. 긴급 키워드 강제 승격
if "urgent" in subject.lower() or "ASAP" in body:
    if priority < 4:
        priority = 4
        reason += " (긴급 키워드)"

# 3. CEO/임원 최소 보장
if sender_role_score >= 30:  # CEO/임원
    if priority < 4:
        priority = 4
        reason += " (임원 발신)"

# 4. 자동 발송 강제 하향
if is_automated:
    priority = min(priority, 2)
    reason += " (자동 발송)"
```

---

## 💾 Claude 프롬프트 구조

```
Analyze this email and calculate priority score in 3 dimensions:

EMAIL INFO:
Subject: {subject}
From: {sender}
Body: {body[:500]}
Conversation History:
  - Sent to sender: {total_sent}
  - Received from sender: {total_received}
  - Recent (7 days): {recent_7days}
  - First contact: {is_first_contact}

SCORING FRAMEWORK:

1. SENDER IMPORTANCE (0-100):
   A. Relationship Depth (0-50):
      weighted_exchanges = (sent × 3) + (received × 1) = {weighted}
      Score mapping: [매핑 표]

   B. Role/Position (0-30):
      Infer from email content, signature, domain
      [30=CEO/임원, 25=직속상사, 20=고객/VIP, ...]

   C. Recent Activity (0-20):
      Recent 7-day exchanges: {recent_7days}
      [20=10+, 15=5+, 10=3+, ...]

2. CONTENT URGENCY (0-100):
   A. Time Sensitivity (0-40):
      Look for: today, ASAP, urgent, deadline, 오늘, 지금
      [40=오늘, 35=이번주, 30=마감일, ...]

   B. Action Required (0-35):
      [35=즉시결정, 30=즉시작업, 25=직접질문, ...]

   C. Content Importance (0-25):
      [25=비즈니스크리티컬, 20=프로젝트크리티컬, ...]

3. CONTEXT MODIFIERS (-20 to +20):
   Bonuses: [+20=첫연락, +15=긴스레드, ...]
   Penalties: [-10=수신만, -15=자동발송, ...]

CALCULATION:
final_score = (sender × 0.35) + (urgency × 0.50) + context

RESPOND WITH:
{
  "sender_importance": {
    "relationship_depth": <0-50>,
    "role_position": <0-30>,
    "recent_activity": <0-20>,
    "total": <0-100>
  },
  "content_urgency": {
    "time_sensitivity": <0-40>,
    "action_required": <0-35>,
    "content_importance": <0-25>,
    "total": <0-100>
  },
  "context_modifiers": {
    "bonuses": ["+20: 첫연락", ...],
    "penalties": ["-10: 수신만", ...],
    "total": <-20 to +20>
  },
  "final_score": <0-100>,
  "priority": <1-5>,
  "reason": "detailed explanation"
}
```

---

## 🔧 구현 시 고려사항

### 1. Claude의 판단력 활용
- 역할/직위는 Claude가 이메일 내용으로 추론
- 시간 민감도는 Claude가 문맥 파악
- 내용 중요도는 Claude가 비즈니스 임팩트 평가

### 2. 투명성
- 각 점수의 근거를 `reason`에 명시
- 사용자가 점수 체계 이해 가능
- Sheets에 점수 상세 기록 (선택)

### 3. 조정 가능성
- 가중치 조정 가능 (0.35, 0.50)
- 맥락 보너스/페널티 조정
- 우선순위 임계값 조정

### 4. 특수 케이스
- 첫 연락: 무조건 조사 필요
- CEO/임원: 항상 높은 우선순위
- 자동 발송: 항상 낮은 우선순위

---

## 📊 예상 분포

정상적인 이메일 환경에서:

```
Priority 5 (5-10%):  정말 급하고 중요한 것만
Priority 4 (15-20%): 중요한 사람들의 업무
Priority 3 (40-50%): 대부분의 일반 업무
Priority 2 (15-20%): 참고용, FYI
Priority 1 (10-15%): 뉴스레터, 광고
```

이 분포가 나오지 않으면 가중치 조정 필요.

---

## ✅ 다음 단계

1. 이 설계를 코드로 구현
2. Claude 프롬프트 업데이트
3. 테스트 및 점수 분포 확인
4. 가중치 fine-tuning
5. Gmail 라벨 자동 적용

이 설계가 마음에 드시나요? 수정할 부분이 있으신가요?
