# 테스트 체크리스트

## ✅ 사전 준비

### Claude API
- [ ] https://console.anthropic.com/ 에서 API Key 생성
- [ ] `.env` 파일 생성하고 `CLAUDE_API_KEY` 입력
  ```bash
  cp .env.example .env
  # .env 파일 편집
  ```

### Google Cloud Console
- [ ] https://console.cloud.google.com/ 접속
- [ ] 새 프로젝트 생성
- [ ] Gmail API 활성화
- [ ] OAuth 2.0 클라이언트 ID 생성 (Desktop app)
- [ ] **중요**: 권한 범위 설정
  - ✅ `https://www.googleapis.com/auth/gmail.readonly` (이메일 읽기)
  - ✅ `https://www.googleapis.com/auth/gmail.compose` (초안 작성)
- [ ] `credentials.json` 다운로드 → `email_agent/` 디렉토리에 복사

---

## 🧪 기능 테스트

### Phase 1: 기본 연결 테스트

```bash
cd /home/kyuwon/projects/email_agent
email-classify
```

**예상 동작**:
1. [ ] 브라우저가 자동으로 열림 (Google OAuth)
2. [ ] Gmail 계정 선택 화면
3. [ ] 권한 요청 화면:
   - [ ] "Gmail 읽기 권한" 요청
   - [ ] "Gmail 초안 작성 권한" 요청
4. [ ] 권한 승인 후 `token.json` 자동 생성
5. [ ] 터미널로 돌아와서 프로그램 실행 계속

**체크포인트**:
- [ ] OAuth 인증 성공
- [ ] `token.json` 파일 생성됨
- [ ] 에러 없이 진행

---

### Phase 2: 스타일 학습 테스트

**예상 출력**:
```
✍️  Learning your writing style from sent emails...
   → Analyzed [N] sent emails
   → Detected style: [formal/casual/neutral]
   → Typical greeting: '[인사말]'
   → Typical closing: '[맺음말]'
```

**체크포인트**:
- [ ] 발신 이메일 가져오기 성공
- [ ] 스타일 분석 완료
- [ ] 인사말/맺음말 추출됨
- [ ] 결과가 실제 작성 스타일과 일치하는지 확인

**참고**: 발신 이메일이 30개 미만이면 더 적은 수로 분석됨

---

### Phase 3: 이메일 분류 테스트

**예상 출력**:
```
📬 Fetching recent emails...
🤖 Analyzing emails and generating draft replies...

  [1/10] [이메일 제목]...
  [2/10] [이메일 제목]...
  ...
```

**체크포인트**:
- [ ] 최근 이메일 10개 가져오기 성공
- [ ] 각 이메일 처리 중 표시
- [ ] 에러 없이 진행

---

### Phase 4: 초안 생성 및 저장 테스트

**예상 출력**:
```
================================================================================
🔴 NEEDS RESPONSE (N emails)
================================================================================

1. [이메일 제목]
   From: [발신자]
   Confidence: XX%
   Reason: [분류 이유]
   ✅ Draft reply created (tone: formal/casual)
```

**체크포인트**:
- [ ] "응답 필요" 이메일 정확히 분류됨
- [ ] 각 이메일에 초안 생성됨 (✅ 표시)
- [ ] 초안 생성 실패 시 ⚠️ 표시

**최종 출력**:
```
📝 Created [N] draft replies in Gmail!
   → Check your Gmail Drafts folder to review and send them.
```

- [ ] 생성된 초안 개수 표시

---

### Phase 5: Gmail 초안함 확인

**Gmail 웹/앱에서**:
1. [ ] Gmail 접속
2. [ ] 초안함(Drafts) 열기
3. [ ] 생성된 초안 확인
4. [ ] 초안 내용 검토:
   - [ ] 원본 이메일에 대한 답장인지 확인
   - [ ] 쓰레드(대화)에 연결되어 있는지 확인
   - [ ] 수신자가 정확한지 확인
   - [ ] 제목이 "Re: [원본 제목]" 형식인지 확인
   - [ ] 본문이 자연스러운지 확인
   - [ ] **학습한 스타일(인사/맺음)이 반영되었는지 확인**

---

## 🐛 문제 해결

### 문제 1: "credentials.json not found"
**해결**:
```bash
# Google Cloud Console에서 다운로드한 파일을 복사
cp ~/Downloads/client_secret_*.json /home/kyuwon/projects/email_agent/credentials.json
```

### 문제 2: "CLAUDE_API_KEY not found"
**해결**:
```bash
cd /home/kyuwon/projects/email_agent
echo "CLAUDE_API_KEY=your_key_here" > .env
```

### 문제 3: 권한 에러
**해결**:
- Google Cloud Console에서 OAuth 범위 확인
- `token.json` 삭제 후 재인증
  ```bash
  rm token.json
  email-classify
  ```

### 문제 4: 초안이 Gmail에 안 보임
**원인**: 권한 부족
**해결**:
1. `token.json` 삭제
2. OAuth 재인증 시 "초안 작성 권한" 확인
3. 다시 실행

---

## 📊 테스트 결과 보고

### 성공 기준
- [x] OAuth 인증 성공
- [x] 스타일 학습 완료 (발신 이메일 분석)
- [x] 이메일 분류 정확도 > 80%
- [x] 초안 자동 생성 성공
- [x] Gmail 초안함에 저장 확인
- [x] 초안 내용이 자연스러움

### 발견된 문제

1. **문제**: [문제 설명]
   **심각도**: 높음/중간/낮음
   **재현 방법**: [단계]

2. **문제**: [문제 설명]
   ...

### 개선 제안

1. [제안 1]
2. [제안 2]
...

---

## 🎯 다음 단계

테스트 완료 후:
- [ ] 스타일 학습 기능 비활성화 버전 테스트 (속도 비교)
- [ ] 더 많은 이메일로 테스트 (10개 → 20개)
- [ ] 다른 Gmail 계정으로 테스트
- [ ] 스타일 캐싱 추가 (JSON 파일 저장)

---

## 📝 참고사항

- 첫 실행은 OAuth + 스타일 학습으로 시간이 걸림 (2-3분)
- 두 번째부터는 `token.json` 재사용으로 빠름 (30초-1분)
- 발신 이메일이 많을수록 스타일 학습 정확도 향상
- 초안은 자동 전송 안 됨 (항상 검토 후 수동 전송)
