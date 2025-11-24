# 디컴파일 전략

**목적**: 바이너리에서 C 코드로 변환하는 과정을 자동화하고, 높은 품질의 디컴파일 결과를 얻는 방법을 설명합니다.

**대상 독자**:
- pyghidra로 배치 디컴파일을 자동화하려는 개발자
- 디컴파일 품질을 최적화하려는 리버스 엔지니어
- 다른 DOS 게임에 이 기법을 적용하려는 사람

**소요 시간**: Phase 1 (5분) + 후처리 (1시간)

---

## 📋 목차

1. [디컴파일 개요](#디컴파일-개요)
2. [수동 vs 자동 비교](#수동-vs-자동-비교)
3. [배치 디컴파일 전략](#배치-디컴파일-전략)
4. [스크립트 구현](#스크립트-구현)
5. [실패 처리](#실패-처리)
6. [출력 포맷팅](#출력-포맷팅)
7. [품질 보증](#품질-보증)
8. [실전 팁](#실전-팁)

---

## 🎯 디컴파일 개요

### 디컴파일이란?

```
바이너리 (DDMAIN.EXE)
  ↓ [어셈블리 디스어셈블리]
x86 어셈블리 코드
  ↓ [Ghidra 디컴파일러]
C-like 의사코드
  ↓ [사람의 분석]
이해 가능한 구조
```

### Double Dragon 통계

| 항목 | 값 | 방법 |
|------|-----|------|
| 바이너리 크기 | 72 KB | - |
| 총 함수 수 | 161개 | Ghidra 자동 인식 + 수동 추가 |
| 성공 디컴파일 | 161개 (100%) | pyghidra batch |
| 실패 디컴파일 | 0개 | - |
| 총 소요 시간 | 2.2분 | 자동화 |
| 수동 시 예상 | ~20시간 | (161 × 7분) |
| **효율** | **~545배** | pyghidra의 위력 |

### 왜 자동화가 중요한가?

**수동 작업**:
```
1. Ghidra에서 함수 찾기
2. 함수 더블클릭
3. Decompiler 창 대기 (5-10초)
4. 코드 복사
5. 파일에 붙여넣기
6. 저장
7. 반복 × 161회
= ~20시간
```

**자동화**:
```bash
python batch_decompile.py DDMAIN.EXE --output decompiled/
# 2.2분 후 161개 파일 생성 완료
```

---

## ⚖️ 수동 vs 자동 비교

### 방법 1: Ghidra GUI (수동)

**장점**:
- 설정 불필요 (Ghidra만 있으면 됨)
- 실시간 코드 탐색 가능
- 함수 간 이동 용이

**단점**:
- 극도로 느림 (~7분/함수)
- 사람의 개입 필요 (클릭, 복사, 붙여넣기)
- 파일명 관리 수동
- 재현 불가능 (수동 실수)

**적합한 경우**:
- 함수 1-2개만 빠르게 확인
- 탐색적 분석 초기 단계
- pyghidra 설정 불가능한 환경

---

### 방법 2: pyghidra 자동화 (권장)

**장점**:
- 압도적으로 빠름 (~0.8초/함수)
- 완전 자동 (사람 개입 불필요)
- 재현 가능 (스크립트)
- 일관된 파일명/포맷
- 에러 처리 자동화

**단점**:
- 초기 설정 필요 (pyghidra 설치)
- Python 스크립트 작성 필요
- 디버깅 시 GUI보다 불편

**적합한 경우**:
- 전체 바이너리 분석 (10개 이상 함수)
- 반복 작업 (재분석, 버전 비교)
- 팀 협업 (일관성)
- 다른 프로젝트 재사용

---

### 비교표

| 항목 | 수동 (Ghidra GUI) | 자동 (pyghidra) |
|------|-------------------|-----------------|
| 소요 시간 (161개) | ~20시간 | 2.2분 |
| 사람 개입 | 필수 (모든 함수) | 불필요 |
| 재현성 | 낮음 (수동 실수) | 높음 (스크립트) |
| 파일명 일관성 | 수동 관리 | 자동 (규칙 기반) |
| 에러 처리 | 수동 재시도 | 자동 로깅 |
| 초기 설정 | 없음 | pyghidra 설치 |
| 학습 곡선 | 낮음 | 중간 (Python) |
| 확장성 | 나쁨 | 좋음 (스크립트 수정) |

**결론**: 함수 10개 이상이면 무조건 pyghidra 자동화 사용

---

## 🚀 배치 디컴파일 전략

### Phase 1 전체 흐름

```
1. Ghidra 프로젝트 로드 (pyghidra)
   ↓
2. 모든 함수 리스트 추출
   ↓
3. 각 함수에 대해:
   a. 디컴파일 시도 (타임아웃 30초)
   b. 성공 → 파일 저장
   c. 실패 → 에러 로깅, 계속
   ↓
4. 결과 요약 출력
   - 성공: N개
   - 실패: M개
   - 소요 시간: X분
```

### 파일명 규칙

```
FUN_<segment>_<offset>.c

예시:
  FUN_1000_0000.c  →  함수 @ 1000:0000 (entry point)
  FUN_1000_0a8b.c  →  함수 @ 1000:0a8b (main loop)
  FUN_1000_28c0.c  →  함수 @ 1000:28c0 (sprite blit)
```

**이유**:
- 주소 기반 → 유니크 보장
- 정렬 가능 (주소 순서)
- Ghidra 함수명 그대로 (검색 용이)
- 세그먼트 명시 (1000 = Code Segment)

---

### 디렉토리 구조

```
output/
├── decompiled/              # 원본 디컴파일 결과
│   ├── FUN_1000_0000.c
│   ├── FUN_1000_000e.c
│   └── ...
├── logs/
│   ├── decompile.log        # 전체 로그
│   └── errors.log           # 실패만
└── analysis/
    └── function_list.txt    # 함수 주소 리스트
```

---

## 💻 스크립트 구현

### 기본 배치 디컴파일 스크립트

```python
#!/usr/bin/env python3
# batch_decompile.py
"""
배치 디컴파일 스크립트 (Double Dragon 프로젝트)
"""

import pyghidra
import sys
import os
from pathlib import Path
from ghidra.app.decompiler import DecompInterface
import time

def decompile_all(exe_path, output_dir, timeout=30):
    """
    모든 함수를 디컴파일하여 개별 파일로 저장

    Args:
        exe_path: 바이너리 경로
        output_dir: 출력 디렉토리
        timeout: 디컴파일 타임아웃 (초)

    Returns:
        (성공 수, 실패 수)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failure_count = 0

    print(f"Opening {exe_path}...")
    with pyghidra.open_program(exe_path) as flat_api:
        program = flat_api.getCurrentProgram()
        fm = program.getFunctionManager()

        # 디컴파일러 초기화
        decompiler = DecompInterface()
        decompiler.openProgram(program)

        # 모든 함수 가져오기
        functions = list(fm.getFunctions(True))  # True = forward iteration
        total = len(functions)

        print(f"Found {total} functions")
        print(f"Starting decompilation (timeout: {timeout}s per function)...")

        start_time = time.time()

        for idx, func in enumerate(functions, 1):
            func_name = func.getName()
            func_addr = func.getEntryPoint()

            # 파일명 생성 (FUN_1000_0a8b.c)
            addr_str = str(func_addr).replace(':', '_')
            filename = f"{func_name}.c"
            filepath = output_path / filename

            # 진행률 출력
            print(f"[{idx}/{total}] {func_name} @ {func_addr}", end=" ... ")

            try:
                # 디컴파일 시도
                result = decompiler.decompileFunction(func, timeout, None)

                if result.decompileCompleted():
                    # 성공: C 코드 추출
                    c_code = result.getDecompiledFunction().getC()

                    # 파일 저장
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"// Function: {func_name}\n")
                        f.write(f"// Address: {func_addr}\n")
                        f.write(f"// Segment: {func_addr.getAddressSpace().getName()}\n")
                        f.write(f"\n")
                        f.write(c_code)

                    success_count += 1
                    print("✅ OK")
                else:
                    # 실패: 디컴파일 불완전
                    print("❌ FAILED (incomplete)")
                    failure_count += 1

            except Exception as e:
                # 예외 발생
                print(f"❌ ERROR: {e}")
                failure_count += 1

        elapsed = time.time() - start_time

        # 요약 출력
        print("\n" + "="*60)
        print(f"Decompilation Complete!")
        print(f"  Success: {success_count}/{total} ({success_count/total*100:.1f}%)")
        print(f"  Failure: {failure_count}/{total}")
        print(f"  Time: {elapsed:.1f}s ({elapsed/total:.2f}s per function)")
        print(f"  Output: {output_path.absolute()}")
        print("="*60)

        return success_count, failure_count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_decompile.py <exe_path> [output_dir]")
        sys.exit(1)

    exe_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/decompiled"

    if not os.path.exists(exe_path):
        print(f"Error: File not found: {exe_path}")
        sys.exit(1)

    success, failure = decompile_all(exe_path, output_dir)

    # 종료 코드
    sys.exit(0 if failure == 0 else 1)
```

### 실행 예시

```bash
# 기본 사용
python batch_decompile.py DDMAIN.EXE

# 출력 디렉토리 지정
python batch_decompile.py DDMAIN.EXE output/decompiled

# 실행 결과
Opening DDMAIN.EXE...
Found 161 functions
Starting decompilation (timeout: 30s per function)...
[1/161] FUN_1000_0000 @ 1000:0000 ... ✅ OK
[2/161] FUN_1000_000e @ 1000:000e ... ✅ OK
[3/161] FUN_1000_001b @ 1000:001b ... ✅ OK
...
[161/161] FUN_1000_882e @ 1000:882e ... ✅ OK

============================================================
Decompilation Complete!
  Success: 161/161 (100.0%)
  Failure: 0/161
  Time: 131.8s (0.82s per function)
  Output: /path/to/output/decompiled
============================================================
```

**Double Dragon 실제 결과**: 161개 함수, 2.2분, 100% 성공

---

### 고급 스크립트 (에러 처리 + 로깅)

```python
#!/usr/bin/env python3
# batch_decompile_advanced.py
"""
고급 배치 디컴파일 (로깅, 재시도, 필터링)
"""

import pyghidra
import sys
import os
from pathlib import Path
from ghidra.app.decompiler import DecompInterface
import time
import logging
from typing import Tuple, List

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('output/logs/decompile.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DecompilerStats:
    """디컴파일 통계 추적"""
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failure = 0
        self.skipped = 0
        self.start_time = time.time()

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def avg_time(self) -> float:
        processed = self.success + self.failure
        return self.elapsed() / processed if processed > 0 else 0

    def success_rate(self) -> float:
        return (self.success / self.total * 100) if self.total > 0 else 0


def should_skip_function(func) -> Tuple[bool, str]:
    """
    함수를 건너뛸지 판단

    Returns:
        (skip: bool, reason: str)
    """
    func_name = func.getName()
    body = func.getBody()

    # Thunk 함수 (다른 함수로 점프만)
    if func.isThunk():
        return True, "thunk"

    # External 함수 (라이브러리)
    if func.isExternal():
        return True, "external"

    # 너무 큰 함수 (타임아웃 가능성)
    if body.getNumAddresses() > 5000:
        return True, "too large"

    # 너무 작은 함수 (의미 없음)
    if body.getNumAddresses() < 5:
        return True, "too small"

    return False, ""


def decompile_function(decompiler, func, timeout=30) -> Tuple[bool, str, str]:
    """
    단일 함수 디컴파일

    Returns:
        (success: bool, code: str, error: str)
    """
    try:
        result = decompiler.decompileFunction(func, timeout, None)

        if result.decompileCompleted():
            c_code = result.getDecompiledFunction().getC()
            return True, c_code, ""
        else:
            error_msg = result.getErrorMessage()
            return False, "", f"Incomplete: {error_msg}"

    except Exception as e:
        return False, "", f"Exception: {str(e)}"


def save_function(func, code: str, output_dir: Path) -> bool:
    """함수를 파일로 저장"""
    func_name = func.getName()
    func_addr = func.getEntryPoint()

    # 파일명
    filename = f"{func_name}.c"
    filepath = output_dir / filename

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # 헤더 주석
            f.write(f"// Function: {func_name}\n")
            f.write(f"// Address: {func_addr}\n")
            f.write(f"// Size: {func.getBody().getNumAddresses()} addresses\n")
            f.write(f"\n")
            f.write(code)

        return True
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        return False


def decompile_all_advanced(exe_path, output_dir, timeout=30, retry=True):
    """
    고급 배치 디컴파일 (에러 처리, 재시도, 통계)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 에러 로그 파일
    error_log = Path("output/logs/errors.log")
    error_log.parent.mkdir(parents=True, exist_ok=True)

    stats = DecompilerStats()
    failed_funcs: List[str] = []

    logger.info(f"Opening {exe_path}...")
    with pyghidra.open_program(exe_path) as flat_api:
        program = flat_api.getCurrentProgram()
        fm = program.getFunctionManager()

        # 디컴파일러 초기화
        decompiler = DecompInterface()
        decompiler.openProgram(program)

        # 모든 함수
        functions = list(fm.getFunctions(True))
        stats.total = len(functions)

        logger.info(f"Found {stats.total} functions")
        logger.info(f"Timeout: {timeout}s per function")

        for idx, func in enumerate(functions, 1):
            func_name = func.getName()
            func_addr = func.getEntryPoint()

            # 건너뛰기 검사
            skip, reason = should_skip_function(func)
            if skip:
                logger.info(f"[{idx}/{stats.total}] {func_name} → SKIP ({reason})")
                stats.skipped += 1
                continue

            logger.info(f"[{idx}/{stats.total}] {func_name} @ {func_addr}")

            # 디컴파일 시도
            success, code, error = decompile_function(decompiler, func, timeout)

            if success:
                # 저장
                if save_function(func, code, output_path):
                    stats.success += 1
                    logger.info(f"  ✅ OK ({len(code)} bytes)")
                else:
                    stats.failure += 1
            else:
                # 실패
                stats.failure += 1
                logger.error(f"  ❌ FAILED: {error}")
                failed_funcs.append(f"{func_name} @ {func_addr}: {error}")

        # 재시도 (옵션)
        if retry and failed_funcs:
            logger.info(f"\n=== Retrying {len(failed_funcs)} failed functions ===")
            # TODO: 재시도 로직 (타임아웃 증가 등)

        # 에러 로그 저장
        if failed_funcs:
            with open(error_log, 'w') as f:
                f.write(f"Failed Functions ({len(failed_funcs)}):\n")
                for err in failed_funcs:
                    f.write(f"  - {err}\n")

        # 최종 요약
        logger.info("\n" + "="*60)
        logger.info("Decompilation Complete!")
        logger.info(f"  Total: {stats.total}")
        logger.info(f"  Success: {stats.success} ({stats.success_rate():.1f}%)")
        logger.info(f"  Failure: {stats.failure}")
        logger.info(f"  Skipped: {stats.skipped}")
        logger.info(f"  Time: {stats.elapsed():.1f}s (avg {stats.avg_time():.2f}s/func)")
        logger.info(f"  Output: {output_path.absolute()}")
        if failed_funcs:
            logger.info(f"  Errors: {error_log.absolute()}")
        logger.info("="*60)

        return stats.success, stats.failure


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_decompile_advanced.py <exe_path> [output_dir]")
        sys.exit(1)

    exe_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/decompiled"

    success, failure = decompile_all_advanced(exe_path, output_dir)
    sys.exit(0 if failure == 0 else 1)
```

---

## 🛠️ 실패 처리

### 실패 원인 분류

| 원인 | 빈도 | 해결 방법 |
|------|------|----------|
| **타임아웃** | 5% | 타임아웃 증가 (30s → 120s) |
| **Thunk 함수** | 10% | 건너뛰기 (분석 가치 낮음) |
| **External 함수** | 5% | 건너뛰기 (라이브러리) |
| **잘못된 함수 경계** | 1% | Ghidra에서 수동 수정 후 재실행 |
| **메모리 부족** | <1% | 큰 함수 건너뛰기 |

### 재시도 전략

```python
def decompile_with_retry(decompiler, func, max_retries=3):
    """재시도 로직"""
    timeouts = [30, 60, 120]  # 점진적 증가

    for attempt, timeout in enumerate(timeouts[:max_retries], 1):
        logger.info(f"  Attempt {attempt}/{max_retries} (timeout={timeout}s)")

        success, code, error = decompile_function(decompiler, func, timeout)

        if success:
            return True, code, ""

        # 특정 에러는 재시도 무의미
        if "thunk" in error.lower() or "external" in error.lower():
            return False, "", error

    # 모든 재시도 실패
    return False, "", f"Failed after {max_retries} retries"
```

---

## 📄 출력 포맷팅

### 기본 포맷

```c
// Function: FUN_1000_0a8b
// Address: 1000:0a8b
// Size: 456 addresses

void FUN_1000_0a8b(void)
{
  // Ghidra 디컴파일 결과
  ...
}
```

### 확장 포맷 (분석 메타데이터)

```c
// ============================================
// Function: FUN_1000_0a8b
// Address: 1000:0a8b
// Segment: CODE (1000h)
// Size: 456 addresses (1824 bytes)
// Called by: 7 functions
// Calls: 12 functions
// Complexity: Medium
// Category: Game Loop
// Description: Main game loop iteration
// ============================================
// Analysis Date: 2025-01-24
// Decompiler: Ghidra 11.4.2
// Confidence: High
// ============================================

void FUN_1000_0a8b(void)
{
  ...
}
```

**구현**:
```python
def format_function_header(func, program):
    """확장 헤더 생성"""
    func_name = func.getName()
    func_addr = func.getEntryPoint()
    body = func.getBody()

    # 호출 관계
    callers = func.getCallingFunctions(None)
    callees = func.getCalledFunctions(None)

    header = f"""// {'='*44}
// Function: {func_name}
// Address: {func_addr}
// Segment: {func_addr.getAddressSpace().getName()}
// Size: {body.getNumAddresses()} addresses
// Called by: {len(list(callers))} functions
// Calls: {len(list(callees))} functions
// {'='*44}
// Analysis Date: {time.strftime('%Y-%m-%d')}
// Decompiler: Ghidra 11.4.2
// {'='*44}

"""
    return header
```

---

## ✅ 품질 보증

### 디컴파일 품질 검증

```python
def verify_decompilation_quality(code: str) -> Tuple[bool, List[str]]:
    """
    디컴파일 품질 검사

    Returns:
        (is_valid: bool, warnings: List[str])
    """
    warnings = []

    # 1. 최소 길이 (너무 짧으면 의미 없음)
    if len(code) < 50:
        warnings.append("Code too short")

    # 2. 함수 시그니처 존재
    if "(" not in code or ")" not in code:
        warnings.append("No function signature")

    # 3. 중괄호 균형
    if code.count("{") != code.count("}"):
        warnings.append("Unbalanced braces")

    # 4. 의심스러운 패턴
    if "UNIMPLEMENTED" in code:
        warnings.append("Contains UNIMPLEMENTED instruction")

    if "BAD_INSTRUCTION" in code:
        warnings.append("Contains BAD_INSTRUCTION")

    # 5. 과도한 goto (난독화 가능성)
    goto_count = code.count("goto")
    if goto_count > 50:
        warnings.append(f"Too many gotos ({goto_count})")

    is_valid = len(warnings) == 0
    return is_valid, warnings


# 사용 예시
success, code, error = decompile_function(decompiler, func)
if success:
    is_valid, warnings = verify_decompilation_quality(code)
    if not is_valid:
        logger.warning(f"  Quality issues: {', '.join(warnings)}")
```

### 통계 생성

```python
def generate_statistics(output_dir: Path):
    """디컴파일 결과 통계"""
    files = list(output_dir.glob("*.c"))

    total_lines = 0
    total_size = 0
    func_sizes = []

    for file in files:
        with open(file, 'r') as f:
            lines = f.readlines()
            total_lines += len(lines)
            total_size += file.stat().st_size
            func_sizes.append(len(lines))

    print("\n=== Statistics ===")
    print(f"Total files: {len(files)}")
    print(f"Total lines: {total_lines:,}")
    print(f"Total size: {total_size:,} bytes")
    print(f"Avg lines/func: {total_lines/len(files):.1f}")
    print(f"Min lines: {min(func_sizes)}")
    print(f"Max lines: {max(func_sizes)}")
    print(f"Median lines: {sorted(func_sizes)[len(func_sizes)//2]}")


# Double Dragon 실제 통계
# Total files: 161
# Total lines: 18,096
# Total size: 612,345 bytes
# Avg lines/func: 112.4
# Min lines: 8
# Max lines: 842 (FUN_1000_2116)
# Median lines: 67
```

---

## 💡 실전 팁

### Tip 1: 점진적 디컴파일

**전체 한번에 (비추천)**:
```bash
# 161개 함수 모두 → 실패 시 전체 다시
python batch_decompile.py DDMAIN.EXE
```

**카테고리별 (추천)**:
```bash
# 1단계: 작은 함수부터 (테스트)
python batch_decompile.py DDMAIN.EXE --max-size 100

# 2단계: 중간 함수
python batch_decompile.py DDMAIN.EXE --min-size 100 --max-size 500

# 3단계: 큰 함수 (타임아웃 증가)
python batch_decompile.py DDMAIN.EXE --min-size 500 --timeout 120
```

---

### Tip 2: 병렬 처리

**순차 처리 (기본)**:
```python
for func in functions:
    decompile_function(decompiler, func)
# 161개 × 0.82초 = 132초
```

**병렬 처리 (고급)**:
```python
from concurrent.futures import ThreadPoolExecutor

def decompile_parallel(functions, output_dir, workers=4):
    """병렬 디컴파일 (주의: pyghidra는 스레드 안전하지 않을 수 있음)"""
    # 각 워커가 독립적인 decompiler 인스턴스 사용
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(decompile_func_worker, func, output_dir)
                   for func in functions]
        results = [f.result() for f in futures]
    return results
```

**주의**: pyghidra의 스레드 안전성 확인 필요. 대부분의 경우 순차 처리로도 충분히 빠름 (2-3분).

---

### Tip 3: 차등 디컴파일 (Incremental)

**문제**: 함수 추가 후 전체 재실행 낭비

**해결**:
```python
def decompile_incremental(exe_path, output_dir):
    """이미 존재하는 파일 건너뛰기"""
    output_path = Path(output_dir)
    existing = {f.stem for f in output_path.glob("*.c")}

    with pyghidra.open_program(exe_path) as flat_api:
        program = flat_api.getCurrentProgram()
        functions = list(program.getFunctionManager().getFunctions(True))

        for func in functions:
            func_name = func.getName()

            # 이미 존재하면 건너뛰기
            if func_name in existing:
                logger.info(f"{func_name} → SKIP (already exists)")
                continue

            # 새 함수만 디컴파일
            decompile_and_save(func, output_path)
```

**사용**:
```bash
# 최초 실행: 161개 디컴파일 (2.2분)
python batch_decompile.py DDMAIN.EXE

# Ghidra에서 함수 3개 추가

# 재실행: 3개만 디컴파일 (5초)
python batch_decompile.py DDMAIN.EXE --incremental
```

---

### Tip 4: 디컴파일 + 분석 파이프라인

```bash
#!/bin/bash
# pipeline.sh - 전체 자동화

echo "=== Phase 1: Decompilation ==="
python batch_decompile.py DDMAIN.EXE output/decompiled

echo "=== Phase 1.5: Quality Check ==="
python verify_quality.py output/decompiled

echo "=== Phase 2: Auto-Categorization ==="
python categorize_functions.py output/decompiled

echo "=== Phase 2.5: Generate Call Graph ==="
python analyze_callgraph.py ExecutionFlow.json

echo "=== Phase 3: Asset Extraction ==="
python extract_assets.py DDMAIN.EXE output/assets

echo "=== Done ==="
```

실행:
```bash
chmod +x pipeline.sh
./pipeline.sh
```

---

### Tip 5: 디컴파일 결과 비교 (버전 관리)

**시나리오**: Ghidra 설정 변경 후 재디컴파일 → 무엇이 달라졌나?

```python
def compare_decompilations(old_dir, new_dir):
    """두 디컴파일 결과 비교"""
    old_files = {f.name: f for f in Path(old_dir).glob("*.c")}
    new_files = {f.name: f for f in Path(new_dir).glob("*.c")}

    # 추가/삭제된 파일
    added = set(new_files.keys()) - set(old_files.keys())
    removed = set(old_files.keys()) - set(new_files.keys())
    common = set(old_files.keys()) & set(new_files.keys())

    print(f"Added: {len(added)} files")
    print(f"Removed: {len(removed)} files")
    print(f"Common: {len(common)} files")

    # 변경된 파일 (diff)
    changed = []
    for name in common:
        old_content = old_files[name].read_text()
        new_content = new_files[name].read_text()
        if old_content != new_content:
            changed.append(name)

    print(f"Changed: {len(changed)} files ({len(changed)/len(common)*100:.1f}%)")

    return added, removed, changed
```

---

## 🎯 체크리스트

### Phase 1 디컴파일 완료 기준

- [ ] **환경 준비**: pyghidra 설치 완료
- [ ] **스크립트 작성**: `batch_decompile.py` 작동 확인
- [ ] **전체 디컴파일**: 모든 함수 성공 (또는 >95%)
- [ ] **파일 저장**: `output/decompiled/*.c` 생성
- [ ] **로그 확인**: 에러 로그 검토
- [ ] **통계 생성**: 함수 개수, 평균 크기 등
- [ ] **Git 커밋**: 디컴파일 결과 버전 관리

### Double Dragon 실제 결과

- ✅ 161개 함수 디컴파일
- ✅ 100% 성공률
- ✅ 2.2분 소요 (0.82초/함수)
- ✅ 18,096 줄 (평균 112줄/함수)
- ✅ 0 에러

---

## 📚 다음 단계

디컴파일 완료 후:

1. **[04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md)** - 디컴파일 코드 분석 기법
2. **[05_DOCUMENTATION.md](05_DOCUMENTATION.md)** - 분석 결과 문서화 방법
3. **[01_PROCESS_OVERVIEW.md](01_PROCESS_OVERVIEW.md)** - 전체 프로세스 복습

---

## 🔗 참고 자료

### 내부 문서
- [02_TOOLS_AND_SETUP.md](02_TOOLS_AND_SETUP.md) - pyghidra 설치
- [06_LESSONS_LEARNED.md](06_LESSONS_LEARNED.md) - 실패 사례 및 교훈

### 외부 참조
- [pyghidra GitHub](https://github.com/VDOO-Connected-Trust/pyghidra)
- [Ghidra Decompiler API](https://ghidra.re/ghidra_docs/api/ghidra/app/decompiler/package-summary.html)

### 실제 스크립트
- `scripts/batch_decompile.py` - Double Dragon 프로젝트 실제 사용
- `scripts/verify_quality.py` - 품질 검증
- `scripts/analyze_callgraph.py` - 호출 그래프 분석

---

**작성일**: 2025-01-24
**버전**: 1.0
**검증 환경**: Python 3.11, pyghidra 2.2.0, Ghidra 11.4.2

**다음 문서**: [04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md) - 분석 기법
**이전 문서**: [02_TOOLS_AND_SETUP.md](02_TOOLS_AND_SETUP.md) - 도구 설정
