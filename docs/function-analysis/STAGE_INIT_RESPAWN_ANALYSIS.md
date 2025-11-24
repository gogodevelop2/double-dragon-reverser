# Stage Initialization & Player Respawn Analysis

**분석 일자**: 2025-11-24
**대상**: Double Dragon DOS (1988)
**Phase**: 4.10 - Stage & Respawn Systems

---

## 목차

1. [개요](#개요)
2. [스테이지 초기화 시스템](#스테이지-초기화-시스템)
3. [플레이어 사망 및 리스폰](#플레이어-사망-및-리스폰)
4. [스폰 위치 찾기 알고리즘](#스폰-위치-찾기-알고리즘)
5. [스테이지 데이터 구조](#스테이지-데이터-구조)
6. [엔티티 초기화](#엔티티-초기화)
7. [스테이지별 그래픽 로딩](#스테이지별-그래픽-로딩)
8. [타일맵 주소 변환](#타일맵-주소-변환)
9. [메모리 맵 업데이트](#메모리-맵-업데이트)
10. [시스템 흐름도](#시스템-흐름도)

---

## 개요

이 문서는 Double Dragon의 **스테이지 초기화**, **플레이어 리스폰**, **스폰 위치 탐색** 시스템을 분석합니다. 특히 424바이트 거대 함수 **FUN_1000_3c7e**에서 스테이지 테이블 기반 데이터 로딩 시스템을 발견했으며, **FUN_1000_3f71**의 정교한 스폰 위치 탐색 알고리즘을 확인했습니다.

### 분석 대상 함수 (8개)

| 주소 | 함수명 | 크기 | 역할 |
|------|--------|------|------|
| 3c7e | FUN_1000_3c7e | 424B | 스테이지 초기화 마스터 함수 ★★★★★ |
| 3e6d | FUN_1000_3e6d | 258B | 플레이어 사망/리스폰 처리 ★★★★ |
| 3f71 | FUN_1000_3f71 | 106B | 스폰 위치 찾기 알고리즘 ★★★ |
| 3e46 | FUN_1000_3e46 | 16B | 적 엔티티 배열 초기화 |
| 3e56 | FUN_1000_3e56 | 23B | 프로젝타일 데이터 복사 |
| 3e1a | FUN_1000_3e1a | 31B | 타일맵 주소 변환 |
| 0a96 | FUN_1000_0a96 | 94B | 일반 스테이지 그래픽 로딩 |
| 0af5 | FUN_1000_0af5 | 94B | 보스 스테이지 그래픽 로딩 |

---

## 스테이지 초기화 시스템

### FUN_1000_3c7e: 스테이지 초기화 마스터 함수 (424 bytes) ★★★★★

**역할**: 스테이지 테이블에서 모든 데이터를 읽어와 새로운 스테이지를 완전히 초기화합니다.

```c
void __cdecl16near FUN_1000_3c7e(void) {
    undefined2 *puVar1;
    code *pcVar2;
    int iVar3;
    int iVar4;

    // ========================================
    // Part 1: Clear entity arrays
    // ========================================
    FUN_1000_3e46();  // Clear enemy entities (5 × 24B)
    FUN_1000_3e56();  // Copy projectile data from table

    // ========================================
    // Part 2: Get stage data pointer from table
    // ========================================
    // Stage data table @ 0x3fce
    // Each stage has a pointer to its data structure
    puVar1 = (undefined2 *)*(int *)((byte)(DAT_1988_38d0 << 1) + 0x3fce);
    //                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    //                               stage_table[stage * 2]
    //                               stage: 0x38d0 (1-based)

    // Check if mode 1 (skip data loading?)
    if (DAT_1988_0035 != '\0') {  // 0x0035 = rendering mode
        FUN_1000_3b20();  // Alternative initialization
        return;
    }

    // ========================================
    // Part 3: Load stage data files (3 files)
    // ========================================
    // File 1: Main stage data
    DAT_1988_320d = 0x1988;  // Source segment
    DAT_1988_320f = 0x5690;  // Source offset (compressed data?)
    DAT_1988_3213 = *puVar1;  // Destination from table[0]
    FUN_1000_1e8a();  // Load & decompress

    // File 2: Tilemap data
    DAT_1988_320d = 0x1988;
    DAT_1988_320f = 0xe000;  // Tilemap source offset
    DAT_1988_3213 = puVar1[1];  // Destination from table[1]
    FUN_1000_1e8a();

    // File 3: Additional data
    DAT_1988_320d = 0x1988;
    DAT_1988_320f = 0x4e;  // Small data offset
    DAT_1988_3213 = puVar1[2];  // Destination from table[2]
    FUN_1000_1e8a();

    // ========================================
    // Part 4: Initialize game state from table
    // ========================================
    // The stage data structure has ~20 fields
    DAT_1988_0046 = puVar1[3];   // Field 3
    DAT_1988_0048 = puVar1[4];   // Field 4
    DAT_1988_004a = puVar1[5];   // Field 5
    DAT_1988_f392 = puVar1[6];   // Field 6 - Scroll related?
    DAT_1988_f396 = puVar1[7];   // Field 7 - Scroll X!
    DAT_1988_f398 = puVar1[8];   // Field 8 - Scroll Y!
    DAT_1988_16ce = puVar1[9];   // Field 9 - Player 1 Y position
    DAT_1988_16d0 = puVar1[10];  // Field 10 - Player 1 X position
    DAT_1988_16e6 = puVar1[0xb]; // Field 11 - Player 2 Y position
    DAT_1988_16e8 = puVar1[0xc]; // Field 12 - Player 2 X position
    DAT_1988_16c9 = *(undefined1 *)(puVar1 + 0xd);  // Field 13 - P1 facing
    DAT_1988_16e1 = *(undefined1 *)((int)puVar1 + 0x1b);  // Field 13+1 - P2 facing
    DAT_1988_38db = puVar1[0xe]; // Field 14 - Stage data ptr
    DAT_1988_38dd = puVar1[0xf]; // Field 15 - Scroll data ptr
    DAT_1988_4411 = puVar1[0x10]; // Field 16
    DAT_1988_4413 = puVar1[0x11]; // Field 17
    DAT_1988_4415 = puVar1[0x12]; // Field 18
    DAT_1988_4417 = *(undefined1 *)(puVar1 + 0x13);  // Field 19
    DAT_1988_4418 = *(undefined1 *)((int)puVar1 + 0x27);  // Field 19+1
    DAT_1988_4419 = *(undefined1 *)(puVar1 + 0x14);  // Field 20
    DAT_1988_4676 = *(undefined2 *)((int)puVar1 + 0x29);  // Field 21
    DAT_1988_16c0 = *(undefined2 *)((int)puVar1 + 0x2b);  // Field 22
    DAT_1988_16c2 = *(undefined2 *)((int)puVar1 + 0x2d);  // Field 23

    // ========================================
    // Part 5: Initialize scroll and rendering
    // ========================================
    DAT_1988_f38c = 0xb0d0;  // VRAM pointer base
    DAT_1988_f38e = 0;       // Clear
    DAT_1988_f390 = 0;       // Clear
    DAT_1988_f394 = 0;       // Clear scroll offset
    DAT_1988_38df = 1;       // Set stage data ready flag
    DAT_1988_16b0 = 0;       // Reset frame counter
    DAT_1988_16bc = 0;       // Clear

    // Load timer value from timer table
    DAT_1988_442e = *(undefined2 *)((byte)(DAT_1988_38d0 << 1) + 0x4404);
    //               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    //               timer_table[stage * 2]

    DAT_1988_4674 = 0;

    FUN_1000_583b();  // Some initialization

    DAT_1988_4410 = 0;
    DAT_1988_441a = 0;

    // ========================================
    // Part 6: Initialize player entities (2 players)
    // ========================================
    iVar3 = 2;  // 2 players
    iVar4 = 0x16c6;  // Player 1 entity
    do {
        // If player exists (state != 0)
        if (*(char *)(iVar4 + 2) != '\0') {
            *(undefined1 *)(iVar4 + 2) = 0x2a;  // Set state to alive (0x2a)
        }
        *(undefined1 *)(iVar4 + 4) = 5;      // HP = 5
        *(undefined1 *)(iVar4 + 5) = 0x14;   // Max HP = 20
        *(undefined2 *)(iVar4 + 6) = 0xffff; // Target = none
        *(undefined2 *)(iVar4 + 0x12) = 0xffff;  // Clear field
        iVar4 = iVar4 + 0x18;  // Next player (24 bytes)
        iVar3 = iVar3 + -1;
    } while (iVar3 != 0);

    // ========================================
    // Part 7: Process tilemap addresses
    // ========================================
    FUN_1000_3e1a();  // Adjust tilemap pointers

    // ========================================
    // Part 8: Load stage-specific graphics
    // ========================================
    if (DAT_1988_38d0 == '\x05') {  // Stage 5 (boss stage)
        FUN_1000_0af5();  // Load boss stage graphics
    }
    else {
        FUN_1000_0a96();  // Load normal stage graphics
    }

    // ========================================
    // Part 9: BIOS video calls (screen setup?)
    // ========================================
    if (DAT_1988_0035 == '\0') {  // Mode 0
        if ((DAT_1988_38d0 != '\x03') && (DAT_1988_38d0 != '\x04')) {
            // Stages 1, 2, 5
            pcVar2 = (code *)swi(0x10);  // INT 10h (Video)
            (*pcVar2)();
            return;
        }
        // Stages 3, 4
        pcVar2 = (code *)swi(0x10);
        (*pcVar2)();
        pcVar2 = (code *)swi(0x10);
        (*pcVar2)();
        return;
    }
    // Mode 1
    pcVar2 = (code *)swi(0x10);
    (*pcVar2)();
    return;
}
```

**스테이지 데이터 구조** (최소 47 bytes):
```c
struct StageData {
    uint16 data_dest_1;      // +0: Main data destination
    uint16 tilemap_dest;     // +2: Tilemap destination
    uint16 data_dest_3;      // +4: Additional data destination
    uint16 field_3;          // +6
    uint16 field_4;          // +8
    uint16 field_5;          // +10
    uint16 scroll_field;     // +12
    uint16 scroll_x;         // +14: Initial scroll X
    uint16 scroll_y;         // +16: Initial scroll Y
    uint16 player1_y;        // +18: P1 spawn Y
    uint16 player1_x;        // +20: P1 spawn X
    uint16 player2_y;        // +22: P2 spawn Y
    uint16 player2_x;        // +24: P2 spawn X
    uint8  player1_facing;   // +26: P1 facing direction
    uint8  player2_facing;   // +27: P2 facing direction
    uint16 stage_data_ptr;   // +28: Stage data pointer
    uint16 scroll_data_ptr;  // +30: Scroll limit data pointer
    uint16 field_16;         // +32
    uint16 field_17;         // +34
    uint16 field_18;         // +36
    uint8  field_19;         // +38
    uint8  field_19b;        // +39
    uint8  field_20;         // +40
    uint16 field_21;         // +41
    uint16 field_22;         // +43
    uint16 field_23;         // +45
    // Total: 47+ bytes
};
```

**스테이지 테이블 @ 0x3fce**:
```
0x3fce: [Stage 1 data pointer]
0x3fd0: [Stage 2 data pointer]
0x3fd2: [Stage 3 data pointer]
0x3fd4: [Stage 4 data pointer]
0x3fd6: [Stage 5 data pointer]
```

---

## 플레이어 사망 및 리스폰

### FUN_1000_3e6d: 플레이어 사망/리스폰 처리 (258 bytes) ★★★★

**역할**: 플레이어 사망 시 생명을 감소시키고, 리스폰 또는 게임오버를 처리합니다.

```c
void __cdecl16near FUN_1000_3e6d(void) {
    int *piVar1;
    int iVar2;
    uint uVar3;
    bool bVar4;
    undefined2 unaff_DS;

    // ========================================
    // Part 1: Check player state
    // ========================================
    // 0x168f = work buffer player ID
    //   0 = Player 1
    //   10 (0x0a) = Player 2
    if ((*(char *)0x168f != '\0') && (*(char *)0x168f != '\n')) {
        // Not a player entity, skip
        // ========================================
        // Special case: Check for invincibility end
        // ========================================
        if (*(char *)0x1694 != '\0') {  // Invincibility counter
            return;  // Still invincible
        }

        // Check if specific death animation sprites
        if ((*(int *)0x1695 != 0x1b6c) && (*(int *)0x1695 != 0x1b81)) {
            return;  // Not death sprites
        }

        // Death animation complete, remove entity
        *(undefined1 *)0x1691 = 0;  // Set state to 0 (dead)
        return;
    }

    // ========================================
    // Part 2: Player entity processing
    // ========================================
    if (*(char *)0x1691 != '\0') {  // Player has state (alive)
        if ('\0' < *(char *)0x1694) {  // Counter > 0
            return;  // Processing...
        }

        // Check for specific states
        if ((*(char *)0x1691 == '*') ||    // State 0x2a (normal alive)
            (*(char *)0x1691 == '\x02')) {  // State 0x02
            // Transition to death state
            *(undefined1 *)0x1691 = 0x1e;  // State = 0x1e (dying)
            *(undefined2 *)0x1695 = 0xffff;  // Sprite = none
            return;
        }

        // Check for specific sprite
        if (*(int *)0x1695 != 0x25f0) {
            return;
        }

        // Death complete
        *(undefined1 *)0x1691 = 0;  // State = 0 (dead)
    }

    // ========================================
    // Part 3: Decrement lives display
    // ========================================
    if (*(char *)0x168f == '\n') {  // Player 2
        piVar1 = (int *)0x442a;  // P2 lives display
        iVar2 = *piVar1;
        *piVar1 = *piVar1 + -1;  // Decrement lives display
        uVar3 = *(uint *)0x442a;
        bVar4 = CARRY2(uVar3, (uint)(iVar2 == 0));
        *(uint *)0x442a = uVar3 + (iVar2 == 0);  // Underflow handling
    }
    else {  // Player 1
        piVar1 = (int *)0x4428;  // P1 lives display
        iVar2 = *piVar1;
        *piVar1 = *piVar1 + -1;  // Decrement lives display
        uVar3 = *(uint *)0x4428;
        bVar4 = CARRY2(uVar3, (uint)(iVar2 == 0));
        *(uint *)0x4428 = uVar3 + (iVar2 == 0);  // Underflow handling
    }

    // ========================================
    // Part 4: Check if can respawn
    // ========================================
    if (bVar4) {  // Underflow occurred (display went negative)
        // Check actual lives counter
        if (*(int *)0x442c == 0) {  // 0x442c = actual lives
            return;  // No lives left, don't respawn
        }

        // ========================================
        // Part 4a: Check for button press (continue screen)
        // ========================================
        if (*(char *)0x168f == '\n') {  // Player 2
            if (*(char *)0x31d9 != '\0') {  // P2 button not pressed
                return;  // Wait for button
            }
            // Button pressed, restore display
            *(undefined2 *)0x442a = 2;  // Lives display = 2
            *(undefined2 *)0x4426 = 0;  // Clear score low
        }
        else {  // Player 1
            if ((*(char *)0x3204 != '\0') && (*(char *)0x31c6 != '\0')) {
                return;  // Wait for button
            }
            // Button pressed, restore display
            *(undefined2 *)0x4428 = 2;  // Lives display = 2
            *(undefined2 *)0x4424 = 0;  // Clear score low
        }

        // ========================================
        // Part 5: Respawn player
        // ========================================
        *(undefined1 *)0x1694 = 0x14;  // Set counter = 20
        *(undefined1 *)0x1691 = 0x20;  // Set state = 0x20 (respawning)
        *(undefined2 *)0x1695 = 0xffff;  // Sprite = none
        *(int *)0x442c = *(int *)0x442c + -1;  // Decrement actual lives
        FUN_1000_3f71();  // Find spawn position ★
        *(undefined2 *)0x442e = *(undefined2 *)((byte)(*(char *)0x38d0 << 1) + 0x4404);
        //                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        //                       Reload timer from timer_table[stage]
        return;
    }

    // ========================================
    // Part 6: Normal death (not out of lives)
    // ========================================
    *(undefined1 *)0x1691 = 0x20;  // State = 0x20
    *(undefined2 *)0x1695 = 0xffff;  // Sprite = none
    *(undefined1 *)0x1694 = 0x14;  // Counter = 20
    FUN_1000_3f71();  // Find spawn position
    return;
}
```

**플레이어 상태 흐름**:
```
Normal State (0x2a)
    ↓ HP = 0
Dying State (0x1e)
    ↓ Animation complete
Dead State (0x00)
    ↓ Lives > 0
    ├─> Lives display--
    ├─> If display < 0:
    │   ├─> Check actual lives (0x442c)
    │   ├─> If lives > 0:
    │   │   ├─> Wait for button press
    │   │   ├─> Lives--
    │   │   ├─> Find spawn position
    │   │   └─> Respawn State (0x20)
    │   └─> If lives = 0:
    │       └─> Game Over (handled by FUN_4780)
    └─> Normal respawn
        ├─> Find spawn position
        └─> Respawn State (0x20)
```

**메모리**:
```
Work Buffer:
  0x168f: Player ID (0=P1, 10=P2)
  0x1691: Entity state
  0x1694: Counter/invincibility
  0x1695: Sprite ID

Lives:
  0x442c: Actual lives counter
  0x4428: P1 lives display
  0x442a: P2 lives display

Scores:
  0x4424: P1 score low
  0x4426: P2 score low

Input flags:
  0x3204, 0x31c6: P1 input
  0x31d9: P2 input
```

---

## 스폰 위치 찾기 알고리즘

### FUN_1000_3f71: 스폰 위치 탐색 (106 bytes) ★★★

**역할**: 타일맵 충돌 검사를 통해 유효한 스폰 위치를 찾습니다.

```c
void __cdecl16near FUN_1000_3f71(void) {
    int iVar1;
    int iVar2;
    int iVar3;
    int iVar4;
    undefined2 unaff_DS;

    // ========================================
    // Part 1: Set initial spawn position
    // ========================================
    iVar1 = *(int *)0xf396 + 0x19;  // X = scroll_x + 25
    if (*(char *)0x168f != '\0') {  // If Player 2
        iVar1 = *(int *)0xf396 + 0x23;  // X = scroll_x + 35
    }
    *(int *)0x16a7 = iVar1;  // Temp X
    *(int *)0x16a9 = *(int *)0xf398 + 0x14;  // Temp Y = scroll_y + 20

    // ========================================
    // Part 2: Search for valid spawn point
    // ========================================
    iVar4 = 1;  // Iteration counter
    iVar3 = 4;  // Step size (starts at 4)
    iVar1 = iVar4;

    while (FUN_1000_12c0(),  // Check tilemap collision at (0x16a7, 0x16a9)
           *(char *)0x16ae != '\0') {  // If collision detected (not walkable)

        // ========================================
        // Part 2a: Move right
        // ========================================
        *(int *)0x16a7 = *(int *)0x16a7 + iVar3;  // X += step
        iVar4 = iVar4 + -1;

        // ========================================
        // Part 2b: If moved right enough, switch to vertical search
        // ========================================
        if (iVar4 == 0) {
            iVar2 = iVar1;
            do {
                // Check collision again
                FUN_1000_12c0();
                if (*(char *)0x16ae == '\0') goto LAB_1000_3fc8;  // Found!

                // ========================================
                // Part 2c: Move vertically
                // ========================================
                *(int *)0x16a9 = *(int *)0x16a9 + iVar3;  // Y += step
                iVar2 = iVar2 + -1;
            } while (iVar2 != 0);

            // ========================================
            // Part 2d: Reverse direction and increase range
            // ========================================
            iVar4 = iVar1 + 1;  // Increase iteration count
            iVar3 = -iVar3;     // Reverse direction (4 → -4)
            iVar1 = iVar4;
        }
    }

LAB_1000_3fc8:
    // ========================================
    // Part 3: Set entity position to found spawn point
    // ========================================
    *(undefined2 *)0x1697 = *(undefined2 *)0x16a7;  // Entity X = found X
    *(undefined2 *)0x1699 = *(undefined2 *)0x16a9;  // Entity Y = found Y
    *(undefined1 *)0x1692 = *(undefined1 *)0x16ad;  // Set tile type?

    return;
}
```

**탐색 알고리즘 시각화**:
```
Start: (scroll_x + 25, scroll_y + 20)  [Player 1]
       (scroll_x + 35, scroll_y + 20)  [Player 2]

Search pattern (spiral outward):
  Step 1: +4 right  → check collision
  Step 2: +4 down   → check collision
  Step 3: -4 left (reverse)  → check collision
  Step 4: -4 down   → check collision
  Step 5: +8 right  → check collision  (doubled range)
  Step 6: +8 down   → check collision
  ...

Example search pattern:
  Start: (100, 50)
  Try 1: (104, 50)  ← +4 X
  Try 2: (104, 54)  ← +4 Y
  Try 3: (100, 54)  ← -4 X (reversed)
  Try 4: (100, 58)  ← -4 Y
  Try 5: (108, 58)  ← +8 X (doubled)
  Try 6: (108, 66)  ← +8 Y
  ...
```

**충돌 검사 함수 (FUN_1000_12c0)**:
```c
// Called with position in 0x16a7 (X), 0x16a9 (Y)
// Returns collision result in 0x16ae:
//   0 = walkable (valid spawn point)
//   non-zero = collision (wall, pit, etc.)
```

**메모리**:
```
Input:
  0x168f: Player ID (0=P1, 10=P2)
  0xf396: Current scroll X
  0xf398: Current scroll Y

Temporary:
  0x16a7: Search X position
  0x16a9: Search Y position
  0x16ae: Collision result (output of FUN_12c0)
  0x16ad: Tile type

Output (to work buffer):
  0x1697: Entity spawn X
  0x1699: Entity spawn Y
  0x1692: Tile type at spawn
```

---

## 스테이지 데이터 구조

### 스테이지 테이블 구조

**Stage Table @ 0x3fce** (10 bytes):
```c
uint16 stage_data_pointers[5] = {
    0x3fce,  // Stage 1 data pointer
    0x3fd0,  // Stage 2 data pointer
    0x3fd2,  // Stage 3 data pointer
    0x3fd4,  // Stage 4 data pointer
    0x3fd6,  // Stage 5 data pointer (boss)
};
```

**Timer Table @ 0x4404**:
```c
uint16 stage_timers[5] = {
    0x4404,  // Stage 1 timer
    0x4406,  // Stage 2 timer
    0x4408,  // Stage 3 timer
    0x440a,  // Stage 4 timer
    0x440c,  // Stage 5 timer
};
```

**Projectile Data Table @ 0x40c3**:
```c
// 6 projectiles × 18 bytes = 108 bytes total
struct ProjectileData {
    // 18 bytes per projectile
    byte data[18];
};

ProjectileData stage_projectiles[5][6] = {
    // Stage 1
    {{...}, {...}, {...}, {...}, {...}, {...}},
    // Stage 2
    {{...}, {...}, {...}, {...}, {...}, {...}},
    // ... stages 3-5
};
```

### 스테이지별 데이터 로딩

**3개 파일 로딩**:
```
File 1: Main stage data
  Source: 0x1988:0x5690
  Dest: stage_data[0]
  Contains: Level geometry, enemy spawn, etc.

File 2: Tilemap data
  Source: 0x1988:0xe000
  Dest: stage_data[1]
  Contains: Collision map, tile indices

File 3: Additional data
  Source: 0x1988:0x004e
  Dest: stage_data[2]
  Contains: Unknown (small data, 78 bytes?)
```

---

## 엔티티 초기화

### FUN_1000_3e46: 적 엔티티 배열 초기화 (16 bytes)

**역할**: 5개 적 엔티티를 초기화합니다.

```c
void __cdecl16near FUN_1000_3e46(void) {
    int iVar1;
    int iVar2;
    undefined2 unaff_DS;

    iVar2 = 0x16f6;  // Enemy entity array (starts at 0x16f6)
    //       ^^^^^^
    //       0x16c6 (player 1) + 0x18 (24 bytes)
    //       0x16de (player 2) + 0x18 (24 bytes)
    //       = 0x16f6 (enemy 1)

    iVar1 = 5;  // 5 enemies
    do {
        *(undefined1 *)(iVar2 + 2) = 0;  // Set state = 0 (inactive)
        iVar2 = iVar2 + 0x18;  // Next entity (24 bytes)
        iVar1 = iVar1 + -1;
    } while (iVar1 != 0);

    return;
}
```

**엔티티 배열 구조**:
```
Entity array (7 × 24 bytes = 168 bytes):
  0x16c6: Player 1    (24 bytes)
  0x16de: Player 2    (24 bytes)
  0x16f6: Enemy 1     (24 bytes) ← Cleared by FUN_3e46
  0x170e: Enemy 2     (24 bytes)
  0x1726: Enemy 3     (24 bytes)
  0x173e: Enemy 4     (24 bytes)
  0x1756: Enemy 5     (24 bytes)
  Total: 0x16c6 to 0x176d (168 bytes)
```

### FUN_1000_3e56: 프로젝타일 데이터 복사 (23 bytes)

**역할**: 스테이지별 프로젝타일 초기 데이터를 복사합니다.

```c
void __cdecl16near FUN_1000_3e56(void) {
    undefined2 *puVar1;
    undefined2 *puVar2;
    int iVar3;
    undefined2 *puVar4;
    undefined2 *puVar5;
    undefined2 unaff_ES;
    undefined2 unaff_DS;

    // Get stage projectile data pointer
    puVar4 = (undefined2 *)*(undefined2 *)((byte)(*(char *)0x38d0 << 1) + 0x40c3);
    //                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    //                                     projectile_table[stage * 2]

    puVar5 = (undefined2 *)0x3542;  // Projectile array destination
    for (iVar3 = 0x36; iVar3 != 0; iVar3 = iVar3 + -1) {
        //       ^^^^ = 54 words = 108 bytes
        //       6 projectiles × 18 bytes = 108 bytes
        puVar2 = puVar5;
        puVar5 = puVar5 + 1;
        puVar1 = puVar4;
        puVar4 = puVar4 + 1;
        *puVar2 = *puVar1;  // Copy word
    }
    return;
}
```

**프로젝타일 배열**:
```
Projectile array @ 0x3542 (6 × 18 bytes = 108 bytes):
  0x3542: Projectile 1 (18 bytes)
  0x3554: Projectile 2 (18 bytes)
  0x3566: Projectile 3 (18 bytes)
  0x3578: Projectile 4 (18 bytes)
  0x358a: Projectile 5 (18 bytes)
  0x359c: Projectile 6 (18 bytes)
  Total: 0x3542 to 0x35ad (108 bytes)
```

---

## 스테이지별 그래픽 로딩

### FUN_1000_0a96: 일반 스테이지 그래픽 로딩 (94 bytes)

**역할**: 스테이지 1-4의 그래픽 데이터를 로딩합니다.

```c
void __cdecl16near FUN_1000_0a96(void) {
    if (DAT_1988_0035 == '\0') {  // Mode 0
        DAT_1988_320d = 0x5f25;  // Source segment
        DAT_1988_320f = 0;       // Source offset
        DAT_1988_3213 = 0x17e8;  // Destination
        FUN_1000_1e8a();  // Load & decompress
    }
    else {  // Mode 1
        DAT_1988_320d = 0x5f25;
        DAT_1988_320f = 0;
        DAT_1988_3213 = 0x177c;  // Different destination
        FUN_1000_1e8a();
    }

    if (DAT_1988_0035 == '\x01') {  // Mode 1 only
        FUN_1000_0cd1();  // CGA bit plane conversion
    }
    return;
}
```

### FUN_1000_0af5: 보스 스테이지 그래픽 로딩 (94 bytes)

**역할**: 스테이지 5 (보스)의 그래픽 데이터를 로딩합니다.

```c
void __cdecl16near FUN_1000_0af5(void) {
    if (DAT_1988_0035 == '\0') {  // Mode 0
        DAT_1988_320d = 0x5f25;  // Source segment (same)
        DAT_1988_320f = 0;       // Source offset (same)
        DAT_1988_3213 = 0x17fc;  // Different destination!
        FUN_1000_1e8a();
    }
    else {  // Mode 1
        DAT_1988_320d = 0x5f25;
        DAT_1988_320f = 0;
        DAT_1988_3213 = 0x1806;  // Different destination
        FUN_1000_1e8a();
    }

    if (DAT_1988_0035 == '\x01') {
        FUN_1000_0cd1();  // CGA bit plane conversion
    }
    return;
}
```

**차이점**:
```
Normal stages (1-4):
  Mode 0: Dest = 0x17e8
  Mode 1: Dest = 0x177c

Boss stage (5):
  Mode 0: Dest = 0x17fc  (+20 bytes from normal)
  Mode 1: Dest = 0x1806  (+138 bytes from normal)

Source: Same for all (0x5f25:0x0000)
```

---

## 타일맵 주소 변환

### FUN_1000_3e1a: 타일맵 주소 조정 (31 bytes)

**역할**: 타일맵 데이터의 주소를 모드에 따라 변환합니다.

```c
void __cdecl16near FUN_1000_3e1a(void) {
    int iVar1;
    int *piVar2;
    undefined2 unaff_DS;

    piVar2 = (int *)0xe000;  // Tilemap data start
    iVar1 = 0x9c6;  // 2502 words = 5004 bytes

    if (*(char *)0x35 != '\0') {  // Mode 1
        // ========================================
        // Mode 1: Multiply all addresses by 2
        // ========================================
        do {
            *piVar2 = *piVar2 << 1;  // *= 2
            piVar2 = piVar2 + 1;
            iVar1 = iVar1 + -1;
        } while (iVar1 != 0);
        return;
    }

    // ========================================
    // Mode 0: Add offset to all addresses
    // ========================================
    do {
        *piVar2 = *piVar2 + 0x5690;  // += 0x5690
        piVar2 = piVar2 + 1;
        iVar1 = iVar1 + -1;
    } while (iVar1 != 0);
    return;
}
```

**변환 공식**:
```
Mode 0: address' = address + 0x5690
Mode 1: address' = address * 2

Example:
  Original tilemap entry: 0x1000

  Mode 0: 0x1000 + 0x5690 = 0x6690
  Mode 1: 0x1000 * 2      = 0x2000

Purpose:
  - Mode 0: Adjust to actual data segment
  - Mode 1: Scale for different tile size?
```

**타일맵 크기**:
```
2502 words = 5004 bytes

If 16-bit tile indices:
  2502 tiles total

Possible dimensions:
  - 50×50 = 2500 tiles (close!)
  - 51×49 = 2499 tiles
  - 417×6 = 2502 tiles (unlikely)

Likely: ~50×50 tilemap with some overhead
```

---

## 메모리 맵 업데이트

### 스테이지 관련

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x38d0 | 1B | Current stage | 1-5 (1-based) |
| 0x3fce | 10B | Stage data table | 5 pointers |
| 0x40c3 | ?B | Projectile table | Stage-specific |
| 0x4404 | 10B | Timer table | 5 timers |
| 0x38db | 2B | Stage data ptr | From stage data |
| 0x38dd | 2B | Scroll data ptr | From stage data |
| 0x38df | 1B | Stage ready flag | 1=ready |

### 플레이어 스폰

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x16a7 | 2B | Temp spawn X | Search position |
| 0x16a9 | 2B | Temp spawn Y | Search position |
| 0x16ad | 1B | Tile type | At spawn |
| 0x16ae | 1B | Collision flag | FUN_12c0 output |
| 0x168f | 1B | Player ID | 0=P1, 10=P2 |
| 0x1697 | 2B | Entity spawn X | Final position |
| 0x1699 | 2B | Entity spawn Y | Final position |

### 엔티티 배열

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x16c6 | 24B | Player 1 | |
| 0x16de | 24B | Player 2 | |
| 0x16f6 | 24B | Enemy 1 | Cleared by FUN_3e46 |
| 0x170e | 24B | Enemy 2 | |
| 0x1726 | 24B | Enemy 3 | |
| 0x173e | 24B | Enemy 4 | |
| 0x1756 | 24B | Enemy 5 | |

### 프로젝타일 배열

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x3542 | 108B | Projectile array | 6 × 18B |

### 타일맵 데이터

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0xe000 | 5004B | Tilemap data | 2502 tiles |

### 그래픽 데이터

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x17e8 | ?B | Normal stage gfx (Mode 0) | Stages 1-4 |
| 0x177c | ?B | Normal stage gfx (Mode 1) | Stages 1-4 |
| 0x17fc | ?B | Boss stage gfx (Mode 0) | Stage 5 |
| 0x1806 | ?B | Boss stage gfx (Mode 1) | Stage 5 |

---

## 시스템 흐름도

### 스테이지 초기화 흐름

```
New Stage Start
    │
    ├─> FUN_1000_3c7e() [Master init function]
    │   │
    │   ├─> FUN_1000_3e46() [Clear enemy entities]
    │   │   └─> 5 enemies × 24B set to 0
    │   │
    │   ├─> FUN_1000_3e56() [Copy projectile data]
    │   │   └─> 108 bytes from table[stage] → 0x3542
    │   │
    │   ├─> Get stage data pointer
    │   │   └─> stage_table[stage * 2] @ 0x3fce
    │   │
    │   ├─> Load 3 data files
    │   │   ├─> File 1: Main data (0x5690 → table[0])
    │   │   ├─> File 2: Tilemap (0xe000 → table[1])
    │   │   └─> File 3: Additional (0x004e → table[2])
    │   │
    │   ├─> Initialize game state (23 fields)
    │   │   ├─> Scroll X, Y
    │   │   ├─> Player 1 position (X, Y, facing)
    │   │   ├─> Player 2 position (X, Y, facing)
    │   │   ├─> Stage data pointers
    │   │   └─> Various game flags
    │   │
    │   ├─> Initialize rendering
    │   │   ├─> VRAM pointer = 0xb0d0
    │   │   ├─> Frame counter = 0
    │   │   └─> Clear scroll offsets
    │   │
    │   ├─> Load timer
    │   │   └─> timer_table[stage * 2] @ 0x4404
    │   │
    │   ├─> Initialize players (2 players)
    │   │   ├─> State = 0x2a (alive)
    │   │   ├─> HP = 5
    │   │   ├─> Max HP = 20
    │   │   └─> Clear target
    │   │
    │   ├─> FUN_1000_3e1a() [Adjust tilemap addresses]
    │   │   ├─> Mode 0: Add 0x5690 to all
    │   │   └─> Mode 1: Multiply all by 2
    │   │
    │   ├─> Load stage graphics
    │   │   ├─> Stage 5: FUN_1000_0af5() [Boss graphics]
    │   │   └─> Stage 1-4: FUN_1000_0a96() [Normal graphics]
    │   │
    │   └─> BIOS video calls
    │       ├─> Stages 1,2,5: 1× INT 10h
    │       └─> Stages 3,4: 2× INT 10h
    │
    └─> Stage ready!
```

### 플레이어 사망/리스폰 흐름

```
Player HP = 0
    │
    ├─> State = 0x2a (alive)
    ├─> Counter > 0? → Wait (invincibility)
    ├─> State = 0x1e (dying)
    ├─> Death animation...
    └─> State = 0 (dead)
        │
        ├─> FUN_1000_3e6d() [Death handler]
        │   │
        │   ├─> Lives display--
        │   │
        │   ├─> If display < 0:
        │   │   ├─> Check actual lives (0x442c)
        │   │   ├─> If lives = 0:
        │   │   │   └─> Game Over (FUN_4780 handles)
        │   │   │
        │   │   └─> If lives > 0:
        │   │       ├─> Wait for button press
        │   │       ├─> Lives--
        │   │       ├─> Restore display = 2
        │   │       ├─> Clear score low
        │   │       ├─> State = 0x20 (respawning)
        │   │       ├─> Counter = 20
        │   │       ├─> Sprite = none
        │   │       ├─> FUN_1000_3f71() [Find spawn]
        │   │       └─> Reload timer
        │   │
        │   └─> Normal respawn (no button wait)
        │       ├─> State = 0x20
        │       ├─> Counter = 20
        │       └─> FUN_1000_3f71() [Find spawn]
        │
        └─> Player respawned!
```

### 스폰 위치 탐색 알고리즘

```
FUN_1000_3f71() [Find spawn position]
    │
    ├─> Set initial position
    │   ├─> X = scroll_x + 25 (P1) or + 35 (P2)
    │   └─> Y = scroll_y + 20
    │
    ├─> Search loop (spiral pattern)
    │   │
    │   ├─> Check collision at (X, Y)
    │   │   └─> FUN_1000_12c0() → result in 0x16ae
    │   │
    │   ├─> If collision (0x16ae != 0):
    │   │   ├─> Move right (+4)
    │   │   ├─> If searched enough:
    │   │   │   ├─> Move down (+4)
    │   │   │   ├─> Reverse direction (×-1)
    │   │   │   └─> Increase range (×2)
    │   │   └─> Repeat
    │   │
    │   └─> If no collision (0x16ae = 0):
    │       └─> Valid spawn found!
    │
    └─> Set entity position
        ├─> Entity X = found X (0x1697)
        ├─> Entity Y = found Y (0x1699)
        └─> Tile type = 0x16ad

Search pattern visualization:
  →→↓↓←←↓↓→→→→↓↓↓↓ (spiral outward)
  Step size: 4 → 4 → 8 → 8 → 16 → 16 → ...
```

---

## 주요 발견사항 요약

1. **스테이지 테이블 기반 초기화**:
   - 모든 스테이지 데이터가 테이블로 관리됨
   - 0x3fce: 스테이지 데이터 포인터 (5개)
   - 0x4404: 스테이지 타이머 (5개)
   - 0x40c3: 프로젝타일 데이터 (5개)

2. **완전한 스테이지 초기화 과정** (424 bytes!):
   - 3개 데이터 파일 로딩
   - 23개 필드 초기화
   - 플레이어/적 엔티티 설정
   - 타일맵 주소 변환
   - 스테이지별 그래픽 로딩
   - BIOS 비디오 설정

3. **정교한 플레이어 리스폰 시스템**:
   - 생명 표시 vs 실제 생명 분리
   - 버튼 대기 화면 (계속하기)
   - 자동 스폰 위치 탐색
   - 타이머 재로딩

4. **스폰 위치 탐색 알고리즘**:
   - 나선형 검색 패턴
   - 타일맵 충돌 기반
   - 점진적 범위 확대 (4 → 8 → 16 → ...)
   - 플레이어별 오프셋 (P1: +25, P2: +35)

5. **엔티티 배열 구조**:
   - 7개 슬롯 (2 플레이어 + 5 적)
   - 각 24 바이트
   - 적은 스테이지마다 초기화

6. **프로젝타일 시스템**:
   - 6개 슬롯, 각 18 바이트
   - 스테이지별 초기 데이터
   - 테이블에서 복사 (108 bytes)

7. **타일맵 주소 변환**:
   - 5004 bytes (2502 tiles)
   - Mode 0: +0x5690 offset
   - Mode 1: ×2 scaling

8. **스테이지별 그래픽**:
   - 일반 스테이지 (1-4): FUN_0a96
   - 보스 스테이지 (5): FUN_0af5
   - Mode에 따라 다른 목적지

---

## 다음 분석 대상

1. **스테이지 데이터 구조 상세**: 47+ bytes 각 필드의 정확한 역할
2. **타일맵 충돌 검사**: FUN_1000_12c0 상세 분석
3. **적 AI 스폰**: 스테이지에서 적이 어떻게 생성되는지
4. **스테이지 진행**: 다음 스테이지로 넘어가는 조건
5. **스크롤 데이터**: 0x38dd 포인터가 가리키는 데이터 구조

---

**분석자**: Claude Code
**문서 버전**: 1.0
**Phase**: 4.10 완료
**누적 문서**: 9개 (14,000+ 줄)
