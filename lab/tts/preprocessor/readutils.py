from collections import UserList
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
                # 십, 백, 천 단위에서 1은 "일"을 생략
                # 예: 10 → "십", 100 → "백", 1000 → "천", 1592 → "천오백구십이"
                if pos > 0 and digit == 1:
                    small_parts.append(_SINO_SMALL_UNITS[pos])  # "일" 없이 단위만
                else:
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
    json_path = Path(__file__).parent / 'dataset' / 'base_eng2kor_dict.json'
    
    if not json_path.exists():
        print(f"경고: {json_path} 파일을 찾을 수 없습니다.")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        return data_dict
    except Exception as e:
        print(f"경고: {json_path} 파일 읽기 실패: {e}")
        return {}


# --- 예외 처리용 user dictionary load 
def load_user_eng2kor_dict() -> dict[str, str]:
    json_path = Path(__file__).parent / 'dataset' / 'user_eng2kor_dict.json'
    if not json_path.exists():
        print(f"경고: {json_path} 파일을 찾을 수 없습니다.")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        return data_dict
    except Exception as e:
        print(f"경고: {json_path} 파일 읽기 실패: {e}")
        return {}


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


# Hugging Face 모델을 위한 전역 변수 (lazy initialization)
_transliterator_model = None
_transliterator_tokenizer = None
_transliterator_device = None  # GPU/CPU 디바이스


def read_engbymodel(term: str) -> str:
    global _transliterator_model, _transliterator_tokenizer, _transliterator_device
    
    # 모델이 없으면 로드 (lazy initialization)
    if _transliterator_model is None or _transliterator_tokenizer is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            model_checkpoint = "eunsour/en-ko-transliterator"
            
            # GPU 사용 가능 여부 확인
            if torch.cuda.is_available():
                _transliterator_device = torch.device("cuda")
                device_name = torch.cuda.get_device_name(0)
                print(f"영한 변환 모델 로딩 중: {model_checkpoint}")
                print(f"  GPU 사용: {device_name}")
            else:
                _transliterator_device = torch.device("cpu")
                print(f"영한 변환 모델 로딩 중: {model_checkpoint} (CPU 모드)")
            
            _transliterator_tokenizer = AutoTokenizer.from_pretrained(
                model_checkpoint, 
                src_lang="en", 
                tgt_lang="ko"
            )
            _transliterator_model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)
            
            # 모델을 GPU로 이동 (가능한 경우)
            _transliterator_model = _transliterator_model.to(_transliterator_device)
            
            # 모델을 평가 모드로 설정 (드롭아웃 등 비활성화)
            _transliterator_model.eval()
            
            print("  모델 로딩 완료")
            
        except ImportError:
            print("경고: transformers 라이브러리가 설치되어 있지 않습니다.")
            print("      설치: pip install transformers torch")
            return term
        except Exception as e:
            print(f"경고: 모델 로딩 실패: {e}")
            return term
    
    # 변환 수행
    try:
        import torch  # torch.no_grad()를 위해 필요
        
        # 입력 토크나이징
        encoded_en = _transliterator_tokenizer(
            term, 
            truncation=True, 
            max_length=48, 
            return_tensors="pt"
        )
        
        # 입력 텐서를 GPU로 이동 (모델과 같은 디바이스)
        if _transliterator_device is not None:
            encoded_en = {k: v.to(_transliterator_device) for k, v in encoded_en.items()}
        
        # 생성 (추론 모드)
        with torch.no_grad():  # 그래디언트 계산 비활성화로 메모리 절약 및 속도 향상
            generated_tokens = _transliterator_model.generate(
                **encoded_en,
                max_new_tokens=48,
                num_beams=1,  # 빠른 추론을 위해 beam search 비활성화
                do_sample=False,  # 샘플링 비활성화로 속도 향상
            )
        
        # 디코딩
        result = _transliterator_tokenizer.batch_decode(
            generated_tokens, 
            skip_special_tokens=True
        )
        
        if result and len(result) > 0:
            return result[0].strip()
        else:
            return term
    except Exception as e:
        print(f"경고: 변환 실패 ({term}): {e}")
        return term