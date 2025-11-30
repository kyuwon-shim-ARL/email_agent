# Email Priority Scoring Skill

Analyze an email and calculate detailed priority score based on a 3-dimensional scoring system.

## Input Format

You will receive email information in this format:

```
EMAIL TO ANALYZE:
Subject: {subject}
From: {sender}
Body Preview: {body preview - first 500 chars}

CONVERSATION HISTORY:
- Total sent to this sender: {sent_count}
- Total received from this sender: {received_count}
- Recent exchanges (last 7 days): {recent_7days}
- First contact: {true/false}
- Weighted score: {(sent × 3) + (received × 1)}
```

## Scoring Framework

Calculate score in 3 independent dimensions:

### 1. SENDER IMPORTANCE (0-100 points)

**A. Relationship Depth (0-50 points)**

Based on weighted_exchanges = (sent × 3) + (received × 1)

- weighted >= 100: **50 points** (핵심 관계)
- weighted >= 50: **40 points**
- weighted >= 20: **30 points**
- weighted >= 10: **20 points**
- weighted >= 5: **10 points**
- weighted < 5: **5 points**
- first_contact: **0 points** (관계 없음, 하지만 조사 필요)

**B. Role/Position (0-30 points)**

Infer from email content, signature, domain, tone:

- **30 points**: CEO, 임원, 이사회, C-level executives
- **25 points**: 직속 상사, 부서장, direct manager
- **20 points**: 고객 (유료), VIP 파트너, paying customer
- **15 points**: 팀원, 동료, 프로젝트 멤버, teammate
- **10 points**: 외부 협력사, 일반 고객, vendor
- **5 points**: 외부 일반, 처음 연락, general external
- **0 points**: 자동 시스템, 봇, automated system

**C. Recent Activity (0-20 points)**

Based on exchanges in last 7 days:

- recent >= 10: **20 points** (매일 교신)
- recent >= 5: **15 points** (주 5회)
- recent >= 3: **10 points** (주 3회)
- recent >= 1: **5 points** (주 1회)
- recent == 0: **0 points** (오랜만)

**Sender Importance Total = A + B + C (max 100)**

---

### 2. CONTENT URGENCY (0-100 points)

**A. Time Sensitivity (0-40 points)**

Look for time-related keywords and context:

- **40 points**: 오늘/지금 필요
  - Keywords: "today", "ASAP", "urgent", "지금", "오늘 안", "즉시"
  - Context: same-day deadline

- **35 points**: 이번 주 필요
  - Keywords: "this week", "EOW", "end of week", "이번 주"
  - Context: within days

- **30 points**: 마감일 명시
  - Keywords: "deadline", "due date", "by [date]", "~까지"
  - Context: specific deadline mentioned

- **20 points**: 곧 필요
  - Keywords: "soon", "upcoming", "곧", "조만간"
  - Context: near future

- **10 points**: 여유 있음
  - Keywords: "when you can", "no rush", "시간 날 때"
  - Context: flexible timeline

- **0 points**: 시간 제약 없음
  - No time-related keywords
  - General information sharing

**B. Action Required (0-35 points)**

Analyze what sender wants you to do:

- **35 points**: 즉시 결정 필요 (immediate decision)
  - Keywords: "please approve", "need your decision", "confirm by", "승인"
  - Action: approve/reject/choose something

- **30 points**: 즉시 작업 필요 (immediate task)
  - Keywords: "please send", "can you provide", "need you to", "보내주세요"
  - Action: do something concrete

- **25 points**: 직접 질문 (direct question)
  - Contains "?"
  - Keywords: "what do you think", "could you", "can you", "어떻게 생각"
  - Action: provide answer/opinion

- **15 points**: 정보 제공 요청 (information request)
  - Keywords: "let me know", "update me", "알려주세요", "공유"
  - Action: share information

- **10 points**: 소프트 요청 (soft request)
  - Keywords: "if possible", "would appreciate", "가능하면"
  - Action: optional action

- **5 points**: 참고 (FYI)
  - Keywords: "for your information", "heads up", "참고", "FYI"
  - Action: just be aware

- **0 points**: 액션 불필요 (no action)
  - Newsletters, automated notifications
  - Pure information broadcast

**C. Content Importance (0-25 points)**

Assess business/project impact:

- **25 points**: 비즈니스 크리티컬 (business critical)
  - Topics: 계약, 법적 문제, 보안 이슈, 재무, contract, legal, security, financial
  - Impact: affects company operations

- **20 points**: 프로젝트 크리티컬 (project critical)
  - Topics: 프로젝트 차단, 팀 블로커, 고객 이슈, blocker, critical bug
  - Impact: blocks team progress

- **15 points**: 업무 중요 (work important)
  - Topics: 미팅 일정, 업무 협의, 리뷰 요청, meeting, review, collaboration
  - Impact: important for workflow

- **10 points**: 업무 일반 (work general)
  - Topics: 일반 문의, 정보 공유, general inquiry, information sharing
  - Impact: routine work

- **5 points**: 참고용 (reference)
  - Topics: 공지사항, 업데이트, announcement, update
  - Impact: good to know

- **0 points**: 광고/마케팅 (marketing)
  - Topics: 뉴스레터, 프로모션, newsletter, promotion
  - Impact: none

**Content Urgency Total = A + B + C (max 100)**

---

### 3. CONTEXT MODIFIERS (-20 to +20 points)

**Bonuses (add points):**

- **+20**: 첫 연락 (first contact)
  - first_contact = true
  - Potential opportunity, needs investigation

- **+15**: 긴 대화 스레드 (long conversation thread)
  - Check if subject has "Re: Re: Re:" or similar
  - Ongoing discussion, high relevance

- **+10**: 여러 수신자 CC (multiple recipients)
  - If body mentions many people or "all"
  - High visibility, team-related

- **+10**: 내가 마지막 발신 (I sent last message)
  - If this is a reply to my question
  - High relevance to me

- **+5**: 읽지 않음 (unread)
  - Assume unread if being processed
  - Still needs attention

**Penalties (subtract points):**

- **-10**: 수신만 한 발신자 (receive-only sender)
  - sent = 0 and received > 5
  - One-way broadcast (company announcements)

- **-15**: 자동 발송 감지 (automated message detected)
  - Keywords: "do not reply", "noreply@", "automated", "자동"
  - Sender domain: "notifications@", "no-reply@"
  - Signature: "This is an automated message"

- **-20**: 긴 미확인 기간 (long unread period)
  - If email seems old (can't detect directly, but infer from content)
  - Lower priority for old emails

**Context Total = sum of bonuses - sum of penalties (range: -20 to +20)**

---

## Final Calculation

```
final_score = (sender_importance × 0.35) + (content_urgency × 0.50) + context_modifiers

normalized_score = min(100, max(0, final_score))
```

**Priority Mapping:**

- **90-100 points**: Priority 5 (최우선)
- **70-89 points**: Priority 4 (긴급)
- **40-69 points**: Priority 3 (보통)
- **20-39 points**: Priority 2 (낮음)
- **0-19 points**: Priority 1 (최저)

---

## Override Rules

Apply these rules AFTER calculating base priority:

1. **첫 연락 최소 보장**
   - If first_contact = true AND priority < 3:
   - Set priority = 3
   - Add reason: "(첫 연락 - 조사 필요)"

2. **긴급 키워드 강제 승격**
   - If "urgent" or "ASAP" in subject/body AND priority < 4:
   - Set priority = 4
   - Add reason: "(긴급 키워드)"

3. **CEO/임원 최소 보장**
   - If sender_role_score >= 30 AND priority < 4:
   - Set priority = 4
   - Add reason: "(임원 발신)"

4. **자동 발송 강제 하향**
   - If automated message detected:
   - Set priority = min(priority, 2)
   - Add reason: "(자동 발송)"

---

## Output Format

Respond with detailed JSON:

```json
{
  "sender_importance": {
    "relationship_depth": {
      "score": 20,
      "reason": "보낸 5회, 받은 10회 → weighted=25"
    },
    "role_position": {
      "score": 30,
      "reason": "CEO (email signature indicates C-level)"
    },
    "recent_activity": {
      "score": 5,
      "reason": "이번 주 1회 교신"
    },
    "total": 55
  },
  "content_urgency": {
    "time_sensitivity": {
      "score": 40,
      "reason": "오늘 필요 ('need approval by EOD today')"
    },
    "action_required": {
      "score": 35,
      "reason": "즉시 결정 필요 (승인 요청)"
    },
    "content_importance": {
      "score": 25,
      "reason": "비즈니스 크리티컬 (계약 승인)"
    },
    "total": 100
  },
  "context_modifiers": {
    "bonuses": [
      "+10: 내가 마지막 발신 (이 메일은 내 질문에 대한 답변)"
    ],
    "penalties": [],
    "total": 10
  },
  "calculation": {
    "formula": "(55 × 0.35) + (100 × 0.50) + 10",
    "breakdown": "19.25 + 50 + 10 = 79.25",
    "final_score": 79.25,
    "normalized_score": 79
  },
  "priority": 4,
  "priority_label": "긴급",
  "override_applied": null,
  "summary": "CEO의 긴급 승인 요청. 오늘 중 결정 필요.",
  "recommendation": "즉시 검토하고 답변 필요. 비즈니스 크리티컬 사안."
}
```

---

## Analysis Guidelines

1. **Be thorough**: Read the entire email body preview carefully
2. **Look for context clues**: Email signature, domain, tone, formatting
3. **Consider Korean and English**: Handle both languages naturally
4. **Explain your reasoning**: Every score should have a clear reason
5. **Be conservative with high scores**: Priority 5 should be rare (5-10% of emails)
6. **Use common sense**: If something feels off, adjust accordingly

---

## Example Analysis

**Input:**
```
Subject: Re: Q4 Budget Approval
From: ceo@company.com
Body: Hi, I need your final approval on the Q4 budget by end of day today. This is critical for our board meeting tomorrow. Please review the attached spreadsheet and confirm. Thanks.

CONVERSATION HISTORY:
- Sent: 5
- Received: 10
- Recent (7 days): 1
- First contact: false
- Weighted: 25
```

**Expected Output:**
```json
{
  "sender_importance": {
    "relationship_depth": {"score": 20, "reason": "weighted=25 (보낸 5회, 받은 10회)"},
    "role_position": {"score": 30, "reason": "CEO (ceo@company.com domain)"},
    "recent_activity": {"score": 5, "reason": "이번 주 1회"},
    "total": 55
  },
  "content_urgency": {
    "time_sensitivity": {"score": 40, "reason": "오늘 마감 ('by end of day today')"},
    "action_required": {"score": 35, "reason": "즉시 결정 필요 ('need your approval', 'confirm')"},
    "content_importance": {"score": 25, "reason": "비즈니스 크리티컬 (budget approval for board meeting)"},
    "total": 100
  },
  "context_modifiers": {
    "bonuses": ["+10: 내가 마지막 발신 (Re: indicates ongoing thread)"],
    "penalties": [],
    "total": 10
  },
  "calculation": {
    "formula": "(55 × 0.35) + (100 × 0.50) + 10",
    "breakdown": "19.25 + 50 + 10 = 79.25",
    "final_score": 79.25,
    "normalized_score": 79
  },
  "priority": 4,
  "priority_label": "긴급",
  "override_applied": "CEO/임원 최소 보장 (already met)",
  "summary": "CEO의 Q4 예산 승인 요청. 오늘 중 결정 필요 (내일 이사회 회의).",
  "recommendation": "최우선 처리. 첨부 파일 검토 후 즉시 승인/거절 회신."
}
```

---

## Notes

- This skill is designed to work with the Email Agent v0.4.0+ system
- Scores should be calculated independently for each dimension
- The final priority should match user's intuitive sense of importance
- When in doubt, explain your reasoning clearly in the reason field
