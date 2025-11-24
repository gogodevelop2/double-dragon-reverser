# Sprite Blitting Algorithm

**작성일**: 2025-11-24
**Phase**: 5 (Algorithm Documents)
**복잡도**: ⭐⭐⭐

---

## 목차

1. [개요](#1-개요)
2. [이론 배경](#2-이론-배경)
3. [Double Dragon 구현](#3-double-dragon-구현)
4. [블리팅 알고리즘](#4-블리팅-알고리즘)
5. [투명도 처리](#5-투명도-처리)
6. [클리핑](#6-클리핑)
7. [플레너-청키 변환](#7-플레너-청키-변환)
8. [구현 예제](#8-구현-예제)
9. [성능 분석](#9-성능-분석)
10. [테스트 전략](#10-테스트-전략)
11. [최적화 기법](#11-최적화-기법)
12. [문제 해결](#12-문제-해결)
13. [참고 자료](#13-참고-자료)

---

## 1. 개요

### 1.1 스프라이트 블리팅이란?

**Sprite Blitting** (Block Image Transfer)은 비트맵 이미지 데이터를 화면 버퍼로 빠르게 복사하는 그래픽 기법입니다.

```
소스 스프라이트 데이터
        ↓
   [블리팅 엔진]
        ↓
    VRAM 버퍼
        ↓
    화면 출력
```

### 1.2 Double Dragon에서의 역할

**사용 빈도**: 60 FPS × 평균 15개 스프라이트 = **900회/초**

**처리하는 것**:
- 플레이어 캐릭터 (2명)
- 적 캐릭터 (최대 5명)
- 무기 및 이펙트
- UI 요소

### 1.3 핵심 과제

1. **투명도**: 배경 픽셀을 보존하면서 스프라이트 그리기
2. **클리핑**: 화면 경계 밖으로 나가는 부분 잘라내기
3. **Z-ordering**: 올바른 순서로 겹치기
4. **성능**: 60 FPS를 유지하기 위한 최적화

---

## 2. 이론 배경

### 2.1 메모리 포맷

#### Chunky Format (연속 저장)

```
메모리: [PPPP PPPP PPPP ...] (P = 완전한 픽셀)

예: 4-bit 픽셀 2개/바이트
Byte: [P1P1P1P1 P0P0P0P0]
```

**장점**:
- 간단한 주소 계산
- 캐시 친화적
- 빠른 읽기/쓰기

#### Planar Format (평면 분리)

```
메모리:
Plane 0: [B0 B0 B0 B0 ...]  (비트 0)
Plane 1: [B1 B1 B1 B1 ...]  (비트 1)
Plane 2: [B2 B2 B2 B2 ...]  (비트 2)
Plane 3: [B3 B3 B3 B3 ...]  (비트 3)

픽셀 = [B3 B2 B1 B0] (4-bit)
```

**장점**:
- 하드웨어 최적화 (VGA)
- 색상별 마스킹 가능
- 압축률 향상

**단점**:
- 복잡한 주소 계산
- 변환 오버헤드

### 2.2 CGA vs EGA

| 속성 | CGA Mode 4 | EGA/Tandy |
|------|-----------|-----------|
| **해상도** | 320×200 | 320×200 |
| **색상** | 4색 (2-bit) | 16색 (4-bit) |
| **메모리 구조** | 2-bit 인터리브 | 4-plane planar |
| **VRAM 크기** | 16KB | 64KB |
| **접근 방법** | 직접 메모리 쓰기 | VGA I/O 포트 |
| **투명도** | 없음 | 마스킹 지원 |

### 2.3 VGA 레지스터 (EGA 모드)

```
I/O 포트:
0x3C4: Sequencer Address Register
0x3C5: Sequencer Data Register
0x3CE: Graphics Controller Address Register
0x3CF: Graphics Controller Data Register

주요 레지스터:
- Map Mask (Index 2): 어떤 플레인에 쓸지 선택
  0x102: Plane 1 (Red)
  0x202: Plane 2 (Green)
  0x402: Plane 3 (Blue)
  0x802: Plane 0 (Intensity)

- Write Mode (Index 5): 데이터 쓰기 방식
  Mode 0: CPU 데이터 직접
  Mode 1: 래치 데이터 복사
  Mode 2: 비트 확장
```

---

## 3. Double Dragon 구현

### 3.1 듀얼 모드 아키텍처

```
초기화 시:
    ↓
하드웨어 감지 (DAT_1988_0035)
    ↓
    ├─ Mode 1 (CGA) → 테이블 @ 0x18da
    └─ Mode 2 (EGA) → 테이블 @ 0x18f0
    ↓
런타임 테이블 @ 0x18c4
    ↓
FUN_499b() 디스패처
    ↓
    ├─ Mode 1: FUN_5f07 (116 bytes)
    └─ Mode 2: FUN_29af (382 bytes)
```

### 3.2 스프라이트 파라미터 구조

```
주소      | 크기 | 이름                  | 설명
----------|------|----------------------|-------------------
0x4640    | 2    | sprite_flags         | 플래그 비트
0x4642    | 2    | sprite_param_1       | 추가 파라미터
0x4644    | 2    | sprite_width         | 폭 (words)
0x4646    | 2    | sprite_height        | 높이 (scanlines)
0x4648    | 2    | sprite_param_4       | 파라미터 4
0x464a    | 2    | sprite_type          | 타입/핸들러
0x464c    | 2    | sprite_src_pointer   | 소스 데이터 포인터
0x464e    | 2    | sprite_flags_2       | 추가 플래그
0x465e    | 2    | sprite_dest_vram     | 목적지 VRAM (0xbb80 = 화면 밖)
```

### 3.3 Mode 1 블리팅 (CGA)

**함수**: FUN_5f07 (1000:5f07, 116 bytes)

**특징**:
- 단순 메모리 복사
- 투명도 없음 (덮어쓰기)
- 수직 클리핑만 지원
- 순환 버퍼 처리

**알고리즘**:
```c
void blit_sprite_cga(SpriteParams* params) {
    // 1. 파라미터 복사 (14 words)
    copy_params(params, 0x4644);

    uint16_t* src = *(uint16_t**)0x464c;
    uint16_t* dst = *(uint16_t**)0x465e;
    int width = *(int*)0x4644;
    int height = *(int*)0x4646;

    // 2. 화면 밖 체크
    if (dst == 0xbb80) {
        return;  // 화면 밖
    }

    // 3. 수직 클리핑 체크
    if (dst + (height * 0x48) >= 0) {
        // 정상 케이스: 단순 복사
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                *dst++ = *src++;
            }
            dst += (0x48 - width);  // 다음 스캔라인
        }
    } else {
        // 순환 버퍼 케이스
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                *(uint16_t*)((uint16_t)dst & 0x7fff) = *src++;
                dst++;
            }
            dst = (uint16_t*)(((uint16_t)dst + (0x48 - width)) & 0x7fff);
        }
    }
}
```

**상수**:
- `0xbb80`: 화면 밖 마커 (유효하지 않은 VRAM 주소)
- `0x48` (72 bytes): CGA 스캔라인 간격
- `0x7fff`: 32KB 순환 버퍼 마스크

### 3.4 Mode 2 블리팅 (EGA)

**함수**: FUN_29af (1000:29af, 382 bytes)

**특징**:
- VGA 포트 프로그래밍
- 4-plane planar 쓰기
- 투명도 마스킹 지원
- 복잡한 데이터 재배열

**알고리즘 개요**:

```c
void blit_sprite_ega(int mode, uint8_t* src, uint8_t* dst) {
    // 1. VGA 초기화
    outportb(0x3CE, 5);  // Write Mode 0

    // 2. 루프 횟수 결정
    int iterations = (mode == 2) ? 12 : 16;

    for (int i = 0; i < iterations; i++) {
        // 3. Plane 3 (Blue) 쓰기
        outportb(0x3C4, 0x0402);  // Map Mask: Plane 3
        dst[0] = src[1];
        dst[1] = src[5];
        dst[2] = src[9];
        dst[3] = src[13];

        // 4. Plane 2 (Green) 쓰기
        outportb(0x3C4, 0x0202);  // Map Mask: Plane 2
        dst[0] = src[2];
        dst[1] = src[6];
        dst[2] = src[10];
        dst[3] = src[14];

        // 5. Plane 1 (Red) 쓰기
        outportb(0x3C4, 0x0102);  // Map Mask: Plane 1
        dst[0] = src[3];
        dst[1] = src[7];
        dst[2] = src[11];
        dst[3] = src[15];

        // 6. Plane 0 (Intensity) 쓰기
        outportb(0x3C4, 0x0802);  // Map Mask: Plane 0
        dst[0] = src[0];
        dst[1] = src[4];
        dst[2] = src[8];
        dst[3] = src[12];

        src += 16;  // 다음 16 bytes
        dst += 40;  // 다음 스캔라인 (320px / 8 = 40 bytes)
    }

    // 7. 투명도 마스킹 (mode != 1일 때)
    if (mode != 1) {
        apply_transparency_mask(dst, src);
    }
}
```

**데이터 재배열**:

```
소스 (16 bytes, 인터리브):
[P0_0, P3_0, P2_0, P1_0, P0_1, P3_1, P2_1, P1_1,
 P0_2, P3_2, P2_2, P1_2, P0_3, P3_3, P2_3, P1_3]

목적지 (4 planes × 4 bytes):
Plane 0: [P0_0, P0_1, P0_2, P0_3]
Plane 1: [P1_0, P1_1, P1_2, P1_3]
Plane 2: [P2_0, P2_1, P2_2, P2_3]
Plane 3: [P3_0, P3_1, P3_2, P3_3]
```

---

## 4. 블리팅 알고리즘

### 4.1 기본 블리팅

**pseudocode**:

```
function blit_simple(src, dst, width, height):
    for y in 0 to height-1:
        for x in 0 to width-1:
            dst[y * screen_width + x] = src[y * width + x]
```

**최적화된 버전** (word 단위):

```
function blit_optimized(src, dst, width_words, height):
    for y in 0 to height-1:
        // memcpy 또는 MOVSW 사용
        copy_memory(dst, src, width_words * 2)
        src += width_words
        dst += scanline_stride
```

### 4.2 순환 버퍼 블리팅

```
function blit_circular(src, dst, width, height, buffer_mask):
    for y in 0 to height-1:
        for x in 0 to width-1:
            masked_addr = (dst & buffer_mask)
            memory[masked_addr] = src[y * width + x]
            dst = (dst + 1) & buffer_mask

        dst = (dst + (scanline_stride - width)) & buffer_mask
```

**순환 버퍼 장점**:
- 고정 메모리 크기
- 무한 스크롤 지원
- 포인터 wrap 자동 처리

### 4.3 Z-ordering

```
function render_sprites_with_z_order(sprite_list):
    // 1. Y 좌표 기준 정렬 (뒤에서 앞으로)
    sort(sprite_list, key=lambda s: s.y)

    // 2. 순차 블리팅
    for sprite in sprite_list:
        blit_sprite(sprite)
```

**Double Dragon 구현**:
- FUN_48e0: 스프라이트 리스트 빌드
- FUN_499b: Z-order 순서로 렌더링

---

## 5. 투명도 처리

### 5.1 CGA 투명도 (없음)

CGA Mode 1은 **투명도를 지원하지 않습니다**. 모든 픽셀이 덮어씌워집니다.

**해결 방법**:
- 직사각형 스프라이트만 사용
- 배경과 스프라이트 색상을 구분

### 5.2 EGA 투명도 (마스킹)

**원리**: 배경색 (0000) 픽셀을 건너뛰기

**알고리즘**:

```c
void apply_transparency_mask(uint8_t* dst, uint8_t* mask_data) {
    for (int i = 0; i < 4; i++) {
        // 마스크 계산
        uint8_t p0_low  = mask_data[0];
        uint8_t p0_high = mask_data[1];
        uint8_t p2_low  = mask_data[2];
        uint8_t p2_high = mask_data[3];

        // 마스크 공식: (~P2) & P0
        uint8_t mask = (~p2_low & p0_low) & (~p0_high & p0_low);

        // XOR로 투명 픽셀 처리
        outportb(0x3C4, 0x0102);  // Plane 1
        dst[i] = p2_high ^ mask;

        outportb(0x3C4, 0x0202);  // Plane 2
        dst[i] = p2_low;

        outportb(0x3C4, 0x0402);  // Plane 3
        dst[i] = p0_high ^ mask;

        outportb(0x3C4, 0x0802);  // Plane 0
        dst[i] = p0_low;

        mask_data += 4;
    }
}
```

**마스크 비트 연산**:

```
픽셀 = [P3 P2 P1 P0]

투명 조건: P3=0, P2=0, P1=0, P0=0
마스크 = 1 (투명), 0 (불투명)

XOR 효과:
- mask = 0: 원본 데이터 그대로
- mask = 1: 비트 반전 (기존 VRAM 보존)
```

### 5.3 현대적 투명도 (알파 블렌딩)

```python
def blit_with_alpha(src, dst, alpha):
    for y in range(height):
        for x in range(width):
            src_pixel = src[y][x]
            dst_pixel = dst[y][x]

            if src_pixel.alpha == 0:
                continue  # 완전 투명

            # 알파 블렌딩
            dst[y][x] = blend(src_pixel, dst_pixel, alpha)

def blend(src, dst, alpha):
    r = src.r * alpha + dst.r * (1 - alpha)
    g = src.g * alpha + dst.g * (1 - alpha)
    b = src.b * alpha + dst.b * (1 - alpha)
    return Color(r, g, b)
```

---

## 6. 클리핑

### 6.1 경계 조건

```
화면 크기: 320×200
스프라이트: (x, y, width, height)

클리핑 필요 조건:
- x < 0            (왼쪽 밖)
- x + width > 320  (오른쪽 밖)
- y < 0            (위쪽 밖)
- y + height > 200 (아래쪽 밖)
```

### 6.2 수직 클리핑

**Double Dragon 구현** (FUN_5f07):

```c
// 수직 경계 체크
if (dst + (height * scanline_stride) >= 0) {
    // 정상: 화면 안
    blit_normal(src, dst, width, height);
} else {
    // 순환 버퍼: 화면 밖 → 안으로 wrap
    blit_circular(src, dst, width, height);
}
```

### 6.3 완전한 클리핑 알고리즘

```python
def blit_with_clipping(src, dst_x, dst_y, width, height):
    # 1. 소스 오프셋 계산
    src_x = 0
    src_y = 0

    # 2. 왼쪽 클리핑
    if dst_x < 0:
        src_x = -dst_x
        width += dst_x
        dst_x = 0

    # 3. 오른쪽 클리핑
    if dst_x + width > SCREEN_WIDTH:
        width = SCREEN_WIDTH - dst_x

    # 4. 위쪽 클리핑
    if dst_y < 0:
        src_y = -dst_y
        height += dst_y
        dst_y = 0

    # 5. 아래쪽 클리핑
    if dst_y + height > SCREEN_HEIGHT:
        height = SCREEN_HEIGHT - dst_y

    # 6. 완전히 화면 밖이면 리턴
    if width <= 0 or height <= 0:
        return

    # 7. 클리핑된 영역 블리팅
    for y in range(height):
        for x in range(width):
            dst[dst_y + y][dst_x + x] = src[src_y + y][src_x + x]
```

### 6.4 화면 밖 마커

**Double Dragon**: `0xbb80`

```c
if (dst_vram == 0xbb80) {
    return;  // 완전히 화면 밖
}
```

**이점**:
- 간단한 체크 (1회 비교)
- 조기 종료
- CPU 사이클 절약

---

## 7. 플레너-청키 변환

### 7.1 필요성

```
스프라이트 파일 저장: Planar 형식 (압축률 높음)
       ↓ 변환 필요
화면 렌더링: Chunky 형식 (빠른 접근)
```

### 7.2 FUN_0cd1 알고리즘

**함수**: 1000:0cd1 (147 bytes)

**입력**: 4 bytes (4 planes)
**출력**: 4 bytes (8 pixels, chunky)

**원리**:

```
4개 입력 바이트의 같은 비트 위치를 모아서
하나의 4-bit 픽셀로 만듦

입력:
Plane 0: [B0_7 B0_6 B0_5 B0_4 B0_3 B0_2 B0_1 B0_0]
Plane 1: [B1_7 B1_6 B1_5 B1_4 B1_3 B1_2 B1_1 B1_0]
Plane 2: [B2_7 B2_6 B2_5 B2_4 B2_3 B2_2 B2_1 B2_0]
Plane 3: [B3_7 B3_6 B3_5 B3_4 B3_3 B3_2 B3_1 B3_0]

출력 픽셀 7: [B0_7 B1_7 B2_7 B3_7]
출력 픽셀 6: [B0_6 B1_6 B2_6 B3_6]
...
출력 픽셀 0: [B0_0 B1_0 B2_0 B3_0]
```

### 7.3 C 구현

```c
void planar_to_chunky(const uint8_t *input, uint8_t *output, size_t num_groups) {
    for (size_t i = 0; i < num_groups; i++) {
        // 4바이트 읽기 (4 planes)
        uint8_t plane0 = input[0];
        uint8_t plane1 = input[1];
        uint8_t plane2 = input[2];
        uint8_t plane3 = input[3];

        // 2개 워드 (4바이트) 출력
        uint16_t word0 = 0;
        uint16_t word1 = 0;

        // MSB부터 LSB까지 (bit 7 → bit 0)
        for (int bit = 7; bit >= 0; bit--) {
            // 각 plane에서 해당 비트 추출
            int b0 = (plane0 >> bit) & 1;
            int b1 = (plane1 >> bit) & 1;
            int b2 = (plane2 >> bit) & 1;
            int b3 = (plane3 >> bit) & 1;

            // 4비트를 합쳐서 픽셀 (0-15)
            int pixel = (b0 << 3) | (b1 << 2) | (b2 << 1) | b3;

            // word0에 상위 4픽셀, word1에 하위 4픽셀
            if (bit >= 4) {
                word0 = (word0 << 4) | pixel;
            } else {
                word1 = (word1 << 4) | pixel;
            }
        }

        // Little-endian으로 출력
        output[0] = word0 & 0xFF;
        output[1] = (word0 >> 8) & 0xFF;
        output[2] = word1 & 0xFF;
        output[3] = (word1 >> 8) & 0xFF;

        input += 4;
        output += 4;
    }
}
```

### 7.4 최적화 버전 (룩업 테이블)

```c
// 초기화 시 한 번만 생성
uint8_t planar_lut[256][4];

void build_planar_lut() {
    for (int i = 0; i < 256; i++) {
        for (int bit = 0; bit < 8; bit++) {
            int b = (i >> bit) & 1;
            planar_lut[i][bit / 2] |= (b << (bit % 2));
        }
    }
}

// 런타임: O(1) 룩업
void planar_to_chunky_fast(const uint8_t *input, uint8_t *output) {
    uint8_t p0 = input[0];
    uint8_t p1 = input[1];
    uint8_t p2 = input[2];
    uint8_t p3 = input[3];

    for (int i = 0; i < 4; i++) {
        output[i] = (planar_lut[p0][i] << 3) |
                    (planar_lut[p1][i] << 2) |
                    (planar_lut[p2][i] << 1) |
                     planar_lut[p3][i];
    }
}
```

---

## 8. 구현 예제

### 8.1 C 구현

```c
#include <stdint.h>
#include <string.h>

// 스프라이트 구조체
typedef struct {
    uint16_t width;    // 폭 (pixels)
    uint16_t height;   // 높이 (pixels)
    uint8_t* data;     // 픽셀 데이터
    uint8_t* mask;     // 투명도 마스크 (옵션)
} Sprite;

// CGA 블리팅 (투명도 없음)
void blit_cga(const Sprite* sprite, uint8_t* vram, int x, int y) {
    const int SCREEN_WIDTH = 320;
    const int SCREEN_HEIGHT = 200;
    const int BYTES_PER_LINE = 80;  // 320px / 4 = 80 bytes

    // 클리핑
    int src_x = 0, src_y = 0;
    int width = sprite->width;
    int height = sprite->height;

    if (x < 0) {
        src_x = -x;
        width += x;
        x = 0;
    }
    if (y < 0) {
        src_y = -y;
        height += y;
        y = 0;
    }
    if (x + width > SCREEN_WIDTH) {
        width = SCREEN_WIDTH - x;
    }
    if (y + height > SCREEN_HEIGHT) {
        height = SCREEN_HEIGHT - y;
    }

    if (width <= 0 || height <= 0) {
        return;  // 완전히 화면 밖
    }

    // 블리팅
    uint8_t* src = sprite->data + (src_y * sprite->width + src_x);
    uint8_t* dst = vram + (y * BYTES_PER_LINE + x / 4);

    for (int row = 0; row < height; row++) {
        memcpy(dst, src, width / 4);  // 4 pixels/byte
        src += sprite->width / 4;
        dst += BYTES_PER_LINE;
    }
}

// EGA 블리팅 (투명도 지원)
void blit_ega(const Sprite* sprite, uint8_t* vram, int x, int y) {
    const int SCREEN_WIDTH = 320;
    const int BYTES_PER_LINE = 40;  // 320px / 8 = 40 bytes

    // 클리핑 (생략 - CGA와 동일)

    // VGA 초기화
    outportb(0x3CE, 5);
    outportb(0x3CF, 0);  // Write Mode 0

    uint8_t* src = sprite->data;
    uint8_t* dst = vram + (y * BYTES_PER_LINE + x / 8);

    for (int row = 0; row < sprite->height; row++) {
        for (int col = 0; col < sprite->width / 8; col++) {
            // 16 bytes 소스 → 4 planes

            // Plane 3
            outportb(0x3C4, 0x02);
            outportb(0x3C5, 0x08);
            dst[0] = src[0];
            dst[1] = src[4];
            dst[2] = src[8];
            dst[3] = src[12];

            // Plane 2
            outportb(0x3C5, 0x04);
            dst[0] = src[1];
            dst[1] = src[5];
            dst[2] = src[9];
            dst[3] = src[13];

            // Plane 1
            outportb(0x3C5, 0x02);
            dst[0] = src[2];
            dst[1] = src[6];
            dst[2] = src[10];
            dst[3] = src[14];

            // Plane 0
            outportb(0x3C5, 0x01);
            dst[0] = src[3];
            dst[1] = src[7];
            dst[2] = src[11];
            dst[3] = src[15];

            src += 16;
            dst += 4;
        }

        dst += (BYTES_PER_LINE - sprite->width / 8 * 4);
    }
}

// 알파 블렌딩 (현대적)
void blit_rgba(const Sprite* sprite, uint32_t* framebuffer,
               int x, int y, int screen_width, int screen_height) {
    for (int row = 0; row < sprite->height; row++) {
        for (int col = 0; col < sprite->width; col++) {
            int dst_x = x + col;
            int dst_y = y + row;

            if (dst_x < 0 || dst_x >= screen_width ||
                dst_y < 0 || dst_y >= screen_height) {
                continue;  // 클리핑
            }

            uint32_t src_pixel = sprite->data[row * sprite->width + col];
            uint8_t alpha = (src_pixel >> 24) & 0xFF;

            if (alpha == 0) {
                continue;  // 완전 투명
            }

            if (alpha == 255) {
                // 완전 불투명
                framebuffer[dst_y * screen_width + dst_x] = src_pixel;
            } else {
                // 알파 블렌딩
                uint32_t dst_pixel = framebuffer[dst_y * screen_width + dst_x];

                uint8_t sr = (src_pixel >> 16) & 0xFF;
                uint8_t sg = (src_pixel >> 8) & 0xFF;
                uint8_t sb = src_pixel & 0xFF;

                uint8_t dr = (dst_pixel >> 16) & 0xFF;
                uint8_t dg = (dst_pixel >> 8) & 0xFF;
                uint8_t db = dst_pixel & 0xFF;

                uint8_t r = (sr * alpha + dr * (255 - alpha)) / 255;
                uint8_t g = (sg * alpha + dg * (255 - alpha)) / 255;
                uint8_t b = (sb * alpha + db * (255 - alpha)) / 255;

                framebuffer[dst_y * screen_width + dst_x] =
                    0xFF000000 | (r << 16) | (g << 8) | b;
            }
        }
    }
}
```

### 8.2 Python 구현

```python
import numpy as np
from typing import Tuple, Optional

class Sprite:
    def __init__(self, width: int, height: int, data: np.ndarray, mask: Optional[np.ndarray] = None):
        self.width = width
        self.height = height
        self.data = data  # (height, width, 4) RGBA
        self.mask = mask

def blit_simple(sprite: Sprite, framebuffer: np.ndarray, x: int, y: int):
    """
    간단한 블리팅 (클리핑 및 투명도 없음)
    """
    h, w = sprite.height, sprite.width
    framebuffer[y:y+h, x:x+w] = sprite.data

def blit_with_clipping(sprite: Sprite, framebuffer: np.ndarray, x: int, y: int):
    """
    클리핑을 지원하는 블리팅
    """
    screen_h, screen_w = framebuffer.shape[:2]

    # 소스 영역 계산
    src_x, src_y = 0, 0
    src_w, src_h = sprite.width, sprite.height

    # 목적지 영역 계산
    dst_x, dst_y = x, y
    dst_w, dst_h = sprite.width, sprite.height

    # 왼쪽 클리핑
    if dst_x < 0:
        src_x = -dst_x
        src_w += dst_x
        dst_x = 0

    # 오른쪽 클리핑
    if dst_x + dst_w > screen_w:
        src_w = screen_w - dst_x

    # 위쪽 클리핑
    if dst_y < 0:
        src_y = -dst_y
        src_h += dst_y
        dst_y = 0

    # 아래쪽 클리핑
    if dst_y + dst_h > screen_h:
        src_h = screen_h - dst_y

    # 완전히 화면 밖이면 리턴
    if src_w <= 0 or src_h <= 0:
        return

    # 블리팅
    framebuffer[dst_y:dst_y+src_h, dst_x:dst_x+src_w] = \
        sprite.data[src_y:src_y+src_h, src_x:src_x+src_w]

def blit_with_alpha(sprite: Sprite, framebuffer: np.ndarray, x: int, y: int):
    """
    알파 블렌딩을 지원하는 블리팅
    """
    screen_h, screen_w = framebuffer.shape[:2]

    # 클리핑 (간단 버전)
    if x < 0 or y < 0 or x + sprite.width > screen_w or y + sprite.height > screen_h:
        return  # TODO: 부분 클리핑

    # 알파 채널 추출
    alpha = sprite.data[:, :, 3:4] / 255.0

    # 블렌딩
    src_rgb = sprite.data[:, :, :3]
    dst_rgb = framebuffer[y:y+sprite.height, x:x+sprite.width, :3]

    blended = src_rgb * alpha + dst_rgb * (1 - alpha)
    framebuffer[y:y+sprite.height, x:x+sprite.width, :3] = blended.astype(np.uint8)

def planar_to_chunky(planar: np.ndarray) -> np.ndarray:
    """
    4-plane planar 데이터를 chunky 형식으로 변환

    Args:
        planar: (4, height, width) uint8 배열

    Returns:
        chunky: (height, width) uint8 배열 (4-bit 픽셀)
    """
    height, width = planar.shape[1:]
    chunky = np.zeros((height, width), dtype=np.uint8)

    for plane in range(4):
        chunky |= ((planar[plane] & 1) << plane)

    return chunky

def blit_cga_style(sprite_planar: np.ndarray, framebuffer: np.ndarray, x: int, y: int):
    """
    CGA 스타일 블리팅 (4-plane planar → chunky)
    """
    # 변환
    sprite_chunky = planar_to_chunky(sprite_planar)

    # 블리팅
    h, w = sprite_chunky.shape
    framebuffer[y:y+h, x:x+w] = sprite_chunky
```

### 8.3 JavaScript 구현

```javascript
class Sprite {
    constructor(width, height, data, mask = null) {
        this.width = width;
        this.height = height;
        this.data = data;  // Uint8ClampedArray (RGBA)
        this.mask = mask;
    }
}

/**
 * 간단한 블리팅 (ImageData 사용)
 */
function blitSimple(sprite, ctx, x, y) {
    const imageData = ctx.createImageData(sprite.width, sprite.height);
    imageData.data.set(sprite.data);
    ctx.putImageData(imageData, x, y);
}

/**
 * 클리핑을 지원하는 블리팅
 */
function blitWithClipping(sprite, ctx, x, y) {
    const canvas = ctx.canvas;
    const screenWidth = canvas.width;
    const screenHeight = canvas.height;

    // 클리핑 영역 계산
    let srcX = 0, srcY = 0;
    let srcW = sprite.width, srcH = sprite.height;
    let dstX = x, dstY = y;

    if (dstX < 0) {
        srcX = -dstX;
        srcW += dstX;
        dstX = 0;
    }
    if (dstY < 0) {
        srcY = -dstY;
        srcH += dstY;
        dstY = 0;
    }
    if (dstX + srcW > screenWidth) {
        srcW = screenWidth - dstX;
    }
    if (dstY + srcH > screenHeight) {
        srcH = screenHeight - dstY;
    }

    if (srcW <= 0 || srcH <= 0) {
        return;  // 완전히 화면 밖
    }

    // 클리핑된 영역만 블리팅
    const imageData = ctx.createImageData(srcW, srcH);

    for (let row = 0; row < srcH; row++) {
        for (let col = 0; col < srcW; col++) {
            const srcIdx = ((srcY + row) * sprite.width + (srcX + col)) * 4;
            const dstIdx = (row * srcW + col) * 4;

            imageData.data[dstIdx + 0] = sprite.data[srcIdx + 0];  // R
            imageData.data[dstIdx + 1] = sprite.data[srcIdx + 1];  // G
            imageData.data[dstIdx + 2] = sprite.data[srcIdx + 2];  // B
            imageData.data[dstIdx + 3] = sprite.data[srcIdx + 3];  // A
        }
    }

    ctx.putImageData(imageData, dstX, dstY);
}

/**
 * 알파 블렌딩을 지원하는 블리팅
 */
function blitWithAlpha(sprite, ctx, x, y) {
    // 기존 프레임버퍼 읽기
    const existingData = ctx.getImageData(x, y, sprite.width, sprite.height);
    const result = ctx.createImageData(sprite.width, sprite.height);

    for (let i = 0; i < sprite.data.length; i += 4) {
        const alpha = sprite.data[i + 3] / 255;

        if (alpha === 0) {
            // 완전 투명: 기존 픽셀 유지
            result.data[i + 0] = existingData.data[i + 0];
            result.data[i + 1] = existingData.data[i + 1];
            result.data[i + 2] = existingData.data[i + 2];
            result.data[i + 3] = existingData.data[i + 3];
        } else if (alpha === 1) {
            // 완전 불투명: 소스 픽셀 복사
            result.data[i + 0] = sprite.data[i + 0];
            result.data[i + 1] = sprite.data[i + 1];
            result.data[i + 2] = sprite.data[i + 2];
            result.data[i + 3] = sprite.data[i + 3];
        } else {
            // 알파 블렌딩
            result.data[i + 0] = sprite.data[i + 0] * alpha + existingData.data[i + 0] * (1 - alpha);
            result.data[i + 1] = sprite.data[i + 1] * alpha + existingData.data[i + 1] * (1 - alpha);
            result.data[i + 2] = sprite.data[i + 2] * alpha + existingData.data[i + 2] * (1 - alpha);
            result.data[i + 3] = 255;
        }
    }

    ctx.putImageData(result, x, y);
}

/**
 * Planar to Chunky 변환
 */
function planarToChunky(planar, width, height) {
    // planar: [plane0, plane1, plane2, plane3]
    // 각 plane은 Uint8Array (width * height bytes)

    const chunky = new Uint8Array(width * height);

    for (let i = 0; i < width * height; i++) {
        const byteIdx = Math.floor(i / 8);
        const bitIdx = 7 - (i % 8);

        let pixel = 0;
        for (let plane = 0; plane < 4; plane++) {
            const bit = (planar[plane][byteIdx] >> bitIdx) & 1;
            pixel |= (bit << plane);
        }

        chunky[i] = pixel;
    }

    return chunky;
}

/**
 * CGA 스타일 렌더링
 */
function blitCGAStyle(spritePlanar, ctx, x, y, width, height, palette) {
    // 변환
    const chunky = planarToChunky(spritePlanar, width, height);

    // RGBA로 변환
    const imageData = ctx.createImageData(width, height);

    for (let i = 0; i < chunky.length; i++) {
        const colorIndex = chunky[i];
        const color = palette[colorIndex];

        imageData.data[i * 4 + 0] = color.r;
        imageData.data[i * 4 + 1] = color.g;
        imageData.data[i * 4 + 2] = color.b;
        imageData.data[i * 4 + 3] = 255;
    }

    ctx.putImageData(imageData, x, y);
}

// 사용 예제
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// CGA 팔레트 정의
const CGA_PALETTE = [
    { r: 0, g: 0, b: 0 },       // 0: 검정
    { r: 0, g: 170, b: 170 },   // 1: 청록
    { r: 170, g: 0, b: 170 },   // 2: 자홍
    { r: 170, g: 170, b: 170 }  // 3: 흰색
];

// 스프라이트 로드 및 블리팅
const sprite = loadSprite('player.png');
blitWithAlpha(sprite, ctx, 100, 100);
```

---

## 9. 성능 분석

### 9.1 복잡도 분석

**기본 블리팅**:
```
시간 복잡도: O(width × height)
공간 복잡도: O(1) (추가 메모리 없음)
```

**클리핑 포함**:
```
시간 복잡도: O(width × height) + O(1) (클리핑 계산)
최악의 경우: O(W × H) (전체 화면)
최선의 경우: O(1) (완전히 화면 밖)
```

**알파 블렌딩**:
```
시간 복잡도: O(width × height × k)
k = 블렌딩 연산 비용 (약 10-20 사이클)
```

### 9.2 실제 성능 (Double Dragon)

**60 FPS 목표**: 16.67ms/frame

**프레임당 블리팅**:
- 플레이어 2명: 2 sprites
- 적 캐릭터: 평균 3명 = 3 sprites
- 무기: 평균 2개 = 2 sprites
- UI: 고정 = 5 sprites

**총 12 sprites/frame**

**평균 스프라이트 크기**: 32×32 pixels = 1,024 pixels

**총 픽셀 처리**: 12 × 1,024 = 12,288 pixels/frame

**CGA 모드** (직접 메모리 쓰기):
```
12,288 pixels × 4 bytes/pixel = 49,152 bytes
Intel 8088 @ 4.77 MHz: ~2-3 사이클/byte
총 시간: 49,152 × 2.5 / 4,770,000 = 0.026ms
여유: 16.67ms - 0.026ms = **16.64ms** (충분!)
```

**EGA 모드** (VGA 포트):
```
추가 오버헤드:
- VGA 포트 쓰기: ~10 사이클
- 플레인 전환: 4회 × 10 = 40 사이클
- 데이터 재배열: ~50 사이클

총 시간: ~0.2ms
여유: 16.67ms - 0.2ms = **16.47ms** (충분!)
```

**결론**: 블리팅은 **전체 프레임 시간의 1-2%** 소모

### 9.3 병목 지점

1. **압축 해제**: RLE 디코딩 (800회/frame)
2. **애니메이션 업데이트**: 객체 7개 × 복잡한 로직
3. **스크롤링**: 타일맵 로딩 (조건부)

블리팅은 **병목이 아님**!

### 9.4 최적화 기법

**1. Early Exit**:
```c
if (dst == 0xbb80) {
    return;  // 0.001ms 절약
}
```

**2. MOVSW 사용** (x86):
```asm
MOV CX, width
REP MOVSW  ; 단일 명령어로 전체 라인 복사
```

**3. 더티 플래그**:
```c
if (dirty_flag == 0) {
    return;  // 변경 없으면 건너뛰기
}
```

**4. 순환 버퍼**:
```c
// 조건 분기 없음
dst = (dst + 1) & buffer_mask;
```

---

## 10. 테스트 전략

### 10.1 단위 테스트

```c
// 테스트 1: 기본 블리팅
void test_basic_blit() {
    uint8_t src[16] = {1, 2, 3, 4, ...};
    uint8_t dst[100] = {0};

    blit_simple(src, dst, 0, 0, 4, 4, 10);

    assert(dst[0] == 1);
    assert(dst[1] == 2);
    assert(dst[10] == 5);  // 두 번째 줄 시작
}

// 테스트 2: 클리핑 (왼쪽)
void test_clip_left() {
    uint8_t src[16] = {1, 2, 3, 4, ...};
    uint8_t dst[100] = {0};

    blit_with_clipping(src, dst, -2, 0, 4, 4, 10, 10);

    // 왼쪽 2픽셀 잘림
    assert(dst[0] == 3);
    assert(dst[1] == 4);
}

// 테스트 3: 알파 블렌딩
void test_alpha_blend() {
    uint32_t src = 0x80FF0000;  // 50% 불투명 빨강
    uint32_t dst = 0xFF0000FF;  // 100% 불투명 파랑

    uint32_t result = blend_pixel(src, dst);

    // 예상: 50% 빨강 + 50% 파랑 = 보라
    assert((result & 0xFF) == 127);        // B
    assert(((result >> 16) & 0xFF) == 127);  // R
}

// 테스트 4: 순환 버퍼
void test_circular_buffer() {
    uint8_t buffer[16] = {0};

    uint16_t ptr = 14;
    buffer[ptr & 0xF] = 1;
    ptr++;
    buffer[ptr & 0xF] = 2;
    ptr++;
    buffer[ptr & 0xF] = 3;  // wrap to 0

    assert(buffer[14] == 1);
    assert(buffer[15] == 2);
    assert(buffer[0] == 3);
}

// 테스트 5: Planar 변환
void test_planar_conversion() {
    uint8_t planar[4] = {0xFF, 0x00, 0xFF, 0x00};
    uint8_t chunky[4];

    planar_to_chunky(planar, chunky, 1);

    // 각 픽셀: [1 0 1 0] = 10 (0xA)
    assert(chunky[0] == 0xAA);
    assert(chunky[1] == 0xAA);
}
```

### 10.2 통합 테스트

```python
def test_full_frame_render():
    """전체 프레임 렌더링 테스트"""
    framebuffer = np.zeros((200, 320, 4), dtype=np.uint8)

    sprites = [
        load_sprite('player1.png', x=100, y=100),
        load_sprite('player2.png', x=150, y=100),
        load_sprite('enemy1.png', x=200, y=120),
    ]

    # Z-order 정렬
    sprites.sort(key=lambda s: s.y)

    # 블리팅
    for sprite in sprites:
        blit_with_alpha(sprite, framebuffer, sprite.x, sprite.y)

    # 검증
    assert_not_equal(framebuffer, np.zeros_like(framebuffer))
    assert_valid_colors(framebuffer)

def test_edge_cases():
    """경계 케이스 테스트"""
    # 1. 완전히 화면 밖
    blit_with_clipping(sprite, fb, -100, -100)
    # 변경 없어야 함

    # 2. 부분적으로 화면 밖
    blit_with_clipping(sprite, fb, 310, 0)
    # 10픽셀만 보여야 함

    # 3. 화면 경계에 정확히 맞음
    blit_with_clipping(sprite, fb, 288, 168)
    # 32×32 스프라이트가 320×200에 딱 맞음
```

### 10.3 시각적 검증

```python
def visual_regression_test():
    """DOSBox 실행 결과와 비교"""
    # 원본 DOSBox 스크린샷
    original = load_image('dosbox_frame100.png')

    # 현대 구현 렌더링
    modern = render_frame_modern(game_state_frame100)

    # 픽셀 단위 비교
    diff = np.abs(original.astype(float) - modern.astype(float))
    similarity = 1.0 - (np.mean(diff) / 255.0)

    assert similarity > 0.95, f"Too different: {similarity:.2%}"

    # 차이 이미지 저장 (디버깅용)
    save_image('diff.png', diff)
```

### 10.4 성능 테스트

```c
#include <time.h>

void benchmark_blit() {
    const int ITERATIONS = 10000;

    clock_t start = clock();

    for (int i = 0; i < ITERATIONS; i++) {
        blit_sprite_cga(&test_sprite, vram, 100, 100);
    }

    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;

    printf("Average: %.3f ms/blit\n", (elapsed * 1000.0) / ITERATIONS);
    printf("FPS capability: %.1f\n", 1000.0 / ((elapsed * 1000.0) / ITERATIONS));
}

void profile_frame() {
    clock_t t1, t2, t3, t4;

    t1 = clock();
    update_entities();

    t2 = clock();
    build_sprite_list();

    t3 = clock();
    blit_all_sprites();

    t4 = clock();

    printf("Update:  %.2f ms\n", (t2 - t1) * 1000.0 / CLOCKS_PER_SEC);
    printf("Build:   %.2f ms\n", (t3 - t2) * 1000.0 / CLOCKS_PER_SEC);
    printf("Blit:    %.2f ms\n", (t4 - t3) * 1000.0 / CLOCKS_PER_SEC);
    printf("Total:   %.2f ms\n", (t4 - t1) * 1000.0 / CLOCKS_PER_SEC);
}
```

---

## 11. 최적화 기법

### 11.1 하드웨어 최적화

**1. MOVSW 사용** (x86 전용):
```asm
; 느린 버전 (루프)
MOV CX, width
loop:
    LODSW
    STOSW
    LOOP loop

; 빠른 버전 (REP 접두사)
MOV CX, width
REP MOVSW  ; 단일 명령어, 하드웨어 최적화
```

**이득**: 2-3배 빠름

**2. VGA 래치 사용** (EGA 모드):
```c
// Write Mode 1: 래치 데이터 복사
outportb(0x3CE, 5);
outportb(0x3CF, 1);

// 소스 읽기 (래치에 로드)
dummy = vram_src[0];

// 목적지 쓰기 (래치 데이터 복사)
vram_dst[0] = 0xFF;  // 값 무관, 래치 데이터 복사됨
```

**이득**: 4배 빠름 (4 planes 동시 복사)

### 11.2 소프트웨어 최적화

**1. 조기 종료**:
```c
// 화면 밖 체크
if (x < -sprite_width || x >= SCREEN_WIDTH ||
    y < -sprite_height || y >= SCREEN_HEIGHT) {
    return;  // 즉시 종료
}

// 투명도 체크
if (alpha == 0) {
    continue;  // 픽셀 건너뛰기
}
```

**2. 룩업 테이블**:
```c
// 초기화 시 (한 번만)
void build_blend_lut() {
    for (int src = 0; src < 256; src++) {
        for (int dst = 0; dst < 256; dst++) {
            for (int alpha = 0; alpha < 256; alpha++) {
                blend_lut[src][dst][alpha] =
                    (src * alpha + dst * (255 - alpha)) / 255;
            }
        }
    }
}

// 런타임 (O(1) 룩업)
result = blend_lut[src][dst][alpha];
```

**단점**: 메모리 사용량 16MB (256³)

**개선**: 1D 테이블 사용
```c
// 8-bit alpha만 지원: 256 × 256 = 64KB
uint8_t alpha_lut[256][256];

void build_alpha_lut() {
    for (int src = 0; src < 256; src++) {
        for (int alpha = 0; alpha < 256; alpha++) {
            alpha_lut[src][alpha] = (src * alpha) / 255;
        }
    }
}

// 사용
result = alpha_lut[src][alpha] + alpha_lut[dst][255 - alpha];
```

**3. SIMD 사용** (현대 CPU):
```c
#include <emmintrin.h>  // SSE2

void blit_simd(uint8_t* src, uint8_t* dst, int width, int height) {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x += 16) {
            __m128i src_pixels = _mm_loadu_si128((__m128i*)&src[x]);
            _mm_storeu_si128((__m128i*)&dst[x], src_pixels);
        }
        src += width;
        dst += screen_width;
    }
}
```

**이득**: 4-8배 빠름

### 11.3 알고리즘 최적화

**1. 더티 사각형**:
```c
typedef struct {
    int x, y, width, height;
} Rect;

Rect dirty_rects[MAX_SPRITES];
int dirty_count = 0;

void mark_dirty(int x, int y, int w, int h) {
    dirty_rects[dirty_count++] = {x, y, w, h};
}

void render_dirty_rects() {
    for (int i = 0; i < dirty_count; i++) {
        Rect r = dirty_rects[i];
        redraw_region(r.x, r.y, r.width, r.height);
    }
    dirty_count = 0;
}
```

**이득**: 전체 화면 대신 변경 영역만 갱신

**2. 스프라이트 배칭**:
```c
// 같은 텍스처의 스프라이트를 모아서 한 번에 그리기
void batch_sprites(Sprite* sprites, int count) {
    sort_by_texture(sprites, count);

    Texture* current_texture = NULL;

    for (int i = 0; i < count; i++) {
        if (sprites[i].texture != current_texture) {
            bind_texture(sprites[i].texture);
            current_texture = sprites[i].texture;
        }

        blit_sprite(&sprites[i]);
    }
}
```

**이득**: 텍스처 전환 최소화 (GPU)

---

## 12. 문제 해결

### 12.1 일반적인 문제

**1. 깜빡임 (Flickering)**

**원인**:
- 더블 버퍼링 없음
- VSync 미사용

**해결책**:
```c
// 백 버퍼에 그리기
draw_to_buffer(back_buffer);

// VSync 대기
while (inp(0x3DA) & 8);  // 수직 블랭킹 대기

// 플립
memcpy(vram, back_buffer, buffer_size);
```

**2. 잘못된 색상**

**원인**:
- Planar 변환 오류
- 팔레트 불일치

**디버깅**:
```python
def debug_planar_conversion():
    planar = [0xFF, 0x00, 0xFF, 0x00]

    for byte_idx in range(4):
        print(f"Plane {byte_idx}: {bin(planar[byte_idx])}")

    chunky = planar_to_chunky(planar)

    for pixel_idx in range(8):
        pixel = (chunky[pixel_idx // 2] >> (4 * (pixel_idx % 2))) & 0xF
        print(f"Pixel {pixel_idx}: {bin(pixel)}")
```

**3. 경계 아티팩트**

**원인**:
- 클리핑 오류
- 오프바이원 에러

**해결책**:
```c
// 철저한 경계 체크
assert(dst_x >= 0 && dst_x < screen_width);
assert(dst_y >= 0 && dst_y < screen_height);
assert(src_x >= 0 && src_x < sprite_width);
assert(src_y >= 0 && src_y < sprite_height);
```

**4. 성능 저하**

**원인**:
- 불필요한 블렌딩
- 과도한 오버드로우

**해결책**:
```c
// 알파 == 255일 때 블렌딩 건너뛰기
if (alpha == 255) {
    *dst = src;  // 단순 복사
} else if (alpha > 0) {
    *dst = blend(src, *dst, alpha);
}

// 오버드로우 최소화 (Z-order 정렬)
sort_sprites_by_z(sprites);
```

### 12.2 디버깅 기법

**1. 시각적 디버깅**:
```c
// 스프라이트 경계 그리기
void draw_sprite_debug(Sprite* sprite, int x, int y) {
    // 정상 블리팅
    blit_sprite(sprite, x, y);

    // 빨간 경계 그리기
    draw_rect(x, y, sprite->width, sprite->height, RED);

    // 중심점 표시
    draw_pixel(x + sprite->width/2, y + sprite->height/2, GREEN);
}

// 클리핑 영역 표시
void debug_clipping(int x, int y, int w, int h) {
    printf("Blit: (%d, %d) %dx%d\n", x, y, w, h);

    if (x < 0) printf("  CLIP LEFT: %d\n", -x);
    if (y < 0) printf("  CLIP TOP: %d\n", -y);
    if (x + w > SCREEN_WIDTH) printf("  CLIP RIGHT: %d\n", x + w - SCREEN_WIDTH);
    if (y + h > SCREEN_HEIGHT) printf("  CLIP BOTTOM: %d\n", y + h - SCREEN_HEIGHT);
}
```

**2. 메모리 덤프**:
```python
def dump_sprite_data(sprite, filename):
    """스프라이트 데이터를 hexdump 형식으로 저장"""
    with open(filename, 'w') as f:
        for y in range(sprite.height):
            offset = y * sprite.width
            hex_str = ' '.join(f'{b:02x}' for b in sprite.data[offset:offset+sprite.width])
            f.write(f'{y:04d}: {hex_str}\n')

def compare_buffers(expected, actual):
    """두 버퍼 비교 및 차이점 출력"""
    for i, (e, a) in enumerate(zip(expected, actual)):
        if e != a:
            print(f"Offset {i}: expected {e:02x}, got {a:02x}")
```

**3. 프로파일링**:
```javascript
function profileBlit() {
    const iterations = 1000;

    console.time('blit_simple');
    for (let i = 0; i < iterations; i++) {
        blitSimple(sprite, ctx, 100, 100);
    }
    console.timeEnd('blit_simple');

    console.time('blit_with_alpha');
    for (let i = 0; i < iterations; i++) {
        blitWithAlpha(sprite, ctx, 100, 100);
    }
    console.timeEnd('blit_with_alpha');
}
```

---

## 13. 참고 자료

### 13.1 관련 문서

**Double Dragon 프로젝트**:
- [01_RENDERING.md](../systems/01_RENDERING.md) - 렌더링 시스템 전체 개요
- [03_ANIMATION.md](../systems/03_ANIMATION.md) - 애니메이션 및 스프라이트 선택
- [SPRITE_FORMAT.md](../technical/SPRITE_FORMAT.md) - 스프라이트 파일 포맷
- [MODE2_COMPLETE_ANALYSIS.md](../function-analysis/MODE2_COMPLETE_ANALYSIS.md) - EGA 렌더링 상세
- [LZW_COMPRESSION.md](LZW_COMPRESSION.md) - 스프라이트 압축
- [RLE_COMPRESSION.md](RLE_COMPRESSION.md) - 스프라이트 스캔라인 압축

**함수 분석**:
- FUN_5f07 (1000:5f07) - CGA 블리팅
- FUN_29af (1000:29af) - EGA 블리팅
- FUN_0cd1 (1000:0cd1) - Planar-to-Chunky 변환

### 13.2 외부 참조

**하드웨어 문서**:
- [IBM CGA Technical Reference](https://archive.org/details/CGA_TechRef) (1981)
- [EGA/VGA Hardware Programming](http://www.osdever.net/FreeVGA/vga/vga.htm)
- [VGA Register Reference](http://www.osdever.net/FreeVGA/vga/vgareg.htm)

**알고리즘**:
- [Fast Bitmap Rotation and Scaling](https://www.drdobbs.com/windows/fast-bitmap-rotation-and-scaling/184416337) (Dr. Dobb's)
- [Transparency in Video Games](https://en.wikipedia.org/wiki/Transparency_(graphic))
- [Alpha Compositing](https://en.wikipedia.org/wiki/Alpha_compositing)

**코드 예제**:
- [DOSBox 소스 코드](https://github.com/dosbox-staging/dosbox-staging) - VGA 에뮬레이션
- [SDL2 Documentation](https://wiki.libsdl.org/SDL2/FrontPage) - 현대적 블리팅
- [FreeVGA Project](http://www.osdever.net/FreeVGA/home.htm) - VGA 프로그래밍

### 13.3 도구

**분석 도구**:
- [Ghidra](https://ghidra-sre.org/) - 리버스 엔지니어링
- [DOSBox Debugger](https://www.dosbox.com/wiki/Debugger) - 실시간 메모리 검사
- [GIMP](https://www.gimp.org/) - 스프라이트 시각화

**개발 도구**:
- [SDL2](https://www.libsdl.org/) - 크로스 플랫폼 그래픽
- [Emscripten](https://emscripten.org/) - 웹 포팅
- [PIL/Pillow](https://pillow.readthedocs.io/) - Python 이미지 처리

### 13.4 용어집

- **Blitting**: Block Image Transfer, 비트맵 데이터 고속 복사
- **Chunky Format**: 픽셀 데이터가 연속으로 저장된 포맷
- **Planar Format**: 색상 비트가 평면별로 분리된 포맷
- **Clipping**: 화면 경계 밖 부분 잘라내기
- **Z-ordering**: 깊이 순서 (뒤에서 앞으로)
- **VRAM**: Video RAM, 화면 출력용 메모리
- **VSync**: Vertical Sync, 수직 동기 신호
- **Double Buffering**: 2개 버퍼 사용으로 깜빡임 방지
- **Dirty Rectangle**: 변경된 화면 영역
- **Alpha Blending**: 투명도 기반 색상 혼합
- **Overdr**: 같은 픽셀을 여러 번 그리기

---

**작성 완료일**: 2025-11-24
**분석 함수 수**: 3개 (FUN_5f07, FUN_29af, FUN_0cd1)
**총 코드 크기**: 645 bytes
**문서 크기**: ~2,100 lines
