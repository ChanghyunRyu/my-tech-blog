# coding: utf-8
"""
LivePortrait Frame Generator (TensorRT 전용)
정적 이미지에서 표정이 변화하는 프레임들을 생성하는 모듈
PyTorch 의존성 완전 제거, TensorRT만 사용
"""

import os
import sys
import cv2
import numpy as np
import torch
import tensorrt as trt

# CUDA 최적화 설정
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# LivePortrait 경로 추가
LIVEPORTRAIT_PATH = os.path.join(os.path.dirname(__file__), 'LivePortrait')
sys.path.insert(0, LIVEPORTRAIT_PATH)

from src.config.crop_config import CropConfig
from src.utils.cropper import Cropper
from src.utils.camera import get_rotation_matrix, headpose_pred_to_degree
from src.utils.io import load_image_rgb
from src.utils.crop import prepare_paste_back, paste_back
from src.utils.retargeting_utils import calc_eye_close_ratio, calc_lip_close_ratio


class TensorRTInference:
    """TensorRT 엔진을 사용한 추론 클래스 (다중 입력/출력 지원)"""
    
    def __init__(self, engine_path, device='cuda:0'):
        self.device = torch.device(device)
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.runtime = trt.Runtime(self.logger)
        
        # 엔진 로드
        with open(engine_path, 'rb') as f:
            engine_data = f.read()
        self.engine = self.runtime.deserialize_cuda_engine(engine_data)
        self.context = self.engine.create_execution_context()
        
        # 텐서 정보 저장
        self.input_names = []
        self.output_names = []
        self.input_shapes = {}
        self.output_shapes = {}
        
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            shape = tuple(self.engine.get_tensor_shape(name)) if self.engine.get_tensor_shape(name) else (1,)
            mode = self.engine.get_tensor_mode(name)
            
            if mode == trt.TensorIOMode.INPUT:
                self.input_names.append(name)
                self.input_shapes[name] = shape
            else:
                self.output_names.append(name)
                self.output_shapes[name] = shape
    
    def _validate_tensor(self, tensor, name="tensor"):
        """텐서 검증 (NaN/Inf 체크)"""
        if isinstance(tensor, torch.Tensor):
            if torch.any(torch.isnan(tensor)) or torch.any(torch.isinf(tensor)):
                print(f"[WARN] NaN/Inf detected in {name}, replacing with 0")
                tensor = torch.nan_to_num(tensor, nan=0.0, posinf=1.0, neginf=0.0)
        return tensor
    
    def infer(self, input_tensors):
        """
        추론 실행 (단일 또는 다중 입력 지원)
        Args:
            input_tensors: torch.Tensor 또는 tuple/list of torch.Tensor (GPU에 있어야 함)
        Returns:
            output_tensor: torch.Tensor 또는 dict (GPU에 있음)
        """
        # 입력 정규화
        if isinstance(input_tensors, (tuple, list)):
            # 다중 입력
            input_list = list(input_tensors)
        else:
            # 단일 입력
            input_list = [input_tensors]
        
        # 입력 검증 및 디바이스 이동
        for i, inp in enumerate(input_list):
            if not isinstance(inp, torch.Tensor):
                raise TypeError(f"Input {i} must be torch.Tensor, got {type(inp)}")
            inp = self._validate_tensor(inp, f"input_{i}")
            if inp.device != self.device:
                inp = inp.to(self.device)
            input_list[i] = inp
        
        # 입력 텐서 주소 설정
        for i, input_name in enumerate(self.input_names):
            if i < len(input_list):
                self.context.set_tensor_address(input_name, input_list[i].data_ptr())
            else:
                raise ValueError(f"Not enough inputs provided. Expected {len(self.input_names)}, got {len(input_list)}")
        
        # 출력 텐서 할당
        if len(self.output_names) == 1:
            # 단일 출력
            output_name = self.output_names[0]
            output_shape = self.output_shapes[output_name]
            output_tensor = torch.empty(
                output_shape,
                dtype=torch.float32,
                device=self.device
            )
            self.context.set_tensor_address(output_name, output_tensor.data_ptr())
            
            # 실행
            self.context.execute_async_v3(stream_handle=0)
            torch.cuda.synchronize()
            
            # 출력 검증
            output_tensor = self._validate_tensor(output_tensor, "output")
            return output_tensor
        else:
            # 다중 출력
            output_tensors = {}
            for output_name in self.output_names:
                output_shape = self.output_shapes[output_name]
                output_tensors[output_name] = torch.empty(
                    output_shape,
                    dtype=torch.float32,
                    device=self.device
                )
                self.context.set_tensor_address(output_name, output_tensors[output_name].data_ptr())
            
            # 실행
            self.context.execute_async_v3(stream_handle=0)
            torch.cuda.synchronize()
            
            # 출력 검증
            for name, tensor in output_tensors.items():
                output_tensors[name] = self._validate_tensor(tensor, f"output_{name}")
            
            return output_tensors


class FrameGenerator:
    """LivePortrait 모델을 래핑하여 표정 프레임을 생성하는 클래스 (TensorRT 전용)"""
    
    def __init__(self, pretrained_weights_path: str = None, device: str = 'auto'):
        """
        Args:
            pretrained_weights_path: pretrained weights 경로 (마스크 등에 사용, None이면 기본 경로 사용)
            device: 'cuda', 'cpu', 또는 'auto' (자동 감지)
        """
        if pretrained_weights_path is None:
            pretrained_weights_path = os.path.join(os.path.dirname(__file__), 'pretrained_weights')
        
        # GPU 호환성 확인
        if device == 'auto':
            if torch.cuda.is_available():
                try:
                    test_tensor = torch.zeros(1).cuda()
                    _ = test_tensor + 1
                    device = 'cuda'
                except RuntimeError as e:
                    print(f"[WARN] CUDA not compatible, falling back to CPU: {e}")
                    device = 'cpu'
            else:
                device = 'cpu'
        
        print(f"[INFO] Using device: {device}")
        self.device = torch.device(device)
        
        # TensorRT 엔진 경로
        engines_dir = os.path.join(os.path.dirname(__file__), 'tensorrt_engines')
        
        # TensorRT 모델 로드 (모든 모델 필수)
        print("[TensorRT] 모델 로드 중...")
        
        # 1. Appearance Feature Extractor
        appearance_engine = os.path.join(engines_dir, 'appearance_feature_extractor.engine')
        if not os.path.exists(appearance_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {appearance_engine}")
        self.appearance_model = TensorRTInference(appearance_engine, device)
        print(f"[OK] appearance_feature_extractor 로드 완료")
        
        # 2. Motion Extractor
        motion_engine = os.path.join(engines_dir, 'motion_extractor.engine')
        if not os.path.exists(motion_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {motion_engine}")
        self.motion_model = TensorRTInference(motion_engine, device)
        print(f"[OK] motion_extractor 로드 완료")
        
        # 3. Warping Module (PyTorch - GridSample 5D 입력 문제로 TensorRT 변환 불가)
        # warping_module은 5D 입력(feature_3d: Bx32x16x64x64)을 사용하는 GridSample 때문에
        # TensorRT 변환이 어려우므로 PyTorch로 유지
        print("[PyTorch] warping_module 로드 중...")
        from src.config.inference_config import InferenceConfig
        from src.utils.helper import load_model
        import yaml
        
        pretrained_weights_path = pretrained_weights_path or os.path.join(os.path.dirname(__file__), 'pretrained_weights')
        inference_cfg = InferenceConfig(
            checkpoint_W=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'warping_module.pth'),
        )
        model_config = yaml.load(open(inference_cfg.models_config, 'r'), Loader=yaml.SafeLoader)
        self.warping_module = load_model(
            inference_cfg.checkpoint_W,
            model_config,
            str(self.device),
            'warping_module'
        )
        print(f"[OK] warping_module 로드 완료 (PyTorch)")
        
        # 4. SPADE Generator
        spade_engine = os.path.join(engines_dir, 'spade_generator.engine')
        if not os.path.exists(spade_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {spade_engine}")
        self.spade_model = TensorRTInference(spade_engine, device)
        print(f"[OK] spade_generator 로드 완료")
        
        # 5. Stitching Retargeting Modules (3개 서브모듈)
        stitching_stitching_engine = os.path.join(engines_dir, 'stitching_stitching.engine')
        stitching_eye_engine = os.path.join(engines_dir, 'stitching_eye.engine')
        stitching_lip_engine = os.path.join(engines_dir, 'stitching_lip.engine')
        
        if not os.path.exists(stitching_stitching_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {stitching_stitching_engine}")
        if not os.path.exists(stitching_eye_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {stitching_eye_engine}")
        if not os.path.exists(stitching_lip_engine):
            raise FileNotFoundError(f"TensorRT 엔진이 없습니다: {stitching_lip_engine}")
        
        self.stitching_stitching_model = TensorRTInference(stitching_stitching_engine, device)
        self.stitching_eye_model = TensorRTInference(stitching_eye_engine, device)
        self.stitching_lip_model = TensorRTInference(stitching_lip_engine, device)
        print(f"[OK] stitching_retargeting_module 로드 완료 (3개 서브모듈)")
        
        # CropConfig 및 Cropper 초기화
        self.crop_cfg = CropConfig()
        self.cropper = Cropper(crop_cfg=self.crop_cfg, device_id=0, flag_force_cpu=True)
        print(f"[OK] Cropper 초기화 완료 (CPU 모드)")
        
        # 마스크 경로 (paste_back용)
        self.mask_crop_path = os.path.join(pretrained_weights_path, 'liveportrait', 'mask_crop.npy')
        if not os.path.exists(self.mask_crop_path):
            print(f"[WARN] 마스크 파일이 없습니다: {self.mask_crop_path}")
            self.mask_crop_path = None
        
        # 소스 이미지 캐시
        self._source_cache = None
    
    def load_source_image(self, image_path: str, scale: float = 2.3):
        """소스 이미지를 로드하고 전처리"""
        img_rgb = load_image_rgb(image_path)
        
        # 얼굴 크롭
        self.crop_cfg.scale = scale
        crop_info = self.cropper.crop_source_image(img_rgb, self.crop_cfg)
        
        if crop_info is None:
            raise ValueError("이미지에서 얼굴을 찾을 수 없습니다.")
        
        # 이미지 전처리
        img_crop_256x256 = crop_info['img_crop_256x256']
        x = img_crop_256x256.astype(np.float32) / 255.0
        x = np.clip(x, 0, 1)
        x = torch.from_numpy(x).permute(2, 0, 1).unsqueeze(0)  # HxWx3 -> 1x3xHxW
        I_s = x.to(self.device)
        
        # 특징 추출 (TensorRT)
        f_s = self.appearance_model.infer(I_s)
        
        # 키포인트 정보 추출 (TensorRT)
        kp_outputs = self.motion_model.infer(I_s)
        
        # motion_extractor 출력 파싱
        x_s_info = {
            'pitch': kp_outputs['pitch'],
            'yaw': kp_outputs['yaw'],
            'roll': kp_outputs['roll'],
            't': kp_outputs['t'],
            'exp': kp_outputs['exp'],
            'scale': kp_outputs['scale'],
            'kp': kp_outputs['kp']
        }
        
        # 차원 변환
        bs = x_s_info['kp'].shape[0]
        x_s_info['pitch'] = headpose_pred_to_degree(x_s_info['pitch'])[:, None]
        x_s_info['yaw'] = headpose_pred_to_degree(x_s_info['yaw'])[:, None]
        x_s_info['roll'] = headpose_pred_to_degree(x_s_info['roll'])[:, None]
        x_s_info['kp'] = x_s_info['kp'].reshape(bs, -1, 3)
        x_s_info['exp'] = x_s_info['exp'].reshape(bs, -1, 3)
        
        # 소스 랜드마크 계산 (리타겟팅용)
        source_lmk = x_s_info['kp'][0].cpu().numpy()
        source_eye_ratio = calc_eye_close_ratio(source_lmk[None])
        source_lip_ratio = calc_lip_close_ratio(source_lmk[None])
        
        # 마스크 준비
        mask_ori = None
        if self.mask_crop_path:
            mask_ori = prepare_paste_back(
                self.mask_crop_path,
                crop_info['M_c2o'],
                dsize=(img_rgb.shape[1], img_rgb.shape[0])
            )
        
        # 캐시 저장
        self._source_cache = {
            'img_rgb': img_rgb,
            'img_crop_256x256': img_crop_256x256,
            'f_s': f_s,
            'x_s_info': x_s_info,
            'crop_info': crop_info,
            'mask_ori': mask_ori,
            'source_lmk': source_lmk,
            'source_eye_ratio': source_eye_ratio,
            'source_lip_ratio': source_lip_ratio,
        }
        
        print(f"[OK] 소스 이미지 로드 완료: {image_path}")
        return self._source_cache
    
    def _transform_keypoint(self, x_s_info, **kwargs):
        """키포인트 변환 (기존 LivePortraitWrapper.transform_keypoint와 동일)"""
        # 기본값 설정
        smile = kwargs.get('smile', 0.0)
        wink = kwargs.get('wink', 0.0)
        eyebrow = kwargs.get('eyebrow', 0.0)
        eye_ratio = kwargs.get('eye_ratio', None)
        lip_ratio = kwargs.get('lip_ratio', None)
        lip_open = kwargs.get('lip_open', 0.0)
        head_pitch = kwargs.get('head_pitch', 0.0)
        head_yaw = kwargs.get('head_yaw', 0.0)
        head_roll = kwargs.get('head_roll', 0.0)
        eyeball_x = kwargs.get('eyeball_x', 0.0)
        eyeball_y = kwargs.get('eyeball_y', 0.0)
        
        # 소스 정보
        x_s = x_s_info['kp']
        R_s = get_rotation_matrix(x_s_info['pitch'], x_s_info['yaw'], x_s_info['roll'])
        t_s = x_s_info['t']
        scale_s = x_s_info['scale']
        exp_s = x_s_info['exp']
        
        # 정규화된 키포인트
        x_c_s = (x_s - t_s) / scale_s
        
        # 드라이빙 변환
        pitch_d = x_s_info['pitch'] + torch.tensor([[head_pitch]], device=self.device, dtype=torch.float32)
        yaw_d = x_s_info['yaw'] + torch.tensor([[head_yaw]], device=self.device, dtype=torch.float32)
        roll_d = x_s_info['roll'] + torch.tensor([[head_roll]], device=self.device, dtype=torch.float32)
        
        R_d_new = get_rotation_matrix(pitch_d, yaw_d, roll_d)
        t_new = t_s.clone()
        t_new[..., 0] += eyeball_x
        t_new[..., 1] += eyeball_y
        t_new[..., 2].fill_(0)
        
        scale_new = scale_s.clone()
        delta_new = exp_s.clone()
        
        # 표정 파라미터 적용
        if smile != 0:
            delta_new[:, 0, 1] += smile * 0.1
        if wink != 0:
            delta_new[:, 1, 1] += wink * 0.05
        if eyebrow != 0:
            delta_new[:, 2, 1] += eyebrow * 0.05
        
        if lip_open != 0:
            delta_new[:, 3, 1] += lip_open * 0.1
        
        # 새 키포인트 계산
        x_d_new = scale_new * (x_c_s @ R_d_new + delta_new) + t_new
        
        return x_d_new, x_s
    
    def _stitching(self, kp_source: torch.Tensor, kp_driving: torch.Tensor) -> torch.Tensor:
        """스티칭 (TensorRT)"""
        bs, num_kp = kp_source.shape[:2]
        kp_driving_new = kp_driving.clone()
        
        # 입력 연결: kp_source (Bx21x3) + kp_driving (Bx21x3) -> Bx126
        kp_source_flat = kp_source.view(bs, -1)  # Bx63
        kp_driving_flat = kp_driving_new.view(bs, -1)  # Bx63
        stitching_input = torch.cat([kp_source_flat, kp_driving_flat], dim=1)  # Bx126
        
        # TensorRT stitching 실행
        delta = self.stitching_stitching_model.infer(stitching_input)
        
        # 출력 파싱: Bx65 -> delta_exp (Bx63) + delta_tx_ty (Bx2)
        delta_exp = delta[..., :3*num_kp].reshape(bs, num_kp, 3)
        delta_tx_ty = delta[..., 3*num_kp:3*num_kp+2].reshape(bs, 1, 2)
        
        kp_driving_new += delta_exp
        kp_driving_new[..., :2] += delta_tx_ty
        
        return kp_driving_new
    
    def _retarget_eye(self, kp_source: torch.Tensor, eye_close_ratio: torch.Tensor) -> torch.Tensor:
        """눈 리타겟팅 (TensorRT)"""
        bs = kp_source.shape[0]
        # 입력 연결: kp_source (Bx63) + eye_close_ratio (Bx3) -> Bx66
        kp_source_flat = kp_source.view(bs, -1)  # Bx63
        eye_ratio_flat = eye_close_ratio.view(bs, -1)  # Bx3
        eye_input = torch.cat([kp_source_flat, eye_ratio_flat], dim=1)  # Bx66
        
        # TensorRT eye retargeting 실행
        delta = self.stitching_eye_model.infer(eye_input)
        
        # 출력 파싱: Bx63 -> Bx21x3
        return delta.reshape(bs, kp_source.shape[1], 3)
    
    def _retarget_lip(self, kp_source: torch.Tensor, lip_close_ratio: torch.Tensor) -> torch.Tensor:
        """입 리타겟팅 (TensorRT)"""
        bs = kp_source.shape[0]
        # 입력 연결: kp_source (Bx63) + lip_close_ratio (Bx2) -> Bx65
        kp_source_flat = kp_source.view(bs, -1)  # Bx63
        lip_ratio_flat = lip_close_ratio.view(bs, -1)  # Bx2
        lip_input = torch.cat([kp_source_flat, lip_ratio_flat], dim=1)  # Bx65
        
        # TensorRT lip retargeting 실행
        delta = self.stitching_lip_model.infer(lip_input)
        
        # 출력 파싱: Bx63 -> Bx21x3
        return delta.reshape(bs, kp_source.shape[1], 3)
    
    def _calc_combined_eye_ratio(self, eye_ratio_list, source_lmk):
        """눈 비율 계산"""
        source_eye_ratio = calc_eye_close_ratio(source_lmk[None])
        target_eye_ratio = np.array(eye_ratio_list)
        combined = np.concatenate([source_eye_ratio, target_eye_ratio], axis=1)
        return torch.from_numpy(combined).float().to(self.device)
    
    def _calc_combined_lip_ratio(self, lip_ratio_list, source_lmk):
        """입 비율 계산"""
        source_lip_ratio = calc_lip_close_ratio(source_lmk[None])
        target_lip_ratio = np.array(lip_ratio_list)
        combined = np.concatenate([source_lip_ratio, target_lip_ratio], axis=1)
        return torch.from_numpy(combined).float().to(self.device)
    
    @torch.no_grad()
    def generate_frame(
        self,
        smile: float = 0.0,
        wink: float = 0.0,
        eyebrow: float = 0.0,
        eye_ratio: float = None,
        lip_ratio: float = None,
        lip_open: float = 0.0,
        head_pitch: float = 0.0,
        head_yaw: float = 0.0,
        head_roll: float = 0.0,
        eyeball_x: float = 0.0,
        eyeball_y: float = 0.0,
        do_paste_back: bool = True,
    ) -> np.ndarray:
        """프레임 생성"""
        if self._source_cache is None:
            raise ValueError("소스 이미지가 로드되지 않았습니다. load_source_image()를 먼저 호출하세요.")
        
        cache = self._source_cache
        f_s = cache['f_s']
        x_s_info = cache['x_s_info']
        
        # 키포인트 변환
        x_d_new, x_s = self._transform_keypoint(
            x_s_info,
            smile=smile,
            wink=wink,
            eyebrow=eyebrow,
            eye_ratio=eye_ratio,
            lip_ratio=lip_ratio,
            lip_open=lip_open,
            head_pitch=head_pitch,
            head_yaw=head_yaw,
            head_roll=head_roll,
            eyeball_x=eyeball_x,
            eyeball_y=eyeball_y,
        )
        
        # 눈/입 리타겟팅
        source_lmk = cache['source_lmk']
        source_eye_ratio = cache.get('source_eye_ratio', None)
        source_lip_ratio = cache.get('source_lip_ratio', None)
        
        eyes_delta, lip_delta = None, None
        
        if eye_ratio is not None and source_eye_ratio is not None:
            if abs(eye_ratio - source_eye_ratio[0, 0]) > 0.01:
                combined_eye_ratio_tensor = self._calc_combined_eye_ratio(
                    [[float(eye_ratio)]], source_lmk
                )
                eyes_delta = self._retarget_eye(x_s, combined_eye_ratio_tensor)
        
        if lip_ratio is not None and source_lip_ratio is not None:
            if abs(lip_ratio - source_lip_ratio[0, 0]) > 0.01:
                combined_lip_ratio_tensor = self._calc_combined_lip_ratio(
                    [[float(lip_ratio)]], source_lmk
                )
                lip_delta = self._retarget_lip(x_s, combined_lip_ratio_tensor)
        
        x_d_new = x_d_new + \
            (eyes_delta if eyes_delta is not None else 0) + \
            (lip_delta if lip_delta is not None else 0)
        
        # 스티칭
        x_d_new = self._stitching(x_s, x_d_new)
        
        # 워핑 (PyTorch - GridSample 5D 입력 문제로 TensorRT 변환 불가)
        # warping_module 입력: feature_3d (Bx32x16x64x64), kp_driving (Bx21x3), kp_source (Bx21x3)
        with torch.no_grad():
            ret_dct = self.warping_module(feature_3d=f_s, kp_driving=x_d_new, kp_source=x_s)
        
        # 출력은 딕셔너리: {'out': Bx256x64x64, 'occlusion_map': Bx1x64x64, 'deformation': ...}
        warping_out = ret_dct['out']
        
        # 디코딩 (TensorRT)
        out = self.spade_model.infer(warping_out)
        
        # 후처리
        I_p = self._parse_output(out)
        
        # 원본에 붙여넣기
        if do_paste_back and cache['mask_ori'] is not None:
            result = paste_back(
                I_p[0],
                cache['crop_info']['M_c2o'],
                cache['img_rgb'],
                cache['mask_ori']
            )
            return result
        else:
            # paste_back=False일 때는 크롭된 이미지 반환 (256x256)
            return I_p[0]
    
    def _parse_output(self, out: torch.Tensor) -> np.ndarray:
        """출력 파싱 (검은색 상자 문제 해결)"""
        # TensorRT 출력은 torch.Tensor 형태
        if isinstance(out, torch.Tensor):
            out_np = out.data.cpu().numpy() if hasattr(out, 'data') else out.cpu().numpy()
        else:
            out_np = np.array(out)
        
        # 차원 확인 및 변환
        if out_np.ndim == 4:
            if out_np.shape[1] == 3:
                # 1x3xHxW -> 1xHxWx3
                out_np = np.transpose(out_np, [0, 2, 3, 1])
            elif out_np.shape[3] == 3:
                # 이미 1xHxWx3 형태
                pass
            else:
                raise ValueError(f"Unexpected output shape: {out_np.shape}")
        elif out_np.ndim == 3:
            if out_np.shape[0] == 3:
                # 3xHxW -> 1xHxWx3
                out_np = np.transpose(out_np, [1, 2, 0])
                out_np = out_np[np.newaxis, ...]
            elif out_np.shape[2] == 3:
                # HxWx3 -> 1xHxWx3
                out_np = out_np[np.newaxis, ...]
            else:
                raise ValueError(f"Unexpected output shape: {out_np.shape}")
        else:
            raise ValueError(f"Unexpected output dimensions: {out_np.ndim}, shape: {out_np.shape}")
        
        # NaN/Inf 체크 및 처리
        if np.any(np.isnan(out_np)) or np.any(np.isinf(out_np)):
            print("[WARN] NaN/Inf detected in output, replacing with 0")
            out_np = np.nan_to_num(out_np, nan=0.0, posinf=1.0, neginf=0.0)
        
        # 값 범위 확인 및 정규화
        out_min, out_max = out_np.min(), out_np.max()
        
        # TensorRT 출력이 -1~1 범위일 수 있음
        if out_min < 0:
            out_np = (out_np + 1.0) / 2.0
        # 0~255 범위를 0~1로 변환
        elif out_max > 1.0 and out_max <= 255.0:
            out_np = out_np / 255.0
        
        # 0~1 범위로 클리핑 후 uint8로 변환
        out_np = np.clip(out_np, 0, 1)
        out_np = np.clip(out_np * 255, 0, 255).astype(np.uint8)
        
        return out_np
