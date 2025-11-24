# Data Loading & Graphics Initialization Analysis

**분석 일자**: 2025-11-24
**대상**: Double Dragon DOS (1988)
**Phase**: 4.8 - Data Systems Analysis

---

## 목차

1. [개요](#개요)
2. [데이터 로딩 시스템](#데이터-로딩-시스템)
3. [LZW 압축 해제](#lzw-압축-해제)
4. [CGA 비트 플레인 인터리빙](#cga-비트-플레인-인터리빙)
5. [팔레트 및 색상 테이블 생성](#팔레트-및-색상-테이블-생성)
6. [그래픽 모드 초기화](#그래픽-모드-초기화)
7. [PIT 타이머 초기화](#pit-타이머-초기화)
8. [5번째 Jump Table 발견](#5번째-jump-table-발견)
9. [초기화 시퀀스](#초기화-시퀀스)
10. [메모리 맵 업데이트](#메모리-맵-업데이트)

---

## 개요

이 문서는 Double Dragon의 **데이터 로딩**, **압축 해제**, **그래픽 초기화** 시스템을 분석합니다. 특히 **LZW 압축**, **CGA 비트 플레인 변환**, **동적 팔레트 생성**, 그리고 **5번째 jump table**을 발견했습니다.

### 분석 대상 함수 (14개)

| 주소 | 함수명 | 크기 | 역할 |
|------|--------|------|------|
| 1e8a | FUN_1000_1e8a | 45B | 메인 데이터 로더 |
| 1df2 | FUN_1000_1df2 | 24B | 데이터 로드 래퍼 |
| 5fe0 | FUN_1000_5fe0 | 19B | 압축 매직 넘버 체크 |
| 5ff3 | FUN_1000_5ff3 | 91B | LZW 압축 해제 |
| 0cd1 | FUN_1000_0cd1 | 147B | CGA 비트 플레인 인터리빙 |
| 0d64 | FUN_1000_0d64 | 42B | 팔레트 테이블 생성 |
| 0b94 | FUN_1000_0b94 | 317B | 그래픽 초기화 A |
| 093a | FUN_1000_093a | 151B | 그래픽 초기화 B |
| 0660 | FUN_1000_0660 | 58B | 초기화 시퀀스 1 |
| 069a | FUN_1000_069a | 58B | 초기화 시퀀스 2 |
| 1c1e | FUN_1000_1c1e | 16B | PIT 타이머 초기화 (사운드) |
| 1c0c | FUN_1000_1c0c | 18B | PIT 타이머 초기화 (게임) |
| 810b | FUN_1000_810b | 4B | 5번째 Jump Table 디스패처! |
| 0e1d | FUN_1000_0e1d | 7B | Word memcpy |

---

## 데이터 로딩 시스템

### FUN_1000_1e8a: 메인 데이터 로더 (45 bytes)

**역할**: 파일 시스템에서 데이터를 읽어오는 메인 함수입니다.

```c
void __cdecl16near FUN_1000_1e8a(void) {
    undefined2 uVar1;
    undefined2 uVar2;
    undefined2 unaff_DS;

    FUN_1000_1c1e();  // PIT 초기화 (사운드 비활성화)

    // Save current source address
    uVar1 = *(undefined2 *)0x320d;  // Source segment
    uVar2 = *(undefined2 *)0x320f;  // Source offset

    // Set temporary source
    *(undefined2 *)0x320f = 0;
    *(undefined2 *)0x320d = 0x2949;  // Temporary buffer?

    FUN_1000_1df2(uVar2, uVar1);  // Load data
    FUN_1000_5fe0();               // Check if compressed & decompress
    FUN_1000_1c0c();               // PIT 초기화 (게임 타이머)

    return;
}
```

**파라미터** (글로벌 변수):
```
0x320d: Source segment  (DS or file segment)
0x320f: Source offset   (file offset)
0x3213: Destination     (target buffer)
```

**동작 흐름**:
1. PIT 타이머 초기화 (사운드 비활성화)
2. 소스 주소 백업
3. 임시 버퍼(0x2949)로 데이터 복사
4. 압축 여부 확인 및 압축 해제
5. PIT 타이머 재초기화 (게임 타이머 활성화)

### FUN_1000_1df2: 데이터 로드 래퍼 (24 bytes)

**역할**: 인터럽트 벡터를 임시로 변경하고 데이터를 로드합니다.

```c
void __cdecl16near FUN_1000_1df2(void) {
    undefined2 uVar1;
    undefined2 unaff_DS;

    // Save interrupt vector 0
    uVar1 = *(undefined2 *)0x0;  // IVT[0] = Divide by Zero handler
    *(undefined2 *)0x0 = 0xffff;  // Disable interrupt

    // Load data sequence
    FUN_1000_1e26();  // Read file metadata
    FUN_1000_1e60();  // Read file data
    FUN_1000_1e7f();  // Post-processing

    // Restore interrupt vector
    *(undefined2 *)0x0 = uVar1;

    return;
}
```

**주의**:
- IVT (Interrupt Vector Table) 조작
- `0x0000:0x0000`은 Divide by Zero 인터럽트 (INT 0)
- 임시로 비활성화하여 데이터 로딩 중 인터럽트 방지

---

## LZW 압축 해제

### FUN_1000_5fe0: 압축 매직 넘버 체크 (19 bytes)

**역할**: 데이터가 LZW 압축되어 있는지 확인합니다.

```c
void __cdecl16near FUN_1000_5fe0(void) {
    int *unaff_SI;
    undefined2 unaff_DS;

    // Check magic number
    if (*unaff_SI != -0x62e1) {  // 0x9d1f (little-endian)
        return;  // Not compressed
    }

    // Decompress
    FUN_1000_5ff3();
    return;
}
```

**매직 넘버**:
```
0x9d1f = -0x62e1 (signed 16-bit)
"LZ" signature in some encoding?
```

### FUN_1000_5ff3: LZW 압축 해제 (91 bytes)

**역할**: LZW 알고리즘을 사용하여 압축된 데이터를 해제합니다.

```c
void __cdecl16near FUN_1000_5ff3(void) {
    int iVar1;
    undefined2 *unaff_SI;  // Source pointer
    undefined2 unaff_DI;   // Destination
    undefined2 unaff_DS;

    // Initialize decompression
    *(int *)0x6536 = unaff_SI[1] + 1;  // Compressed size + 1
    FUN_1000_604e();  // Initialize LZW dictionary

    while(true) {
        // Write output
        *unaff_SI = unaff_DI;
        unaff_SI = unaff_SI + 1;

        // Read next code
        while (iVar1 = FUN_1000_6091(), iVar1 == 0x100) {
            *(int *)0x6534 = *(int *)0x6534 + 1;  // Skip padding
        }

        if (*(int *)0x6536 == 0) {  // Check remaining size
            return;  // Decompression complete
        }

        FUN_1000_605b();  // Decode LZW code

        // Read next code again
        while (iVar1 = FUN_1000_6091(), iVar1 == 0x100) {
            *(int *)0x6534 = *(int *)0x6534 + 1;
        }

        if (*(int *)0x6536 == 0) break;

        FUN_1000_605b();  // Decode second code
    }
    return;
}
```

**LZW 알고리즘**:
- **Dictionary**: Dynamic code table (초기 256 entries, 확장 가능)
- **Code size**: Variable (likely 9-12 bits)
- **End marker**: 0x100 (padding or end-of-stream)
- **Max code**: 4096? (standard LZW)

**메모리**:
```
0x6534: Input bit position / padding skip counter
0x6536: Remaining compressed size
0x6091: Returns next LZW code
0x605b: Decodes LZW code to output
0x604e: Initializes LZW dictionary
```

**이전 분석 연결**:
- Phase 3에서 `dd_lzw_decompress` C 구현 완성
- 실제 게임 코드와 일치함을 확인
- 압축률: ~50-60% (36개 파일 분석 결과)

---

## CGA 비트 플레인 인터리빙

### FUN_1000_0cd1: CGA 비트 플레인 변환 (147 bytes) ★★★

**역할**: 선형 픽셀 데이터를 CGA 4-plane interlaced 형식으로 변환합니다.

```c
void __cdecl16near FUN_1000_0cd1(void) {
    int *piVar1;
    int iVar2;
    int iVar3;
    int in_CX;      // Loop counter (number of words to process)
    char cVar4, cVar5, cVar6, cVar7;
    int *unaff_DI;  // Destination pointer
    undefined2 unaff_ES;

    do {
        // Read 2 words (32 pixels = 4 bytes)
        iVar2 = unaff_DI[1];
        iVar3 = *unaff_DI;

        // Extract individual bytes
        cVar4 = (char)iVar3;           // Byte 0
        cVar5 = (char)((uint)iVar3 >> 8);  // Byte 1
        cVar6 = (char)iVar2;           // Byte 2
        cVar7 = (char)((uint)iVar2 >> 8);  // Byte 3

        // Bit interleaving for first output word
        // Extract bits 0-1 from each byte, pack into plane format
        iVar2 = (((((((((((((((uint)(cVar4 < '\0') << 1 | (uint)(iVar3 < 0)) << 1 |
                              (uint)(cVar6 < '\0')) << 1 | (uint)(iVar2 < 0)) << 1 |
                            (uint)((char)(cVar4 << 1) < '\0')) << 1 |
                           (uint)((char)(cVar5 << 1) < '\0')) << 1 |
                          (uint)((char)(cVar6 << 1) < '\0')) << 1 |
                         (uint)((char)(cVar7 << 1) < '\0')) << 1 |
                        (uint)((char)(cVar4 << 2) < '\0')) << 1 |
                       (uint)((char)(cVar5 << 2) < '\0')) << 1 |
                      (uint)((char)(cVar6 << 2) < '\0')) << 1 |
                     (uint)((char)(cVar7 << 2) < '\0')) << 1 |
                    (uint)((char)(cVar4 << 3) < '\0')) << 1 |
                   (uint)((char)(cVar5 << 3) < '\0')) << 1 |
                  (uint)((char)(cVar6 << 3) < '\0')) << 1;

        piVar1 = unaff_DI + 1;
        *unaff_DI = CONCAT11((byte)iVar2 | (char)(cVar7 << 3) < '\0',
                             (char)((uint)iVar2 >> 8));

        // Bit interleaving for second output word
        // Extract bits 4-7 from each byte, pack into plane format
        iVar2 = (((((((((((((((uint)((char)(cVar4 << 4) < '\0') << 1 |
                               (uint)((char)(cVar5 << 4) < '\0')) << 1 |
                              (uint)((char)(cVar6 << 4) < '\0')) << 1 |
                             (uint)((char)(cVar7 << 4) < '\0')) << 1 |
                            (uint)((char)(cVar4 << 5) < '\0')) << 1 |
                           (uint)((char)(cVar5 << 5) < '\0')) << 1 |
                          (uint)((char)(cVar6 << 5) < '\0')) << 1 |
                         (uint)((char)(cVar7 << 5) < '\0')) << 1 |
                        (uint)((char)(cVar4 << 6) < '\0')) << 1 |
                       (uint)((char)(cVar5 << 6) < '\0')) << 1 |
                      (uint)((char)(cVar6 << 6) < '\0')) << 1 |
                     (uint)((char)(cVar7 << 6) < '\0')) << 1 |
                    (uint)((char)(cVar4 << 7) < '\0')) << 1 |
                   (uint)((int)((uint)(byte)(cVar5 << 7) << 8) < 0)) << 1 |
                  (uint)((char)(cVar6 << 7) < '\0')) << 1;

        unaff_DI = unaff_DI + 2;
        *piVar1 = CONCAT11((byte)iVar2 | (int)((uint)(byte)(cVar7 << 7) << 8) < 0,
                           (char)((uint)iVar2 >> 8));

        in_CX = in_CX + -1;
    } while (in_CX != 0);
    return;
}
```

**알고리즘 설명**:

입력: 4 bytes (32 pixels, 2bpp chunky)
```
Byte 0: AABBCCDD EEFFGGHH (8 pixels)
Byte 1: IIJJKKLL MMNNOOPP (8 pixels)
Byte 2: QQRRSSTТ UUVVWWXX (8 pixels)
Byte 3: YYZZaabb ccddeeff (8 pixels)
```

출력: 4 bytes (32 pixels, CGA planar)
```
Word 0 (bits 0-1):
  Byte 0: AEIMQUXX AEIMQUXX (plane 0, bit 0)
  Byte 1: BFJNRVXX BFJNRVXX (plane 0, bit 1)

Word 1 (bits 4-7):
  Byte 0: CGKOSW.. CGKOSW.. (plane 1, bit 0)
  Byte 1: DHLPTX.. DHLPTX.. (plane 1, bit 1)
```

**변환 과정**:
1. 4 bytes (32 pixels)을 2 words로 읽기
2. 각 byte에서 bit를 추출 (shift + test MSB)
3. 비트를 plane 순서로 재배열
4. 2 words로 출력 (plane interleaved)

**CGA 플레인 구조**:
```
320×200, 4 colors (2bpp)
Plane layout:
  Plane 0: Even scanlines (0, 2, 4, ...)
  Plane 1: Odd scanlines  (1, 3, 5, ...)
Each plane: 8KB (16KB total)

Bit interleaving within plane:
  Bit 0: Color bit 0
  Bit 1: Color bit 1
  → 4 possible colors per pixel (00, 01, 10, 11)
```

**Phase 3 연결**:
- `cga_planar_to_chunky.c` (역변환) 구현 완료
- 스프라이트 추출에 사용
- LINDA.EG1 → PNG 변환 성공

---

## 팔레트 및 색상 테이블 생성

### FUN_1000_0d64: 팔레트 테이블 생성 (42 bytes)

**역할**: CGA 색상 조합 테이블을 동적으로 생성합니다.

```c
void __cdecl16near FUN_1000_0d64(void) {
    byte *pbVar1;
    int iVar2;
    uint uVar3;
    int in_BX;      // Base palette address
    byte *unaff_DI; // Destination table
    undefined2 unaff_ES;

    uVar3 = 0;
    iVar2 = 0x100;  // 256 entries
    do {
        pbVar1 = unaff_DI;
        unaff_DI = unaff_DI + 1;

        // Generate palette entry
        *pbVar1 = *(char *)(ulong)(in_BX + (uVar3 >> 4 & 0xf)) << 4 |
                  *(byte *)(ulong)(in_BX + (uVar3 & 0xf));
        //        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        //        high_nibble = palette[high_4bits]
        //        low_nibble  = palette[low_4bits]

        uVar3 = uVar3 + 1;
        iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
    return;
}
```

**알고리즘**:
```
For i = 0 to 255:
    high = palette[i >> 4]  # High nibble (4 bits)
    low  = palette[i & 0xF] # Low nibble (4 bits)
    table[i] = (high << 4) | low

Result: 256-entry color combination table
```

**사용 예시**:
```c
// CGA palette (4 colors)
byte palette[16] = {0, 1, 2, 3, ...};  // In BX register

// Generate 256-entry table
FUN_1000_0d64();

// Result: All 16×16 = 256 color combinations
table[0x00] = palette[0] << 4 | palette[0]  // 0x00
table[0x01] = palette[0] << 4 | palette[1]  // 0x01
table[0x12] = palette[1] << 4 | palette[2]  // 0x12
...
table[0xFF] = palette[15] << 4 | palette[15] // 0xFF
```

### FUN_1000_0b94에서의 팔레트 초기화

```c
// Generate inverted mask table @ 0x8800
pbVar6 = (byte *)0x8800;
uVar5 = 0;
iVar4 = 0x100;
do {
    bVar3 = 0;
    if ((uVar5 & 0xf) != 0) {    // Low nibble set?
        bVar3 = 0xf;              // Set low nibble mask
    }
    if ((uVar5 & 0xf0) != 0) {   // High nibble set?
        bVar3 = bVar3 | 0xf0;     // Set high nibble mask
    }
    pbVar1 = pbVar6;
    pbVar6 = pbVar6 + 1;
    *pbVar1 = ~bVar3;  // Inverted mask for masking operations
    uVar5 = uVar5 + 1;
    iVar4 = iVar4 + -1;
} while (iVar4 != 0);
```

**결과**:
```
table[0x00] = ~0x00 = 0xFF  (both nibbles clear)
table[0x01] = ~0x0F = 0xF0  (low nibble set)
table[0x10] = ~0xF0 = 0x0F  (high nibble set)
table[0x11] = ~0xFF = 0x00  (both nibbles set)
...
```

**용도**: 픽셀 마스킹 및 블렌딩 연산에 사용

---

## 그래픽 모드 초기화

### FUN_1000_0b94: 그래픽 초기화 시퀀스 A (317 bytes)

**역할**: Mode 1용 그래픽 데이터 로딩 및 초기화.

```c
void __cdecl16near FUN_1000_0b94(void) {
    // Load sprite data 1
    DAT_1988_320d = 0x2f9e;  // Source segment
    DAT_1988_320f = 0;       // Source offset
    DAT_1988_3213 = 0x1790;  // Destination
    FUN_1000_1e8a();         // Load & decompress

    // Load sprite data 2
    DAT_1988_320d = 0x3f9e;
    DAT_1988_320f = 0;
    DAT_1988_3213 = 0x179c;
    FUN_1000_1e8a();

    // Load sprite data 3
    DAT_1988_320d = 0x493a;
    DAT_1988_320f = 0;
    DAT_1988_3213 = 0x17a8;
    FUN_1000_1e8a();

    FUN_1000_063e();  // DOS interrupt (file operation?)

    // Load sprite data 4
    DAT_1988_320d = 0x53a0;
    DAT_1988_320f = 0;
    DAT_1988_3213 = 0x1786;
    FUN_1000_1e8a();

    // CGA bit plane conversion (4 times)
    FUN_1000_0cd1(0x1988, 0x1988);
    FUN_1000_0cd1();
    FUN_1000_0cd1();
    FUN_1000_0cd1();

    // Generate inverted mask table @ 0x8800 (256 bytes)
    [mask generation code - see above]

    // Generate palette tables (7 times)
    FUN_1000_0d64();  // 7 calls
    FUN_1000_0d64();
    FUN_1000_0d64();
    FUN_1000_0d64();
    FUN_1000_0d64();
    FUN_1000_0d64();
    FUN_1000_0d64();

    // Initialize sprite pointer table @ 0xf4f0
    DAT_1988_f4f0 = 0x8100;
    DAT_1988_f4f2 = 0x8100;
    DAT_1988_f4f4 = 0x8100;
    DAT_1988_f4f6 = 0x8100;
    DAT_1988_f4f8 = 0x8100;
    DAT_1988_f4fa = 0x8200;
    DAT_1988_f4fc = 0x8700;
    DAT_1988_f4fe = 0x8700;
    DAT_1988_f500 = 0x8700;
    DAT_1988_f502 = 0x8400;
    DAT_1988_f504 = 0x8500;
    DAT_1988_f506 = 0x8300;

    return;
}
```

**초기화 순서**:
1. 4개 스프라이트 데이터 로딩 (segments: 0x2f9e, 0x3f9e, 0x493a, 0x53a0)
2. CGA 비트 플레인 변환 (4회)
3. 마스크 테이블 생성 (256 bytes @ 0x8800)
4. 팔레트 테이블 생성 (7개 테이블)
5. 스프라이트 포인터 테이블 초기화 (12 entries @ 0xf4f0)

### FUN_1000_093a: 그래픽 초기화 시퀀스 B (151 bytes)

**역할**: Mode 2용 그래픽 데이터 로딩 및 초기화.

```c
void __cdecl16near FUN_1000_093a(void) {
    // Same data loading sequence as FUN_0b94
    [4 sprite data loads - identical]

    // Different sprite pointer table
    DAT_1988_f4f0 = 0x6162;  // Different from Mode 1!
    DAT_1988_f4f2 = 0x6162;
    DAT_1988_f4f4 = 0x6162;
    DAT_1988_f4f6 = 0x6162;
    DAT_1988_f4f8 = 0x6162;
    DAT_1988_f4fa = 0x6324;
    DAT_1988_f4fc = 0x64fd;
    DAT_1988_f4fe = 0x66fa;
    DAT_1988_f500 = 0x66fa;
    DAT_1988_f502 = 0x66fa;
    DAT_1988_f504 = 0x68df;
    DAT_1988_f506 = 0x64fd;

    return;
}
```

**차이점**:
- 데이터 로딩은 동일
- **스프라이트 포인터 테이블만 다름** (0xf4f0-f506)
- Mode 1과 Mode 2는 다른 스프라이트 세트 사용

### FUN_1000_0660 & 069a: 통합 초기화 래퍼

```c
// FUN_1000_0660: Initialization sequence 1
void __cdecl16near FUN_1000_0660(void) {
    *(undefined2 *)0x320d = 0x1988;
    *(undefined2 *)0x320f = 0x13da;
    *(undefined2 *)0x3213 = 0x17b4;
    FUN_1000_1e8a();   // Load common data
    FUN_1000_0b94();   // Graphics init A (Mode 1)
    FUN_1000_0db2();   // Rendering table switch
    DAT_1988_0042 = 9; // Set mode parameter
    FUN_1000_0dd6();   // Finalize (3× FUN_0e1d)
    return;
}

// FUN_1000_069a: Initialization sequence 2
void __cdecl16near FUN_1000_069a(void) {
    *(undefined2 *)0x320d = 0x1988;
    *(undefined2 *)0x320f = 0x13da;
    *(undefined2 *)0x3213 = 0x17b4;
    FUN_1000_1e8a();   // Load common data (same)
    FUN_1000_093a();   // Graphics init B (Mode 2)
    FUN_1000_0db2();   // Rendering table switch
    DAT_1988_0042 = 0xd;  // Different mode parameter
    FUN_1000_0dd6();   // Finalize (3× FUN_0e1d)
    return;
}
```

**차이점**: `DAT_1988_0042` 값만 다름 (9 vs 13)

---

## PIT 타이머 초기화

### FUN_1000_1c1e: PIT 초기화 (사운드 비활성화) (16 bytes)

**역할**: PC Speaker 사운드를 중지합니다.

```c
undefined1 __cdecl16near FUN_1000_1c1e(void) {
    undefined2 unaff_DS;

    *(undefined1 *)0x318c = 1;  // Sound disable flag

    // PIT Channel 0, Mode 3 (Square Wave)
    out(0x43, 0x36);  // Command: Channel 0, LSB+MSB, Mode 3
    out(0x40, 0);     // LSB = 0
    out(0x40, 0);     // MSB = 0
    // Frequency = 1193180 / 0 = undefined (no sound)

    return 0;
}
```

**PIT (Programmable Interval Timer) 8253**:
```
Port 0x43: Command register
  0x36 = 00110110b
    Bits 7-6: 00 = Channel 0
    Bits 5-4: 11 = Access mode LSB+MSB
    Bits 3-1: 011 = Mode 3 (Square Wave Generator)
    Bit 0:    0 = Binary counter

Port 0x40: Channel 0 data
  Divisor = 0x0000 → No output (silence)
```

### FUN_1000_1c0c: PIT 초기화 (게임 타이머) (18 bytes)

**역할**: 게임 타이머를 ~18.2 Hz로 설정합니다.

```c
undefined1 __cdecl16near FUN_1000_1c0c(void) {
    undefined2 unaff_DS;

    *(undefined1 *)0x318c = 0;  // Sound enable flag

    // PIT Channel 0, Mode 3 (Square Wave)
    out(0x43, 0x36);     // Command: Channel 0, LSB+MSB, Mode 3
    out(0x40, 0);        // LSB = 0
    out(0x40, 0x10);     // MSB = 0x10
    // Frequency = 1193180 / 0x1000 = 291.5 Hz
    // Timer tick = ~3.43 ms (291.5 Hz)

    return 0x10;
}
```

**타이머 주파수**:
```
Base frequency: 1.193180 MHz
Divisor: 0x1000 (4096)
Output frequency: 1193180 / 4096 = 291.5 Hz
Period: 3.43 ms

DOS default: 0xFFFF (65535) → 18.2 Hz (54.9 ms)
Game timer: 0x1000 (4096)  → 291.5 Hz (3.43 ms)
  → 16× faster than DOS default
```

**용도**: 고해상도 게임 타이밍 (60 FPS를 위한 정밀 타이머)

---

## 5번째 Jump Table 발견

### FUN_1000_810b: Jump Table 디스패처 @ 0x18d2 (4 bytes) ★★★

**역할**: 5번째 jump table을 발견했습니다!

```c
void FUN_1000_810b(void) {
    undefined2 unaff_DS;

    // WARNING: Could not recover jumptable at 0x0001810b. Too many branches
    // WARNING: Treating indirect jump as call
    (*(code *)*(undefined2 *)0x18d2)();
    //         ^^^^^^^^^^^^^^^^^^^^^
    //         Jump to function pointer @ 0x18d2
    return;
}
```

**디스어셈블리**:
```asm
jmp  word [0x18d2]  ; Indirect jump to function pointer
```

**Jump Table 위치**:
```
Address: 0x18d2
Type: Single function pointer (not array)
Purpose: Unknown (likely rendering or update hook)
```

**발견된 Jump Table 5종**:
| Jump Table | 주소 | 디스패처 | 용도 | 타입 |
|-----------|------|----------|------|------|
| AI Table | 0x16ef | FUN_1000_16e0 | Entity AI state machine | 배열 (256 entries) |
| Collision Table | 0xe3f | FUN_1000_0e30 | Collision type handlers | 배열 (256 entries) |
| Rendering Table | 0x18c4 | FUN_1000_499b | Rendering modes | 배열 (30 entries) |
| Physics Table | 0x2264 | FUN_1000_2255 | Projectile physics | 배열 (256 entries) |
| **Hook Table** | **0x18d2** | **FUN_1000_810b** | **Update/Render hook** | **단일 포인터** |

**사용 위치**:
- `FUN_1000_3830` (main loop)에서 호출됨
- 매 프레임 실행되는 것으로 추정

---

## 초기화 시퀀스

### 전체 초기화 흐름

```
Game Start
    │
    ├─> FUN_1000_0660() or FUN_1000_069a()  [Choose mode]
    │   │
    │   ├─> Load common data
    │   │   ├─> Set source (0x1988:0x13da)
    │   │   ├─> Set dest (0x17b4)
    │   │   └─> FUN_1000_1e8a()
    │   │       ├─> FUN_1000_1c1e()  [PIT: Disable sound]
    │   │       ├─> FUN_1000_1df2()  [Load data]
    │   │       │   ├─> Disable INT 0
    │   │       │   ├─> FUN_1000_1e26()  [Read metadata]
    │   │       │   ├─> FUN_1000_1e60()  [Read data]
    │   │       │   ├─> FUN_1000_1e7f()  [Post-process]
    │   │       │   └─> Restore INT 0
    │   │       ├─> FUN_1000_5fe0()  [Check & decompress]
    │   │       │   ├─> Check magic (0x9d1f)
    │   │       │   └─> FUN_1000_5ff3()  [LZW decompress]
    │   │       └─> FUN_1000_1c0c()  [PIT: Enable timer]
    │   │
    │   ├─> FUN_1000_0b94() or FUN_1000_093a()  [Graphics init]
    │   │   ├─> Load 4 sprite datasets
    │   │   ├─> FUN_1000_0cd1() × 4  [CGA plane convert]
    │   │   ├─> Generate mask table (0x8800)
    │   │   ├─> FUN_1000_0d64() × 7  [Palette tables]
    │   │   └─> Initialize sprite pointers (0xf4f0)
    │   │
    │   ├─> FUN_1000_0db2()  [Rendering table switch]
    │   ├─> Set mode (0x0042 = 9 or 13)
    │   └─> FUN_1000_0dd6()  [Finalize]
    │       └─> FUN_1000_0e1d() × 3  [Word memcpy]
    │
    └─> Main Loop (FUN_1000_3830)
```

### 모드별 초기화

**Mode 1** (FUN_1000_0660):
1. Common data @ 0x17b4
2. Graphics init A (FUN_1000_0b94)
   - Sprite pointers: 0x8100, 0x8200, 0x8700, 0x8400, 0x8500, 0x8300
3. Mode parameter: 9
4. Rendering table: 0x18da → 0x18c4

**Mode 2** (FUN_1000_069a):
1. Common data @ 0x17b4 (same)
2. Graphics init B (FUN_1000_093a)
   - Sprite pointers: 0x6162, 0x6324, 0x64fd, 0x66fa, 0x68df
3. Mode parameter: 13
4. Rendering table: 0x18f0 → 0x18c4

---

## 메모리 맵 업데이트

### 새로 발견된 주소

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x0000 | 2B | INT 0 vector (IVT) | Divide by Zero |
| 0x0035 | 1B | Rendering mode (0/1/2) | Jump table switcher |
| 0x0042 | 1B | Graphics mode parameter | 9 or 13 |
| 0x318c | 1B | Sound enable flag | 0=on, 1=off |
| 0x320d | 2B | Data source segment | File/memory |
| 0x320f | 2B | Data source offset | File offset |
| 0x3213 | 2B | Data destination | Target buffer |
| 0x6534 | 2B | LZW bit position | Decompression state |
| 0x6536 | 2B | LZW remaining size | Bytes left |
| 0x8800 | 256B | Inverted mask table | Pixel masking |
| 0xf4f0 | 24B | Sprite pointer table | 12 entries × 2B |
| 0x18d2 | 2B | 5th Jump Table (hook) | Single function pointer |

### 데이터 세그먼트

| 세그먼트 | 용도 | 로드 위치 |
|----------|------|-----------|
| 0x1988:0x13da | Common data | 0x17b4 |
| 0x2f9e:0x0000 | Sprite data 1 | 0x1790 |
| 0x3f9e:0x0000 | Sprite data 2 | 0x179c |
| 0x493a:0x0000 | Sprite data 3 | 0x17a8 |
| 0x53a0:0x0000 | Sprite data 4 | 0x1786 |

### Jump Table 정리 (5종)

| 이름 | 주소 | 크기 | 디스패처 | 인덱스 | 용도 |
|------|------|------|----------|--------|------|
| AI Table | 0x16ef | ~512B | FUN_16e0 | state | Entity AI |
| Collision Table | 0xe3f | ~512B | FUN_0e30 | type | Collision |
| Rendering Table | 0x18c4 | 60B | FUN_499b | static | Rendering |
| Physics Table | 0x2264 | ~512B | FUN_2255 | proj_type | Projectile |
| **Hook Table** | **0x18d2** | **2B** | **FUN_810b** | **N/A** | **Update hook** |

---

## 주요 발견사항 요약

1. **완전한 데이터 로딩 시스템**:
   - 파일 I/O → 압축 체크 → LZW 해제 → 버퍼 복사
   - 인터럽트 비활성화로 안전한 로딩
   - PIT 타이머 제어로 사운드 관리

2. **LZW 압축 해제**:
   - 매직 넘버: 0x9d1f
   - Phase 3에서 구현한 C 코드와 일치
   - Variable-length code (9-12 bits?)
   - 압축률: ~50-60%

3. **CGA 비트 플레인 인터리빙**:
   - 선형 픽셀 → CGA planar 변환
   - 4 bytes (32 pixels) → 4 bytes (2 planes)
   - Bit-level interleaving
   - Phase 3 역변환 구현 완료

4. **동적 팔레트 시스템**:
   - 256-entry 색상 조합 테이블
   - Nibble-based indexing
   - 마스크 테이블 (픽셀 블렌딩용)
   - 7개 팔레트 테이블 생성

5. **2가지 그래픽 모드**:
   - Mode 1: 스프라이트 세트 A (0x8100 series)
   - Mode 2: 스프라이트 세트 B (0x6162 series)
   - 동일한 데이터 로딩, 다른 포인터

6. **5번째 Jump Table**:
   - 0x18d2: 단일 함수 포인터
   - 매 프레임 호출되는 hook
   - 렌더링 또는 업데이트 콜백

7. **PIT 타이머 제어**:
   - 사운드 비활성화: divisor = 0
   - 게임 타이머: 291.5 Hz (16× DOS default)
   - 60 FPS를 위한 정밀 타이밍

8. **세그먼트 기반 데이터 관리**:
   - 5개 데이터 세그먼트 (common + 4 sprites)
   - 세그먼트:오프셋 주소 지정
   - 동적 로딩 및 압축 해제

---

## 다음 분석 대상

1. **LZW 함수 상세 분석**:
   - FUN_1000_604e (dictionary init)
   - FUN_1000_6091 (read code)
   - FUN_1000_605b (decode code)

2. **파일 I/O 함수**:
   - FUN_1000_1e26 (read metadata)
   - FUN_1000_1e60 (read data)
   - FUN_1000_1e7f (post-process)

3. **0x18d2 Jump Table**:
   - 실제 사용되는 함수 포인터 분석
   - 모드별 다른 함수인지 확인

4. **스프라이트 포인터 테이블**:
   - 0xf4f0-f506 (12 entries)
   - 각 포인터가 가리키는 스프라이트 데이터

5. **렌더링 함수**:
   - 0x18c4 테이블의 각 엔트리 분석
   - 30개 렌더링 함수의 역할

6. **세그먼트 데이터 구조**:
   - 각 세그먼트의 정확한 데이터 형식
   - 압축/비압축 구분

---

**분석자**: Claude Code
**문서 버전**: 1.0
**Phase**: 4.8 완료
