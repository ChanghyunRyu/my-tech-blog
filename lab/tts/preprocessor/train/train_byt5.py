#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ByT5 한영 음차 변환 파인튜닝 스크립트
영어 단어를 한글 음차로 변환하는 모델을 학습합니다.
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
MODEL_NAME = "google/byt5-base"
DATA_PATH = "./dataset/base_eng2kor_dict.json"
OUTPUT_DIR = "./models/byt5-eng2kor"
CHECKPOINT_DIR = "./checkpoints"

# 하이퍼파라미터
LEARNING_RATE = 5e-5  # 낮춤: ByT5는 낮은 학습률 필요
BATCH_SIZE = 8  # 줄임: 안정성 향상
GRADIENT_ACCUMULATION_STEPS = 4  # 실제 배치 크기 = 8 * 4 = 32
NUM_EPOCHS = 5  # 줄임: 과적합 방지
MAX_INPUT_LENGTH = 128  # 바이트 단위
MAX_TARGET_LENGTH = 64
WARMUP_RATIO = 0.1  # 전체 스텝의 10%를 warmup으로
EVAL_STEPS = 500
SAVE_STEPS = 500
LOGGING_STEPS = 100
MAX_GRAD_NORM = 1.0  # Gradient clipping

# Task prefix
TASK_PREFIX = "transliterate: "


def load_data(data_path: str) -> list[dict]:
    """Load dataset and convert to training format."""
    print(f"Loading data: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    examples = []
    for eng, kor in data.items():
        examples.append({
            "input_text": f"{TASK_PREFIX}{eng}",
            "target_text": kor
        })
    
    print(f"Loaded {len(examples)} examples")
    return examples


def prepare_datasets(examples: list[dict], test_size: float = 0.2, val_ratio: float = 0.5):
    """Split data into train/validation/test sets."""
    print("Splitting dataset...")
    
    # Train/temp split (8:2)
    train_data, temp_data = train_test_split(
        examples, test_size=test_size, random_state=42
    )
    
    # Temp to validation/test split (1:1)
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
    """Create tokenization function."""
    
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
        
        # labels에서 padding token을 -100으로 변경 (loss 계산에서 제외)
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
    print("ByT5 English-Korean Transliteration Fine-tuning")
    print("=" * 60)
    
    # GPU check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("WARNING: GPU not available. Training on CPU.")
    
    # 1. 데이터 로드 및 분할
    examples = load_data(DATA_PATH)
    train_dataset, val_dataset, test_dataset = prepare_datasets(examples)
    
    # Save test data for later evaluation
    test_dataset.to_json("./test_data.json")
    print("Test data saved: ./test_data.json")
    
    # 2. Load model and tokenizer
    print(f"\nLoading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    
    print(f"Model parameters: {model.num_parameters():,}")
    
    # 3. Tokenize data
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
    
    # 5. Training configuration
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
        warmup_ratio=WARMUP_RATIO,  # warmup_steps 대신 비율 사용
        max_grad_norm=MAX_GRAD_NORM,  # Gradient clipping
        predict_with_generate=True,
        fp16=False,  # FP16 비활성화 - 안정성 우선
        bf16=torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8,  # Ampere 이상만 bf16
        logging_steps=LOGGING_STEPS,
        logging_dir="./logs",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",  # wandb 등 비활성화
        save_total_limit=3,  # 최근 3개 체크포인트만 유지
        dataloader_num_workers=0,  # Windows 호환성
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
    
    # 7. Start training
    print("\n" + "=" * 60)
    print("Training started!")
    print("=" * 60)
    
    trainer.train()
    
    # 8. Save final model
    print(f"\nSaving model to: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 9. Quick inference test
    print("\nQuick inference test:")
    test_words = ["brooklyn", "microsoft", "tensorflow", "apple"]
    
    model.eval()
    model.to(device)
    
    for word in test_words:
        input_text = f"{TASK_PREFIX}{word}"
        inputs = tokenizer(input_text, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=MAX_TARGET_LENGTH,
                num_beams=4,
                early_stopping=True
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"  {word} → {result}")


if __name__ == "__main__":
    main()

