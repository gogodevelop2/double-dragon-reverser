# 스크롤 시스템 완전 분석

**작성일**: 2025-11-24
**Phase**: 4.6 완료 후속
**분석 함수**: 4개 (FUN_1000_81c6, _822e, _827b, _82f8)

---

## 🎯 개요

Phase 4.6에서 복구한 4개 스크롤 함수의 완전한 분석입니다. 이 함수들은 0x18c6 렌더링 점프 테이블의 엔트리 [1-4]에 위치하며, CGA 320×200 4색 모드에서 픽셀 레벨 스크롤을 구현합니다.

---

## 📊 4개 스크롤 함수

| 함수 | 주소 | 테이블 인덱스 | 방향 | 용도 |
|------|------|---------------|------|------|
| **FUN_1000_81c6** | 0x81c6 | [1] | ⬇️ DOWN | Y 증가, 아래 스크롤 |
| **FUN_1000_822e** | 0x822e | [2] | ⬆️ UP | Y 감소, 위 스크롤 |
| **FUN_1000_827b** | 0x827b | [3] | ➡️ RIGHT | X 증가, 오른쪽 스크롤 |
| **FUN_1000_82f8** | 0x82f8 | [4] | ⬅️ LEFT | X 감소, 왼쪽 스크롤 |

---

## 🔍 상세 분석

### 1. FUN_1000_81c6 - 스크롤 다운 (⬇️)

**주소**: 1000:81c6
**크기**: 100 bytes
**인덱스**: 0x18c6[1]

#### 코드
```c
void FUN_1000_81c6(void) {
    // 1. Y 좌표 증가
    *(int *)0xf398 = *(int *)0xf398 + 1;

    // 2. VRAM 오프셋 업데이트 (+240 bytes = 1 scanline)
    uVar1 = *(undefined2 *)0xf38c;
    *(int *)0xf38c = *(int *)0xf38c + 0xf0;

    // 3. Scanline 오프셋 업데이트 (+4)
    *(int *)0xf38e = *(int *)0xf38e + 4;

    // 4. Scanline 랩핑 체크 (160 scanlines)
    if (0x9f < *(int *)0xf38e) {
        *(int *)0xf38c = *(int *)0xf38c + -0x2580;  // -9600
        *(int *)0xf38e = *(int *)0xf38e + -0xa0;    // -160
    }

    // 5. 평면 오프셋 업데이트 (+16)
    *(int *)0xf394 = *(int *)0xf394 + 0x10;
    if (0x3f < *(int *)0xf394) {
        *(int *)0xf394 = *(int *)0xf394 + -0x40;  // -64
        *(int *)0xf392 = *(int *)0xf392 + *(int *)0x46;
    }

    // 6. 헬퍼 함수 호출
    func_0x00018351(uVar1);
    func_0x00018391();

    // 7. 스크롤 플래그 설정
    *(undefined1 *)0xf39e = 1;
}
```

#### 메모리 업데이트
```
0xf398 (Y scroll) :  +1
0xf38c (VRAM ptr) :  +0xf0 (240 bytes)
0xf38e (Scanline) :  +4
0xf394 (Plane)    :  +0x10 (16)
0xf39e (Flag)     :  = 1
```

#### CGA 메모리 구조
```
CGA 320×200 = 64,000 pixels
= 16,000 bytes (4 planes)
= 8,000 bytes per bank (odd/even)

1 scanline = 80 bytes
1 pixel row (4 planes) = 240 bytes (0xf0)
```

#### 동작 원리
1. **Y 좌표**: 픽셀 단위로 증가
2. **VRAM 포인터**: 다음 scanline으로 이동 (240 bytes)
3. **Scanline 카운터**: 4씩 증가 (CGA 인터레이스)
4. **랩핑**: 160 scanlines 도달 시 처음으로

---

### 2. FUN_1000_822e - 스크롤 업 (⬆️)

**주소**: 1000:822e
**크기**: 73 bytes
**인덱스**: 0x18c6[2]

#### 코드
```c
void FUN_1000_822e(void) {
    // 1. Y 좌표 감소
    *(int *)0xf398 = *(int *)0xf398 + -1;

    // 2. VRAM 오프셋 업데이트 (-240 bytes)
    *(int *)0xf38c = *(int *)0xf38c + -0xf0;

    // 3. Scanline 오프셋 업데이트 (-4)
    piVar1 = (int *)0xf38e;
    iVar2 = *piVar1;
    *piVar1 = *piVar1 + -4;

    // 4. Scanline 언더플로우 체크
    if (SBORROW2(iVar2,4) != *piVar1 < 0) {
        *(int *)0xf38c = *(int *)0xf38c + 0x2580;  // +9600
        *(int *)0xf38e = *(int *)0xf38e + 0xa0;    // +160
    }

    // 5. 평면 오프셋 업데이트 (-16)
    piVar1 = (int *)0xf394;
    iVar2 = *piVar1;
    *piVar1 = *piVar1 + -0x10;
    if (SBORROW2(iVar2,0x10) != *piVar1 < 0) {
        *(int *)0xf394 = *(int *)0xf394 + 0x40;  // +64
        *(int *)0xf392 = *(int *)0xf392 - *(int *)0x46;
    }

    // 6. 헬퍼 함수 호출
    func_0x00018351();
    func_0x00018391();

    // 7. 스크롤 플래그 설정
    *(undefined1 *)0xf39e = 1;
}
```

#### 메모리 업데이트
```
0xf398 (Y scroll) :  -1
0xf38c (VRAM ptr) :  -0xf0 (240 bytes)
0xf38e (Scanline) :  -4
0xf394 (Plane)    :  -0x10 (16)
0xf39e (Flag)     :  = 1
```

#### 동작 원리
- **DOWN의 역연산**: 모든 값이 반대 방향
- **언더플로우 처리**: 음수 되면 최대값으로 랩핑

---

### 3. FUN_1000_827b - 스크롤 오른쪽 (➡️)

**주소**: 1000:827b
**크기**: 121 bytes
**인덱스**: 0x18c6[3]

#### 코드
```c
void FUN_1000_827b(void) {
    // 1. X 좌표 증가
    *(int *)0xf396 = *(int *)0xf396 + 1;

    // 2. VRAM 오프셋 업데이트 (+1 byte)
    uVar1 = *(undefined2 *)0xf38e;
    *(int *)0xf38c = *(int *)0xf38c + 1;

    // 3. 카운터 업데이트 (+1)
    *(int *)0xf390 = *(int *)0xf390 + 1;

    // 4. 60픽셀마다 scanline 증가
    if (0x3b < *(int *)0xf390) {  // > 59
        *(undefined2 *)0xf390 = 0;
        *(int *)0xf38e = *(int *)0xf38e + 1;

        // 160 scanlines 랩핑
        if (0x9f < *(int *)0xf38e) {
            *(undefined2 *)0xf38c = 0xb0d0;
            *(undefined2 *)0xf38e = 0;
        }
    }

    // 5. 평면 오프셋 업데이트 (+1)
    *(int *)0xf394 = *(int *)0xf394 + 1;

    // 6. 4픽셀마다 평면 변경
    if ((*(uint *)0xf394 & 4) != 0) {
        *(int *)0xf394 = *(int *)0xf394 + -4;
        *(int *)0xf392 = *(int *)0xf392 + 2;
    }

    // 7. 헬퍼 함수 호출
    func_0x000183bd(uVar1);
    func_0x00018455();

    // 8. 스크롤 플래그 설정
    *(undefined1 *)0xf39e = 1;
}
```

#### 메모리 업데이트
```
0xf396 (X scroll) :  +1
0xf38c (VRAM ptr) :  +1 byte
0xf390 (Counter)  :  +1 (wrap at 60)
0xf38e (Scanline) :  +1 (every 60 pixels)
0xf394 (Plane)    :  +1 (adjust every 4 pixels)
0xf392 (Aux)      :  +2 (when plane wraps)
0xf39e (Flag)     :  = 1
```

#### 동작 원리

**CGA 수평 구조**:
```
320 pixels / 4 planes = 80 bytes per scanline
4 pixels share 1 byte (2 bits each)
60 visible pixels = 15 bytes
```

**60픽셀 카운터**:
- CGA는 80 bytes/scanline이지만 실제 표시는 60 pixels
- 60픽셀마다 다음 scanline으로

**4픽셀 평면 변경**:
- CGA 4-plane 구조
- 4픽셀마다 평면 전환
- Bit 2 체크 (& 4)로 평면 경계 감지

---

### 4. FUN_1000_82f8 - 스크롤 왼쪽 (⬅️)

**주소**: 1000:82f8
**크기**: 89 bytes
**인덱스**: 0x18c6[4]

#### 코드
```c
void FUN_1000_82f8(void) {
    // 1. X 좌표 감소
    *(int *)0xf396 = *(int *)0xf396 + -1;

    // 2. VRAM 오프셋 업데이트 (-1 byte)
    *(int *)0xf38c = *(int *)0xf38c + -1;

    // 3. 카운터 업데이트 (-1)
    piVar1 = (int *)0xf390;
    iVar2 = *piVar1;
    *piVar1 = *piVar1 + -1;

    // 4. 언더플로우 시 scanline 감소
    if (SBORROW2(iVar2,1) != *piVar1 < 0) {
        *(undefined2 *)0xf390 = 0x3b;  // = 59

        piVar1 = (int *)0xf38e;
        iVar2 = *piVar1;
        *piVar1 = *piVar1 + -1;

        if (SBORROW2(iVar2,1) != *piVar1 < 0) {
            *(undefined2 *)0xf38c = 0xd64f;
            *(undefined2 *)0xf38e = 0x9f;  // = 159
        }
    }

    // 5. 평면 오프셋 업데이트 (-1)
    *(int *)0xf394 = *(int *)0xf394 + -1;

    // 6. 4픽셀마다 평면 변경
    if ((*(uint *)0xf394 & 4) != 0) {
        *(int *)0xf394 = *(int *)0xf394 + 4;
        *(int *)0xf392 = *(int *)0xf392 + -2;
    }

    // 7. 헬퍼 함수 호출
    func_0x000183bd();
    func_0x00018455();

    // 8. 스크롤 플래그 설정
    *(undefined1 *)0xf39e = 1;
}
```

#### 메모리 업데이트
```
0xf396 (X scroll) :  -1
0xf38c (VRAM ptr) :  -1 byte
0xf390 (Counter)  :  -1 (wrap to 59)
0xf38e (Scanline) :  -1 (when counter underflows)
0xf394 (Plane)    :  -1 (adjust every 4 pixels)
0xf392 (Aux)      :  -2 (when plane wraps)
0xf39e (Flag)     :  = 1
```

#### 동작 원리
- **RIGHT의 역연산**: 모든 값이 반대 방향
- **언더플로우 처리**: 0 → 59, 평면 역순

---

## 🧩 통합 스크롤 시스템

### 메모리 맵

| 주소 | 크기 | 이름 | 용도 |
|------|------|------|------|
| **0xf396** | 2B | x_scroll | X 스크롤 위치 (픽셀) |
| **0xf398** | 2B | y_scroll | Y 스크롤 위치 (픽셀) |
| **0xf38c** | 2B | vram_offset | VRAM 포인터 오프셋 |
| **0xf38e** | 2B | scanline_offset | Scanline 카운터 (0~159) |
| **0xf390** | 2B | h_counter | 수평 카운터 (0~59) |
| **0xf392** | 2B | aux_vram | 보조 VRAM 포인터 |
| **0xf394** | 2B | plane_offset | 평면 오프셋 (0~63) |
| **0xf39e** | 1B | scroll_flag | 스크롤 발생 플래그 |

### 호출 그래프
```
FUN_1000_48e0 (렌더링 디스패처)
    │
    ├─[1]─> FUN_1000_81c6 (⬇️ DOWN)
    │           ├─> func_0x00018351()
    │           └─> func_0x00018391()
    │
    ├─[2]─> FUN_1000_822e (⬆️ UP)
    │           ├─> func_0x00018351()
    │           └─> func_0x00018391()
    │
    ├─[3]─> FUN_1000_827b (➡️ RIGHT)
    │           ├─> func_0x000183bd()
    │           └─> func_0x00018455()
    │
    └─[4]─> FUN_1000_82f8 (⬅️ LEFT)
                ├─> func_0x000183bd()
                └─> func_0x00018455()
```

### 헬퍼 함수

| 함수 | 사용처 | 용도 (추정) |
|------|--------|-------------|
| **func_0x00018351** | UP/DOWN | 수직 스크롤 화면 업데이트 |
| **func_0x00018391** | UP/DOWN | 수직 스크롤 완료 처리 |
| **func_0x000183bd** | RIGHT/LEFT | 수평 스크롤 화면 업데이트 |
| **func_0x00018455** | RIGHT/LEFT | 수평 스크롤 완료 처리 |

---

## 🎮 CGA 스크롤 최적화

### CGA 320×200 4색 메모리 구조
```
Total: 64,000 pixels = 16,000 bytes

4 color planes:
  Plane 0: 4,000 bytes (bits 0-1 of each pixel)
  Plane 1: 4,000 bytes (bits 2-3 of each pixel)
  Plane 2: 4,000 bytes (bits 4-5 of each pixel)
  Plane 3: 4,000 bytes (bits 6-7 of each pixel)

Interlaced banks:
  Even scanlines: 0xB8000 ~ 0xB9F3F (8,000 bytes)
  Odd scanlines:  0xBA000 ~ 0xBBF3F (8,000 bytes)

1 scanline = 80 bytes = 320 pixels / 4 bits per pixel
```

### 스크롤 성능 최적화

#### 수직 스크롤 (UP/DOWN)
```c
// VRAM 포인터만 업데이트 (메모리 복사 없음)
vram_offset += 240;  // 1 scanline = 240 bytes (4 planes)

// 장점:
// - O(1) 시간 복잡도
// - 메모리 복사 불필요
// - 즉각 반응
```

#### 수평 스크롤 (RIGHT/LEFT)
```c
// 1 바이트씩 이동 + 4픽셀마다 평면 전환
vram_offset += 1;
plane_offset = (plane_offset + 1) % 64;

// 60픽셀마다 scanline 변경
if (++h_counter > 59) {
    h_counter = 0;
    scanline_offset++;
}

// 장점:
// - 픽셀 레벨 정밀도
// - 부드러운 스크롤
```

---

## 💡 핵심 발견

### 1. 포인터 기반 스크롤
- **메모리 복사 없음**: VRAM 포인터만 조작
- **O(1) 복잡도**: 화면 크기와 무관
- **즉각 반응**: 프레임 드랍 없음

### 2. CGA 평면 처리
- **4-plane 구조**: 각 평면 독립 처리
- **4픽셀 단위**: 1 byte = 4 pixels (2 bits each)
- **평면 전환**: bit 2 체크로 경계 감지

### 3. 랩핑 시스템
- **수직**: 160 scanlines
- **수평**: 60 pixels
- **순환 버퍼**: 화면 경계에서 자동 랩핑

### 4. 플래그 시스템
- **0xf39e = 1**: 스크롤 발생
- **메인 루프**: 플래그 확인 후 화면 업데이트
- **프레임 동기**: 스크롤과 렌더링 분리

---

## 🔧 C++ 재구현 가이드

### 구조체 정의
```cpp
struct ScrollState {
    int16_t x_scroll;        // 0xf396
    int16_t y_scroll;        // 0xf398
    int16_t vram_offset;     // 0xf38c
    int16_t scanline_offset; // 0xf38e
    int16_t h_counter;       // 0xf390
    int16_t aux_vram;        // 0xf392
    int16_t plane_offset;    // 0xf394
    bool    scroll_flag;     // 0xf39e
};
```

### 함수 정의
```cpp
class ScrollSystem {
public:
    void scrollDown();   // FUN_1000_81c6
    void scrollUp();     // FUN_1000_822e
    void scrollRight();  // FUN_1000_827b
    void scrollLeft();   // FUN_1000_82f8

private:
    ScrollState state;

    void updateVertical(int delta);
    void updateHorizontal(int delta);
    void wrapScanline();
    void wrapPlane();
};
```

### 현대 그래픽 적용
```cpp
// CGA → 현대 프레임버퍼 변환
void renderFrame() {
    int vram_x = state.vram_offset % 80;
    int vram_y = state.scanline_offset;

    for (int y = 0; y < 200; y++) {
        for (int x = 0; x < 320; x++) {
            int src_x = (x + state.x_scroll) % 320;
            int src_y = (y + state.y_scroll) % 200;

            // CGA 평면에서 픽셀 읽기
            uint8_t color = readCGAPixel(src_x, src_y);

            // 현대 프레임버퍼에 쓰기
            framebuffer[y * 320 + x] = color;
        }
    }
}
```

---

## 📊 성능 분석

### 시간 복잡도
- **UP/DOWN**: O(1) - 포인터 업데이트만
- **RIGHT/LEFT**: O(1) - 포인터 + 카운터 업데이트
- **전체**: O(1) - 화면 크기 무관

### 메모리 사용
- **상태 변수**: 16 bytes (8개 변수)
- **VRAM**: 16,000 bytes (CGA 전체)
- **총합**: ~16KB

### CPU 사이클 (추정)
- **UP/DOWN**: ~50 사이클
- **RIGHT/LEFT**: ~70 사이클
- **60 FPS**: 여유 있음 (4.77 MHz 8088)

---

## 🎓 역사적 의의

### 1988년 기준 최적화
1. **메모리 효율**: 포인터 조작으로 복사 최소화
2. **CPU 효율**: O(1) 알고리즘
3. **부드러운 스크롤**: 픽셀 레벨 정밀도
4. **CGA 최적화**: 4-plane 구조 완벽 활용

이는 1988년 DOS 게임 중에서도 **상당히 고급 기술**입니다.

---

**분석 완료일**: 2025-11-24
**다음 분석**: func_0x00018351, func_0x00018391, func_0x000183bd, func_0x00018455
**참고 문서**: [RENDERING_SYSTEM.md](../technical/RENDERING_SYSTEM.md), [MEMORY_MAP.md](../technical/MEMORY_MAP.md)
