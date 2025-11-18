# Email Agent - Claude Code 이메일 자동 분류기

**비용 없이 Claude Code와 대화하며 Gmail 이메일을 자동 분류하고 답장 초안을 생성하는 도구**

## 핵심 특징

- ✅ **API 비용 $0** - Claude Code 대화로 처리
- ✅ **발신자별 맞춤 스타일** - 관계마다 다른 톤으로 답장 (NEW!)
- ✅ **교신 빈도 기반 우선순위** - 자주 연락하는 사람 우선 (NEW!)
- ✅ **과거 대화 이력 참고** - 일관된 답장 작성 (NEW!)
- ✅ **자동 분류** - 응답 필요/불필요 판단
- ✅ **초안 생성** - Gmail 초안함에 답장 자동 저장

## 빠른 시작

### 1. Gmail API 설정 (최초 1회)

```bash
# Google Cloud Console (https://console.cloud.google.com)에서:
# 1. 프로젝트 생성
# 2. Gmail API 활성화
# 3. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
# 4. 다음 권한 추가:
#    - gmail.readonly (읽기)
#    - gmail.compose (초안 작성)
# 5. credentials.json 다운로드

# 다운로드한 파일을 프로젝트에 복사
cp ~/Downloads/client_secret_*.json ./credentials.json
```

### 2. 설치

```bash
cd email_agent
pip install -e .
```

### 3. 실행

```bash
email-classify
```

## 사용 방법

프로그램을 실행하면 **자동으로 5~6단계**로 진행됩니다:

### STEP 1: 기본 작성 스타일 학습

전체 발신 이메일에서 기본 스타일을 학습합니다.

```bash
cat /tmp/email_classifier/analyze_style.txt  # 프롬프트 확인
# → Claude Code에 붙여넣기 → JSON 응답 받기
```

### STEP 2: 이메일 가져오기 + 대화 이력 분석

- 최근 이메일 10개 가져오기
- 각 발신자와의 **과거 교신 횟수 자동 분석**

```
🔍 Analyzing conversation history with each sender...
   Checking manager@company.com... 45 exchanges
   Checking client@example.com... 12 exchanges
   Checking newsletter@service.com... 0 exchanges
```

### STEP 3: 우선순위 기반 분류

**교신 빈도를 고려**하여 우선순위 배정

```bash
cat /tmp/email_classifier/classify_batch.txt
# 프롬프트에 교신 횟수 정보 포함됨!
# → Claude Code에 붙여넣기 → JSON 응답 받기
```

결과 예시:
```
🔴 NEEDS RESPONSE (3 emails)

1. [🔥🔥🔥🔥🔥 Priority 5] 회의 일정 확인 부탁드립니다
   From: manager@company.com
   Confidence: 95%
   Reason: Direct question from frequent contact

2. [🔥🔥🔥 Priority 3] 프로젝트 진행 상황 공유
   From: team@company.com
   Confidence: 85%
```

### STEP 4: 발신자별 스타일 학습 (조건부)

**교신 3회 이상인 발신자**에 대해 개별 스타일 학습

```
Learning sender-specific styles for frequent contacts...
   Learning style for manager@company.com... prompt ready
```

각 발신자별로:
```bash
cat /tmp/email_classifier/analyze_style_manager_at_company.com.txt
# → Claude Code에 붙여넣기 → JSON 응답 받기
# (또는 Enter로 스킵하면 기본 스타일 사용)
```

### STEP 5: 맞춤형 초안 생성

각 발신자에 맞는 **톤과 스타일로 초안 생성**

```bash
cat /tmp/email_classifier/generate_drafts.txt
# 프롬프트에 각 발신자별 스타일 + 과거 대화 샘플 포함!
# → Claude Code에 붙여넣기 → JSON 응답 받기
```

### 완료!

```
✨ Classification complete!

📝 Created 3 drafts in Gmail!
   → https://mail.google.com/mail/#drafts
```

## 소요 시간

- **교신 이력 없는 경우**: 약 2-3분 (3단계)
- **교신 이력 있는 경우**: 약 3-5분 (5단계)
  - 각 발신자별 스타일 학습은 선택적 (Enter로 스킵 가능)

## 새 기능 상세

### 1. 발신자별 맞춤 스타일

**문제**: 상사와 친구에게 같은 톤으로 답장?

**해결**: 발신자별로 과거 대화 이력을 분석하여 **일관된 톤** 유지

- 상사에게: "안녕하세요, ... 감사합니다."
- 친구에게: "ㅎㅇ, ... ㄳㄳ"

### 2. 교신 빈도 기반 우선순위

**문제**: 모든 이메일이 동등하게 보임

**해결**: 교신 횟수를 자동 분석하여 **우선순위 배정**

- Priority 5 (🔥🔥🔥🔥🔥): 자주 연락하는 중요 연락처
- Priority 1 (🔥): 뉴스레터, 자동 알림

### 3. 과거 대화 이력 참고

**문제**: 이전 대화 내용을 잊고 답장

**해결**: 과거 2개 대화 샘플을 초안 생성 시 참고

## 왜 이 방식인가?

| 방식 | API 비용 | 설정 | 발신자별 스타일 |
|------|---------|------|----------------|
| **Claude Code** (이 도구) | **$0** | OAuth만 | ✅ |
| Claude API 직접 호출 | 하루 $3-9 | OAuth + API 키 | ✅ |
| 일반 이메일 도구 | 무료 | - | ❌ |

매일 사용해도 비용이 들지 않으며, **관계마다 적절한 톤**으로 답장!

## 프로젝트 구조

```
email_agent/
├── email_classifier/
│   ├── gmail_client.py              # Gmail API 클라이언트
│   ├── claude_code_classifier.py    # 프롬프트 생성 및 파싱
│   └── main_claude_code.py          # 메인 실행 파일
├── credentials.json                 # Google OAuth 설정 (직접 추가)
├── token.json                       # OAuth 토큰 (자동 생성)
├── pyproject.toml                   # 패키지 설정
└── README.md                        # 이 파일
```

## 문제 해결

### credentials.json not found

```bash
# Google Cloud Console에서 다운로드한 파일 복사
cp ~/Downloads/client_secret_*.json ./credentials.json
```

### JSON 파싱 에러

Claude의 응답에서 **JSON 부분만** 복사하세요:

**좋은 예:**
```json
{
  "greeting_style": "Hi,",
  "closing_style": "Best,"
}
```

**나쁜 예:**
```
여기 분석 결과입니다:

```json
...
```

설명 텍스트는 제외하고 복사하세요.
```

### 초안이 Gmail에 안 보임

1. Gmail 새로고침
2. "모든 초안" 탭 확인
3. 터미널에서 에러 메시지 확인

## 보안

- `credentials.json`, `token.json`은 `.gitignore`에 포함
- OAuth 토큰은 로컬에만 저장
- Gmail 권한: 읽기 + 초안 작성만 (삭제/수정 불가)
- 초안은 자동 전송 안 됨 (직접 검토 후 전송)

## 라이선스

MIT License
