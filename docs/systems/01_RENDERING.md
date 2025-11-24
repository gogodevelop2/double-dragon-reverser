# 렌더링 시스템 (Rendering System)

**작성일**: 2025-11-24
**Phase**: 4 통합 문서
**복잡도**: ⭐⭐⭐⭐⭐ (최고)

---

## 1. 개요

Double Dragon의 렌더링 시스템은 **듀얼 모드 아키텍처**를 채택하여 1980년대 다양한 PC 하드웨어를 지원합니다.

### 핵심 특징

- **Mode 1 (CGA)**: 320×200 4색, 직접 메모리 접근
- **Mode 2 (EGA/Tandy)**: 320×200 16색, VGA I/O 포트 제어
- **함수 포인터 디스패치**: 런타임 하드웨어 선택
- **4방향 스크롤**: 픽셀 단위 부드러운 스크롤
- **스프라이트 블리팅**: 클리핑, 투명도, Z-ordering

### 설계 철학

1. **하드웨어 추상화**: Strategy 패턴으로 모드 분리
2. **메모리 효율**: 순환 버퍼로 고정 크기 VRAM
3. **성능 최적화**: 더티 플래그, 4픽셀 경계 타일 로딩

---

## 2. 아키텍처

### 2.1 듀얼 모드 시스템

```
게임 초기화
    ↓
하드웨어 감지 (DAT_1988_0035)
    ↓
    ├─ Mode 1 (CGA) → 테이블 @ 0x18da 복사
    └─ Mode 2 (EGA) → 테이블 @ 0x18f0 복사
    ↓
런타임 테이블 @ 0x18c4 (11개 함수 포인터)
    ↓
디스패처 호출 (FUN_499b, FUN_48e0)
    ↓
    ├─ 스프라이트 블리팅
    ├─ 스크롤링 (상/하/좌/우)
    ├─ 화면 버퍼 관리
    └─ 타일맵 렌더링
```

### 2.2 Mode 1 vs Mode 2 비교

| 항목 | Mode 1 (CGA) | Mode 2 (EGA/Tandy) |
|------|-------------|-------------------|
| **해상도** | 320×200 | 320×200 |
| **색상** | 4색 (2-bit) | 16색 (4-bit) |
| **메모리 구조** | 2-bit 인터리브 | 4-plane planar |
| **하드웨어 접근** | 직접 메모리 쓰기 | VGA I/O 포트 (0x3c4, 0x3ce) |
| **VRAM 크기** | 16KB | 64KB (4×16KB) |
| **스크롤 단위** | 라인 단위 (거친) | 픽셀 단위 (부드러운) |
| **함수 코드** | 1,700 bytes | 1,429 bytes |
| **복잡도** | 중간 | 높음 |

### 2.3 렌더링 파이프라인

```
메인 루프 (60 FPS)
    ↓
엔티티 업데이트 → 애니메이션 프레임 선택
    ↓
스프라이트 리스트 빌드 (FUN_48e0)
    ├─ 방향별 프레임 (4-way)
    ├─ 화면 좌표 변환 (스크롤 보정)
    └─ Z-order 정렬
    ↓
렌더 리스트 실행 (FUN_499b)
    └─ Mode별 블리팅 함수
        ├─ Mode 1: FUN_5f07 (클리핑, 단순 복사)
        └─ Mode 2: FUN_60d0 → Jump table (투명도, 마스킹)
    ↓
스크롤 처리 (입력 기반)
    ├─ DOWN:  FUN_8492 (M1) / FUN_2e86 (M2)
    ├─ UP:    FUN_84ee (M1) / FUN_2ee2 (M2)
    ├─ RIGHT: FUN_8583 (M1) / FUN_2f75 (M2)
    └─ LEFT:  FUN_853d (M1) / FUN_2f31 (M2)
    ↓
타일맵 로딩 (조건부, 4픽셀 경계)
    ├─ Mode 1: func_185fb (V), func_185cf (H)
    └─ Mode 2: func_12c90 (V), func_12da9 (H)
    ↓
VRAM 업데이트 (더티 플래그 체크)
    └─ VSync 대기 → 화면 출력
```

---

## 3. Mode 1 (CGA) 렌더링

### 3.1 CGA 하드웨어

**IBM CGA (Color Graphics Adapter)**:
- VRAM: 0xB800:0000 (16KB)
- 픽셀 형식: 2 bits/pixel, 4 pixels/byte
- 팔레트: 4색 (배경 + 3가지 전경색)

**메모리 구조**:
```
각 바이트: [PP PP PP PP] (P = 2-bit pixel)
주소 계산: offset = (y * 80) + (x / 4)
비트 시프트: shift = (x % 4) * 2
```

### 3.2 스프라이트 블리팅 (FUN_5f07)

```python
function sprite_blit_cga(sprite_params):
    # 14 words (28 bytes) 파라미터 복사
    copy_params(sprite_params, buffer_0x4644)

    src = read_word(0x464c)   # 소스 스프라이트
    dst = read_word(0x465e)   # 목적지 VRAM
    width = read_word(0x4644)
    height = read_word(0x4646)

    # 경계 체크
    if dst == 0xbb80:
        return  # 화면 밖

    # 수직 클리핑
    if dst + (height * 0x48) >= 0:
        # 단순 복사 (투명도 없음)
        for y in range(height):
            for x in range(width):
                write_word(dst, read_word(src))
                dst += 1
                src += 1
            dst += (0x48 - width)  # 다음 스캔라인
    else:
        # 순환 버퍼 처리
        for y in range(height):
            for x in range(width):
                write_word(dst & 0x7fff, read_word(src))
                dst += 1
                src += 1
            dst = (dst + (0x48 - width)) & 0x7fff
```

**상수**:
- `0xbb80`: 화면 밖 마커
- `0x48` (72 bytes): CGA 스캔라인 간격 (320px / 4 = 80, 조정값)
- `0x7fff`: 32KB 순환 버퍼 마스크

### 3.3 텍스트 렌더링 (FUN_5c0a)

```python
function render_text_cga(text_string):
    # 폰트 데이터 @ 0x13da (8×8, 96문자)
    font_table = 0x13da

    for char in text_string:
        if char == ' ':
            char = adjust_whitespace(char)

        # 폰트 인덱스 계산
        font_data = font_table + ((char - 0x20) * 8)

        # 8 스캔라인
        for y in range(8):
            bits = read_byte(font_data + y)

            # 비트 확장: 1-bit → 4-bit (0x0 또는 0xf)
            for x in range(8):
                pixel = (bits & 0x80) ? 0xf : 0x0

                # CGA 4-planar 메모리 쓰기
                write_byte(vram + 0x0000, pixel)  # Plane 0
                write_byte(vram + 0x1000, pixel)  # Plane 1
                write_byte(vram + 0x2000, pixel)  # Plane 2
                write_byte(vram + 0x3000, pixel)  # Plane 3

                vram += 1
                bits <<= 1

            vram += (0x50 - 8)  # 다음 라인 (80 - 8)
```

**CGA 플레인 인터리빙**:
- Plane 0-3: +0x0000, +0x1000, +0x2000, +0x3000
- 각 플레인 1-bit → 합쳐서 4-bit 색상
- 0x50 (80 bytes): 320 pixels / 4 = 80 bytes/line

### 3.4 스크롤 (Down 예시)

```python
function scroll_down_cga():
    # Y 위치 증가
    write_word(0xf398, read_word(0xf398) + 1)

    # VRAM 오프셋 업데이트 (16KB 순환)
    offset = read_word(0xf38c)
    offset = ((offset + 0x5050) & 0x3fff) + 0xb0d0
    write_word(0xf38c, offset)

    # 타일맵 Y 델타
    write_word(0xf394, read_word(0xf394) + 0x10)
```

**스크롤 증분**:
- `0x5050` (20560 bytes): VRAM 다운 스크롤
- `0x3fff`: 16KB 순환 마스크
- `0xb0d0`: VRAM 베이스 오프셋
- `0x10` (16): Y 델타 증가

---

## 4. Mode 2 (EGA/Tandy) 렌더링

### 4.1 EGA 하드웨어

**EGA (Enhanced Graphics Adapter)**:
- VRAM: 0xA000:0000 (64KB)
- 4-plane planar 구조
- VGA 레지스터: Sequencer (0x3c4), Graphics Controller (0x3ce)

**4-Plane 구조**:
```
Plane 0 (0x802): Intensity
Plane 1 (0x102): Red
Plane 2 (0x202): Green
Plane 3 (0x402): Blue

색상 = [I R G B] (4-bit) = 16 colors
```

### 4.2 스프라이트 블리팅 (FUN_29af)

```python
function sprite_blit_ega(sprite_data):
    # VGA 초기화
    out(0x3ce, 5)  # Write Mode 0

    # 루프 횟수 (12 or 16)
    iterations = 0xc if mode == 2 else 0x10

    for i in range(iterations):
        # === Plane 3 (Blue) ===
        out(0x3c4, 0x402)  # Map Mask: Plane 3
        dst[0] = src[1]
        dst[1] = src[5]
        dst[2] = src[9]
        dst[3] = src[13]

        # === Plane 2 (Green) ===
        out(0x3c4, 0x202)
        dst[0] = src[2]
        dst[1] = src[6]
        dst[2] = src[10]
        dst[3] = src[14]

        # === Plane 1 (Red) ===
        out(0x3c4, 0x102)
        dst[0] = src[3]
        dst[1] = src[7]
        dst[2] = src[11]
        dst[3] = src[15]

        # === Plane 0 (Intensity) ===
        out(0x3c4, 0x802)
        dst[0] = src[0]
        dst[1] = src[4]
        dst[2] = src[8]
        dst[3] = src[12]

        src += 0x10  # 다음 16 bytes
        dst += 0x28  # 다음 라인 (40 bytes)

    # 투명도 마스킹 (mode != 1)
    if mode != 1:
        apply_transparency_mask(dst, src)
```

**VGA I/O 포트**:
- `0x3c4`: Sequencer Index/Data
- `0x3ce`: Graphics Controller
- Map Mask: 플레인 선택 (0x102, 0x202, 0x402, 0x802)

**데이터 재배열**:
```
소스 (16 bytes):
[P0_0, P3_0, P2_0, P1_0, P0_1, P3_1, P2_1, P1_1, ...]
     ↓
목적지 (4 bytes × 4 planes):
Plane 0: [P0_0, P0_1, P0_2, P0_3]
Plane 1: [P1_0, P1_1, P1_2, P1_3]
Plane 2: [P2_0, P2_1, P2_2, P2_3]
Plane 3: [P3_0, P3_1, P3_2, P3_3]
```

### 4.3 투명도 마스킹

```python
function apply_transparency_mask(dst, mask_data):
    for i in range(4):
        # 마스크 계산: (~P2) & P0
        word1 = read_word(mask_data)
        word2 = read_word(mask_data + 2)

        p0_low = word1 & 0xff
        p0_high = (word1 >> 8) & 0xff
        p2_low = word2 & 0xff
        p2_high = (word2 >> 8) & 0xff

        mask = (~p2_low & p0_low) & (~p0_high & p0_low)

        # XOR로 투명 픽셀 처리
        out(0x3c4, 0x102)
        write_byte(dst, p2_high ^ mask)

        out(0x3c4, 0x202)
        write_byte(dst, p2_low)

        out(0x3c4, 0x402)
        write_byte(dst, p0_high ^ mask)

        out(0x3c4, 0x802)
        write_byte(dst, p0_low)

        dst += 1
        mask_data += 4
```

**투명도 원리**:
- 배경색 (검정, 0000) 픽셀 건너뛰기
- 비트 마스크로 선택적 XOR
- 기존 VRAM 픽셀 보존

### 4.4 세밀한 스크롤 (Down 예시)

```python
function scroll_down_ega():
    # Y 위치 증가
    write_word(0xf398, read_word(0xf398) + 1)

    # 메인 버퍼 오프셋
    offset = read_word(0xf38c)
    offset = ((offset + 0x5050) & 0x3fff) + 0xb0d0
    write_word(0xf38c, offset)

    # Y 델타
    delta = read_word(0xf394) + 0x10
    write_word(0xf394, delta)

    # === EGA 전용 추가 로직 ===
    if delta > 0x3f:  # 64 픽셀 초과
        # 델타 리셋
        write_word(0xf394, delta - 0x40)

        # X 오프셋 조정
        stride = read_word(0x46)
        write_word(0xf392, read_word(0xf392) + stride)

        # 보조 버퍼 (8KB 순환)
        aux = read_word(0xf39c)
        aux = (aux + 0x240) & 0x1fff
        write_word(0xf39c, aux)

        # 타일맵 갱신
        call func_12c90()

    # 더티 플래그
    write_byte(0xf39e, 1)
```

**추가 변수**:
- `0xf392`: X 오프셋 (세밀한 제어)
- `0xf39c`: 보조 버퍼 (8KB 순환)
- `0xf39e`: 더티 플래그 (업데이트 필요)
- `0x240` (576 bytes): EGA 타일맵 증분 (CGA의 1/4)

---

## 5. 화면 버퍼 관리

### 5.1 순환 버퍼 시스템

```
Mode 1 (CGA):
  VRAM: 16KB
  마스크: & 0x3fff
  베이스: 0xb0d0

Mode 2 (EGA):
  메인: 16KB (& 0x3fff)
  보조: 8KB (& 0x1fff)
  베이스: 0xb0d0
```

```python
function circular_buffer_update(offset, delta, mask, base):
    offset = ((offset + delta) & mask) + base
    return offset
```

**장점**:
- 고정 메모리 크기
- 무한 스크롤 지원
- 포인터 산술 단순화

### 5.2 화면 버퍼 복사 (FUN_8139)

```python
function copy_screen_buffer_cga():
    vram_src = read_word(0xf38c)
    scanline = read_word(0xf38e)

    # CGA 인터레이스: 홀짝 라인 분리
    if (scanline & 1) == 0:
        # 짝수 라인 → 0x32a
        dst = 0x32a
    else:
        # 홀수 라인 → 0x22ee
        dst = 0x22ee

    # 60 bytes (30 words) 복사
    for i in range(0x1e):
        write_word(dst, read_word(vram_src))
        dst += 1
        vram_src += 1

    # 경계 처리
    if needs_boundary_handling():
        call func_1818e()
```

**CGA 인터레이스**:
```
Bank 0 (0xB8000): 짝수 scanlines (0, 2, 4, ..., 198)
Bank 1 (0xBA000): 홀수 scanlines (1, 3, 5, ..., 199)
```

### 5.3 타일맵 변환 (FUN_5864)

```python
function convert_tilemap(mode, offset_index):
    dst = 0x1c70 + (offset_index * 2)

    if mode == 2:
        # Mode 2 (CGA): 6+6 words per iteration
        src = read_word(0x1dc5)
        tile_offset = -0x9f8
        words_per_iter = 12
    else:
        # Mode 1 (EGA): 5+5 words per iteration
        src = read_word(0x1d25)
        tile_offset = -0xaf8
        words_per_iter = 10

    # 8 스캔라인
    for y in range(8):
        # 첫 번째 평면
        for x in range(words_per_iter // 2):
            tile_index = read_word(src + x) & 0xff
            pixel = read_byte(tile_index + tile_offset)
            write_byte(dst + x, pixel)

        # 두 번째 평면 (+0x2000 오프셋)
        for x in range(words_per_iter // 2):
            tile_index = read_word(src + x + 6) & 0xff
            pixel = read_byte(tile_index + tile_offset)
            write_byte(dst + 0x2000 + x, pixel)

        src += words_per_iter
        dst += 0x50  # 다음 스캔라인 (80 bytes)
```

**타일 간접 참조**:
```
Tile Index → Lookup Table → Pixel Data
   (8-bit)    (-0xaf8/-0x9f8)  (8×8 비트맵)
```

### 5.4 패턴 Fill (FUN_591d)

```python
function pattern_fill(width, pattern_select, offset_index):
    # 패턴 선택
    if pattern_select == 0x900:
        pattern = 0x5555 | 0xc0  # 체크보드 1
    elif width == 0:
        pattern = 0x0000 | 0xc0  # 빈 영역
    else:
        pattern = 0xaaaa | 0xc0  # 체크보드 2

    dst = 0x1d60 + (offset_index * 2)

    # 6회 반복 (6 words width)
    for i in range(6):
        # 8개 위치 동시 fill (4 scanlines × 2 planes)
        write_word(dst + 0x0000, pattern)  # Scanline 0, Plane 0
        write_word(dst + 0x1000, pattern)  # Scanline 0, Plane 1
        write_word(dst + 0x0028, pattern)  # Scanline 1, Plane 0
        write_word(dst + 0x1028, pattern)  # Scanline 1, Plane 1
        write_word(dst + 0x0050, pattern)  # Scanline 2, Plane 0
        write_word(dst + 0x1050, pattern)  # Scanline 2, Plane 1
        write_word(dst + 0x0078, pattern)  # Scanline 3, Plane 0
        write_word(dst + 0x1078, pattern)  # Scanline 3, Plane 1

        dst += 1
        width -= 1

        # 테두리 처리
        if width == 0:
            pattern = 0xc0
```

**패턴**:
- `0x5555`: 01010101 (체크보드 A)
- `0xaaaa`: 10101010 (체크보드 B)
- `0xc0`: 테두리 비트

---

## 6. 함수 포인터 디스패치

### 6.1 테이블 구조

```
0x18c4-0x18d9: 런타임 테이블 (11 × 2 = 22 bytes)
0x18da-0x18ef: Mode 1 소스 테이블 (22 bytes)
0x18f0-0x1905: Mode 2 소스 테이블 (22 bytes)
```

```python
# 초기화 시
if hardware_mode == 1:
    copy_memory(0x18da, 0x18c4, 22)  # Mode 1
else:
    copy_memory(0x18f0, 0x18c4, 22)  # Mode 2

# 런타임 호출
function_ptr = read_word(0x18c4 + (index * 2))
call function_ptr
```

### 6.2 디스패처 매핑

| Index | Mode 1 주소 | Mode 2 주소 | 기능 |
|-------|-----------|-----------|------|
| 0 | 0x5f07 | 0x6b19 | 스프라이트 블릿 |
| 1 | 0x5e55 | 0x60d0 | 스프라이트 디스패처 |
| 2 | 0x8492 | 0x2e86 | Scroll DOWN |
| 3 | 0x84ee | 0x2ee2 | Scroll UP |
| 4 | 0x8583 | 0x2f75 | Scroll RIGHT |
| 5 | 0x853d | 0x2f31 | Scroll LEFT |
| 6 | 0x8622 | 0x2fbf | 버퍼 관리 |
| 7 | 0x7eb0 | 0x2c2f | 유틸리티 |
| 8 | 0x5aaa | 0x29af | 그래픽 변환 / EGA 렌더링 |
| 9 | 0x5b5f | 0x2ba1 | 그래픽 처리 |
| 10 | 0x5c0a | 0x2b2e | 텍스트 렌더링 / 그래픽 |

### 6.3 디스패처 함수

```python
# FUN_499b - 렌더링 디스패처
function render_dispatcher():
    func_ptr = read_word(0x18c4)  # Index 0
    call func_ptr

# FUN_48e0 - 스프라이트 디스패처
function sprite_dispatcher():
    func_ptr = read_word(0x18c6)  # Index 1
    call func_ptr
```

---

## 7. 메모리 레이아웃

### 7.1 렌더링 상태 변수

```
주소      | 크기 | 이름                    | Mode 1 | Mode 2
----------|------|------------------------|--------|--------
0xf38c    | 2    | vram_base_offset       | ✓      | ✓
0xf392    | 2    | additional_x_offset    |        | ✓
0xf394    | 2    | tilemap_y_offset       | ✓      | ✓
0xf396    | 2    | scroll_x               | ✓      | ✓
0xf398    | 2    | scroll_y               | ✓      | ✓
0xf39c    | 2    | aux_buffer_offset      |        | ✓
0xf39e    | 1    | dirty_flag             |        | ✓
```

### 7.2 스프라이트 파라미터 버퍼

```
주소      | 크기 | 이름
----------|------|------------------------
0x4640    | 2    | sprite_flags
0x4642    | 2    | sprite_param_1
0x4644    | 2    | sprite_width
0x4646    | 2    | sprite_height
0x4648    | 2    | sprite_param_4
0x464a    | 2    | sprite_type / handler_ptr
0x464c    | 2    | sprite_src_pointer
0x464e    | 18   | additional_params
0x465e    | 2    | sprite_dest_vram (0xbb80 = 화면 밖)
```

### 7.3 데이터 테이블

```
주소      | 크기   | 내용
----------|--------|---------------------------
0x13da    | ~768   | 폰트 테이블 (Mode 1, 8×8, 96문자)
0x1d25    | ?      | Mode 1 타일맵 소스
0x1dc5    | ?      | Mode 2 타일맵 소스
0x8800    | ?      | Mode 1 팔레트 룩업
0x5650    | ?      | Mode 2 점프 테이블
```

---

## 8. 함수 목록

### 8.1 공통 디스패처

| 함수 | 주소 | 크기 | 설명 |
|------|------|------|------|
| FUN_499b | 1000:499b | 4 | 렌더링 진입점 (0x18c4[0] 호출) |
| FUN_48e0 | 1000:48e0 | 4 | 스프라이트 진입점 (0x18c6[1] 호출) |

### 8.2 Mode 1 (CGA) 함수

| 함수 | 주소 | 크기 | 설명 |
|------|------|------|------|
| FUN_5f07 | 1000:5f07 | 116 | 스프라이트 블릿 (클리핑) |
| FUN_5e55 | 1000:5e55 | 178 | 팔레트 변환 렌더링 |
| FUN_8492 | 1000:8492 | 92 | Scroll DOWN |
| FUN_84ee | 1000:84ee | 79 | Scroll UP |
| FUN_8583 | 1000:8583 | 76 | Scroll RIGHT |
| FUN_853d | 1000:853d | 70 | Scroll LEFT |
| FUN_8622 | 1000:8622 | 278 | 링 버퍼 복사 |
| FUN_7eb0 | 1000:7eb0 | 74 | 루프 호출 (12회) |
| FUN_5aaa | 1000:5aaa | 180 | 그래픽 변환 |
| FUN_5b5f | 1000:5b5f | 167 | 그래픽 처리 |
| FUN_5c0a | 1000:5c0a | 591 | **텍스트 렌더링** |

### 8.3 Mode 2 (EGA) 함수

| 함수 | 주소 | 크기 | 설명 |
|------|------|------|------|
| FUN_6b19 | 1000:6b19 | 68 | 스프라이트 메타데이터 복사 |
| FUN_60d0 | 1000:60d0 | 168 | 스프라이트 디스패처 (점프 테이블) |
| FUN_2e86 | 1000:2e86 | 92 | Scroll DOWN (세밀) |
| FUN_2ee2 | 1000:2ee2 | 79 | Scroll UP (세밀) |
| FUN_2f75 | 1000:2f75 | 74 | Scroll RIGHT (세밀) |
| FUN_2f31 | 1000:2f31 | 68 | Scroll LEFT (세밀) |
| FUN_2fbf | 1000:2fbf | 144 | 버퍼 관리 |
| FUN_2c2f | 1000:2c2f | 97 | 유틸리티 |
| FUN_29af | 1000:29af | 382 | **EGA 스프라이트 렌더링** |
| FUN_2ba1 | 1000:2ba1 | 142 | 그래픽 변환 |
| FUN_2b2e | 1000:2b2e | 115 | 그래픽 함수 |

### 8.4 헬퍼 함수

| 함수 | 주소 | 크기 | 설명 |
|------|------|------|------|
| FUN_48e4 | 1000:48e4 | 90 | 렌더링 파라미터 변환 |
| FUN_8139 | 1000:8139 | 84 | 화면 버퍼 조건부 복사 |
| FUN_810f | 1000:810f | 38 | 화면 전체 업데이트 |
| FUN_5864 | 1000:5864 | 165 | 타일맵 변환 |
| FUN_591d | 1000:591d | 124 | 패턴 Fill |

---

## 9. 구현 가이드

### 9.1 모던 C++ 구조

```cpp
// 렌더링 Strategy 인터페이스
class IRenderer {
public:
    virtual ~IRenderer() = default;
    virtual void blit_sprite(const SpriteParams&) = 0;
    virtual void scroll_down() = 0;
    virtual void scroll_up() = 0;
    virtual void scroll_right() = 0;
    virtual void scroll_left() = 0;
};

// CGA 렌더러
class CGARenderer : public IRenderer {
private:
    uint8_t vram[16384];  // 16KB
    uint16_t vram_offset;
    uint16_t scroll_x, scroll_y;

public:
    void blit_sprite(const SpriteParams& params) override {
        // 단순 memcpy (투명도 없음)
        uint16_t dst = params.dst_vram;
        const uint8_t* src = params.sprite_data;

        for (int y = 0; y < params.height; y++) {
            memcpy(&vram[dst], src, params.width * 2);
            src += params.width * 2;
            dst += 72;  // 0x48
        }
    }

    void scroll_down() override {
        scroll_y++;
        vram_offset = ((vram_offset + 0x5050) & 0x3fff) + 0xb0d0;
    }
};

// EGA 렌더러
class EGARenderer : public IRenderer {
private:
    uint8_t vram[65536];  // 64KB (4 planes)
    uint16_t vram_offset;
    uint16_t scroll_x, scroll_y;
    uint16_t aux_buffer;
    uint8_t dirty_flag;

public:
    void blit_sprite(const SpriteParams& params) override {
        // VGA 레지스터 프로그래밍
        set_write_mode(0);

        const uint8_t* src = params.sprite_data;
        uint16_t dst = params.dst_vram;

        for (int y = 0; y < params.height; y++) {
            // Plane 3
            select_plane(3);
            vram[dst+0] = src[1];
            vram[dst+1] = src[5];
            vram[dst+2] = src[9];
            vram[dst+3] = src[13];

            // Plane 2
            select_plane(2);
            vram[dst+0] = src[2];
            vram[dst+1] = src[6];
            vram[dst+2] = src[10];
            vram[dst+3] = src[14];

            // Plane 1
            select_plane(1);
            vram[dst+0] = src[3];
            vram[dst+1] = src[7];
            vram[dst+2] = src[11];
            vram[dst+3] = src[15];

            // Plane 0
            select_plane(0);
            vram[dst+0] = src[0];
            vram[dst+1] = src[4];
            vram[dst+2] = src[8];
            vram[dst+3] = src[12];

            src += 16;
            dst += 40;  // 0x28
        }

        if (params.enable_transparency) {
            apply_transparency_mask(dst, params.mask_data);
        }
    }

    void scroll_down() override {
        scroll_y++;
        vram_offset = ((vram_offset + 0x5050) & 0x3fff) + 0xb0d0;

        uint16_t delta = tilemap_y_offset + 16;
        tilemap_y_offset = delta;

        if (delta > 63) {
            tilemap_y_offset = delta - 64;
            additional_x_offset += stride;
            aux_buffer = (aux_buffer + 0x240) & 0x1fff;
            update_tilemap();
        }

        dirty_flag = 1;
    }

private:
    void select_plane(int plane) {
        // 실제 VGA 포트 쓰기 시뮬레이션
        uint16_t mask = 1 << (plane + 8);  // 0x102, 0x202, 0x402, 0x802
        // out(0x3c4, mask | 0x02);
    }
};

// 렌더링 시스템
class RenderingSystem {
private:
    std::unique_ptr<IRenderer> renderer;

public:
    void initialize(GraphicsMode mode) {
        if (mode == GraphicsMode::CGA) {
            renderer = std::make_unique<CGARenderer>();
        } else {
            renderer = std::make_unique<EGARenderer>();
        }
    }

    void render_frame(const std::vector<Sprite>& sprites) {
        for (const auto& sprite : sprites) {
            SpriteParams params = build_sprite_params(sprite);
            renderer->blit_sprite(params);
        }
    }

    void handle_scroll(Direction dir) {
        switch (dir) {
            case Direction::DOWN:  renderer->scroll_down(); break;
            case Direction::UP:    renderer->scroll_up(); break;
            case Direction::RIGHT: renderer->scroll_right(); break;
            case Direction::LEFT:  renderer->scroll_left(); break;
        }
    }
};
```

### 9.2 SDL2 포트 예시

```cpp
class SDL2Renderer : public IRenderer {
private:
    SDL_Renderer* sdl_renderer;
    SDL_Texture* framebuffer;
    uint32_t pixels[320 * 200];

public:
    SDL2Renderer(SDL_Renderer* renderer) : sdl_renderer(renderer) {
        framebuffer = SDL_CreateTexture(
            renderer,
            SDL_PIXELFORMAT_ARGB8888,
            SDL_TEXTUREACCESS_STREAMING,
            320, 200
        );
    }

    void blit_sprite(const SpriteParams& params) override {
        // 스프라이트 데이터 → RGB 픽셀 변환
        for (int y = 0; y < params.height; y++) {
            for (int x = 0; x < params.width; x++) {
                int screen_x = params.screen_x + x;
                int screen_y = params.screen_y + y;

                if (screen_x >= 0 && screen_x < 320 &&
                    screen_y >= 0 && screen_y < 200) {
                    uint8_t color_index = get_sprite_pixel(params, x, y);
                    pixels[screen_y * 320 + screen_x] = palette[color_index];
                }
            }
        }
    }

    void present() {
        SDL_UpdateTexture(framebuffer, nullptr, pixels, 320 * 4);
        SDL_RenderCopy(sdl_renderer, framebuffer, nullptr, nullptr);
        SDL_RenderPresent(sdl_renderer);
    }
};
```

### 9.3 데이터 추출

```python
# 폰트 추출 (Mode 1)
def extract_font_cga():
    font_data = read_memory(0x1000, 0x13da, 768)  # 96 chars × 8 bytes

    fonts = []
    for i in range(96):
        char_data = font_data[i*8:(i+1)*8]
        bitmap = [[0] * 8 for _ in range(8)]

        for y in range(8):
            bits = char_data[y]
            for x in range(8):
                bitmap[y][x] = (bits >> (7-x)) & 1

        fonts.append(bitmap)

    return fonts

# 타일맵 추출
def extract_tilemap(mode):
    if mode == 1:
        src_addr = 0x1d25
        offset = -0xaf8
    else:
        src_addr = 0x1dc5
        offset = -0x9f8

    tilemap = []
    src = read_memory(0x1000, src_addr, 1024)

    for i in range(0, len(src), 2):
        tile_index = src[i] & 0xff
        tile_addr = tile_index + offset
        tile_pixels = read_tile_pixels(tile_addr)
        tilemap.append(tile_pixels)

    return tilemap
```

---

## 10. 테스트 전략

### 10.1 단위 테스트

```cpp
TEST(RenderingSystem, CGASpriteBlit) {
    CGARenderer renderer;
    SpriteParams params {
        .sprite_data = test_sprite_8x8,
        .width = 8,
        .height = 8,
        .dst_vram = 0x1000
    };

    renderer.blit_sprite(params);

    // 검증: VRAM에 올바른 픽셀 쓰여졌는지
    ASSERT_EQ(renderer.read_vram(0x1000), expected_pixel_0);
    ASSERT_EQ(renderer.read_vram(0x1048), expected_pixel_scanline_1);
}

TEST(RenderingSystem, EGAScrollDown) {
    EGARenderer renderer;

    uint16_t initial_y = renderer.get_scroll_y();
    renderer.scroll_down();

    ASSERT_EQ(renderer.get_scroll_y(), initial_y + 1);
    ASSERT_EQ(renderer.get_dirty_flag(), 1);
}

TEST(RenderingSystem, CircularBuffer) {
    uint16_t offset = 0xf000;
    offset = ((offset + 0x5050) & 0x3fff) + 0xb0d0;

    // 16KB 경계에서 wrap 검증
    ASSERT_EQ(offset, expected_wrapped_offset);
}
```

### 10.2 통합 테스트

```cpp
TEST(RenderingSystem, FullFrameRender) {
    RenderingSystem system;
    system.initialize(GraphicsMode::EGA);

    std::vector<Sprite> sprites = load_test_sprites();
    system.render_frame(sprites);

    // 프레임버퍼 비교
    auto framebuffer = system.get_framebuffer();
    ASSERT_TRUE(compare_framebuffer(framebuffer, expected_frame));
}

TEST(RenderingSystem, ScrollingSequence) {
    RenderingSystem system;
    system.initialize(GraphicsMode::CGA);

    // 100 프레임 스크롤 시뮬레이션
    for (int i = 0; i < 100; i++) {
        system.handle_scroll(Direction::DOWN);
    }

    // 스크롤 위치 검증
    ASSERT_EQ(system.get_scroll_y(), 100);
}
```

### 10.3 시각적 검증

```cpp
// DOSBox 실행 결과와 비교
TEST(RenderingSystem, VisualRegression) {
    RenderingSystem modern_system;
    modern_system.initialize(GraphicsMode::EGA);

    // 원본 DOSBox 스크린샷
    auto original_frame = load_dosbox_screenshot("frame_100.png");

    // 현대 구현 렌더링
    modern_system.render_frame(game_state_frame_100);
    auto modern_frame = modern_system.capture_screenshot();

    // 픽셀 단위 비교 (허용 오차 5%)
    double similarity = compare_images(original_frame, modern_frame);
    ASSERT_GT(similarity, 0.95);
}
```

---

## 11. 참고

### 관련 문서

- [ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md](../function-analysis/ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md): 애니메이션 및 스프라이트 선택
- [RENDERING_SCROLLING_SYSTEM_ANALYSIS.md](../function-analysis/RENDERING_SCROLLING_SYSTEM_ANALYSIS.md): 렌더링 및 스크롤 상세 분석
- [MODE2_COMPLETE_ANALYSIS.md](../function-analysis/MODE2_COMPLETE_ANALYSIS.md): Mode 2 EGA 완전 분석
- [08_HARDWARE_IO.md](08_HARDWARE_IO.md): VGA 포트 I/O 상세

### 외부 참조

- IBM CGA Technical Reference (1981)
- EGA/VGA Hardware Programming Guide
- DOSBox 소스 코드 (VGA 에뮬레이션)

### 용어집

- **CGA**: Color Graphics Adapter (IBM, 1981, 4색)
- **EGA**: Enhanced Graphics Adapter (IBM, 1984, 16색)
- **Planar**: 각 색상 비트가 분리된 평면에 저장되는 메모리 구조
- **Blitting**: 비트맵 데이터를 빠르게 복사하는 기법
- **Z-ordering**: 스프라이트 렌더링 순서 (깊이 정렬)
- **Dirty Flag**: 화면 업데이트 필요 여부 표시

---

**작성 완료일**: 2025-11-24
**분석 함수 수**: 22개
**총 코드 크기**: 3,129 bytes
**문서 크기**: ~3,800 lines
