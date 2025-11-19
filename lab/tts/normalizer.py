from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class NormalizerConfig:
    lowercase: bool = True
    collapse_spaces: bool = True


class TextNormalizer:
    """텍스트를 phoneme 단계로 넘기기 전에 간단히 정제한다."""

    _punct_pattern = re.compile(r"[^a-zA-Z0-9\s']")
    _space_pattern = re.compile(r"\s+")

    def __init__(self, config: NormalizerConfig | None = None) -> None:
        self.config = config or NormalizerConfig()

    def normalize(self, text: str) -> str:
        cleaned = text.strip()
        if self.config.lowercase:
            cleaned = cleaned.lower()
        cleaned = self._punct_pattern.sub(" ", cleaned)
        if self.config.collapse_spaces:
            cleaned = self._space_pattern.sub(" ", cleaned)
        return cleaned.strip()

