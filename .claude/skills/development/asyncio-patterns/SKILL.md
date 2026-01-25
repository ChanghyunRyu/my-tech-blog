---
name: asyncio-patterns
description: Python asyncio 고급 패턴 - TaskGroup, run_in_executor, Queue backpressure, 취소 처리
---

# Python Asyncio 패턴 가이드

## 핵심 원칙

1. **블로킹 호출은 executor로** - I/O 바운드 작업은 스레드풀 사용
2. **취소는 항상 처리** - `asyncio.CancelledError` 명시적 핸들링
3. **backpressure 관리** - Queue 크기 제한으로 메모리 보호

## 패턴 1: TaskGroup (Python 3.11+)

```python
async def process_batch(items: list[str]) -> list[Result]:
    """TaskGroup으로 병렬 처리 후 결과 수집"""
    results = []
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process_item(item)) for item in items]
    return [t.result() for t in tasks]
```

### 에러 처리
TaskGroup은 첫 예외 발생 시 나머지 태스크 자동 취소. 개별 에러 허용 시:
```python
async def safe_process(item):
    try:
        return await process_item(item)
    except Exception as e:
        return ErrorResult(item, e)
```

## 패턴 2: run_in_executor (블로킹 I/O)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 전역 executor (재사용)
_executor = ThreadPoolExecutor(max_workers=4)

async def load_file(path: str) -> bytes:
    """파일 읽기를 스레드풀에서 실행"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _sync_read, path)

def _sync_read(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()
```

### 주의사항
- CPU 바운드 → `ProcessPoolExecutor` 사용
- executor 함수는 동기 함수여야 함
- cleanup 시 `executor.shutdown(wait=True)`

## 패턴 3: Queue with Backpressure

```python
async def producer_consumer_with_backpressure():
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)  # 크기 제한!

    async def producer():
        for item in generate_items():
            await queue.put(item)  # 가득 차면 대기
        await queue.put(None)  # 종료 신호

    async def consumer():
        while (item := await queue.get()) is not None:
            await process(item)
            queue.task_done()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer())
        tg.create_task(consumer())
```

## 패턴 4: 취소 처리

```python
async def cancellable_operation():
    try:
        while True:
            await do_work()
    except asyncio.CancelledError:
        # 정리 작업 수행
        await cleanup()
        raise  # 반드시 재발생!
```

### shield로 취소 방지
```python
async def critical_section():
    # 취소되어도 완료까지 실행
    await asyncio.shield(save_to_database())
```

## 패턴 5: Timeout 처리

```python
async def with_timeout(coro, seconds: float):
    try:
        async with asyncio.timeout(seconds):
            return await coro
    except TimeoutError:
        return None  # 또는 적절한 fallback
```

## Anti-patterns (하지 말 것)

### 1. asyncio.run() 중첩
```python
# BAD - RuntimeError 발생
async def outer():
    asyncio.run(inner())  # X

# GOOD
async def outer():
    await inner()  # O
```

### 2. 블로킹 호출 직접 사용
```python
# BAD - 이벤트 루프 블로킹
async def bad():
    time.sleep(1)  # X

# GOOD
async def good():
    await asyncio.sleep(1)  # O
```

### 3. 취소 삼키기
```python
# BAD - 취소가 전파되지 않음
async def bad():
    try:
        await work()
    except asyncio.CancelledError:
        pass  # X - 취소 무시

# GOOD
async def good():
    try:
        await work()
    except asyncio.CancelledError:
        await cleanup()
        raise  # O - 재발생
```

## LLM-VA 프로젝트 적용

### MECoT 병렬 샘플링
```python
# src/erl/mecot/reasoner.py 참조
async def infer_delta_distribution_async(self, context: str):
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(self._async_sample(context))
            for _ in range(self.num_samples)
        ]
    return aggregate_results([t.result() for t in tasks])
```

### 오디오 스트리밍 파이프라인
```python
# Queue 기반 오디오 청크 처리
audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=50)

async def audio_producer(stream):
    async for chunk in stream:
        await audio_queue.put(chunk)

async def audio_consumer():
    while chunk := await audio_queue.get():
        await process_audio(chunk)
```

## 체크리스트

- [ ] 블로킹 I/O가 executor에서 실행되는가?
- [ ] CancelledError가 적절히 처리되는가?
- [ ] Queue에 maxsize가 설정되어 있는가?
- [ ] TaskGroup/gather의 에러 전파 방식이 의도와 맞는가?
- [ ] 리소스 정리(cleanup)가 finally/취소 핸들러에 있는가?
