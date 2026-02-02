# 슬래시 커맨드 인덱스

## 개요

총 20개의 슬래시 커맨드가 사용 가능합니다.

## 카테고리별 목록

### dev/ - 개발
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/implement` | 기능 구현 시작 | - |
| `/test` | 테스트 생성/실행 | testing-orchestrator |
| `/review` | 코드 리뷰 | code-reviewer |
| `/debug` | 디버깅 세션 | - |

### plan/ - 계획
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/design` | 설계 문서 생성 | planner-orchestrator |
| `/plan` | 구현 계획 작성 | - |
| `/brainstorm` | 아이디어 탐색 | - |

### quality/ - 품질
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/security` | 보안 리뷰 | security-reviewer |
| `/improve` | 코드 개선 제안 | - |
| `/cleanup` | 데드 코드 제거 | - |

### docs/ - 문서
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/doc` | 문서 작성/업데이트 | doc-maintainer |
| `/explain` | 코드 설명 | - |

### research/ - 연구
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/research` | 심층 조사 | research-orchestrator |

### workflow/ - 워크플로우
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/pdca` | PDCA 사이클 시작 | pdca-iterator |
| `/iterate` | 반복 개선 | pm-agent |
| `/gap` | 설계-구현 갭 분석 | gap-detector |

### frontend/ - 프론트엔드
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/clone` | 웹사이트 클론 | frontend-orchestrator |

### meta/ - 메타
| 커맨드 | 설명 | 연결 에이전트 |
|--------|------|--------------|
| `/status` | 현재 상태 확인 | - |
| `/load` | 컨텍스트 로드 | - |
| `/help` | 도움말 | - |

## 행동 모드 플래그

커맨드와 함께 사용 가능한 플래그:

| 플래그 | 설명 | 예시 |
|--------|------|------|
| `--brainstorm` | 아이디어 탐색 | `/implement --brainstorm 인증` |
| `--introspect` | 추론 과정 명시 | `/design --introspect API` |
| `--task-manage` | 계층적 작업 분해 | `/implement --task-manage 대시보드` |
| `--uc` | 토큰 압축 | `/explain --uc 코드` |
| `--deep-think` | 심층 사고 | `/research --deep-think 아키텍처` |

## 사용 예시

```bash
# 기본 사용
/review

# 옵션과 함께
/test --e2e login

# 행동 모드와 함께
/implement --brainstorm 결제 시스템

# 대상 지정
/security src/auth/
```

## 파일 위치

모든 커맨드 파일은 `.claude/commands/` 디렉토리에 있습니다.
