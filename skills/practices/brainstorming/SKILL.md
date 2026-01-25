---
name: brainstorming
description: 브레인스토밍 - 아이디어를 설계로 발전. 한 번에 하나씩 질문, 2-3개 접근법 제시, 점진적 검증. 기능 구현/컴포넌트 생성 전 사용.
source: https://github.com/obra/superpowers
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time. Once you understand what you're building, present the design in small sections, checking after each section whether it looks right.

---

## The Process

### Understanding the idea

- Check out the current project state first (files, docs, recent commits)
- Ask questions **one at a time** to refine the idea
- Prefer multiple choice questions when possible
- Focus on: purpose, constraints, success criteria

### Exploring approaches

- Propose **2-3 different approaches** with trade-offs
- Lead with your recommended option and explain why
- Present options conversationally

### Presenting the design

- Break into sections of **200-300 words**
- Ask after each section: "Does this look right so far?"
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify

---

## Key Principles

| Principle | Description |
|-----------|-------------|
| **One question at a time** | Don't overwhelm with multiple questions |
| **Multiple choice preferred** | Easier to answer than open-ended |
| **YAGNI ruthlessly** | Remove unnecessary features from all designs |
| **Explore alternatives** | Always propose 2-3 approaches before settling |
| **Incremental validation** | Present design in sections, validate each |
| **Be flexible** | Go back and clarify when something doesn't make sense |

---

## Question Examples

**Good (multiple choice):**
```
Should this component:
A) Handle its own state internally
B) Receive state from parent via props
C) Use a global state store (e.g., Zustand)

I recommend B because [reason].
```

**Good (open-ended when necessary):**
```
What should happen when the API returns an error?
```

**Bad (multiple questions):**
```
What state does it need? How should errors be handled?
Should it be a class or function? What about testing?
```

---

## Design Document Template

```markdown
# [Feature Name] Design

## Goal
[One sentence]

## Approach
[2-3 sentences explaining the chosen approach]

## Architecture

### Components
- [Component 1]: [responsibility]
- [Component 2]: [responsibility]

### Data Flow
[How data moves through the system]

### Error Handling
[How errors are caught and handled]

## Trade-offs
- Chose X over Y because [reason]
- This means [limitation] but [benefit]

## Testing Strategy
- Unit tests for [components]
- Integration tests for [flows]

## Open Questions
- [Any unresolved decisions]
```

---

## After the Design

1. **Save design document** to `docs/plans/YYYY-MM-DD-<topic>-design.md`
2. **Commit** the design document
3. **Ask:** "Ready to create implementation plan?"
4. If yes, use `writing-plans` skill for detailed implementation steps

---

## Anti-patterns

| Don't | Do Instead |
|-------|------------|
| Ask 5 questions at once | One question per message |
| Jump straight to code | Explore approaches first |
| Present 1000-word design dump | 200-300 word sections with checks |
| Assume requirements | Ask clarifying questions |
| Skip trade-off discussion | Always explain why approach X over Y |
