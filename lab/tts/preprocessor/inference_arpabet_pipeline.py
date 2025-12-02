#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
영어 → 한글 음차 변환 추론 파이프라인
영어 단어 → wordninja 분리 → G2P(ARPABET) → ByT5 모델 → 한글 음차
"""

import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration
from g2p_en import G2p
import wordninja


class Eng2KorTransliteratorPipeline:
    """영어-한글 음차 변환 파이프라인"""
    
    def __init__(
        self, 
        model_path: str = "./models/byt5-arpabet2kor",
        device: str = None,
        use_compound_split: bool = True
    ):
        """
        Args:
            model_path: 학습된 모델 경로
            device: 사용할 디바이스 ('cuda', 'cpu', 또는 None으로 자동 선택)
            use_compound_split: 합성어 분리 사용 여부
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_compound_split = use_compound_split
        
        print(f"Loading model: {model_path}")
        print(f"Device: {self.device}")
        
        # G2P 모델 로드
        print("Loading G2P model...")
        self.g2p = G2p()
        
        # ByT5 모델 로드
        print("Loading ByT5 model...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        print("Pipeline ready!")
    
    def split_compound(self, word: str) -> list[str]:
        """합성어를 분리합니다."""
        if not self.use_compound_split:
            return [word]
        
        # 이미 공백이 있으면 분리
        if ' ' in word:
            return word.split()
        
        parts = wordninja.split(word)
        
        # 너무 짧은 조각 방지
        if any(len(p) < 2 for p in parts):
            return [word]
        
        return parts
    
    def word_to_arpabet(self, word: str) -> str:
        """영어 단어를 ARPABET으로 변환합니다."""
        phonemes = self.g2p(word)
        return ' '.join(phonemes)
    
    def arpabet_to_korean(
        self, 
        arpabet: str, 
        num_beams: int = 4,
        max_length: int = 64
    ) -> str:
        """ARPABET을 한글로 변환합니다."""
        inputs = self.tokenizer(arpabet, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True
            )
        
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result
    
    def transliterate(
        self, 
        text: str, 
        num_beams: int = 4,
        max_length: int = 64,
        return_details: bool = False
    ) -> str | dict:
        """
        영어 단어/문구를 한글 음차로 변환합니다.
        
        Args:
            text: 변환할 영어 텍스트
            num_beams: 빔 서치 크기
            max_length: 최대 출력 길이
            return_details: 상세 정보 반환 여부
            
        Returns:
            한글 음차 변환 결과 (또는 상세 정보 딕셔너리)
        """
        text = text.lower().strip()
        
        # 1. 합성어 분리
        parts = self.split_compound(text)
        
        # 2. 각 파트를 ARPABET으로 변환
        arpabet_parts = []
        for part in parts:
            arpabet = self.word_to_arpabet(part)
            arpabet_parts.append(arpabet)
        
        # 3. 합성어면 [SEP]로 구분
        if len(arpabet_parts) > 1:
            arpabet_text = ' [SEP] '.join(arpabet_parts)
        else:
            arpabet_text = arpabet_parts[0]
        
        # 4. ARPABET을 한글로 변환
        korean = self.arpabet_to_korean(arpabet_text, num_beams, max_length)
        
        if return_details:
            return {
                "input": text,
                "parts": parts,
                "arpabet_parts": arpabet_parts,
                "arpabet": arpabet_text,
                "korean": korean,
                "is_compound": len(parts) > 1
            }
        
        return korean
    
    def transliterate_batch(
        self, 
        texts: list[str], 
        num_beams: int = 4,
        max_length: int = 64
    ) -> list[str]:
        """
        여러 영어 단어/문구를 일괄 변환합니다.
        """
        results = []
        for text in texts:
            result = self.transliterate(text, num_beams, max_length)
            results.append(result)
        return results


def main():
    """테스트 실행"""
    # 파이프라인 로드
    pipeline = Eng2KorTransliteratorPipeline()
    
    # 테스트 단어들
    test_words = [
        # 기본 단어
        "brooklyn",
        "microsoft",
        "apple",
        "google",
        # 묵음 테스트
        "psychology",
        "honest",
        "schedule",
        "queue",
        # 외래어
        "champagne",
        "croissant",
        "cafe",
        # 합성어
        "concerthall",
        "sunshine",
        "basketball",
        # 기타
        "transformer",
        "artificial",
        "machine",
    ]
    
    print("\n" + "=" * 70)
    print("English to Korean Transliteration Test")
    print("=" * 70)
    
    for word in test_words:
        details = pipeline.transliterate(word, return_details=True)
        
        compound_info = ""
        if details["is_compound"]:
            compound_info = f" (compound: {details['parts']})"
        
        print(f"{word:20} -> {details['korean']}{compound_info}")
        print(f"  ARPABET: {details['arpabet'][:50]}...")
        print()


if __name__ == "__main__":
    main()

