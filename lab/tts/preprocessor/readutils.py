import string
import re
import glob
import os
import json
from pathlib import Path
from lexicon import _SINO_DIGITS, _SINO_SMALL_UNITS, _SINO_BIG_UNITS, _NATIVE_ONES, _NATIVE_TENS
from lexicon import ENG_NUM_0, ENG_NUM_TENS, ENG_NUM_TEEN, ENG_NUM_READ_PER_DIGIT, ALPHA_READ
from lexicon import symbols, sym_kor, sym_eng, count_symbols, count_sym_kor


def read_sino_kor(n: int) -> str:
    if n == 0:
        return "영"
    if n < 0:
        return "마이너스 " + read_sino_kor(-n)

    # 너무 큰 수는 일단 스트링으로만 (필요하면 확장)
    if n > 9999999999999999:
        return str(n)

    parts: list[str] = []
    group_index = 0  # 만, 억, 조, ...

    while n > 0:
        group = n % 10000
        n //= 10000

        if group == 0:
            group_index += 1
            continue

        small_parts: list[str] = []
        pos = 0
        while group > 0:
            digit = group % 10
            group //= 10

            if digit != 0:
                small_parts.append(_SINO_DIGITS[digit] + _SINO_SMALL_UNITS[pos])
            pos += 1

        group_str = "".join(reversed(small_parts))
        unit_str = _SINO_BIG_UNITS[group_index]
        parts.append(group_str + unit_str)

        group_index += 1

    return "".join(reversed(parts))


def read_native_kor(n: int) -> str:
    if n >= 100:
        return read_sino_kor(n)
    
    if n == 20:
        return "스무"

    tens = n // 10
    ones = n % 10

    # 1~9
    if tens == 0:
        native = _NATIVE_ONES.get(ones, read_sino_kor(n))
        return native

    # 10, 20, 30, ... 90 (딱 떨어지는 경우)
    if ones == 0:
        tens_str = _NATIVE_TENS.get(tens, read_sino_kor(n))
        return tens_str

    # 11~19, 21~99 (둘 다 있는 경우)
    tens_str = _NATIVE_TENS.get(tens, "")
    ones_str = _NATIVE_ONES.get(ones, "")

    if tens_str and ones_str:
        return tens_str + ones_str

    # 혹시 매핑밖이면 그냥 한자어 숫자 + 단위
    return read_sino_kor(n)


def read_counter_kor(n: int, nxt: str) -> str:
    from lexicon import _get_counter_reader
    counter_reader = _get_counter_reader()
    reader = counter_reader.get(nxt, read_sino_kor)
    return reader(n)


def read_only_num(n):
    nums = '영일이삼사오육칠팔구'
    read = [nums[int(z)] for z in str(n)]
    return ''.join(read)


def read_num_eng(n: int) -> str:
    if n == 0:
        return "제로"

    # 음수 처리
    if n < 0:
        return "마이너스 " + read_num_eng(-n)

    # 1~9
    if n < 10:
        return ENG_NUM_0[n]

    # 10~99
    if n < 100:
        tens, ones = divmod(n, 10)

        # 10~19
        if tens == 1:
            if ones == 0:
                # 10
                return ENG_NUM_TENS[0]
            # 11~19
            return ENG_NUM_TEEN[ones]

        # 20~99
        tens_str = ENG_NUM_TENS[tens - 1]  # 20 → index 1
        ones_str = ENG_NUM_0[ones]
        return tens_str + ones_str

    # 100 이상: 각 자리수를 '원투쓰리...'로 읽기
    return "".join(ENG_NUM_READ_PER_DIGIT[int(d)] for d in str(n))


def check_latin(term: str) -> bool:
    return any(ch in string.ascii_letters for ch in term)


def read_sym_kor(symbol: str) -> str:
    return sym_kor[symbols.index(symbol)]


def read_sym_eng(symbol: str) -> str:
    return sym_eng[symbols.index(symbol)]


def read_count_sym_kor(symbol: str) -> str:
    return count_sym_kor[count_symbols.index(symbol)]


def load_base_eng2kor_dict() -> dict[str, str]:
    dataset = []
    for data_name in glob.glob('transliteration/data/source/*'):
        with open(data_name, 'r') as f:
            lines = f.read().splitlines()
            cleaned = [line.split('\t') for line in lines[3:] if '\t' in line]
            dataset.extend(cleaned)
    
    data_dict = {
        re.sub(' +', ' ', eng).lower():
        re.sub(' +', ' ', kor)
            for eng, kor in dataset
    }
    return data_dict


# --- 예외 처리용 user dictionary load 
def load_user_eng2kor_dict(path: str = 'eng_user_dict.json') -> dict[str, str]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding= "utf-8") as f:
        return json.load(f)


def load_eng2kor_dict() -> dict[str, str]:
    base_dict = load_base_eng2kor_dict()
    user_dict = load_user_eng2kor_dict()

    base_dict.update(user_dict)
    return base_dict
    

VOWELS = set("aeiou")


def check_acronym(term: str) -> bool:
    if len(term) == 1 and term.isupper():
        return True
    
    if all(ch.isupper() for ch in term if ch.isalpha()):
        return True
    
    if all((ch.lower() not in VOWELS) for ch in  term if ch.isalpha()):
        return True
    return False


def read_acronym2kor(term: str) -> str:
    result = []
    for ch in term:
        if ch.isalpha():
            idx = ord(ch.lower()) - ord('a')
            result.append(ALPHA_READ[idx])
        else:
            result.append(ch)
    return ''.join(result)


def read_engbymodel(term: str) -> str:
    return term