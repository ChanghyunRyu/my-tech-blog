---
name: test-driven-development
description: TDD 방법론 - RED-GREEN-REFACTOR 사이클. 테스트 먼저 작성, 실패 확인, 최소 구현, 리팩토링. 기능 구현/버그 수정 전 필수.
source: https://github.com/obra/superpowers
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask first):**
- Throwaway prototypes
- Generated code
- Configuration files

---

## Red-Green-Refactor

```
RED → Verify Fails → GREEN → Verify Passes → REFACTOR → Repeat
```

### RED - Write Failing Test

Write one minimal test showing what should happen.

```python
# Good: Clear name, tests real behavior, one thing
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)

    assert result == 'success'
    assert attempts == 3
```

**Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
pytest path/to/test.py -v
```

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

### GREEN - Minimal Code

Write simplest code to pass the test.

```python
# Good: Just enough to pass
async def retry_operation(fn, max_retries=3):
    for i in range(max_retries):
        try:
            return await fn()
        except Exception:
            if i == max_retries - 1:
                raise
```

Don't add features, refactor other code, or "improve" beyond the test.

### Verify GREEN - Watch It Pass

**MANDATORY.**

```bash
pytest path/to/test.py -v
```

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior.

---

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
| "TDD will slow me down" | TDD faster than debugging. |

---

## Red Flags - STOP and Start Over

- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"

**All of these mean: Delete code. Start over with TDD.**

---

## Example: Bug Fix

**Bug:** Empty email accepted

**RED**
```python
def test_rejects_empty_email():
    result = submit_form({'email': ''})
    assert result['error'] == 'Email required'
```

**Verify RED**
```bash
$ pytest
FAIL: expected 'Email required', got None
```

**GREEN**
```python
def submit_form(data):
    if not data.get('email', '').strip():
        return {'error': 'Email required'}
    # ...
```

**Verify GREEN**
```bash
$ pytest
PASS
```

---

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

---

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions.
