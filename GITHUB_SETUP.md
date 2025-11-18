# GitHub 저장소 설정 가이드

**Email Agent를 GitHub에 배포하는 방법**

## 📋 사전 준비

- GitHub 계정
- Git 설치됨
- email_agent 로컬 저장소 (이미 완료!)

## 🚀 GitHub 저장소 생성 및 푸시

### 1. GitHub에서 새 저장소 생성

1. https://github.com 접속 및 로그인
2. 우측 상단 "+" → "New repository" 클릭
3. 저장소 정보 입력:
   - **Repository name**: `email-agent`
   - **Description**: `Gmail email classifier with Claude Code - Zero API costs, sender-specific styles, priority ranking`
   - **Visibility**: Public (또는 Private)
   - ⚠️ **중요**: "Add a README file" 체크 **해제**
   - ⚠️ **중요**: "Add .gitignore" 선택 **하지 말기**
4. "Create repository" 클릭

### 2. 로컬 저장소와 GitHub 연결

```bash
cd /home/kyuwon/projects/email_agent

# GitHub 저장소와 연결 (YOUR_USERNAME 수정!)
git remote add origin https://github.com/YOUR_USERNAME/email-agent.git

# 기본 브랜치를 main으로 변경 (권장)
git branch -M main

# 첫 푸시
git push -u origin main
```

**GitHub 인증 필요 시:**

```bash
# Personal Access Token 사용 (권장)
# 1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 2. "Generate new token" → repo 권한 체크 → 생성
# 3. 토큰 복사 (한 번만 표시됨!)
# 4. push 시 비밀번호 대신 토큰 입력
```

### 3. 푸시 확인

브라우저에서 `https://github.com/YOUR_USERNAME/email-agent` 접속하여 확인

## 📝 저장소 설명 추가 (권장)

### README.md 배지 추가

README.md 상단에 배지를 추가하면 전문적으로 보입니다:

```markdown
# Email Agent - Claude Code 이메일 자동 분류기

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-orange.svg)

**비용 없이 Claude Code와 대화하며 Gmail 이메일을 자동 분류하고 답장 초안을 생성하는 도구**
```

### About 섹션 설정

1. GitHub 저장소 페이지에서 우측 상단 ⚙️ (Settings) 클릭
2. "About" 섹션 편집:
   - **Description**: `Gmail email classifier with Claude Code integration - Zero API costs`
   - **Website**: (있으면 입력)
   - **Topics** (태그) 추가:
     - `gmail`
     - `email-automation`
     - `claude-ai`
     - `claude-code`
     - `python`
     - `oauth2`
     - `email-classifier`
3. "Save changes"

## 📄 LICENSE 추가 (권장)

```bash
cd /home/kyuwon/projects/email_agent

# MIT 라이선스 생성
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 커밋 및 푸시
git add LICENSE
git commit -m "docs: Add MIT license"
git push
```

## 🎨 GitHub Actions 설정 (선택 사항)

자동 테스트를 위한 CI/CD 설정:

```bash
mkdir -p .github/workflows

cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 email_classifier --count --select=E9,F63,F7,F82 --show-source --statistics
EOF

git add .github/
git commit -m "ci: Add GitHub Actions workflow"
git push
```

## 📢 사용자에게 공유하기

### 설치 명령어 (한 줄)

```bash
git clone https://github.com/YOUR_USERNAME/email-agent.git && cd email-agent && python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

### README에 추가할 빠른 시작

```markdown
## 빠른 설치

```bash
# 클론 및 설치
git clone https://github.com/YOUR_USERNAME/email-agent.git
cd email-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Gmail API 설정 (INSTALLATION.md 참조)
cp ~/Downloads/client_secret_*.json ./credentials.json

# 실행!
email-classify
```

상세한 설치 가이드는 [INSTALLATION.md](INSTALLATION.md)를 참조하세요.
```

## 🔄 업데이트 배포 프로세스

코드를 수정한 후:

```bash
# 변경사항 스테이징
git add .

# 커밋 (의미 있는 메시지)
git commit -m "feat: Add new feature description"

# 푸시
git push origin main
```

**커밋 메시지 컨벤션:**
- `feat:` - 새 기능
- `fix:` - 버그 수정
- `docs:` - 문서 변경
- `refactor:` - 코드 리팩토링
- `test:` - 테스트 추가/수정
- `chore:` - 빌드/설정 변경

## 🏷️ 릴리스 버전 관리

안정적인 버전을 태그로 표시:

```bash
# 버전 태그 생성
git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release"

# 태그 푸시
git push origin v1.0.0

# 모든 태그 푸시
git push --tags
```

GitHub에서 Release 생성:
1. 저장소 → "Releases" → "Create a new release"
2. Tag 선택: `v1.0.0`
3. Release title: `v1.0.0 - Initial Release`
4. 변경사항 설명 작성
5. "Publish release"

## 🔐 보안 체크리스트

배포 전 확인:

- ✅ `.gitignore`에 `credentials.json` 포함됨
- ✅ `.gitignore`에 `token.json` 포함됨
- ✅ `.gitignore`에 `.env` 포함됨
- ✅ 실제 credentials.json이 커밋되지 않음
- ✅ 하드코딩된 API 키 없음

확인 명령어:

```bash
# 커밋된 파일 중 민감한 정보 검색
git log --all --full-history -- credentials.json
git log --all --full-history -- token.json

# 아무것도 나오지 않으면 OK!
```

## 📊 저장소 관리 팁

### Issue 템플릿 생성

```bash
mkdir -p .github/ISSUE_TEMPLATE

cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Report a bug
title: '[BUG] '
labels: bug
---

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.0]
- Email Agent version: [e.g., v1.0.0]
EOF
```

### Pull Request 템플릿

```bash
cat > .github/PULL_REQUEST_TEMPLATE.md << 'EOF'
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Tests added/updated (if applicable)
EOF
```

## 🎉 완료!

이제 다른 사용자들이:

```bash
git clone https://github.com/YOUR_USERNAME/email-agent.git
```

으로 간단히 설치할 수 있습니다!

## 다음 단계

1. **GitHub 저장소 URL을 README.md에 추가**
2. **소셜 미디어에 공유** (선택)
3. **사용자 피드백 수집**
4. **Issues로 버그 트래킹**

---

**배포 완료!** 🚀
