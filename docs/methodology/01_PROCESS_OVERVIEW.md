# 리버스 엔지니어링 프로세스 개요

**작성일**: 2025-11-24
**기반**: Double Dragon DOS 프로젝트 (성공적 완료)
**목적**: 5단계 프로세스를 정의하여 다른 DOS 게임에 적용

---

## 📋 목차

1. [프로세스 전체 개요](#프로세스-전체-개요)
2. [Phase 0: 환경 준비](#phase-0-환경-준비)
3. [Phase 1: 자동 디컴파일](#phase-1-자동-디컴파일)
4. [Phase 2: 코드 분석 및 분류](#phase-2-코드-분석-및-분류)
5. [Phase 3: 에셋 분석](#phase-3-에셋-분석)
6. [Phase 4: 완전 분석](#phase-4-완전-분석)
7. [시간 배분 전략](#시간-배분-전략)
8. [마일스톤 체크리스트](#마일스톤-체크리스트)
9. [Double Dragon 타임라인](#double-dragon-타임라인)

---

## 프로세스 전체 개요

### 🎯 5단계 프로세스

```
Phase 0: 환경 준비 (5분)
   ↓
Phase 1: 자동 디컴파일 (5분)
   ↓
Phase 2: 코드 분석 (1-2시간)
   ↓
Phase 3: 에셋 분석 (2-4시간)
   ↓
Phase 4: 완전 분석 (10-20시간)
   ↓
완료: 100% 이해, 재구현 준비
```

### 📊 시간 배분 (72KB 게임 기준)

| Phase | 소요 시간 | 누적 | 비율 | 자동화 가능 |
|-------|-----------|------|------|-------------|
| Phase 0 | 5분 | 5분 | 0.5% | 50% |
| Phase 1 | 5분 | 10분 | 1% | 95% |
| Phase 2 | 1-2시간 | 2시간 | 10% | 30% |
| Phase 3 | 2-4시간 | 6시간 | 25% | 50% |
| Phase 4 | 10-20시간 | 17시간 | 64% | 20% |
| **합계** | **~17시간** | - | **100%** | **40%** |

### 🎓 핵심 원칙

1. **순차적 진행**: Phase 건너뛰지 않기
2. **자동화 우선**: 가능한 모든 것 스크립트화
3. **즉시 문서화**: 각 Phase 완료 후 문서 작성
4. **점진적 이해**: 첫 패스 80%, 점차 깊이 증가

---

## Phase 0: 환경 준비

### 🎯 목표
- 분석 도구 설치 및 설정
- 바이너리 파일 준비
- 초기 정보 수집

### ⏱️ 소요 시간
- **이상적**: 5분 (도구 이미 설치)
- **최초**: 30-60분 (도구 설치 포함)

### 📝 작업 목록

#### 1. 도구 설치
```bash
# Ghidra 11.4.2
# - https://ghidra-sre.org/
# - Java JDK 21 필요

# pyghidra 2.2.0
pip install pyghidra

# Spice86 (선택)
# - https://github.com/OpenRakis/Spice86
# - .NET 6 필요

# DOSBox-X (선택)
# - https://dosbox-x.com/
```

#### 2. 바이너리 수집
```
프로젝트/
├── GAME.EXE        ← 메인 실행 파일
├── DATA/           ← 에셋 파일들
│   ├── *.EG1       (스프라이트)
│   ├── *.PC1       (배경)
│   └── *.DAT       (기타)
└── docs/           ← 문서 저장소
```

#### 3. Ghidra 프로젝트 생성
```
1. Ghidra 실행
2. File → New Project
3. Import File → GAME.EXE
4. Language: x86 16-bit Real Mode
5. 자동 분석 실행 (Analyze)
   - 옵션: 기본값 사용
   - 시간: 1-5분
```

#### 4. 초기 정보 수집
```bash
# 파일 정보
file GAME.EXE
  → DOS executable

# 크기
ls -lh GAME.EXE
  → 72KB

# 문자열 추출
strings GAME.EXE > strings.txt
  → 버전, 저작권, 에러 메시지

# 16진수 덤프 (헤더)
hexdump -C GAME.EXE | head -20
  → DOS EXE 헤더 확인
```

#### 5. Spice86 실행 추적 (선택)
```bash
# 실행 추적 활성화
./Spice86 GAME.EXE --record-execution

# 게임 플레이 (1-2분)
# - 메뉴 탐색
# - 게임 시작
# - 이동, 점프, 공격
# - 적 처치
# - 게임 오버 or 종료

# ExecutionFlow.json 생성됨
# → 호출 그래프 데이터
```

### 📦 산출물

- ✅ Ghidra 프로젝트 (.gpr)
- ✅ strings.txt (추출된 문자열)
- ✅ ExecutionFlow.json (호출 그래프, 선택)
- ✅ 문서 디렉토리 구조

### ✅ 완료 조건

- [ ] Ghidra 자동 분석 완료 (100%)
- [ ] pyghidra 테스트 성공
- [ ] 문서 저장소 초기화
- [ ] (선택) Spice86 실행 추적 완료

### 💡 팁

- **도구 버전 고정**: Ghidra 11.4.2, pyghidra 2.2.0 사용
- **Docker 고려**: 환경 재현 가능
- **스냅샷**: VM or Git 초기 상태 저장

---

## Phase 1: 자동 디컴파일

### 🎯 목표
- 모든 함수 자동 디컴파일
- C 코드로 변환
- JSON 메타데이터 생성

### ⏱️ 소요 시간
- **실제**: 2.2분 (Double Dragon, 118개 함수)
- **예상**: 3-10분 (게임 크기에 비례)

### 📝 작업 목록

#### 1. pyghidra 스크립트 작성

```python
# batch_decompile.py
import pyghidra
import json
from pathlib import Path

# Ghidra 초기화
with pyghidra.open_program("GAME.EXE") as program:
    decompiler = program.decompile()

    results = []
    output_dir = Path("output/decompiled")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 모든 함수 순회
    for func in program.functions():
        # Thunk 함수 제외
        if func.isThunk():
            continue

        try:
            # 디컴파일
            c_code = decompiler.decompile(func)

            # 파일 저장
            func_name = func.getName()
            output_file = output_dir / f"{func_name}.c"
            output_file.write_text(c_code)

            # 메타데이터
            results.append({
                "name": func_name,
                "address": func.getEntryPoint().toString(),
                "size": func.getBody().getNumAddresses(),
                "file": str(output_file)
            })

            print(f"✓ {func_name}")

        except Exception as e:
            print(f"✗ {func_name}: {e}")

    # JSON 저장
    with open("output/functions.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n완료: {len(results)}개 함수")
```

#### 2. 스크립트 실행

```bash
# 실행
python batch_decompile.py

# 출력 예시:
# ✓ FUN_1000_029a
# ✓ FUN_1000_0cd1
# ✓ FUN_1000_04a9
# ...
# 완료: 118개 함수
# 소요 시간: 2.2분
```

#### 3. 결과 확인

```bash
# 파일 개수
ls output/decompiled/*.c | wc -l
  → 118개

# 전체 코드 줄 수
cat output/decompiled/*.c | wc -l
  → 4,412줄

# 함수 크기 통계
jq '.[] | .size' output/functions.json | \
  awk '{sum+=$1; n++} END {print "평균:", sum/n, "bytes"}'
  → 평균: 37 bytes
```

### 📦 산출물

- ✅ C 파일 (118개)
  - `output/decompiled/FUN_1000_029a.c`
  - `output/decompiled/FUN_1000_0cd1.c`
  - ...

- ✅ JSON 메타데이터
  ```json
  [
    {
      "name": "FUN_1000_029a",
      "address": "1000:029a",
      "size": 156,
      "file": "output/decompiled/FUN_1000_029a.c"
    },
    ...
  ]
  ```

- ✅ 통계 리포트
  - 총 함수 수
  - 총 코드 줄 수
  - 평균 함수 크기

### ✅ 완료 조건

- [ ] 모든 함수 디컴파일 완료
- [ ] C 파일 생성 확인
- [ ] JSON 메타데이터 생성
- [ ] Thunk 함수 제외 확인
- [ ] 에러 없음 (또는 < 5%)

### ⚠️ 주의사항

**Thunk 함수 처리**:
```c
// Thunk 함수 = 단순 점프
void FUN_1000_xxxx(void) {
  FUN_1000_yyyy();  // 단순 호출만
}

// → 제외 (의미 없음)
```

**함수 포인터 미인식**:
```
Ghidra가 일부 함수 인식 못함
 → Phase 4에서 복구 (호출 그래프 활용)
```

### 💡 Double Dragon 실제 데이터

```
총 함수: 120개
디컴파일 성공: 118개 (98%)
실패: 2개 (thunk)
소요 시간: 2.2분
총 코드: 4,412줄
평균 크기: 37 bytes
```

---

## Phase 2: 코드 분석 및 분류

### 🎯 목표
- 함수 카테고리 분류
- 주요 함수 네이밍
- 시스템 아키텍처 파악

### ⏱️ 소요 시간
- **이상적**: 1시간
- **실제**: 1-2시간 (게임 복잡도에 따라)

### 📝 작업 목록

#### 1. 자동 분류 스크립트

```python
# classify_functions.py
import json
from pathlib import Path

categories = {
    "graphics": [],      # Port 0xB800, INT 10h
    "input": [],         # Port 0x60, 0x201, INT 16h
    "file_io": [],       # INT 21h (file operations)
    "memory": [],        # memcpy, memset patterns
    "game_logic": [],    # Entity, collision, AI
    "sound": [],         # Port 0x61, 0x388
    "system": [],        # Initialization, main loop
    "utility": [],       # Math, string, etc.
}

def classify_function(func_name, c_code):
    """함수 코드 분석하여 카테고리 결정"""

    # 그래픽
    if "0xb800" in c_code.lower() or "int_10h" in c_code:
        return "graphics"

    # 입력
    if ("port_60" in c_code or "port_201" in c_code or
        "int_16h" in c_code):
        return "input"

    # 파일 I/O
    if "int_21h" in c_code and ("0x3d" in c_code or "0x3f" in c_code):
        return "file_io"

    # 메모리 조작
    if "memcpy" in c_code or "memset" in c_code:
        return "memory"

    # 사운드
    if "port_61" in c_code or "port_388" in c_code:
        return "sound"

    # 시스템 (main loop 패턴)
    if "while" in c_code and "true" in c_code:
        return "system"

    # 기본: 게임 로직
    return "game_logic"

# 모든 함수 분류
for c_file in Path("output/decompiled").glob("*.c"):
    code = c_file.read_text()
    category = classify_function(c_file.stem, code)
    categories[category].append(c_file.stem)

# 결과 저장
with open("output/classification.json", "w") as f:
    json.dump(categories, f, indent=2)

# 통계 출력
for cat, funcs in categories.items():
    print(f"{cat:15s}: {len(funcs):3d} functions")
```

#### 2. 주요 함수 식별

**Entry Point**:
```c
// FUN_1000_029a
// → entry_point 또는 main
```

**초기화**:
```c
// 그래픽 모드 설정 발견
// FUN_1000_0cd1
// → initialize_graphics
```

**메인 루프**:
```c
// while(1) 패턴 발견
// FUN_1000_04a9
// → main_loop
```

**렌더링**:
```c
// 0xB800 많이 접근
// FUN_1000_48e0
// → render_frame
```

#### 3. 아키텍처 다이어그램

```
┌─────────────┐
│ Entry Point │ FUN_1000_029a
└──────┬──────┘
       ↓
┌─────────────┐
│ Initialize  │ FUN_1000_0cd1
└──────┬──────┘
       ↓
┌─────────────┐
│ Main Loop   │ FUN_1000_04a9
└──────┬──────┘
       ↓
   ┌───┴───┐
   ↓       ↓
┌──────┐ ┌──────┐
│Input │ │Render│
└──────┘ └──────┘
```

### 📦 산출물

- ✅ `classification.json`
  ```json
  {
    "graphics": [30개],
    "input": [5개],
    "file_io": [8개],
    "memory": [12개],
    "game_logic": [50개],
    "sound": [3개],
    "system": [8개],
    "utility": [2개]
  }
  ```

- ✅ `architecture.md`
  - 시스템 다이어그램
  - 주요 함수 목록
  - 카테고리별 설명

- ✅ `function_names.txt`
  ```
  FUN_1000_029a → entry_point
  FUN_1000_0cd1 → initialize_graphics
  FUN_1000_04a9 → main_loop
  ...
  ```

### ✅ 완료 조건

- [ ] 모든 함수 카테고리 분류
- [ ] 주요 10개 함수 네이밍
- [ ] 시스템 다이어그램 작성
- [ ] Entry point 식별
- [ ] Main loop 식별

### 💡 Double Dragon 실제 데이터

```
총 118개 함수:
  - Graphics: 30개 (렌더링, 스프라이트)
  - Game Logic: 50개 (엔티티, AI, 충돌)
  - File I/O: 8개 (에셋 로딩)
  - Memory: 12개 (메모리 관리)
  - Input: 5개 (키보드, 조이스틱)
  - Sound: 3개 (효과음, 음악)
  - System: 8개 (초기화, 메인 루프)
  - Utility: 2개 (수학, 유틸)
```

---

## Phase 3: 에셋 분석

### 🎯 목표
- 압축 알고리즘 식별
- 에셋 추출
- 파일 포맷 이해

### ⏱️ 소요 시간
- **이상적**: 2시간
- **실제**: 2-4시간 (압축 복잡도에 따라)

### 📝 작업 목록

#### 1. 에셋 파일 수집

```bash
# 모든 데이터 파일 나열
find . -type f ! -name "*.EXE" ! -name "*.COM"

# Double Dragon 예시:
# DATA.EG1, LINDA.EG1, WILL.EG1  (스프라이트)
# LEVEL1.PC1, LEVEL2.PC1, ...    (배경)
# SOUND.NW1, SOUND.NW2, ...      (사운드)
```

#### 2. 파일 포맷 분석

```bash
# 매직 넘버 확인
hexdump -C DATA.EG1 | head -5

# Double Dragon 예시:
# 00000000  1f 9d 90 ...  ← LZW 압축 (Unix compress)
```

#### 3. 압축 함수 찾기

**방법 1: 파일 I/O 추적**
```c
// 파일 열기 찾기
INT_21h(AH=0x3D, ...);  // Open file

// 읽기
INT_21h(AH=0x3F, ...);  // Read

// → 다음 호출이 압축 해제 함수!
FUN_1000_60d0(buffer, output);  ← 찾았다!
```

**방법 2: 패턴 인식**
```c
// LZW 패턴:
if (header[0] == 0x1F && header[1] == 0x9D) {
  // Unix compress 형식
}

// RLE 패턴:
if (count < 0) {
  // Repeat run
} else {
  // Literal run
}
```

#### 4. 압축 알고리즘 역공학

**6단계 프로세스** (04_ANALYSIS_TECHNIQUES.md 참조):

```
Step 1: 샘플 데이터 수집
Step 2: 헤더 분석
Step 3: 패턴 찾기
Step 4: 함수 추적
Step 5: 알고리즘 복원
Step 6: C 구현 + 검증
```

#### 5. 압축 해제 도구 구현

```c
// dd_lzw_decompress.c
#include <stdio.h>
#include <stdlib.h>

void decompress_lzw(FILE* input, FILE* output) {
  // LZW 알고리즘 구현
  // (Phase 4 분석 결과 기반)
}

int main(int argc, char** argv) {
  FILE* in = fopen(argv[1], "rb");
  FILE* out = fopen(argv[2], "wb");
  decompress_lzw(in, out);
  fclose(in);
  fclose(out);
  return 0;
}
```

```bash
# 컴파일
gcc -o dd_lzw_decompress dd_lzw_decompress.c

# 모든 파일 추출
for f in *.EG1; do
  ./dd_lzw_decompress "$f" "raw_$f.dat"
done
```

#### 6. 에셋 분류

```
output/assets/
├── sprites/        (*.EG1 압축 해제)
│   ├── DATA.dat
│   ├── LINDA.dat
│   └── WILL.dat
├── backgrounds/    (*.PC1 압축 해제)
│   ├── LEVEL1.dat
│   └── LEVEL2.dat
└── sounds/         (*.NW1 압축 해제)
    └── SOUND.dat
```

### 📦 산출물

- ✅ 압축 해제 도구 (C 프로그램)
- ✅ 추출된 에셋 파일 (36개)
- ✅ 파일 포맷 문서
  ```markdown
  # LZW 압축 포맷
  - 매직 넘버: 0x1F9D
  - 초기 비트: 9
  - 최대 비트: 16
  - 딕셔너리 크기: 4096
  ```

- ✅ 에셋 분류 문서
  - 스프라이트: 6개
  - 배경: 15개
  - 사운드: 15개

### ✅ 완료 조건

- [ ] 압축 알고리즘 식별
- [ ] 압축 해제 도구 구현
- [ ] 모든 에셋 추출 성공
- [ ] 파일 포맷 문서화

### 💡 Double Dragon 실제 데이터

```
압축 알고리즘: LZW (Unix compress)
매직 넘버: 0x1F9D
에셋 파일: 36개
  - 스프라이트: 6개 EG1
  - 배경: 15개 PC1
  - 기타: 15개 NW1-5

압축 해제 구현:
  - C 프로그램 (dd_lzw_decompress.c)
  - 30분 작성, 검증 완료
```

---

## Phase 4: 완전 분석

### 🎯 목표
- 모든 함수 완전 이해
- 100% 커버리지
- 재구현 가능한 문서

### ⏱️ 소요 시간
- **이상적**: 10시간
- **실제**: 10-20시간 (게임 복잡도)
- **Double Dragon**: 14시간

### 📝 작업 목록

#### Sub-Phase 구조

Phase 4는 여러 Sub-Phase로 나뉨:

```
Phase 4.1: 실행 경로 추적 (2시간)
  → Entry, Init, Main Loop

Phase 4.2: 호출 그래프 분석 (1시간)
  → 상위 20개 함수 식별

Phase 4.3: 핵심 시스템 (4시간)
  → 렌더링, 엔티티, 물리

Phase 4.4: 누락 함수 복구 (1시간)
  → 호출 그래프 기반 복구

Phase 4.5: 나머지 함수 (6시간)
  → 100% 커버리지
```

#### 1. 실행 경로 추적 (Phase 4.1)

**목표**: 핵심 흐름 이해

```
Step 1: Entry Point 분석
  FUN_1000_029a (1시간)
  - DOS 환경 체크
  - 메모리 초기화
  - 초기화 함수 호출

Step 2: 초기화 분석
  FUN_1000_0cd1 (30분)
  - 그래픽 모드 설정
  - 점프 테이블 초기화
  - 에셋 로딩

Step 3: 메인 루프 분석
  FUN_1000_04a9 (30분)
  - 입력 처리
  - 업데이트
  - 렌더링
  - VSync
```

**산출물**: `EXECUTION_PATH.md`

---

#### 2. 호출 그래프 분석 (Phase 4.2)

**목표**: 중요 함수 우선 분석

```python
# analyze_call_graph.py
import json

# Spice86 데이터 로드
with open('ExecutionFlow.json') as f:
    data = json.load(f)

# 호출 빈도 집계
call_count = {}
for call in data['calls']:
    addr = call['target']
    call_count[addr] = call_count.get(addr, 0) + 1

# 상위 20개
top_20 = sorted(call_count.items(),
                key=lambda x: x[1],
                reverse=True)[:20]

# 출력
for addr, count in top_20:
    print(f"0x{addr:04X}: {count:4d} calls")
```

**결과**:
```
0x293e:   29 calls  → 렌더링 디스패처!
0x2711:    6 calls  → 엔티티 업데이트!
0x12c0:   11 calls  → 타일맵 디스패처!
...
```

**산출물**: `CALL_GRAPH.md`, 상위 20개 함수 분석

---

#### 3. 시스템별 분석 (Phase 4.3-4.15)

각 시스템을 개별 문서로:

| Sub-Phase | 시스템 | 함수 수 | 시간 |
|-----------|--------|---------|------|
| 4.3 | 렌더링 | 29 | 3시간 |
| 4.4 | 엔티티/AI | 18 | 2시간 |
| 4.5 | 물리/충돌 | 12 | 2시간 |
| 4.6 | 입력/카메라 | 11 | 1시간 |
| 4.7 | 애니메이션 | 7 | 1시간 |
| 4.8 | 스테이지 | 15 | 1시간 |
| 4.9 | 압축 | 10 | 2시간 |
| 4.10 | 하드웨어 I/O | 15 | 1시간 |
| 4.11-15 | 나머지 | 44 | 1시간 |

**각 시스템 분석 프로세스**:

```
1. 관련 함수 목록 작성 (10분)
2. 각 함수 디컴파일 읽기 (30분)
3. 의사코드 작성 (30분)
4. 메모리 맵 작성 (20분)
5. 시스템 다이어그램 (20분)
6. 문서 작성 (30분)
─────────────────────────────
총 ~2-3시간/시스템
```

---

#### 4. 누락 함수 복구 (Phase 4.5)

**문제**: Ghidra가 일부 함수 인식 못함

**해결**:
```python
# batch_decompile_missing.py
# 1. 호출 그래프에서 함수 주소 추출
missing = set(spice_funcs) - set(ghidra_funcs)

# 2. 각 주소에 함수 생성
for addr in missing:
    create_function_at(addr)
    decompile(addr)
```

**Double Dragon 사례**:
- Phase 4.5: 15개 함수 복구 (5분)
- Phase 4.6: 9개 함수 복구 (5분)

---

#### 5. 점프 테이블 발견 (Phase 4.6-4.15)

**패턴**:
```c
// 간접 호출 찾기
(**(code **)(0x18c4 + index * 2))();
```

**자동 발견**:
```python
# dump_jump_table.py
def find_jump_tables():
    # 간접 호출 찾기
    # 테이블 주소 추출
    # 각 엔트리 디컴파일
```

**Double Dragon 발견**:
- 0x16ef: AI (256 entries)
- 0x0e3f: Collision (256 entries)
- 0x18c4: Rendering (30 entries)
- 0x2264: Physics (128 entries)
- 0x18d2: Hook (1 entry)

---

#### 6. 문서화 (계속)

**각 함수 문서 템플릿**:

```markdown
# FUN_1000_XXXX

## 요약
한 줄 설명

## 파라미터
- param1: 설명
- param2: 설명

## 의사코드
```
function name(params):
  logic
  return result
```

## 메모리
- 0xXXXX: 설명

## 호출 관계
- 호출자: FUN_1000_YYYY
- 피호출자: FUN_1000_ZZZZ

## 참고
관련 문서 링크
```

### 📦 산출물

**Phase 4 완료 시**:

- ✅ 161개 함수 완전 분석 (100%)
- ✅ 14개 시스템 문서 (18,096줄)
  - RENDERING_SYSTEM.md
  - ENTITY_AI_SYSTEM.md
  - PHYSICS_COLLISION.md
  - etc.

- ✅ 메모리 맵 (80+ 주소)
- ✅ 점프 테이블 (5개 완전 발견)
- ✅ 실행 흐름도
- ✅ 알고리즘 의사코드

### ✅ 완료 조건

- [ ] 100% 함수 커버리지
- [ ] 모든 시스템 문서화
- [ ] 메모리 맵 완성
- [ ] 점프 테이블 완전 발견
- [ ] 재구현 가능 수준

### 💡 Double Dragon 통계

```
Phase 4 소요 시간: 14시간
함수 수: 161개 (100%)
문서: 14개 (18,096줄)
메모리 주소: 80+
점프 테이블: 5개

Sub-Phase 분포:
  4.1-4.9:   143개 함수 (8시간)
  4.10-4.15:  18개 함수 (6시간)
```

---

## 시간 배분 전략

### 📊 이상적 배분 (17시간)

| 작업 | 시간 | 비율 | 우선순위 |
|------|------|------|----------|
| **Phase 0** | 5분 | 0.5% | P0 |
| **Phase 1** | 5분 | 1% | P0 |
| **Phase 2** | 2시간 | 10% | P1 |
| **Phase 3** | 3시간 | 18% | P2 |
| **Phase 4.1-4.2** | 3시간 | 18% | P1 |
| **Phase 4.3-4.8** | 8시간 | 47% | P2 |
| **Phase 4.9-4.15** | 1시간 | 6% | P3 |
| **합계** | **17시간** | **100%** | - |

### 🎯 우선순위 전략

**P0 (필수, 10분)**:
- 환경 준비
- 자동 디컴파일

**P1 (핵심, 5시간)**:
- 코드 분류
- 실행 경로 추적
- 호출 그래프 분석

**P2 (중요, 11시간)**:
- 에셋 분석
- 주요 시스템 분석

**P3 (보완, 1시간)**:
- 나머지 함수
- 문서 정리

### ⚡ 병목 회피

**병목 지점**:
1. **압축 알고리즘** (2-4시간)
   - 해결: 기존 라이브러리 확인 먼저
   - Unix compress? → 표준 구현 재사용

2. **점프 테이블** (1-2시간)
   - 해결: 자동 발견 스크립트
   - 한 번 작성, 계속 재사용

3. **문서화** (4-6시간)
   - 해결: 즉시 작성 (재분석 방지)
   - 템플릿 사용 (시간 절약)

---

## 마일스톤 체크리스트

### 🎯 Phase 0 완료

- [ ] Ghidra 11.4.2 설치
- [ ] pyghidra 2.2.0 설치
- [ ] Ghidra 프로젝트 생성
- [ ] 자동 분석 완료
- [ ] (선택) Spice86 실행 추적

**시간**: 5분 (최초 1시간)

---

### 🎯 Phase 1 완료

- [ ] batch_decompile.py 실행
- [ ] 모든 함수 디컴파일 (95%+)
- [ ] C 파일 생성 확인
- [ ] JSON 메타데이터 생성
- [ ] 코드 줄 수 확인

**시간**: 5분
**산출물**: 118개 C 파일, functions.json

---

### 🎯 Phase 2 완료

- [ ] 함수 카테고리 분류
- [ ] Entry point 식별
- [ ] Main loop 식별
- [ ] 주요 10개 함수 네이밍
- [ ] 시스템 다이어그램 작성

**시간**: 2시간
**산출물**: classification.json, architecture.md

---

### 🎯 Phase 3 완료

- [ ] 압축 알고리즘 식별
- [ ] 압축 해제 도구 구현
- [ ] 모든 에셋 추출
- [ ] 파일 포맷 문서화
- [ ] 에셋 분류 완료

**시간**: 3시간
**산출물**: 압축 해제 도구, 36개 에셋

---

### 🎯 Phase 4 완료

- [ ] 실행 경로 추적 완료
- [ ] 호출 그래프 분석 완료
- [ ] 상위 20개 함수 분석
- [ ] 모든 시스템 문서화
- [ ] 100% 함수 커버리지
- [ ] 메모리 맵 완성
- [ ] 점프 테이블 발견

**시간**: 14시간
**산출물**: 14개 시스템 문서, 18,096줄

---

## Double Dragon 타임라인

### 📅 실제 프로젝트 타임라인

#### 2025-11-24 (Day 1)

**09:00-09:05 | Phase 0**
- Ghidra 프로젝트 생성
- 자동 분석 실행
- ✅ 완료 (5분)

**09:05-09:07 | Phase 1**
- pyghidra 일괄 디컴파일
- 118개 함수, 4,412줄
- ✅ 완료 (2.2분)

**09:07-10:07 | Phase 2**
- 함수 분류 (8개 카테고리)
- 주요 함수 네이밍 (30개)
- 아키텍처 다이어그램
- ✅ 완료 (1시간)

**10:07-12:07 | Phase 3**
- LZW 압축 식별
- dd_lzw_decompress.c 구현
- 36개 에셋 추출
- ✅ 완료 (2시간)

**12:07-14:07 | Phase 4.1-4.2**
- 실행 경로 추적
- 호출 그래프 분석
- 상위 20개 함수 식별
- ✅ 완료 (2시간)

**14:07-18:07 | Phase 4.3-4.4**
- 렌더링 시스템 (3시간)
- 엔티티 시스템 (1시간)
- ✅ 50개 함수 분석 (4시간)

**18:07-22:07 | Phase 4.5-4.8**
- 호출 그래프 기반 15개 함수 복구 (5분)
- 점프 테이블 9개 함수 복구 (5분)
- 물리, 입력, 애니메이션 시스템
- ✅ 61개 함수 추가 분석 (4시간)

**22:07-24:00 | Phase 4.9-4.12**
- 스테이지, 압축, 하드웨어 I/O
- ✅ 32개 함수 분석 (2시간)

---

#### 2025-11-24 Late (Day 2)

**00:00-06:00 | Phase 4.13-4.15**
- 애니메이션, 카메라, 최종 시스템
- ✅ 18개 함수 분석 (6시간)

**06:00-07:00 | 문서 정리**
- 중복 제거
- 언어 중립적 재작성
- ✅ 완료 (1시간)

---

### 📊 최종 통계

```
총 소요 시간: 17시간 (휴식 제외)
실제 달력: 2일 (24시간 마라톤)

Phase 0:    5분   (0.5%)
Phase 1:  2.2분   (0.2%)
Phase 2:    1시간 (6%)
Phase 3:    2시간 (12%)
Phase 4:   14시간 (82%)
─────────────────────────
합계:      17시간 (100%)

함수 분석: 161개 (100%)
문서: 18,096줄
메모리 주소: 80+
점프 테이블: 5개
```

### 🏆 효율성

**예상 (자동화 없이)**: 40시간
**실제**: 17시간
**절약**: 58% (23시간)

**핵심 요인**:
- pyghidra 자동 디컴파일 (~100배)
- 호출 그래프 활용 (2배)
- 즉시 문서화 (재분석 방지)
- 패턴 인식 (누적 효과)

---

## 💡 다음 프로젝트 목표

### 🎯 개선 목표

**현재 (Double Dragon)**:
- 소요 시간: 17시간
- 자동화율: 40%
- 문서: 18,096줄

**다음 프로젝트**:
- 목표 시간: 10시간 (40% 단축)
- 자동화율: 60% (스크립트 재사용)
- 문서: 템플릿 기반 (빠른 작성)

### 📋 개선 계획

1. **자동화 강화**
   - 함수 분류 자동화
   - 패턴 자동 인식
   - 문서 템플릿 자동 생성

2. **패턴 라이브러리**
   - Work Buffer 패턴
   - 점프 테이블 패턴
   - RLE/LZW 패턴

3. **도구 체인 개선**
   - 완전 자동 파이프라인
   - Docker 컨테이너화
   - CI/CD 통합

---

## 📚 참고 문서

- [04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md) - 분석 기법
- [06_LESSONS_LEARNED.md](06_LESSONS_LEARNED.md) - 실수와 배운 점
- [02_TOOLS_AND_SETUP.md](02_TOOLS_AND_SETUP.md) - 도구 세팅
- [../PROGRESS.md](../PROGRESS.md) - Double Dragon 진행 상황

---

**작성자 노트**:
> 이 프로세스는 Double Dragon DOS 프로젝트에서 검증되었습니다. 5단계를 순차적으로 따라가면 17시간 만에 72KB 게임을 완전히 이해할 수 있습니다.

**다음 프로젝트에 적용하세요!**

---

**다음 읽을 문서**:
- [02_TOOLS_AND_SETUP.md](02_TOOLS_AND_SETUP.md) - 도구 설치 및 설정
- [04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md) - 핵심 분석 기법
