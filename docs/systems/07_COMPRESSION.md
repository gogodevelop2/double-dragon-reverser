# 압축 시스템 (Compression System)

**목적**: Double Dragon에서 사용되는 두 가지 압축 알고리즘(RLE, LZW)의 구조와 동작 방식을 언어 중립적으로 설명합니다.

**관련 함수**: 10개
**의존성**: 독립적 (다른 시스템 의존 없음)
**복잡도**: ⭐⭐⭐ (RLE: ⭐⭐, LZW: ⭐⭐⭐⭐)

---

## 📋 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [RLE 압축 시스템](#3-rle-압축-시스템)
4. [LZW 압축 시스템](#4-lzw-압축-시스템)
5. [메모리 레이아웃](#5-메모리-레이아웃)
6. [함수 목록](#6-함수-목록)
7. [구현 가이드](#7-구현-가이드)
8. [테스트 전략](#8-테스트-전략)

---

## 1. 개요

### 1.1 역할

Double Dragon은 두 가지 압축 방식을 사용하여 72KB 제한 내에서 최대한 많은 데이터를 저장합니다:

1. **RLE (Run-Length Encoding)**: 스프라이트 데이터 압축
2. **LZW (Lempel-Ziv-Welch)**: 에셋 파일 압축

### 1.2 주요 기능

**RLE 압축**:
- 스프라이트 평면 데이터 압축 (4-plane CGA)
- 실시간 디코딩 (매 프레임)
- 평균 3:1 압축률

**LZW 압축**:
- 에셋 파일 압축 (LINDA.EG1, JIMMY.EG1 등)
- 게임 초기화 시 한 번만 디코딩
- Unix compress 호환 (매직 넘버: 0x1F9D)

### 1.3 사용 패턴

```
게임 시작
  ↓
LZW 디코딩 (에셋 로딩)
  → LINDA.EG1 압축 해제
  → JIMMY.EG1 압축 해제
  → 기타 에셋 압축 해제
  ↓
메인 게임 루프
  ↓
RLE 디코딩 (매 프레임)
  → 스프라이트 압축 해제 (200 스캔라인 × 4 평면)
  → VRAM 블리팅
  ↓
반복
```

---

## 2. 아키텍처

### 2.1 시스템 다이어그램

```
┌────────────────────────────────────────────┐
│         압축 시스템 (Compression)           │
├────────────────────┬───────────────────────┤
│   RLE 시스템       │    LZW 시스템         │
│  (실시간 디코딩)    │  (초기화 시 디코딩)    │
├────────────────────┼───────────────────────┤
│ • FUN_1000_0771    │ • FUN_1000_5fe0       │
│ • FUN_1000_2840    │ • FUN_1000_5ff3       │
│ • FUN_1000_2865    │ • FUN_1000_604e       │
│ • FUN_1000_2894    │ • FUN_1000_6091       │
│                    │ • FUN_1000_605b       │
│                    │ • FUN_1000_5fec       │
│                    │ • FUN_1000_6009       │
│                    │ • FUN_1000_6011       │
└────────────────────┴───────────────────────┘
           ↓                   ↓
    ┌──────────┐        ┌──────────┐
    │ 스프라이트 │        │ 에셋 파일 │
    │  데이터   │        │  데이터   │
    └──────────┘        └──────────┘
```

### 2.2 데이터 흐름

**RLE 흐름**:
```
압축된 스프라이트 데이터 (ROM)
  ↓ [RLE 디코더]
작업 버퍼 (4 평면 × 40 bytes)
  ↓ [평면 인터리빙]
VRAM (160 bytes per 스캔라인)
```

**LZW 흐름**:
```
압축된 에셋 파일 (.EG1)
  ↓ [매직 넘버 체크]
  ↓ [LZW 디코더]
메모리 버퍼 (압축 해제된 데이터)
  ↓ [게임 사용]
```

---

## 3. RLE 압축 시스템

### 3.1 개요

**용도**: 스프라이트 데이터 실시간 압축 해제
**특징**: 간단하고 빠른 디코딩 (CPU 부담 최소화)
**압축률**: 평균 3:1 (solid color 최대 20:1)

### 3.2 RLE 포맷

```
제어 바이트:
  0x80       → Skip marker (무시)
  0x00-0x7F  → Literal run (n+1 bytes follow)
  0x81-0xFF  → Repeat run ((1-n) times of next byte)
```

**예시**:
```
원본 데이터:
  [AA AA AA AA BB CC CC CC CC CC]

RLE 압축:
  [FC AA 00 BB FA CC]
   └─┬─┘ └┬┘ └─┬─┘
     │    │    │
     │    │    └─ Repeat 0xCC 5 times (1 - (-5) = 6, 근데 0xFA = -6)
     │    └────── Literal 1 byte: 0xBB
     └─────────── Repeat 0xAA 4 times (1 - (-4) = 5, 근데 0xFC = -4)

실제 계산:
  0xFC = -4 (signed char) → count = 1 - (-4) = 5 (하지만 코드는 1-count)

정확한 공식:
  if (control_byte < 0 && control_byte != 0x80):
    count = 1 - control_byte  // 음수를 양수로 변환
    repeat next_byte count times
```

### 3.3 디코딩 알고리즘 (의사코드)

```python
function decompress_rle(input_stream, output_buffer, output_size):
    """
    RLE 압축 해제

    Args:
        input_stream: 압축된 데이터 스트림
        output_buffer: 출력 버퍼
        output_size: 출력할 바이트 수 (39 bytes for sprite scanline)

    Returns:
        None (output_buffer에 결과 저장)
    """
    output_pos = 0

    while output_pos <= output_size:
        # 제어 바이트 읽기
        control_byte = read_byte(input_stream)

        # Skip marker 처리
        if control_byte == 0x80:
            continue  # 무시하고 다음 바이트

        # Repeat run (음수)
        if control_byte < 0:
            count = 1 - control_byte  # 예: 0xFF → 1, 0x81 → 127
            data_byte = read_byte(input_stream)

            # Repeat
            for i in range(count):
                output_buffer[output_pos] = data_byte
                output_pos += 1
                if output_pos > output_size:
                    break

        # Literal run (양수 또는 0)
        else:
            count = control_byte + 1  # 예: 0x00 → 1, 0x7F → 128

            # Copy literal bytes
            for i in range(count):
                data_byte = read_byte(input_stream)
                output_buffer[output_pos] = data_byte
                output_pos += 1
                if output_pos > output_size:
                    break
```

### 3.4 RLE 처리 파이프라인

```
1. Entry Point (FUN_1000_0771)
   ↓
2. Main Loop (FUN_1000_2840)
   ↓
   반복 200회 (200 스캔라인):
     a. RLE 디코드 Plane 0 (FUN_1000_2865)
     b. RLE 디코드 Plane 1 (FUN_1000_2865)
     c. RLE 디코드 Plane 2 (FUN_1000_2865)
     d. RLE 디코드 Plane 3 (FUN_1000_2865)
     e. 평면 인터리빙 (FUN_1000_2894)
   ↓
3. VRAM 블리팅
```

### 3.5 메모리 레이아웃 (RLE)

```
작업 버퍼 (Work Buffer):
  0x3800: ┌────────┐ Plane 0 (40 bytes)
  0x3828: ├────────┤ Plane 1 (40 bytes)
  0x3850: ├────────┤ Plane 2 (40 bytes)
  0x3878: ├────────┤ Plane 3 (40 bytes)
  0x38A0: └────────┘ Total: 160 bytes

각 평면:
  - 39 bytes 데이터 (RLE 디코딩 결과)
  - 40번째 바이트는 패딩

인터리빙 후:
  [P0 P1 P2 P3] [P0 P1 P2 P3] ... (160 bytes)
```

### 3.6 성능 특성

**압축률**:
```
Best case (solid color):
  40 bytes → 2 bytes (제어 바이트 + 데이터 바이트)
  압축률: 20:1

Worst case (random data):
  40 bytes → 80 bytes (각 바이트마다 제어 바이트 필요)
  압축률: 0.5:1

Average (typical sprite):
  40 bytes → ~13 bytes
  압축률: 3:1
```

**처리 속도** (60 FPS 기준):
```
200 스캔라인 × 4 평면 = 800 RLE 디코딩/프레임
800 디코딩 × 60 FPS = 48,000 디코딩/초

평균 디코딩 시간: ~20 CPU 사이클/디코딩
총 CPU 시간: ~1,000,000 사이클/프레임 (60%)
```

---

## 4. LZW 압축 시스템

### 4.1 개요

**용도**: 에셋 파일 압축 (LINDA.EG1, JIMMY.EG1 등)
**특징**: Unix compress 호환, 딕셔너리 기반
**압축률**: 평균 2.5:1 ~ 4:1

### 4.2 LZW 포맷

```
파일 구조:
  [0x00-0x01]: 매직 넘버 (0x1F 0x9D)
  [0x02-0x03]: 압축 크기 (little-endian)
  [0x04-...]:  압축 데이터 (가변 비트 코드)

코드 의미:
  0-255:   리터럴 바이트
  256:     비트 크기 증가 마커 (클리어 코드 아님!)
  257+:    딕셔너리 인덱스 (code - 257)
```

### 4.3 비트 읽기 (MSB-first)

Double Dragon LZW는 **MSB-first** 방식을 사용:

```
바이트: 0x3F = 0011 1111

읽기 순서:
  Bit 7 (0) → Bit 6 (0) → Bit 5 (1) → ... → Bit 0 (1)

일반적인 LSB-first와 반대!
```

**의사코드**:
```python
function read_bits_msb(bit_stream, num_bits):
    """
    MSB-first 방식으로 비트 읽기

    Args:
        bit_stream: 비트 스트림 상태 (buffer, available_bits, ...)
        num_bits: 읽을 비트 수 (9-13)

    Returns:
        num_bits 크기의 코드
    """
    result = 0

    for i in range(num_bits):
        # 버퍼 리필 필요?
        if bit_stream.bits_available <= 0:
            bit_stream.buffer = read_byte(bit_stream.input)
            bit_stream.bits_available = 8
            bit_stream.remaining_bytes -= 1

        # MSB 추출
        msb = (bit_stream.buffer >> 7) & 1  # 비트 7
        bit_stream.buffer <<= 1              # 왼쪽 시프트

        # 결과에 추가
        result = (result << 1) | msb

        bit_stream.bits_available -= 1

    return result
```

### 4.4 LZW 디코딩 알고리즘 (의사코드)

```python
function decompress_lzw(input_data, output_buffer):
    """
    LZW 압축 해제 (Double Dragon 변형)

    Args:
        input_data: 압축된 데이터 (매직 넘버 포함)
        output_buffer: 출력 버퍼

    Returns:
        output_size: 압축 해제된 데이터 크기
    """
    # 1. 매직 넘버 확인
    if input_data[0] != 0x1F or input_data[1] != 0x9D:
        return error("Not a valid LZW file")

    # 2. 초기화
    bit_stream = {
        'input': input_data[4:],  # Skip magic + size
        'bits_to_read': 9,        # 초기 코드 크기
        'bits_available': 0,
        'buffer': 0,
        'remaining_bytes': read_uint16_le(input_data[2:4]) + 1
    }

    dictionary = []  # [(start_ptr, end_ptr), ...]
    output_pos = 0
    prev_code = None

    # 3. 메인 루프
    while bit_stream.remaining_bytes > 0:
        # 코드 읽기
        code = read_bits_msb(bit_stream, bit_stream.bits_to_read)

        # 코드 256: 비트 크기 증가
        if code == 256:
            bit_stream.bits_to_read += 1
            if bit_stream.bits_to_read > 13:
                bit_stream.bits_to_read = 13  # 최대 13비트
            continue

        # 딕셔너리 엔트리 저장 (이전 시퀀스 끝 위치)
        if prev_code is not None:
            dict_entry = (prev_start, output_pos)
            dictionary.append(dict_entry)

        # 코드 디코딩
        prev_start = output_pos
        if code < 256:
            # 리터럴 바이트
            output_buffer[output_pos] = code
            output_pos += 1

        else:
            # 딕셔너리 참조 (code >= 257)
            dict_index = code - 257
            if dict_index < len(dictionary):
                start, end = dictionary[dict_index]
                length = end - start

                # 시퀀스 복사
                for i in range(length):
                    output_buffer[output_pos] = output_buffer[start + i]
                    output_pos += 1
            else:
                # 딕셔너리에 없음 (에러)
                return error(f"Invalid code: {code}")

        prev_code = code

    return output_pos  # 출력 크기
```

### 4.5 LZW 처리 파이프라인

```
1. 매직 넘버 체크 (FUN_1000_5fe0)
   ↓
   [0x1F 0x9D] 확인
   ↓
2. 초기화 (FUN_1000_604e)
   ↓
   bits_to_read = 9
   bits_available = 0
   딕셔너리 = []
   ↓
3. 메인 디코더 (FUN_1000_5ff3)
   ↓
   반복:
     a. 비트 읽기 (FUN_1000_6091)
     b. 코드 == 256? → 비트 크기 증가
     c. 코드 디코드 (FUN_1000_605b)
     d. 딕셔너리 업데이트
   ↓
4. 출력 완료
```

### 4.6 딕셔너리 구조

```
메모리 레이아웃:
  Base Pointer (BP) + (code - 257) * 4:
    [0]: start_ptr (2 bytes)  # 시퀀스 시작 포인터
    [2]: end_ptr   (2 bytes)  # 시퀀스 끝 포인터

예시:
  code 257 → dictionary[0] → BP + 0
    [0x0000]: 0x1000  (start)
    [0x0002]: 0x1003  (end)
    → 3 bytes at 0x1000-0x1002

  code 258 → dictionary[1] → BP + 4
    [0x0004]: 0x1003  (start)
    [0x0006]: 0x1007  (end)
    → 4 bytes at 0x1003-0x1006

최대 딕셔너리 크기:
  13비트 코드 → 8192 엔트리
  8192 × 4 bytes = 32 KB (딕셔너리 테이블)
```

### 4.7 코드 256의 특별한 처리

**표준 LZW**:
- 코드 256 = 클리어 코드 (딕셔너리 리셋)

**Double Dragon LZW**:
- 코드 256 = 비트 크기 증가 마커
- 딕셔너리 리셋 **안 함**
- 단순히 `bits_to_read++`만 수행

**비트 크기 증가 패턴**:
```
초기:     9비트 (코드 0-511)
코드 256: 10비트 (코드 0-1023)
코드 256: 11비트 (코드 0-2047)
코드 256: 12비트 (코드 0-4095)
코드 256: 13비트 (코드 0-8191)
최대:     13비트 (고정)
```

### 4.8 성능 특성

**압축률**:
```
LINDA.EG1:
  압축 전: 12,453 bytes
  압축 후: 4,872 bytes
  압축률: 2.56:1

JIMMY.EG1:
  압축 전: 8,921 bytes
  압축 후: 2,234 bytes
  압축률: 3.99:1
```

**디코딩 속도**:
```
평균 디코딩: ~50 CPU 사이클/코드
전체 파일: ~10ms (4.77 MHz 8088 기준)

게임 시작 시 한 번만 실행 → 성능 영향 미미
```

---

## 5. 메모리 레이아웃

### 5.1 RLE 메모리

```
작업 버퍼:
  0x3800: Plane 0 (40 bytes)
  0x3828: Plane 1 (40 bytes)
  0x3850: Plane 2 (40 bytes)
  0x3878: Plane 3 (40 bytes)

반환 값:
  0x1988: 스프라이트 데이터 세그먼트
```

### 5.2 LZW 메모리

```
전역 변수 (데이터 세그먼트):
  0x6534: bits_to_read     (2 bytes, int16)
  0x6536: remaining_bytes  (2 bytes, int16)
  0x6538: bits_available   (2 bytes, int16)
  0x653a: bit_buffer       (1 byte, uint8)

딕셔너리 (동적 할당):
  Base + 0: dictionary[0]  (4 bytes: start, end)
  Base + 4: dictionary[1]  (4 bytes: start, end)
  ...
  Base + N*4: dictionary[N]

최대 크기: 8192 × 4 = 32 KB
```

### 5.3 레지스터 사용

**RLE 디코더**:
```
SI: 입력 포인터 (압축 데이터)
BX: 출력 포인터 (작업 버퍼)
DI: VRAM 포인터
ES: VRAM 세그먼트
DS: 데이터 세그먼트
```

**LZW 디코더**:
```
SI: 입력 포인터 / 딕셔너리 포인터
DI: 출력 포인터
BP: 딕셔너리 베이스
AX: 코드 (파라미터)
ES: 출력 세그먼트
DS: 데이터 세그먼트
```

---

## 6. 함수 목록

### 6.1 RLE 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:0771 | Entry Point | 스프라이트 블리팅 진입점 | Low |
| 1000:2840 | Main Loop | 200 스캔라인 디코딩 루프 | Low |
| 1000:2865 | RLE Decompressor | RLE 압축 해제 (1 평면) | Medium |
| 1000:2894 | Planar Copy | 4 평면 → 인터리빙 | Low |

**호출 관계**:
```
FUN_1000_0771 (Entry)
    ↓
FUN_1000_2840 (Loop)
    ├─→ FUN_1000_2865 (Decompress) ×4
    └─→ FUN_1000_2894 (Interleave)
```

### 6.2 LZW 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:5fe0 | Magic Check | 매직 넘버 확인 | Low |
| 1000:5ff3 | Main Decoder | LZW 디코더 메인 루프 | High |
| 1000:604e | Initialize | 상태 초기화 | Low |
| 1000:6091 | Read Bits | MSB-first 비트 읽기 | Medium |
| 1000:605b | Decode Code | 코드 → 데이터 변환 | Medium |
| 1000:5fec | LZW Wrapper 1 | 표준 LZW 래퍼 | Low |
| 1000:6009 | LZW Wrapper 2 | 대체 LZW 래퍼 | Low |
| 1000:6011 | LZW Wrapper 3 | 대체 LZW 래퍼 | Low |

**호출 관계**:
```
FUN_1000_5fe0 (Magic Check)
    ↓
FUN_1000_5ff3 (Main Decoder)
    ├─→ FUN_1000_604e (Init)
    ├─→ FUN_1000_6091 (Read Bits) [반복]
    └─→ FUN_1000_605b (Decode) [반복]
```

---

## 7. 구현 가이드

### 7.1 RLE 구현 단계

**Step 1: 기본 구조**
```
1. 제어 바이트 파싱 함수
2. Repeat run 처리
3. Literal run 처리
4. Skip marker 처리
```

**Step 2: 최적화**
```
1. 버퍼 오버런 체크 (output_pos <= size)
2. 입력 끝 감지
3. 32비트 워드 복사 (2배 속도)
```

**Step 3: 통합**
```
1. 4 평면 디코딩 루프
2. 평면 인터리빙
3. VRAM 블리팅 연결
```

### 7.2 LZW 구현 단계

**Step 1: 비트 읽기**
```
1. MSB-first 비트 스트림 구현
2. 가변 비트 읽기 (9-13비트)
3. 버퍼 리필 로직
```

**Step 2: 딕셔너리**
```
1. 딕셔너리 구조체 정의
2. 엔트리 추가 함수
3. 엔트리 조회 함수
```

**Step 3: 디코더**
```
1. 매직 넘버 확인
2. 초기화
3. 메인 루프
   a. 코드 읽기
   b. 코드 256 처리
   c. 리터럴/딕셔너리 디코딩
   d. 딕셔너리 업데이트
```

### 7.3 함정 (Pitfalls)

**RLE 함정**:
```
❌ 나쁜 예:
  if (control_byte < 0):
    count = -control_byte  # 틀림!

✅ 좋은 예:
  if (control_byte < 0):
    count = 1 - control_byte  # 올바름
```

**LZW 함정**:
```
❌ 나쁜 예:
  # LSB-first 방식 (표준)
  bit = (buffer & 1)
  buffer >>= 1

✅ 좋은 예:
  # MSB-first 방식 (Double Dragon)
  bit = (buffer >> 7) & 1
  buffer <<= 1
```

---

## 8. 테스트 전략

### 8.1 RLE 테스트 케이스

**기본 케이스**:
```
입력:  [0xFF, 0xAA, 0x00, 0xBB]
의미:  Repeat 0xAA 1회, Literal 0xBB 1회
출력:  [0xAA, 0xBB]
```

**엣지 케이스**:
```
# 최대 반복
입력:  [0x81, 0xFF]
의미:  Repeat 0xFF 127회
출력:  [0xFF] × 127

# Skip marker
입력:  [0x80, 0xFF, 0xAA]
의미:  Skip, Repeat 0xAA 1회
출력:  [0xAA]

# 긴 리터럴
입력:  [0x7F, <128 bytes>]
의미:  Literal 128 bytes
출력:  <128 bytes>
```

**실제 데이터**:
```
# Double Dragon sprite scanline
압축:   13 bytes
해제:   40 bytes
압축률: 3.08:1

테스트: 4 평면 디코딩 → 인터리빙 → 원본 비교
```

### 8.2 LZW 테스트 케이스

**기본 케이스**:
```
입력:  [0x1F, 0x9D, 0x05, 0x00, <compressed>]
       └─┬─┘ └─────┬─────┘
         │        └─ 크기: 5 bytes
         └────────── 매직 넘버

출력:  검증된 압축 해제 데이터
```

**엣지 케이스**:
```
# 매직 넘버 없음
입력:  [0x00, 0x00, ...]
출력:  Error (invalid magic)

# 코드 256 (비트 증가)
입력:  <9-bit codes>, 256, <10-bit codes>
출력:  올바른 디코딩

# 딕셔너리 최대 크기
입력:  <13-bit codes> × 8192
출력:  메모리 오버플로우 없음
```

**실제 데이터**:
```
# LINDA.EG1
압축:   4,872 bytes
해제:   12,453 bytes
매직:   0x1F 0x9D

테스트: 전체 디코딩 → CRC 검증
```

---

## 9. 참고

### 9.1 관련 알고리즘

- [`../algorithms/RLE_COMPRESSION.md`](../algorithms/RLE_COMPRESSION.md) - RLE 의사코드
- [`../algorithms/LZW_COMPRESSION.md`](../algorithms/LZW_COMPRESSION.md) - LZW 의사코드

### 9.2 관련 시스템

- [`01_RENDERING.md`](01_RENDERING.md) - RLE 디코딩 후 블리팅
- [`06_STAGE_LIFECYCLE.md`](06_STAGE_LIFECYCLE.md) - LZW 에셋 로딩

### 9.3 원본 분석

- [`../archive/phase4-analysis/FINAL_SYSTEMS_ANALYSIS.md`](../archive/phase4-analysis/FINAL_SYSTEMS_ANALYSIS.md) - RLE 상세 분석
- [`../technical/LZW_COMPRESSION.md`](../technical/LZW_COMPRESSION.md) - LZW 완전 분석

### 9.4 외부 참조

- [Run-Length Encoding (Wikipedia)](https://en.wikipedia.org/wiki/Run-length_encoding)
- [LZW Compression (Wikipedia)](https://en.wikipedia.org/wiki/Lempel–Ziv–Welch)
- [Unix compress Format](https://en.wikipedia.org/wiki/Compress)

---

**작성일**: 2025-01-24
**버전**: 1.0
**언어 중립성**: 의사코드 기반, 모든 언어로 구현 가능

**다음 문서**: [08_HARDWARE_IO.md](08_HARDWARE_IO.md) - 하드웨어 I/O 시스템
**관련 문서**: [README.md](README.md) - 시스템 개요
