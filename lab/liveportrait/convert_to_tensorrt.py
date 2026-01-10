# coding: utf-8
"""
LivePortrait 모델을 ONNX로 변환하고 TensorRT 엔진으로 빌드하는 스크립트
FasterLivePortrait 가이드에 따라 구현
"""

import os
import sys
import torch
import numpy as np
import yaml
import onnx
import onnx.helper as helper

# LivePortrait 경로 추가
LIVEPORTRAIT_PATH = os.path.join(os.path.dirname(__file__), 'LivePortrait')
sys.path.insert(0, LIVEPORTRAIT_PATH)

from src.config.inference_config import InferenceConfig
from src.utils.helper import load_model


def export_model_to_onnx(model, dummy_input, output_path, input_names=None, output_names=None, dynamic_axes=None):
    """PyTorch 모델을 ONNX로 변환 (단일 파일로 저장)"""
    print(f"[INFO] Exporting model to ONNX: {output_path}")
    
    model.eval()
    with torch.no_grad():
        # motion_extractor는 딕셔너리를 반환하므로, 출력 이름을 명시적으로 지정
        if output_names is None:
            # 모델 타입에 따라 출력 이름 결정
            if 'motion_extractor' in output_path:
                output_names = ['pitch', 'yaw', 'roll', 't', 'exp', 'scale', 'kp']
            else:
                output_names = ['output']
        
        # 임시 파일로 먼저 저장
        temp_path = output_path + '.temp'
        torch.onnx.export(
            model,
            dummy_input,
            temp_path,
            input_names=input_names or ['input'],
            output_names=output_names,
            dynamic_axes=dynamic_axes,
            opset_version=18,  # TensorRT 10.x는 opset 18 지원
            do_constant_folding=True,
            export_params=True,
            verbose=False
        )
        
        # ONNX 모델을 로드하여 external data를 내부로 병합
        try:
            # External data를 포함하여 로드
            onnx_model = onnx.load(temp_path, load_external_data=True)
            
            # External data 경로 확인 및 병합
            external_data_dir = os.path.dirname(temp_path)
            if external_data_dir:
                # External data를 모델 내부로 로드
                onnx.load_external_data_for_model(onnx_model, external_data_dir)
            
            # 단일 파일로 저장 (external data 포함)
            onnx.save(onnx_model, output_path, save_as_external_data=False)
            
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # .onnx.data 파일도 삭제 (더 이상 필요 없음)
            data_path = temp_path + '.data'
            if os.path.exists(data_path):
                os.remove(data_path)
            
            print(f"[OK] ONNX model saved as single file: {output_path}")
        except Exception as e:
            print(f"[WARN] External data 병합 실패, 원본 파일 사용: {e}")
            import traceback
            traceback.print_exc()
            if os.path.exists(temp_path):
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_path, output_path)


def build_tensorrt_engine(onnx_path, engine_path, fp16=True, workspace_size=4096):
    """ONNX 모델을 TensorRT 엔진으로 변환"""
    try:
        import tensorrt as trt
    except ImportError:
        print("[ERROR] TensorRT가 설치되지 않았습니다.")
        print("설치 방법: pip install nvidia-tensorrt")
        return False
    
    print(f"[INFO] Building TensorRT engine from ONNX: {onnx_path}")
    
    # ONNX 모델 검증
    try:
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print("[INFO] ONNX 모델 검증 완료")
    except Exception as e:
        print(f"[WARN] ONNX 모델 검증 경고: {e}")
    
    # TensorRT 로거
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    
    # 네트워크 생성 (EXPLICIT_BATCH 플래그)
    network_flags = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(network_flags)
    parser = trt.OnnxParser(network, logger)
    
    # ONNX 파일 파싱
    with open(onnx_path, 'rb') as model_file:
        model_data = model_file.read()
        if not parser.parse(model_data):
            print("[ERROR] ONNX 파싱 실패:")
            for i in range(parser.num_errors):
                print(f"  Error {i}: {parser.get_error(i)}")
            return False
    
    print(f"[INFO] ONNX 파싱 완료: {len(network)} layers")
    
    # 빌더 설정
    config = builder.create_builder_config()
    
    # TensorRT 10.x API: memory_pool_limit 사용
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_size * (1 << 20))
    
    # FP16 활성화
    if fp16:
        if builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)
            print("[INFO] FP16 모드 활성화")
        else:
            print("[WARN] FP16이 이 플랫폼에서 지원되지 않습니다. FP32로 빌드합니다.")
    
    # INT8 최적화 (선택사항)
    # if builder.platform_has_fast_int8:
    #     config.set_flag(trt.BuilderFlag.INT8)
    
    # 엔진 빌드 (TensorRT 10.x API)
    print("[INFO] TensorRT 엔진 빌드 중... (시간이 걸릴 수 있습니다)")
    try:
        # TensorRT 10.x: build_serialized_network 사용
        serialized_engine = builder.build_serialized_network(network, config)
        
        if serialized_engine is None:
            print("[ERROR] TensorRT 엔진 빌드 실패 (serialized_engine is None)")
            return False
        
        # 엔진 저장
        with open(engine_path, 'wb') as f:
            f.write(serialized_engine)
            
    except AttributeError:
        # TensorRT 8.x/9.x: build_engine 사용
        try:
            engine = builder.build_engine(network, config)
            if engine is None:
                print("[ERROR] TensorRT 엔진 빌드 실패")
                return False
            with open(engine_path, 'wb') as f:
                f.write(engine.serialize())
        except Exception as e:
            print(f"[ERROR] TensorRT 엔진 빌드 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"[ERROR] TensorRT 엔진 빌드 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"[OK] TensorRT engine saved: {engine_path}")
    print(f"[INFO] 엔진 크기: {os.path.getsize(engine_path) / (1024*1024):.2f} MB")
    return True


def convert_liveportrait_models(pretrained_weights_path=None, output_dir=None):
    """LivePortrait의 모든 모델을 ONNX 및 TensorRT로 변환"""
    if pretrained_weights_path is None:
        pretrained_weights_path = os.path.join(os.path.dirname(__file__), 'pretrained_weights')
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'tensorrt_engines')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 변환 결과 추적
    conversion_results = {}
    
    # 설정 로드
    inference_cfg = InferenceConfig(
        checkpoint_F=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'appearance_feature_extractor.pth'),
        checkpoint_M=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'motion_extractor.pth'),
        checkpoint_G=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'spade_generator.pth'),
        checkpoint_W=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'warping_module.pth'),
        checkpoint_S=os.path.join(pretrained_weights_path, 'liveportrait', 'retargeting_models', 'stitching_retargeting_module.pth'),
    )
    
    model_config = yaml.load(open(inference_cfg.models_config, 'r'), Loader=yaml.SafeLoader)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"[INFO] Using device: {device}")
    print(f"[INFO] Output directory: {output_dir}")
    
    # 모델 정의 및 변환
    models_to_convert = [
        ('appearance_feature_extractor', inference_cfg.checkpoint_F, 'F'),
        ('motion_extractor', inference_cfg.checkpoint_M, 'M'),
        ('warping_module', inference_cfg.checkpoint_W, 'W'),
        ('spade_generator', inference_cfg.checkpoint_G, 'G'),
    ]
    
    # stitching_retargeting_module 서브모듈 변환
    stitching_modules_to_convert = []
    if inference_cfg.checkpoint_S and os.path.exists(inference_cfg.checkpoint_S):
        stitching_modules_to_convert = [
            ('stitching', 'stitching'),
            ('eye', 'eye'),
            ('lip', 'lip'),
        ]
    
    for model_name, checkpoint_path, model_type in models_to_convert:
        print(f"\n[INFO] Converting {model_name}...")
        
        # 모델 로드
        model = load_model(checkpoint_path, model_config, device, model_name)
        model.eval()
        
        # 더미 입력 생성 (모델 타입에 따라 다름)
        if model_type == 'F':  # Appearance Feature Extractor
            dummy_input = torch.randn(1, 3, 256, 256).to(device)
        elif model_type == 'M':  # Motion Extractor
            dummy_input = torch.randn(1, 3, 256, 256).to(device)
        elif model_type == 'W':  # Warping Module
            # 실제 입력은 더 복잡하지만, 변환을 위해 간단화
            dummy_input = (
                torch.randn(1, 32, 16, 64, 64).to(device),  # f_s
                torch.randn(1, 21, 3).to(device),  # x_s
                torch.randn(1, 21, 3).to(device),  # x_d
            )
        elif model_type == 'G':  # SPADE Generator
            dummy_input = torch.randn(1, 256, 64, 64).to(device)
        else:
            print(f"[WARN] Unknown model type: {model_type}, skipping...")
            continue
        
        # ONNX 변환
        onnx_path = os.path.join(output_dir, f"{model_name}.onnx")
        try:
            if model_type == 'W':
                # Warping Module은 여러 입력을 받으므로 다중 입력으로 변환
                print(f"[INFO] Converting {model_name} with multiple inputs...")
                input_names = ['feature_3d', 'kp_driving', 'kp_source']
                output_names = ['out', 'occlusion_map', 'deformation']
                
                # ONNX 변환 (다중 입력 지원)
                model.eval()
                with torch.no_grad():
                    temp_path = onnx_path + '.temp'
                    torch.onnx.export(
                        model,
                        dummy_input,
                        temp_path,
                        input_names=input_names,
                        output_names=output_names,
                        opset_version=18,
                        do_constant_folding=True,
                        export_params=True,
                        verbose=False
                    )
                    
                    # External data 병합
                    try:
                        onnx_model = onnx.load(temp_path, load_external_data=True)
                        external_data_dir = os.path.dirname(temp_path)
                        if external_data_dir:
                            onnx.load_external_data_for_model(onnx_model, external_data_dir)
                        onnx.save(onnx_model, onnx_path, save_as_external_data=False)
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        data_path = temp_path + '.data'
                        if os.path.exists(data_path):
                            os.remove(data_path)
                        print(f"[OK] ONNX model saved: {onnx_path}")
                    except Exception as e:
                        print(f"[WARN] External data 병합 실패: {e}")
                        if os.path.exists(temp_path):
                            if os.path.exists(onnx_path):
                                os.remove(onnx_path)
                            os.rename(temp_path, onnx_path)
                
                conversion_results[model_name] = 'onnx_created'
            else:
                # 출력 이름 지정 (motion_extractor는 딕셔너리 반환)
                output_names = None
                if model_type == 'M':  # Motion Extractor
                    output_names = ['pitch', 'yaw', 'roll', 't', 'exp', 'scale', 'kp']
                
                export_model_to_onnx(model, dummy_input, onnx_path, output_names=output_names)
                conversion_results[model_name] = 'onnx_created'
            
            # TensorRT 엔진 빌드
            engine_path = os.path.join(output_dir, f"{model_name}.engine")
            if build_tensorrt_engine(onnx_path, engine_path, fp16=True):
                print(f"[OK] {model_name} 변환 완료 (TensorRT 엔진 생성)")
                conversion_results[model_name] = 'tensorrt_created'
            else:
                print(f"[WARN] {model_name} TensorRT 엔진 빌드 실패 (ONNX는 생성됨)")
                conversion_results[model_name] = 'tensorrt_failed'
        except Exception as e:
            print(f"[ERROR] {model_name} 변환 중 오류: {e}")
            conversion_results[model_name] = 'failed'
            import traceback
            traceback.print_exc()
    
    # stitching_retargeting_module 서브모듈 변환
    if stitching_modules_to_convert:
        print("\n[INFO] Converting stitching_retargeting_module submodules...")
        stitching_config = model_config['model_params']['stitching_retargeting_module_params']
        checkpoint = torch.load(inference_cfg.checkpoint_S, map_location=lambda storage, loc: storage)
        
        from src.utils.helper import remove_ddp_dumplicate_key
        from src.modules.stitching_retargeting_network import StitchingRetargetingNetwork
        
        for submodule_name, config_key in stitching_modules_to_convert:
            print(f"\n[INFO] Converting stitching_retargeting_module.{submodule_name}...")
            try:
                # 모델 생성 및 로드
                config = stitching_config.get(config_key)
                if config is None:
                    print(f"[WARN] Config for {submodule_name} not found, skipping...")
                    continue
                
                model = StitchingRetargetingNetwork(**config).to(device)
                
                # 체크포인트 키 매핑
                checkpoint_key_map = {
                    'stitching': 'retarget_shoulder',
                    'eye': 'retarget_eye',
                    'lip': 'retarget_mouth',
                }
                checkpoint_key = checkpoint_key_map.get(submodule_name)
                if checkpoint_key is None:
                    print(f"[WARN] Checkpoint key for {submodule_name} not found, skipping...")
                    continue
                
                model.load_state_dict(remove_ddp_dumplicate_key(checkpoint[checkpoint_key]))
                model.eval()
                
                # 더미 입력 생성
                input_size = config['input_size']
                dummy_input = torch.randn(1, input_size).to(device)
                
                # ONNX 변환
                onnx_path = os.path.join(output_dir, f"stitching_{submodule_name}.onnx")
                export_model_to_onnx(
                    model, 
                    dummy_input, 
                    onnx_path,
                    input_names=['input'],
                    output_names=['output']
                )
                conversion_results[f'stitching_{submodule_name}'] = 'onnx_created'
                
                # TensorRT 엔진 빌드
                engine_path = os.path.join(output_dir, f"stitching_{submodule_name}.engine")
                if build_tensorrt_engine(onnx_path, engine_path, fp16=True):
                    print(f"[OK] stitching_{submodule_name} 변환 완료 (TensorRT 엔진 생성)")
                    conversion_results[f'stitching_{submodule_name}'] = 'tensorrt_created'
                else:
                    print(f"[WARN] stitching_{submodule_name} TensorRT 엔진 빌드 실패 (ONNX는 생성됨)")
                    conversion_results[f'stitching_{submodule_name}'] = 'tensorrt_failed'
                    
            except Exception as e:
                print(f"[ERROR] stitching_{submodule_name} 변환 중 오류: {e}")
                conversion_results[f'stitching_{submodule_name}'] = 'failed'
                import traceback
                traceback.print_exc()
    
    # 변환 결과 요약
    print("\n" + "="*60)
    print("변환 결과 요약")
    print("="*60)
    
    tensorrt_success = 0
    onnx_only = 0
    failed = 0
    skipped = 0
    
    all_models = [(name, None, None) for name, _, _ in models_to_convert]
    all_models.extend([(f'stitching_{name}', None, None) for name, _ in stitching_modules_to_convert])
    
    for model_name, _, _ in all_models:
        status = conversion_results.get(model_name, 'unknown')
        engine_path = os.path.join(output_dir, f"{model_name}.engine")
        onnx_path = os.path.join(output_dir, f"{model_name}.onnx")
        
        if status == 'tensorrt_created' or os.path.exists(engine_path):
            print(f"[OK] {model_name}: TensorRT 엔진 생성 완료")
            tensorrt_success += 1
        elif status == 'onnx_created' or os.path.exists(onnx_path):
            print(f"[WARN] {model_name}: ONNX만 생성됨 (TensorRT 엔진 빌드 필요)")
            onnx_only += 1
        elif status == 'skipped':
            print(f"[SKIP] {model_name}: 수동 변환 필요 (복잡한 입력 구조)")
            skipped += 1
        else:
            print(f"[ERROR] {model_name}: 변환 실패")
            failed += 1
    
    print("="*60)
    print(f"TensorRT 엔진: {tensorrt_success}개")
    print(f"ONNX만 생성: {onnx_only}개")
    print(f"건너뜀: {skipped}개")
    print(f"실패: {failed}개")
    print("="*60)
    
    if failed > 0:
        print("\n[WARN] 일부 모델 변환이 실패했습니다.")
        print("[INFO] 필요한 패키지 확인:")
        print("  - pip install onnxscript onnx")
        print("  - pip install nvidia-tensorrt (TensorRT 엔진 빌드용)")
    elif onnx_only > 0:
        print("\n[INFO] ONNX 모델은 생성되었지만 TensorRT 엔진 빌드가 필요합니다.")
        print("[INFO] TensorRT 설치: pip install nvidia-tensorrt")
        print("[INFO] 또는 trtexec 명령어로 수동 빌드 가능")
    elif tensorrt_success > 0:
        print("\n[OK] TensorRT 엔진이 생성되었습니다!")
        print("[INFO] 서버가 자동으로 TensorRT 모드를 사용합니다.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LivePortrait 모델을 TensorRT로 변환')
    parser.add_argument('--weights', type=str, default=None, help='Pretrained weights 경로')
    parser.add_argument('--output', type=str, default=None, help='출력 디렉토리')
    args = parser.parse_args()
    
    convert_liveportrait_models(args.weights, args.output)
