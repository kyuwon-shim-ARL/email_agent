# Implementation Tasks - v0.6.3 Deployment Ready

## Overview

배포 가능한 상태로 하드코딩 제거 및 CI/CD 구축.

---

## v0.6.3 Tasks (Completed)

### Task 1: Context-Based Priority System ✅

- ✅ 하드코딩된 이름/규칙 제거 (Soojin Jang 등)
- ✅ 5축 맥락 기반 판단 시스템 구현
- ✅ prioritize-email.md 스킬 파일 업데이트
- ✅ spec.md, plan.md 업데이트

### Task 2: Remove Hardcoded Paths ✅

- ✅ `/home/kyuwon/...` 경로 제거
- ✅ `~/.venv/bin/python` → `python`으로 변경
- ✅ 스프레드시트 ID → config 파일에서 로드
- ✅ 슬래시 명령어 업데이트 (email-analyze, email-draft, email-send, email-auto)

### Task 3: Cron Script Fix ✅

- ✅ `claude` 명령어 PATH 동적 탐색
- ✅ 일반적인 npm 설치 경로 추가
- ✅ 에러 핸들링 추가

### Task 4: uv Support ✅

- ✅ pyproject.toml 업데이트 (hatch build 설정)
- ✅ uv.lock 파일 생성
- ✅ README.md, INSTALL.md에 uv 사용법 추가

### Task 5: CI/CD Pipeline ✅

- ✅ `.github/workflows/check-deploy.yml` 생성
- ✅ 하드코딩 검사 자동화
- ✅ 클린 환경 설치 테스트
- ✅ `scripts/check_hardcoding.sh` 로컬 검사 스크립트

### Task 6: Documentation ✅

- ✅ README.md v0.6.3 업데이트
- ✅ CHANGELOG.md 업데이트
- ✅ 구버전 docs/ 폴더 삭제
- ✅ "업데이트 (기존 사용자)" 섹션 추가

---

## Completion Summary

| Task | Description | Status |
|------|-------------|--------|
| 1 | Context-based priority | ✅ |
| 2 | Remove hardcoded paths | ✅ |
| 3 | Cron script fix | ✅ |
| 4 | uv support | ✅ |
| 5 | CI/CD pipeline | ✅ |
| 6 | Documentation | ✅ |

---

## Key Changes

### Files Modified

```
.claude/commands/
├── email-analyze.md  # sys.path.insert(0, os.getcwd())
├── email-draft.md    # python (not ~/.venv/bin/python)
├── email-send.md     # config에서 spreadsheet ID 로드
└── email-auto.md     # 동일 패턴

.claude/skills/
└── prioritize-email.md  # 맥락 기반 판단 가이드라인

scripts/
├── daily_email_analyze.sh   # PATH 확장, command -v claude
└── check_hardcoding.sh      # 배포 전 검사 스크립트

.github/workflows/
└── check-deploy.yml  # CI 파이프라인

pyproject.toml        # hatch build, uv config
uv.lock               # 의존성 잠금
```

### Deployment Checklist

```bash
# 1. 로컬 검사
./scripts/check_hardcoding.sh

# 2. 클린 환경 테스트
cd /tmp && git clone <repo> test && cd test
uv sync
python -c "from email_classifier.gmail_client import GmailClient"

# 3. Push (CI 자동 실행)
git push
```

---

## Previous Versions

### v0.6.2 (Completed)
- Gmail 초안 자동 생성
- 16열 스키마
- HTML 제거

### v0.6.1 (Completed)
- 수신유형 기반 우선순위 조정

### v0.6.0 (Completed)
- 통합 스프레드시트 아키텍처
- 답장 여부 체크
- Cron 자동화
