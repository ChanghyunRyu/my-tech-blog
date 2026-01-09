# coding: utf-8
"""
표정 프리셋 정의
각 표정에 대한 파라미터와 애니메이션 설정을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import copy


@dataclass
class ExpressionKeyframe:
    """표정 키프레임"""
    time: float  # 0.0 ~ 1.0 (정규화된 시간)
    params: Dict[str, float] = field(default_factory=dict)


@dataclass
class Expression:
    """표정 정의"""
    name: str
    display_name: str
    description: str
    keyframes: List[ExpressionKeyframe] = field(default_factory=list)
    duration_ms: int = 1000  # 애니메이션 지속 시간 (밀리초)
    fps: int = 30  # 프레임 레이트
    loop: bool = False  # 반복 여부
    return_to_neutral: bool = True  # 원래 상태로 돌아갈지 여부
    
    def get_total_frames(self) -> int:
        """총 프레임 수 계산"""
        return int(self.duration_ms * self.fps / 1000)
    
    def interpolate_params(self, t: float) -> Dict[str, float]:
        """특정 시간 t에서의 파라미터 보간"""
        if not self.keyframes:
            return {}
        
        # 키프레임이 하나뿐이면 그 값 반환
        if len(self.keyframes) == 1:
            return copy.deepcopy(self.keyframes[0].params)
        
        # 현재 시간에 해당하는 두 키프레임 찾기
        prev_kf = self.keyframes[0]
        next_kf = self.keyframes[-1]
        
        for i, kf in enumerate(self.keyframes):
            if kf.time <= t:
                prev_kf = kf
            if kf.time >= t:
                next_kf = kf
                break
        
        # 보간
        if prev_kf.time == next_kf.time:
            return copy.deepcopy(prev_kf.params)
        
        # 이징 함수 (ease-in-out)
        local_t = (t - prev_kf.time) / (next_kf.time - prev_kf.time)
        local_t = 3 * local_t ** 2 - 2 * local_t ** 3  # smoothstep
        
        # 파라미터 보간
        result = {}
        all_keys = set(prev_kf.params.keys()) | set(next_kf.params.keys())
        
        for key in all_keys:
            prev_val = prev_kf.params.get(key, 0.0)
            next_val = next_kf.params.get(key, 0.0)
            result[key] = prev_val + (next_val - prev_val) * local_t
        
        return result


# ============================================================================
# 표정 프리셋 정의
# ============================================================================

# 웃기 (Smile)
SMILE = Expression(
    name="smile",
    display_name="웃어봐 😊",
    description="자연스럽게 미소 짓는 표정",
    duration_ms=1500,
    fps=30,
    return_to_neutral=True,
    keyframes=[
        ExpressionKeyframe(time=0.0, params={}),
        ExpressionKeyframe(time=0.3, params={
            "smile": 0.8,
            "eyebrow": 5.0,
        }),
        ExpressionKeyframe(time=0.5, params={
            "smile": 1.0,
            "eyebrow": 8.0,
            "eyeball_y": -5.0,  # 약간 아래 보기 (수줍음)
        }),
        ExpressionKeyframe(time=0.7, params={
            "smile": 0.9,
            "eyebrow": 6.0,
        }),
        ExpressionKeyframe(time=1.0, params={}),
    ]
)

# 눈 깜빡임 (Blink)
BLINK = Expression(
    name="blink",
    display_name="깜빡여봐 😉",
    description="양쪽 눈을 깜빡이는 동작",
    duration_ms=500,
    fps=30,
    return_to_neutral=True,
    keyframes=[
        ExpressionKeyframe(time=0.0, params={}),
        ExpressionKeyframe(time=0.3, params={
            "eye_ratio": 0.0,  # 눈 감기
        }),
        ExpressionKeyframe(time=0.5, params={
            "eye_ratio": 0.0,
        }),
        ExpressionKeyframe(time=0.7, params={
            "eye_ratio": 0.35,  # 눈 뜨기
        }),
        ExpressionKeyframe(time=1.0, params={}),
    ]
)

# 말하기 (Talk)
TALK = Expression(
    name="talk",
    display_name="말해봐 💬",
    description="말하는 것처럼 입을 움직이는 표정",
    duration_ms=2000,
    fps=30,
    return_to_neutral=True,
    keyframes=[
        ExpressionKeyframe(time=0.0, params={}),
        # 첫 번째 음절
        ExpressionKeyframe(time=0.1, params={
            "lip_open": 30.0,
            "lip_ratio": 0.3,
        }),
        ExpressionKeyframe(time=0.2, params={
            "lip_open": 10.0,
            "lip_ratio": 0.1,
        }),
        # 두 번째 음절
        ExpressionKeyframe(time=0.3, params={
            "lip_open": 50.0,
            "lip_ratio": 0.4,
        }),
        ExpressionKeyframe(time=0.4, params={
            "lip_open": 20.0,
            "lip_ratio": 0.15,
        }),
        # 세 번째 음절
        ExpressionKeyframe(time=0.5, params={
            "lip_open": 40.0,
            "lip_ratio": 0.35,
        }),
        ExpressionKeyframe(time=0.6, params={
            "lip_open": 15.0,
            "lip_ratio": 0.1,
        }),
        # 네 번째 음절
        ExpressionKeyframe(time=0.7, params={
            "lip_open": 35.0,
            "lip_ratio": 0.3,
        }),
        ExpressionKeyframe(time=0.85, params={
            "lip_open": 10.0,
            "lip_ratio": 0.05,
        }),
        ExpressionKeyframe(time=1.0, params={}),
    ]
)

# 놀람 (Surprise)
SURPRISE = Expression(
    name="surprise",
    display_name="놀라봐 😲",
    description="놀란 표정",
    duration_ms=1200,
    fps=30,
    return_to_neutral=True,
    keyframes=[
        ExpressionKeyframe(time=0.0, params={}),
        ExpressionKeyframe(time=0.15, params={
            "eyebrow": 25.0,
            "eye_ratio": 0.7,  # 눈 크게 뜨기
            "lip_open": 40.0,
            "lip_ratio": 0.3,
        }),
        ExpressionKeyframe(time=0.4, params={
            "eyebrow": 28.0,
            "eye_ratio": 0.75,
            "lip_open": 50.0,
            "lip_ratio": 0.4,
            "head_pitch": -3.0,  # 고개 약간 뒤로
        }),
        ExpressionKeyframe(time=0.6, params={
            "eyebrow": 22.0,
            "eye_ratio": 0.65,
            "lip_open": 35.0,
            "lip_ratio": 0.25,
            "head_pitch": -2.0,
        }),
        ExpressionKeyframe(time=1.0, params={}),
    ]
)

# 윙크 (Wink) - 보너스
WINK = Expression(
    name="wink",
    display_name="윙크해봐 😜",
    description="한쪽 눈을 깜빡이며 윙크",
    duration_ms=800,
    fps=30,
    return_to_neutral=True,
    keyframes=[
        ExpressionKeyframe(time=0.0, params={}),
        ExpressionKeyframe(time=0.2, params={
            "wink": 20.0,
            "smile": 0.4,
        }),
        ExpressionKeyframe(time=0.4, params={
            "wink": 35.0,
            "smile": 0.6,
        }),
        ExpressionKeyframe(time=0.6, params={
            "wink": 25.0,
            "smile": 0.5,
        }),
        ExpressionKeyframe(time=1.0, params={}),
    ]
)


# 모든 표정 딕셔너리
EXPRESSIONS: Dict[str, Expression] = {
    "smile": SMILE,
    "blink": BLINK,
    "talk": TALK,
    "surprise": SURPRISE,
    "wink": WINK,
}


def get_expression(name: str) -> Optional[Expression]:
    """이름으로 표정 프리셋 가져오기"""
    return EXPRESSIONS.get(name)


def list_expressions() -> List[Dict]:
    """모든 표정 정보 리스트"""
    return [
        {
            "name": exp.name,
            "display_name": exp.display_name,
            "description": exp.description,
            "duration_ms": exp.duration_ms,
        }
        for exp in EXPRESSIONS.values()
    ]


if __name__ == '__main__':
    # 테스트
    print("Available expressions:")
    for info in list_expressions():
        print(f"  - {info['name']}: {info['display_name']} ({info['duration_ms']}ms)")
    
    # 보간 테스트
    smile = get_expression("smile")
    if smile:
        print(f"\nSmile expression at t=0.5:")
        params = smile.interpolate_params(0.5)
        for k, v in params.items():
            print(f"  {k}: {v:.3f}")
