# Double Dragon - 애니메이션 및 발사체 시스템 완전 분석

**분석 날짜**: 2025-11-24
**Phase**: 4.13
**문서 버전**: 1.0

---

## 📋 개요

이 문서는 Double Dragon의 **애니메이션 시스템**과 **발사체 업데이트 시스템**을 완전히 분석합니다. 스프라이트 프레임 선택, 방향별 애니메이션, 발사체 물리 시뮬레이션을 중점적으로 다룹니다.

### 분석 범위
- 7개 함수 분석 완료
- 애니메이션 프레임 선택 시스템
- 방향별 스프라이트 처리 (4방향)
- 발사체 업데이트 루프 (6개 슬롯)
- Work buffer 패턴 (엔티티와 동일)

---

## 🎯 핵심 발견 사항

### 1. 애니메이션 시스템 아키텍처

```
엔티티 업데이트 루프 (FUN_0360)
    ↓
스프라이트 프레임 선택 (FUN_0426)
    ├─> 애니메이션 상태 조회 (FUN_04a9)
    │   └─> Jump table @ 0x1930 (애니메이션 시퀀스)
    ↓
방향별 프레임 선택 (4-way directional)
    ├─> 0x02: 오른쪽 (+4 offset)
    ├─> 0x06: 위 (+8 offset)
    ├─> 0x04: 왼쪽 (+12 offset)
    └─> 0x08: 아래 (+16 offset)
    ↓
화면 좌표 변환 (스크롤 보정)
    ├─> X = sprite_x + entity_x - scroll_x
    └─> Y = (sprite_y + entity_y - scroll_y) × 4
    ↓
렌더 리스트 추가 (FUN_029a → FUN_48e0)
```

### 2. 발사체 시스템 아키텍처

```
메인 루프
    ↓
발사체 업데이트 루프 (FUN_20fb)
    For each projectile (6 slots @ 0x3542):
        if (active):
            ↓
        FUN_2189: Copy → Work buffer (0x3530, 18 bytes)
            ↓
        FUN_2255: Physics update (jump table @ 0x2264)
            ↓
        FUN_2192: Copy ← Work buffer
```

**Work Buffer 패턴**:
- 엔티티: `0x16c6-0x1756` (7 slots × 24 bytes) → `0x168f` (24 bytes)
- 발사체: `0x3542-0x35ae` (6 slots × 18 bytes) → `0x3530` (18 bytes)

**동일한 디자인 패턴**: 복사 → 처리 → 복사

---

## 📊 함수별 상세 분석

## 애니메이션 시스템 (3개, 240 bytes)

### FUN_1000_0426 (131 bytes) - Sprite Frame Selector
**주소**: 1000:0426

```c
void FUN_1000_0426(void) {
    int *piVar1, *piVar3;
    int iVar2;

    // 애니메이션 상태 무효 시 업데이트
    if (*(int *)0x1695 == -1) {
        FUN_1000_04a9();  // 애니메이션 상태 조회
    }

    // 애니메이션 시퀀스 포인터
    piVar3 = (int *)*(int *)*(undefined2 *)0x1695;

    // 방향별 프레임 오프셋
    if (*(char *)0x1690 == '\x02') {  // 오른쪽
        piVar3 = piVar3 + 4;  // +8 bytes (4 words)
    }
    if (*(char *)0x1690 == '\x06') {  // 위
        piVar3 = piVar3 + 8;  // +16 bytes
    }
    if (*(char *)0x1690 == '\x04') {  // 왼쪽
        piVar3 = piVar3 + 0xc;  // +24 bytes
    }
    if (*(char *)0x1690 == '\b') {  // 아래
        piVar3 = piVar3 + 0x10;  // +32 bytes
    }

    // 렌더 리스트 엔트리 포인터
    piVar1 = (int *)*(int *)0x169f;

    // 스프라이트 데이터 포인터
    piVar1[4] = *piVar3;  // Sprite data address

    // 스프라이트 크기 (width, height)
    iVar2 = piVar3[2];
    piVar1[2] = (int)(char)iVar2;          // Width (low byte)
    piVar1[3] = (int)(char)((uint)iVar2 >> 8);  // Height (high byte)

    // 화면 좌표 계산 (스크롤 보정)
    iVar2 = piVar3[3];
    piVar1[0] = ((int)(char)iVar2 + *(int *)0x1697) - *(int *)0xf396;  // X
    piVar1[1] = (int)(char)((uint)iVar2 >> 8) + (*(int *)0x1699 - *(int *)0xf398) * 4;  // Y

    // 우선순위 (Z-order)
    piVar1[5] = *(int *)(*(char *)0x168f + -0xb10);
}
```

**상세 분석**:

#### 1. 애니메이션 상태 (0x1695)
```
0x1695 = -1: 무효 상태
  → FUN_04a9() 호출하여 새 애니메이션 로드
  → Jump table @ 0x1930 사용

0x1695 = valid pointer:
  → ***(0x1695) = 애니메이션 시퀀스 데이터
  → 이중 간접 참조 (double indirection)
```

#### 2. 방향 인코딩 (0x1690)
```
값    | 방향   | 오프셋 (words) | 바이트
------|--------|---------------|-------
0x00  | 기본   | +0            | +0
0x02  | 오른쪽 | +4            | +8
0x06  | 위     | +8            | +16
0x04  | 왼쪽   | +12           | +24
0x08  | 아래   | +16           | +32
```

**4방향 스프라이트**:
- 각 방향마다 8 bytes (4 words) 데이터
- 총 40 bytes per animation frame (5 directions including default)

#### 3. 애니메이션 프레임 구조 (추정)
```c
struct AnimationFrame {
    uint16_t sprite_data_ptr;  // +0: 스프라이트 데이터 주소
    uint16_t unknown;          // +2: (미사용?)
    uint8_t  width;            // +4: 스프라이트 너비
    uint8_t  height;           // +5: 스프라이트 높이
    uint8_t  offset_x;         // +6: X 오프셋 (signed)
    uint8_t  offset_y;         // +7: Y 오프셋 (signed)
};

struct DirectionalAnimation {
    AnimationFrame default;     // +0
    AnimationFrame right;       // +8
    AnimationFrame up;          // +16
    AnimationFrame left;        // +24
    AnimationFrame down;        // +32
};  // Total: 40 bytes
```

#### 4. 렌더 리스트 엔트리 (0x169f)
```c
struct RenderListEntry {
    int16_t screen_x;          // +0: 화면 X 좌표
    int16_t screen_y;          // +2: 화면 Y 좌표
    int16_t width;             // +4: 스프라이트 너비
    int16_t height;            // +6: 스프라이트 높이
    int16_t sprite_data_ptr;   // +8: 스프라이트 데이터 포인터
    int16_t priority;          // +10: Z-order (렌더 우선순위)
};  // Total: 12 bytes (6 words)
```

#### 5. 화면 좌표 변환
```c
// X 좌표 (픽셀 단위)
screen_x = sprite_offset_x + entity_x - scroll_x

// Y 좌표 (4배 스케일)
screen_y = sprite_offset_y + (entity_y - scroll_y) * 4
```

**Y 좌표 × 4 이유**:
- CGA 인터레이스 스캔라인?
- 고정소수점 연산 (0.25 픽셀 정밀도)?
- **추정**: 내부 좌표계가 1/4 픽셀 단위

#### 6. 우선순위 계산
```c
priority = *(int *)(entity_state_byte - 0xb10);
```

**0xb10 = 2832 (음수 오프셋)**:
- Entity state byte (0x168f)를 기준으로 역산
- 예: `0x168f - 0xb10 = 0xbb7f` (우선순위 테이블?)
- **추정**: 엔티티 타입별 고정 우선순위

---

### FUN_1000_04a9 (55 bytes) - Animation State Lookup
**주소**: 1000:04a9

```c
void FUN_1000_04a9(void) {
    int iVar1;

    // 애니메이션 플래그 확인 (bits 0-1)
    if ((*(byte *)0x1693 & 3) != 0) {
        // Jump table 인덱스 계산
        iVar1 = *(int *)((char)(((*(byte *)0x1693 & 3) - 1) + *(char *)0x1691) * 2 + 0x1930);

        // 특수 처리: 타입 0x02 or 0x36
        if (((*(byte *)0x1693 & 8) != 0) &&
            ((*(char *)0x1691 == '\x02' || (*(char *)0x1691 == '6')))) {
            iVar1 = iVar1 + 0x38;  // +56 bytes 오프셋
        }

        // 애니메이션 상태 포인터 설정
        *(int *)0x1695 = iVar1;
        return;
    }

    // 무효 애니메이션: 게임 종료
    FUN_1000_1ba0();  // Exit to DOS
}
```

**상세 분석**:

#### 1. 애니메이션 플래그 (0x1693)
```
Bit 0-1: Animation state (0-3)
  00 = 무효 (종료)
  01 = 애니메이션 1
  10 = 애니메이션 2
  11 = 애니메이션 3

Bit 3: Special flag (0x08)
  1 = 특수 오프셋 적용 (타입 의존)
```

#### 2. Jump Table @ 0x1930
```c
// 인덱스 계산
index = ((flags & 3) - 1) + entity_type;
table_offset = 0x1930 + (index * 2);
anim_ptr = *(uint16_t *)table_offset;
```

**테이블 크기 추정**:
- Entity types: ~50개 (추정)
- Animation states: 3개
- Total entries: 150 pointers × 2 bytes = **300 bytes**

#### 3. 특수 오프셋 (0x38 = 56 bytes)
```
Entity type 0x02 or 0x36 (54):
  if (flag & 0x08):
      anim_ptr += 0x38
```

**추정 의미**:
- 타입 0x02: Player 1?
- 타입 0x36: Player 2?
- 0x38: 대체 애니메이션 세트 (파워업? 무기?)

#### 4. 게임 종료 조건
```c
if ((*(byte *)0x1693 & 3) == 0) {
    FUN_1000_1ba0();  // Exit to DOS
}
```

**의미**:
- 애니메이션 상태 0 = 엔티티 제거
- 중요 엔티티 (플레이어?) 제거 시 게임 종료

---

### FUN_1000_04e1 (54 bytes) - Animation Frame Advancer
**주소**: 1000:04e1

```c
void FUN_1000_04e1(void) {
    char cVar1;
    int iVar2;

    cVar1 = *(char *)0x1691;  // Entity type

    // 특수 타입 체크 (프레임 고정)
    if (cVar1 == '*') {  // 0x2a = 42
        return;  // No advance
    }
    if (cVar1 == '8') {  // 0x38 = 56
        return;  // No advance
    }

    // 특수 타입 0x1a (26)
    if (cVar1 == '\x1a') {
        if (*(int *)0x169b == 0 && *(int *)0x169d == 0) {
            return;  // No advance
        }

        // Sub-animation sequence
        if (*(int *)0x169d == 1) {
            iVar2 = *(int *)(*(int *)(*(int *)0x1695 + 2) + 2);
            goto ADVANCE_FRAME;
        }
    }

    // 일반 프레임 진행
    iVar2 = *(int *)0x1695;

ADVANCE_FRAME:
    // 다음 프레임 포인터
    *(undefined2 *)0x1695 = *(undefined2 *)(iVar2 + 2);
}
```

**상세 분석**:

#### 1. 고정 프레임 타입
```
0x2a (42): 고정 애니메이션 (정지 스프라이트?)
0x38 (56): 고정 애니메이션 (배경 오브젝트?)
```

**추정**:
- 아이템, 장애물, 파괴된 엔티티
- 애니메이션 없이 단일 프레임

#### 2. 조건부 진행 (0x1a)
```c
if (entity_type == 0x1a) {
    if (flags_0x169b == 0 && flags_0x169d == 0) {
        return;  // Paused
    }

    if (flags_0x169d == 1) {
        // 이중 간접 참조 (linked list?)
        next_frame = **(*(0x1695 + 2) + 2);
    }
}
```

**추정**:
- 타입 0x1a: 특수 애니메이션 (발사체? 이펙트?)
- Flags: 재생 제어 (pause, loop, reverse)

#### 3. 프레임 링크 구조
```c
struct AnimationFrameLink {
    uint16_t current_frame_data;  // +0
    uint16_t next_frame_ptr;      // +2
};
```

**Linked list 애니메이션**:
```
Frame 1 → Frame 2 → Frame 3 → Frame 1 (loop)
   ↓         ↓         ↓
 Sprite    Sprite    Sprite
```

---

## 발사체 시스템 (4개, 67 bytes)

### FUN_1000_20fb (32 bytes) - Projectile Update Loop
**주소**: 1000:20fb

```c
void FUN_1000_20fb(void) {
    int iVar1;

    iVar1 = 0x3542;  // 발사체 배열 시작

    do {
        // 활성화 체크 (offset +2)
        if (*(char *)(iVar1 + 2) != '\0') {
            FUN_1000_2189();  // Copy to work buffer
            FUN_1000_2255();  // Physics update
            FUN_1000_2192();  // Copy back
        }

        iVar1 = iVar1 + 0x12;  // +18 bytes (다음 발사체)
    } while (iVar1 != 0x35ae);  // 6개 발사체
}
```

**상세 분석**:

#### 1. 발사체 배열 구조
```
시작: 0x3542
종료: 0x35ae
크기: 0x35ae - 0x3542 = 0x6c = 108 bytes

Slot size: 0x12 = 18 bytes
Slot count: 108 / 18 = 6 projectiles
```

#### 2. 발사체 구조 (추정)
```c
struct Projectile {
    uint16_t pos_x;           // +0x00: X 좌표
    uint16_t active_flag;     // +0x02: 활성화 (0=inactive, !=0=active)
    uint16_t pos_y;           // +0x04: Y 좌표
    uint16_t vel_x;           // +0x06: X 속도
    uint16_t vel_y;           // +0x08: Y 속도
    uint16_t type;            // +0x0a: 발사체 타입 (physics 인덱스)
    uint16_t sprite_id;       // +0x0c: 스프라이트 ID
    uint16_t owner;           // +0x0e: 소유자 엔티티
    uint16_t damage;          // +0x10: 데미지
};  // Total: 18 bytes (0x12)
```

#### 3. Work Buffer 패턴
```
엔티티 시스템:
  Array: 0x16c6-0x1756 (7 × 24 bytes)
  Buffer: 0x168f (24 bytes)

발사체 시스템:
  Array: 0x3542-0x35ae (6 × 18 bytes)
  Buffer: 0x3530 (18 bytes)
```

**동일한 디자인 패턴**: 복사 → 처리 → 복사

---

### FUN_1000_2189 (9 bytes) - Copy Projectile to Work Buffer
**주소**: 1000:2189

```c
void FUN_1000_2189(void) {
    undefined2 *puVar2, *puVar4;
    undefined2 *unaff_SI;  // Source: 발사체 슬롯 포인터
    int iVar3;

    puVar4 = (undefined2 *)0x3530;  // Work buffer destination

    // 9 words (18 bytes) 복사
    for (iVar3 = 9; iVar3 != 0; iVar3 = iVar3 + -1) {
        *puVar4++ = *unaff_SI++;
    }
}
```

**분석**:
- **입력**: SI = 발사체 슬롯 주소 (0x3542 + n×0x12)
- **출력**: 0x3530에 18 bytes 복사
- **용도**: Physics 업데이트 전 데이터 준비

---

### FUN_1000_2255 (15 bytes) - Projectile Physics Dispatcher
**주소**: 1000:2255

```c
void FUN_1000_2255(void) {
    // Jump table @ 0x2264
    // Index: projectile type @ 0x3530
    (*(code *)*(undefined2 *)(*(byte *)0x3530 + 0x2264))();
}
```

**상세 분석**:

#### Jump Table @ 0x2264
```c
uint8_t projectile_type = *(uint8_t *)0x3530;  // Work buffer의 type 필드
uint16_t table_offset = 0x2264 + projectile_type;
void (*physics_func)() = *(void (**)())table_offset;
physics_func();
```

#### 발사체 타입 (추정)
```
0x00: 펀치/킥 (hitbox)
0x01: 던진 무기 (칼, 배트)
0x02: 화살/총알 (직선 비행)
0x03: 수류탄/폭탄 (포물선)
0x04: 특수 공격 (회전킥 등)
...
```

#### Physics 함수 (미분석)
- 위치 업데이트: `pos += vel`
- 중력 적용: `vel_y += gravity`
- 충돌 검사: `check_collision()`
- 수명 관리: `lifetime--`

---

### FUN_1000_2192 (11 bytes) - Copy Work Buffer Back to Projectile
**주소**: 1000:2192

```c
void FUN_1000_2192(void) {
    undefined2 *puVar1, *puVar2, *puVar4;
    undefined2 *unaff_SI;  // Destination: 발사체 슬롯
    int iVar3;

    puVar4 = (undefined2 *)0x3530;  // Work buffer source

    // 9 words (18 bytes) 복사
    for (iVar3 = 9; iVar3 != 0; iVar3 = iVar3 + -1) {
        *unaff_SI++ = *puVar4++;
    }
}
```

**분석**:
- **입력**: 0x3530 work buffer
- **출력**: SI = 발사체 슬롯 주소
- **용도**: Physics 업데이트 후 결과 저장

---

## 🗺️ 메모리 맵 완전 정리

### 애니메이션 시스템 (0x168f - 0x169f)

```
주소     | 크기 | 이름                      | 설명
---------|------|---------------------------|-----------------------------
0x168f   | 1    | entity_state_byte         | 엔티티 상태 (우선순위 계산용)
0x1690   | 1    | entity_direction          | 방향 (0x02/0x04/0x06/0x08)
0x1691   | 1    | entity_type               | 엔티티 타입 (애니메이션 선택)
0x1693   | 1    | animation_flags           | Bit 0-1: state, Bit 3: special
0x1695   | 2    | animation_state_ptr       | 현재 애니메이션 프레임 포인터
0x1697   | 2    | entity_x                  | 엔티티 X 좌표
0x1699   | 2    | entity_y                  | 엔티티 Y 좌표
0x169b   | 2    | animation_control_0       | 재생 제어 플래그
0x169d   | 2    | animation_control_1       | 재생 제어 플래그
0x169f   | 2    | render_list_entry_ptr     | 렌더 리스트 엔트리 포인터
```

### 발사체 시스템 (0x3530 - 0x35ae)

```
주소     | 크기 | 이름                      | 설명
---------|------|---------------------------|-----------------------------
0x3530   | 18   | projectile_work_buffer    | 발사체 작업 버퍼
0x3542   | 18   | projectile_slot_0         | 발사체 슬롯 0
0x3554   | 18   | projectile_slot_1         | 발사체 슬롯 1
0x3566   | 18   | projectile_slot_2         | 발사체 슬롯 2
0x3578   | 18   | projectile_slot_3         | 발사체 슬롯 3
0x358a   | 18   | projectile_slot_4         | 발사체 슬롯 4
0x359c   | 18   | projectile_slot_5         | 발사체 슬롯 5
0x35ae   | -    | (end marker)              | 발사체 배열 종료
```

### Jump Tables

```
주소     | 크기 | 이름                      | 설명
---------|------|---------------------------|-----------------------------
0x1930   | ~300 | animation_sequence_table  | 애니메이션 시퀀스 포인터 (150 entries)
0x2264   | ~256 | projectile_physics_table  | 발사체 물리 함수 포인터 (128 entries)
```

---

## 🎨 시스템 설계 분석

### 1. 4방향 애니메이션 시스템

```c
// 애니메이션 데이터 레이아웃
struct DirectionalAnimationSet {
    struct AnimationFrame {
        uint16_t sprite_ptr;   // 스프라이트 데이터
        uint16_t unused;
        uint8_t  width;        // 스프라이트 크기
        uint8_t  height;
        int8_t   offset_x;     // 중심점 오프셋
        int8_t   offset_y;
    } frames[5];  // default, right, up, left, down

    // Total: 40 bytes per animation state
};
```

**방향 인코딩 최적화**:
```c
// 4개 if 문 (비효율적)
if (dir == 0x02) offset = 4;
if (dir == 0x06) offset = 8;
if (dir == 0x04) offset = 12;
if (dir == 0x08) offset = 16;

// 최적화 가능 (LUT):
offset = direction_lut[dir >> 1];  // {0, 4, 8, 12, 16}
```

**하지만 원본 코드는 순차 if 사용** → 코드 크기 최소화 우선

### 2. Linked List 애니메이션

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Frame 1     │      │ Frame 2     │      │ Frame 3     │
├─────────────┤      ├─────────────┤      ├─────────────┤
│ Sprite Data │      │ Sprite Data │      │ Sprite Data │
│ Next → ─────┼─────>│ Next → ─────┼─────>│ Next → ─────┼──┐
└─────────────┘      └─────────────┘      └─────────────┘  │
      ↑                                                       │
      └───────────────────────────────────────────────────────┘
                        (Loop back to Frame 1)
```

**장점**:
- 가변 길이 애니메이션 (2-20 프레임)
- 메모리 효율 (사용 중인 프레임만 할당)
- 동적 분기 (조건부 프레임 스킵)

**단점**:
- 캐시 미스 (비연속 메모리)
- 간접 참조 오버헤드

### 3. Work Buffer 패턴 일관성

```
시스템         | 배열 크기      | Work Buffer | 함수 트리플렛
--------------|---------------|-------------|------------------
엔티티        | 7 × 24 bytes  | 0x168f (24) | 0412 → 16e0 → 041b
발사체        | 6 × 18 bytes  | 0x3530 (18) | 2189 → 2255 → 2192
```

**패턴**:
```c
for each object in array:
    copy_to_buffer(object, buffer);
    process(buffer);  // 디스패처 호출
    copy_from_buffer(buffer, object);
```

**이유**:
1. **고정 주소 접근**: Work buffer는 고정 주소 (빠른 접근)
2. **레지스터 할당**: 24-byte buffer는 레지스터에 맞음
3. **원자성**: 복사 → 처리 → 복사 (중간 상태 노출 없음)

---

## 🔍 흥미로운 발견

### 1. Y 좌표 × 4 스케일

```c
screen_y = sprite_offset_y + (entity_y - scroll_y) * 4;
```

**가능한 이유**:

#### A. 고정소수점 연산
```
내부 좌표계: 0.25 픽셀 정밀도
표시 좌표계: 1 픽셀 정밀도

Entity Y: 100.75 → 내부값 403
Screen Y: 403 × 1 / 4 = 100 (반올림)
```

**장점**:
- 부드러운 움직임 (서브픽셀 정밀도)
- 정수 연산만 사용 (부동소수점 없음)

#### B. CGA 인터레이스 보정
```
CGA 4-color mode:
  Even scanlines: Buffer A (0xB800:0000)
  Odd scanlines:  Buffer B (0xB800:2000)

Y × 4 = 인터레이스 주소 계산 보정?
```

#### C. 좌표계 변환
```
World space: 픽셀 단위
Screen space: word 단위 (2 bytes/pixel in CGA)

Y × 4 = 2 (bytes/pixel) × 2 (EGA 다중 플레인)?
```

**결론**: 고정소수점 가능성 가장 높음

---

### 2. 우선순위 계산의 수수께끼

```c
priority = *(int *)(entity_state_byte - 0xb10);
```

**0xb10 = 2832 (음수 오프셋)**:
```
0x168f - 0xb10 = 0xbb7f (overflow, 16-bit)

실제: 0x168f - 0x0b10 = 0x0b7f
또는: 0x1988:168f - 0xb10 = ...
```

**추정**:
1. **세그먼트 베이스 오프셋**: DS = 0x1988
   - `DS:168f - 0xb10 = 1988:b7f`
   - 우선순위 테이블 @ 0x1988:0b7f

2. **음수 인덱싱**:
   - 0xb10 = -0x4f0 (2's complement)
   - 스택 상대 주소?

**필요**: 메모리 덤프로 0xb7f 주변 확인

---

### 3. 애니메이션 상태 0 = 게임 종료

```c
if ((animation_flags & 3) == 0) {
    FUN_1000_1ba0();  // Exit to DOS
}
```

**의미**:
- 플레이어 애니메이션 = 게임 상태
- 상태 0 = 사망 또는 제거
- **즉시 종료** (게임 오버 화면 없음?)

**추정 흐름**:
```
플레이어 HP = 0
  → 사망 애니메이션 재생
  → 애니메이션 종료 시 flags = 0
  → FUN_04a9 호출
  → 게임 종료
```

**문제**: 이건 너무 급작스러움. 게임 오버 로직이 다른 곳에?

---

## 📊 통계 및 성능 분석

### 함수 크기 비교

| 함수 | 크기 (bytes) | 복잡도 | 호출 빈도 | 비고 |
|------|-------------|--------|----------|------|
| FUN_0426 | 131 | High | 매 프레임 | Sprite frame selector |
| FUN_04a9 | 55 | Medium | 상태 변경 시 | Animation lookup |
| FUN_04e1 | 54 | Medium | 매 프레임 | Frame advancer |
| FUN_20fb | 32 | Low | 매 프레임 | Projectile loop |
| FUN_2189 | 9 | Trivial | 6회/프레임 | Copy to buffer |
| FUN_2255 | 15 | Low | 6회/프레임 | Physics dispatcher |
| FUN_2192 | 11 | Trivial | 6회/프레임 | Copy from buffer |
| **총합** | **307** | - | - | - |

### 메모리 사용량

```
애니메이션 시스템:
- 상태 변수: 17 bytes (0x168f-0x169f)
- Jump table: ~300 bytes (0x1930)
= 317 bytes

발사체 시스템:
- Work buffer: 18 bytes (0x3530)
- 발사체 배열: 108 bytes (0x3542-0x35ae)
- Physics table: ~256 bytes (0x2264)
= 382 bytes

총합: 699 bytes
```

### 프레임당 오버헤드

```
엔티티 7개 (플레이어 2 + 적 5):
  - FUN_0426: 131 bytes × 7 = 917 cycles (추정)
  - FUN_04e1: 54 bytes × 7 = 378 cycles
= 1295 cycles/frame (엔티티 애니메이션)

발사체 6개:
  - FUN_2189: 9 bytes × 6 = 54 cycles
  - FUN_2255: 15 bytes × 6 = 90 cycles (+ physics)
  - FUN_2192: 11 bytes × 6 = 66 cycles
= 210 cycles/frame (발사체 기본) + physics

총 오버헤드: ~2000 cycles/frame (@ 4.77 MHz → 0.4ms)
```

---

## 🚀 다음 분석 과제

### Priority P0 (필수)

1. **Physics Functions** (0x2264 table):
   - 발사체 타입별 물리 구현
   - 중력, 속도, 충돌

2. **Animation Sequences** (0x1930 table):
   - 실제 애니메이션 데이터 구조
   - 프레임 링크 검증

3. **Render List System**:
   - 0x169f 엔트리 관리
   - Z-order 정렬 알고리즘

### Priority P1 (중요)

4. **우선순위 테이블 확인**:
   - 0xb7f 주변 메모리 덤프
   - 엔티티 타입별 Z-order 값

5. **Direction Encoding 표준화**:
   - 0x02/0x04/0x06/0x08 매핑 확인
   - 8방향 지원 여부

---

## 📖 참고 문서

- [ENTITY_SYSTEM_ANALYSIS.md](ENTITY_SYSTEM_ANALYSIS.md): 엔티티 업데이트 루프
- [RENDERING_SCROLLING_SYSTEM_ANALYSIS.md](RENDERING_SCROLLING_SYSTEM_ANALYSIS.md): 스프라이트 렌더링
- [MAIN_LOOP_COMPLETE_ANALYSIS.md](MAIN_LOOP_COMPLETE_ANALYSIS.md): 메인 루프 통합

---

## 📝 요약

### 핵심 발견

1. ✅ **4방향 애니메이션**: 방향별 8-byte 오프셋 (40 bytes/frame)
2. ✅ **Linked List 구조**: 프레임 체인 (가변 길이)
3. ✅ **Work Buffer 패턴**: 엔티티/발사체 동일 디자인
4. ✅ **Jump Table 디스패치**: 애니메이션 (0x1930) + 물리 (0x2264)
5. ✅ **화면 좌표 변환**: Y × 4 스케일 (고정소수점 추정)

### 분석 완료 함수

- **7개 함수** 완전 분석
- **307 bytes** 총 코드 크기
- **애니메이션 + 발사체** 2개 하위 시스템
- **메모리 맵** 완전 정리 (699 bytes)

### 남은 과제

- Physics 함수들 (0x2264 table)
- Animation sequence 데이터
- Render list Z-order 정렬

---

**다음 문서**: [PHYSICS_COLLISION_SYSTEM_ANALYSIS.md](PHYSICS_COLLISION_SYSTEM_ANALYSIS.md) (예정)
**작성일**: 2025-11-24
**분석자**: Claude Code
