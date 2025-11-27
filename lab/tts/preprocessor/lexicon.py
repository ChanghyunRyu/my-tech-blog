# 순환 import 방지를 위해 함수는 나중에 초기화
_COUNTER_READER = None

def _get_counter_reader():
    """_COUNTER_READER 딕셔너리를 지연 초기화"""
    global _COUNTER_READER
    if _COUNTER_READER is None:
        from readutils import read_sino_kor, read_native_kor
        _COUNTER_READER = {
            "개": read_native_kor,
            "개월": read_sino_kor,
            "권": read_native_kor,
            "그램": read_sino_kor,
            "그루": read_native_kor,
            "근": read_native_kor,
            "냥": read_native_kor,
            "년": read_sino_kor,
            "다발": read_native_kor,
            "단": read_sino_kor,
            "달러": read_sino_kor,
            "대": read_native_kor,
            "덩이": read_native_kor,
            "도": read_sino_kor,
            "되": read_native_kor,
            "등": read_sino_kor,
            "리": read_sino_kor,
            "리터": read_sino_kor,
            "말": read_native_kor,
            "명": read_native_kor,
            "묶음": read_native_kor,
            "뭉치": read_native_kor,
            "미터": read_sino_kor,
            "번": read_sino_kor,
            "벌": read_native_kor,
            "봉지": read_native_kor,
            "분": read_sino_kor,
            "센티미터": read_sino_kor,
            "송이": read_native_kor,
            "승": read_sino_kor,
            "알": read_native_kor,
            "야드": read_sino_kor,
            "에이커": read_sino_kor,
            "엔": read_sino_kor,
            "원": read_sino_kor,
            "위": read_sino_kor,
            "위안": read_sino_kor,
            "유로": read_sino_kor,
            "인치": read_sino_kor,
            "일": read_sino_kor,
            "입방미터": read_sino_kor,
            "자루": read_native_kor,
            "작": read_native_kor,
            "제곱미터": read_sino_kor,
            "주": read_sino_kor,
            "줌": read_native_kor,
            "차": read_sino_kor,
            "채": read_native_kor,
            "초": read_sino_kor,
            "킬로그램": read_sino_kor,
            "톤": read_sino_kor,
            "톳": read_native_kor,
            "통": read_native_kor,
            "파운드": read_sino_kor,
            "퍼센트": read_sino_kor,
            "평": read_sino_kor,
            "포기": read_native_kor,
            "푼": read_native_kor,
            "피트": read_sino_kor,
            "헥타르": read_sino_kor,
            "호": read_sino_kor,
            "홉": read_native_kor,
            "회": read_sino_kor
        }
    return _COUNTER_READER


_SINO_DIGITS = {
    0: "",
    1: "일",
    2: "이",
    3: "삼",
    4: "사",
    5: "오",
    6: "육",
    7: "칠",
    8: "팔",
    9: "구",
}
_SINO_SMALL_UNITS = ["", "십", "백", "천"]  # 1, 10, 100, 1000
_SINO_BIG_UNITS = ["", "만", "억", "조", "경"]  # 10^4, 10^8 ...

_NATIVE_ONES = {
    1: "한",
    2: "두",
    3: "세",
    4: "네",
    5: "다섯",
    6: "여섯",
    7: "일곱",
    8: "여덟",
    9: "아홉",
}

_NATIVE_TENS = {
    1: "열",    # 10, 11~19는 '열한', '열두', ...
    2: "스물",  # 20
    3: "서른",  # 30
    4: "마흔",  # 40
    5: "쉰",    # 50
    6: "예순",  # 60
    7: "일흔",  # 70
    8: "여든",  # 80
    9: "아흔",  # 90
}

# 0~9 (단독 숫자 / 20~99의 1의 자리 등)
ENG_NUM_0 = (
    "",          # 0 자리 (사용 안 함, 필요시 "제로"는 함수에서 처리)
    "원",        # 1
    "투",        # 2
    "쓰리",      # 3
    "포",        # 4
    "파이브",    # 5
    "식스",      # 6
    "세븐",      # 7
    "에잇",      # 8
    "나인",      # 9
)

# 10, 20, 30, ..., 90 (십의 자리)
# index 0 → 10, index 1 → 20, ...
ENG_NUM_TENS = (
    "텐",        # 10
    "트웬티",    # 20
    "써티",      # 30
    "포티",      # 40
    "피프티",    # 50
    "식스티",    # 60
    "세븐티",    # 70
    "에잇티",    # 80
    "나인티",    # 90
)

# 11~19 (teen numbers)
# index 1 → 11, index 2 → 12, ...
ENG_NUM_TEEN = (
    "",          # 0: 사용 안 함
    "일레븐",    # 11
    "투웰브",    # 12
    "써틴",      # 13
    "포틴",      # 14
    "피프틴",    # 15
    "식스틴",    # 16
    "세븐틴",    # 17
    "에잇틴",    # 18
    "나인틴",    # 19
)

# 각 자리수를 개별적으로 읽을 때(예: 123 → 원투쓰리)
ENG_NUM_READ_PER_DIGIT = (
    "오",        # 0 → 보통 '오(알파벳 O)' 식으로 읽을 때 사용
    "원",
    "투",
    "쓰리",
    "포",
    "파이브",
    "식스",
    "세븐",
    "에잇",
    "나인",
)


symbols = ['@', '#', '*', '(', ')', '+', '-', ';', ':', '/', '=', '&', '_', "'", '"']
sym_kor = ['골뱅이', '샵', '별표', '괄호열고', '괄호닫고', '더하기', '다시', '세미콜론', '땡땡', '짝대기', '는', '그리고', '밑줄', '따옴표', '쌍따옴표']
sym_eng = ['앳', '넘버', '스타', '괄호열고', '괄호닫고', '플러스', '대쉬', '세미콜론', '콜론', '슬래쉬', '이퀄스', '앤드', '언더바', '어퍼스트로피', '쌍따옴표']
count_symbols = ['$', '￦', '￡', '￥', '€', '℃', '%']
count_sym_kor = ['달러', '원', '파운드', '엔', '유로', '도씨', '퍼센트']