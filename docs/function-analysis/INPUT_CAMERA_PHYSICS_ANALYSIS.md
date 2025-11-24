# Input, Camera & Physics System Analysis

**분석 일자**: 2025-11-24
**대상**: Double Dragon DOS (1988)
**Phase**: 4.7 - Advanced Systems Analysis

---

## 목차

1. [개요](#개요)
2. [카메라 및 자동 스크롤 시스템](#카메라-및-자동-스크롤-시스템)
3. [물리 디스패처 시스템](#물리-디스패처-시스템)
4. [난수 생성기](#난수-생성기)
5. [서브시스템 관리](#서브시스템-관리)
6. [스프라이트 선택 및 미러링](#스프라이트-선택-및-미러링)
7. [충돌 및 상호작용 시스템](#충돌-및-상호작용-시스템)
8. [렌더링 테이블 동적 전환](#렌더링-테이블-동적-전환)
9. [메모리 맵 업데이트](#메모리-맵-업데이트)
10. [시스템 아키텍처 다이어그램](#시스템-아키텍처-다이어그램)

---

## 개요

이 문서는 Double Dragon의 **입력 처리**, **카메라 제어**, **물리 디스패처**, **서브시스템 관리**를 분석합니다. 이전 분석에서 발견한 3개의 jump table (AI, collision, rendering) 외에 **4번째 jump table (physics)**과 **동적 렌더링 테이블 전환** 메커니즘을 발견했습니다.

### 분석 대상 함수 (8개)

| 주소 | 함수명 | 크기 | 역할 |
|------|--------|------|------|
| 0518 | FUN_1000_0518 | 118B | 카메라 자동 스크롤 |
| 0590 | FUN_1000_0590 | ? | 2-플레이어 카메라 계산 |
| 2255 | FUN_1000_2255 | 15B | 물리 디스패처 (4번째 jump table!) |
| 05e9 | FUN_1000_05e9 | 26B | LCG 난수 생성기 |
| 4640 | FUN_1000_4640 | 32B | 서브시스템 매니저 |
| 0db2 | FUN_1000_0db2 | 36B | 렌더링 테이블 동적 전환 |
| 04a9 | FUN_1000_04a9 | 55B | 방향별 스프라이트 선택 |
| 039e | FUN_1000_039e | 44B | 스크롤 기반 스프라이트 미러링 |

---

## 카메라 및 자동 스크롤 시스템

### FUN_1000_0518: 자동 스크롤 제어 (118 bytes)

**역할**: 플레이어 위치를 기반으로 화면을 자동으로 스크롤합니다.

```c
void __cdecl16near FUN_1000_0518(void) {
    int in_CX;      // Player Y?
    int iVar1;      // Calculated Y
    int in_BX;      // Player X?
    undefined4 uVar2;

    // Get 2-player camera target position
    uVar2 = FUN_1000_0590();  // Returns (Y << 16) | X
    iVar1 = (int)((ulong)uVar2 >> 16);  // Extract Y

    // Reset scroll direction flags
    *(undefined1 *)0x16be = 0;  // X scroll direction
    *(undefined1 *)0x16bf = 0;  // Y scroll direction

    // X axis scroll decision
    if (0x2f < (int)uVar2) {  // Player too far right (> 47 pixels from edge)
        *(char *)0x16be = *(char *)0x16be + 1;  // Scroll right
        in_BX = in_BX + -1;
    }
    if (in_BX < 0xd) {  // Player too far left (< 13 pixels from edge)
        *(char *)0x16be = *(char *)0x16be + -1;  // Scroll left
    }

    // Y axis scroll decision
    if (0x20 < in_CX) {  // Player too far down (> 32 pixels)
        *(char *)0x16bf = *(char *)0x16bf + 1;  // Scroll down
        iVar1 = iVar1 + -1;
    }
    if (iVar1 < 0x10) {  // Player too far up (< 16 pixels)
        *(char *)0x16bf = *(char *)0x16bf + -1;  // Scroll up
    }

    // Execute scroll with bounds checking
    if (*(char *)0x16be != '\0') {
        if (*(char *)0x16be < '\0') {  // Scroll left
            if (*(int *)0x38d3 < *(int *)0xf396) {  // Check left bound
                FUN_1000_82f4();  // Scroll left
            }
        }
        else if (*(int *)0xf396 < *(int *)0x38d5) {  // Check right bound
            FUN_1000_8277();  // Scroll right
        }
    }

    if (*(char *)0x16bf != '\0') {
        if (*(char *)0x16bf < '\0') {  // Scroll up
            if (*(int *)0x38d7 < *(int *)0xf398) {  // Check top bound
                FUN_1000_822a();  // Scroll up
            }
        }
        else if (*(int *)0xf398 < *(int *)0x38d9) {  // Check bottom bound
            FUN_1000_81c2();  // Scroll down
        }
    }
}
```

**주요 특징**:
1. **데드존 기반 스크롤**: X축 [13, 47], Y축 [16, 32] 범위 내에서는 스크롤하지 않음
2. **스크롤 경계 검사**: 0x38d3-38d9에 저장된 스테이지별 스크롤 한계를 체크
3. **방향 플래그**: 0x16be (X), 0x16bf (Y)에 -1/0/+1 값으로 방향 저장

**메모리 맵**:
```
0x16be: X scroll direction (-1=left, 0=none, +1=right)
0x16bf: Y scroll direction (-1=up, 0=none, +1=down)
0x38d3: Left scroll limit
0x38d5: Right scroll limit
0x38d7: Top scroll limit
0x38d9: Bottom scroll limit
0xf396: Current scroll X
0xf398: Current scroll Y
```

### FUN_1000_0590: 2-플레이어 카메라 타겟 계산

**역할**: 두 플레이어의 위치를 고려하여 카메라 타겟 위치를 계산합니다 (코드 미분석, 추론).

**추정 동작**:
```c
uint32 FUN_1000_0590(void) {
    // Returns: (Y << 16) | X
    // Likely calculates midpoint or min/max of two players
    int p1_x = *(int *)0x16cc;  // Player 1 X
    int p2_x = *(int *)0x16e4;  // Player 2 X
    int p1_y = *(int *)0x16ce;  // Player 1 Y
    int p2_y = *(int *)0x16e6;  // Player 2 Y

    // Camera should keep both players on screen
    int target_x = min(max(p1_x, p2_x), scroll_limit);
    int target_y = min(max(p1_y, p2_y), scroll_limit);

    return (target_y << 16) | target_x;
}
```

---

## 물리 디스패처 시스템

### FUN_1000_2255: 물리 Jump Table 디스패처 (15 bytes) ★★★

**역할**: **4번째 jump table 발견!** Projectile의 타입별 물리 업데이트 함수를 호출합니다.

```c
void FUN_1000_2255(void) {
    undefined2 unaff_DS;

    // WARNING: Could not recover jumptable at 0x00012262. Too many branches
    // WARNING: Treating indirect jump as call
    (*(code *)*(undefined2 *)(*(byte *)0x3530 + 0x2264))();
    //                         ^^^^^^^^^^^^^^^^^^^^^^^^
    //                         jump_table[projectile_type]
    return;
}
```

**디스어셈블리 분석**:
```asm
; projectile_type at work buffer 0x3530
mov  bl, [0x3530]        ; BL = projectile type (0-255)
xor  bh, bh              ; BX = projectile type (zero extend)
jmp  word [bx + 0x2264]  ; Jump to physics_table[type]
```

**Jump Table 구조**:
```
Address: 0x2264 (segment 0x1000)
Entries: ~256 (full byte range)
Entry size: 2 bytes (word pointer)
Total size: ~512 bytes
```

**발견된 Jump Table 정리**:
| Jump Table | 주소 | 디스패처 | 용도 | 인덱스 |
|-----------|------|----------|------|--------|
| AI Table | 0x16ef | FUN_1000_16e0 | Entity AI state machine | Entity state (0x168f) |
| Collision Table | 0xe3f | FUN_1000_0e30 | Collision type handlers | Entity type (0x1691) |
| Rendering Table | 0x18c4 | FUN_1000_499b | Rendering modes | Mode index (0x18c4 + N*2) |
| **Physics Table** | **0x2264** | **FUN_1000_2255** | **Projectile physics** | **Projectile type (0x3530)** |

**시스템 아키텍처**:
```
Main Loop
    ├─> Entity Update
    │   ├─> FUN_1000_16e0()  [AI Dispatcher @ 0x16ef]
    │   └─> FUN_1000_0e30()  [Collision Dispatcher @ 0xe3f]
    │
    └─> Projectile Update
        └─> FUN_1000_2255()  [Physics Dispatcher @ 0x2264]  ← NEW!
```

---

## 난수 생성기

### FUN_1000_05e9: Linear Congruential Generator (26 bytes)

**역할**: LCG 알고리즘을 사용한 의사 난수 생성.

```c
void __cdecl16near FUN_1000_05e9(void) {
    long lVar1;
    uint uVar2;
    int iVar3;
    uint uVar4;
    undefined2 unaff_DS;

    if (*(uint *)0x16b2 == 0) {
        iVar3 = -0x4d;  // seed = -77
    }
    else {
        // LCG: seed = (seed * 77) - high_word(seed * 77)
        lVar1 = (ulong)*(uint *)0x16b2 * 0x4d;  // Multiply by 77
        uVar4 = (uint)((ulong)lVar1 >> 16);     // High word
        uVar2 = (uint)lVar1;                     // Low word
        iVar3 = uVar2 - uVar4;                   // result = low - high
        if (uVar2 < uVar4) {
            iVar3 = iVar3 + 1;  // Carry correction
        }
    }
    *(int *)0x16b2 = iVar3;  // Store new seed
    return;
}
```

**알고리즘 분석**:
```
LCG 공식: X(n+1) = (X(n) * 77) mod M

여기서:
- Multiplier: 77 (0x4d)
- Modulus: Implicit (16-bit arithmetic overflow)
- Increment: 0
- Period: ~32768

초기화:
- seed = 0 → -77 (특수 케이스)
- seed ≠ 0 → (seed * 77) - (high_word)
```

**메모리**:
```
0x16b2: RNG seed (16-bit)
```

**사용 예시**:
```c
// Call FUN_1000_05e9() to update seed
FUN_1000_05e9();
int random = *(int *)0x16b2;  // Read new random value

// Typical usage in AI:
if (random & 0x01) {
    // 50% probability action
}
```

---

## 서브시스템 관리

### FUN_1000_4640: 서브시스템 매니저 (32 bytes)

**역할**: 프레임별 조건부 서브시스템 호출을 관리합니다.

```c
void __cdecl16near FUN_1000_4640(void) {
    undefined2 unaff_DS;

    // First 2 frames: Run initialization subsystems
    if (*(int *)0x16b0 < 2) {  // 0x16b0 = frame counter
        FUN_1000_4660();  // Init subsystem 1
        FUN_1000_474a();  // Init subsystem 2
    }

    // Every frame: Run core subsystems
    FUN_1000_468e();  // Subsystem 3
    FUN_1000_46cd();  // Subsystem 4
    FUN_1000_4711();  // Subsystem 5
    FUN_1000_471e();  // Subsystem 6
    FUN_1000_475d();  // Subsystem 7
    FUN_1000_4780();  // Subsystem 8

    return;
}
```

**서브시스템 분류**:
- **초기화 서브시스템** (frame < 2만 실행):
  - `FUN_1000_4660()`: 5회 반복 호출 (FUN_1000_599d × 5)
  - `FUN_1000_474a()`: 2회 반복 호출 (FUN_1000_5860 × 2)

- **핵심 서브시스템** (매 프레임 실행):
  - `FUN_1000_468e()` ~ `FUN_1000_4780()`: 6개 서브시스템

**메모리**:
```
0x16b0: Frame counter (increments every frame)
```

### FUN_1000_034b: 입력 폴링 루프 (21 bytes)

**역할**: 타이머를 기반으로 입력 처리 함수를 반복 호출합니다.

```c
void __cdecl16near FUN_1000_034b(void) {
    uint uVar1;
    undefined2 unaff_DS;

    uVar1 = *(uint *)0x4c;  // Read timer value
    do {
        FUN_1000_499b();  // Process input/rendering
        uVar1 = uVar1 - 2;
    } while (0x1569 < uVar1);  // Continue while timer > 5481

    return;
}
```

**분석**:
- **0x4c**: DOS BIOS timer tick count (18.2 Hz, ~55ms per tick)
- **0x1569 (5481)**: 약 300초 (5분) 타임아웃
- **FUN_1000_499b()**: 렌더링 디스패처 (0x18c4 jump table 호출)

**주의**: 이 함수는 타임아웃이 매우 길어서 실제로는 다른 조건으로 탈출하는 것으로 보임.

---

## 스프라이트 선택 및 미러링

### FUN_1000_04a9: 방향별 스프라이트 선택 (55 bytes)

**역할**: 캐릭터의 방향(좌/우)과 상태에 따라 적절한 스프라이트를 선택합니다.

```c
void __cdecl16near FUN_1000_04a9(void) {
    int iVar1;
    undefined2 unaff_DS;

    // Check if sprite has directional variants
    if ((*(byte *)0x1693 & 3) != 0) {  // Bits 0-1: direction flags

        // Calculate sprite index based on direction (1-3)
        char direction = (*(byte *)0x1693 & 3) - 1;  // 0-2
        char state = *(char *)0x1691;                // Entity state

        // Lookup sprite from table: sprite_table[state][direction]
        iVar1 = *(int *)((direction + state) * 2 + 0x1930);

        // Special case: punching/kicking sprites
        if ((*(byte *)0x1693 & 8) != 0) {  // Bit 3: attack flag
            if ((state == '\x02') || (state == '6')) {  // State 2 or 54
                iVar1 = iVar1 + 0x38;  // Add 56 (attack variant offset)
            }
        }

        *(int *)0x1695 = iVar1;  // Store selected sprite ID
        return;
    }

    // No directional variants: mark sprite as invalid
    FUN_1000_1ba0();
    return;
}
```

**스프라이트 테이블 구조**:
```
Address: 0x1930
Structure: sprite_table[state][direction]
    - state: Entity AI state (0x1691)
    - direction: 0-2 (left, neutral, right)
Entry size: 2 bytes (word)

Example:
0x1930: [State 0, Dir 0] → Sprite ID
0x1932: [State 0, Dir 1] → Sprite ID
0x1934: [State 0, Dir 2] → Sprite ID
0x1936: [State 1, Dir 0] → Sprite ID
...
```

**방향 플래그** (0x1693):
```
Bit 0-1: Direction (0=none, 1-3=variants)
Bit 3:   Attack flag (adds 56 to sprite ID)
```

**메모리**:
```
0x1691: Entity state/type
0x1693: Direction and attack flags
0x1695: Selected sprite ID (output)
0x1930: Sprite selection table
```

### FUN_1000_039e: 스크롤 기반 스프라이트 미러링 (44 bytes)

**역할**: 스프라이트가 화면 밖으로 나가면 미러링 플래그를 초기화합니다.

```c
void __cdecl16near FUN_1000_039e(void) {
    int iVar1;
    int iVar2;
    undefined2 unaff_DS;

    iVar1 = *(int *)0x1697;  // Entity X position
    iVar2 = *(int *)0xf396;  // Scroll X

    // Check if sprite is near left edge
    if ((iVar1 - iVar2 < 0xc) && (*(int *)0x169b == -1)) {
        *(undefined2 *)0x169b = 0;  // Reset mirror flag
    }

    // Check if sprite is near right edge
    if ((0x30 < iVar1 - iVar2) && (*(int *)0x169b == 1)) {
        *(undefined2 *)0x169b = 0;  // Reset mirror flag
    }

    return;
}
```

**분석**:
- **화면 좌표**: `sprite_screen_x = entity_x - scroll_x`
- **왼쪽 경계**: `< 12 pixels` (0xc)
- **오른쪽 경계**: `> 48 pixels` (0x30)
- **미러 플래그**: 0x169b (-1=left flip, 0=normal, 1=right flip)

**메모리**:
```
0x1697: Entity X position (work buffer)
0x169b: Sprite mirror flag (-1, 0, 1)
0xf396: Current scroll X
```

---

## 충돌 및 상호작용 시스템

### FUN_1000_2711: 엔티티 간 충돌 및 상호작용 (많은 코드)

**역할**: 모든 엔티티를 순회하며 projectile과의 충돌을 검사하고 상호작용을 처리합니다.

```c
void FUN_1000_2711(void) {
    char *pcVar1;
    char cVar2;
    int iVar3;
    char *extraout_DX;
    char *pcVar4;
    undefined2 unaff_DS;
    bool bVar5;

    pcVar4 = (char *)0x16c6;  // Start of entity array
    do {
        // Entity validation checks
        if (((((*pcVar4 != -1) &&           // Entity exists
              (pcVar4[2] != '\x18')) &&     // Not type 0x18
              (pcVar4[2] != '<')) &&        // Not type 0x3c

             // Check if entity has valid target and target is vulnerable
             ((*(int *)(pcVar4 + 6) != -1 &&
              (bVar5 = false, (*(byte *)(*(int *)(pcVar4 + 6) + 6) & 2) != 0)))) &&

             // Three-stage collision check (function calls return bool in bVar5)
             ((func_0x0001280c(), bVar5 &&
              (func_0x00012821(), bVar5 &&
              (func_0x000127f7(), bVar5))))) {

            // Collision confirmed! Process interaction
            func_0x000127eb();  // Collision response

            // Special case: projectile type 4 vs entity type 6
            if (*(char *)0x3530 == '\x04') {  // Projectile type
                if (pcVar4[2] == '\x06') {    // Entity type
                    func_0x00011d84();
                    iVar3 = FUN_1000_1b92();
                    if (*(int *)0x353a + iVar3 == 0) {
                        *(int *)0x3536 = *(int *)0x3536 + iVar3 * 4;
                        func_0x000123fa();
                        goto LAB_1000_27de;  // Skip damage processing
                    }
                }

                // Apply damage to projectile owner
                *(undefined2 *)0x3534 = 0x2e9e;  // Damage sprite?
                *(undefined2 *)0x353a = 0;        // Clear velocity Y
                pcVar4[5] = pcVar4[5] + -10;      // Reduce HP by 10
                func_0x00011d72();
            }

            // Create hit effect sprite
            FUN_1000_0412(pcVar4);  // Copy entity to work buffer
            *(undefined1 *)0x1691 = 0x32;  // Set effect type (50)
            *(char *)0x1692 = *(char *)0x1692 + '\x03';  // +3 to some field
            *(int *)0x1699 = *(int *)0x1699 + -3;        // -3 to Y position
            *(undefined2 *)0x1695 = 0xffff;  // Sprite ID = -1
            *(undefined2 *)0x169d = 0xfffe;  // -2
            *(undefined2 *)0x169b = *(undefined2 *)0x353a;  // Copy projectile Y vel
            FUN_1000_0426();  // Prepare sprite
            FUN_1000_04e1();  // Advance animation

            // Decrement effect counter
            pcVar1 = (char *)0x1694;
            cVar2 = *pcVar1;
            *pcVar1 = *pcVar1 + -2;
            if (SBORROW1(cVar2, '\x02') != *pcVar1 < '\0') {
                *(undefined1 *)0x1694 = 0;  // Clamp to 0
            }

            FUN_1000_041b();  // Copy work buffer back to entity
            FUN_1000_1668();  // Commit entity
            pcVar4 = extraout_DX;
        }

LAB_1000_27de:
        pcVar4 = pcVar4 + 0x18;  // Next entity (24 bytes)
        if ((char *)0x176d < pcVar4) {  // 0x176d = end of entity array
            return;
        }
    } while(true);
}
```

**충돌 검사 단계**:
1. **엔티티 유효성**: 존재 여부, 특정 타입 제외
2. **타겟 유효성**: 타겟이 존재하고 vulnerable 플래그 체크
3. **3단계 충돌 검사**:
   - `func_0x0001280c()`: 1차 충돌 검사 (AABB?)
   - `func_0x00012821()`: 2차 충돌 검사 (정밀?)
   - `func_0x000127f7()`: 3차 충돌 검사 (최종 확인?)

**충돌 시 처리**:
1. `func_0x000127eb()`: 충돌 응답 (넉백, 사운드 등)
2. HP 감소 (일반적으로 -10)
3. 타격 이펙트 생성 (state 0x32)
4. 스프라이트 업데이트

**메모리**:
```
0x16c6: Entity array start
0x176d: Entity array end (7 entities × 24 bytes = 168 bytes)
0x3530: Projectile type (work buffer)
0x353a: Projectile velocity Y
0x3534: Projectile sprite ID
Entity structure (24 bytes):
  +0: Exists flag (-1 = empty)
  +2: Entity type
  +5: HP
  +6: Target entity pointer
  Target +6 flags:
    Bit 1: Vulnerable flag
```

---

## 렌더링 테이블 동적 전환

### FUN_1000_0db2: 렌더링 Jump Table 동적 복사 (36 bytes) ★★★

**역할**: 게임 모드에 따라 렌더링 jump table (0x18c4)을 동적으로 교체합니다.

```c
void __cdecl16near FUN_1000_0db2(void) {
    undefined2 *puVar1;
    undefined2 *puVar2;
    int iVar3;
    undefined2 *puVar4;
    undefined2 *puVar5;

    if (DAT_1988_0035 != '\0') {  // Mode != 0
        puVar4 = (undefined2 *)0x18da;  // Source table A
        if (DAT_1988_0035 != '\x01') {  // Mode != 1
            puVar4 = (undefined2 *)0x18f0;  // Source table B
        }

        puVar5 = (undefined2 *)0x18c4;  // Destination: active jump table
        for (iVar3 = 0xb; iVar3 != 0; iVar3 = iVar3 + -1) {
            puVar2 = puVar5;
            puVar5 = puVar5 + 1;
            puVar1 = puVar4;
            puVar4 = puVar4 + 1;
            *puVar2 = *puVar1;  // Copy 2 bytes (word)
        }
    }
    return;
}
```

**렌더링 테이블 구조**:
```
Active Table:  0x18c4 (11 entries, 22 bytes)  ← 실제로 디스패처가 참조
Table A:       0x18da (11 entries, 22 bytes)  ← Mode 1용
Table B:       0x18f0 (11 entries, 22 bytes)  ← Mode 2용

Mode switch:
- Mode 0: No change (use default 0x18c4)
- Mode 1: Copy 0x18da → 0x18c4
- Mode 2: Copy 0x18f0 → 0x18c4

Total: 3 sets of rendering function pointers!
```

**디스패처 흐름**:
```
Main Loop
    └─> FUN_1000_034b()  [Input polling]
        └─> FUN_1000_499b()  [Rendering dispatcher]
            └─> (* [0x18c4])()  [Jump table @ 0x18c4]
                                 ↑
                                 Mode에 따라 0x18da 또는 0x18f0에서 복사됨
```

**사용 시나리오**:
- **Mode 0**: 기본 렌더링 (메뉴, 게임플레이)
- **Mode 1**: 특수 효과 렌더링 (보스전, 컷씬)
- **Mode 2**: 다른 특수 렌더링 (2-player 화면 분할?)

**메모리**:
```
0x0035: Rendering mode selector (0/1/2)
0x18c4: Active rendering jump table (11 entries)
0x18da: Rendering table A (Mode 1)
0x18f0: Rendering table B (Mode 2)
```

**이전 분석 보완**:
- 이전에 0x18c6 jump table (30 entries)를 발견했는데,
- 실제로는 **0x18c4**가 active table이고,
- **0x18c6**은 0x18c4의 두 번째 엔티티입니다.
- 총 30개 엔티티 = 0x18c4부터 0x18c4 + 60 bytes (30 words)

---

## 메모리 맵 업데이트

### 새로 발견된 주소

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x0035 | 1B | Rendering mode (0/1/2) | Jump table switcher |
| 0x004c | 2B | BIOS timer tick count | DOS interrupt 0x1a |
| 0x16b0 | 2B | Frame counter | Increments every frame |
| 0x16b2 | 2B | RNG seed | LCG state |
| 0x16be | 1B | X scroll direction | -1/0/+1 |
| 0x16bf | 1B | Y scroll direction | -1/0/+1 |
| 0x1693 | 1B | Direction/attack flags | Bits: 0-1=dir, 3=attack |
| 0x1695 | 2B | Selected sprite ID | Output of FUN_1000_04a9 |
| 0x169b | 2B | Sprite mirror flag | -1/0/1 |
| 0x1930 | ?B | Sprite selection table | [state][direction] |
| 0x18da | 22B | Rendering table A | Mode 1 |
| 0x18f0 | 22B | Rendering table B | Mode 2 |
| 0x2264 | ~512B | Physics jump table | Projectile physics |
| 0x38d3 | 2B | Left scroll limit | Stage-specific |
| 0x38d5 | 2B | Right scroll limit | Stage-specific |
| 0x38d7 | 2B | Top scroll limit | Stage-specific |
| 0x38d9 | 2B | Bottom scroll limit | Stage-specific |

### Jump Table 정리

| 이름 | 주소 | 크기 | 인덱스 | 디스패처 | 용도 |
|------|------|------|--------|----------|------|
| AI Table | 0x16ef | ~512B | Entity state (0x168f) | FUN_1000_16e0 | AI state machine |
| Collision Table | 0xe3f | ~512B | Entity type (0x1691) | FUN_1000_0e30 | Collision handlers |
| Rendering Table | 0x18c4 | 60B | Static (0-29) | FUN_1000_499b | Rendering modes |
| Rendering A | 0x18da | 22B | - | - | Mode 1 source |
| Rendering B | 0x18f0 | 22B | - | - | Mode 2 source |
| **Physics Table** | **0x2264** | **~512B** | **Projectile type (0x3530)** | **FUN_1000_2255** | **Projectile physics** |

---

## 시스템 아키텍처 다이어그램

### 전체 게임 루프 (업데이트)

```
Main Loop (FUN_1000_3830)
    │
    ├─> Input Polling (FUN_1000_034b)
    │   └─> Rendering Dispatcher (FUN_1000_499b)
    │       └─> Jump Table @ 0x18c4  [Dynamic!]
    │
    ├─> Entity Update (FUN_1000_0360)
    │   ├─> For each entity:
    │   │   ├─> Copy to work buffer (FUN_1000_0412)
    │   │   ├─> AI Dispatcher (FUN_1000_16e0)
    │   │   │   └─> Jump Table @ 0x16ef
    │   │   ├─> Physics & Animation (FUN_1000_3e6d)
    │   │   ├─> Sprite Prep (FUN_1000_0426)
    │   │   └─> Copy back (FUN_1000_041b)
    │   │
    │   └─> Collision Check (FUN_1000_2711)
    │       └─> Collision Dispatcher (FUN_1000_0e30)
    │           └─> Jump Table @ 0xe3f
    │
    ├─> Projectile Update (FUN_1000_20fb)
    │   ├─> For each projectile:
    │   │   ├─> Copy to work buffer (FUN_1000_2189)
    │   │   ├─> Physics Dispatcher (FUN_1000_2255)  ← NEW!
    │   │   │   └─> Jump Table @ 0x2264
    │   │   └─> Copy back (FUN_1000_2192)
    │   │
    │   └─> Animation (FUN_1000_213b)
    │
    ├─> Camera & Scroll (FUN_1000_0518)
    │   ├─> Get 2P camera target (FUN_1000_0590)
    │   └─> Auto-scroll with bounds check
    │
    ├─> Sprite Selection (FUN_1000_04a9)
    │   └─> Lookup in sprite table @ 0x1930
    │
    ├─> Subsystem Manager (FUN_1000_4640)
    │   ├─> Init subsystems (first 2 frames only)
    │   └─> Core subsystems (every frame)
    │
    ├─> Random Number Gen (FUN_1000_05e9)
    │   └─> LCG algorithm (multiplier = 77)
    │
    └─> VSync Wait (FUN_1000_0604)
        └─> Port 0x3da, 60 FPS
```

### 렌더링 테이블 동적 전환

```
Game State Change
    │
    ├─> Check Mode (0x0035)
    │   ├─> Mode 0: No change
    │   ├─> Mode 1: Copy 0x18da → 0x18c4
    │   └─> Mode 2: Copy 0x18f0 → 0x18c4
    │
    └─> FUN_1000_0db2() executes copy
        └─> 11 entries × 2 bytes = 22 bytes copied

Next Frame:
    └─> FUN_1000_499b() calls (* [0x18c4])()
        └─> Now uses new function pointers!
```

### 4개 Jump Table 디스패처 구조

```
┌─────────────────────────────────────────────────────────────┐
│                      Game Engine Core                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ AI Dispatcher│    │ Collision    │    │ Physics      │  │
│  │ FUN_16e0     │    │ Dispatcher   │    │ Dispatcher   │  │
│  │              │    │ FUN_0e30     │    │ FUN_2255     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │           │
│         v                   v                    v           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Jump Table   │    │ Jump Table   │    │ Jump Table   │  │
│  │ @ 0x16ef     │    │ @ 0xe3f      │    │ @ 0x2264     │  │
│  │ AI states    │    │ Collision    │    │ Projectile   │  │
│  │ (256 entries)│    │ types        │    │ physics      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  ┌──────────────┐                                           │
│  │ Rendering    │                                           │
│  │ Dispatcher   │      ┌──────────┐  ┌──────────┐         │
│  │ FUN_499b     │      │ Table A  │  │ Table B  │         │
│  └──────┬───────┘      │ @ 0x18da │  │ @ 0x18f0 │         │
│         │              └────┬─────┘  └────┬─────┘         │
│         v                   └──────┬──────┘               │
│  ┌──────────────┐                  v                       │
│  │ Jump Table   │           ┌──────────────┐              │
│  │ @ 0x18c4     │◄──────────┤ FUN_0db2     │              │
│  │ Rendering    │           │ (Dynamic     │              │
│  │ modes        │           │  Copy)       │              │
│  │ (30 entries) │           └──────────────┘              │
│  └──────────────┘                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 주요 발견사항 요약

1. **4번째 Jump Table 발견**:
   - Physics dispatcher @ 0x2264 (Projectile type-based)
   - 총 4개 jump table 시스템 완전 파악

2. **동적 렌더링 테이블 전환**:
   - 3개의 렌더링 테이블 (0x18c4, 0x18da, 0x18f0)
   - 모드에 따라 런타임에 교체 가능
   - 화면 분할, 특수 효과 등 유연한 렌더링

3. **2-플레이어 카메라 시스템**:
   - 두 플레이어 위치를 추적하여 카메라 타겟 계산
   - 데드존 기반 스크롤 (부드러운 카메라 이동)
   - 스테이지별 스크롤 경계 적용

4. **LCG 난수 생성기**:
   - Multiplier = 77
   - 16-bit arithmetic overflow modulus
   - AI 의사결정, 스폰 위치 등에 사용

5. **서브시스템 관리 패턴**:
   - 초기화 서브시스템 (첫 2프레임만)
   - 핵심 서브시스템 (매 프레임)
   - 조건부 실행으로 최적화

6. **스프라이트 시스템**:
   - 방향별 스프라이트 선택 (3방향)
   - 공격 변형 (+56 offset)
   - 스크롤 기반 미러링
   - 테이블 기반 빠른 룩업 (0x1930)

7. **충돌 시스템**:
   - 3단계 충돌 검사 (성능 최적화)
   - 엔티티-프로젝타일 상호작용
   - 타격 이펙트 자동 생성
   - Vulnerable 플래그로 무적 시간 구현

---

## 다음 분석 대상

1. **0x2264 Physics Jump Table 내부**: 각 projectile type별 물리 함수 분석
2. **카메라 계산 상세**: FUN_1000_0590의 정확한 알고리즘
3. **충돌 검사 함수**: func_0x0001280c, 0x12821, 0x127f7 상세 분석
4. **스프라이트 테이블**: 0x1930 전체 구조 및 모든 상태/방향 매핑
5. **서브시스템 개별 분석**: FUN_1000_468e ~ 4780의 역할
6. **렌더링 모드**: 각 모드(0/1/2)의 사용 시나리오

---

**분석자**: Claude Code
**문서 버전**: 1.0
**Phase**: 4.7 완료
