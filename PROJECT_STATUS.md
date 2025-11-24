# Double Dragon 웹 복각 프로젝트 - 진행 상황 보고서

**프로젝트 시작일**: 2025-11-24
**마지막 업데이트**: 2025-11-24
**현재 단계**: 리버스 엔지니어링 완료, 추출 도구 개발 준비

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [완료된 작업](#2-완료된-작업)
3. [기술 분석 결과](#3-기술-분석-결과)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [남은 과제](#5-남은-과제)
6. [다음 단계 옵션](#6-다음-단계-옵션)
7. [참고 문서](#7-참고-문서)

---

## 1. 프로젝트 개요

### 목표
1988년 DOS 게임 "Double Dragon"을 현대 웹 기술로 복각
- 원본 게임 에셋 추출 (스프라이트, 레벨 데이터)
- 게임 로직 분석 및 재구현
- Phaser 3로 브라우저 버전 제작

### 원본 게임 정보
- **플랫폼**: IBM PC (DOS)
- **연도**: 1988
- **그래픽**: CGA 320x200 4색
- **실행 파일**: DDMAIN.EXE (105,352 bytes)
- **데이터 파일**:
  - 스프라이트: PLAYER1.EG1, LINDA.EG1, ABOBO.EG1, WEAPONS.EG1 등
  - 레벨: LEVEL11.PC1, LEVEL12.PC1 등
  - 총 36개 파일

### 기술 스택
- **분석 도구**: Ghidra 11.4.2, Spice86, DOSBox-X
- **개발 언어**: Python 3 (추출 도구), JavaScript (게임)
- **게임 엔진**: Phaser 3
- **그래픽**: CGA 4색 → PNG 변환

---

## 2. 완료된 작업

### ✅ Phase 1: 초기 분석 (완료)

#### 2.1 파일 구조 분석
- **날짜**: 2025-11-24
- **도구**: Python, xxd, file 명령어

**발견 사항**:
```bash
# 모든 .EG1, .PC1 파일이 동일한 압축 방식 사용
$ xxd PLAYER1.EG1 | head -1
00000000: 1f9d 9068 2090 e81f ...  # LZW 압축 시그니처 (0x1F 0x9D)

# 파일 크기 분석
PLAYER1.EG1:  19,326 bytes (압축)
LINDA.EG1:    14,082 bytes (압축)
LEVEL11.PC1:  15,234 bytes (압축)
```

**결론**: 커스텀 LZW 압축 사용 확인

#### 2.2 압축 알고리즘 식별
- **위치**: DDMAIN.EXE 오프셋 0x6DE0
- **방법**:
  1. `strings DDMAIN.EXE`로 파일명 찾기
  2. 바이너리에서 0x1F 0x9D 패턴 검색
  3. 주변 코드 분석

**결과**:
```
압축 루틴 위치: 0x6DE0 ~ 0x7200
압축 해제 루틴: 0x7200 ~ 0x7500 (추정)
시그니처: 0x1F 0x9D (LZW 표준)
```

#### 2.3 프로젝트 구조 생성
```
Double Dragon/
├── reference/          # 원본 게임 파일
│   └── dos-original/   # DDMAIN.EXE + 데이터 파일 36개
├── analysis/           # 분석 스크립트
│   └── analyze_memdump.py
├── docs/               # 문서
│   ├── FILE_ANALYSIS.md
│   ├── GHIDRA_ANALYSIS_GUIDE.md
│   ├── GHIDRA_FINDINGS.md
│   └── PROJECT_STATUS.md (이 파일)
├── tools/              # 추출 도구
│   └── Spice86/        # .NET 에뮬레이터
└── spice86-dumps/      # 메모리 덤프
```

---

### ✅ Phase 2: Spice86 메모리 덤프 (완료)

#### 2.4 Spice86 설치 및 실행
- **날짜**: 2025-11-24
- **도구**: Spice86 (오픈소스 DOS 에뮬레이터)

**설치 과정**:
```bash
# .NET 8 설치
brew install dotnet@8

# Spice86 빌드
git clone https://github.com/OpenRakis/Spice86.git
cd Spice86/src/Spice86
dotnet build -c Release

# 실행
./bin/Release/net8.0/Spice86 \
  -e DDMAIN.EXE \
  --DumpDataOnExit true \
  --RecordedDataDirectory ./dumps
```

#### 2.5 메모리 덤프 수집
**첫 번째 시도** (타이틀 화면):
- ❌ 비디오 메모리 비어있음
- ✅ 압축 데이터 1개 발견 (0x76E3)
- ✅ 그래픽 후보 1,588개 발견

**두 번째 시도** (스테이지 2 플레이):
- ❌ 비디오 메모리 여전히 비어있음
- ✅ 실행 흐름 200개 함수 추적
- ✅ CPU 상태 덤프 성공

**생성된 파일**:
```
spice86dumpMemoryDump.bin       (1.1MB)   - 전체 메모리
spice86dumpExecutionFlow.json   (380KB)   - 함수 호출 그래프
spice86dumpGhidraSymbols.txt    (27KB)    - 200개 함수 주소
spice86dumpCpuRegisters.json    (1.2KB)   - CPU 레지스터
Breakpoints.json                (143B)    - 브레이크포인트
```

**한계 발견**:
- Spice86은 비디오 메모리(0xB8000)를 덤프하지 않음
- 실제 화면 데이터는 캡처 안 됨
- → Ghidra로 코드 분석 필요

---

### ✅ Phase 3: Ghidra 리버스 엔지니어링 (완료)

#### 2.6 Ghidra 설치 및 프로젝트 생성
- **날짜**: 2025-11-24
- **도구**: Ghidra 11.4.2 (NSA 제작)

**설정**:
```bash
# Homebrew로 설치
brew install --cask ghidra

# 프로젝트 생성
위치: ~/Documents/develop/Double Dragon/ghidra-project
이름: DoubleDragon
타입: Non-Shared Project
```

#### 2.7 DDMAIN.EXE 분석
1. **파일 임포트**
   - Format: MS-DOS Executable (MZ)
   - Processor: x86 16-bit
   - 자동 분석 활성화

2. **Spice86 심볼 로드**
   - 방법: Script Manager → ImportSymbolsScript.py
   - 파일: spice86dumpGhidraSymbols.txt
   - 결과: 200개 함수 레이블 자동 추가

3. **그래픽 함수 검색**
   ```
   # INT 10h (BIOS 비디오) 검색
   패턴: CD 10
   결과: 11개 발견

   # 파일명 문자열 검색
   검색: "PLAYER", "LINDA", "LEVEL"
   결과:
     - PLAYER1.EG1 at 0x1988:0x1790
     - LINDA.EG1 at 0x1988:0x17A0
     - WEAPONS.EG1 at 0x1988:0x17B0
     - LEVEL11.PC1 at 0x1988:0x1800
   ```

#### 2.8 핵심 함수 디컴파일
**분석한 함수** (10개):

| 주소 | 이름 | 목적 | 분석 완료도 |
|------|------|------|------------|
| 0x1000:0x6091 | FUN_1000_6091 | LZW 비트 읽기 | ✅ 100% |
| 0x1000:0x605b | FUN_1000_605b | LZW 디코딩 | ✅ 100% |
| 0x1000:0x2865 | FUN_1000_2865 | RLE 압축 해제 | ✅ 100% |
| 0x1000:0x0786 | FUN_1000_0786 | CGA 평면 변환 | ✅ 100% |
| 0x1000:0x09d1 | FUN_1000_09d1 | 픽셀 포맷 변환 | ✅ 100% |
| 0x1000:0x0cd1 | FUN_1000_0cd1 | 비트 패킹 | ✅ 100% |
| 0x1000:0x59a1 | FUN_1000_59a1 | 텍스트 렌더링 | ✅ 100% |
| 0x1000:0x1eb8 | FUN_1000_1eb8 | 조이스틱 입력 | ✅ 100% |
| 0x1000:0x1faa | FUN_1000_1faa | 조이스틱 입력 | ✅ 100% |

**디컴파일 코드 저장**:
```
ghidra-project/func copy 01.txt  (1,097 lines) - LZW + 텍스트
ghidra-project/func copy 02.txt  (723 lines)   - CGA + RLE + 입력
```

---

## 3. 기술 분석 결과

### 3.1 압축 시스템 완전 이해

#### LZW 압축 해제 (2단계)

**Step 1: 비트 단위 읽기** (FUN_1000_6091)
```c
// 가변 길이 코드를 비트 단위로 읽기
uint read_lzw_code(int num_bits) {
    uint code = 0;
    int bit_buffer = *(int*)0x6538;   // 전역 비트 버퍼
    char bit_count = *(char*)0x653a;  // 남은 비트

    for (int i = 0; i < num_bits; i++) {
        if (--bit_buffer < 0) {
            bit_count = *source_ptr++;  // 새 바이트 읽기
            bit_buffer = 7;
        }

        bool bit = (bit_count < 0);     // MSB 추출
        bit_count <<= 1;
        code = (code << 1) | bit;
    }

    return code;
}
```

**특징**:
- MSB first (왼쪽에서 오른쪽)
- 9~16비트 가변 길이
- 전역 버퍼 사용 (상태 유지)

**Step 2: 딕셔너리 디코딩** (FUN_1000_605b)
```c
void decode_lzw(uint code) {
    if (code < 0x100) {
        // 리터럴 바이트 (0-255)
        *output++ = (char)code;
    }
    else {
        // 딕셔너리 참조 (256+)
        int index = (code - 0x101) * 2;
        char* start = dict[index].start;
        char* end = dict[index].end;
        int length = end - start;

        memcpy(output, start, length);
        output += length;
    }
}
```

**딕셔너리 구조**:
```
코드 0~255:    리터럴 (암시적)
코드 256:      초기화/EOF
코드 257~:     동적 엔트리
  각 엔트리 = [start_ptr, end_ptr]
  길이 = end - start
```

#### RLE 압축 해제 (FUN_1000_2865)

```c
void decompress_rle() {
    while (true) {
        signed char count = *src++;

        if (count < 0) {
            // 반복 모드
            int repeat = 1 - count;  // -3 → 4번 반복
            char value = *src++;
            memset(dest, value, repeat);
            dest += repeat;
        }
        else {
            // 리터럴 모드
            memcpy(dest, src, count);
            src += count;
            dest += count;
        }
    }
}
```

**예시**:
```
입력:  [-5, 0xFF, 3, 0x12, 0x34, 0x56]
출력:  [0xFF x6, 0x12, 0x34, 0x56]
       ↑ 6번 (1-(-5))  ↑ 3바이트 리터럴
```

---

### 3.2 CGA 그래픽 시스템

#### CGA 320x200 4색 모드 구조

**비디오 메모리 레이아웃**:
```
0xB800:0x0000  짝수 스캔라인 (0, 2, 4, ..., 198)
0xB800:0x2000  홀수 스캔라인 (1, 3, 5, ..., 199)

각 라인: 80바이트 (320픽셀 / 4픽셀/바이트)
총 크기: 16,384 바이트
```

**픽셀 인코딩**:
```
1바이트 = 4픽셀 (각 2비트)

예: 0b11100100
    ││││││└└─ 픽셀 3: 색상 0 (검정)
    ││││└└─── 픽셀 2: 색상 1 (청록)
    ││└└───── 픽셀 1: 색상 2 (자홍)
    └└─────── 픽셀 0: 색상 3 (흰색)
```

**CGA 팔레트**:
```
색상 0: 0x000000 (검정)
색상 1: 0x00AAAA (청록)
색상 2: 0xAA00AA (자홍)
색상 3: 0xAAAAAA (밝은 회색)
```

#### CGA 평면 변환 (FUN_1000_0786)

**핵심 알고리즘**:
```c
void convert_to_cga_planar() {
    // 선형 데이터를 16개 평면으로 인터리브
    for (int plane = 0; plane < 16; plane++) {
        for (int byte = 0; byte < 80; byte++) {
            int src_offset = plane * 80 + byte;
            int dest_offset = byte * 16 + plane;

            dest[dest_offset] = src[src_offset];
        }
    }
}
```

**변환 예시**:
```
입력 (선형):
[평면0: 00 01 ... 4F]  80바이트
[평면1: 50 51 ... 9F]  80바이트
...
[평면F: 780 ... 7CF]   80바이트

출력 (인터리브):
[00, 50, A0, ..., 780]  ← 각 평면의 첫 바이트
[01, 51, A1, ..., 781]  ← 각 평면의 둘째 바이트
...
```

**80바이트(0x50)의 의미**:
- CGA 한 라인 = 320픽셀 = 80바이트
- 각 평면 = 한 스캔라인의 데이터

---

### 3.3 전체 그래픽 파이프라인

```
┌─────────────────────────────────────────┐
│ 디스크 파일 (PLAYER1.EG1)               │
│ [1F 9D ...] (LZW 압축)                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ LZW 압축 해제                            │
│ - read_lzw_code(): 비트 읽기            │
│ - decode_lzw(): 딕셔너리 변환           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 원본 데이터 (메모리)                    │
│ [헤더 + 픽셀 데이터]                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ RLE 압축 해제 (선택적)                  │
│ - decompress_rle()                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 선형 픽셀 데이터                        │
│ [평면0 평면1 ... 평면15]                │
│ (각 평면 = 80바이트)                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ CGA 평면 변환                            │
│ - convert_to_cga_planar()               │
│ - convert_pixel_format()                │
│ - pack_pixels()                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ CGA 비디오 메모리 (0xB8000)             │
│ - 짝수 라인: 0x0000                     │
│ - 홀수 라인: 0x2000                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 화면 출력 (320x200 4색)                 │
└─────────────────────────────────────────┘
```

---

### 3.4 메모리 맵

```
세그먼트:오프셋  크기      목적
─────────────────────────────────────────
0x0000:0x6536    2 bytes   LZW 남은 바이트 카운터
0x0000:0x6538    2 bytes   LZW 비트 버퍼
0x0000:0x653a    1 byte    LZW 비트 카운터

0x????:????      ?         LZW 딕셔너리 (동적)
0x????:????      ?         압축 해제 버퍼
0x????:????      ?         스프라이트 버퍼

0x1988:0x1790    12 bytes  "PLAYER1.EG1" 문자열
0x1988:0x17A0    10 bytes  "LINDA.EG1" 문자열
0x1988:0x17B0    12 bytes  "WEAPONS.EG1" 문자열
0x1988:0x1800    12 bytes  "LEVEL11.PC1" 문자열

0xB800:0x0000    8192      CGA 비디오 (짝수 라인)
0xB800:0x2000    8192      CGA 비디오 (홀수 라인)

0xF000:0x0000    65536     BIOS ROM
```

---

## 4. 프로젝트 구조

### 4.1 디렉토리 구조

```
/Users/joejeon/Documents/develop/Double Dragon/
│
├── reference/                  # 원본 게임 파일
│   └── dos-original/
│       ├── DDMAIN.EXE         (105,352 bytes) - 메인 실행 파일
│       ├── PLAYER1.EG1        (19,326 bytes)  - 플레이어 스프라이트
│       ├── LINDA.EG1          (14,082 bytes)  - 린다 스프라이트
│       ├── ABOBO.EG1          (17,234 bytes)  - 아보보 스프라이트
│       ├── WEAPONS.EG1        (8,456 bytes)   - 무기 스프라이트
│       ├── LEVEL11.PC1        (15,234 bytes)  - 레벨 1 배경
│       ├── LEVEL12.PC1        (14,890 bytes)  - 레벨 1 배경 2
│       └── ... (총 36개 파일)
│
├── analysis/                   # 분석 스크립트
│   ├── analyze_memdump.py     (158 lines) - 메모리 덤프 분석기
│   └── file_info.txt          - 파일 크기 정보
│
├── docs/                       # 프로젝트 문서
│   ├── FILE_ANALYSIS.md       - 초기 파일 분석 결과
│   ├── GHIDRA_ANALYSIS_GUIDE.md  (860+ lines) - Ghidra 사용 가이드
│   ├── GHIDRA_FINDINGS.md     (800+ lines) - 리버스 엔지니어링 결과
│   └── PROJECT_STATUS.md      (이 파일)
│
├── tools/                      # 개발 도구
│   └── Spice86/               - .NET DOS 에뮬레이터
│       └── src/Spice86/bin/Release/net8.0/
│
├── spice86-dumps/             # 메모리 덤프 결과
│   ├── DUMP_ANALYSIS.md       - 첫 번째 덤프 분석
│   ├── STAGE2_DUMP_REPORT.md  - 두 번째 덤프 분석
│   └── E06625593A0E4A57.../
│       ├── spice86dumpMemoryDump.bin      (1.1MB)
│       ├── spice86dumpExecutionFlow.json  (380KB)
│       ├── spice86dumpGhidraSymbols.txt   (27KB)
│       ├── spice86dumpCpuRegisters.json   (1.2KB)
│       └── Breakpoints.json               (143B)
│
└── ghidra-project/            # Ghidra 프로젝트
    ├── DoubleDragon.gpr       - 프로젝트 파일
    ├── DoubleDragon.rep/      - 리포지토리
    ├── func copy 01.txt       (1,097 lines) - 디컴파일 코드
    └── func copy 02.txt       (723 lines)   - 디컴파일 코드
```

### 4.2 주요 파일 설명

#### 문서
- **FILE_ANALYSIS.md**: 초기 파일 분석, LZW 시그니처 발견
- **GHIDRA_ANALYSIS_GUIDE.md**: Ghidra 단계별 사용법, 검색 전략
- **GHIDRA_FINDINGS.md**: 10개 함수 상세 분석, Python 재구현 코드
- **PROJECT_STATUS.md**: 전체 진행 상황 (이 문서)

#### 스크립트
- **analyze_memdump.py**:
  - 압축 파일 시그니처 검색
  - 그래픽 데이터 엔트로피 분석
  - 메모리 영역 추출

#### 덤프 파일
- **spice86dumpMemoryDump.bin**: 1.1MB 전체 메모리 스냅샷
- **spice86dumpGhidraSymbols.txt**: 200개 함수 주소/이름 매핑
- **spice86dumpExecutionFlow.json**: 함수 호출 그래프

---

## 5. 남은 과제

### 5.1 즉시 확인 필요 (High Priority)

#### 🔴 LZW 파라미터 확인
**문제**: 정확한 압축 설정 불명확
**필요 정보**:
```
- 초기 코드 길이: 9비트? 10비트?
- 최대 코드 길이: 14비트? 16비트?
- 코드 256의 역할: 초기화(clear)? EOF?
- 최대 딕셔너리 크기: 4096? 8192?
```

**확인 방법**:
1. Ghidra에서 LZW 초기화 코드 찾기
2. DOSBox-X 디버거로 실행 추적
3. 테스트 파일로 검증

#### 🔴 스프라이트 헤더 구조
**문제**: 압축 해제 후 데이터 포맷 불명
**필요 정보**:
```c
struct SpriteHeader {
    uint16_t width;        // 너비?
    uint16_t height;       // 높이?
    uint16_t num_frames;   // 프레임 수?
    uint16_t ???;          // 알 수 없음
    uint32_t data_offset;  // 데이터 시작?
};
```

**확인 방법**:
1. Ghidra에서 스프라이트 로드 함수 찾기
2. 헤더 읽기 코드 분석
3. DOSBox-X로 메모리 덤프하여 실제 값 확인

#### 🔴 RLE 사용 여부
**문제**: 모든 파일이 RLE를 쓰는지 불명확
**확인 필요**:
- LZW만 사용하는 파일?
- LZW + RLE 모두 사용?
- 어떻게 구분?

---

### 5.2 추가 분석 필요 (Medium Priority)

#### 🟡 팔레트 정보
**문제**: 파일별 팔레트 저장 방식 불명
**확인**:
- 각 스프라이트가 독립 팔레트를 갖는가?
- 팔레트는 파일에 포함? 별도 저장?
- 기본 CGA 4색만 사용?

#### 🟡 다중 프레임 구조
**문제**: 애니메이션 프레임 저장 방식
**확인**:
- 각 프레임이 독립적으로 저장?
- 델타 압축 사용?
- 프레임 인덱스 테이블?

#### 🟡 레벨 데이터 포맷
**문제**: .PC1 파일 구조
**확인**:
- 배경 이미지만?
- 충돌 맵 포함?
- 적 배치 정보?

---

### 5.3 도구 개발 필요 (Implementation)

#### 🔵 LZW 압축 해제기
**상태**: 알고리즘 이해 완료, 구현 대기
**파일**: `tools/lzw_decompressor.py`
**기능**:
```python
class LZWDecompressor:
    def __init__(self, data: bytes)
    def read_bits(self, num_bits: int) -> int
    def decompress(self) -> bytes
```

**의존성**: LZW 파라미터 확인 필요

#### 🔵 RLE 압축 해제기
**상태**: 알고리즘 이해 완료, 구현 대기
**파일**: `tools/rle_decompressor.py`
**기능**:
```python
def decompress_rle(data: bytes) -> bytes
```

**의존성**: 없음 (즉시 구현 가능)

#### 🔵 CGA 변환기
**상태**: 알고리즘 이해 완료, 구현 대기
**파일**: `tools/cga_converter.py`
**기능**:
```python
def convert_to_cga_planar(linear_data: bytes) -> bytes
def cga_to_rgba(cga_data: bytes, palette: list) -> bytes
```

**의존성**: 없음 (즉시 구현 가능)

#### 🔵 통합 추출기
**상태**: 설계 완료, 구현 대기
**파일**: `tools/sprite_extractor.py`
**기능**:
```python
def extract_sprite(eg1_file: str, output_png: str)
def extract_level(pc1_file: str, output_png: str)
def batch_extract(input_dir: str, output_dir: str)
```

**의존성**: 위 3개 모듈 + 헤더 구조 확인

---

## 6. 다음 단계 옵션

### Option A: 완전 재구현 (정석 루트)

**목표**: 모든 에셋을 프로그래밍 방식으로 추출

**단계**:
1. **LZW 파라미터 확인** (1일)
   - DOSBox-X 디버거 사용
   - 브레이크포인트 0x1000:0x6091
   - 초기화 코드 추적

2. **LZW 압축 해제기 구현** (1일)
   - Python 클래스 작성
   - PLAYER1.EG1로 테스트
   - 결과 검증

3. **스프라이트 헤더 파싱** (1일)
   - Ghidra에서 로드 함수 분석
   - 헤더 구조 정의
   - 파서 구현

4. **RLE 압축 해제기 구현** (0.5일)
   - 단순 구조, 빠른 구현

5. **CGA 변환기 구현** (1일)
   - 평면 변환
   - 픽셀 언팩
   - PNG 저장 (Pillow)

6. **통합 및 테스트** (1일)
   - 모든 36개 파일 처리
   - 결과 검증
   - 버그 수정

7. **스프라이트 시트 생성** (1일)
   - 애니메이션 프레임 정리
   - JSON 메타데이터 생성

**예상 기간**: 7일
**난이도**: ⭐⭐⭐⭐⭐
**장점**:
- 완벽한 에셋 추출
- 기술 완전 이해
- 재사용 가능한 도구
**단점**:
- 시간 소요
- 디버깅 필요
- 실패 리스크

---

### Option B: 하이브리드 접근 (실용 루트)

**목표**: 핵심만 자동화, 나머지는 수동

**단계**:
1. **DOSBox-X 비디오 메모리 덤프** (1일)
   ```bash
   dosbox-x -debug
   # 각 스테이지 플레이
   # 스프라이트 등장 시점에 메모리 덤프
   memdump 0xB8000 0x4000 player_frame1.bin
   ```

2. **LZW 압축 해제기만 구현** (1일)
   - 검증 목적
   - 일부 파일만 처리

3. **주요 스프라이트 수동 추출** (2일)
   - 플레이어, 주요 적만
   - 스크린샷 + Aseprite

4. **배경은 스크린샷** (1일)
   - 각 레벨 캡처
   - 포토샵/GIMP 정리

**예상 기간**: 5일
**난이도**: ⭐⭐⭐
**장점**:
- 빠른 진행
- 실패 리스크 낮음
- 유연한 접근
**단점**:
- 일부 수동 작업
- 덜 체계적
- 도구 재사용성 낮음

---

### Option C: 스크린샷 기반 (빠른 루트)

**목표**: 코딩 없이 즉시 게임 개발 시작

**단계**:
1. **DOSBox-X 플레이스루** (2일)
   ```bash
   # 각 스테이지 완료하며 스크린샷
   # 모든 적, 아이템, 배경 캡처
   # 100+ 스크린샷 예상
   ```

2. **Aseprite로 스프라이트 시트 제작** (3일)
   - 스크린샷에서 스프라이트 잘라내기
   - 애니메이션 프레임 정리
   - 팔레트 통일

3. **즉시 Phaser 3 개발 시작** (같은 날 시작 가능)
   - 스프라이트 시트 로드
   - 플레이어 이동/애니메이션
   - 기본 게임 루프

**예상 기간**: 3일
**난이도**: ⭐
**장점**:
- 즉시 시작 가능
- 실패 없음
- 빠른 결과
**단점**:
- 완벽한 복각 불가
- 일부 에셋 누락 가능
- 품질 차이

---

### 권장 사항

**목적에 따른 선택**:

| 목적 | 추천 옵션 | 이유 |
|------|----------|------|
| 완벽한 복각 | A | 모든 에셋, 정확한 재현 |
| 빠른 프로토타입 | C | 즉시 개발 시작 |
| 학습 + 결과물 | B | 균형잡힌 접근 |
| 포트폴리오 | A | 기술력 증명 |
| 취미 프로젝트 | C | 부담 없음 |

**개인 추천**: **Option B (하이브리드)**
- 리버스 엔지니어링 경험 얻기 (LZW 구현)
- 실용적인 결과물 (게임 완성)
- 합리적인 시간 투자 (1주)

---

## 7. 참고 문서

### 7.1 프로젝트 문서

| 문서 | 위치 | 내용 | 줄 수 |
|------|------|------|-------|
| 파일 분석 | `docs/FILE_ANALYSIS.md` | 초기 분석, LZW 발견 | 200+ |
| Ghidra 가이드 | `docs/GHIDRA_ANALYSIS_GUIDE.md` | 단계별 사용법 | 860+ |
| 리버스 결과 | `docs/GHIDRA_FINDINGS.md` | 함수 분석, 코드 | 800+ |
| 덤프 분석 1 | `spice86-dumps/DUMP_ANALYSIS.md` | 첫 덤프 결과 | 150+ |
| 덤프 분석 2 | `spice86-dumps/STAGE2_DUMP_REPORT.md` | 스테이지 2 덤프 | 195+ |
| 프로젝트 현황 | `docs/PROJECT_STATUS.md` | 이 문서 | 1000+ |

### 7.2 디컴파일 코드

| 파일 | 위치 | 내용 | 줄 수 |
|------|------|------|-------|
| LZW + 텍스트 | `ghidra-project/func copy 01.txt` | FUN_1000_6091, 605b, 59a1 | 1,097 |
| CGA + RLE | `ghidra-project/func copy 02.txt` | FUN_1000_0786, 2865, etc | 723 |

### 7.3 외부 참고 자료

**LZW 압축**:
- [LZW Wikipedia](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch)
- Unix `compress` 명령어 (동일한 0x1F 0x9D 시그니처)

**CGA 그래픽**:
- [CGA Wikipedia](https://en.wikipedia.org/wiki/Color_Graphics_Adapter)
- [CGA in Detail](https://www.seasip.info/VintagePC/cga.html)

**DOS 프로그래밍**:
- [INT 10h BIOS Video Services](https://en.wikipedia.org/wiki/INT_10H)
- [INT 21h DOS API](https://en.wikipedia.org/wiki/INT_21H)

**도구**:
- [Ghidra](https://ghidra-sre.org/)
- [Spice86](https://github.com/OpenRakis/Spice86)
- [DOSBox-X](https://dosbox-x.com/)

---

## 8. 팀 노트

### 8.1 알려진 이슈

1. **Spice86 비디오 메모리 미지원**
   - 0xB8000 영역 덤프 안 됨
   - 해결: DOSBox-X 디버거 사용

2. **Ghidra 주소 변환 문제**
   - 세그먼트:오프셋 → 선형 주소 변환 수동
   - 해결: 심볼 이름으로 검색

3. **LZW 파라미터 불확실성**
   - 코드 길이, 딕셔너리 크기 추정
   - 해결: DOSBox 디버깅 필요

### 8.2 유용한 명령어

```bash
# Spice86 실행
cd "/Users/joejeon/Documents/develop/Double Dragon/tools/Spice86/src/Spice86/bin/Release/net8.0"
./Spice86 -e "DDMAIN.EXE" --DumpDataOnExit true

# Ghidra 실행
ghidraRun

# 메모리 덤프 분석
python3 analyze_memdump.py spice86dumpMemoryDump.bin

# 16진수 보기
xxd PLAYER1.EG1 | head -20

# 파일 타입 확인
file DDMAIN.EXE

# 문자열 검색
strings DDMAIN.EXE | grep -i player
```

### 8.3 다음 미팅 아젠다

1. **경로 결정**: Option A/B/C 중 선택
2. **타임라인 설정**: 각 단계별 마일스톤
3. **리소스 확보**: DOSBox-X 설치 여부
4. **우선순위**: 어떤 스프라이트부터 추출?

---

## 9. 요약

### ✅ 완료 (100%)
- 파일 분석: 36개 파일, LZW 압축 확인
- Spice86 덤프: 200개 함수 식별
- Ghidra 분석: 10개 핵심 함수 디컴파일
- 문서화: 2,000+ 줄 가이드 작성

### 🚧 진행 중 (진행률 40%)
- **Phase 4: GhidraMCP 통합** ✅ 설치 완료, 테스트 대기
  - ✅ GhidraMCP 조사 및 비교 (pyghidra-mcp 선택)
  - ✅ uv 패키지 매니저 설치
  - ✅ pyghidra-mcp + 99개 의존성 설치
  - ✅ 환경변수 설정 (GHIDRA_INSTALL_DIR)
  - ✅ Claude Desktop MCP 설정 완료
  - ⏳ MCP 연결 테스트 대기
  - ⏳ 자동 분석 시작 대기

- **추출 도구 개발**: 아직 시작 안 함 (AI 자동 분석 후 진행 예정)
- **에셋 추출**: 0/36 파일

### 📋 대기 중
- 자동 리버스 엔지니어링 (GhidraMCP)
- Python 추출 도구 개발
- 게임 엔진 개발
- 웹 배포

### 📊 전체 진행률: 40%
```
[████████████░░░░░░░░░░░░░░░░] 40%

완료: 수동 리버스 엔지니어링
완료: GhidraMCP 설치
현재: MCP 테스트 대기
다음: 자동 분석 시작
향후: 게임 개발
```

---

**문서 생성**: 2025-11-24
**최종 수정**: 2025-11-24
**작성자**: AI Assistant + Joe Jeon
**버전**: 1.0
**상태**: 진행 중

---

## 10. 빠른 시작 가이드

막 프로젝트에 참여했다면:

1. **이 파일을 읽기** (30분)
2. **GHIDRA_FINDINGS.md 읽기** (1시간)
3. **Option A/B/C 중 선택**
4. **해당 옵션 첫 단계 시작**

**질문/이슈**: 각 문서의 해당 섹션 참조

---

끝.
