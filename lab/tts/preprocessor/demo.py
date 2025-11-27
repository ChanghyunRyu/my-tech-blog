import time
import normalizer

TEST_CASES = [
    "내일 morning meeting에서 새로운 API를 같이 리뷰할 예정입니다.",
    "임진왜란은 1592년에 발생했습니다.",
    "PyTorch 3차 세미나, Kaggle 2회 대회, AI Bootcamp 3기 모집, NLP 2학년 수업, Cloud 3호 라인",
    "Sprint 3일차 회고, Season 2분기 실적!",
    "제 전화번호는 010-2629-3115 입니다?"
]

for text in TEST_CASES:
    start_time = time.time()
    new_text = normalizer.trans_sentence(text)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    print(new_text)
    print("-"*100)