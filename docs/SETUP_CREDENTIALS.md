# Gmail API credentials.json 설정 가이드

## 📋 개요

`credentials.json` 파일은 Gmail API를 사용하기 위한 OAuth 2.0 인증 정보입니다.
Google Cloud Console에서 한 번만 설정하면 됩니다.

**소요 시간**: 약 10분

---

## 🚀 단계별 설정

### Step 1: Google Cloud Console 접속

1. 브라우저에서 https://console.cloud.google.com/ 접속
2. Google 계정으로 로그인

---

### Step 2: 프로젝트 생성

1. 상단 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 정보 입력:
   - **프로젝트 이름**: `email-classifier` (또는 원하는 이름)
   - **조직**: (없으면 비워두기)
4. "만들기" 클릭
5. 생성 완료까지 10-20초 대기
6. 상단 알림에서 "프로젝트 선택" 클릭

---

### Step 3: Gmail API 활성화

1. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
2. 검색창에 **"Gmail API"** 입력
3. "Gmail API" 선택
4. **"사용"** 버튼 클릭
5. 활성화 완료 (몇 초 소요)

---

### Step 4: OAuth 동의 화면 구성

**중요**: 이 단계를 먼저 해야 OAuth 클라이언트 ID를 만들 수 있습니다!

1. 좌측 메뉴 → "API 및 서비스" → **"OAuth 동의 화면"**
2. User Type 선택:
   - ✅ **"외부"** 선택 (개인 사용)
   - "만들기" 클릭

3. **앱 정보 입력**:
   - 앱 이름: `Email Classifier`
   - 사용자 지원 이메일: `your-email@gmail.com` (본인 이메일)
   - 개발자 연락처 정보: `your-email@gmail.com` (본인 이메일)
4. "저장 후 계속" 클릭

5. **범위 설정** (중요!):
   - "범위 추가 또는 삭제" 클릭
   - 검색창에 "gmail" 입력
   - 다음 두 개 체크:
     - ✅ `.../auth/gmail.readonly` (Gmail 이메일 읽기)
     - ✅ `.../auth/gmail.compose` (Gmail 초안 작성)
   - "업데이트" 클릭
   - "저장 후 계속" 클릭

6. **테스트 사용자 추가** (중요!):
   - "+ ADD USERS" 클릭
   - 본인 Gmail 주소 입력: `your-email@gmail.com`
   - "추가" 클릭
   - "저장 후 계속" 클릭

7. "대시보드로 돌아가기" 클릭

---

### Step 5: OAuth 2.0 클라이언트 ID 생성

1. 좌측 메뉴 → "API 및 서비스" → **"사용자 인증 정보"**
2. 상단 "+ 사용자 인증 정보 만들기" 클릭
3. **"OAuth 클라이언트 ID"** 선택

4. 애플리케이션 유형:
   - ✅ **"데스크톱 앱"** 선택
   - 이름: `Email Classifier CLI` (또는 원하는 이름)
5. "만들기" 클릭

6. **OAuth 클라이언트 생성됨** 창이 뜸:
   - **"JSON 다운로드"** 버튼 클릭 ⬇️
   - 파일이 Downloads 폴더에 저장됨
   - 파일명: `client_secret_xxxxx.json`

---

### Step 6: credentials.json 파일 배치

#### 방법 1: 터미널에서 복사

```bash
# 다운로드 폴더에서 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json

# 파일 확인
ls -l /home/kyuwon/projects/email_agent/credentials.json
```

**예상 출력**:
```
-rw-r--r--. 1 kyuwon kyuwon 582 Nov 13 10:30 /home/kyuwon/projects/email_agent/credentials.json
```

#### 방법 2: 수동으로 복사

1. Finder/파일 탐색기에서 Downloads 폴더 열기
2. `client_secret_xxxxx.json` 파일 찾기
3. `/home/kyuwon/projects/email_agent/` 폴더로 복사
4. 파일명을 `credentials.json`으로 변경

---

## ✅ 설정 완료 확인

```bash
cd /home/kyuwon/projects/email_agent

# 파일이 있는지 확인
ls -l credentials.json

# 파일 내용 확인 (client_id가 보여야 함)
head -5 credentials.json
```

**예상 출력**:
```json
{
  "installed": {
    "client_id": "xxxxx.apps.googleusercontent.com",
    "project_id": "email-classifier-xxxxx",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    ...
}
```

---

## 🎯 다음 단계

이제 프로그램을 실행할 수 있습니다!

```bash
email-classify
```

**첫 실행 시**:
1. 브라우저가 자동으로 열림
2. Google 계정 선택
3. ⚠️ "Google에서 확인되지 않음" 경고 표시:
   - **"고급"** 클릭
   - **"Email Classifier(안전하지 않음)로 이동"** 클릭
4. 권한 승인:
   - Gmail 읽기 권한 ✓
   - Gmail 초안 작성 권한 ✓
5. "계속" 클릭
6. `token.json` 파일 자동 생성
7. 프로그램 실행 시작!

---

## 🐛 문제 해결

### 문제 1: "credentials.json not found"

**확인사항**:
```bash
# 파일 위치 확인
ls /home/kyuwon/projects/email_agent/credentials.json

# 파일명 확인 (정확히 credentials.json이어야 함)
ls /home/kyuwon/projects/email_agent/client_secret_*.json
```

**해결**:
```bash
# 다운로드 폴더에서 다시 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

---

### 문제 2: "Error 403: access_denied"

**원인**: OAuth 동의 화면에서 테스트 사용자를 추가하지 않음

**해결**:
1. Google Cloud Console → OAuth 동의 화면
2. "테스트 사용자" 섹션 → "+ ADD USERS"
3. 본인 Gmail 주소 추가
4. `token.json` 삭제 후 재시도:
   ```bash
   rm /home/kyuwon/projects/email_agent/token.json
   email-classify
   ```

---

### 문제 3: "insufficient permissions" 에러

**원인**: OAuth 범위(scope)가 제대로 설정되지 않음

**확인**:
1. Google Cloud Console → OAuth 동의 화면
2. "범위" 섹션 확인
3. 다음 두 개가 있어야 함:
   - `.../auth/gmail.readonly`
   - `.../auth/gmail.compose`

**해결**:
1. 없으면 "수정" 클릭 후 추가
2. `token.json` 삭제:
   ```bash
   rm /home/kyuwon/projects/email_agent/token.json
   ```
3. 다시 실행:
   ```bash
   email-classify
   ```

---

### 문제 4: 브라우저가 안 열림

**수동 인증**:
1. 터미널에 출력된 URL 복사
2. 브라우저에 수동으로 붙여넣기
3. 인증 진행

---

### 문제 5: "Google에서 확인되지 않음" 경고

**이건 정상입니다!**

개인 프로젝트이므로 Google 검증을 받지 않았습니다.

**안전하게 진행하는 방법**:
1. "고급" 클릭
2. "Email Classifier(안전하지 않음)로 이동" 클릭
3. 권한 승인

**참고**: 본인이 만든 앱이므로 안전합니다.

---

## 📝 요약

1. ✅ Google Cloud Console 접속
2. ✅ 프로젝트 생성
3. ✅ Gmail API 활성화
4. ✅ OAuth 동의 화면 구성 (테스트 사용자 추가!)
5. ✅ OAuth 클라이언트 ID 생성
6. ✅ JSON 다운로드
7. ✅ `credentials.json`로 복사

**완료!** 이제 실행하세요:

```bash
email-classify
```

---

## 🔒 보안 참고사항

- `credentials.json`은 public하게 공유하지 마세요
- `.gitignore`에 이미 포함되어 있음
- `token.json`도 자동으로 무시됨
- 본인의 Gmail만 접근 가능
- 읽기 + 초안 작성 권한만 (이메일 삭제 불가)

---

**설정 완료!** 질문이 있으면 에러 메시지와 함께 알려주세요.
