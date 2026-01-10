# coding: utf-8
"""
LivePortrait Demo 서버
FastAPI 기반 백엔드 서버
"""

import os
import sys
import io
import base64
import asyncio
import json
from typing import Optional, List
from contextlib import asynccontextmanager

import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import asyncio

# 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# 전역 변수
generator = None
source_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    global generator, source_loaded
    
    print("[INFO] LivePortrait server starting...")
    print("[INFO] TensorRT 기반 프레임 생성기 사용")
    print("[INFO] Performance optimizations:")
    print("  - TensorRT: 최적화된 엔진 사용 (appearance, motion, spade)")
    print("  - PyTorch fallback: TensorRT 엔진이 없을 때 자동 폴백")
    print("  - CUDA optimizations: cuDNN benchmark, TF32 enabled")
    print("  - Streaming: real-time frame delivery")
    
    # FrameGenerator 초기화 (TensorRT 자동 감지)
    try:
        from frame_generator import FrameGenerator
        generator = FrameGenerator(device='auto')  # GPU 자동 감지 (RTX 5090 지원)
        print("[OK] FrameGenerator 초기화 완료")
        
        # 샘플 이미지 로드
        sample_image = os.path.join(CURRENT_DIR, 'photo', 'sample-image.png')
        if os.path.exists(sample_image):
            generator.load_source_image(sample_image)
            source_loaded = True
            print(f"[OK] Sample image loaded: {sample_image}")
        else:
            print(f"[WARN] Sample image not found: {sample_image}")
            
        print("[OK] LivePortrait model loaded!")
    except Exception as e:
        print(f"[ERROR] Model load failed: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    print("[INFO] Server shutting down...")


app = FastAPI(
    title="LivePortrait Demo API",
    description="정적 이미지에 표정 애니메이션을 적용하는 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 요청/응답 모델
# ============================================================================

class GenerateRequest(BaseModel):
    """표정 생성 요청"""
    expression: str  # smile, blink, talk, surprise, wink
    
    
class GenerateResponse(BaseModel):
    """표정 생성 응답"""
    success: bool
    video: str  # Base64 인코딩된 GIF 비디오
    fps: int
    total_frames: int
    duration_ms: int


class ExpressionInfo(BaseModel):
    """표정 정보"""
    name: str
    display_name: str
    description: str
    duration_ms: int


class ExpressionsListResponse(BaseModel):
    """표정 목록 응답"""
    expressions: List[ExpressionInfo]


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    model_loaded: bool
    source_loaded: bool


# ============================================================================
# 유틸리티 함수
# ============================================================================

def image_to_base64(image: np.ndarray) -> str:
    """numpy 이미지를 Base64 문자열로 변환"""
    if image.dtype != np.uint8:
        image = (image * 255).astype(np.uint8)
    
    # RGB -> PIL Image
    pil_image = Image.fromarray(image)
    
    # PNG로 인코딩
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    # Base64 인코딩
    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"


# ============================================================================
# API 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """프론트엔드 페이지 서빙"""
    frontend_path = os.path.join(CURRENT_DIR, 'frontend', 'dist', 'index.html')
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "LivePortrait Demo API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """헬스체크"""
    return {
        "status": "ok",
        "model_loaded": generator is not None,
        "source_loaded": source_loaded
    }


@app.get("/expressions", response_model=ExpressionsListResponse)
async def get_expressions():
    """사용 가능한 표정 목록"""
    from expressions import list_expressions
    return {"expressions": list_expressions()}


@app.get("/source-image")
async def get_source_image():
    """현재 로드된 소스 이미지 반환"""
    if not source_loaded or generator is None:
        raise HTTPException(status_code=404, detail="소스 이미지가 로드되지 않았습니다.")
    
    # 원본 이미지를 직접 반환 (캐시에서 가져오기)
    if generator._source_cache is None:
        raise HTTPException(status_code=404, detail="소스 이미지 캐시가 없습니다.")
    
    # 원본 이미지 반환 (RGB numpy array)
    img_rgb = generator._source_cache['img_rgb']
    base64_image = image_to_base64(img_rgb)
    
    return {"image": base64_image}


@app.post("/generate")
async def generate_expression(request: GenerateRequest):
    """표정 애니메이션 생성 - Server-Sent Events로 실시간 스트리밍"""
    global generator, source_loaded
    
    if generator is None:
        raise HTTPException(status_code=500, detail="모델이 로드되지 않았습니다.")
    
    if not source_loaded:
        raise HTTPException(status_code=400, detail="소스 이미지가 로드되지 않았습니다.")
    
    # 표정 프리셋 가져오기
    from expressions import get_expression
    expression = get_expression(request.expression)
    
    if expression is None:
        raise HTTPException(
            status_code=400, 
            detail=f"알 수 없는 표정: {request.expression}. 사용 가능: smile, blink, talk, surprise, wink"
        )
    
    async def generate_stream():
        """프레임을 실시간으로 스트리밍"""
        try:
            import time
            start_time = time.time()
            total_frames = expression.get_total_frames()
            
            print(f"[INFO] Starting streaming: {total_frames} frames for {request.expression}")
            
            # 첫 번째 메시지: 메타데이터
            yield f"data: {json.dumps({'type': 'start', 'total_frames': total_frames, 'fps': expression.fps, 'duration_ms': expression.duration_ms})}\n\n"
            
            # 프레임 생성 및 스트리밍 (생성하는 대로 즉시 전송)
            for i in range(total_frames):
                t = i / (total_frames - 1) if total_frames > 1 else 0.0
                params = expression.interpolate_params(t)
                
                # 프레임 생성 (do_paste_back=True로 원본 이미지에 붙여넣기)
                frame_start = time.time()
                frame = generator.generate_frame(**params, do_paste_back=True)
                frame_time = time.time() - frame_start
                
                # Base64로 변환
                base64_frame = image_to_base64(frame)
                
                # 즉시 스트리밍 전송
                yield f"data: {json.dumps({'type': 'frame', 'index': i, 'frame': base64_frame, 'time_ms': frame_time*1000})}\n\n"
                
                # CPU 양보 (다음 프레임 생성 전)
                await asyncio.sleep(0.001)
            
            total_time = time.time() - start_time
            print(f"[INFO] Streaming complete: {total_frames} frames in {total_time:.2f}s ({total_time/total_frames*1000:.1f}ms per frame)")
            
            # 완료 메시지
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 정적 파일 서빙 (프론트엔드)
frontend_dist = os.path.join(CURRENT_DIR, 'frontend', 'dist')
assets_dir = os.path.join(frontend_dist, 'assets')
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == '__main__':
    import uvicorn
    print("\n" + "="*60)
    print("LivePortrait Demo Server")
    print("="*60)
    print("서버가 시작되었습니다!")
    print("브라우저에서 다음 주소로 접속하세요:")
    print("  - http://localhost:8000")
    print("  - http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
