import re
from typing import List, Tuple
from g2pk import G2p


_g2p = G2p()


def basic_cleanup(text: str) -> str:
    text = text.strip()
    # 연속 공백을 하나로
    text = re.sub(r"\s+", " ", text)
    # 문장부호 앞 공백 제거
    text = re.sub(r"\s+([,.?!:;])", r"\1", text)
    return text


def normalize_text(text: str) -> str:
    cleaned = basic_cleanup(text)
    return _g2p(cleaned)


SENT_SPLIT_PATTERN = re.compile(r"([.?!])")


def split_sentences(text: str) -> List[str]:
    parts = SENT_SPLIT_PATTERN.split(text)
    sentences: List[str] = []
    buf = ""
    for part in parts:
        if part in ".?!":
            buf += part
            sent = buf.strip()
            if sent:
                sentences.append(sent)
            buf = ""
        else:
            buf += part
    tail = buf.strip()
    if tail:
        sentences.append(tail)
    return sentences


def normalize_and_split(text: str, do_split: bool = False) -> Tuple[str, List[str]]:
    norm = normalize_text(text)
    if not do_split:
        return norm, []
    return norm, split_sentences(norm)
