#!/bin/bash
# 하드코딩 검사 스크립트
# 사용: ./scripts/check_hardcoding.sh

set -e

echo "🔍 하드코딩 검사 중..."

ERRORS=0

# 1. 사용자별 경로 검사 (실행 코드만, 문서 제외)
echo -n "  - 사용자 경로 (/home/*, /Users/*)... "
if git ls-files | xargs grep -l "/home/[a-z]" 2>/dev/null | grep -v "check_hardcoding.sh\|CHANGELOG\|tasks.md\|\.github"; then
    echo "❌ 발견"
    ERRORS=$((ERRORS + 1))
else
    echo "✅"
fi

# 2. ~/.venv 등 홈 디렉토리 참조 (실행 코드만, 문서 제외)
echo -n "  - 홈 디렉토리 참조 (~/)... "
if git ls-files | xargs grep -E "~/\.(venv|local|config)" 2>/dev/null | grep -v "check_hardcoding.sh\|CHANGELOG\|tasks.md\|\.github"; then
    echo "❌ 발견"
    ERRORS=$((ERRORS + 1))
else
    echo "✅"
fi

# 3. 하드코딩된 스프레드시트 ID (44자 영숫자)
echo -n "  - 스프레드시트 ID 하드코딩... "
if git ls-files | xargs grep -E "1[a-zA-Z0-9_-]{43}" 2>/dev/null | grep -v "example\|Example\|\.lock"; then
    echo "❌ 발견"
    ERRORS=$((ERRORS + 1))
else
    echo "✅"
fi

# 4. 실제 이메일 주소 (예시용 제외)
echo -n "  - 개인 이메일 주소... "
if git ls-files | xargs grep -E "[a-z]+@(gmail|yahoo|outlook)\.com" 2>/dev/null | grep -v "example\|Example\|your_\|test_\|TESTING"; then
    echo "⚠️  확인 필요"
else
    echo "✅"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ 하드코딩 검사 통과!"
    exit 0
else
    echo "❌ $ERRORS개 문제 발견"
    exit 1
fi
