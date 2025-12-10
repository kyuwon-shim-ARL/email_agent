# Implementation Tasks - v0.6.3 Context-Based Priority

## Overview

맥락 기반 우선순위 판단 시스템 구현.

### v0.6.3 Changes

- ✅ 맥락 기반 우선순위 판단 (하드코딩 제거)
- ✅ prioritize-email.md 스킬 파일 업데이트
- ✅ spec.md 업데이트
- ✅ plan.md 업데이트
- ✅ /email-analyze 프롬프트 업데이트

### v0.6.2 Changes (Completed)

- ✅ Gmail 초안 자동 생성 (/email-analyze 시)
- ✅ 16열 스키마 (답장여부 컬럼 추가)
- ✅ 내용미리보기 HTML 태그 제거
- ✅ /email-analyze, /email-draft 슬래시 커맨드

---

## Task 0: Context-Based Priority System (v0.6.3)

### 0.1 Remove Hardcoded Rules

**Status**: ✅ Completed

**Problem**:
- 기존: "발신자가 팀장(Soojin Jang)이면 → P5" 하드코딩
- 다른 사용자가 쓰면 작동 안 함
- VIP 목록 관리 기능 없음

**Solution**:
- Claude가 이메일 맥락에서 종합 추론
- 어투, 서명, 요청 방식에서 관계 파악
- 하드코딩 없이 범용적으로 작동

### 0.2 5-Axis Priority Framework

**Status**: ✅ Completed

**File**: `.claude/skills/prioritize-email.md`

**5가지 판단 축**:

| 축 | 판단 요소 |
|----|----------|
| 발신자-수신자 관계 | 어투, 서명 직급, 요청 방식에서 추론 |
| 요청 강도 | 즉시 결정 > 명시적 요청 > 소프트 요청 > FYI |
| 긴급 신호 | 오늘/ASAP > 이번 주 > 마감일 있음 > 여유 |
| 메일 유형 | 개인 1:1 > 팀 메일 > 전체 공지 > 자동발송 |
| 수신 방식 | To(직접) > CC(참조, -1) > 그룹(-1) |

### 0.3 Priority Definitions

**Status**: ✅ Completed

| 등급 | 기준 |
|------|------|
| **P5** | 상위 직급의 직접 요청 + 긴급 + 즉시 액션 필요 (5-10%만) |
| **P4** | 명시적 마감일 + 액션 필요 OR 중요 발신자 요청 |
| **P3** | 일반 업무 요청, 회신 필요하지만 여유 있음 (기본값) |
| **P2** | 공지사항, 참고용, FYI |
| **P1** | 자동발송, 뉴스레터, 마케팅, 스팸 |

---

## Task 1: Update Skill File

### 1.1 prioritize-email.md Rewrite

**Status**: ✅ Completed

**Changes**:
- 복잡한 점수 계산 시스템 제거
- 맥락 기반 가이드라인으로 변경
- MECE한 5가지 판단 축 정의
- 각 우선순위별 판단 체크리스트 추가

**Key Sections**:
1. 핵심 원칙 (하드코딩 없이 맥락 추론)
2. 5가지 판단 축
3. 우선순위 정의 (P1-P5)
4. 판단 가이드라인
5. 주의사항

---

## Task 2: Update Documentation

### 2.1 spec.md Update

**Status**: ✅ Completed

- Version: v0.6.2 → v0.6.3
- Core Philosophy: "Context-Based Priority" 추가
- AI 분석 기준: 맥락 기반 판단으로 변경

### 2.2 plan.md Update

**Status**: ✅ Completed

- Version: v0.6.3
- Priority System 섹션 추가
- 5가지 판단 축 설명

### 2.3 tasks.md Update

**Status**: ✅ Completed

- v0.6.3 태스크 추가
- 완료 상태 업데이트

---

## Task 3: Update /email-analyze Prompt

### 3.1 Remove Hardcoded Rules

**Status**: ✅ Completed

**File**: `.claude/commands/email-analyze.md`

**Changes**:
- "발신자가 팀장(Soojin Jang)이면 → P5" 제거
- 맥락 기반 판단 가이드라인으로 교체
- prioritize-email.md 스킬 참조

---

## Completion Summary

| Task | Status |
|------|--------|
| 0.1 Remove hardcoded rules | ✅ |
| 0.2 5-axis priority framework | ✅ |
| 0.3 Priority definitions | ✅ |
| 1.1 prioritize-email.md rewrite | ✅ |
| 2.1 spec.md update | ✅ |
| 2.2 plan.md update | ✅ |
| 2.3 tasks.md update | ✅ |
| 3.1 /email-analyze prompt update | ✅ |

---

## Key Files

- **스킬 파일**: `.claude/skills/prioritize-email.md`
- **명령어 파일**: `.claude/commands/email-analyze.md`
- **스펙 문서**: `spec.md`, `plan.md`
