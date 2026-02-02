---
name: load
description: 특정 컨텍스트를 로드합니다.
---

# /load

특정 컨텍스트나 이전 세션을 로드합니다.

## 사용법

```
/load docs/INDEX.md        # 문서 컨텍스트
/load src/auth/            # 특정 모듈
/load --session            # 이전 세션 복원
/load --project            # 프로젝트 전체
```

## 동작

1. 대상 파일/디렉토리 식별
2. 관련 컨텍스트 수집
3. 요약 생성
4. 메모리에 로드

## 로드 대상

| 대상 | 로드 내용 |
|------|----------|
| 파일 경로 | 해당 파일 내용 |
| 디렉토리 | 주요 파일 요약 |
| `--session` | 이전 세션 상태 |
| `--project` | 프로젝트 구조 + INDEX.md |

## 출력 형식

```markdown
## 컨텍스트 로드 완료

### 로드된 항목
- `docs/INDEX.md` - 프로젝트 개요
- `docs/explanation/architecture.md` - 아키텍처
- `src/` - 소스 코드 구조

### 요약
{프로젝트/모듈 요약}

### 관련 에이전트
- doc-maintainer (문서 관련)
- code-reviewer (코드 관련)

### 다음 추천 작업
- /implement - 기능 구현
- /review - 코드 리뷰
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--session` | 이전 세션 상태 복원 |
| `--project` | 프로젝트 전체 컨텍스트 |
| `--deep` | 더 깊은 컨텍스트 수집 |
