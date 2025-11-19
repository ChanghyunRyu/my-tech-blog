from __future__ import annotations

from dataclasses import dataclass
from typing import List

try:
    from g2pk import G2p
except ImportError as exc:  # pragma: no cover - runtime guard
    raise ImportError(
        "g2pk 패키지가 필요합니다. `pip install g2pk` 로 설치 후 다시 시도하세요."
    ) from exc


@dataclass
class PhonemizerConfig:
    word_boundary_token: str = "|"
    pause_token: str = "SIL"


class KoreanG2PPhonemizer:
    """g2pk2 기반의 한국어 grapheme-to-phoneme 변환기."""

    def __init__(self, config: PhonemizerConfig | None = None) -> None:
        self.config = config or PhonemizerConfig()
        self._engine = G2p()

    def to_phonemes(self, text: str) -> List[str]:
        raw = self._engine(text)
        tokens = [token for token in raw.strip().split() if token]
        if not tokens:
            return []

        phonemes: List[str] = []
        for idx, token in enumerate(tokens):
            phonemes.append(token)
            if idx < len(tokens) - 1:
                phonemes.append(self.config.word_boundary_token)
        return phonemes

