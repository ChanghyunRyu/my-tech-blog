# Claude Code Instructions

## Context Loading

프로젝트 이해가 필요하면:
1. `docs/INDEX.md` - 문서 진입점 (현황, 모듈-문서 매핑)
2. `docs/explanation/architecture.md` - 전체 아키텍처
3. `docs/reference/` - API/설정 참조

## Working Principles

- 유사 코드 작성 전 **기존 구현 먼저 읽기**
- 추측 대신 **코드/문서 확인**
- 코드 수정 후 **code-reviewer로 자체 리뷰 권장**
- 문서 변경 필요 시 **doc-maintainer 활용**

---

## Slash Commands

슬래시 커맨드로 주요 작업을 빠르게 시작할 수 있습니다.

### 자주 사용하는 커맨드

| 커맨드 | 용도 | 예시 |
|--------|------|------|
| `/implement` | 기능 구현 시작 | `/implement 사용자 인증` |
| `/test` | 테스트 생성/실행 | `/test --e2e login` |
| `/review` | 코드 리뷰 | `/review` |
| `/design` | 설계 문서 생성 | `/design 결제 시스템` |
| `/security` | 보안 리뷰 | `/security src/auth/` |
| `/research` | 심층 조사 | `/research React 19` |
| `/pdca` | PDCA 사이클 시작 | `/pdca --threshold 90` |
| `/status` | 현재 상태 확인 | `/status` |

전체 목록: `.claude/commands/_index.md`

---

## Agents

### 핵심 에이전트

| Agent | 용도 | 호출 시점 | 출력 |
|-------|------|----------|------|
| doc-maintainer | 문서 동기화 (Diátaxis) | 코드 변경 후 | `docs/` |
| code-reviewer | 코드 품질 검토 (12개 항목) | 코드 작성 완료 후 | `docs/reviews/` |
| security-reviewer | OWASP 기반 보안 리뷰 | 보안 관련 코드 변경 시 | `docs/reviews/security/` |
| research-orchestrator | 멀티홉 추론 심층 연구 | 복잡한 조사/분석 요청 시 | `docs/research/` |
| frontend-orchestrator | 웹사이트 클론/구현 | 프론트엔드 구현 요청 시 | `blog/src/`, `docs/frontend/` |
| planner-orchestrator | 설계 문서 생성 | 4줄 이상 요구사항 기반 설계 시 | `docs/plans/` |
| testing-orchestrator | 테스트 자동 생성/실행 | 테스트 요청 시 | `tests/`, `e2e/`, `docs/testing/` |

### 자기 개선 에이전트 (PDCA)

| Agent | 용도 | 호출 시점 | 출력 |
|-------|------|----------|------|
| gap-detector | 설계-구현 Gap 분석 | Check Phase | `gap-report.json/md` |
| pdca-iterator | PDCA 사이클 관리 | `/pdca` 시작 시 | 상태 업데이트 |
| pm-agent | 개선 우선순위 결정 | Act Phase | `improvement-plan.md` |

---

## PDCA Workflow

설계-구현 일치율 90% 도달까지 자동 반복하는 자기 개선 워크플로우.

### 사용법

```bash
/pdca                           # PDCA 사이클 시작
/pdca --threshold 95            # 95% 목표
/gap                            # Gap 분석만 실행
/status --workflow              # 현재 워크플로우 상태
```

### 사이클 흐름

```
Plan (설계) → Do (구현) → Check (Gap 분석) → Act (개선 계획)
                              ↓
                        90% 이상? → 완료
                              ↓
                        미달성 → Plan으로 (최대 5회)
```

### 결과 해석

| 일치율 | 상태 | 조치 |
|--------|------|------|
| 90% 이상 | 완료 | 다음 기능으로 |
| 70-89% | 개선 필요 | 자동 반복 |
| 70% 미만 | 설계 재검토 | 사용자 확인 요청 |

---

## Behavior Modes

요청에 플래그를 추가하여 응답 방식을 조절합니다.

### 사용법
```bash
"이 기능을 설계해줘 --brainstorm"
/implement --task-manage 대시보드
/research --deep-think 아키텍처
```

### 모드 목록

| 모드 | 플래그 | 설명 | 상세 |
|------|--------|------|------|
| 브레인스토밍 | `--brainstorm` | 2-3개 옵션 제시, 권장안 명시 | `.claude/modes/brainstorm.md` |
| 메타인지 | `--introspect` | 추론 과정 명시, 확신도 표시 (🟢/🟡/🔴) | `.claude/modes/introspect.md` |
| 태스크 관리 | `--task-manage` | 계층적 작업 분해, 진행률 추적 | `.claude/modes/task-manage.md` |
| 오케스트레이션 | `--orchestrate` | 다중 에이전트 조율 | `.claude/modes/orchestrate.md` |
| 토큰 압축 | `--uc` | 간결한 응답, 약어 사용 | `.claude/modes/uc.md` |
| 심층 사고 | `--deep-think` | 다중 관점 분석, What-If 시나리오 | `.claude/modes/deep-think.md` |

### 권장 조합

| 상황 | 조합 |
|------|------|
| 복잡한 설계 | `--brainstorm --introspect` |
| 대규모 구현 | `--task-manage --orchestrate` |
| 빠른 분석 | `--uc --introspect` |

---

## Auto-Activation Rules

특정 패턴 감지 시 자동으로 적절한 에이전트/모드가 제안됩니다.

### 주요 트리거

| 패턴 | 활성화 |
|------|--------|
| 보안 관련 파일 수정 | security-reviewer 제안 |
| 공개 API 변경 | doc-maintainer 제안 |
| 테스트 커버리지 부족 | testing-orchestrator 제안 |
| PDCA 진행 중 | 자동 Phase 전환 |

상세: `.claude/RULES.md`

---

## State Management

세션 상태는 `.claude/state/.claude-status.json`에 저장됩니다.

### 상태 확인

```bash
/status                    # 전체 상태
/status --workflow         # 워크플로우만
/status --tasks            # 대기 작업만
```

### 추적 항목

- 세션 정보 (시작 시간, 마지막 활동)
- 프로젝트 컨텍스트 (언어, 프레임워크)
- 활성 워크플로우 (PDCA Phase, 일치율)
- 대기 작업 (문서 동기화, 테스트 필요 등)
- 활성 모드 (brainstorm, introspect 등)

---

## Hooks

특정 시점에 자동 실행되는 동작이 정의되어 있습니다.

### 주요 훅

| 훅 | 트리거 | 동작 |
|----|--------|------|
| post-edit/security-check | 보안 파일 수정 시 | security-reviewer 제안 |
| post-agent/doc-sync | 코드 리뷰 후 API 변경 감지 | doc-maintainer 제안 |
| post-phase/record | PDCA Phase 완료 시 | 상태 기록 |
| pre-commit/validate | 커밋 전 | 린트, 테스트, 보안 검사 |

상세: `.claude/hooks/README.md`

---

## Workflow Examples

### Planner Workflow

```bash
# 설계 문서 생성
/design 결제 시스템

# 또는 직접 요청
"다음 요구사항으로 설계 문서 만들어줘: [4줄 이상]"
```

출력:
```
docs/plans/{project}/
├── INDEX.md          # 전체 구조
├── requirements.md   # 요구사항 분석
└── {section}.md      # 섹션별 문서
```

### Testing Workflow

```bash
/test                          # 전체 테스트 생성
/test src/services/payment.py  # 특정 파일
/test --e2e login              # E2E 테스트
```

### Security Workflow

```bash
/security                      # 전체 보안 리뷰
/security src/auth/            # 특정 경로
```

### Research Workflow

```bash
/research React 19             # 기술 조사
/research --deep-think 아키텍처 # 심층 분석
```

---

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

---

## Directory Structure

```
.claude/
├── CLAUDE.md           # 이 파일
├── RULES.md            # 자동 활성화 규칙
├── agents/             # 에이전트 정의
│   ├── code-reviewer.md
│   ├── security-reviewer.md
│   ├── gap-detector.md
│   ├── pdca-iterator.md
│   ├── pm-agent.md
│   └── ...
├── commands/           # 슬래시 커맨드 (20개)
│   ├── _index.md
│   ├── dev/
│   ├── plan/
│   ├── quality/
│   ├── docs/
│   ├── research/
│   ├── workflow/
│   ├── frontend/
│   └── meta/
├── modes/              # 행동 모드 (6개)
│   ├── brainstorm.md
│   ├── introspect.md
│   ├── task-manage.md
│   ├── orchestrate.md
│   ├── uc.md
│   └── deep-think.md
├── hooks/              # 훅 정의
│   ├── post-edit/
│   ├── post-agent/
│   ├── pre-commit/
│   └── post-phase/
├── skills/             # 스킬 정의
│   ├── code-review/
│   ├── security/
│   ├── research/
│   └── practices/
└── state/              # 상태 관리
    ├── .claude-status.json
    └── status-schema.json
```
