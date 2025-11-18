# 테스트 실행 가이드

## 🎯 목표
Gmail 이메일을 자동 분류하고 답장 초안을 Gmail 초안함에 생성하는 도구를 테스트합니다.

---

## ⏱️ 예상 소요 시간
- **최초 설정**: 10-15분
- **실행 및 결과 확인**: 2-5분
- **총**: 15-20분

---

## 📋 체크리스트

### Step 1: Claude API Key 설정 (3분)

```bash
cd /home/kyuwon/projects/email_agent

# .env 파일 생성
cp .env.example .env
```

그 다음 `.env` 파일을 편집하여 Claude API Key를 입력하세요:

```bash
# 방법 1: nano 편집기 사용
nano .env

# 방법 2: vim 사용
vim .env

# 방법 3: 직접 echo 사용 (API 키를 알고 있는 경우)
echo "CLAUDE_API_KEY=sk-ant-your-actual-key-here" > .env
```

**Claude API Key 받는 방법**:
1. https://console.anthropic.com/ 접속
2. 로그인
3. API Keys 메뉴
4. "Create Key" 클릭
5. 생성된 키 복사

---

### Step 2: Google Cloud Console 설정 (10분)

**2.1 프로젝트 생성**
1. https://console.cloud.google.com/ 접속
2. 상단 프로젝트 선택 → "새 프로젝트" 클릭
3. 프로젝트 이름: "email-classifier" 입력
4. "만들기" 클릭

**2.2 Gmail API 활성화**
1. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
2. 검색창에 "Gmail API" 입력
3. "Gmail API" 선택 → "사용" 클릭

**2.3 OAuth 동의 화면 구성**
1. 좌측 메뉴 → "API 및 서비스" → "OAuth 동의 화면"
2. User Type: "외부" 선택 → "만들기"
3. 앱 정보:
   - 앱 이름: "Email Classifier"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
4. "저장 후 계속" 클릭
5. 범위 추가:
   - ".../auth/gmail.readonly" 추가
   - ".../auth/gmail.compose" 추가
6. "저장 후 계속" 클릭
7. 테스트 사용자 추가: 본인 Gmail 주소 입력
8. "저장 후 계속" 클릭

**2.4 OAuth 2.0 클라이언트 ID 생성**
1. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
2. 상단 "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: "데스크톱 앱" 선택
4. 이름: "Email Classifier CLI" 입력
5. "만들기" 클릭
6. **JSON 다운로드** 버튼 클릭 (중요!)

**2.5 credentials.json 배치**
```bash
# 다운로드 폴더에서 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json

# 또는 직접 다운로드 위치 지정
cp /path/to/downloaded/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json

# 파일이 있는지 확인
ls -l /home/kyuwon/projects/email_agent/credentials.json
```

---

### Step 3: 첫 실행 (2분)

```bash
cd /home/kyuwon/projects/email_agent

# 스타일 학습 포함 버전 실행
/home/kyuwon/.venv/bin/email-classify
```

**예상 동작**:
1. ✅ "📧 Connecting to Gmail..." 메시지 표시
2. ✅ 브라우저가 자동으로 열림
3. ✅ Google 계정 선택 화면
4. ✅ "Google에서 확인되지 않음" 경고 → **"고급" 클릭 → "이메일 분류기(안전하지 않음)로 이동" 클릭**
5. ✅ 권한 요청 화면:
   - Gmail 이메일 읽기 권한
   - Gmail 초안 작성 권한
6. ✅ "계속" 클릭
7. ✅ "인증에 성공했습니다" 메시지
8. ✅ 브라우저 탭 닫고 터미널로 돌아오기
9. ✅ `token.json` 파일 자동 생성
10. ✅ 프로그램 실행 시작

**진행 과정**:
```
✍️  Learning your writing style from sent emails...
   → Analyzed 30 sent emails
   → Detected style: formal
   → Typical greeting: 'Hi,'
   → Typical closing: 'Best regards,'

📬 Fetching recent emails...

🤖 Analyzing emails and generating draft replies...

  [1/10] 이메일 제목 1...
  [2/10] 이메일 제목 2...
  ...
```

---

### Step 4: 결과 확인 (3분)

**4.1 터미널 출력 확인**

```
================================================================================
🔴 NEEDS RESPONSE (3 emails)
================================================================================

1. 회의 일정 확인 부탁드립니다
   From: colleague@company.com
   Confidence: 95%
   Reason: Direct question requiring response
   ✅ Draft reply created (tone: formal)

2. 프로젝트 진행 상황 공유
   From: team@company.com
   Confidence: 85%
   Reason: Team update likely needs acknowledgment
   ✅ Draft reply created (tone: casual)

================================================================================
✅ NO RESPONSE NEEDED (7 emails)
================================================================================

1. GitHub Notification: PR merged
   From: notifications@github.com
   Confidence: 99%
   Reason: Automated notification

================================================================================
✨ Classification complete!

📝 Created 3 draft replies in Gmail!
   → Check your Gmail Drafts folder to review and send them.
```

**4.2 Gmail 초안함 확인**

1. Gmail 웹 접속: https://mail.google.com/
2. 좌측 메뉴에서 **"초안"** 클릭
3. 생성된 초안 확인:
   - ✅ 개수가 터미널 출력과 일치하는지
   - ✅ 각 초안이 원본 이메일 스레드에 연결되어 있는지
   - ✅ "받는사람" 필드가 올바른지
   - ✅ 제목이 "Re: [원본 제목]" 형식인지
   - ✅ 본문 내용이 자연스러운지
   - ✅ 본인의 평소 말투와 비슷한지

**4.3 초안 검토 및 전송**

1. 초안 하나를 열어보기
2. 내용 확인 및 필요시 수정
3. "보내기" 클릭 (또는 삭제)

---

## 🧪 추가 테스트: 스타일 학습 비교

스타일 학습이 실제로 효과가 있는지 확인하려면:

```bash
# 1. 스타일 학습 없는 버전 실행
/home/kyuwon/.venv/bin/email-classify-simple

# 2. 생성된 초안을 Gmail에서 확인
# 3. 스타일 학습 버전과 비교
```

**비교 포인트**:
- 인사말 (Hi vs 안녕하세요 등)
- 맺음말 (Best vs 감사합니다 등)
- 문장 톤 (격식 vs 캐주얼)
- 전반적인 자연스러움

---

## ❌ 문제 해결

### 문제 1: "credentials.json not found"
```bash
# 파일이 올바른 위치에 있는지 확인
ls -l /home/kyuwon/projects/email_agent/credentials.json

# 없다면 다시 다운로드하여 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

### 문제 2: "CLAUDE_API_KEY not found"
```bash
# .env 파일 확인
cat /home/kyuwon/projects/email_agent/.env

# 없거나 비어있다면 다시 설정
echo "CLAUDE_API_KEY=sk-ant-your-key" > /home/kyuwon/projects/email_agent/.env
```

### 문제 3: 권한 에러 (insufficient permissions)
**원인**: OAuth 스코프 설정 누락

**해결**:
1. Google Cloud Console → OAuth 동의 화면 → 범위 확인
2. 다음 두 개가 있어야 함:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
3. 없다면 추가
4. `token.json` 삭제 후 재인증:
```bash
rm /home/kyuwon/projects/email_agent/token.json
/home/kyuwon/.venv/bin/email-classify
```

### 문제 4: 브라우저가 안 열림
터미널에 출력된 URL을 복사하여 수동으로 브라우저에 붙여넣기

### 문제 5: 초안이 Gmail에 안 보임
1. Gmail 새로고침 (F5)
2. "모든 초안" 탭 확인 (일부만 표시될 수 있음)
3. 터미널 출력에서 에러 메시지 확인

### 문제 6: "No sent emails found for style analysis"
**원인**: 발신 이메일이 없거나 너무 적음

**해결**:
- 스타일 학습 없는 버전 사용: `email-classify-simple`
- 또는 Gmail에서 이메일 몇 개 보낸 후 재시도

---

## 📊 성공 기준

테스트가 성공적이려면:

✅ **기능 동작**
- [ ] OAuth 인증 성공
- [ ] 이메일 10개 가져오기 성공
- [ ] 분류 결과 표시됨 (응답 필요 vs 불필요)
- [ ] 신뢰도 점수와 이유가 표시됨
- [ ] 초안이 Gmail 초안함에 생성됨

✅ **품질**
- [ ] 분류 정확도 >80% (직관적으로 맞다고 느껴짐)
- [ ] 초안 내용이 자연스러움
- [ ] 초안이 본인 스타일과 유사함
- [ ] 초안 수정이 최소한 (<2분)

✅ **성능**
- [ ] 전체 실행 시간 <2분 (10개 이메일 기준)
- [ ] 에러 없이 완료

---

## 📝 테스트 후 피드백

테스트 완료 후 다음을 알려주세요:

1. **성공 여부**:
   - 모든 단계가 성공했는지?
   - 어디서 막혔는지?

2. **분류 정확도**:
   - 응답 필요/불필요 분류가 맞았는지?
   - 틀린 것이 있다면 어떤 이메일?

3. **초안 품질**:
   - 초안이 자연스러웠는지?
   - 본인 스타일과 비슷했는지?
   - 수정이 많이 필요했는지?

4. **스타일 학습 효과**:
   - `email-classify`와 `email-classify-simple` 비교 시 차이가 느껴졌는지?

5. **개선 사항**:
   - 어떤 기능이 필요한지?
   - 어떤 부분이 불편했는지?

---

## 🔄 두 번째 실행부터

첫 실행 후에는 훨씬 빠릅니다:

```bash
# OAuth 인증 없이 바로 실행 (token.json 재사용)
/home/kyuwon/.venv/bin/email-classify
```

**소요 시간**: 30초 ~ 1분 (스타일 학습 포함)

---

## 🎯 다음 단계

테스트 성공 후:

1. **만족하면**: 그대로 사용 (필요할 때마다 실행)
2. **개선 필요하면**: 피드백 주시면 수정
3. **추가 기능 원하면**: 다음 기능 제안:
   - 스타일 캐싱 (매번 재분석 안 함)
   - 이메일 개수 조정 (10개 → 20개)
   - 특정 발신자만 필터링
   - 스케줄 자동 실행

---

**준비 완료!** 위 단계를 따라 테스트해보세요. 문제가 생기면 에러 메시지와 함께 알려주세요.
