# Quick Start Guide

## ✅ 설치 완료!

패키지가 성공적으로 설치되었습니다.

## 🚀 실행 방법

### 스타일 학습 포함 버전 (권장)
```bash
cd /home/kyuwon/projects/email_agent
/home/kyuwon/.venv/bin/email-classify
```

### 스타일 학습 없는 버전 (비교 테스트용)
```bash
cd /home/kyuwon/projects/email_agent
/home/kyuwon/.venv/bin/email-classify-simple
```

## 📋 실행 전 확인사항

### 1. Claude API Key 설정
```bash
cd /home/kyuwon/projects/email_agent
cp .env.example .env
# .env 파일 편집하여 CLAUDE_API_KEY 입력
```

### 2. Google Cloud Console 설정
1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
3. **Gmail API 활성화**
4. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
5. **권한 범위 확인**:
   - ✅ `https://www.googleapis.com/auth/gmail.readonly`
   - ✅ `https://www.googleapis.com/auth/gmail.compose`
6. `credentials.json` 다운로드
7. 다운로드한 파일을 `/home/kyuwon/projects/email_agent/credentials.json`으로 복사

### 3. 첫 실행
```bash
/home/kyuwon/.venv/bin/email-classify
```

**예상 동작**:
1. 브라우저 자동 실행 (Google OAuth)
2. Gmail 계정 선택
3. 권한 승인 (읽기 + 초안 작성)
4. `token.json` 자동 생성
5. 프로그램 실행 시작

## 📊 실행 결과 확인

프로그램이 다음 작업을 수행합니다:

1. ✍️ **스타일 학습** (최대 30개 발신 이메일 분석)
   - 인사말 패턴 추출
   - 맺음말 스타일 파악
   - 격식 수준 판단
   - 자주 쓰는 표현 추출

2. 📬 **최근 이메일 10개 가져오기**

3. 🤖 **각 이메일 분석 및 분류**
   - 응답 필요 vs 응답 불필요
   - 신뢰도 점수
   - 분류 이유

4. ✨ **자동 초안 생성**
   - 학습한 사용자 스타일 적용
   - Gmail 초안함에 자동 저장

5. 📝 **결과 출력**
   - 응답 필요한 이메일 목록
   - 응답 불필요한 이메일 목록
   - 생성된 초안 개수

## 🔍 Gmail에서 확인

1. Gmail 웹/앱 접속
2. **초안함(Drafts)** 열기
3. 생성된 초안 확인
4. 내용 검토 후 전송

## 🐛 문제 해결

### "credentials.json not found"
```bash
# Google Cloud Console에서 다운로드한 파일 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

### "CLAUDE_API_KEY not found"
```bash
cd /home/kyuwon/projects/email_agent
echo "CLAUDE_API_KEY=your_api_key_here" > .env
```

### 권한 에러
```bash
# token.json 삭제 후 재인증
rm /home/kyuwon/projects/email_agent/token.json
/home/kyuwon/.venv/bin/email-classify
```

## 📖 자세한 테스트 가이드

전체 테스트 체크리스트는 `TEST_CHECKLIST.md` 참조
