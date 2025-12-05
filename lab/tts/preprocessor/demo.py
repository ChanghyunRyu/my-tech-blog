import time
import normalizer

TEST_CASES = [
    "요즘 제 취향은 cozy한 분위기의 카페예요.",
    "친구가 갑자기 “don’t overthink it”이라고 해줬어요.",
    "오늘 outfit은 casual하게 입었습니다.",
    "그 영화 ending이 너무 anticlimactic했어요.",
    "이번 주말엔 short trip 다녀올 예정입니다.",
    "그 사람 vibe가 생각보다 chill하더라고요.",
    "평소에는 black coffee만 마십니다.",
    "meeting 분위기가 너무 awkward했어요.",
    "그 문장은 tone이 조금 aggressive해요.",
    "저는 spicy food를 정말 좋아해요.",
    "playlist에 새로 올라온 indie track 추천해줘.",
    "오늘 너무 exhausted해서 아무것도 하기 싫어요.",
    "그 말투는 좀 passive aggressive로 들립니다.",
    "운동 루틴은 mostly cardio 위주예요.",
    "오늘 weather가 surprisingly warm하네요.",
    "이 가방 design이 미니멀해서 마음에 들어요.",
    "그 드라마 pacing이 너무 fast예요.",
    "오늘 강아지가 hyperactive해서 힘들었어요.",
    "이 식당 portion이 생각보다 generous합니다.",
    "그 앱 UI가 super intuitive해요.",
    "오늘 outfit이 너무 overdressed였나?",
    "그 친구는 tiny details도 잘 챙겨요.",
    "모임 분위기가 overall peaceful했어요.",
    "그 가수 live performance가 훨씬 좋아요.",
    "오늘 mood는 그냥 low energy입니다.",
    "새로 산 노트북 keyboard가 surprisingly soft예요.",
    "이 향수 scent가 너무 synthetic합니다.",
    "그 학생 attitude가 매우 positive합니다.",
    "제 방 lighting이 너무 dim해서 바꿀 예정입니다.",
    "이번 trip은 정말 unforgettable experience예요.",
    "그 사진 composition이 꽤 artistic합니다.",
    "오늘 haircut이 surprisingly 잘 나왔어요.",
    "그 식당 service가 professional하고 친절해요.",
    "이 책 narrative가 smooth해서 읽기 좋아요.",
    "오늘 하루가 mentally draining했습니다.",
    "그분 personality가 굉장히 laid-back이에요.",
    "오늘 저녁 menu는 simple하게 salad로 했습니다.",
    "그 브랜드 quality가 consistent해서 좋아요.",
    "카페 music이 너무 loud해서 집중이 안 돼요.",
    "오늘 lecture가 fully interactive해서 좋았어요.",
    "그 친구의 humor가 아주 sarcastic해요.",
    "오늘 exercise intensity가 좀 high였습니다.",
    "그 영화 plot twist는 예측 불가였어요.",
    "지하철 vibe가 너무 chaotic했습니다.",
    "오늘 dinner portion이 slightly 부족했어요.",
    "그 옷 fabric이 surprisingly durable합니다.",
    "요즘 제 hobby는 journaling입니다.",
    "오늘 conversation flow가 아주 natural했어요.",
    "그 장소 atmosphere가 calming해서 좋았어요.",
    "오늘 hairstyle이 너무 messy하네요.",
    "그분 feedback이 incredibly helpful했어요.",
    "이 사진 color grading이 훌륭합니다.",
    "오늘 schedule이 fully booked입니다.",
    "그 식당 ambience가 정말 cozy해요.",
    "그 표현이 너무 outdated해서 잘 안 써요.",
    "오늘 감정이 slightly overwhelming합니다.",
    "저는 usually minimalistic 스타일을 좋아해요.",
    "그 커피 aftertaste가 정말 smooth하네요."
]


for text in TEST_CASES:
    start_time = time.time()
    new_text = normalizer.trans_sentence(text)

    end_time = time.time()
    print('original:{}'.format(text))
    print('normalized:{}'.format(new_text))
    print(f"Time taken: {end_time - start_time} seconds")
    print("-"*100)