"""
데이터셋 총 길이 체크
"""
import soundfile as sf
from pathlib import Path
import csv

DATASET_DIR = Path("dataset")
METADATA_FILE = DATASET_DIR / "metadata.csv"
WAVS_DIR = DATASET_DIR / "wavs"

def check_duration():
    print("=" * 60)
    print("데이터셋 총 길이 계산 중...")
    print("=" * 60)
    
    if not METADATA_FILE.exists():
        print(f"❌ {METADATA_FILE} 파일을 찾을 수 없습니다.")
        return
    
    total_duration = 0
    valid_count = 0
    error_count = 0
    
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='|')
        next(reader)  # 헤더 스킵
        
        for i, row in enumerate(reader, 1):
            if len(row) < 2:
                continue
            
            audio_file = row[0]
            audio_path = DATASET_DIR / audio_file
            
            if not audio_path.exists():
                error_count += 1
                continue
            
            try:
                info = sf.info(audio_path)
                duration = info.duration
                total_duration += duration
                valid_count += 1
                
                # 진행상황 표시 (100개마다)
                if valid_count % 100 == 0:
                    print(f"  처리 중... {valid_count}개 완료 ({total_duration/60:.1f}분)")
                    
            except Exception as e:
                error_count += 1
                print(f"  오류: {audio_file} - {e}")
    
    print("\n" + "=" * 60)
    print("📊 데이터셋 통계")
    print("=" * 60)
    print(f"✅ 유효한 샘플: {valid_count}개")
    if error_count > 0:
        print(f"❌ 오류 샘플: {error_count}개")
    print(f"\n⏱️  총 길이: {total_duration:.0f}초")
    print(f"⏱️  총 길이: {total_duration/60:.2f}분")
    print(f"⏱️  총 길이: {total_duration/3600:.2f}시간")
    print(f"\n📈 평균 길이: {total_duration/valid_count:.2f}초/샘플")
    print("=" * 60)
    
    # 훈련 예상 시간
    print("\n💡 예상 훈련 시간:")
    print(f"  - 10 epochs: 약 {valid_count * 10 * 0.2 / 60:.0f}분")
    print(f"  - 20 epochs: 약 {valid_count * 20 * 0.2 / 60:.0f}분")
    print(f"  - 30 epochs: 약 {valid_count * 30 * 0.2 / 60:.0f}분")
    print("=" * 60)

if __name__ == "__main__":
    check_duration()

