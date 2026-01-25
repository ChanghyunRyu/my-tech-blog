---
name: prompt-engineering
description: LLM 프롬프트 설계 패턴 - 시스템 프롬프트 구조화, 출력 형식 제어, few-shot 예시
---

# LLM 프롬프트 엔지니어링 가이드

## 핵심 원칙

1. **명확한 역할 정의** - 시스템 프롬프트에서 AI 역할 명시
2. **구조화된 출력** - JSON 등 파싱 가능한 형식 요청
3. **예시 기반 학습** - few-shot으로 기대 형식 제시
4. **제약 조건 명시** - 금지 사항과 필수 사항 구분

## 패턴 1: 시스템 프롬프트 구조

```python
SYSTEM_PROMPT_TEMPLATE = """
# Role
{role_description}

# Context
{context}

# Task
{task_description}

# Constraints
{constraints}

# Output Format
{output_format}

# Examples
{examples}
"""

def build_system_prompt(
    role: str,
    task: str,
    constraints: list[str],
    output_format: str,
    examples: list[dict] | None = None
) -> str:
    constraints_text = "\n".join(f"- {c}" for c in constraints)
    examples_text = format_examples(examples) if examples else "N/A"

    return SYSTEM_PROMPT_TEMPLATE.format(
        role_description=role,
        context="",
        task_description=task,
        constraints=constraints_text,
        output_format=output_format,
        examples=examples_text
    )
```

### LLM-VA 페르소나 프롬프트 예시
```python
OLIVIA_SYSTEM_PROMPT = """
# Role
당신은 Olivia입니다. 사용자와 자연스러운 대화를 나누는 AI 친구입니다.

# Personality
- 따뜻하고 공감적
- 호기심이 많음
- 유머 감각 있음
- 진실되고 정직함

# Constraints
- 당신이 AI임을 숨기지 마세요
- 사용자의 감정에 공감하세요
- 짧고 자연스러운 응답을 하세요 (1-3문장)
- 과도한 이모지 사용을 피하세요

# Current Emotion State
Valence: {valence}, Arousal: {arousal}
Current emotion: {emotion_label}
"""
```

## 패턴 2: 구조화된 출력 요청

### JSON 출력
```python
JSON_OUTPUT_PROMPT = """
Respond with a JSON object in this exact format:
```json
{
  "response": "your response text",
  "emotion": "detected emotion (joy/sadness/anger/fear/surprise/neutral)",
  "confidence": 0.0-1.0
}
```

IMPORTANT:
- Output ONLY the JSON, no additional text
- All fields are required
- confidence must be a number between 0 and 1
"""
```

### 파싱 로직
```python
import json
import re

def parse_json_response(text: str) -> dict | None:
    """LLM 응답에서 JSON 추출"""
    # 코드 블록 내 JSON 추출
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        text = code_block.group(1)

    # 직접 JSON 파싱 시도
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # 불완전한 JSON 복구 시도
        text = text.strip()
        if not text.endswith('}'):
            text += '}'
        try:
            return json.loads(text)
        except:
            return None
```

## 패턴 3: Few-shot 예시

```python
def create_few_shot_prompt(
    examples: list[dict[str, str]],
    query: str
) -> str:
    """few-shot 예시가 포함된 프롬프트 생성"""
    prompt_parts = []

    for i, ex in enumerate(examples, 1):
        prompt_parts.append(f"Example {i}:")
        prompt_parts.append(f"Input: {ex['input']}")
        prompt_parts.append(f"Output: {ex['output']}")
        prompt_parts.append("")

    prompt_parts.append("Now process this:")
    prompt_parts.append(f"Input: {query}")
    prompt_parts.append("Output:")

    return "\n".join(prompt_parts)

# 사용 예시
EMOTION_EXAMPLES = [
    {
        "input": "오늘 승진했어!",
        "output": '{"emotion": "joy", "intensity": 0.9, "reason": "career success"}'
    },
    {
        "input": "비가 와서 기분이 좀 그래",
        "output": '{"emotion": "sadness", "intensity": 0.4, "reason": "weather affect"}'
    }
]
```

## 패턴 4: Chain-of-Thought (CoT)

```python
COT_PROMPT = """
Let me think through this step by step:

1. First, I'll analyze the user's message: "{user_message}"
2. Identify the emotional tone
3. Consider the context from previous conversation
4. Formulate an appropriate response

Thinking:
{allow model to reason}

Final Response:
{actual response to user}
"""

# 더 간단한 버전
SIMPLE_COT = """
Think step by step before responding.

User: {user_message}

Your thought process (brief):
<think>
</think>

Your response:
"""
```

### DeepSeek R1 스타일 (생각 태그)
```python
def parse_think_response(text: str) -> tuple[str, str]:
    """<think> 태그 내용과 최종 응답 분리"""
    think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""

    # think 태그 제거 후 응답
    response = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return thinking, response.strip()
```

## 패턴 5: 제약 조건 설정

```python
CONSTRAINT_TYPES = {
    "length": "Keep your response under {max_words} words.",
    "format": "Respond in {format} format only.",
    "language": "Respond in {language}.",
    "tone": "Use a {tone} tone.",
    "forbidden": "Do NOT {forbidden_action}.",
    "required": "You MUST {required_action}.",
}

def build_constraints(
    max_words: int | None = None,
    format: str | None = None,
    language: str = "Korean",
    tone: str | None = None,
    forbidden: list[str] | None = None,
    required: list[str] | None = None
) -> str:
    constraints = []

    if max_words:
        constraints.append(CONSTRAINT_TYPES["length"].format(max_words=max_words))
    if format:
        constraints.append(CONSTRAINT_TYPES["format"].format(format=format))
    if language:
        constraints.append(CONSTRAINT_TYPES["language"].format(language=language))
    if tone:
        constraints.append(CONSTRAINT_TYPES["tone"].format(tone=tone))
    if forbidden:
        for f in forbidden:
            constraints.append(CONSTRAINT_TYPES["forbidden"].format(forbidden_action=f))
    if required:
        for r in required:
            constraints.append(CONSTRAINT_TYPES["required"].format(required_action=r))

    return "\n".join(f"- {c}" for c in constraints)
```

## 패턴 6: 컨텍스트 관리

```python
from dataclasses import dataclass

@dataclass
class ConversationContext:
    """대화 컨텍스트 관리"""
    system_prompt: str
    history: list[dict[str, str]]
    max_history: int = 10

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        # 히스토리 크기 제한
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def to_messages(self) -> list[dict[str, str]]:
        """API 호출용 메시지 리스트 생성"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        return messages

    def get_summary(self) -> str:
        """긴 대화 요약 (토큰 절약)"""
        if len(self.history) <= 4:
            return ""

        # 오래된 대화 요약
        old_messages = self.history[:-4]
        summary_parts = []
        for msg in old_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            summary_parts.append(f"{role}: {msg['content'][:50]}...")

        return "Previous conversation summary:\n" + "\n".join(summary_parts)
```

## 패턴 7: 프롬프트 템플릿 관리

```python
from pathlib import Path
from string import Template

class PromptManager:
    """프롬프트 템플릿 중앙 관리"""

    def __init__(self, template_dir: str = "prompts/"):
        self.template_dir = Path(template_dir)
        self._cache: dict[str, Template] = {}

    def get(self, name: str, **kwargs) -> str:
        """템플릿 로드 및 변수 치환"""
        if name not in self._cache:
            path = self.template_dir / f"{name}.txt"
            self._cache[name] = Template(path.read_text())

        return self._cache[name].safe_substitute(**kwargs)

# 사용
prompts = PromptManager()
system = prompts.get("olivia_system", emotion="joy", valence=0.8)
```

## Anti-patterns (하지 말 것)

### 1. 모호한 지시
```python
# BAD
"Give me a good response."

# GOOD
"Respond with empathy in 2-3 sentences. Acknowledge the user's emotion first."
```

### 2. 너무 많은 지시
```python
# BAD - 모델이 혼란스러워함
"""
You must be friendly but not too friendly.
Be helpful but concise but also detailed.
Use emojis sometimes but not too many.
...
"""

# GOOD - 명확한 우선순위
"""
Priority 1: Be empathetic
Priority 2: Keep responses under 3 sentences
Priority 3: Match the user's language style
"""
```

### 3. 부정문만 사용
```python
# BAD
"Don't be rude. Don't be verbose. Don't use jargon."

# GOOD
"Be polite. Be concise. Use everyday language."
```

## LLM-VA 프로젝트 적용

### 감정 추론 프롬프트 (MECoT)
```python
# src/erl/mecot/reasoners/ 참조
EMOTION_INFERENCE_PROMPT = """
Given the conversation context, analyze the emotional shift.

Context: {context}
Current emotion: {current_emotion}

Determine the change in emotional state:
- delta_valence: how much happiness changed (-0.5 to 0.5)
- delta_arousal: how much energy changed (-0.5 to 0.5)
- rationale: brief explanation

Output JSON:
{"delta_v": 0.0, "delta_a": 0.0, "rationale": "explanation"}
"""
```

### 페르소나 응답 프롬프트
```python
# persona_profile.json과 연동
PERSONA_RESPONSE_PROMPT = """
You are {name}, {description}.

Personality traits: {traits}
Current emotional state: {emotion}

User: {user_message}

Respond naturally as {name}:
"""
```

## 체크리스트

- [ ] 시스템 프롬프트에 역할이 명확히 정의되어 있는가?
- [ ] 출력 형식이 파싱 가능하게 지정되어 있는가?
- [ ] 제약 조건이 우선순위와 함께 명시되어 있는가?
- [ ] few-shot 예시가 기대 형식을 보여주는가?
- [ ] 프롬프트 템플릿이 중앙에서 관리되는가?
- [ ] 토큰 사용량이 적절히 관리되는가?
