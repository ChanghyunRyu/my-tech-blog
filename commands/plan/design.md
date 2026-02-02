---
name: design
description: 설계 문서 생성. planner-orchestrator를 호출합니다.
agent: planner-orchestrator
---

# /design

설계 문서를 생성합니다.

## 사용법

```
/design 사용자 인증 시스템
/design --from requirements.md
/design --priority RICE
```

## 동작

1. 요구사항 분석
2. 분류 구조 결정 (사용자 승인)
3. 섹션별 상세 설계
4. 통합 및 마무리

## 입력 요건

- **4줄 이상**의 정리된 요구사항
- 또는 기존 요구사항 파일 경로

## 출력 구조

```
docs/plans/{project}/
├── INDEX.md          # 전체 구조, 섹션 링크
├── requirements.md   # 요구사항 분석
└── {section}.md      # 분류된 세부 문서들
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--from` | 기존 파일에서 요구사항 로드 |
| `--priority` | 우선순위 방법론 (MoSCoW, RICE) |
| `--risk` | 리스크 분석 포함 |

## 연관 커맨드

- `/implement` - 설계 후 구현
- `/gap` - 설계-구현 갭 분석
