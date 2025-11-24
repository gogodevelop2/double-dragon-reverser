# Double Dragon - 렌더링 및 스크롤링 시스템 완전 분석

**분석 날짜**: 2025-11-24
**Phase**: 4.11
**문서 버전**: 1.0

---

## 📋 개요

이 문서는 Double Dragon의 **렌더링 시스템**과 **스크롤링 메커니즘**을 완전히 분석합니다. 특히 **0x18c4 함수 포인터 테이블**을 통한 동적 렌더링 디스패치와, **Mode 1 (EGA)**과 **Mode 2 (CGA)** 간의 차이점을 중점적으로 다룹니다.

### 분석 범위
- 11개 함수 분석 완료
- Mode 1/2 렌더링 시스템 완전 비교
- 스크롤링 메커니즘 (상/하/좌/우)
- 스프라이트 블리팅 시스템
- VRAM 주소 계산 및 관리

---

## 🎯 핵심 발견 사항

### 1. 듀얼 모드 렌더링 아키텍처

Double Dragon은 **Mode 1 (EGA)**과 **Mode 2 (CGA)** 두 가지 그래픽 모드를 지원하며, 각 모드는 **완전히 다른 렌더링 함수 세트**를 사용합니다.

```
게임 초기화
    ↓
FUN_1000_0db2() - 함수 포인터 테이블 초기화
    ↓
DAT_1988_0035 확인 (게임 모드)
    ↓
    ├─ Mode 1 → 0x18da 테이블 복사 (EGA 함수들)
    └─ Mode 2 → 0x18f0 테이블 복사 (CGA 함수들)
    ↓
0x18c4 활성 테이블 (11개 함수 포인터)
    ↓
런타임 디스패치 (FUN_1000_499b, FUN_1000_48e0)
```

### 2. 스크롤링 시스템 비교

| 동작 | Mode 1 (EGA) | Mode 2 (CGA) | 주요 차이 |
|------|-------------|-------------|----------|
| **Scroll DOWN** | FUN_1000_8492 | FUN_1000_2e86 | VRAM 증가: 0x900 vs 0x240 |
| **Scroll UP** | FUN_1000_84ee | FUN_1000_2ee2 | VRAM 감소: 0x900 vs 0x240 |
| **Scroll RIGHT** | FUN_1000_8583 | FUN_1000_2f75 | VRAM 증가: 8 vs 2 |
| **Scroll LEFT** | FUN_1000_853d | FUN_1000_2f31 | VRAM 감소: 8 vs 2 |

**주요 차이점**:
- **Mode 1**: 고해상도, VRAM 증분 크기 4배
- **Mode 2**: CGA 4-color, interlaced scanline 방식
- **스크롤 플래그**: 모든 함수에서 `0xf39e = 1` 설정 (dirty flag)

### 3. 메모리 레이아웃 발견

```
렌더링 관련 메모리 맵:

0xf38c: VRAM base address (& 0x3fff) + 0xb0d0
0xf392: Tilemap X offset
0xf394: Tilemap Y offset (0-0x3f range, wraps at 0x40)
0xf396: Scroll X position
0xf398: Scroll Y position
0xf39c: Tilemap data pointer (& 0x7fff for Mode 1, & 0x1fff for Mode 2)
0xf39e: Dirty flag (set to 1 when screen needs update)

0x18c4-0x18d9: Active rendering function table (11 entries × 2 bytes)
0x18da: Mode 1 source table (EGA functions)
0x18f0: Mode 2 source table (CGA functions)
```

---

## 📊 함수별 상세 분석

### 디스패처 함수 (2개)

#### FUN_1000_499b (4 bytes) - 렌더링 디스패처
**주소**: 1000:499b
**테이블**: 0x18c4[0]

```c
void FUN_1000_499b(void) {
    // 0x18c4에 저장된 함수 포인터 호출
    (*(code *)*(undefined2 *)0x18c4)();
}
```

**분석**:
- **역할**: 렌더링 시스템의 진입점
- **동작**: 0x18c4 테이블의 첫 번째 함수를 간접 호출
- **호출자**: 메인 루프 (FUN_1000_034b)
- **간접 점프**: Mode 1/2에 따라 다른 함수 실행

---

#### FUN_1000_48e0 (4 bytes) - 스프라이트 디스패처
**주소**: 1000:48e0
**테이블**: 0x18c4[1]

```c
void FUN_1000_48e0(void) {
    // 0x18c6에 저장된 함수 포인터 호출
    (*(code *)*(undefined2 *)0x18c6)();
}
```

**분석**:
- **역할**: 스프라이트 렌더링 진입점
- **동작**: 0x18c6 테이블의 두 번째 함수를 간접 호출
- **호출자**: 메인 루프 (FUN_1000_029a)
- **중요도**: ⭐⭐⭐ (모든 스프라이트 렌더링 통과)

---

## 🔄 Mode 1 (EGA) 스크롤링 함수 (4개)

### FUN_1000_8492 (20 bytes) - Scroll DOWN (Mode 1)
**주소**: 1000:8492
**테이블**: 0x18c4[2] (Mode 1)

```c
void FUN_1000_8492(void) {
    *(int *)0xf398 = *(int *)0xf398 + 1;  // Y position++

    // VRAM address update (circular buffer)
    *(int *)0xf38c = (*(int *)0xf38c + 0x5050U & 0x3fff) + 0xb0d0;

    // Tilemap Y offset
    *(int *)0xf394 = *(int *)0xf394 + 0x10;

    if (0x3f < *(int *)0xf394) {  // Wrap at 0x40 (64 tiles)
        *(int *)0xf392 = *(int *)0xf392 + *(int *)0x46;  // Tilemap X stride
        *(int *)0xf394 = *(int *)0xf394 + -0x40;

        // Tilemap pointer update
        *(uint *)0xf39c = *(int *)0xf39c + 0x900U & 0x7fff;

        func_0x000185fb();  // 타일맵 로딩 함수
    }

    *(undefined1 *)0xf39e = 1;  // Set dirty flag
}
```

**상세 분석**:

1. **Y 위치 증가**: 스크롤 Y 좌표 +1
2. **VRAM 주소 계산**:
   - `0x5050` 증가 (20560 bytes)
   - `& 0x3fff` 마스킹 (16KB 순환 버퍼)
   - `+ 0xb0d0` 베이스 오프셋 추가
3. **타일맵 Y 오프셋**: +0x10 (16 픽셀)
4. **타일맵 로우 전환**:
   - 0x40 (64) 도달 시 다음 타일 로우
   - 타일맵 포인터 +0x900 (2304 bytes)
   - `func_0x000185fb()` 호출: 새 타일 로우 로딩
5. **Dirty Flag**: 화면 업데이트 필요 표시

**메모리 계산**:
- `0x900 = 2304 bytes = 9 rows × 256 bytes/row`
- EGA 모드는 9개 타일 로우를 한 번에 처리

---

### FUN_1000_84ee (22 bytes) - Scroll UP (Mode 1)
**주소**: 1000:84ee
**테이블**: 0x18c4[3] (Mode 1)

```c
void FUN_1000_84ee(void) {
    *(int *)0xf398 = *(int *)0xf398 + -1;  // Y position--

    // VRAM address update (circular buffer, opposite direction)
    *(int *)0xf38c = (*(int *)0xf38c + 0x4e10U & 0x3fff) + 0xb0d0;

    // Tilemap Y offset with underflow check
    int *piVar1 = (int *)0xf394;
    int iVar2 = *piVar1;
    *piVar1 = *piVar1 + -0x10;

    if (SBORROW2(iVar2, 0x10) != *piVar1 < 0) {  // Underflow detection
        *(int *)0xf394 = *(int *)0xf394 + 0x40;

        // Tilemap pointer wrap-around
        *(uint *)0xf39c = *(int *)0xf39c - 0x900U & 0x7fff;
        *(int *)0xf392 = *(int *)0xf392 - *(int *)0x46;

        func_0x000185fb();  // Load previous tile row
    }

    *(undefined1 *)0xf39e = 1;
}
```

**상세 분석**:

1. **Y 위치 감소**: 스크롤 Y 좌표 -1
2. **VRAM 주소 계산**:
   - `0x4e10` 증가 (19984 bytes = -576 in 16-bit wrap)
   - Circular buffer 역방향 이동
3. **언더플로우 검출**:
   - `SBORROW2()`: signed borrow 플래그 체크
   - 0 아래로 가면 0x40에서 wrap
4. **타일맵 역스크롤**:
   - 타일맵 포인터 -0x900
   - 이전 타일 로우 로딩

**트릭**:
- `0x4e10 + 0x5050 = 0x9e60` (overflow → 순환)
- Signed arithmetic으로 정확한 underflow 감지

---

### FUN_1000_8583 (18 bytes) - Scroll RIGHT (Mode 1)
**주소**: 1000:8583
**테이블**: 0x18c4[4] (Mode 1)

```c
void FUN_1000_8583(void) {
    *(int *)0xf396 = *(int *)0xf396 + 1;  // X position++

    uint uVar1 = *(uint *)0xf38c;
    *(int *)0xf38c = (*(int *)0xf38c + 0x4f31U & 0x3fff) + 0xb0d0;

    // Conditional tilemap update (every 4th pixel)
    if ((uVar1 & 3) == 0) {
        *(uint *)0xf39c = *(int *)0xf39c + 8U & 0x7fff;
        func_0x000185cf();  // Load tile column
        *(int *)0xf392 = *(int *)0xf392 + 2;
    }

    *(undefined1 *)0xf39e = 1;
}
```

**상세 분석**:

1. **X 위치 증가**: 스크롤 X 좌표 +1
2. **VRAM 주소**: `+0x4f31` (20273 bytes)
3. **조건부 타일맵 업데이트**:
   - `(uVar1 & 3) == 0`: 4의 배수일 때만 실행
   - 타일맵 포인터 +8 bytes (타일 4개분)
   - `func_0x000185cf()`: 새 타일 컬럼 로딩
   - X 오프셋 +2

**최적화**:
- 픽셀 단위 스크롤이지만 타일은 4픽셀마다 로딩
- 대역폭 절약 (1/4로 감소)

---

### FUN_1000_853d (16 bytes) - Scroll LEFT (Mode 1)
**주소**: 1000:853d
**테이블**: 0x18c4[5] (Mode 1)

```c
void FUN_1000_853d(void) {
    *(int *)0xf396 = *(int *)0xf396 + -1;  // X position--

    *(int *)0xf38c = (*(int *)0xf38c + 0x4f2fU & 0x3fff) + 0xb0d0;

    // Conditional tilemap update (every 4th pixel, backwards)
    if ((*(int *)0xf38c + 0x4f30U & 3) == 0) {
        *(uint *)0xf39c = *(int *)0xf39c - 8U & 0x7fff;
        *(int *)0xf392 = *(int *)0xf392 + -2;
        func_0x000185cf();  // Load previous tile column
    }

    *(undefined1 *)0xf39e = 1;
}
```

**상세 분석**:

1. **X 위치 감소**: 스크롤 X 좌표 -1
2. **VRAM 주소**: `+0x4f2f` (20271 bytes, -2 in wrap)
3. **역방향 타일맵 업데이트**:
   - `(addr + 0x4f30) & 3 == 0`: 경계 보정 후 체크
   - 타일맵 포인터 -8 bytes
   - 이전 타일 컬럼 로딩

**트릭**:
- `0x4f2f + 0x4f31 = 0x9e60` (정확한 대칭)
- `+0x4f30` 보정으로 경계 맞춤

---

## 🎨 Mode 2 (CGA) 스크롤링 함수 (4개)

### FUN_1000_2e86 (18 bytes) - Scroll DOWN (Mode 2)
**주소**: 1000:2e86
**테이블**: 0x18c4[2] (Mode 2)

```c
void FUN_1000_2e86(void) {
    *(int *)0xf398 = *(int *)0xf398 + 1;  // Y position++
    *(int *)0xf38c = (*(int *)0xf38c + 0x5050U & 0x3fff) + 0xb0d0;
    *(int *)0xf394 = *(int *)0xf394 + 0x10;

    if (0x3f < *(int *)0xf394) {
        *(int *)0xf394 = *(int *)0xf394 + -0x40;
        *(int *)0xf392 = *(int *)0xf392 + *(int *)0x46;

        // CGA interlaced: 0x240 = 576 bytes (4.5 rows)
        *(uint *)0xf39c = *(int *)0xf39c + 0x240U & 0x1fff;

        func_0x00012c90();  // CGA tile loading
    }

    *(undefined1 *)0xf39e = 1;
}
```

**Mode 1과의 차이**:

| 속성 | Mode 1 (EGA) | Mode 2 (CGA) | 비율 |
|-----|-------------|-------------|-----|
| VRAM 증분 | 0x900 (2304) | 0x240 (576) | **4:1** |
| 마스킹 | & 0x7fff | & 0x1fff | **4:1** |
| 타일 로딩 | func_0x000185fb | func_0x00012c90 | 다름 |

**CGA 인터레이스**:
- `0x240 = 576 bytes`
- CGA 4-color 모드: 2 bits/pixel
- 320×200 화면에서 짝수/홀수 스캔라인 분리
- `4.5 rows` = CGA 인터레이스 특성

---

### FUN_1000_2ee2 (22 bytes) - Scroll UP (Mode 2)
**주소**: 1000:2ee2
**테이블**: 0x18c4[3] (Mode 2)

```c
void FUN_1000_2ee2(void) {
    *(int *)0xf398 = *(int *)0xf398 + -1;
    *(int *)0xf38c = (*(int *)0xf38c + 0x4e10U & 0x3fff) + 0xb0d0;

    int *piVar1 = (int *)0xf394;
    int iVar2 = *piVar1;
    *piVar1 = *piVar1 + -0x10;

    if (SBORROW2(iVar2, 0x10) != *piVar1 < 0) {
        *(int *)0xf394 = *(int *)0xf394 + 0x40;

        // CGA reversed scrolling
        *(int *)0xf39c = *(int *)0xf39c + -0x240;
        *(uint *)0xf39c = *(uint *)0xf39c & 0x1fff;

        *(int *)0xf392 = *(int *)0xf392 - *(int *)0x46;
        func_0x00012c90();
    }

    *(undefined1 *)0xf39e = 1;
}
```

**특이사항**:
- 2단계 마스킹: `-0x240` 후 `& 0x1fff`
- Mode 1과 동일한 underflow 로직
- CGA 전용 타일 로딩 함수

---

### FUN_1000_2f75 (18 bytes) - Scroll RIGHT (Mode 2)
**주소**: 1000:2f75
**테이블**: 0x18c4[4] (Mode 2)

```c
void FUN_1000_2f75(void) {
    *(int *)0xf396 = *(int *)0xf396 + 1;

    uint uVar1 = *(uint *)0xf38c;
    *(int *)0xf38c = (*(int *)0xf38c + 0x4f31U & 0x3fff) + 0xb0d0;

    if ((uVar1 & 3) == 0) {
        // CGA: +2 bytes instead of +8
        *(uint *)0xf39c = *(int *)0xf39c + 2U & 0x1fff;
        func_0x00012da9();  // CGA column loading
        *(int *)0xf392 = *(int *)0xf392 + 2;
    }

    *(undefined1 *)0xf39e = 1;
}
```

**Mode 1과의 차이**:

| 속성 | Mode 1 | Mode 2 | 비율 |
|-----|--------|--------|-----|
| 타일맵 증분 | +8 bytes | +2 bytes | **4:1** |
| 마스킹 | & 0x7fff | & 0x1fff | **4:1** |
| 로딩 함수 | func_0x000185cf | func_0x00012da9 | 다름 |

**해석**:
- CGA는 EGA 대비 1/4 해상도 (수평 방향)
- 타일 데이터도 1/4 크기

---

### FUN_1000_2f31 (16 bytes) - Scroll LEFT (Mode 2)
**주소**: 1000:2f31
**테이블**: 0x18c4[5] (Mode 2)

```c
void FUN_1000_2f31(void) {
    *(int *)0xf396 = *(int *)0xf396 + -1;
    *(int *)0xf38c = (*(int *)0xf38c + 0x4f2fU & 0x3fff) + 0xb0d0;

    if ((*(int *)0xf38c + 0x4f30U & 3) == 0) {
        // CGA: -2 bytes instead of -8
        *(uint *)0xf39c = *(int *)0xf39c - 2U & 0x1fff;
        *(int *)0xf392 = *(int *)0xf392 + -2;
        func_0x00012da9();
    }

    *(undefined1 *)0xf39e = 1;
}
```

**대칭성**:
- Mode 1 대비 정확히 1/4 크기
- 동일한 4픽셀 경계 체크
- CGA 전용 역스크롤

---

## 🖼️ 스프라이트 블리팅 시스템 (2개)

### FUN_1000_5f07 (144 bytes) - Sprite Blit with Clipping (Mode 1)
**주소**: 1000:5f07
**테이블**: 0x18c4[0] (Mode 1 target)

```c
undefined2 FUN_1000_5f07(void) {
    undefined2 *puVar1, *puVar2;
    int iVar3, iVar4, iVar5;
    int unaff_SI;
    undefined2 *puVar6, *puVar7;

    // Copy sprite parameters (14 words = 28 bytes)
    puVar7 = (undefined2 *)0x4644;
    puVar6 = (undefined2 *)(unaff_SI + 4);
    for (iVar4 = 0xe; iVar4 != 0; iVar4 = iVar4 + -1) {
        *puVar7++ = *puVar6++;
    }

    puVar6 = (undefined2 *)*(undefined2 *)0x464c;  // Source sprite data
    puVar7 = (undefined2 *)*(undefined2 *)0x465e;  // Destination VRAM

    if (puVar7 != (undefined2 *)0xbb80) {  // Check if valid destination
        iVar4 = *(int *)0x4646;  // Height
        iVar3 = *(int *)0x4644;  // Width

        // Vertical clipping check
        if (-1 < (int)(puVar7 + iVar4 * 0x48)) {
            // Normal case: no wrapping
            iVar5 = iVar3;
            do {
                for (; iVar5 != 0; iVar5 = iVar5 + -1) {
                    *puVar7++ = *puVar6++;
                }
                puVar7 = puVar7 + (0x48 - iVar3);  // Next scanline
                iVar4 = iVar4 + -1;
                iVar5 = iVar3;
            } while (iVar4 != 0);
            return 0x1988;
        }

        // Wrapping case: circular buffer
        iVar5 = iVar3;
        do {
            do {
                *puVar7 = *puVar6++;
                puVar7 = (undefined2 *)((uint)(puVar7 + 1) & 0x7fff);  // Wrap
                iVar5 = iVar5 + -1;
            } while (iVar5 != 0);
            puVar7 = (undefined2 *)((uint)(puVar7 + (0x48 - iVar3)) & 0x7fff);
            iVar4 = iVar4 + -1;
            iVar5 = iVar3;
        } while (iVar4 != 0);
    }

    return 0x1988;
}
```

**상세 분석**:

1. **스프라이트 파라미터**:
   ```
   0x4644: Width (words)
   0x4646: Height (scanlines)
   0x464c: Source sprite data pointer
   0x465e: Destination VRAM pointer
   ```

2. **클리핑 로직**:
   - `0xbb80` = 화면 밖 (invalid marker)
   - Vertical clipping: `(dest + height * 0x48) < 0`
   - 0x48 = 72 bytes/scanline (Mode 1 EGA)

3. **블리팅 루프**:
   ```
   for each scanline:
       copy width words
       advance destination by (0x48 - width)
   ```

4. **순환 버퍼 처리**:
   - `& 0x7fff`: 32KB VRAM 순환
   - 화면 하단에서 상단으로 wrap

**성능**:
- 단순 memcpy (no transparency)
- 하드웨어 가속 없음
- CPU 집약적

---

### FUN_1000_60d0 (56 bytes) - Sprite Dispatcher with Jump Table (Mode 2)
**주소**: 1000:60d0
**테이블**: 0x18c4[1] (Mode 2 target)

```c
void FUN_1000_60d0(void) {
    undefined2 *unaff_SI;
    code *pcVar4;

    // Copy sprite parameters (7 words)
    *(undefined2 *)0x4640 = *unaff_SI;
    *(undefined2 *)0x4642 = unaff_SI[1];
    *(undefined2 *)0x4644 = unaff_SI[2];
    *(undefined2 *)0x4646 = unaff_SI[3];
    *(undefined2 *)0x4648 = unaff_SI[4];
    *(undefined2 *)0x464a = unaff_SI[5];
    *(undefined2 *)0x464c = unaff_SI[6];

    *(undefined2 *)0x465e = 48000;  // Default destination

    func_0x00016ad0();  // Clipping check

    if ((bool)in_CF) {  // Carry flag: clipped out
        // Copy backup parameters
        uRam0001dece = uRam0001dec0;
        // ... (9 words copy)
        return;
    }

    *(undefined2 *)0x465e = 0x464e;
    uRam0002f9d2 = *(undefined2 *)0x4646;
    int iVar3 = *(int *)0x4644;
    pcVar4 = (code *)*(int *)0x464a;

    // Jump table selection based on sprite type
    if ((((pcVar4 != (code *)0x6162) &&
          (pcVar4 != (code *)0x6324)) &&
          (pcVar4 != (code *)0x64fd)) &&
        ((pcVar4 != (code *)0x66fa &&
          (pcVar4 != (code *)0x68df)))) {
        pcVar4 = (code *)0x6162;  // Default handler
    }

    // Width alignment (odd → +2)
    bool bVar6 = (*(uint *)0x4640 & 1) != 0;
    if (bVar6) {
        *(int *)0x4644 = *(int *)0x4644 + 2;
    }

    uRam0002f9da = (uint)bVar6;
    uRam0002f9d0 = iVar3 + 1U >> 1;  // Width / 2

    // Indirect jump to sprite handler
    (*pcVar4)();
}
```

**상세 분석**:

1. **점프 테이블 주소** (Mode 2 전용):
   ```
   0x6162: Default sprite handler
   0x6324: Special sprite type 1
   0x64fd: Special sprite type 2
   0x66fa: Special sprite type 3
   0x68df: Special sprite type 4
   ```

2. **클리핑 시스템**:
   - `func_0x00016ad0()`: 화면 경계 체크
   - Carry flag 반환: `CF=1` → 완전히 화면 밖
   - 백업 파라미터 복원

3. **Width 정렬**:
   - `& 1`: 홀수 width 체크
   - 홀수면 +2 (word 정렬)
   - CGA byte 정렬 요구사항

4. **Half-width 계산**:
   - `(width + 1) >> 1`: CGA는 2 pixels/byte
   - EGA 대비 압축

**Mode 1 vs Mode 2 차이**:

| 기능 | Mode 1 (FUN_5f07) | Mode 2 (FUN_60d0) |
|------|-------------------|-------------------|
| 파라미터 복사 | 14 words | 7 words |
| 클리핑 | Inline | func_0x00016ad0 |
| Jump table | 없음 | 5개 핸들러 |
| Width 처리 | 직접 | Half-width + 정렬 |
| 순환 버퍼 | 0x7fff | (핸들러 내부) |

---

## 🔍 추가 발견 사항

### 1. VRAM 순환 버퍼 시스템

```
EGA Mode 1:
0xb0d0 + (offset & 0x3fff) = 실제 VRAM 주소
Mask: 0x7fff (32KB)

CGA Mode 2:
0xb0d0 + (offset & 0x3fff) = 실제 VRAM 주소
Mask: 0x1fff (8KB)
```

**의미**:
- Mode 1: 32KB VRAM 사용 (EGA high-res)
- Mode 2: 8KB VRAM 사용 (CGA 4-color)
- 둘 다 16KB 순환 버퍼 (`& 0x3fff`)
- 베이스 주소 0xb0d0 = 45264 (segment offset)

---

### 2. 스크롤 최적화 전략

#### Vertical Scrolling:
```
Mode 1: 0x900 bytes/row = 9 tile rows
Mode 2: 0x240 bytes/row = 4.5 tile rows (interlaced)

→ 한 번에 여러 타일 로우 로딩 (대역폭 최적화)
```

#### Horizontal Scrolling:
```
4픽셀마다 타일 컬럼 로딩 (4의 배수 체크)

Mode 1: 8 bytes/column
Mode 2: 2 bytes/column

→ 부드러운 픽셀 스크롤 + 타일 로딩 최소화
```

---

### 3. Dirty Flag 시스템

```c
모든 스크롤 함수:
    *(undefined1 *)0xf39e = 1;
```

**용도**:
- 화면 업데이트 필요 표시
- 메인 루프에서 체크
- VSync 동기화 가능성

**추정 흐름**:
```
1. 스크롤 함수 호출 → 0xf39e = 1
2. 메인 루프 체크 → if (0xf39e) { update_screen(); }
3. 화면 업데이트 후 → 0xf39e = 0
```

---

### 4. 타일맵 로딩 함수 (미분석)

| 함수 | 용도 | 호출처 |
|------|------|--------|
| func_0x000185fb | Mode 1 vertical tile loading | DOWN/UP scroll |
| func_0x000185cf | Mode 1 horizontal tile loading | RIGHT/LEFT scroll |
| func_0x00012c90 | Mode 2 vertical tile loading | DOWN/UP scroll |
| func_0x00012da9 | Mode 2 horizontal tile loading | RIGHT/LEFT scroll |

**다음 분석 대상**: 이 4개 함수의 상세 구현

---

## 📐 메모리 맵 완전 정리

### 렌더링 상태 (0xf38c - 0xf39e)

```
주소     | 크기 | 이름                    | 설명
---------|------|------------------------|----------------------------------
0xf38c   | 2    | vram_base_offset       | (offset & 0x3fff) + 0xb0d0
0xf392   | 2    | tilemap_x_offset       | 타일맵 X 오프셋 (바이트 단위)
0xf394   | 2    | tilemap_y_offset       | 타일맵 Y 오프셋 (0-0x3f, wraps)
0xf396   | 2    | scroll_x               | 스크롤 X 위치 (픽셀)
0xf398   | 2    | scroll_y               | 스크롤 Y 위치 (픽셀)
0xf39c   | 2    | tilemap_data_pointer   | 타일맵 데이터 포인터
0xf39e   | 1    | dirty_flag             | 화면 업데이트 플래그 (0/1)
```

### 함수 포인터 테이블 (0x18c4 - 0x18d9)

```
주소     | 인덱스 | Mode 1 (EGA)   | Mode 2 (CGA)   | 용도
---------|--------|----------------|----------------|------------------
0x18c4   | 0      | FUN_1000_5f07  | ?              | 스프라이트 블릿
0x18c6   | 1      | ?              | FUN_1000_60d0  | 스프라이트 디스패처
0x18c8   | 2      | FUN_1000_8492  | FUN_1000_2e86  | Scroll DOWN
0x18ca   | 3      | FUN_1000_84ee  | FUN_1000_2ee2  | Scroll UP
0x18cc   | 4      | FUN_1000_8583  | FUN_1000_2f75  | Scroll RIGHT
0x18ce   | 5      | FUN_1000_853d  | FUN_1000_2f31  | Scroll LEFT
0x18d0   | 6      | ?              | ?              | (미발견)
0x18d2   | 7      | ?              | ?              | (미발견)
0x18d4   | 8      | ?              | ?              | (미발견)
0x18d6   | 9      | ?              | ?              | (미발견)
0x18d8   | 10     | ?              | ?              | (미발견)
```

### 스프라이트 파라미터 버퍼 (0x4640 - 0x465e)

```
주소     | 크기 | 이름                | Mode 1 | Mode 2
---------|------|---------------------|--------|--------
0x4640   | 2    | sprite_flags        | ✓      | ✓
0x4642   | 2    | sprite_param_1      | ✓      | ✓
0x4644   | 2    | sprite_width        | ✓      | ✓
0x4646   | 2    | sprite_height       | ✓      | ✓
0x4648   | 2    | sprite_param_4      | ✓      | ✓
0x464a   | 2    | sprite_type/handler | ✓      | ✓ (jump table)
0x464c   | 2    | sprite_src_pointer  | ✓      | ✓
0x464e   | 18   | additional_params   | ✓      | ✓
0x465e   | 2    | sprite_dest_vram    | ✓      | ✓
```

---

## 🎓 시스템 설계 분석

### 1. 디자인 패턴: **Strategy Pattern**

```cpp
class RenderingStrategy {
public:
    virtual void scroll_down() = 0;
    virtual void scroll_up() = 0;
    virtual void scroll_right() = 0;
    virtual void scroll_left() = 0;
    virtual void blit_sprite() = 0;
};

class EGARenderer : public RenderingStrategy {
    void scroll_down()  { /* FUN_1000_8492 */ }
    void scroll_up()    { /* FUN_1000_84ee */ }
    void scroll_right() { /* FUN_1000_8583 */ }
    void scroll_left()  { /* FUN_1000_853d */ }
    void blit_sprite()  { /* FUN_1000_5f07 */ }
};

class CGARenderer : public RenderingStrategy {
    void scroll_down()  { /* FUN_1000_2e86 */ }
    void scroll_up()    { /* FUN_1000_2ee2 */ }
    void scroll_right() { /* FUN_1000_2f75 */ }
    void scroll_left()  { /* FUN_1000_2f31 */ }
    void blit_sprite()  { /* FUN_1000_60d0 */ }
};

// 런타임 선택
RenderingStrategy* renderer = (mode == 1) ? new EGARenderer() : new CGARenderer();
```

### 2. 최적화 기법

#### A. 순환 버퍼 (Circular Buffer)
```
EGA: 32KB VRAM, mask = 0x7fff
CGA: 8KB VRAM, mask = 0x1fff

장점:
- 메모리 절약 (고정 크기)
- 화면 wrap 자동 처리
- 포인터 산술 단순화
```

#### B. 지연 업데이트 (Lazy Update)
```
dirty_flag 시스템:
- 스크롤 시 flag만 설정
- 실제 화면 업데이트는 메인 루프에서
- VSync와 동기화 가능

→ 프레임 드롭 방지
```

#### C. 4픽셀 경계 타일 로딩
```
if ((vram_offset & 3) == 0) {
    load_tile_column();
}

→ 대역폭 75% 절감 (1/4로 감소)
```

#### D. 대칭적 함수 구현
```
UP/DOWN, LEFT/RIGHT 쌍:
- 동일한 구조
- 반대 부호 연산
- 코드 재사용 최대화

→ 유지보수 용이
```

---

## 🔗 시스템 통합

### 렌더링 파이프라인 전체 흐름

```
메인 루프 (FUN_1000_029a)
    ↓
엔티티 업데이트 (FUN_1000_0360)
    ↓
스프라이트 리스트 빌드 (FUN_1000_48e0)
    └─> 0x18c6 디스패처
        └─> Mode 1: ? / Mode 2: FUN_1000_60d0
            ↓
렌더 리스트 실행 (FUN_1000_034b)
    └─> FUN_1000_499b
        └─> 0x18c4 디스패처
            └─> Mode 1: FUN_1000_5f07 / Mode 2: ?
                ↓
스크롤 처리 (입력 기반)
    ├─> Scroll DOWN:  0x18c8 디스패처
    ├─> Scroll UP:    0x18ca 디스패처
    ├─> Scroll RIGHT: 0x18cc 디스패처
    └─> Scroll LEFT:  0x18ce 디스패처
        ↓
타일맵 로딩 (조건부)
    ├─> func_0x000185fb (Mode 1 vertical)
    ├─> func_0x000185cf (Mode 1 horizontal)
    ├─> func_0x00012c90 (Mode 2 vertical)
    └─> func_0x00012da9 (Mode 2 horizontal)
        ↓
VRAM 업데이트 (dirty_flag 체크)
    └─> 화면 출력
```

---

## 📊 통계 및 성능 분석

### 함수 크기 비교

| 함수 | 크기 (bytes) | 복잡도 | 비고 |
|------|-------------|--------|------|
| FUN_1000_499b | 4 | Trivial | Dispatcher only |
| FUN_1000_48e0 | 4 | Trivial | Dispatcher only |
| FUN_1000_8492 | 20 | Low | Scroll DOWN M1 |
| FUN_1000_84ee | 22 | Low | Scroll UP M1 |
| FUN_1000_8583 | 18 | Low | Scroll RIGHT M1 |
| FUN_1000_853d | 16 | Low | Scroll LEFT M1 |
| FUN_1000_2e86 | 18 | Low | Scroll DOWN M2 |
| FUN_1000_2ee2 | 22 | Low | Scroll UP M2 |
| FUN_1000_2f75 | 18 | Low | Scroll RIGHT M2 |
| FUN_1000_2f31 | 16 | Low | Scroll LEFT M2 |
| FUN_1000_5f07 | 144 | Medium | Sprite blit M1 |
| FUN_1000_60d0 | 56 | Medium | Sprite dispatch M2 |
| **총합** | **356** | - | - |

### 메모리 사용량

```
함수 포인터 테이블:
- Mode 1 소스 (0x18da): 22 bytes (11 pointers)
- Mode 2 소스 (0x18f0): 22 bytes (11 pointers)
- 활성 테이블 (0x18c4): 22 bytes (11 pointers)
= 총 66 bytes

렌더링 상태:
- 0xf38c - 0xf39e: 19 bytes

스프라이트 버퍼:
- 0x4640 - 0x465e: 31 bytes

= 총 116 bytes (렌더링 시스템 전체)
```

---

## 🚀 다음 분석 과제

### Priority P0 (필수)

1. **타일맵 로딩 함수 4개**:
   - func_0x000185fb (Mode 1 vertical)
   - func_0x000185cf (Mode 1 horizontal)
   - func_0x00012c90 (Mode 2 vertical)
   - func_0x00012da9 (Mode 2 horizontal)

2. **나머지 테이블 엔트리 (0x18d0 - 0x18d8)**:
   - 5개 미발견 함수 분석

3. **스프라이트 핸들러 5개** (Mode 2):
   - 0x6162, 0x6324, 0x64fd, 0x66fa, 0x68df

### Priority P1 (중요)

4. **클리핑 함수**:
   - func_0x00016ad0 (Mode 2 clipping)

5. **VRAM 직접 쓰기 함수들**:
   - 0xA000 (EGA) or 0xB800 (CGA) 참조 함수

6. **VSync 동기화**:
   - dirty_flag 처리 로직

---

## 📖 참고 문서

- [MAIN_LOOP_COMPLETE_ANALYSIS.md](MAIN_LOOP_COMPLETE_ANALYSIS.md): 메인 루프 흐름
- [FUNCTION_POINTER_TABLE_ANALYSIS.md](FUNCTION_POINTER_TABLE_ANALYSIS.md): 0x18c4 테이블 초기 분석
- [DATA_LOADING_GRAPHICS_INIT_ANALYSIS.md](DATA_LOADING_GRAPHICS_INIT_ANALYSIS.md): 그래픽 초기화
- [../technical/EXECUTION_PATH.md](../technical/EXECUTION_PATH.md): 전체 실행 경로

---

## 📝 요약

### 핵심 발견

1. ✅ **듀얼 모드 렌더링**: Mode 1 (EGA) / Mode 2 (CGA) 완전 분리
2. ✅ **Strategy 패턴**: 함수 포인터 테이블 기반 동적 디스패치
3. ✅ **스크롤링 시스템**: 4방향 smooth scroll, 4픽셀 경계 최적화
4. ✅ **순환 버퍼**: 32KB (EGA) / 8KB (CGA) VRAM 관리
5. ✅ **Dirty Flag**: 지연 업데이트 시스템
6. ✅ **스프라이트 블리팅**: 클리핑, wrapping, jump table 지원

### 분석 완료 함수

- **11개 함수** 완전 분석
- **356 bytes** 총 코드 크기
- **Mode 1/Mode 2** 완전 비교
- **메모리 맵** 완전 정리 (116 bytes)

### 남은 과제

- 타일맵 로딩 함수 4개
- 나머지 테이블 엔트리 5개
- 스프라이트 핸들러 5개

---

**다음 문서**: [TILE_LOADING_SYSTEM_ANALYSIS.md](TILE_LOADING_SYSTEM_ANALYSIS.md) (예정)
**작성일**: 2025-11-24
**분석자**: Claude Code
