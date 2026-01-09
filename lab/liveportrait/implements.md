# 간단한 Live2D Portrait 제작

이 폴더에 실험용으로 살아있는 초상화를 구현하세요. 허깅페이스 모델 liveportrait(https://huggingface.co/KlingTeam/LivePortrait)를 이용하여 photo/sample-image.png 이미지를 사용자의 요청에 따른 표정을 짓는 형태의 간단한 서비스를 제작하세요.

공식 문서나 이를 사용한 프로젝트 등을 웹에서 검색하고 이를 활용하여 제작하세요.

## 1. GPU를 활용하여 Frame 생성 구현

livePortrait 모델을 사용하여 샘플 이미지로 프레임을 생성하는 코드를 구현하세요. 이 때 조정할 수 있는 파라미터(eye_ratio, lip_ratio 등)를 자세히 알아내고 각각 무엇인지 기록하세요.

### ✅ 구현 완료: `frame_generator.py`

### 조사된 파라미터 목록

| 파라미터 | 범위 | 설명 |
|---------|------|------|
| `smile` | -0.3 ~ 1.3 | 웃음 정도. 양수는 미소, 1.0 이상은 활짝 웃음 |
| `wink` | 0 ~ 39 | 윙크 정도. 한쪽 눈을 감음 |
| `eyebrow` | -30 ~ 30 | 눈썹 움직임. 양수는 올림, 음수는 찌푸림 |
| `eye_ratio` | 0 ~ 0.8 | 눈 열림 비율. 0은 감김, 0.4는 보통, 0.8은 크게 뜸 |
| `lip_ratio` | 0 ~ 0.8 | 입 열림 비율. 0은 다물음, 0.5 이상은 크게 벌림 |
| `lip_open` | -90 ~ 120 | 입 열기/닫기 세부 조절 |
| `head_pitch` | -15 ~ 15 | 머리 상하 회전 (고개 끄덕임) |
| `head_yaw` | -25 ~ 25 | 머리 좌우 회전 |
| `head_roll` | -15 ~ 15 | 머리 기울기 |
| `eyeball_x` | -30 ~ 30 | 시선 수평 방향 |
| `eyeball_y` | -63 ~ 63 | 시선 수직 방향 | 

## 2. 자연스러운 livePortrait을 구현하기 위한 설정값 조사

보통 livePortrait의 경우, 모션 트래킹 등의 사용자의 표정을 흉내내는 것을 구현한 것 같습니다. 제가 원하는 동작은 "웃어줘", "말해봐" 등의 명령을 입력했을 때 자동으로 이를 보여주는 것입니다. 이를 어떻게 구현할 수 있을지 조사하고 그런 상태를 제작하세요.

### ✅ 구현 완료: `expressions.py`

키프레임 기반 애니메이션을 사용하여 자연스러운 표정 전환을 구현했습니다.

### 구현된 표정 프리셋

| 표정 | 지속시간 | 설명 |
|-----|---------|------|
| `smile` (웃어봐 😊) | 1500ms | 자연스럽게 미소 짓고 원래대로 돌아옴 |
| `blink` (깜빡여봐 😉) | 500ms | 양쪽 눈을 깜빡임 |
| `talk` (말해봐 💬) | 2000ms | 여러 음절을 말하는 것처럼 입을 움직임 |
| `surprise` (놀라봐 😲) | 1200ms | 눈을 크게 뜨고 입을 벌림 |
| `wink` (윙크해봐 😜) | 800ms | 한쪽 눈을 감으며 미소 |

### 애니메이션 방식

각 표정은 키프레임 시퀀스로 정의되어 있으며, smoothstep 이징을 적용하여 자연스러운 전환을 구현:
- `time`: 0.0 ~ 1.0 (정규화된 시간)
- `params`: 해당 시점의 표정 파라미터
- 키프레임 사이는 자동으로 보간됨

## 3. 데모를 위한 Frontend 구현

위의 구현이 완료되면 이를 통해 제작된 Frame을 재생하는 간단한 localhost 웹사이트를 제작해주세요. 평상시 사진에 웃어봐 버튼을 눌렀을 때 자연스럽게 웃고 잠시 뒤 원상태로 돌아오는 등의 웹사이트를 제작해야 합니다.

### ✅ 구현 완료

- **백엔드**: `server.py` (FastAPI)
- **프론트엔드**: `frontend/dist/index.html` (Vanilla HTML/CSS/JS)

### 실행 방법

#### 사전 요구사항

**RTX 5090 GPU 사용 시:**
RTX 5090은 CUDA 12.8을 지원하는 PyTorch Nightly 버전이 필요합니다:

```bash
# 기존 PyTorch 제거
pip uninstall torch torchvision torchaudio -y

# PyTorch Nightly (CUDA 12.8) 설치
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

**일반 GPU 또는 CPU 사용 시:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

#### 서버 실행

```bash
cd lab/liveportrait
python server.py
```

브라우저에서 `http://localhost:8000` 접속

### API 엔드포인트

| 메서드 | 경로 | 설명 |
|-------|------|------|
| GET | `/health` | 서버 상태 확인 |
| GET | `/expressions` | 사용 가능한 표정 목록 |
| GET | `/source-image` | 현재 로드된 소스 이미지 |
| POST | `/generate` | 표정 애니메이션 프레임 생성 |

### 프론트엔드 기능

- 5가지 표정 버튼 (웃어봐, 깜빡여봐, 말해봐, 놀라봐, 윙크해봐)
- 버튼 클릭 시 API 호출하여 프레임 생성
- 생성된 프레임을 FPS에 맞춰 순차 재생
- 애니메이션 완료 후 원본 이미지로 자동 복귀
- 모던 다크 테마 UI