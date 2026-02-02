---
name: status
description: 현재 작업 상태를 확인합니다.
---

# /status

현재 작업 상태를 확인합니다.

## 사용법

```
/status                    # 전체 상태
/status --workflow         # 워크플로우 상태만
/status --tasks            # 작업 목록
```

## 동작

`.claude/state/.claude-status.json`을 읽어 현재 상태를 표시합니다.

## 출력 형식

```markdown
## 현재 상태

### 세션
- **시작**: 2025-02-01 10:30
- **마지막 활동**: 5분 전

### 컨텍스트
- **언어**: Python
- **프레임워크**: FastAPI
- **테스트**: pytest

### 활성 워크플로우
- **유형**: PDCA
- **Phase**: Check
- **반복**: 2/5
- **일치율**: 78%

### 진행 중인 기능
| 기능 | 상태 | 일치율 |
|------|------|--------|
| auth | in_progress | 78% |
| api | completed | 95% |

### 대기 작업
- [ ] 문서 동기화: src/auth.py
- [ ] 테스트 필요: UserService
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--workflow` | 워크플로우만 |
| `--tasks` | 대기 작업만 |
| `--json` | JSON 형식 |

## 연관 커맨드

- `/pdca` - PDCA 사이클
- `/iterate` - 반복 개선
