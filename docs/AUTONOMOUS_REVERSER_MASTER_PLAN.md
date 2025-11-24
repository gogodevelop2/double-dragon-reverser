# Double Dragon 완전 자율 리버스 엔지니어링 마스터 플랜

**작성일**: 2025-11-24
**버전**: 2.0 (단순화 버전)
**목적**: GhidraMCP 직접 디컴파일을 활용한 초고속 소스 재구성

---

## 🎯 핵심 변경사항 (v2.0)

### v1.0의 문제점
- ❌ 과도하게 복잡한 분석 과정
- ❌ 예상 시간 과대평가 (68시간 → 실제 필요 13시간)
- ❌ 불필요한 중간 단계

### v2.0의 핵심
- ✅ **GhidraMCP가 이미 C 코드로 디컴파일해줌!**
- ✅ 200개 함수 × 2초 = **7분이면 전체 코드 추출 완료**
- ✅ AI는 이미 변환된 C 코드만 읽고 재구성
- ✅ **예상 소요: 1-2일** (기존 9일 → 85% 단축!)

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [실행 원칙](#2-실행-원칙)
3. [Phase별 실행 계획 (단순화)](#3-phase별-실행-계획)
4. [인간 체크포인트](#4-인간-체크포인트)
5. [중단/재개 메커니즘](#5-중단재개-메커니즘)
6. [최종 산출물](#6-최종-산출물)

---

## 1. 프로젝트 개요

### 1.1 입력 자료

```
/Users/joejeon/Documents/develop/Double Dragon/
├── reference/dos-original/
│   ├── DDMAIN.EXE (103KB)          - 메인 게임 로직
│   ├── DUAL.EXE (547B)              - 듀얼 모드 유틸리티
│   ├── SHOW.EXE (836B)              - 스프라이트 뷰어
│   └── [36개 데이터 파일]           - .EG1, .PC1, .NW1~5 등
│
├── spice86-dumps/.../
│   ├── spice86dumpMemoryDump.bin    - 메모리 스냅샷 (1.1MB)
│   ├── spice86dumpExecutionFlow.json - 함수 호출 그래프 (380KB)
│   └── spice86dumpGhidraSymbols.txt  - 200개 함수 주소
│
└── ghidra-project/
    └── DoubleDragon.gpr              - 기존 Ghidra 프로젝트
```

### 1.2 최종 목표

**출력**:
- 완전한 C/C++ 소스 코드
- 컴파일 가능한 CMake 프로젝트
- 모든 게임 에셋 (PNG, JSON)
- 완전한 문서화

**품질 기준**:
- 컴파일 성공률: 100%
- 원본과 행동 일치율: 95% 이상
- 코드 커버리지: 90% 이상

---

## 2. 실행 원칙

### 2.1 자율성 레벨

| 작업 단계 | 자율성 | 인간 개입 |
|----------|--------|----------|
| **분석** | 100% 자동 | 승인만 |
| **코드 생성** | 100% 자동 | 검토만 |
| **검증** | 100% 자동 | 결과 확인 |
| **반복 수정** | 100% 자동 | 없음 |
| **다음 Phase 진행** | 수동 승인 필요 | **필수** |

### 2.2 보고 원칙

**모든 Phase 종료 시**:
1. ✅ 자동 보고서 생성
2. 🛑 실행 일시 중지
3. 👤 사용자 검토 대기
4. ✅ 승인 후 다음 Phase 진행

**긴급 중단 조건** (자동):
- 검증 실패율 > 50%
- 반복 시도 50회 초과
- 메모리/디스크 부족
- 예상치 못한 에러

---

## 3. Phase별 실행 계획 (단순화)

## 전체 프로세스 개요

```
Phase 0: 환경 준비 (10분)
   ↓
Phase 1: 전체 코드 추출 (1-2시간) ⚡ GhidraMCP 직접 디컴파일
   ↓ CHECKPOINT #1
Phase 2: 코드 분석 및 재구성 (4-6시간) ⚡ AI가 C 코드 읽고 C++ 변환
   ↓ CHECKPOINT #2
Phase 3: 에셋 추출 (2-4시간)
   ↓ CHECKPOINT #3
Phase 4: 통합 및 검증 (2-3시간)
   ↓ CHECKPOINT #4 - 완료!

총 예상 시간: 9-15시간 (1-2일)
```

---

## Phase 0: 환경 준비 및 검증 (10분)

### 목표
- GhidraMCP 연결 확인
- 샘플 함수 디컴파일 테스트
- 작업 디렉토리 구성

### 자동 실행 내용

```bash
1. GhidraMCP 서버 시작 (1분)
   uvx pyghidra-mcp DDMAIN.EXE DUAL.EXE SHOW.EXE

2. 연결 테스트 (2분)
   질문: "DDMAIN.EXE에 몇 개의 함수가 있어?"
   예상 응답: 200개 이상

   질문: "FUN_1000_6091 함수를 디컴파일해줘"
   예상: C 코드가 바로 나옴

3. 파일 검증 (2분)
   - 36개 데이터 파일 존재 확인
   - 메모리 덤프 크기 확인 (1.1MB)

4. 디렉토리 생성 (1분)
   mkdir -p output/{decompiled,src,assets,docs,checkpoints}
```

### 산출물

```
output/
├── phase0_environment_report.md
├── ghidra_test_function.c        # 샘플 디컴파일 결과
└── file_inventory.json
```

### 📊 CHECKPOINT #0: 환경 준비 완료

**보고 내용**:
- ✅ GhidraMCP 연결: 성공/실패
- ✅ 디컴파일 테스트: 성공/실패
- ✅ 파일 검증: 36/36 파일 OK
- ✅ 예상 함수 개수: ~200개

**사용자 결정**:
- [ ] ✅ Phase 1 진행 승인 (전체 코드 추출 시작)
- [ ] 🔧 환경 문제 해결 필요
- [ ] ⛔ 작업 중단

**예상 다음 단계 소요**: 1-2시간

---

## Phase 1: 전체 코드 추출 (1-2시간) ⚡

### 목표
- **모든 함수 디컴파일 (GhidraMCP 직접 활용)**
- 데이터 영역 추출
- 구조화된 파일로 저장

### 핵심 변경: GhidraMCP 직접 디컴파일!

**기존 계획 (v1.0)**:
```
❌ 바이너리 분석 → 패턴 찾기 → 추론 → 검증 → 코드 생성
   예상 시간: 6-12시간
```

**새 계획 (v2.0)**:
```
✅ list_functions() → decompile() → 저장
   실제 시간: 1-2시간!
```

### 자동 실행 단계

#### Step 1.1: 전체 함수 디컴파일 (30분)

```python
# GhidraMCP를 통한 자동 추출
import json

# 1. 모든 함수 목록 가져오기 (1초)
functions = mcp.list_functions("DDMAIN.EXE")
print(f"총 {len(functions)}개 함수 발견")

# 2. 각 함수 디컴파일 (함수당 ~2초)
for i, func in enumerate(functions):
    print(f"[{i+1}/{len(functions)}] {func.name} 디컴파일 중...")

    # Ghidra가 바로 C 코드로 변환!
    c_code = mcp.decompile("DDMAIN.EXE", func.address)

    # 파일로 저장
    save(f"output/decompiled/{func.name}.c", c_code)

    # 메타데이터 저장
    metadata = {
        "name": func.name,
        "address": func.address,
        "size": func.size,
        "calls_to": func.calls,
        "called_from": func.callers
    }
    save(f"output/decompiled/{func.name}.json", metadata)

# 결과: 200개 × 2초 = 400초 = 약 7분!
```

#### Step 1.2: 데이터 영역 추출 (20분)

```markdown
GhidraMCP 자동 질문:

질문 1: "DDMAIN.EXE의 모든 문자열을 추출해줘"
→ 파일명, 게임 텍스트, 디버그 메시지

질문 2: "전역 변수 목록을 추출해줘"
→ 데이터 세그먼트 분석

질문 3: "정의된 모든 데이터 구조체를 찾아줘"
→ Ghidra가 자동 인식한 구조체들
```

#### Step 1.3: DUAL.EXE, SHOW.EXE 처리 (10분)

```python
# 같은 방식으로 처리
for exe in ["DUAL.EXE", "SHOW.EXE"]:
    functions = mcp.list_functions(exe)
    for func in functions:
        c_code = mcp.decompile(exe, func.address)
        save(f"output/decompiled/{exe}/{func.name}.c", c_code)
```

#### Step 1.4: 구조화 및 정리 (10분)

```python
# 함수 그룹핑
categorize_functions({
    "compression": [f for f in functions if "0x6091" in f.address or "lzw" in f.name],
    "graphics": [f for f in functions if "0x0786" in f.address],
    "io": [f for f in functions if "int_21" in f.calls],
    "game_logic": [...],
    # ...
})
```

### 산출물

```
output/
├── decompiled/
│   ├── DDMAIN/
│   │   ├── FUN_1000_6091.c         # LZW 비트 읽기
│   │   ├── FUN_1000_605b.c         # LZW 디코딩
│   │   ├── FUN_1000_2865.c         # RLE 압축 해제
│   │   ├── FUN_1000_0786.c         # CGA 변환
│   │   └── ... (200개 C 파일)
│   │
│   ├── DUAL/
│   │   └── ... (10개 C 파일)
│   │
│   └── SHOW/
│       └── ... (5개 C 파일)
│
├── data/
│   ├── strings.txt                 # 모든 문자열
│   ├── global_variables.json       # 전역 변수 목록
│   └── data_structures.h           # 발견된 구조체
│
└── docs/
    ├── phase1_extraction_report.md
    └── function_catalog.md         # 함수 분류 카탈로그
```

### 📊 CHECKPOINT #1: 전체 코드 추출 완료

**자동 생성 보고서**: `output/docs/phase1_report.md`

```markdown
# Phase 1 완료 보고서

## 실행 정보
- 시작: 2025-11-24 10:00
- 종료: 2025-11-24 11:30
- 소요 시간: 1.5시간

## 추출 결과

### 디컴파일된 함수

| 실행 파일 | 함수 개수 | C 코드 라인 | 비고 |
|----------|---------|-----------|------|
| DDMAIN.EXE | 203개 | ~15,000 | ✅ 완료 |
| DUAL.EXE | 8개 | ~300 | ✅ 완료 |
| SHOW.EXE | 12개 | ~450 | ✅ 완료 |
| **합계** | **223개** | **~15,750** | ✅ |

### 함수 분류

| 카테고리 | 함수 개수 | 주요 함수 |
|---------|---------|----------|
| 압축/해제 | 15개 | FUN_1000_6091 (LZW), FUN_1000_2865 (RLE) |
| 그래픽 | 23개 | FUN_1000_0786 (CGA), FUN_1000_09d1 |
| 파일 I/O | 12개 | FUN_1000_1A60 (파일 열기) |
| 게임 로직 | 87개 | 플레이어, 적 AI, 충돌 |
| 입력 처리 | 8개 | 키보드, 조이스틱 |
| 사운드 | 6개 | AdLib, PC Speaker |
| 기타 | 72개 | 유틸리티, 수학, 메모리 |

### 데이터 추출

- **문자열**: 127개 (파일명, 메시지, 디버그)
- **전역 변수**: 89개
- **구조체**: 23개 (Ghidra 자동 인식)

### 검증

✅ 모든 함수 디컴파일 성공
✅ 컴파일 가능한 C 코드 (warning 있을 수 있음)
✅ 메타데이터 완전 (주소, 크기, 호출 관계)

## 다음 Phase 준비

✅ Phase 2 (코드 분석 및 재구성) 진행 가능
- 모든 C 코드 준비됨
- AI 분석 준비 완료

## 샘플 코드 (LZW 함수)

```c
// FUN_1000_6091.c - LZW 비트 읽기 함수
uint read_lzw_code(int num_bits) {
    uint code = 0;
    int bit_buffer = *(int*)0x6538;
    char bit_count = *(char*)0x653a;
    // ... (전체 코드는 파일 참조)
}
```

## 예상 다음 단계 소요 시간

Phase 2: 4-6시간 (AI가 C 코드 읽고 C++ 재구성)
```

**사용자 결정**:
- [ ] ✅ Phase 2 진행 승인 (AI 분석 시작)
- [ ] 🔍 디컴파일 코드 검토
- [ ] 💾 저장하고 중단
- [ ] ⛔ 작업 종료

**중요**: 이미 모든 C 코드가 준비되었습니다!
Phase 2에서는 AI가 이 코드를 **읽고 이해**만 하면 됩니다.

---

## Phase 2: 코드 분석 및 재구성 (4-6시간) ⚡

### 목표
- 200개 C 파일 읽고 이해
- 데이터 구조 역산
- 모던 C++ 프로젝트로 재구성

### 자동 실행 단계

#### Step 1.1: SHOW.EXE 분석 (2시간)

**GhidraMCP 자동 질문 시퀀스**:

```markdown
질문 1: "SHOW.EXE의 메인 함수를 찾아줘.
         entry point부터 시작해서 전체 실행 흐름을 추적해줘."

질문 2: "파일 I/O 함수를 찾아줘:
         - INT 21h, AH=3Dh (파일 열기)
         - INT 21h, AH=3Fh (파일 읽기)
         호출하는 모든 위치를 찾아줘."

질문 3: "파일 읽기 직후 처음 16~64바이트를 어떻게 처리하는지
         디컴파일해줘. 특히:
         - 어떤 메모리 주소에 저장하는가?
         - 저장한 값을 후속 코드에서 어떻게 사용하는가?
         - 반복 루프가 있다면 카운터는 무엇인가?"

질문 4: "위 분석을 바탕으로 C 구조체를 정의해줘:

         struct SpriteFileHeader {
             uint16_t field_00;  // offset 0x00, 사용처: ???
             uint16_t field_02;  // offset 0x02, 사용처: ???
             // ...
         };

         각 필드의 의미를 추론해줘 (width? height? frames?)"

질문 5: "화면에 그리는 루틴을 찾아서:
         - 반복 횟수 (프레임 수?)
         - 각 프레임 크기 계산 방법
         - 픽셀 데이터 시작 오프셋
         을 역산해줘."
```

**자동 검증**:
```python
# AI가 추론한 구조체로 테스트
for test_file in ["PLAYER1.EG1", "LINDA.EG1", "LEVEL11.PC1"]:
    header = parse_header(test_file, inferred_structure)

    # 합리성 검사
    assert 0 < header.width <= 640
    assert 0 < header.height <= 480
    assert 0 < header.frames <= 100

    # 데이터 크기 검증
    expected_size = calculate_data_size(header)
    actual_size = file_size - header_size
    assert abs(expected_size - actual_size) < 100  # 오차 허용
```

#### Step 1.2: 메모리 덤프 교차 검증 (1시간)

```python
# 메모리에서 압축 해제된 스프라이트 찾기
mem = load_memory_dump("spice86dumpMemoryDump.bin")

# Step 1.1에서 추론한 헤더로 검색
pattern = struct.pack('<HH', inferred_width, inferred_height)
offsets = find_all(mem, pattern)

for offset in offsets:
    # 실제 메모리에 로드된 헤더 확인
    memory_header = parse_header_from_memory(mem, offset)

    # 추론과 비교
    if matches(memory_header, inferred_structure):
        confidence += 1
```

#### Step 1.3: 전체 파일 타입별 분석 (3시간)

```markdown
질문 6: "PLAYER1.EG1와 LEVEL11.PC1의 헤더를 비교해줘.
         같은 구조인가, 다른 구조인가?
         다르다면 각각의 구조를 정의해줘."

질문 7: ".NW1~NW5 파일들을 분석해줘.
         CHR_BL.NW1, CHR_BL.NW2, ..., CHR_BL.NW5

         - 이들의 관계는? (순차적? 독립적?)
         - 헤더 구조는?
         - 애니메이션 프레임인가?"

질문 8: "CHARSET.BIN, LDSCRN.CGA 파일도 분석해줘.
         - 압축되어 있나?
         - 헤더가 있나?
         - 직접 픽셀 데이터인가?"
```

#### Step 1.4: 최종 구조체 확정 (2시간)

```c
// AI가 최종 확정한 구조체들
// output/src/assets/file_formats.h

typedef struct {
    uint16_t magic;           // 0x1F9D (LZW signature)
    uint16_t width;           // 픽셀 단위
    uint16_t height;
    uint16_t num_frames;
    uint16_t flags;           // bit 0: RLE 사용 여부
    uint32_t data_offset;     // 픽셀 데이터 시작
} SpriteFileHeader;

typedef struct {
    uint16_t magic;
    uint16_t width;
    uint16_t height;
    uint16_t scroll_length;   // 레벨 길이
    uint16_t num_enemies;
    uint32_t enemy_table_offset;
    uint32_t trigger_table_offset;
} LevelFileHeader;

// ... 등등
```

### 산출물

```
output/
├── docs/
│   ├── phase1_file_format_analysis.md
│   ├── header_structures.md
│   └── verification_results.json
│
├── src/assets/
│   └── file_formats.h
│
└── temp/
    ├── show_exe_decompiled.c
    ├── memory_dump_analysis.txt
    └── test_results/
```

### 📊 CHECKPOINT #1: 파일 포맷 분석 완료

**자동 생성 보고서**: `output/docs/phase1_report.md`

**내용**:

```markdown
# Phase 1 완료 보고서

## 실행 정보
- 시작: 2025-11-24 09:00
- 종료: 2025-11-24 15:30
- 소요 시간: 6.5시간

## 분석 결과

### 파일 타입별 구조

| 파일 타입 | 개수 | 헤더 구조 확정 | 파싱 성공률 |
|----------|------|---------------|------------|
| .EG1 (스프라이트) | 17개 | ✅ | 17/17 (100%) |
| .PC1 (레벨) | 4개 | ✅ | 4/4 (100%) |
| .NW1~5 (애니메이션) | 10개 | ✅ | 10/10 (100%) |
| .BIN (기타) | 5개 | ✅ | 5/5 (100%) |

### 확정된 구조체

1. **SpriteFileHeader** (12 bytes)
   - width: uint16_t at +0x02
   - height: uint16_t at +0x04
   - num_frames: uint16_t at +0x06
   - flags: uint16_t at +0x08

2. **LevelFileHeader** (16 bytes)
   - width: uint16_t at +0x02
   - height: uint16_t at +0x04
   - scroll_length: uint16_t at +0x06
   - ...

### 검증 결과

#### 메모리 덤프 교차 검증
- 발견된 헤더 패턴: 23개
- 구조체 일치: 23/23 (100%)
- 신뢰도: **98.5%**

#### 파일 파싱 테스트
- PLAYER1.EG1: ✅ 성공 (width=320, height=200, frames=16)
- LINDA.EG1: ✅ 성공 (width=320, height=200, frames=12)
- LEVEL11.PC1: ✅ 성공 (width=640, height=200, enemies=15)
- [전체 결과: output/temp/test_results/]

## 다음 Phase 준비 상태

✅ Phase 2 (압축 알고리즘) 진행 가능
- LZW 루틴 위치 확인됨: 0x1000:0x6091
- RLE 루틴 위치 확인됨: 0x1000:0x2865
- 테스트 파일 준비 완료

## 문제 및 경고

⚠️ JOYKEY.SCR 파일: 헤더 없음, 직접 픽셀 데이터로 추정
✅ 해결: 별도 처리 로직 추가

## 예상 다음 단계 소요 시간

Phase 2: 8-16시간 (압축 알고리즘 복잡도에 따라)
```

**사용자 결정**:
- [ ] ✅ Phase 2 진행 승인
- [ ] 🔍 Phase 1 재검토 필요 (어떤 부분?)
- [ ] 💾 여기서 저장하고 나중에 재개
- [ ] ⛔ 작업 중단

**저장 체크포인트**:
```bash
# 자동 저장됨
output/checkpoints/phase1_complete.json
{
  "phase": 1,
  "status": "completed",
  "timestamp": "2025-11-24T15:30:00",
  "confidence": 0.985,
  "ready_for_next": true,
  "artifacts": [
    "output/src/assets/file_formats.h",
    "output/docs/phase1_report.md"
  ]
}
```

---

## Phase 2: 압축 알고리즘 완전 역산 (8-16시간)

### 목표
- LZW 압축 해제 100% 재구현
- RLE 압축 해제 100% 재구현
- 모든 데이터 파일 압축 해제 가능

### 자동 실행 단계

#### Step 2.1: LZW 루틴 완전 디컴파일 (4시간)

```markdown
질문 1: "DDMAIN.EXE의 FUN_1000_6091과 FUN_1000_605b를
         완전히 디컴파일해줘.

         특히:
         - 모든 전역 변수 (0x6538, 0x653a 등)
         - 모든 지역 변수
         - 모든 분기문
         - 루프 조건"

질문 2: "LZW 초기화 함수를 찾아줘.
         - 전역 변수들의 초기값은?
         - 딕셔너리 시작 주소는?
         - 최대 딕셔너리 크기는?"

질문 3: "비트 읽기 방향을 확정해줘:
         - MSB first인가 LSB first인가?
         - 실제 어셈블리 코드의 SHL/SHR 명령어를 봐줘
         - 비트 버퍼 업데이트 순서는?"

질문 4: "코드 크기 증가 로직을 찾아줘:
         - 언제 9비트 → 10비트가 되나?
         - 최대 코드 크기는?
         - 코드 256의 역할은?"

질문 5: "위 분석을 바탕으로 완전한 C 코드를 작성해줘:

         // 정확한 구조체
         typedef struct {
             uint8_t* input;
             size_t input_size;
             size_t input_pos;

             int bit_buffer;
             int bits_in_buffer;

             int current_code_size;
             int max_code_size;

             uint8_t* dict_buffer;
             int dict_size;
         } LZWState;

         // 완전한 함수들
         void lzw_init(LZWState* state, uint8_t* input, size_t size);
         uint16_t lzw_read_code(LZWState* state);
         int lzw_decompress(uint8_t* input, size_t input_size,
                           uint8_t* output, size_t* output_size);

         주석 포함, 실제 컴파일 가능한 코드로!"
```

#### Step 2.2: 자동 검증 및 반복 (4-8시간)

```python
# 자동 검증 루프
max_attempts = 50

for attempt in range(max_attempts):
    # 1. AI가 생성한 C 코드 컴파일
    compile_result = compile_c_code("output/temp/lzw.c")
    if not compile_result.success:
        error_msg = f"컴파일 실패: {compile_result.error}"
        # AI에게 피드백
        corrected_code = ask_ghidra_mcp(f"컴파일 에러 수정: {error_msg}")
        continue

    # 2. 테스트 파일로 실행
    test_files = [
        ("PLAYER1.EG1", "expected_player1.bin"),  # 메모리 덤프에서 추출
        ("LINDA.EG1", "expected_linda.bin"),
        ("LEVEL11.PC1", "expected_level11.bin")
    ]

    all_passed = True
    for test_file, expected in test_files:
        # 압축 해제 실행
        actual = run_lzw_decompressor(test_file)
        expected_data = load(expected)

        # 바이트 단위 비교
        comparison = compare_bytes(actual, expected_data)

        if comparison.match_rate < 1.0:
            all_passed = False

            # 디버그 정보 생성
            debug_info = {
                "file": test_file,
                "match_rate": comparison.match_rate,
                "first_diff_offset": comparison.first_diff_offset,
                "expected_byte": expected_data[comparison.first_diff_offset],
                "actual_byte": actual[comparison.first_diff_offset],
                "context": actual[comparison.first_diff_offset-10:comparison.first_diff_offset+10]
            }

            # AI에게 수정 요청
            correction_prompt = f"""
            LZW 압축 해제 결과가 틀렸어.

            파일: {debug_info['file']}
            일치율: {debug_info['match_rate']*100:.1f}%
            첫 불일치 오프셋: 0x{debug_info['first_diff_offset']:X}

            예상 값: 0x{debug_info['expected_byte']:02X}
            실제 값: 0x{debug_info['actual_byte']:02X}

            주변 데이터:
            {hexdump(debug_info['context'])}

            원인을 분석하고 코드를 수정해줘.
            가능한 원인:
            1. 비트 읽기 순서 (MSB/LSB)
            2. 코드 크기 증가 타이밍
            3. 딕셔너리 관리 로직
            4. 초기값 설정

            수정된 전체 C 코드를 다시 작성해줘.
            """

            corrected_code = ask_ghidra_mcp(correction_prompt)
            break

    if all_passed:
        print(f"✅ LZW 검증 성공! (시도 {attempt+1}회)")
        break
else:
    print(f"❌ LZW 검증 실패 (최대 시도 초과)")
    # 긴급 중단
    raise VerificationFailure("LZW implementation failed after 50 attempts")
```

#### Step 2.3: RLE 루틴 분석 및 구현 (2시간)

```markdown
질문 6: "FUN_1000_2865 (RLE 압축 해제)를 디컴파일해줘.

         RLE 포맷:
         - 음수 카운트: 반복
         - 양수 카운트: 리터럴

         정확한 로직을 C로 구현해줘."
```

```python
# RLE 자동 검증 (LZW와 동일한 프로세스)
# 단순해서 보통 1-2회 시도로 성공
```

#### Step 2.4: 전체 파일 압축 해제 (2시간)

```python
# 36개 파일 모두 압축 해제
for file in all_data_files:
    decompressed = decompress_file(file)
    save(f"output/temp/decompressed/{file}.bin", decompressed)

    # PNG 변환 (CGA 포맷)
    if file.endswith(('.EG1', '.PC1')):
        png = convert_cga_to_png(decompressed)
        save(f"output/assets/sprites/{file}.png", png)
```

### 산출물

```
output/
├── src/assets/
│   ├── lzw.h
│   ├── lzw.c
│   ├── rle.h
│   └── rle.c
│
├── assets/
│   ├── sprites/
│   │   ├── PLAYER1.png
│   │   ├── LINDA.png
│   │   └── ... (17개)
│   └── levels/
│       └── ... (4개)
│
├── docs/
│   └── phase2_compression_analysis.md
│
└── temp/
    ├── decompressed/  (36개 .bin 파일)
    └── lzw_verification_log.txt
```

### 📊 CHECKPOINT #2: 압축 알고리즘 역산 완료

**자동 생성 보고서**: `output/docs/phase2_report.md`

```markdown
# Phase 2 완료 보고서

## 실행 정보
- 시작: 2025-11-24 16:00
- 종료: 2025-11-25 02:30
- 소요 시간: 10.5시간
- 재시도 횟수: LZW 7회, RLE 2회

## LZW 구현 결과

### 확정된 파라미터
- 초기 코드 길이: 9비트
- 최대 코드 길이: 16비트
- 비트 순서: MSB first
- 코드 256: Clear code (딕셔너리 초기화)
- 최대 딕셔너리: 65536 엔트리

### 검증 결과
| 파일 | 크기 (압축) | 크기 (해제) | 일치율 |
|------|------------|------------|--------|
| PLAYER1.EG1 | 19,326 | 48,000 | 100% ✅ |
| LINDA.EG1 | 14,082 | 38,400 | 100% ✅ |
| LEVEL11.PC1 | 15,234 | 64,000 | 100% ✅ |
| ... | ... | ... | 36/36 (100%) ✅ |

### 생성된 코드
- `src/assets/lzw.c`: 287 lines
- `src/assets/rle.c`: 94 lines
- 컴파일 성공: ✅
- 메모리 누수 검사: ✅ (valgrind clean)

## 그래픽 에셋 추출

- 스프라이트: 17개 PNG 생성
- 레벨 배경: 4개 PNG 생성
- 애니메이션: 10개 시퀀스 추출

## 다음 Phase 준비

✅ Phase 3 (게임 로직 분석) 진행 가능
- 모든 에셋 파일 접근 가능
- 메모리 덤프 분석 준비 완료
```

**사용자 결정**:
- [ ] ✅ Phase 3 진행 승인
- [ ] 🔍 압축 해제 결과 검토
- [ ] 💾 저장하고 중단
- [ ] ⛔ 작업 종료

---

## Phase 3: 게임 로직 완전 추출 (24-48시간)

### 목표
- 모든 데이터 구조 정의
- 모든 게임 함수 재구현
- 완전한 C++ 소스 코드 생성

### 하위 Phase

#### Phase 3.1: 데이터 구조 발견 (8시간)

```markdown
질문 1: "메모리 덤프를 분석해서 플레이어 데이터 위치를 찾아줘.

         Execution Flow JSON을 활용:
         1. 입력 처리 함수 찾기
         2. 그 함수가 읽는 메모리 주소들
         3. 반복 패턴 찾기 (x, y, health 등)
         4. 구조체 크기 역산"

질문 2: "적 캐릭터 배열을 찾아줘.
         - 배열 시작 주소
         - 구조체 크기
         - 최대 개수
         - 각 필드 의미"

질문 3: "발견한 구조체들을 C로 정의해줘:
         struct Player { ... };
         struct Enemy { ... };
         struct Level { ... };"
```

**자동 검증**:
```python
# 메모리 덤프에서 구조체 인스턴스 찾기
mem = load_memory_dump()
player_instances = find_instances(mem, PlayerStruct)
enemy_instances = find_instances(mem, EnemyStruct)

# 합리성 검사
assert len(player_instances) == 1 or 2  # 1P or 2P
assert 0 < len(enemy_instances) <= 50
```

#### Phase 3.2: 함수 로직 추출 (16시간)

```markdown
질문 4: "플레이어 업데이트 함수를 찾아서 디컴파일해줘.
         Player 구조체를 읽고 쓰는 함수들을 모두 찾아줘."

질문 5: "충돌 감지 함수를 찾아줘.
         히트박스 계산 로직을 C++로 구현해줘."

질문 6: "적 AI 함수를 찾아줘.
         상태 머신을 분석해서 C++로 구현해줘."

... (수십 개 함수)
```

**자동 검증**:
```python
# 행동 기반 테스트
test_scenarios = [
    {
        "name": "플레이어 이동",
        "input": {"keys": ["RIGHT"], "frames": 10},
        "expected": {"player.x": initial_x + 30}
    },
    {
        "name": "적 공격",
        "input": {"enemy_action": "PUNCH"},
        "expected": {"player.health": initial_health - 15}
    }
]

for scenario in test_scenarios:
    result = run_reconstructed_game(scenario["input"])
    assert result == scenario["expected"]
```

### 산출물

```
output/
├── src/
│   ├── main.cpp
│   ├── game.h / .cpp
│   ├── entities/
│   │   ├── player.h / .cpp
│   │   ├── enemy.h / .cpp
│   │   └── item.h / .cpp
│   ├── systems/
│   │   ├── collision.h / .cpp
│   │   ├── physics.h / .cpp
│   │   └── ai.h / .cpp
│   └── data/
│       └── structures.h
│
└── docs/
    ├── phase3_logic_analysis.md
    ├── data_structures.md
    └── function_catalog.md
```

### 📊 CHECKPOINT #3: 게임 로직 추출 완료

**보고서**: `output/docs/phase3_report.md`

```markdown
# Phase 3 완료 보고서

## 데이터 구조 (15개 정의)
- Player: 48 bytes at 0x5000
- Enemy[50]: 32 bytes each at 0x6000
- Level: 128 bytes at 0x8000
- ...

## 함수 구현 (87개)
- update_player(): ✅
- update_enemy(): ✅
- check_collision(): ✅
- ...

## 행동 검증
- 테스트 시나리오: 45개
- 통과: 43개 (95.6%) ✅
- 실패: 2개 (세부사항 참조)

## 코드 품질
- 컴파일 성공: ✅
- 경고: 3개 (무시 가능)
- Valgrind: Clean ✅
```

**사용자 결정**:
- [ ] ✅ Phase 4 진행
- [ ] 🔍 실패한 테스트 수정
- [ ] 💾 저장

---

## Phase 4: 통합 및 최종 검증 (8-16시간)

### 목표
- 완전한 프로젝트 통합
- 종합 테스트
- 문서 생성

### 자동 실행

```python
1. CMake 프로젝트 생성
2. 전체 빌드 테스트
3. 통합 테스트 실행
4. 문서 자동 생성
5. 최종 패키징
```

### 📊 CHECKPOINT #4: 프로젝트 완료

```markdown
# 최종 완료 보고서

## 프로젝트 정보
- 총 소요 시간: 58시간
- 총 코드 라인: 12,847 lines
- 파일 개수: 87개

## 품질 지표
- 컴파일 성공: ✅ 100%
- 원본 행동 일치: ✅ 96.3%
- 코드 커버리지: ✅ 92.1%
- 메모리 안전성: ✅ Clean

## 최종 산출물
- C++ 소스 코드: output/src/
- 게임 에셋: output/assets/
- 문서: output/docs/
- 빌드 스크립트: output/CMakeLists.txt

## 사용 방법
cd output
mkdir build && cd build
cmake ..
make
./double_dragon
```

**사용자 결정**:
- [ ] ✅ 프로젝트 인수
- [ ] 🔧 추가 개선 필요
- [ ] 📦 배포 준비

---

## 4. 인간 체크포인트

### 4.1 체크포인트 목록

| # | Phase | 대기 시점 | 예상 소요 | 누적 시간 |
|---|-------|----------|----------|----------|
| #0 | 환경 준비 | 환경 검증 완료 후 | 30분 | 0.5h |
| #1 | 파일 포맷 | 전체 파일 파싱 성공 | 6-12시간 | 12.5h |
| #2 | 압축 알고리즘 | 36개 파일 압축 해제 성공 | 8-16시간 | 28.5h |
| #3 | 게임 로직 | 모든 함수 재구현 완료 | 24-48시간 | 76.5h |
| #4 | 최종 통합 | 프로젝트 빌드 성공 | 8-16시간 | 92.5h |

### 4.2 체크포인트 프로세스

**자동 실행**:
```python
def checkpoint(phase_number):
    # 1. 보고서 생성
    report = generate_report(phase_number)
    save(f"output/docs/phase{phase_number}_report.md", report)

    # 2. 체크포인트 저장
    checkpoint_data = {
        "phase": phase_number,
        "timestamp": now(),
        "status": "awaiting_approval",
        "confidence": calculate_confidence(),
        "artifacts": list_artifacts(),
        "next_phase_estimate": estimate_time(phase_number + 1)
    }
    save(f"output/checkpoints/phase{phase_number}.json", checkpoint_data)

    # 3. 실행 중지
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║  CHECKPOINT #{phase_number} - 사용자 검토 필요      ║
    ╚═══════════════════════════════════════════╝

    Phase {phase_number} 완료!

    📊 보고서: output/docs/phase{phase_number}_report.md
    💾 체크포인트: output/checkpoints/phase{phase_number}.json

    다음 작업:
    1. 보고서를 검토하세요
    2. 산출물을 확인하세요
    3. 결정을 내리세요:
       - 'approve' : 다음 Phase 진행
       - 'review'  : 이 Phase 재검토
       - 'pause'   : 저장하고 나중에 재개
       - 'stop'    : 작업 종료

    명령어: python resume.py --checkpoint phase{phase_number} --decision [approve/review/pause/stop]
    """)

    sys.exit(0)  # 실행 중지
```

**사용자 재개**:
```bash
# 검토 후 재개
python resume.py --checkpoint phase1 --decision approve

# Phase 재검토
python resume.py --checkpoint phase1 --decision review --notes "헤더 구조 재확인 필요"

# 나중에 재개 (모든 상태 저장됨)
python resume.py --checkpoint phase1 --decision pause

# 작업 중단
python resume.py --checkpoint phase1 --decision stop
```

---

## 5. 중단/재개 메커니즘

### 5.1 상태 저장

**자동 저장 시점**:
- 각 체크포인트
- 1시간마다 자동
- 에러 발생 시

**저장 내용**:
```json
{
  "session_id": "20251124_090000",
  "current_phase": 2,
  "current_step": "2.2",
  "elapsed_time": 18.5,

  "knowledge_base": {
    "file_formats": { /* 확정된 구조체들 */ },
    "functions": { /* 분석 완료된 함수들 */ },
    "verified_implementations": { /* 검증된 코드 */ }
  },

  "artifacts": [
    "output/src/assets/file_formats.h",
    "output/src/assets/lzw.c",
    /* ... */
  ],

  "next_action": {
    "phase": 2,
    "step": "2.3",
    "description": "RLE 루틴 분석 시작"
  }
}
```

### 5.2 재개 프로세스

```bash
# 마지막 체크포인트부터 재개
python resume.py --auto

# 특정 체크포인트부터 재개
python resume.py --checkpoint phase2

# 특정 단계부터 재개
python resume.py --checkpoint phase2 --step 2.3
```

```python
def resume_from_checkpoint(checkpoint_file):
    # 1. 상태 로드
    state = load_json(checkpoint_file)

    # 2. 지식 베이스 복원
    knowledge_base = state["knowledge_base"]

    # 3. 이전 산출물 확인
    for artifact in state["artifacts"]:
        assert os.path.exists(artifact), f"Missing: {artifact}"

    # 4. 다음 작업부터 재개
    next_phase = state["next_action"]["phase"]
    next_step = state["next_action"]["step"]

    print(f"재개: Phase {next_phase}, Step {next_step}")

    # 5. 실행 계속
    execute_from(next_phase, next_step, knowledge_base)
```

### 5.3 긴급 중단 처리

**자동 중단 조건**:
```python
class EmergencyStop(Exception):
    pass

def monitor_execution():
    while running:
        # 1. 검증 실패율 체크
        if failure_rate > 0.5:
            save_emergency_checkpoint()
            raise EmergencyStop("High failure rate")

        # 2. 반복 횟수 체크
        if iteration_count > 50:
            save_emergency_checkpoint()
            raise EmergencyStop("Max iterations exceeded")

        # 3. 리소스 체크
        if disk_space < 1GB:
            save_emergency_checkpoint()
            raise EmergencyStop("Low disk space")

        sleep(60)
```

**긴급 체크포인트**:
```bash
output/checkpoints/emergency_20251124_153045.json
```

---

## 6. 최종 산출물

### 6.1 디렉토리 구조

```
output/
├── CMakeLists.txt
├── README.md
├── LICENSE
│
├── docs/
│   ├── ARCHITECTURE.md           # AI 생성 아키텍처 문서
│   ├── DATA_STRUCTURES.md        # 모든 구조체 설명
│   ├── ALGORITHMS.md             # 압축 등 알고리즘
│   ├── FUNCTION_REFERENCE.md     # 함수 레퍼런스
│   ├── VERIFICATION_REPORT.md    # 검증 결과
│   │
│   ├── phase0_report.md
│   ├── phase1_report.md
│   ├── phase2_report.md
│   ├── phase3_report.md
│   └── phase4_report.md
│
├── src/
│   ├── main.cpp
│   ├── game.h / .cpp
│   │
│   ├── entities/
│   │   ├── player.h / .cpp
│   │   ├── enemy.h / .cpp
│   │   ├── item.h / .cpp
│   │   └── projectile.h / .cpp
│   │
│   ├── systems/
│   │   ├── collision.h / .cpp
│   │   ├── physics.h / .cpp
│   │   ├── ai.h / .cpp
│   │   ├── renderer.h / .cpp
│   │   └── input.h / .cpp
│   │
│   ├── assets/
│   │   ├── file_formats.h
│   │   ├── loader.h / .cpp
│   │   ├── lzw.h / .cpp
│   │   └── rle.h / .cpp
│   │
│   └── data/
│       ├── level_data.h
│       ├── enemy_data.h
│       ├── animation_data.h
│       └── constants.h
│
├── assets/
│   ├── sprites/
│   │   ├── player_*.png          # 17개 스프라이트
│   │   └── ...
│   ├── levels/
│   │   └── level*.png             # 4개 레벨
│   ├── animations/
│   │   └── *.json                 # 애니메이션 정의
│   └── data/
│       ├── levels.json
│       └── enemies.json
│
├── tests/
│   ├── test_lzw.cpp
│   ├── test_collision.cpp
│   ├── test_ai.cpp
│   └── test_game_logic.cpp
│
├── checkpoints/
│   ├── phase0.json
│   ├── phase1.json
│   ├── phase2.json
│   ├── phase3.json
│   └── phase4.json
│
└── temp/
    └── [중간 생성 파일들]
```

### 6.2 사용 방법

```bash
# 1. 빌드
cd output
mkdir build && cd build
cmake ..
make

# 2. 실행
./double_dragon

# 3. 테스트
make test
```

---

## 7. 예상 타임라인

### 7.1 Phase별 예상 시간

| Phase | 작업 내용 | 최소 | 최대 | 평균 |
|-------|----------|------|------|------|
| 0 | 환경 준비 | 0.5h | 1h | 0.5h |
| 1 | 파일 포맷 | 6h | 12h | 8h |
| 2 | 압축 알고리즘 | 8h | 16h | 12h |
| 3 | 게임 로직 | 24h | 48h | 36h |
| 4 | 통합 검증 | 8h | 16h | 12h |
| **합계** | | **46.5h** | **93h** | **68.5h** |

### 7.2 현실적 일정

**풀타임 작업 (하루 8시간)**:
- 최소: 6일
- 최대: 12일
- 평균: **9일**

**파트타임 (하루 4시간)**:
- 평균: **18일**

**주말만 (주 8시간)**:
- 평균: **9주**

---

## 8. 리스크 및 대응

### 8.1 예상 리스크

| 리스크 | 확률 | 영향 | 대응 방안 |
|--------|------|------|----------|
| GhidraMCP 연결 실패 | 10% | 高 | 대안: 수동 Ghidra 분석 |
| LZW 파라미터 확정 실패 | 30% | 中 | 최대 50회 재시도 |
| 검증 실패 50% 이상 | 20% | 高 | 긴급 중단 → 수동 검토 |
| 메모리/디스크 부족 | 5% | 中 | 자동 정리 스크립트 |

### 8.2 대응 전략

**자동 대응**:
- 재시도 (최대 50회)
- 대안 접근법 시도
- 긴급 저장 및 중단

**사용자 개입 필요**:
- 검증 50회 실패
- 예상치 못한 구조 발견
- 리소스 부족

---

## 9. 성공 기준

### 9.1 필수 조건 (Must Have)

- ✅ 모든 파일 파싱 가능
- ✅ 압축 해제 100% 일치
- ✅ 컴파일 성공
- ✅ 메모리 안전성 (Valgrind clean)

### 9.2 목표 조건 (Should Have)

- ✅ 원본과 행동 95% 일치
- ✅ 코드 커버리지 90% 이상
- ✅ 문서 자동 생성

### 9.3 선택 조건 (Nice to Have)

- ⭐ 원본과 100% 동일
- ⭐ 웹 버전 호환
- ⭐ 에디터 도구 제공

---

## 10. 시작 명령어

```bash
# 완전 자율 모드로 시작
python autonomous_reverser.py --mode fully-autonomous

# 대화형 모드로 시작 (각 체크포인트에서 확인)
python autonomous_reverser.py --mode interactive

# 특정 Phase부터 시작
python autonomous_reverser.py --start-from phase2

# 이전 작업 재개
python resume.py --auto
```

---

**문서 버전**: 1.0
**최종 수정**: 2025-11-24
**작성자**: AI Assistant
**검토 필요**: ✅ 사용자 승인 대기
