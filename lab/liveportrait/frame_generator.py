# coding: utf-8
"""
LivePortrait Frame Generator
정적 이미지에서 표정이 변화하는 프레임들을 생성하는 모듈
"""

import os
import sys
import cv2
import numpy as np
import torch

# LivePortrait 경로 추가
LIVEPORTRAIT_PATH = os.path.join(os.path.dirname(__file__), 'LivePortrait')
sys.path.insert(0, LIVEPORTRAIT_PATH)

from src.config.inference_config import InferenceConfig
from src.config.crop_config import CropConfig
from src.live_portrait_wrapper import LivePortraitWrapper
from src.utils.cropper import Cropper
from src.utils.camera import get_rotation_matrix
from src.utils.io import load_image_rgb
from src.utils.crop import prepare_paste_back, paste_back


class FrameGenerator:
    """LivePortrait 모델을 래핑하여 표정 프레임을 생성하는 클래스"""
    
    def __init__(self, pretrained_weights_path: str = None, device: str = 'auto'):
        """
        Args:
            pretrained_weights_path: pretrained weights 경로 (None이면 기본 경로 사용)
            device: 'cuda', 'cpu', 또는 'auto' (자동 감지)
        """
        if pretrained_weights_path is None:
            pretrained_weights_path = os.path.join(os.path.dirname(__file__), 'pretrained_weights')
        
        # GPU 호환성 확인
        if device == 'auto':
            if torch.cuda.is_available():
                try:
                    # 간단한 CUDA 테스트
                    test_tensor = torch.zeros(1).cuda()
                    _ = test_tensor + 1
                    device = 'cuda'
                except RuntimeError as e:
                    print(f"[WARN] CUDA not compatible, falling back to CPU: {e}")
                    device = 'cpu'
            else:
                device = 'cpu'
        
        print(f"[INFO] Using device: {device}")
        
        # 설정 초기화
        self.inference_cfg = InferenceConfig(
            checkpoint_F=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'appearance_feature_extractor.pth'),
            checkpoint_M=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'motion_extractor.pth'),
            checkpoint_G=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'spade_generator.pth'),
            checkpoint_W=os.path.join(pretrained_weights_path, 'liveportrait', 'base_models', 'warping_module.pth'),
            checkpoint_S=os.path.join(pretrained_weights_path, 'liveportrait', 'retargeting_models', 'stitching_retargeting_module.pth'),
            flag_force_cpu=(device == 'cpu'),
        )
        self.crop_cfg = CropConfig()
        
        # LivePortrait 래퍼 초기화
        self.live_portrait_wrapper = LivePortraitWrapper(inference_cfg=self.inference_cfg)
        self.cropper = Cropper(crop_cfg=self.crop_cfg)
        
        self.device = torch.device(device)
        
        # 소스 이미지 캐시
        self._source_cache = None
        
    def load_source_image(self, image_path: str, scale: float = 2.3):
        """소스 이미지를 로드하고 전처리
        
        Args:
            image_path: 이미지 파일 경로
            scale: 크롭 스케일
        """
        img_rgb = load_image_rgb(image_path)
        
        # 얼굴 크롭
        self.crop_cfg.scale = scale
        crop_info = self.cropper.crop_source_image(img_rgb, self.crop_cfg)
        
        if crop_info is None:
            raise ValueError("이미지에서 얼굴을 찾을 수 없습니다.")
        
        # 특징 추출
        I_s = self.live_portrait_wrapper.prepare_source(crop_info['img_crop_256x256'])
        x_s_info = self.live_portrait_wrapper.get_kp_info(I_s)
        f_s = self.live_portrait_wrapper.extract_feature_3d(I_s)
        x_s = self.live_portrait_wrapper.transform_keypoint(x_s_info)
        R_s = get_rotation_matrix(x_s_info['pitch'], x_s_info['yaw'], x_s_info['roll'])
        
        # 마스크 준비
        mask_ori = prepare_paste_back(
            self.inference_cfg.mask_crop, 
            crop_info['M_c2o'], 
            dsize=(img_rgb.shape[1], img_rgb.shape[0])
        )
        
        # 원본 눈/입 비율 계산 (리타겟팅 비교용)
        from src.utils.retargeting_utils import calc_eye_close_ratio, calc_lip_close_ratio
        source_lmk = crop_info['lmk_crop']
        source_eye_ratio = calc_eye_close_ratio(source_lmk[None])
        source_lip_ratio = calc_lip_close_ratio(source_lmk[None])
        
        # 캐시 저장
        self._source_cache = {
            'img_rgb': img_rgb,
            'crop_info': crop_info,
            'I_s': I_s,
            'x_s_info': x_s_info,
            'f_s': f_s,
            'x_s': x_s,
            'R_s': R_s,
            'mask_ori': mask_ori,
            'source_lmk': source_lmk,
            'source_eye_ratio': float(source_eye_ratio.mean()),
            'source_lip_ratio': float(source_lip_ratio[0][0]),
        }
        
        return self._source_cache
    
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
        paste_back: bool = True,
    ) -> np.ndarray:
        """표정 파라미터를 적용하여 프레임 생성
        
        Args:
            smile: 웃음 정도 (-0.3 ~ 1.3)
            wink: 윙크 정도 (0 ~ 39)
            eyebrow: 눈썹 움직임 (-30 ~ 30)
            eye_ratio: 눈 열림 비율 (0 ~ 0.8, None이면 원본 유지)
            lip_ratio: 입 열림 비율 (0 ~ 0.8, None이면 원본 유지)
            lip_open: 입 열기/닫기 (-90 ~ 120)
            head_pitch: 머리 상하 회전 (-15 ~ 15)
            head_yaw: 머리 좌우 회전 (-25 ~ 25)
            head_roll: 머리 기울기 (-15 ~ 15)
            eyeball_x: 시선 수평 방향 (-30 ~ 30)
            eyeball_y: 시선 수직 방향 (-63 ~ 63)
            paste_back: 원본 이미지에 붙여넣기 여부
            
        Returns:
            생성된 프레임 이미지 (RGB numpy array)
        """
        if self._source_cache is None:
            raise ValueError("먼저 load_source_image()를 호출하세요.")
        
        cache = self._source_cache
        device = self.device
        
        # 텐서 변환
        x_s = cache['x_s'].to(device)
        f_s = cache['f_s'].to(device)
        x_s_info = cache['x_s_info']
        R_s = cache['R_s'].to(device)
        
        x_c_s = x_s_info['kp'].to(device)
        delta_new = x_s_info['exp'].clone().to(device)
        scale_new = x_s_info['scale'].to(device)
        t_new = x_s_info['t'].to(device)
        
        # 머리 회전 적용
        x_d_info_pitch = x_s_info['pitch'] + head_pitch
        x_d_info_yaw = x_s_info['yaw'] + head_yaw
        x_d_info_roll = x_s_info['roll'] + head_roll
        R_d = get_rotation_matrix(x_d_info_pitch, x_d_info_yaw, x_d_info_roll).to(device)
        R_d_new = (R_d @ R_s.permute(0, 2, 1)) @ R_s
        
        # 표정 파라미터 적용
        if eyeball_x != 0 or eyeball_y != 0:
            delta_new = self._update_eyeball_direction(eyeball_x, eyeball_y, delta_new)
        
        if smile != 0:
            delta_new = self._update_smile(smile, delta_new)
        
        if wink != 0:
            delta_new = self._update_wink(wink, delta_new)
        
        if eyebrow != 0:
            delta_new = self._update_eyebrow(eyebrow, delta_new)
        
        if lip_open != 0:
            delta_new = self._update_lip_open(lip_open, delta_new)
        
        # 새 키포인트 계산
        x_d_new = scale_new * (x_c_s @ R_d_new + delta_new) + t_new
        
        # 눈/입 리타겟팅 (원본과 다를 때만)
        eyes_delta, lip_delta = None, None
        source_lmk = cache['source_lmk']
        source_eye_ratio = cache.get('source_eye_ratio', None)
        source_lip_ratio = cache.get('source_lip_ratio', None)
        
        if eye_ratio is not None and source_eye_ratio is not None:
            # 원본과 다를 때만 리타겟팅
            if abs(eye_ratio - source_eye_ratio) > 0.01:
                combined_eye_ratio_tensor = self.live_portrait_wrapper.calc_combined_eye_ratio(
                    [[float(eye_ratio)]], source_lmk
                )
                eyes_delta = self.live_portrait_wrapper.retarget_eye(x_s, combined_eye_ratio_tensor)
        
        if lip_ratio is not None and source_lip_ratio is not None:
            # 원본과 다를 때만 리타겟팅
            if abs(lip_ratio - source_lip_ratio) > 0.01:
                combined_lip_ratio_tensor = self.live_portrait_wrapper.calc_combined_lip_ratio(
                    [[float(lip_ratio)]], source_lmk
                )
                lip_delta = self.live_portrait_wrapper.retarget_lip(x_s, combined_lip_ratio_tensor)
        
        x_d_new = x_d_new + \
            (eyes_delta if eyes_delta is not None else 0) + \
            (lip_delta if lip_delta is not None else 0)
        
        # 스티칭
        x_d_new = self.live_portrait_wrapper.stitching(x_s, x_d_new)
        
        # 워핑 및 디코딩
        out = self.live_portrait_wrapper.warp_decode(f_s, x_s, x_d_new)
        I_p = self.live_portrait_wrapper.parse_output(out['out'])[0]
        
        # 원본에 붙여넣기 (성능 최적화: paste_back은 선택적으로)
        if paste_back and cache['mask_ori'] is not None:
            result = paste_back_impl(
                I_p, 
                cache['crop_info']['M_c2o'], 
                cache['img_rgb'], 
                cache['mask_ori']
            )
        else:
            result = I_p
        
        return result
    
    def generate_frames_batch(
        self,
        expression_params_list: list,
        paste_back: bool = False,
    ) -> list:
        """여러 프레임을 배치로 생성 (성능 최적화)
        
        Args:
            expression_params_list: 각 프레임의 파라미터 딕셔너리 리스트
            paste_back: 원본 이미지에 붙여넣기 여부
            
        Returns:
            생성된 프레임 리스트
        """
        if self._source_cache is None:
            raise ValueError("먼저 load_source_image()를 호출하세요.")
        
        cache = self._source_cache
        device = self.device
        
        # 공통 텐서 준비 (한 번만)
        x_s = cache['x_s'].to(device)
        f_s = cache['f_s'].to(device)
        x_s_info = cache['x_s_info']
        R_s = cache['R_s'].to(device)
        x_c_s = x_s_info['kp'].to(device)
        scale_new = x_s_info['scale'].to(device)
        t_new = x_s_info['t'].to(device)
        source_lmk = cache['source_lmk']
        source_eye_ratio = cache.get('source_eye_ratio', None)
        source_lip_ratio = cache.get('source_lip_ratio', None)
        
        frames = []
        
        for params in expression_params_list:
            # 각 프레임별 파라미터 적용
            delta_new = x_s_info['exp'].clone().to(device)
            
            # 표정 파라미터 적용
            if params.get('eyeball_x', 0) != 0 or params.get('eyeball_y', 0) != 0:
                delta_new = self._update_eyeball_direction(
                    params.get('eyeball_x', 0), 
                    params.get('eyeball_y', 0), 
                    delta_new
                )
            
            if params.get('smile', 0) != 0:
                delta_new = self._update_smile(params.get('smile', 0), delta_new)
            
            if params.get('wink', 0) != 0:
                delta_new = self._update_wink(params.get('wink', 0), delta_new)
            
            if params.get('eyebrow', 0) != 0:
                delta_new = self._update_eyebrow(params.get('eyebrow', 0), delta_new)
            
            if params.get('lip_open', 0) != 0:
                delta_new = self._update_lip_open(params.get('lip_open', 0), delta_new)
            
            # 머리 회전
            head_pitch = params.get('head_pitch', 0.0)
            head_yaw = params.get('head_yaw', 0.0)
            head_roll = params.get('head_roll', 0.0)
            x_d_info_pitch = x_s_info['pitch'] + head_pitch
            x_d_info_yaw = x_s_info['yaw'] + head_yaw
            x_d_info_roll = x_s_info['roll'] + head_roll
            R_d = get_rotation_matrix(x_d_info_pitch, x_d_info_yaw, x_d_info_roll).to(device)
            R_d_new = (R_d @ R_s.permute(0, 2, 1)) @ R_s
            
            # 새 키포인트 계산
            x_d_new = scale_new * (x_c_s @ R_d_new + delta_new) + t_new
            
            # 눈/입 리타겟팅
            eyes_delta, lip_delta = None, None
            eye_ratio = params.get('eye_ratio')
            lip_ratio = params.get('lip_ratio')
            
            if eye_ratio is not None and source_eye_ratio is not None:
                if abs(eye_ratio - source_eye_ratio) > 0.01:
                    combined_eye_ratio_tensor = self.live_portrait_wrapper.calc_combined_eye_ratio(
                        [[float(eye_ratio)]], source_lmk
                    )
                    eyes_delta = self.live_portrait_wrapper.retarget_eye(x_s, combined_eye_ratio_tensor)
            
            if lip_ratio is not None and source_lip_ratio is not None:
                if abs(lip_ratio - source_lip_ratio) > 0.01:
                    combined_lip_ratio_tensor = self.live_portrait_wrapper.calc_combined_lip_ratio(
                        [[float(lip_ratio)]], source_lmk
                    )
                    lip_delta = self.live_portrait_wrapper.retarget_lip(x_s, combined_lip_ratio_tensor)
            
            x_d_new = x_d_new + \
                (eyes_delta if eyes_delta is not None else 0) + \
                (lip_delta if lip_delta is not None else 0)
            
            # 스티칭
            x_d_new = self.live_portrait_wrapper.stitching(x_s, x_d_new)
            
            # 워핑 및 디코딩
            out = self.live_portrait_wrapper.warp_decode(f_s, x_s, x_d_new)
            I_p = self.live_portrait_wrapper.parse_output(out['out'])[0]
            
            # paste_back은 성능상 제외 (필요시 나중에 추가)
            frames.append(I_p)
        
        return frames
    
    def generate_animation_frames(
        self,
        expression_params: dict,
        num_frames: int = 30,
        fps: int = 30,
        ease_type: str = 'ease_in_out',
    ) -> list:
        """애니메이션 프레임 시퀀스 생성
        
        Args:
            expression_params: 최종 표정 파라미터 딕셔너리
            num_frames: 총 프레임 수
            fps: FPS
            ease_type: 이징 타입 ('linear', 'ease_in', 'ease_out', 'ease_in_out')
            
        Returns:
            프레임 리스트
        """
        frames = []
        
        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 1.0
            
            # 이징 적용
            if ease_type == 'ease_in':
                t = t * t
            elif ease_type == 'ease_out':
                t = 1 - (1 - t) * (1 - t)
            elif ease_type == 'ease_in_out':
                t = 3 * t * t - 2 * t * t * t
            
            # 현재 프레임의 파라미터 계산
            current_params = {k: v * t for k, v in expression_params.items()}
            
            # 프레임 생성
            frame = self.generate_frame(**current_params)
            frames.append(frame)
        
        return frames
    
    def _update_eyeball_direction(self, x: float, y: float, delta_new):
        """시선 방향 업데이트"""
        if x > 0:
            delta_new[0, 11, 0] += x * 0.0007
            delta_new[0, 15, 0] += x * 0.001
        else:
            delta_new[0, 11, 0] += x * 0.001
            delta_new[0, 15, 0] += x * 0.0007
        
        delta_new[0, 11, 1] += y * -0.001
        delta_new[0, 15, 1] += y * -0.001
        blink = -y / 2.0
        delta_new[0, 11, 1] += blink * -0.001
        delta_new[0, 13, 1] += blink * 0.0003
        delta_new[0, 15, 1] += blink * -0.001
        delta_new[0, 16, 1] += blink * 0.0003
        
        return delta_new
    
    def _update_smile(self, smile: float, delta_new):
        """웃음 표정 업데이트"""
        delta_new[0, 20, 1] += smile * -0.01
        delta_new[0, 14, 1] += smile * -0.02
        delta_new[0, 17, 1] += smile * 0.0065
        delta_new[0, 17, 2] += smile * 0.003
        delta_new[0, 13, 1] += smile * -0.00275
        delta_new[0, 16, 1] += smile * -0.00275
        delta_new[0, 3, 1] += smile * -0.0035
        delta_new[0, 7, 1] += smile * -0.0035
        
        return delta_new
    
    def _update_wink(self, wink: float, delta_new):
        """윙크 업데이트"""
        delta_new[0, 11, 1] += wink * 0.001
        delta_new[0, 13, 1] += wink * -0.0003
        delta_new[0, 17, 0] += wink * 0.0003
        delta_new[0, 17, 1] += wink * 0.0003
        delta_new[0, 3, 1] += wink * -0.0003
        
        return delta_new
    
    def _update_eyebrow(self, eyebrow: float, delta_new):
        """눈썹 업데이트"""
        if eyebrow > 0:
            delta_new[0, 1, 1] += eyebrow * 0.001
            delta_new[0, 2, 1] += eyebrow * -0.001
        else:
            delta_new[0, 1, 0] += eyebrow * -0.001
            delta_new[0, 2, 0] += eyebrow * 0.001
            delta_new[0, 1, 1] += eyebrow * 0.0003
            delta_new[0, 2, 1] += eyebrow * -0.0003
        
        return delta_new
    
    def _update_lip_open(self, lip_open: float, delta_new):
        """입 열기/닫기 업데이트"""
        delta_new[0, 19, 1] += lip_open * 0.001
        delta_new[0, 19, 2] += lip_open * 0.0001
        delta_new[0, 17, 1] += lip_open * -0.0001
        
        return delta_new


def paste_back_impl(I_p, M_c2o, img_rgb, mask_ori):
    """이미지 붙여넣기 구현"""
    from src.utils.crop import paste_back
    return paste_back(I_p, M_c2o, img_rgb, mask_ori)


if __name__ == '__main__':
    # 테스트 코드
    generator = FrameGenerator()
    
    # 샘플 이미지 로드
    sample_image = os.path.join(os.path.dirname(__file__), 'photo', 'sample-image.png')
    if os.path.exists(sample_image):
        generator.load_source_image(sample_image)
        
        # 웃는 표정 프레임 생성
        frame = generator.generate_frame(smile=1.0)
        print(f"Generated frame shape: {frame.shape}")
        
        # 애니메이션 프레임 생성
        frames = generator.generate_animation_frames({'smile': 1.0}, num_frames=10)
        print(f"Generated {len(frames)} animation frames")
    else:
        print(f"Sample image not found: {sample_image}")
