# 시작하기 (Claude Code 사용자용)

## 무엇을 하는 도구인가요?

Gmail 이메일을 Claude Code와 대화하며 자동으로:
1. 응답 필요한 이메일 찾기
2. 내 작성 스타일 학습
3. 답장 초안 자동 생성

**비용 $0** (Claude Code 대화로 처리)

## 1분 요약

```bash
# 1. 설치
cd email_agent
pip install -e .

# 2. Gmail API 설정 (최초 1회)
# https://console.cloud.google.com 에서:
# - Gmail API 활성화
# - OAuth 클라이언트 ID 생성
# - credentials.json 다운로드
cp ~/Downloads/client_secret_*.json ./credentials.json

# 3. 실행
email-classify
```

그 후 Claude Code와 대화하며 진행!

## 어떻게 동작하나요?

프로그램이 프롬프트 파일을 생성하면:
1. 파일 내용을 `cat` 명령으로 확인
2. Claude Code에 복사-붙여넣기
3. Claude의 JSON 응답을 복사
4. 터미널에 붙여넣기

**3번 반복** (스타일 학습 → 분류 → 초안 생성)

## 예시 대화

```
$ email-classify

✅ Style analysis prompt ready!
   File: /tmp/email_classifier/analyze_style.txt

ACTION REQUIRED:
1. Open file: cat /tmp/email_classifier/analyze_style.txt
```

**여러분이 할 일:**
```bash
cat /tmp/email_classifier/analyze_style.txt
# 출력된 프롬프트를 복사해서 Claude Code에 붙여넣기
```

**Claude Code에게:**
```
Analyze my writing style from these sent emails...
[이메일 내용들...]
```

**Claude의 응답:**
```json
{
  "greeting_style": "안녕하세요,",
  "closing_style": "감사합니다,",
  "formality_level": "formal"
}
```

**터미널에 붙여넣기:**
```
📋 Paste Claude's style analysis JSON: [위 JSON 붙여넣기]

✅ Style learned!
```

## 왜 이렇게 하나요?

**일반 방식 (API 직접 호출):**
- Claude API 키 필요
- 매일 $3-9 비용 발생
- 자동화되지만 비쌈

**Claude Code 방식 (이 도구):**
- API 키 불필요
- 비용 $0
- 대화하며 진행
- 매일 사용해도 무료

## 자주 묻는 질문

### Q: 왜 3번이나 붙여넣어야 하나요?
A: 각 단계(스타일 학습, 분류, 초안 생성)가 독립적이어서 각각 Claude의 판단이 필요합니다.

### Q: JSON 부분만 복사해야 하나요?
A: 네! Claude의 설명 텍스트는 제외하고 `{...}` 또는 `[...]` 부분만 복사하세요.

### Q: 얼마나 걸리나요?
A: 전체 과정 2-3분 정도입니다.

### Q: credentials.json은 어디서 받나요?
A: Google Cloud Console → Gmail API 활성화 → OAuth 클라이언트 ID 생성
자세한 설명: `docs/SETUP_CREDENTIALS.md`

## 더 자세한 설명

- **사용 방법**: `README.md`
- **Gmail 설정**: `docs/SETUP_CREDENTIALS.md`
- **상세 가이드**: `docs/README_CLAUDE_CODE.md`
- **테스트 방법**: `docs/TEST_CHECKLIST.md`

## 지금 바로 시작

```bash
email-classify
```

그리고 Claude Code와 대화하세요!
