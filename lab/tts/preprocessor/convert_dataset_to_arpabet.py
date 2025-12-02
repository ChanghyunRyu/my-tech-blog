#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터셋을 ARPABET 형식으로 변환하는 스크립트
영어 단어 → ARPABET 발음기호로 변환하여 새로운 데이터셋 생성
"""

import json
import os
from tqdm import tqdm
from g2p_en import G2p
import wordninja

# G2P 모델 초기화
g2p = G2p()


def split_compound_word(word: str) -> list[str]:
    """
    합성어를 분리합니다.
    예: "concerthall" → ["concert", "hall"]
    """
    # 이미 공백이 있으면 그대로 분리
    if ' ' in word:
        return word.split()
    
    # wordninja로 합성어 분리
    parts = wordninja.split(word)
    
    # 분리 결과가 원본과 같으면 (분리 안됨) 그대로 반환
    if len(parts) == 1:
        return parts
    
    # 너무 짧은 조각은 합성어 분리 실패로 간주
    # 예: "the" → ["t", "he"] 같은 잘못된 분리 방지
    if any(len(p) < 2 for p in parts):
        return [word]
    
    return parts


def word_to_arpabet(word: str) -> str:
    """
    영어 단어를 ARPABET 발음기호로 변환합니다.
    예: "psychology" → "S AY1 K AA1 L AH0 JH IY0"
    """
    phonemes = g2p(word)
    # 리스트를 공백으로 연결
    return ' '.join(phonemes)


def process_entry(eng_word: str, kor_word: str) -> dict:
    """
    하나의 영어-한글 쌍을 처리합니다.
    합성어 분리 → ARPABET 변환
    """
    # 1. 합성어 분리
    parts = split_compound_word(eng_word.lower())
    
    # 2. 각 파트를 ARPABET으로 변환
    arpabet_parts = []
    for part in parts:
        arpabet = word_to_arpabet(part)
        arpabet_parts.append(arpabet)
    
    # 3. 합성어면 [SEP]로 구분, 아니면 그대로
    if len(arpabet_parts) > 1:
        arpabet_text = ' [SEP] '.join(arpabet_parts)
    else:
        arpabet_text = arpabet_parts[0]
    
    return {
        "original_word": eng_word,
        "arpabet": arpabet_text,
        "korean": kor_word,
        "is_compound": len(parts) > 1,
        "parts": parts
    }


def convert_dataset(input_path: str, output_path: str):
    """
    전체 데이터셋을 변환합니다.
    """
    print(f"Loading dataset: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total entries: {len(data)}")
    print("Converting to ARPABET format...")
    
    converted_data = []
    failed_entries = []
    
    for eng_word, kor_word in tqdm(data.items(), desc="Converting"):
        try:
            entry = process_entry(eng_word, kor_word)
            converted_data.append(entry)
        except Exception as e:
            failed_entries.append({
                "word": eng_word,
                "error": str(e)
            })
    
    # 결과 저장
    print(f"\nSuccessfully converted: {len(converted_data)}")
    print(f"Failed: {len(failed_entries)}")
    
    # 변환된 데이터 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to: {output_path}")
    
    # 실패한 항목 저장 (있으면)
    if failed_entries:
        failed_path = output_path.replace('.json', '_failed.json')
        with open(failed_path, 'w', encoding='utf-8') as f:
            json.dump(failed_entries, f, ensure_ascii=False, indent=2)
        print(f"Failed entries saved to: {failed_path}")
    
    # 샘플 출력
    print("\n" + "=" * 60)
    print("Sample conversions:")
    print("=" * 60)
    for i, entry in enumerate(converted_data[:10]):
        print(f"{entry['original_word']:20} → {entry['arpabet'][:40]:40} → {entry['korean']}")
        if entry['is_compound']:
            print(f"  (compound: {entry['parts']})")
    
    return converted_data


def create_training_dataset(converted_data: list, output_path: str):
    """
    학습용 데이터셋 생성 (input_text, target_text 형식)
    """
    training_data = []
    
    for entry in converted_data:
        training_data.append({
            "input_text": entry["arpabet"],
            "target_text": entry["korean"]
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print(f"Training dataset saved to: {output_path}")
    return training_data


if __name__ == "__main__":
    # 경로 설정
    INPUT_PATH = "./dataset/base_eng2kor_dict.json"
    CONVERTED_PATH = "./dataset/base_eng2kor_arpabet.json"
    TRAINING_PATH = "./dataset/training_arpabet.json"
    
    # 1. 데이터셋 변환
    converted_data = convert_dataset(INPUT_PATH, CONVERTED_PATH)
    
    # 2. 학습용 데이터셋 생성
    create_training_dataset(converted_data, TRAINING_PATH)
    
    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)

