---
name: writing-plans
description: 구현 계획 작성법 - 상세한 단계별 태스크 분해, 파일 경로/코드/테스트 명령 포함. 멀티 스텝 작업 전 사용.
source: https://github.com/obra/superpowers
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context. Document everything: which files to touch, code, testing, how to verify. Give the whole plan as bite-sized tasks.

**Principles:** DRY, YAGNI, TDD, Frequent commits.

---

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

---

## Plan Document Header

**Every plan MUST start with:**

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

---

## Task Structure

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

---

## Key Requirements

- **Exact file paths always** - No ambiguity
- **Complete code in plan** - Not "add validation"
- **Exact commands with expected output**
- **DRY, YAGNI** - Remove unnecessary features
- **TDD** - Test first, always
- **Frequent commits** - After each passing test

---

## Save Location

Save plans to: `docs/plans/YYYY-MM-DD-<feature-name>.md`

---

## After Writing Plan

Offer execution choice:

1. **Sequential execution** - Task by task with verification between
2. **Batch execution** - Multiple tasks then checkpoint

Always verify completion of each task before moving to next.
