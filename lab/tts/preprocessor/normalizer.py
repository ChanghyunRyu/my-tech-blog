import re
import hgtk
from typing import Optional
from readutils import read_counter_kor, read_only_num, read_num_eng, read_sino_kor
from readutils import read_sym_kor, read_sym_eng, read_count_sym_kor, load_eng2kor_dict
from readutils import check_acronym, read_acronym2kor, read_engbymodel
from lexicon import symbols, count_symbols, count_exceptions


# Mecab은 필요할 때만 초기화 (lazy initialization)
_mecab_instance = None
Morph = tuple[str, str]
ENG2KOR_DICT =  load_eng2kor_dict()

particles_final = ['은', '이', '과', '을', '이다']
particles_not_final = ['는', '가', '와', '를', '다']


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
    prev: Optional[Morph] = None
    nxt: Optional[Morph] = None

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
    
    if nxt is not None and (nxt_pos.startswith("NNBC") or (nxt_pos.startswith("NNG") and nxt_surface in count_exceptions)):
        return read_counter_kor(n, nxt_surface)

    # exception case 구현 파트 --- 아직 미구현

    if prev_pos.startswith("SL") or nxt_pos.startswith("SL"):
        return read_num_eng(n)
    
    if prev_surface in symbols or nxt_surface in symbols:
        return read_only_num(n)
    
    return read_sino_kor(n)


def trans_sym2kor(symbol: str, prev: Optional[Morph], nxt: Optional[Morph]):
    prev_surface = prev[0] if prev is not None else ""
    prev_pos     = prev[1] if prev is not None else ""

    nxt_surface  = nxt[0]  if nxt  is not None else ""
    nxt_pos      = nxt[1]  if nxt  is not None else ""

    if symbol in count_symbols:
        return read_count_sym_kor(symbol)
    elif not prev_pos.startswith("SF"):
        if hgtk.checker.is_hangul(prev_surface) or hgtk.checker.is_hangul(nxt_surface):
            return read_sym_kor(symbol)
        elif prev_surface.isdigit() or nxt_surface.isdigit():
            return read_sym_kor(symbol)
        elif prev_pos.startswith("SL") or nxt_pos.startswith("SL"):
            return read_sym_eng(symbol)
        else:
            return ''
    else:
        return ''
    

def trans_eng2kor(term: str):
    if term.lower() in ENG2KOR_DICT:
        return ENG2KOR_DICT[term.lower()]
    
    if check_acronym(term):
        return read_acronym2kor(term)
    try:
        return  read_engbymodel(term)
    except:
        return term

    
def trans_bundle(chunks: list[tuple[str]], chunks_snapshot: list[list[Morph]]) -> list[list[str]]:
    for i in range(len(chunks)):
        eojeol = chunks[i]

        for j in range(len(eojeol)):
            term = eojeol[j]
            prev, nxt = get_context(i, j, chunks_snapshot)
            # --- number ---
            if term.isdigit():
                n = int(term)
                chunks[i][j] = trans_num2kor(n, prev, nxt)
            # --- symbol ---
            elif term in symbols + count_symbols and (i+j > 0):
                chunks[i][j] = trans_sym2kor(term, prev, nxt)
            # --- english ---
            elif chunks_snapshot[i][j][1].startswith("SL"):
                chunks[i][j] = trans_eng2kor(term)
                print('english:{} -> korean:{}'.format(term, chunks[i][j]))
            # --- hangul ---
            elif hgtk.checker.is_hangul(term):
                if chunks_snapshot[i][j][1].startswith("JX") and (term in particles_final or term in particles_not_final):
                    chunks[i][j] = correction_particle(prev, term)
                else:
                    chunks[i][j] = term
            else:
                # --- exception case ---
                chunks[i][j] = ''
    return chunks


def correction_particle(prev: str, term: str) -> str:
    if not prev:
        return term

    last = prev[-1]
    
    if not hgtk.checker.is_hangul(last):
        return term

    _, _, final = hgtk.letter.decompose(last)
    has_final = (final != '')

    if term in particles_final and not has_final:
        return particles_not_final[particles_final.index(term)]
    
    if term in particles_not_final and has_final:
        return particles_final[particles_not_final.index(term)]
    
    return term


def trans_sentence(sentence: str) -> str:
    sentence = check_typos(sentence)
    if hgtk.checker.is_hangul(sentence):
        return sentence
    
    _, _, chunks_snapshot = align_text(sentence)
    chunks = [[m[0] for m in eojeol] for eojeol in chunks_snapshot]
    chunks = trans_bundle(chunks, chunks_snapshot)
    chunks = [''.join(e) for e in chunks]
    return ' '.join(chunks)
