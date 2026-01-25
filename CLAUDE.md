# Claude Code Instructions

## Context Loading

프로젝트 이해가 필요하면:
1. `docs/INDEX.md` - 문서 진입점 (현황, 모듈-문서 매핑)
2. `docs/explanation/architecture.md` - 전체 아키텍처
3. `docs/reference/` - API/설정 참조
ㅈ
## Working Principles

- 유사 코드 작성 전 **기존 구현 먼저 읽기**
- 추측 대신 **코드/문서 확인**
- 코드 수정 후 **code-reviewer로 자체 리뷰 권장**
- 문서 변경 필요 시 **doc-maintainer 활용**

## Agents

| Agent | 용도 | 호출 시점 | 출력 |
|-------|------|----------|------|
| doc-maintainer | 문서 동기화 (Diátaxis) | 코드 변경 후 | `docs/` |
| code-reviewer | 코드 품질 검토 | 코드 작성 완료 후 | `docs/reviews/` |
| frontend-orchestrator | 웹사이트 클론/구현 | 프론트엔드 구현 요청 시 | `blog/src/`, `docs/frontend/` |

### Frontend Workflow

`frontend-orchestrator` 사용 시:

1. URL/이미지/추상적 요청 제공
2. 자동으로 스크래핑 → 분석 → 설계 → 구현 → 검토 수행
3. 설계 단계에서 사용자 승인 요청
4. 검토 후 수정 필요 시 자동 반복 (최대 3회)

호출 예시:
- "이 사이트 클론해줘: https://example.com"
- "미니멀한 블로그 만들어줘"
- "이 디자인 구현해줘" (이미지 첨부)

## Script-First Policy

일회성 bash 명령 대신 스크립트 우선 사용:

| 작업 | 스크립트 |
|------|----------|
| 테스트 | `scripts/dev/test.sh` |
| 린트 | `scripts/dev/lint.sh` |
| 실행 | `scripts/dev/run.sh` |

**원칙**:
- 3번 이상 반복되는 명령 → `scripts/`에 추가
- 복합 명령(&&, \|) → 스크립트화
