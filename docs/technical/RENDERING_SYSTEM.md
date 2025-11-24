# 렌더링 시스템 완전 분석

**작성일**: 2025-11-24
**Phase**: 4.6 완료

---

## 🎯 개요

Double Dragon DOS 버전의 렌더링 시스템은 **5단계 파이프라인**으로 구성되어 있으며, CGA 4-color 그래픽 모드를 사용합니다.

---

## 📊 렌더링 파이프라인 (5단계)

```
1. FUN_1000_029a - 깊이 정렬 렌더링 루프
   ↓ (각 객체마다)
2. FUN_1000_48e0 - 렌더링 디스패처 (점프 테이블 @ 0x18c6)
   ↓
3. FUN_1000_293e - 렌더링 모드 선택 (DI 레지스터 체크)
   ↓
4a. FUN_1000_28c0 × 4 (모드 1: 직접 복사)
    OR
4b. FUN_1000_28ef × 4 (모드 2: 마스킹/투명도)
   ↓
5. CGA 비디오 메모리 출력 (0xB8000)
```

---

## 🔍 단계별 상세 분석

### 1단계: 깊이 정렬 렌더링 루프

**함수**: `FUN_1000_029a` (177 bytes)
**주소**: 1000:029a
**역할**: Z-ordering (깊이 정렬) 렌더링

#### 알고리즘

```c
void render_all_objects_depth_sorted(void) {
  undefined2 *render_list = (undefined2 *)0x156a;
  uint depth = DAT_1988_16c0;  // 시작 깊이 (뒤)

  // 깊이 레이어 순회 (뒤 → 앞)
  do {
    // 1. 투사체 렌더링 (해당 깊이만)
    for (projectile in projectiles_array) {  // 0x3542 ~ 0x35ae
      if (projectile.active && projectile.depth == depth) {
        DAT_1988_4664 = 0x493a;  // 스프라이트 데이터
        *render_list++ = projectile.render_data;
        FUN_1000_48e0();  // 렌더링 디스패처 호출
      }
    }

    // 2. 엔티티 렌더링 (해당 깊이만)
    for (entity in entities_array) {  // 0x16c6 ~ 0x176e
      if (entity.active && entity.depth == depth) {
        // 방향별 스프라이트 선택
        sprite_offset = entity.sprite_table;
        if (entity.direction == 0x02) sprite_offset += 8;   // 아래
        if (entity.direction == 0x06) sprite_offset += 0x10; // 위
        if (entity.direction == 0x04) sprite_offset += 0x18; // 왼쪽
        if (entity.direction == 0x08) sprite_offset += 0x20; // 오른쪽

        DAT_1988_4664 = *(undefined2 *)(sprite_offset + 2);
        *render_list++ = entity.render_data;
        FUN_1000_48e0();  // 렌더링 디스패처 호출
      }
    }

    depth++;  // 다음 레이어 (앞으로)
  } while (depth <= DAT_1988_16c2);
}
```

#### 메모리 구조

**엔티티 배열** (0x16c6 ~ 0x176e):
- 개수: 7개
- 크기: 24 bytes each
- 용도: 플레이어(2) + 적(5)

**투사체 배열** (0x3542 ~ 0x35ae):
- 개수: 6개
- 크기: 18 bytes each
- 용도: 투사체/아이템/이펙트

**구조체 오프셋**:
```
엔티티 (24 bytes):
  +0x01: 방향 (2,4,6,8)
  +0x02: 활성 플래그
  +0x03: 깊이 오프셋
  +0x06: 스프라이트 테이블 포인터
  +0x0a: Y 좌표
  +0x10: 렌더 데이터

투사체 (18 bytes):
  +0x02: 활성 플래그
  +0x03: 깊이 오프셋
  +0x08: Y 좌표
  +0x0e: 렌더 데이터
```

---

### 2단계: 렌더링 디스패처

**함수**: `FUN_1000_48e0` (4 bytes)
**주소**: 1000:48e0
**역할**: 점프 테이블을 통한 동적 함수 호출

```c
void FUN_1000_48e0(void) {
  (*(code *)*(undefined2 *)0x18c6)();  // 점프 테이블 @ 0x18c6
}
```

#### 점프 테이블 (0x18c6, 30개 엔트리)

| Index | 함수 | 역할 | 그룹 |
|-------|------|------|------|
| 0 | FUN_1000_48e4 | 렌더링 파라미터 변환 | 파라미터 |
| 1 | FUN_1000_81c6 | 스크롤 다운 + VRAM 업데이트 | 스크롤 |
| 2 | FUN_1000_822e | 스크롤 업 | 스크롤 |
| 3 | FUN_1000_827b | 스크롤 오른쪽 | 스크롤 |
| 4 | FUN_1000_82f8 | 스크롤 왼쪽 | 스크롤 |
| 5 | FUN_1000_8139 | 조건부 화면 복사 | 화면 버퍼 |
| 6 | FUN_1000_810f | 반복 화면 업데이트 | 화면 버퍼 |
| 7 | FUN_1000_5864 | 타일맵 데이터 변환 | 화면 버퍼 |
| 8 | FUN_1000_591d | 추가 변환 | 파라미터 |
| 9-29 | ... | 렌더링 헬퍼 함수들 | 다양 |

---

### 3단계: 렌더링 모드 선택

**함수**: `FUN_1000_293e` (20 bytes)
**주소**: 1000:293e
**역할**: DI 레지스터 값으로 렌더링 모드 결정

```c
void FUN_1000_293e(void) {
  uint unaff_DI;  // 렌더링 모드 플래그

  if (unaff_DI < 0x1dc1) {
    // 모드 1: 직접 복사 (불투명 스프라이트)
    FUN_1000_28c0();
    FUN_1000_28c0();
    FUN_1000_28c0();
    FUN_1000_28c0();
  } else {
    // 모드 2: 마스킹 (투명 스프라이트)
    FUN_1000_28ef();
    FUN_1000_28ef();
    FUN_1000_28ef();
    FUN_1000_28ef();
  }
}
```

**임계값**: 0x1dc1 (7617)
**4번 반복**: CGA 4-color 모드의 4개 평면 처리

---

### 4단계: Blit 함수 (2종)

#### 모드 1: 직접 복사 (불투명)

**함수**: `FUN_1000_28c0`
**크기**: 90 bytes
**용도**: 배경, 벽, 불투명 객체

```c
void blit_opaque(void) {
  int stride = in_BX;           // Scanline stride (보통 80)
  undefined2 *src = unaff_SI;   // 소스 데이터
  undefined2 *dst = unaff_DI;   // 비디오 메모리

  // 16 scanlines × 2 bytes = 32 bytes
  for (int line = 0; line < 16; line++) {
    *dst = *src;
    dst = (undefined2 *)((int)dst + stride + 2);
    src++;
  }
}
```

#### 모드 2: 마스킹 (투명)

**함수**: `FUN_1000_28ef`
**크기**: 100 bytes
**용도**: 캐릭터, 적, 투명 객체

```c
void blit_transparent(void) {
  uint mask = in_CX;            // 투명도 마스크
  int stride = in_BX;
  undefined2 *src = unaff_SI;
  uint dst_addr = unaff_DI;

  // 16 scanlines × 2 bytes = 32 bytes
  for (int line = 0; line < 16; line++) {
    *(undefined2 *)(dst_addr & mask) = *src;  // AND 마스킹
    dst_addr = (dst_addr + stride + 2) & mask;
    src++;
  }
}
```

**마스킹 원리**:
- CX 레지스터 = 마스크 값
- `dst & mask` → 0 비트 = 투명 (배경 보존)
- `dst & mask` → 1 비트 = 불투명 (스프라이트 표시)

---

## 🎨 CGA 4-Color 구조

### 비디오 모드
- **해상도**: 320×200
- **색상**: 4색 (2-bit per pixel)
- **메모리**: 0xB8000 ~ 0xBBFFF (16KB)
- **평면 구조**: 4개 평면 (각 평면 = 1 bit)

### 스프라이트 데이터 구조

```
16×16 스프라이트 = 4개 평면 × 32 bytes
  Plane 0: 16 scanlines × 2 bytes = 32 bytes (Color bit 0)
  Plane 1: 16 scanlines × 2 bytes = 32 bytes (Color bit 1)
  Plane 2: 16 scanlines × 2 bytes = 32 bytes (Intensity)
  Plane 3: 16 scanlines × 2 bytes = 32 bytes (예비/마스크)
──────────────────────────────────────────────
총 128 bytes per 16×16 sprite
```

### 4번 반복의 의미

```c
FUN_1000_28c0() × 4;  // 각 평면마다 1번씩
```

1. 호출 1: Plane 0 (Color bit 0)
2. 호출 2: Plane 1 (Color bit 1)
3. 호출 3: Plane 2 (Intensity)
4. 호출 4: Plane 3 (마스크)

---

## 🖼️ 스크롤 시스템

### 스크롤 함수 (4방향)

| 함수 | 방향 | 동작 | 크기 |
|------|------|------|------|
| FUN_1000_81c6 | 다운 | Y++, VRAM+=0xf0 | 100B |
| FUN_1000_822e | 업 | Y--, VRAM-=0xf0 | 73B |
| FUN_1000_827b | 오른쪽 | X++, VRAM 조정 | 121B |
| FUN_1000_82f8 | 왼쪽 | X--, VRAM 조정 | 89B |

### 스크롤 다운 예시

```c
void scroll_down(void) {
  *(int *)0xf398 += 1;        // Y 스크롤 위치++
  *(int *)0xf38c += 0xf0;     // VRAM 오프셋 += 240
  *(int *)0xf38e += 4;        // Scanline 오프셋
  *(int *)0xf394 += 0x10;     // 평면 오프셋

  // 경계 체크 및 래핑
  if (*(int *)0xf38e > 0x9f) {
    *(int *)0xf38c -= 0x2580;
    *(int *)0xf38e -= 0xa0;
  }

  if (*(int *)0xf394 > 0x3f) {
    *(int *)0xf394 -= 0x40;
    *(int *)0xf392 += *(int *)0x46;
  }

  update_video_memory();      // 새 영역 복사
  *(undefined1 *)0xf39e = 1;  // 스크롤 플래그 설정
}
```

### 화면 버퍼 복사

**함수**: `FUN_1000_8139` (84 bytes)

```c
void copy_screen_buffer(void) {
  undefined2 *src = (undefined2 *)*(undefined2 *)0xf38c;
  undefined2 *dst;

  // 홀수/짝수 라인 체크
  if ((*(uint *)0xf38e & 1) == 0) {
    dst = (undefined2 *)0x32a;  // 짝수
  } else {
    dst = (undefined2 *)0x22ee;  // 홀수
  }

  // 0x1e (30) 워드 복사
  for (int i = 0; i < 0x1e; i++) {
    *dst++ = *src++;
  }
}
```

---

## 📍 메모리 맵

### 렌더링 관련

| 주소 | 크기 | 용도 |
|------|------|------|
| 0x156a | 2B | 렌더 리스트 포인터 |
| 0x16c0 | 2B | 시작 깊이 레이어 |
| 0x16c2 | 2B | 끝 깊이 레이어 |
| 0x16c6~0x176e | 168B | 엔티티 배열 (7×24B) |
| 0x18c6 | 60B | 렌더링 점프 테이블 (30×2B) |
| 0x1dc1 | - | 렌더링 모드 임계값 |
| 0x3542~0x35ae | 108B | 투사체 배열 (6×18B) |
| 0x4640~0x465e | 30B | 렌더링 파라미터 버퍼 |
| 0x4664 | 2B | 스프라이트 데이터 포인터 |

### 스크롤 관련

| 주소 | 크기 | 용도 |
|------|------|------|
| 0x32a | - | 화면 버퍼 1 (짝수) |
| 0x22ee | - | 화면 버퍼 2 (홀수) |
| 0xf38c | 2B | VRAM 오프셋 포인터 |
| 0xf38e | 2B | Scanline 오프셋 |
| 0xf392 | 2B | 보조 포인터 |
| 0xf394 | 2B | 평면 오프셋 |
| 0xf396 | 2B | X 스크롤 위치 |
| 0xf398 | 2B | Y 스크롤 위치 |
| 0xf39e | 1B | 스크롤 플래그 |

---

## 🔧 핵심 함수 목록

### 렌더링 파이프라인 (5개)
- `FUN_1000_029a`: 깊이 정렬 렌더링 루프
- `FUN_1000_48e0`: 렌더링 디스패처
- `FUN_1000_293e`: 모드 선택
- `FUN_1000_28c0`: Blit 직접 복사
- `FUN_1000_28ef`: Blit 마스킹

### 점프 테이블 함수 (30개)
- **파라미터 처리** (2개): 48e4, 591d
- **스크롤** (4개): 81c6, 822e, 827b, 82f8
- **화면 버퍼** (3개): 8139, 810f, 5864
- **헬퍼** (21개): 나머지

---

## 📊 성능 분석

### 렌더링 복잡도

```
매 프레임:
  for depth_layer in [back...front]:       // 깊이 레이어 (예: 10개)
    for projectile in projectiles[6]:       // 투사체 6개
      if active && matches_depth:
        dispatch_render() × 4 평면          // 4번 호출
    for entity in entities[7]:              // 엔티티 7개
      if active && matches_depth:
        dispatch_render() × 4 평면          // 4번 호출
```

**최대 렌더링 호출**: 10 레이어 × (6 + 7) 객체 × 4 평면 = **520회/프레임**
**실제**: 활성 객체만 렌더링하므로 대략 **50~100회/프레임**

### 최적화 기법

1. **깊이 정렬**: Z-ordering으로 올바른 렌더링 순서
2. **활성 체크**: 비활성 객체 스킵
3. **함수 포인터**: 점프 테이블로 동적 디스패치
4. **평면 분리**: CGA 4평면을 별도 처리

---

## 🎓 결론

Double Dragon DOS의 렌더링 시스템은:
- ✅ **효율적**: 활성 객체만 렌더링
- ✅ **유연함**: 점프 테이블로 다양한 렌더링 모드
- ✅ **정확함**: 깊이 정렬로 올바른 Z-ordering
- ✅ **최적화됨**: CGA 하드웨어 특성 완전 활용

**72KB 프로그램에 이 정도 구조를 담은 것은 1988년 당시 최적화의 결정체**입니다.

---

**작성일**: 2025-11-24
**Phase**: 4.6 완료
**총 함수**: 164개 (렌더링 관련 약 40개)
