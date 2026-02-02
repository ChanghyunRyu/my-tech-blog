---
name: pdca
description: PDCA 사이클 시작. pdca-iterator를 호출합니다.
agent: pdca-iterator
---

# /pdca

PDCA(Plan-Do-Check-Act) 사이클을 시작합니다.

## 사용법

```
/pdca "사용자 인증 기능"
/pdca --max-iterations 3
/pdca --target 95
```

## 동작

```
START
  │
  ▼
┌─────────┐
│  Plan   │ ← 요구사항 분석, 설계 문서 생성
└────┬────┘
     │
     ▼
┌─────────┐
│   Do    │ ← 구현
└────┬────┘
     │
     ▼
┌─────────┐
│  Check  │ ← gap-detector로 일치율 평가
└────┬────┘
     │
     ├── 90%+ ──► COMPLETE
     │
     ├── iteration >= max ──► 사용자 개입
     │
     └── <90%
           │
           ▼
    ┌─────────┐
    │   Act   │ ← 개선점 반영
    └────┬────┘
         │
         └──► Do로 복귀
```

## 판정 기준

| 일치율 | 상태 | 조치 |
|--------|------|------|
| 90%+ | complete | 완료 |
| 70-89% | needs_improvement | 반복 |
| 50-69% | significant_gaps | 2-3회 반복 |
| <50% | major_redesign | 설계 재검토 |

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--max-iterations` | 최대 반복 횟수 (기본: 5) |
| `--target` | 목표 일치율 (기본: 90) |

## 상태 추적

`.claude/state/.claude-status.json`에 진행 상황 기록:

```json
{
  "workflow": {
    "active": "pdca",
    "phase": "check",
    "iteration": 2,
    "matchRate": 0.78
  }
}
```

## 연관 커맨드

- `/design` - Plan 단계에서 호출
- `/gap` - Check 단계에서 호출
- `/iterate` - 반복 개선
