import re
import os
import hgtk
from typing import Optional
from readutils import read_counter_kor, read_only_num, read_num_eng, read_sino_kor, check_latin
from lexicon import symbols

# Mecab은 필요할 때만 초기화 (lazy initialization)
_mecab_instance = None

Morph = tuple[str, str] 


def check_typos(text: str) -> str:
    """
    텍스트에서 오탈자를 삭제하는 함수.
    """
    result = text
    
    # 한글 자모 정규식
    # 초성: ㄱ-ㅎ (0x3131-0x314E)
    # 중성: ㅏ-ㅣ (0x314F-0x3163)
    # 종성: ㄱ-ㅎ (0x3131-0x314E)
    
    # 1. 모음만 있는 경우 삭제 (예: ㅣ, ㅡ, ㅏ 등)
    # 중성만 있는 패턴 (ㅏ-ㅣ)
    result = re.sub(r'[ㅏ-ㅣ]+', '', result)
    
    # 2. 자음만 있는 경우 삭제 (예: ㄱ, ㄴ, ㄷ 등)
    # 초성/종성만 있는 패턴 (ㄱ-ㅎ)
    result = re.sub(r'[ㄱ-ㅎ]+', '', result)
    
    # 3. 비정상적인 공백 패턴 정규화 (연속된 공백 3개 이상을 1개로 변경)
    result = re.sub(r' {3,}', ' ', result)
    return result
    

class MecabWrapper:
    """mecab_ko.Tagger를 konlpy.Mecab과 호환되도록 래핑하는 클래스"""
    def __init__(self):
        from mecab_ko import Tagger
        self.tagger = Tagger()
    
    def pos(self, text):
        """형태소 분석 결과를 (형태소, 품사) 튜플 리스트로 반환"""
        result = self.tagger.parse(text)
        pos_list = []
        for line in result.strip().split('\n'):
            if line == 'EOS':
                break
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    word = parts[0]
                    features = parts[1].split(',')
                    pos_tag = features[0] if features else 'UNKNOWN'
                    pos_list.append((word, pos_tag))
        return pos_list


def _get_mecab():
    """Mecab 인스턴스를 가져오는 함수 (lazy initialization)"""
    global _mecab_instance
    if _mecab_instance is None:
        try:
            # 먼저 konlpy를 시도
            try:
                from konlpy.tag import Mecab
                _mecab_instance = Mecab()
            except:
                # konlpy가 실패하면 mecab_ko 직접 사용
                _mecab_instance = MecabWrapper()
        except Exception as e:
            raise RuntimeError(
                f"Mecab 초기화 실패: {e}\n"
                "mecab-ko-dic이 설치되어 있는지 확인하세요."
            )
    return _mecab_instance


def align_text(sentence: str):
    mecab = _get_mecab()
    
    s = sentence.split(" ")
    particles = mecab.pos(sentence)
    chunks = []
    final = False
    if len(particles) > 0:
        count_word = 0
        morphemes = []
        total = []
        for i in range(len(particles)):
            morphemes.append(particles[i][0])
            total.append(particles[i])
            if i+1 < len(particles):
                morphemes_temp = morphemes[:]
                morphemes_temp.append(particles[i+1][0])
                if "".join(morphemes_temp) not in s[count_word]:
                    chunks.append(total)
                    count_word += 1
                    morphemes = []
                    total = []
            else:
                chunks.append(total)
    return s, particles, chunks


def is_sentence_final(pos: str) -> bool:
    return pos.startswith("SF")


def get_context(i: int, j: int, meta) -> tuple[str | None, str | None]:
    prev_word = Optional[Morph]
    next_word = Optional[Morph]

    # --- prev ---
    if j > 0:
        prev = meta[i][j-1]
    elif i > 0:
        prev = meta[i-1][-1]
    if prev is not None and is_sentence_final(prev[1]):
        prev = None

    # --- next ---
    if j + 1 < len(meta[i]):
        nxt = meta[i][j+1]
    elif i + 1 < len(meta):
        nxt = meta[i+1][0]
    if nxt is not None and is_sentence_final(nxt[1]):
        nxt = None

    return prev, nxt


def trans_num2kor(n: int, prev: Optional[Morph], nxt: Optional[Morph]):
    """
    숫자 n을 한글 표기로 바꾸는 래퍼.
    """

    prev_surface = prev[0] if prev is not None else ""
    prev_pos     = prev[1] if prev is not None else ""

    nxt_surface  = nxt[0]  if nxt  is not None else ""
    nxt_pos      = nxt[1]  if nxt  is not None else ""
    
    if nxt is not None and nxt_pos.startswith("NNBC"):
        return read_counter_kor(n, nxt_surface)

    # exception case 구현 파트 --- 아직 미구현

    if check_latin(prev_surface) or check_latin(nxt_surface):
        return read_num_eng(n)
    
    if prev_surface in symbols or nxt_surface in symbols:
        return read_only_num(n)
    
    return read_sino_kor(n)


def trans_bundle(chunks: list[tuple[str]], chunks_snapshot: list[tuple[str]]):
    for i in range(len(chunks)):
        eojeol = chunks[i]
        for j in range(len(eojeol)):
            term = eojeol[j]
            if term.isdigit():
                term = int(term)
                chunks[i][j] = trans_num2kor(term) 
            
    return 
