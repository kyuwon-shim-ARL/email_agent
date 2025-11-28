# Claude Code 통합 가이드

**Email Agent를 Claude Code 환경에서 최대한 활용하는 방법**

## 📂 Claude Code 파일 구조

이 프로젝트는 Claude Code와 완벽하게 통합되도록 설계되었습니다:

```
email_agent/
├── .claude/
│   ├── skills/
│   │   └── classify-emails.md    # 자동 이메일 분류 스킬
│   └── commands/
│       └── classify.md            # /classify 슬래시 커맨드
├── email_classifier/              # 핵심 코드
└── docs/                         # 문서
```

## 🎯 Claude Code 스킬 사용법

### 스킬 자동 인식

프로젝트를 클론하면 Claude Code가 자동으로 스킬을 인식합니다:

```bash
git clone https://github.com/kyuwon-shim-ARL/email_agent.git
cd email_agent

# Claude Code에서 이 디렉토리 열기
```

이제 Claude Code와 대화할 때:

```
사용자: "내 이메일 분류해줘"
사용자: "최근 이메일 확인하고 초안 작성해줘"
사용자: "20개 이메일 처리하고 답장 생성해줘"
```

Claude Code가 자동으로 **classify-emails 스킬**을 실행합니다!

### 슬래시 커맨드 사용

```
/classify
```

빠르게 이메일 분류 프로세스를 시작할 수 있습니다.

## 🔧 스킬 커스터마이징

### 1. 이메일 개수 조정

`.claude/skills/classify-emails.md` 파일 수정:

```markdown
## Usage

User can say:
- "Classify my emails"
- "Check my recent **50** emails and create drafts"  # 기본값 변경
```

### 2. 우선순위 기준 조정

스킬 파일에 우선순위 가이드라인 추가:

```markdown
## Priority Guidelines

- Priority 5: VIP contacts (>50 exchanges)
- Priority 4: Frequent contacts (20-50 exchanges)
- Priority 3: Known contacts (5-20 exchanges)
- Priority 2: Occasional (1-5 exchanges)
- Priority 1: First contact or automated
```

### 3. 발신자별 스타일 설정

특정 발신자에 대한 스타일을 미리 정의:

```markdown
## Predefined Sender Styles

- manager@company.com: Very formal, respectful
- team@company.com: Professional but friendly
- friends@gmail.com: Casual, use emojis
```

## 🚀 워크플로우 자동화

### Spec-Kit 스타일 프로젝트 구조 (선택)

더 고급 사용을 위해 spec-kit 구조 추가 가능:

```bash
mkdir -p .claude/spec
```

`.claude/spec/email-processing.md` 생성:

```markdown
# Email Processing Specification

## Objective
Automatically classify emails and generate personalized draft replies.

## Requirements
1. Learn user's writing style from sent emails
2. Classify recent emails by urgency
3. Generate sender-specific draft replies
4. Maintain conversation context

## Deliverables
1. Classification results with priority ranking
2. Personalized draft replies in Gmail
3. Processing summary report

## Success Criteria
- 95%+ classification accuracy
- Drafts match user's tone
- Processing time < 5 minutes
```

### 자동 실행 설정

`.claude/commands/auto-classify.md`:

```markdown
# Auto Classify Daily Emails

Run this command every morning:

```bash
#!/bin/bash
cd /path/to/email_agent
source .venv/bin/activate
email-classify --auto
```

Schedule with cron:
```bash
0 9 * * * /path/to/email_agent/auto-classify.sh
```
```

## 📖 스킬 재사용 가이드

### 다른 프로젝트에서 이 스킬 재사용

1. **스킬 파일 복사:**
   ```bash
   cp email_agent/.claude/skills/classify-emails.md \
      my_project/.claude/skills/
   ```

2. **의존성 설치:**
   ```bash
   cd my_project
   pip install -e /path/to/email_agent
   ```

3. **스킬 수정:**
   프로젝트에 맞게 `.claude/skills/classify-emails.md` 내용 조정

### 스킬을 라이브러리로 사용

```python
# my_project/process_emails.py
from email_classifier.gmail_client import GmailClient
from email_classifier.claude_code_classifier import ClaudeCodeClassifier

def custom_email_workflow():
    gmail = GmailClient()
    classifier = ClaudeCodeClassifier()

    # 커스텀 로직
    emails = gmail.get_recent_emails(max_results=50)
    # ...
```

## 🎨 Claude Code 최적화 팁

### 1. 컨텍스트 효율성

큰 이메일 배치 처리 시:

```python
# 배치 크기 조정
emails = gmail.get_recent_emails(max_results=10)  # 작게 시작

# 증분 처리
for batch in chunks(emails, 5):
    process_batch(batch)
```

### 2. 프롬프트 재사용

자주 쓰는 프롬프트를 파일로 저장:

```bash
.claude/prompts/
├── style-analysis.txt
├── classification.txt
└── draft-generation.txt
```

### 3. 결과 캐싱

발신자 스타일을 캐시:

```python
# ~/.email_agent_cache/sender_styles.json
{
  "manager@company.com": {
    "greeting": "안녕하세요,",
    "closing": "감사합니다,",
    "formality": "formal"
  }
}
```

## 🔄 업데이트 워크플로우

프로젝트가 업데이트되면:

```bash
cd email_agent
git pull origin main

# 스킬 자동 업데이트 확인
git diff .claude/skills/classify-emails.md

# 필요시 스킬 재설치
pip install -e . --upgrade
```

## 📊 Claude Code 성능 모니터링

### 처리 시간 측정

`.claude/skills/classify-emails.md`에 추가:

```markdown
## Performance Metrics

Track:
- Style learning: ~30 seconds
- Email fetching: ~10 seconds
- Classification: ~30 seconds per 10 emails
- Draft generation: ~20 seconds per draft
- Total: ~2-3 minutes for 10 emails
```

### 오류 로깅

```python
# email_classifier/logger.py
import logging

logging.basicConfig(
    filename='.claude/logs/classifier.log',
    level=logging.INFO
)
```

## 🆘 문제 해결

### 스킬이 인식되지 않음

1. `.claude/skills/` 폴더 확인:
   ```bash
   ls -la .claude/skills/
   ```

2. Claude Code 재시작

3. 스킬 파일 형식 확인 (Markdown)

### 커맨드가 작동하지 않음

1. `.claude/commands/` 폴더 확인
2. 파일명이 `.md`로 끝나는지 확인
3. 슬래시 커맨드 이름 확인 (`/classify`)

## 🎓 고급 활용

### MCP (Model Context Protocol) 통합

향후 Claude Code MCP 지원 시:

```json
// .claude/mcp.json
{
  "tools": [
    {
      "name": "email-classifier",
      "command": "email-classify",
      "description": "Classify Gmail emails and generate drafts"
    }
  ]
}
```

### 커스텀 플러그인

```python
# .claude/plugins/email_notifier.py
def on_classification_complete(results):
    # Slack 알림
    # Desktop 알림
    pass
```

## 📚 참고 자료

- [Claude Code Skills 문서](https://docs.claude.ai/skills)
- [Spec-Kit 가이드](https://github.com/anthropics/spec-kit)
- Email Agent [README.md](../README.md)

---

**Claude Code와 완벽하게 통합된 Email Agent를 즐기세요!** 🚀
