#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ByT5-small ARPABET → Korean 음차 변환 파인튜닝 스크립트
경량화된 ByT5-small 모델을 사용하여 ARPABET을 한글 음차로 변환합니다.
"""

import json
import os
import torch
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    T5ForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
)

# ========== 설정 ==========
MODEL_NAME = "google/byt5-small"  # 300M params (vs base 580M)
DATA_PATH = "./training_arpabet.json"
OUTPUT_DIR = "./models/byt5-small-arpabet2kor"
CHECKPOINT_DIR = "./checkpoints_small"

# 하이퍼파라미터 (small 모델에 맞게 조정)
LEARNING_RATE = 5e-5
BATCH_SIZE = 16  # small 모델은 메모리 여유 있음
GRADIENT_ACCUMULATION_STEPS = 2  # 실제 배치 32
NUM_EPOCHS = 10
MAX_INPUT_LENGTH = 256
MAX_TARGET_LENGTH = 64
WARMUP_RATIO = 0.1
EVAL_STEPS = 500
SAVE_STEPS = 500
LOGGING_STEPS = 100
MAX_GRAD_NORM = 1.0


def load_data(data_path: str) -> list[dict]:
    """데이터셋을 로드합니다."""
    print(f"Loading data: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} examples")
    return data


def prepare_datasets(examples: list[dict], test_size: float = 0.2, val_ratio: float = 0.5):
    """데이터를 학습/검증/테스트 세트로 분할합니다."""
    print("Splitting dataset...")
    
    train_data, temp_data = train_test_split(
        examples, test_size=test_size, random_state=42
    )
    
    val_data, test_data = train_test_split(
        temp_data, test_size=val_ratio, random_state=42
    )
    
    print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
    
    return (
        Dataset.from_list(train_data),
        Dataset.from_list(val_data),
        Dataset.from_list(test_data)
    )


def create_preprocess_function(tokenizer, max_input_length: int, max_target_length: int):
    """토큰화 함수를 생성합니다."""
    
    def preprocess_function(examples):
        inputs = tokenizer(
            examples["input_text"],
            max_length=max_input_length,
            truncation=True,
            padding="max_length"
        )
        
        targets = tokenizer(
            examples["target_text"],
            max_length=max_target_length,
            truncation=True,
            padding="max_length"
        )
        
        labels = []
        for label in targets["input_ids"]:
            labels.append([
                -100 if token == tokenizer.pad_token_id else token 
                for token in label
            ])
        
        inputs["labels"] = labels
        return inputs
    
    return preprocess_function


def main():
    print("=" * 60)
    print("ByT5-small ARPABET->Korean Fine-tuning")
    print("=" * 60)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("WARNING: GPU not available. Training on CPU.")
    
    # 1. 데이터 로드 및 분할
    examples = load_data(DATA_PATH)
    train_dataset, val_dataset, test_dataset = prepare_datasets(examples)
    
    # 테스트 데이터 저장
    test_dataset.to_json("./test_data_small.json")
    print("Test data saved: ./test_data_small.json")
    
    # 2. 모델 및 토크나이저 로드
    print(f"\nLoading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    
    print(f"Model parameters: {model.num_parameters():,}")
    
    # 3. 데이터 토큰화
    print("\nTokenizing data...")
    preprocess_fn = create_preprocess_function(
        tokenizer, MAX_INPUT_LENGTH, MAX_TARGET_LENGTH
    )
    
    tokenized_train = train_dataset.map(
        preprocess_fn, 
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="Tokenizing train data"
    )
    
    tokenized_val = val_dataset.map(
        preprocess_fn,
        batched=True,
        remove_columns=val_dataset.column_names,
        desc="Tokenizing val data"
    )
    
    # 4. Data Collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100
    )
    
    # 5. 학습 설정
    print("\nConfiguring training...")
    training_args = Seq2SeqTrainingArguments(
        output_dir=CHECKPOINT_DIR,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        num_train_epochs=NUM_EPOCHS,
        weight_decay=0.01,
        warmup_ratio=WARMUP_RATIO,
        max_grad_norm=MAX_GRAD_NORM,
        predict_with_generate=True,
        fp16=False,
        bf16=torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8,
        logging_steps=LOGGING_STEPS,
        logging_dir="./logs_small",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        save_total_limit=3,
        dataloader_num_workers=0,
    )
    
    # 6. Trainer 초기화
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    # 7. 학습 시작
    print("\n" + "=" * 60)
    print("Training started!")
    print("=" * 60)
    
    trainer.train()
    
    # 8. 최종 모델 저장
    print(f"\nSaving model to: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 9. 간단한 테스트
    print("\nQuick inference test:")
    test_arpabets = [
        ("B R UH1 K L IH0 N", "brooklyn"),
        ("M AY1 K R AH0 S AO2 F T", "microsoft"),
        ("S AY1 K AA1 L AH0 JH IY0", "psychology"),
        ("SH AE0 M P EY1 N", "champagne"),
    ]
    
    model.eval()
    model.to(device)
    
    for arpabet, original in test_arpabets:
        inputs = tokenizer(arpabet, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=MAX_TARGET_LENGTH,
                num_beams=4,
                early_stopping=True
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"  {original:15} ({arpabet[:30]:30}...) -> {result}")


if __name__ == "__main__":
    main()

