#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ByT5 한영 음차 변환 추론 스크립트
학습된 모델을 사용하여 영어 단어를 한글 음차로 변환합니다.
"""

import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration


class Eng2KorTransliterator:
    """영어-한글 음차 변환기"""
    
    def __init__(self, model_path: str = "./models/byt5-eng2kor", device: str = None):
        """
        Args:
            model_path: 학습된 모델 경로
            device: 사용할 디바이스 ('cuda', 'cpu', 또는 None으로 자동 선택)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.task_prefix = "transliterate: "
        
        print(f"모델 로드 중: {model_path}")
        print(f"디바이스: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        print("모델 로드 완료!")
    
    def transliterate(
        self, 
        text: str, 
        num_beams: int = 4,
        max_length: int = 64
    ) -> str:
        """
        영어 단어/문구를 한글 음차로 변환합니다.
        
        Args:
            text: 변환할 영어 텍스트
            num_beams: 빔 서치 크기 (클수록 정확하지만 느림)
            max_length: 최대 출력 길이
            
        Returns:
            한글 음차 변환 결과
        """
        input_text = f"{self.task_prefix}{text.lower()}"
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True
            )
        
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result
    
    def transliterate_batch(
        self, 
        texts: list[str], 
        num_beams: int = 4,
        max_length: int = 64,
        batch_size: int = 32
    ) -> list[str]:
        """
        여러 영어 단어/문구를 일괄 변환합니다.
        
        Args:
            texts: 변환할 영어 텍스트 리스트
            num_beams: 빔 서치 크기
            max_length: 최대 출력 길이
            batch_size: 배치 크기
            
        Returns:
            한글 음차 변환 결과 리스트
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            input_texts = [f"{self.task_prefix}{t.lower()}" for t in batch]
            
            inputs = self.tokenizer(
                input_texts, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True
                )
            
            batch_results = self.tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )
            results.extend(batch_results)
        
        return results


def main():
    """테스트 실행"""
    # 모델 로드
    transliterator = Eng2KorTransliterator()
    
    # 테스트 단어들
    test_words = [
        "brooklyn",
        "microsoft",
        "tensorflow",
        "apple",
        "google",
        "starbucks",
        "mcdonalds",
        "california",
        "manhattan",
        "transformer",
        "artificial intelligence",
        "machine learning",
    ]
    
    print("\n" + "=" * 50)
    print("음차 변환 테스트")
    print("=" * 50)
    
    for word in test_words:
        result = transliterator.transliterate(word)
        print(f"{word:30} → {result}")
    
    print("\n" + "=" * 50)
    print("배치 변환 테스트")
    print("=" * 50)
    
    results = transliterator.transliterate_batch(test_words)
    for word, result in zip(test_words, results):
        print(f"{word:30} → {result}")


if __name__ == "__main__":
    main()

