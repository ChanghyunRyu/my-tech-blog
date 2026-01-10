# coding: utf-8
"""cuda-python 임포트 테스트"""

print("Testing cuda-python imports...")

# 방법 1
try:
    import cudart
    print("[OK] import cudart")
    print("  - cudart members:", [x for x in dir(cudart) if not x.startswith('_')][:10])
except Exception as e:
    print(f"[FAIL] import cudart: {e}")

# 방법 2
try:
    from cuda import cudart
    print("[OK] from cuda import cudart")
except Exception as e:
    print(f"[FAIL] from cuda import cudart: {e}")

# 방법 3
try:
    import cuda.cudart as cudart
    print("[OK] import cuda.cudart as cudart")
except Exception as e:
    print(f"[FAIL] import cuda.cudart: {e}")

# 방법 4
try:
    import cuda.runtime as cudart
    print("[OK] import cuda.runtime as cudart")
    print("  - cudart members:", [x for x in dir(cudart) if not x.startswith('_')][:10])
except Exception as e:
    print(f"[FAIL] import cuda.runtime: {e}")

# 방법 5
try:
    from cuda import runtime
    print("[OK] from cuda import runtime")
    print("  - runtime members:", [x for x in dir(runtime) if not x.startswith('_')][:10])
except Exception as e:
    print(f"[FAIL] from cuda import runtime: {e}")
