"""
mecab 사전에서 NNBC(수사+단위명사)로 분류되는 단어들을 추출하는 스크립트

사용 방법:
    python extract_nnbc.py

출력:
    - 콘솔에 NNBC 단어 목록 출력
    - nnbc_words.txt 파일에 저장
"""
import os
import sys
from pathlib import Path

def find_mecab_dic_files():
    """mecab 사전 파일을 찾는 함수"""
    import site
    
    possible_paths = []
    
    # site-packages에서 찾기
    for site_path in site.getsitepackages():
        # mecab-ko-dic 관련 디렉토리 찾기
        for root, dirs, files in os.walk(site_path):
            if 'mecab' in root.lower() or 'dic' in root.lower():
                for file in files:
                    if file.endswith('.csv') or file.endswith('.dic') or 'user' in file.lower():
                        possible_paths.append(os.path.join(root, file))
    
    return possible_paths

def parse_mecab_dic_file(file_path):
    """mecab 사전 파일을 파싱하여 NNBC 단어 추출"""
    nnbc_words = set()
    
    # 여러 인코딩 시도
    encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # mecab 사전 파일 형식: 표면형,왼쪽문맥ID,오른쪽문맥ID,비용,품사,...
                    parts = line.split(',')
                    if len(parts) >= 5:
                        surface = parts[0]
                        pos = parts[4]  # 품사 필드
                        
                        if pos == 'NNBC':
                            nnbc_words.add(surface)
            
            if nnbc_words:
                break  # 성공하면 중단
        except Exception as e:
            continue  # 다음 인코딩 시도
    
    return nnbc_words

def extract_nnbc_from_mecab():
    """mecab을 사용하여 실제 분석 결과에서 NNBC 단어 수집"""
    nnbc_words = set()
    
    try:
        from mecab_ko import Tagger
        tagger = Tagger()
        
        # 일반적인 단위명사들을 테스트
        # 숫자와 단위를 조합하여 테스트
        units = [
            # 개수 단위
            '개', '명', '장', '권', '대', '마리', '벌', '채', '통', '줄', '줌', '푼',
            '그루', '송이', '포기', '자루', '봉지', '박스', '팩', '세트', '케이스',
            '단', '묶음', '다발', '뭉치', '덩이', '톳', '알', '낱개',
            # 시간 단위
            '초', '분', '시간', '일', '주', '개월', '년', '달', '세기',
            # 길이 단위
            'mm', 'cm', 'm', 'km', '미터', '센티미터', '킬로미터', '인치', '피트', '야드',
            # 무게 단위
            'g', 'kg', '그램', '킬로그램', '톤', '근', '냥', '돈',
            # 부피 단위
            'ml', '리터', 'cc', '되', '말', '홉', '작', '승',
            # 면적 단위
            '평', '제곱미터', '헥타르', '에이커',
            # 화폐 단위
            '원', '달러', '엔', '위안', '유로', '파운드',
            # 기타
            '층', '호', '번', '회', '차', '등', '위', '급', '단계', '단계',
            '도', '퍼센트', '%', '배', '절', '할', '푼', '리',
            '평방미터', '입방미터', '평방킬로미터',
        ]
        
        # 각 단위에 대해 여러 숫자 조합 테스트
        test_numbers = ['1', '2', '3', '4', '5', '10', '100', '1000']
        test_cases = []
        for unit in units:
            test_text = ' '.join([f"{num}{unit}" for num in test_numbers])
            test_cases.append(test_text)
        
        for test_text in test_cases:
            result = tagger.parse(test_text)
            for line in result.strip().split('\n'):
                if line == 'EOS':
                    break
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        features = parts[1].split(',')
                        if len(features) > 0 and features[0] == 'NNBC':
                            nnbc_words.add(word)
        
    except Exception as e:
        print(f"mecab 분석 오류: {e}")
    
    return nnbc_words

def main():
    """메인 함수"""
    print("NNBC 단어 추출 중...")
    
    # 방법 1: mecab 사전 파일에서 직접 추출
    dic_files = find_mecab_dic_files()
    nnbc_from_dic = set()
    
    if dic_files:
        print(f"\n발견된 사전 파일: {len(dic_files)}개")
        for dic_file in dic_files[:5]:  # 처음 5개만 시도
            print(f"  - {dic_file}")
            words = parse_mecab_dic_file(dic_file)
            nnbc_from_dic.update(words)
            if words:
                print(f"    → {len(words)}개 NNBC 단어 발견")
    else:
        print("\n사전 파일을 찾을 수 없습니다. mecab 분석 결과를 사용합니다.")
    
    # 방법 2: mecab 분석 결과에서 추출
    nnbc_from_analysis = extract_nnbc_from_mecab()
    
    # 두 방법 결과 합치기
    all_nnbc_words = nnbc_from_dic | nnbc_from_analysis
    
    # 정렬
    sorted_words = sorted(all_nnbc_words)
    
    # 결과 출력
    print(f"\n총 {len(sorted_words)}개의 NNBC 단어를 찾았습니다:")
    print("-" * 50)
    for word in sorted_words:
        print(word)
    
    # 파일로 저장
    output_file = Path(__file__).parent / 'nnbc_words.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in sorted_words:
            f.write(word + '\n')
    
    print(f"\n결과가 '{output_file}'에 저장되었습니다.")
    
    return sorted_words

if __name__ == '__main__':
    main()

