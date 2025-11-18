# 설치 가이드 (다른 사용자용)

**Email Agent를 본인의 환경에서 사용하기 위한 완벽 가이드**

## 📋 사전 요구사항

- Python 3.11 이상
- Claude Code 설치됨
- Gmail 계정
- Git

## 🚀 빠른 설치 (5분)

### 1. 저장소 클론

```bash
# 원하는 위치로 이동
cd ~/projects  # 또는 원하는 디렉토리

# 저장소 클론
git clone https://github.com/YOUR_USERNAME/email_agent.git
cd email_agent
```

### 2. Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows

# 패키지 설치
pip install -e .
```

### 3. Gmail API 설정 (최초 1회, 약 10분)

이 단계가 가장 중요합니다! 차근차근 따라하세요.

#### 3-1. Google Cloud Console 접속

1. https://console.cloud.google.com/ 접속
2. Google 계정 로그인

#### 3-2. 프로젝트 생성

1. 상단 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름: `email-agent` (또는 원하는 이름)
4. "만들기" 클릭
5. 생성 완료 후 프로젝트 선택

#### 3-3. Gmail API 활성화

1. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
2. 검색창에 "Gmail API" 입력
3. "Gmail API" 선택
4. "사용" 버튼 클릭

#### 3-4. OAuth 동의 화면 구성

1. 좌측 메뉴 → "API 및 서비스" → "OAuth 동의 화면"
2. User Type: **"외부"** 선택 → "만들기"
3. 앱 정보 입력:
   - 앱 이름: `Email Agent`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
4. "저장 후 계속"

5. **범위 설정** (중요!):
   - "범위 추가 또는 삭제" 클릭
   - 검색창에 "gmail" 입력
   - 다음 두 개 체크:
     - ✅ `.../auth/gmail.readonly` (이메일 읽기)
     - ✅ `.../auth/gmail.compose` (초안 작성)
   - "업데이트" → "저장 후 계속"

6. **테스트 사용자 추가** (중요!):
   - "+ ADD USERS" 클릭
   - 본인 Gmail 주소 입력
   - "추가" → "저장 후 계속"

7. "대시보드로 돌아가기"

#### 3-5. OAuth 클라이언트 ID 생성

1. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
2. "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: **"데스크톱 앱"** 선택
4. 이름: `Email Agent CLI`
5. "만들기" 클릭
6. **"JSON 다운로드"** 버튼 클릭 ⬇️
7. 다운로드된 파일을 `credentials.json`으로 저장

#### 3-6. credentials.json 배치

```bash
# 다운로드 폴더에서 email_agent 폴더로 복사
cp ~/Downloads/client_secret_*.json ~/projects/email_agent/credentials.json

# 파일 확인
ls -l credentials.json
# -rw-r--r-- 1 user user 582 Nov 18 10:30 credentials.json
```

### 4. 첫 실행 및 OAuth 인증

```bash
# 가상환경이 활성화된 상태에서
email-classify
```

**예상 동작:**

1. 브라우저가 자동으로 열림
2. Google 계정 선택
3. **"Google에서 확인되지 않음" 경고** 표시됨 (정상!)
   - "고급" 클릭
   - "Email Agent(안전하지 않음)로 이동" 클릭
4. 권한 승인:
   - Gmail 읽기 ✓
   - Gmail 초안 작성 ✓
5. "계속" 클릭
6. `token.json` 파일 자동 생성
7. 프로그램 실행 시작!

## 🎯 실제 사용 예시

```bash
$ email-classify

🔍 Email Classifier (Claude Code Edition - FREE!)
   ✨ NEW: Sender-specific styles + Priority ranking
   No API costs - runs in your Claude Code session

📧 Connecting to Gmail...
🤖 Initializing Claude Code classifier...

================================================================================
STEP 1: LEARN YOUR DEFAULT WRITING STYLE
================================================================================

✍️  Fetching your sent emails...
   → Found 50 sent emails

✅ Default style analysis prompt ready!
   File: /tmp/email_classifier/analyze_style.txt

================================================================================
ACTION REQUIRED:
================================================================================
1. Run: cat /tmp/email_classifier/analyze_style.txt
2. Copy the prompt
3. Paste it to Claude Code (in this conversation)
4. Copy Claude's JSON response
5. Paste it below
================================================================================

📋 Paste Claude's default style JSON:
```

**이후 5단계 진행** (README.md 참조)

## 📁 설치 후 폴더 구조

```
email_agent/
├── .venv/                    # 가상환경 (자동 생성)
├── email_classifier/         # 핵심 코드
├── docs/                     # 문서
├── credentials.json          # Google OAuth (직접 추가)
├── token.json               # OAuth 토큰 (자동 생성)
├── README.md                # 사용 가이드
├── GETTING_STARTED.md       # 빠른 시작
└── pyproject.toml           # 패키지 설정
```

## 🐛 설치 중 문제 해결

### Python 버전 확인

```bash
python3 --version
# Python 3.11.0 이상이어야 함

# 버전이 낮으면 업그레이드
# Ubuntu/Debian:
sudo apt update && sudo apt install python3.11

# macOS:
brew install python@3.11
```

### pip install 에러

```bash
# pip 업그레이드
pip install --upgrade pip

# 의존성 개별 설치
pip install google-api-python-client
pip install google-auth-oauthlib
pip install google-auth-httplib2
```

### credentials.json not found

```bash
# 파일 위치 확인
ls -la | grep credentials

# 없으면 3-6 단계 다시 수행
# 파일명 확인 (정확히 credentials.json이어야 함)
```

### "Google에서 확인되지 않음" 경고

**이건 정상입니다!** 개인 프로젝트이므로 Google 검증을 받지 않았습니다.

**안전하게 진행:**
1. "고급" 클릭
2. "Email Agent(안전하지 않음)로 이동" 클릭
3. 본인이 만든 앱이므로 안전합니다

### Error 403: access_denied

**원인:** OAuth 동의 화면에서 테스트 사용자를 추가하지 않음

**해결:**
1. Google Cloud Console → OAuth 동의 화면
2. "테스트 사용자" 섹션 → "+ ADD USERS"
3. 본인 Gmail 주소 추가
4. `token.json` 삭제 후 재시도:
   ```bash
   rm token.json
   email-classify
   ```

### 브라우저가 안 열림

**수동 인증:**
1. 터미널에 출력된 URL 복사
2. 브라우저에 수동으로 붙여넣기
3. 인증 진행

## 🔄 업데이트 방법

```bash
cd email_agent

# 최신 코드 가져오기
git pull origin main

# 가상환경 활성화
source .venv/bin/activate

# 패키지 재설치
pip install -e .
```

## 🗑️ 제거 방법

```bash
# 1. 가상환경 비활성화
deactivate

# 2. 폴더 전체 삭제
rm -rf ~/projects/email_agent

# 3. Google Cloud Console에서 프로젝트 삭제 (선택)
# https://console.cloud.google.com/
# → 프로젝트 선택 → 설정 → 프로젝트 종료
```

## 💡 다음 단계

설치가 완료되었다면:

1. **사용 방법**: `README.md` 읽기
2. **빠른 시작**: `GETTING_STARTED.md` 보기
3. **실행**: `email-classify` 명령어로 시작!

## 🆘 도움이 필요하신가요?

- **문서**: `docs/` 폴더의 상세 가이드 확인
- **Issues**: GitHub Issues에 질문 남기기
- **이메일**: 프로젝트 관리자에게 연락

---

**설치 완료!** 이제 `email-classify`를 실행해보세요! 🎉
