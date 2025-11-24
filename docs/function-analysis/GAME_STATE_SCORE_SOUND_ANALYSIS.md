# Game State, Scoring & Sound System Analysis

**분석 일자**: 2025-11-24
**대상**: Double Dragon DOS (1988)
**Phase**: 4.9 - Game State & Score Systems

---

## 목차

1. [개요](#개요)
2. [게임 상태 관리 시스템](#게임-상태-관리-시스템)
3. [BCD 점수 계산 시스템](#bcd-점수-계산-시스템)
4. [점수 표시 시스템](#점수-표시-시스템)
5. [사운드 시스템](#사운드-시스템)
6. [생명 및 게임오버 관리](#생명-및-게임오버-관리)
7. [서브시스템 관리](#서브시스템-관리)
8. [게임 종료 및 정리](#게임-종료-및-정리)
9. [메모리 맵 업데이트](#메모리-맵-업데이트)
10. [시스템 아키텍처](#시스템-아키텍처)

---

## 개요

이 문서는 Double Dragon의 **게임 상태 관리**, **BCD 점수 계산**, **사운드 시스템**을 분석합니다. 특히 281바이트 거대 함수 **FUN_1000_4780**에서 레벨 초기화부터 메인 게임 루프까지 전체 게임 흐름을 발견했으며, 243바이트의 **BCD 산술 연산**을 통한 정교한 점수 계산 시스템을 확인했습니다.

### 분석 대상 함수 (15개)

| 주소 | 함수명 | 크기 | 역할 |
|------|--------|------|------|
| 4780 | FUN_1000_4780 | 281B | 게임 상태 관리 + 메인 루프 ★★★ |
| 30d2 | FUN_1000_30d2 | 243B | BCD 점수 계산 ★★★ |
| 3094 | FUN_1000_3094 | 24B | 점수 표시 업데이트 1 |
| 30ac | FUN_1000_30ac | 35B | 점수 표시 업데이트 2 |
| 1d57 | FUN_1000_1d57 | 33B | 사운드 제어 (PIT) |
| 1ba0 | FUN_1000_1ba0 | 13B | 게임 종료 (INT 10h, 21h) |
| 1bad | FUN_1000_1bad | 95B | 게임 종료 래퍼 |
| 1b92 | FUN_1000_1b92 | 11B | 방향 계산 (-1, 1, 3) |
| 20a0 | FUN_1000_20a0 | 91B | 프로젝타일 스프라이트 설정 |
| 1f0b | FUN_1000_1f0b | 53B | 화면 중앙 정렬 |
| 1c2e | FUN_1000_1c2e | 21B | 입력 초기화 |
| 3824 | FUN_1000_3824 | 5B | abs() 함수 |
| 468e | FUN_1000_468e | 63B | 서브시스템 1 (프레임 기반) |
| 46cd | FUN_1000_46cd | 68B | 서브시스템 2 (타이머 관리) |
| 4711 | FUN_1000_4711 | 13B | 서브시스템 3 (점수 표시) |

---

## 게임 상태 관리 시스템

### FUN_1000_4780: 게임 상태 관리 + 메인 루프 (281 bytes) ★★★★★

**역할**: 게임의 **핵심 제어 함수**입니다. 레벨 초기화, 플레이어 생명 관리, 메인 게임 루프를 모두 담당합니다.

```c
void __cdecl16near FUN_1000_4780(void) {
    byte bVar1;
    int iVar2;
    int iVar3;
    undefined2 unaff_DS;

    // ========================================
    // Part 1: Early return check
    // ========================================
    if ((*(char *)0x16c8 != '\0') || (*(char *)0x16e0 != '\0')) {
        return;  // Players still alive, don't initialize
    }

    // ========================================
    // Part 2: Screen flash effect
    // ========================================
    FUN_1000_599d();  // Call twice for effect
    FUN_1000_599d();
    iVar3 = 0xa0;  // 160 frames
    do {
        // VSync wait
        do {
            bVar1 = in(0x3da);
        } while ((bVar1 & 8) == 0);
        do {
            bVar1 = in(0x3da);
        } while ((bVar1 & 8) != 0);
        iVar3 = iVar3 + -1;
    } while (iVar3 != 0);

    // ========================================
    // Part 3: Check lives remaining
    // ========================================
    if (*(int *)0x442c != 0) {  // 0x442c = lives remaining
        // ========================================
        // Part 3a: Wait for button press (respawn)
        // ========================================
        do {
            FUN_1000_599d();  // Update screen
            FUN_1000_599d();

            iVar3 = 0;
            do {
                // Check for game over conditions
                if ((*(char *)0x3204 == '\0') ||  // Quit flag?
                    (*(char *)0x31c6 == '\0')) {   // Exit flag?
                    goto LAB_1000_482f;  // Player 1 quit
                }
                if (*(char *)0x31d9 == '\0') {  // Player 2 button?
                    goto LAB_1000_4841;  // Player 2 quit
                }
                iVar3 = iVar3 + -1;
            } while (iVar3 != 0);

            FUN_1000_599d();
            FUN_1000_599d();

            // Wait longer (30000 iterations)
            iVar3 = 30000;
            do {
                if ((*(char *)0x3204 == '\0') ||
                    (*(char *)0x31c6 == '\0')) {
                    goto LAB_1000_482f;
                }
                if (*(char *)0x31d9 == '\0') {
                    goto LAB_1000_4841;
                }
                iVar3 = iVar3 + -1;
            } while (iVar3 != 0);
        } while(true);
    }

    // ========================================
    // Part 4: Game Over - Load title screen
    // ========================================
    unaff_DS = 0x1988;
    DAT_1988_320d = 0x1988;  // Source segment
    DAT_1988_320f = 0x5690;  // Source offset
    DAT_1988_3213 = 0x166e;  // Destination
    FUN_1000_1e8a();  // Load & decompress data

    FUN_1000_0612();  // Initialize something

    // Screen flash effect (20 times)
    bVar1 = 0xe;
    iVar3 = 0x14;
    do {
        FUN_1000_0604();  // VSync wait
        FUN_1000_0604();
        FUN_1000_0604();
        out(0x3d9, bVar1);  // CGA color port
        bVar1 = bVar1 ^ 0x1e;  // Toggle colors
        iVar3 = iVar3 + -1;
    } while (iVar3 != 0);

    // ========================================
    // Part 5: Initialize game state for new game
    // ========================================
    DAT_1988_3220 = 0;  // Clear flag
    DAT_1988_3217 = 0;  // Clear flag
    DAT_1988_3204 = 1;  // Set flag
    DAT_1988_31d9 = 1;  // Set flag
    DAT_1988_322d = 0x1f;  // Initialize
    DAT_1988_322e = 0x1f;
    DAT_1988_442c = 5;  // Lives = 5 (Player 1)
    DAT_1988_4428 = 2;  // Lives = 2 (initial display?)
    DAT_1988_442a = 2;  // Lives = 2 (Player 2)
    DAT_1988_4424 = 0;  // Score P1 low
    DAT_1988_4426 = 0;  // Score P2 low
    DAT_1988_38d0 = 1;  // Stage = 1
    DAT_1988_38d1 = 0;  // Stage state
    DAT_1988_38d2 = 0;  // Stage state 2
    DAT_1988_16cc = 0xffff;  // Player 1 target = none
    DAT_1988_16e4 = 0xffff;  // Player 2 target = none
    DAT_1988_16c8 = 0x2a;  // Player 1 state = 0x2a (alive)
    DAT_1988_16e0 = 0x2a;  // Player 2 state = 0x2a (alive)
    DAT_1988_16ca = 5;   // Player 1 HP = 5
    DAT_1988_16e2 = 5;   // Player 2 HP = 5
    DAT_1988_16cb = 0x14;  // Player 1 max HP = 20
    DAT_1988_16e3 = 0x14;  // Player 2 max HP = 20

    // ========================================
    // Part 6: Title screen input loop
    // ========================================
    do {
        iVar3 = FUN_1000_59a1();  // Get input?
        iVar2 = 0x78;  // 120 iterations
        do {
            // Check player 1 input
            if (DAT_1988_318f == '\0') goto LAB_1000_01f5;
            // Check player 2 input
            if (DAT_1988_3190 == '\0') goto LAB_1000_0220;

            iVar3 = FUN_1000_0604();  // VSync
            iVar3 = iVar3 + 1;
            iVar2 = iVar2 + -1;
        } while (iVar2 != 0);

        // Repeat 3 times total (3 × 120 = 360 frames = 6 seconds @ 60 FPS)
        [repeated twice more]
    } while(true);

LAB_1000_482f:
    // Player 1 quit/died
    *(undefined2 *)0x4428 = 2;  // Reset lives display
    *(undefined2 *)0x4424 = 0;  // Reset score
    goto LAB_1000_4850;

LAB_1000_4841:
    // Player 2 quit/died
    *(undefined2 *)0x442a = 2;  // Reset lives display
    *(undefined2 *)0x4426 = 0;  // Reset score

LAB_1000_4850:
    // Respawn player
    FUN_1000_0412();  // Copy to work buffer
    *(undefined1 *)0x1694 = 0x14;  // Set counter = 20
    *(undefined1 *)0x1691 = 0x20;  // Set state = 0x20
    *(undefined2 *)0x1695 = 0xffff;  // Sprite = none
    FUN_1000_3f71();  // Process something
    FUN_1000_041b();  // Copy from work buffer
    *(int *)0x442c = *(int *)0x442c + -1;  // Decrement lives
    FUN_1000_599d();
    FUN_1000_599d();
    *(undefined2 *)0x442e = *(undefined2 *)((byte)(*(char *)0x38d0 << 1) + 0x448c);
    goto LAB_1000_024b;  // Jump to main loop

LAB_1000_01f5:
    // Player 1 pressed button
    if (DAT_1988_0000 == -1) {  // 1-player mode
        DAT_1988_16e0 = 0;  // Disable player 2
        DAT_1988_442a = 0;  // P2 lives = 0
    }
    else {  // 2-player mode
        DAT_1988_16c8 = 0;  // Disable player 1
        DAT_1988_4428 = 0;  // P1 lives = 0
        iVar3 = FUN_1000_1c2e();  // Initialize input
        DAT_1988_3217 = 1;
    }
    goto LAB_1000_0234;

LAB_1000_0220:
    // Player 2 pressed button (2-player mode)
    if (DAT_1988_0000 != -1) {
        iVar3 = FUN_1000_1c2e();
        DAT_1988_3217 = 1;
        DAT_1988_3220 = 1;  // Set 2P flag
    }

LAB_1000_0234:
    DAT_1988_16b2 = iVar3;  // Store RNG seed
    FUN_1000_3c7e();  // Initialize something
    FUN_1000_810b();  // Call hook dispatcher

    // ========================================
    // Part 7: MAIN GAME LOOP ★★★
    // ========================================
LAB_1000_024b:
    do {
        // Wait for timer tick
        do {
        } while (*(byte *)0x318a < 0xf);  // Wait for tick 15
        *(undefined2 *)0x318a = 0;  // Reset timer

        // Main game loop (from FUN_1000_3830)
        FUN_1000_3830();  // Input & stage management
        FUN_1000_0360();  // Entity update
        FUN_1000_03ca();  // Entity render prep
        FUN_1000_20fb();  // Projectile render prep
        FUN_1000_039e();  // Sprite mirroring
        FUN_1000_211b();  // Projectile sprite prep
        FUN_1000_029a();  // Depth-sorted rendering
        FUN_1000_03ea();  // Entity animation (odd frames)
        FUN_1000_213b();  // Projectile animation
        FUN_1000_8135();  // Screen update
        FUN_1000_034b();  // Input polling
        FUN_1000_462a();  // Subsystem (timer)
        FUN_1000_0518();  // Camera auto-scroll
        FUN_1000_4640();  // Subsystem manager
        FUN_1000_3fe0();  // Stage data streaming
        *(int *)0x16b0 = *(int *)0x16b0 + 1;  // Frame counter++
        FUN_1000_05e9();  // RNG update
    } while (*(char *)0x318e != '\0');  // Loop until exit flag

    // Game exit
    FUN_1000_1ba0();  // Cleanup & exit to DOS
    return;
}
```

**함수 구조 분석**:

```
Part 1: Early return (5 lines)
    └─> If players alive, return

Part 2: Screen flash (10 lines)
    └─> VSync wait × 160 frames

Part 3: Lives check (40 lines)
    ├─> If lives > 0: Wait for respawn button
    └─> If lives = 0: Continue to game over

Part 4: Game over screen (15 lines)
    ├─> Load title screen data
    └─> Screen flash effect (20× color toggle)

Part 5: Initialize new game (25 lines)
    ├─> Lives = 5
    ├─> Stage = 1
    ├─> HP = 5/20
    └─> Clear scores

Part 6: Title screen input (40 lines)
    ├─> Wait for button press
    ├─> 1P or 2P mode selection
    └─> 360 frames timeout

Part 7: Main game loop (20 lines)
    ├─> 17 subsystems per frame
    ├─> 60 FPS synchronization
    └─> Exit on flag

Total: 155 lines of C code, 281 bytes assembly
```

**메모리**:
```
Lives:
  0x442c: Player 1 lives (max 5)
  0x442a: Player 2 lives (max 5)
  0x4428, 442a: Lives display values

Player state:
  0x16c8: Player 1 state (0=dead, 0x2a=alive)
  0x16e0: Player 2 state
  0x16ca, 16e2: Current HP
  0x16cb, 16e3: Max HP (20)

Stage:
  0x38d0: Current stage (1-based)
  0x38d1, 38d2: Stage state flags

Flags:
  0x3204, 31c6, 31d9: Input/exit flags
  0x318e: Exit flag (main loop)
  0x318a: Timer tick counter
  0x0000: Player mode (-1=1P, other=2P)
```

---

## BCD 점수 계산 시스템

### FUN_1000_30d2: BCD 산술 연산 (243 bytes) ★★★★★

**역할**: **Binary-Coded Decimal** 형식으로 점수를 계산합니다. 10진수 산술을 정확하게 수행하기 위한 복잡한 알고리즘입니다.

```c
void __cdecl16near FUN_1000_30d2(void) {
    byte bVar1;
    uint uVar3;
    byte bVar4;
    byte bVar5;
    uint in_AX;  // Input: score to add (BCD format)
    int iVar6;
    char *pcVar7;
    undefined2 unaff_DS;
    byte in_AF;
    byte bVar2;

    // ========================================
    // Part 1: Initialize BCD accumulator
    // ========================================
    *(undefined2 *)0x38b9 = 0;  // Low word = 0
    *(undefined2 *)0x38bb = 0;  // Mid word = 0
    *(undefined2 *)0x38b5 = 0;  // High word = 0
    *(undefined2 *)0x38b7 = 0;  // Overflow = 0
    *(undefined1 *)0x38b5 = 1;  // Set multiplier = 1

    // ========================================
    // Part 2: BCD multiplication loop (16 iterations)
    // ========================================
    iVar6 = 0x10;  // 16 bits
    do {
        // Extract bit from input
        uVar3 = in_AX & 1;
        in_AX = in_AX >> 1;

        // If bit is set, add current multiplier to accumulator
        if (uVar3 != 0) {
            // ========================================
            // BCD addition: accumulator += multiplier
            // ========================================
            // Byte 0 (lowest)
            bVar4 = *(byte *)0x38b5 + *(byte *)0x38b9;  // Add bytes
            bVar1 = 9 < (bVar4 & 0xf) | in_AF;  // Check if nibble > 9
            bVar4 = bVar4 + bVar1 * '\x06';  // Add 6 if > 9 (BCD adjust)
            bVar2 = 0x90 < (bVar4 & 0xf0) |  // Check if high nibble > 9
                    CARRY1(*(byte *)0x38b5,*(byte *)0x38b9) |
                    bVar1 * (0xf9 < bVar4);
            *(char *)0x38b9 = bVar4 + bVar2 * '`';  // Add 0x60 if needed

            // Byte 1
            bVar4 = *(byte *)0x38b6 + *(byte *)0x38ba;
            bVar5 = bVar4 + bVar2;  // Add carry
            bVar1 = 9 < (bVar5 & 0xf) | bVar1;
            bVar5 = bVar5 + bVar1 * '\x06';
            bVar2 = 0x90 < (bVar5 & 0xf0) |
                    (CARRY1(*(byte *)0x38b6,*(byte *)0x38ba) ||
                     CARRY1(bVar4,bVar2)) |
                    bVar1 * (0xf9 < bVar5);
            *(char *)0x38ba = bVar5 + bVar2 * '`';

            // Byte 2
            bVar4 = *(byte *)0x38b7 + *(byte *)0x38bb;
            bVar5 = bVar4 + bVar2;
            bVar1 = 9 < (bVar5 & 0xf) | bVar1;
            bVar5 = bVar5 + bVar1 * '\x06';
            bVar2 = 0x90 < (bVar5 & 0xf0) |
                    (CARRY1(*(byte *)0x38b7,*(byte *)0x38bb) ||
                     CARRY1(bVar4,bVar2)) |
                    bVar1 * (0xf9 < bVar5);
            *(char *)0x38bb = bVar5 + bVar2 * '`';

            // Byte 3 (highest)
            bVar4 = *(byte *)0x38b8 + *(byte *)0x38bc;
            bVar5 = bVar4 + bVar2;
            in_AF = 9 < (bVar5 & 0xf) | bVar1;
            bVar5 = bVar5 + in_AF * '\x06';
            *(char *)0x38bc =
                 bVar5 + (0x90 < (bVar5 & 0xf0) |
                         (CARRY1(*(byte *)0x38b8,*(byte *)0x38bc) ||
                          CARRY1(bVar4,bVar2)) |
                         in_AF * (0xf9 < bVar5)) * '`';
        }

        // ========================================
        // BCD multiplication by 2: multiplier *= 2
        // ========================================
        // Byte 0
        bVar4 = *(byte *)0x38b5;
        bVar1 = 9 < (bVar4 * '\x02' & 0xf) | in_AF;
        bVar5 = bVar4 * '\x02' + bVar1 * '\x06';
        bVar2 = 0x90 < (bVar5 & 0xf0) |
                CARRY1(bVar4,bVar4) |
                bVar1 * (0xf9 < bVar5);
        *(char *)0x38b5 = bVar5 + bVar2 * '`';

        // Byte 1
        bVar4 = *(byte *)0x38b6;
        bVar5 = bVar4 * '\x02' + bVar2;
        bVar1 = 9 < (bVar5 & 0xf) | bVar1;
        bVar5 = bVar5 + bVar1 * '\x06';
        bVar2 = 0x90 < (bVar5 & 0xf0) |
                (CARRY1(bVar4,bVar4) ||
                 CARRY1(bVar4 * '\x02',bVar2)) |
                bVar1 * (0xf9 < bVar5);
        *(char *)0x38b6 = bVar5 + bVar2 * '`';

        // Byte 2
        bVar4 = *(byte *)0x38b7;
        bVar5 = bVar4 * '\x02' + bVar2;
        bVar1 = 9 < (bVar5 & 0xf) | bVar1;
        bVar5 = bVar5 + bVar1 * '\x06';
        bVar2 = 0x90 < (bVar5 & 0xf0) |
                (CARRY1(bVar4,bVar4) ||
                 CARRY1(bVar4 * '\x02',bVar2)) |
                bVar1 * (0xf9 < bVar5);
        *(char *)0x38b7 = bVar5 + bVar2 * '`';

        // Byte 3
        bVar4 = *(byte *)0x38b8;
        bVar5 = bVar4 * '\x02' + bVar2;
        in_AF = 9 < (bVar5 & 0xf) | bVar1;
        bVar5 = bVar5 + in_AF * '\x06';
        *(char *)0x38b8 =
             bVar5 + (0x90 < (bVar5 & 0xf0) |
                     (CARRY1(bVar4,bVar4) ||
                      CARRY1(bVar4 * '\x02',bVar2)) |
                     in_AF * (0xf9 < bVar5)) * '`';

        iVar6 = iVar6 + -1;
    } while (iVar6 != 0);

    // ========================================
    // Part 3: Convert BCD to ASCII string
    // ========================================
    s_00000000_1988_38a8[8] = (*(byte *)0x38b9 & 0xf) + 0x30;  // Digit 8
    s_00000000_1988_38a8[7] = (*(byte *)0x38b9 >> 4) + 0x30;   // Digit 7
    s_00000000_1988_38a8[6] = (*(byte *)0x38ba & 0xf) + 0x30;  // Digit 6
    s_00000000_1988_38a8[5] = (*(byte *)0x38ba >> 4) + 0x30;   // Digit 5
    s_00000000_1988_38a8[4] = (*(byte *)0x38bb & 0xf) + 0x30;  // Digit 4
    s_00000000_1988_38a8[3] = (*(byte *)0x38bb >> 4) + 0x30;   // Digit 3
    s_00000000_1988_38a8[2] = (*(byte *)0x38bc & 0xf) + 0x30;  // Digit 2
    s_00000000_1988_38a8[1] = (*(byte *)0x38bc >> 4) + 0x30;   // Digit 1

    // ========================================
    // Part 4: Remove leading zeros
    // ========================================
    for (pcVar7 = (char *)0x38a9; *pcVar7 == '0'; pcVar7 = pcVar7 + 1) {
        *pcVar7 = ' ';  // Replace '0' with ' '
    }

    return;
}
```

**BCD 알고리즘 설명**:

**BCD (Binary-Coded Decimal)**:
```
Each decimal digit is stored in 4 bits (nibble):
  0 = 0x0
  1 = 0x1
  ...
  9 = 0x9

Example: 1234 in BCD
  Byte 0: 0x34 (3 and 4)
  Byte 1: 0x12 (1 and 2)
  → Total: 0x1234 (4 digits, 8 nibbles)
```

**BCD Addition Algorithm**:
```c
// Add two BCD digits
result = digit1 + digit2

// If result > 9, add 6 (BCD adjust)
if ((result & 0x0F) > 9) {
    result = result + 0x06;
    carry = 1;
}

// Same for high nibble
if ((result & 0xF0) > 0x90) {
    result = result + 0x60;
    carry = 1;
}
```

**알고리즘 예시**:
```
Add 50 points (BCD: 0x0050):

Input:  AX = 0x0050
Multiplier: 1 (BCD)
Accumulator: 0 (BCD)

Loop 16 times:
  Iteration 1: bit=0 → skip add, multiply × 2 → multiplier = 2
  Iteration 2: bit=0 → skip add, multiply × 2 → multiplier = 4
  Iteration 3: bit=0 → skip add, multiply × 2 → multiplier = 8
  Iteration 4: bit=0 → skip add, multiply × 2 → multiplier = 16
  Iteration 5: bit=1 → add 16, multiply × 2 → accumulator = 16
  Iteration 6: bit=1 → add 32, multiply × 2 → accumulator = 48
  Iteration 7: bit=0 → skip add, multiply × 2 → multiplier = 64
  ...

Final accumulator: 50 (BCD: 0x0050)
```

**메모리**:
```
BCD Multiplier (4 bytes):
  0x38b5: Byte 0 (low)
  0x38b6: Byte 1
  0x38b7: Byte 2
  0x38b8: Byte 3 (high)

BCD Accumulator (4 bytes):
  0x38b9: Byte 0 (low)
  0x38ba: Byte 1
  0x38bb: Byte 2
  0x38bc: Byte 3 (high)

ASCII String (8 digits):
  0x38a8[1-8]: "12345678" (8 decimal digits)
  → Max score: 99,999,999
```

**성능**:
- 16회 반복 (16-bit input)
- 각 반복: 4 bytes × 2 operations (add + multiply) = 8 bytes
- 총 128 byte operations
- BCD 조정: 각 nibble마다 조건 검사 및 +6/+0x60

---

## 점수 표시 시스템

### FUN_1000_3094: 점수 표시 업데이트 1 (24 bytes)

**역할**: 점수 표시를 업데이트하고 화면에 반영합니다.

```c
void __cdecl16near FUN_1000_3094(void) {
    undefined2 unaff_DS;

    // Toggle display flag
    *(uint *)0x38b3 = *(uint *)0x38b3 ^ 0x200;  // XOR with 0x200

    // Calculate and update score display
    FUN_1000_30d2();  // BCD calculation

    // Set display character
    *(undefined1 *)0x38b1 = 0x30;  // '0' character

    // Update screen
    FUN_1000_599d();

    // Toggle back
    *(uint *)0x38b3 = *(uint *)0x38b3 ^ 0x200;

    return;
}
```

**메모리**:
```
0x38b3: Display mode flag
  Bit 9 (0x200): Toggle flag

0x38b1: Display character ('0' = 0x30)
```

### FUN_1000_30ac: 점수 표시 업데이트 2 (35 bytes)

**역할**: 조건부 점수 표시 업데이트.

```c
void __cdecl16near FUN_1000_30ac(void) {
    int in_AX;
    undefined2 unaff_DS;

    // Toggle display flag
    *(uint *)0x38b3 = *(uint *)0x38b3 ^ 0x200;

    // Calculate score
    FUN_1000_30d2();

    // Conditional character set
    if (in_AX == 0) {
        *(undefined1 *)0x38b0 = 0x30;  // Set 0x38b0
    }
    *(undefined1 *)0x38b1 = 0;  // Clear 0x38b1

    // Update screen
    FUN_1000_599d();

    // Toggle back
    *(uint *)0x38b3 = *(uint *)0x38b3 ^ 0x200;

    return;
}
```

**차이점**:
- FUN_3094: Always set 0x38b1 = '0'
- FUN_30ac: Conditional set 0x38b0, clear 0x38b1

---

## 사운드 시스템

### FUN_1000_1d57: 사운드 제어 (33 bytes)

**역할**: PC Speaker를 제어하여 사운드 효과를 출력합니다.

```c
byte __cdecl16near FUN_1000_1d57(void) {
    byte in_AL;
    byte bVar1;
    undefined2 unaff_DS;

    // Set sound frequency or effect
    *(undefined2 *)0x3229 = 0x336a;  // Frequency/effect code

    // Check if sound is enabled
    if (*(int *)0x322b != 0) {
        // Enable PC Speaker with PIT
        out(0x43, 0xb6);  // PIT command: Channel 2, Mode 3
        //         ^^^^ = 10110110b
        //         Bits 7-6: 10 = Channel 2 (PC Speaker)
        //         Bits 5-4: 11 = Access mode LSB+MSB
        //         Bits 3-1: 011 = Mode 3 (Square Wave)
        //         Bit 0:    0 = Binary counter

        // Read current speaker control
        bVar1 = in(0x61);  // PC keyboard controller port
        //      Bit 0: Timer 2 gate (speaker enable)
        //      Bit 1: Speaker data (on/off)

        // Enable speaker
        out(0x61, bVar1 | 3);  // Set bits 0-1 (enable timer + speaker)

        return bVar1 | 3;
    }

    // Disable sound
    *(undefined2 *)0x3229 = 0;
    return in_AL;
}
```

**PIT Channel 2 (PC Speaker)**:
```
Port 0x43: PIT command register
  Command 0xb6:
    - Channel 2 (PC Speaker)
    - Access: LSB+MSB
    - Mode 3: Square Wave Generator
    - Binary counter

Port 0x40-0x42: PIT data (channels 0-2)
  Channel 2 controls speaker frequency:
  Frequency = 1193180 / divisor

Port 0x61: Keyboard controller
  Bit 0: Timer 2 gate (1=enable)
  Bit 1: Speaker data (1=on)

Enable speaker: out(0x61, in(0x61) | 3)
Disable speaker: out(0x61, in(0x61) & ~3)
```

**메모리**:
```
0x3229: Sound frequency/effect code
0x322b: Sound enable flag (0=off, non-zero=on)
```

**사운드 주파수 예시**:
```
Divisor = 0x336a (13162)
Frequency = 1193180 / 13162 = 90.6 Hz

Common frequencies:
  Middle C (262 Hz): divisor = 4560 (0x11D0)
  A440 (440 Hz):     divisor = 2711 (0x0A97)
  Beep (1000 Hz):    divisor = 1193 (0x04A9)
```

---

## 생명 및 게임오버 관리

### 생명 시스템

**메모리 구조**:
```
Player 1:
  0x442c: Lives remaining (0-5)
  0x4428: Lives display value
  0x4424-4425: Score (BCD, 8 digits)
  0x16c8: State (0=dead, 0x2a=alive)
  0x16ca: Current HP
  0x16cb: Max HP (20)

Player 2:
  0x442a: Lives remaining (0-5)
  0x442a: Lives display value (same address!)
  0x4426-4427: Score (BCD, 8 digits)
  0x16e0: State
  0x16e2: Current HP
  0x16e3: Max HP (20)
```

**생명 감소 로직**:
```c
// When player dies
if (player_hp <= 0) {
    player_state = 0;  // Set to dead

    // FUN_1000_4780 will handle respawn
    if (lives > 0) {
        lives--;  // Decrement lives
        // Wait for button press
        // Respawn player
        player_hp = max_hp;  // Restore HP
        player_state = 0x2a;  // Set to alive
    }
    else {
        // Game over
        // Return to title screen
    }
}
```

### 게임오버 시퀀스

```
1. Both players dead (HP = 0)
2. FUN_1000_4780 called
3. Check lives (0x442c, 0x442a)
4. If lives = 0:
   a. Load title screen (segment 0x5690)
   b. Screen flash effect (20× color toggle)
   c. Initialize game state
      - Lives = 5
      - Stage = 1
      - HP = 5/20
      - Score = 0
   d. Wait for button press (title screen)
5. If lives > 0:
   a. Wait for button press (continue screen)
   b. Respawn player
   c. Decrement lives
   d. Return to main loop
```

---

## 서브시스템 관리

### FUN_1000_468e: 서브시스템 1 (프레임 기반) (63 bytes)

**역할**: 프레임 카운터 기반 서브시스템 호출.

```c
void __cdecl16near FUN_1000_468e(void) {
    uint uVar1;
    undefined2 unaff_DS;

    // Extract bits 1-2 from frame counter
    uVar1 = (*(uint *)0x16b0 & 6) >> 1;  // (frame & 0x06) >> 1
    //       ^^^^^^^^^^^^^^^^
    //       Bits 1-2 of frame counter
    //       → Values: 0, 1, 2, 3 (every 2 frames, cycles every 8 frames)

    if (uVar1 == 1) {
        FUN_1000_3094();  // Score display update
        return;
    }

    if (uVar1 != 2) {
        if (uVar1 != 3) {
            return;  // uVar1 = 0, skip
        }
        FUN_1000_3094();  // Score display update
        return;
    }

    FUN_1000_3094();  // Score display update (uVar1 = 2)
    return;
}
```

**실행 패턴**:
```
Frame counter (0x16b0) & 0x06:
  Frame 0: bits 1-2 = 00 → uVar1 = 0 → skip
  Frame 1: bits 1-2 = 00 → uVar1 = 0 → skip
  Frame 2: bits 1-2 = 10 → uVar1 = 1 → call FUN_3094
  Frame 3: bits 1-2 = 10 → uVar1 = 1 → call FUN_3094
  Frame 4: bits 1-2 = 00 → uVar1 = 2 → call FUN_3094
  Frame 5: bits 1-2 = 00 → uVar1 = 2 → call FUN_3094
  Frame 6: bits 1-2 = 10 → uVar1 = 3 → call FUN_3094
  Frame 7: bits 1-2 = 10 → uVar1 = 3 → call FUN_3094
  Frame 8: bits 1-2 = 00 → uVar1 = 0 → skip (repeat)

Result: Called 6 out of 8 frames (75% rate)
```

### FUN_1000_46cd: 서브시스템 2 (타이머 관리) (68 bytes)

**역할**: 타이머 카운터를 관리하고 점수 표시를 업데이트합니다.

```c
void __cdecl16near FUN_1000_46cd(void) {
    int *piVar1;
    undefined2 unaff_DS;
    bool bVar2;
    bool bVar3;

    // Check if in skip range (frames 1-30)
    if ((*(uint *)0x16b0 & 0x3e) != 0) {
        return;  // Skip if bits 1-5 are set
    }
    //   ^^^^ = 0x3e = 00111110b
    //   Bits 1-5: Frames 2-63 (mod 64)
    //   → Only execute on frames 0, 1, 64, 65, ... (every 64 frames)

    bVar3 = false;
    bVar2 = false;

    // Check if odd frame
    if ((*(uint *)0x16b0 & 1) == 0) {  // Even frame
        piVar1 = (int *)0x442e;  // Timer counter
        bVar3 = SBORROW2(*piVar1, 1);
        *piVar1 = *piVar1 + -1;  // Decrement timer
        bVar2 = *piVar1 < 0;
    }

    if (bVar3 == bVar2) {  // No overflow
        FUN_1000_30ac();  // Update score display
        return;
    }

    // Timer expired
    *(undefined1 *)0x16cb = 0;  // Clear player 1 HP?
    *(undefined1 *)0x16e3 = 0;  // Clear player 2 HP?

    // Reload timer from table
    *(undefined2 *)0x442e = *(undefined2 *)((byte)(*(char *)0x38d0 << 1) + 0x448c);
    //                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    //                                       timer_table[stage * 2]
    *(int *)0x442e = *(int *)0x442e + 1;  // +1 to timer

    return;
}
```

**메모리**:
```
0x442e: Timer counter (decrements every even frame)
0x448c: Timer table (stage-based)
  stage_1_timer = *(int *)(0x448c + 1*2)
  stage_2_timer = *(int *)(0x448c + 2*2)
  ...
```

### FUN_1000_4711: 서브시스템 3 (13 bytes)

**역할**: 단순히 점수 표시를 호출합니다.

```c
void __cdecl16near FUN_1000_4711(void) {
    FUN_1000_30ac();  // Update score display
    return;
}
```

---

## 게임 종료 및 정리

### FUN_1000_1ba0: 게임 종료 (13 bytes)

**역할**: DOS로 복귀하기 전 정리 작업을 수행합니다.

```c
void FUN_1000_1ba0(void) {
    code *pcVar1;
    undefined1 uVar2;

    FUN_1000_1c43();  // Cleanup function

    // Call BIOS video interrupt
    pcVar1 = (code *)swi(0x10);  // INT 10h (Video Services)
    (*pcVar1)();
    //  Likely: Set video mode (text mode)

    // Call DOS interrupt
    pcVar1 = (code *)swi(0x21);  // INT 21h (DOS Services)
    (*pcVar1)();
    //  Likely: Terminate program (AH=4Ch)

    // Save state (probably never executed after INT 21h)
    DAT_1988_3180 = uRam00000024;
    DAT_1988_3182 = uRam00000026;
    uRam0000003c = uRam00000020;
    DAT_1988_3184 = uRam00000020;
    uRam0000003e = uRam00000022;
    DAT_1988_3186 = uRam00000022;

    uVar2 = FUN_1000_1c0c();  // PIT timer cleanup

    // Set interrupt vectors
    uRam00000024 = 0x1db5;
    uRam00000026 = 0x1000;
    uRam00000020 = 0x1c83;
    uRam00000022 = 0x1000;

    DAT_1988_3231 = 1;
    DAT_1988_3230 = 1;

    out(0x201, uVar2);  // Game port?

    return;
}
```

**DOS/BIOS 인터럽트**:
```
INT 10h (BIOS Video Services):
  AH=00h: Set video mode
  AH=03h: Get cursor position
  AH=0Fh: Get current video mode

  Likely: AH=00h, AL=03h (80×25 text mode)

INT 21h (DOS Services):
  AH=4Ch: Terminate program
    AL = return code

  Likely: AH=4Ch, AL=00h (exit with code 0)
```

### FUN_1000_1bad: 게임 종료 래퍼 (95 bytes)

**역할**: FUN_1000_1ba0과 유사하지만 INT 호출 없음.

```c
void __cdecl16near FUN_1000_1bad(void) {
    undefined1 uVar1;

    // Save state
    DAT_1988_3180 = uRam00000024;
    DAT_1988_3182 = uRam00000026;
    uRam0000003c = uRam00000020;
    DAT_1988_3184 = uRam00000020;
    uRam0000003e = uRam00000022;
    DAT_1988_3186 = uRam00000022;

    uVar1 = FUN_1000_1c0c();  // PIT cleanup

    // Set interrupt vectors
    uRam00000024 = 0x1db5;
    uRam00000026 = 0x1000;
    uRam00000020 = 0x1c83;
    uRam00000022 = 0x1000;

    DAT_1988_3231 = 1;
    DAT_1988_3230 = 1;

    out(0x201, uVar1);  // Game port

    return;
}
```

**차이점**: INT 호출 없음 (중간 정리용?)

---

## 메모리 맵 업데이트

### 게임 상태

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x442c | 2B | Player 1 lives | 0-5 |
| 0x442a | 2B | Player 2 lives | 0-5 |
| 0x4428 | 2B | P1 lives display | |
| 0x4424 | 2B | P1 score low | |
| 0x4426 | 2B | P2 score low | |
| 0x442e | 2B | Timer counter | Decrements |
| 0x448c | ?B | Timer table | Stage-based |
| 0x38d0 | 1B | Current stage | 1-based |
| 0x38d1 | 1B | Stage state 1 | |
| 0x38d2 | 1B | Stage state 2 | |
| 0x16c8 | 1B | P1 state | 0=dead, 0x2a=alive |
| 0x16e0 | 1B | P2 state | |
| 0x16ca | 1B | P1 current HP | |
| 0x16cb | 1B | P1 max HP | 20 |
| 0x16e2 | 1B | P2 current HP | |
| 0x16e3 | 1B | P2 max HP | 20 |
| 0x16cc | 2B | P1 target entity | -1=none |
| 0x16e4 | 2B | P2 target entity | -1=none |

### BCD 점수 시스템

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x38b5 | 4B | BCD multiplier | 4 bytes |
| 0x38b9 | 4B | BCD accumulator | 4 bytes |
| 0x38a8 | 9B | ASCII score string | "12345678" |
| 0x38b0 | 1B | Display char 1 | |
| 0x38b1 | 1B | Display char 2 | |
| 0x38b3 | 2B | Display mode flag | Bit 9: toggle |

### 사운드 시스템

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x3229 | 2B | Sound frequency | PIT divisor |
| 0x322b | 2B | Sound enable flag | 0=off |

### 플래그 및 제어

| 주소 | 크기 | 용도 | 비고 |
|------|------|------|------|
| 0x3204 | 1B | Input flag | |
| 0x31c6 | 1B | Exit flag | |
| 0x31d9 | 1B | P2 input flag | |
| 0x318e | 1B | Main loop exit | |
| 0x318a | 1B | Timer tick | Wait for 15 |
| 0x0000 | 2B | Player mode | -1=1P |
| 0x3217 | 1B | Game state flag | |
| 0x3220 | 1B | 2P mode flag | |
| 0x322d | 1B | Init value | 0x1f |
| 0x322e | 1B | Init value | 0x1f |

---

## 시스템 아키텍처

### 게임 전체 흐름

```
Game Start
    │
    ├─> Entry Point
    │   └─> Initialize hardware
    │       ├─> CGA graphics mode
    │       ├─> PIT timer (291.5 Hz)
    │       └─> Load data
    │
    ├─> Title Screen Loop
    │   ├─> FUN_1000_4780()
    │   │   ├─> Initialize game state
    │   │   │   ├─> Lives = 5
    │   │   │   ├─> Stage = 1
    │   │   │   ├─> HP = 5/20
    │   │   │   └─> Score = 0
    │   │   │
    │   │   └─> Wait for button press (360 frames)
    │   │       ├─> 1P mode: Disable P2
    │   │       └─> 2P mode: Enable both
    │   │
    │   └─> Main Game Loop ★
    │
    ├─> Main Game Loop
    │   │
    │   ├─> Frame sync (wait for timer tick 15)
    │   │
    │   ├─> Game logic (17 subsystems)
    │   │   ├─> FUN_1000_3830()  [Input & stage]
    │   │   ├─> FUN_1000_0360()  [Entity update]
    │   │   ├─> FUN_1000_03ca()  [Entity render prep]
    │   │   ├─> FUN_1000_20fb()  [Projectile prep]
    │   │   ├─> FUN_1000_039e()  [Sprite mirroring]
    │   │   ├─> FUN_1000_211b()  [Projectile sprite]
    │   │   ├─> FUN_1000_029a()  [Rendering ★]
    │   │   ├─> FUN_1000_03ea()  [Entity anim]
    │   │   ├─> FUN_1000_213b()  [Projectile anim]
    │   │   ├─> FUN_1000_8135()  [Screen update]
    │   │   ├─> FUN_1000_034b()  [Input polling]
    │   │   ├─> FUN_1000_462a()  [Timer subsystem]
    │   │   ├─> FUN_1000_0518()  [Camera scroll]
    │   │   ├─> FUN_1000_4640()  [Subsystem manager]
    │   │   │   ├─> FUN_1000_468e()  [Score update]
    │   │   │   ├─> FUN_1000_46cd()  [Timer manager]
    │   │   │   └─> FUN_1000_4711()  [Score display]
    │   │   ├─> FUN_1000_3fe0()  [Stage data]
    │   │   ├─> Frame counter++
    │   │   └─> FUN_1000_05e9()  [RNG update]
    │   │
    │   └─> Check exit flag (0x318e)
    │
    ├─> Player Death Event
    │   ├─> HP = 0 → state = 0 (dead)
    │   ├─> FUN_1000_4780() called
    │   ├─> Check lives
    │   │   ├─> Lives > 0:
    │   │   │   ├─> Screen flash (160 frames)
    │   │   │   ├─> Wait for button
    │   │   │   ├─> Respawn player
    │   │   │   ├─> Lives--
    │   │   │   └─> Return to main loop
    │   │   │
    │   │   └─> Lives = 0:
    │   │       ├─> Load title screen
    │   │       ├─> Screen flash (20× color)
    │   │       ├─> Initialize new game
    │   │       └─> Return to title loop
    │   │
    │   └─> Continue
    │
    └─> Game Exit
        ├─> Exit flag set (0x318e)
        ├─> FUN_1000_1ba0()  [Cleanup]
        │   ├─> FUN_1000_1c43()  [Cleanup routine]
        │   ├─> INT 10h  [BIOS: Set text mode]
        │   ├─> INT 21h  [DOS: Terminate program]
        │   └─> PIT cleanup
        │
        └─> Return to DOS
```

### BCD 점수 계산 흐름

```
Score Event (e.g., Enemy defeated)
    │
    ├─> Get score value (e.g., 50 points)
    │
    ├─> FUN_1000_3094() or FUN_1000_30ac()
    │   ├─> Toggle display flag (0x38b3 ^= 0x200)
    │   │
    │   ├─> FUN_1000_30d2()  [BCD calculation ★]
    │   │   ├─> Initialize:
    │   │   │   ├─> Accumulator = current score (BCD)
    │   │   │   └─> Multiplier = 1
    │   │   │
    │   │   ├─> Loop 16 times (for each bit):
    │   │   │   ├─> If bit = 1:
    │   │   │   │   └─> Accumulator += Multiplier (BCD add)
    │   │   │   └─> Multiplier *= 2 (BCD multiply)
    │   │   │
    │   │   ├─> Convert BCD → ASCII:
    │   │   │   ├─> Extract each nibble
    │   │   │   └─> Add 0x30 ('0' character)
    │   │   │
    │   │   └─> Remove leading zeros
    │   │       └─> Replace '0' with ' '
    │   │
    │   ├─> Update display characters
    │   ├─> FUN_1000_599d()  [Refresh screen]
    │   └─> Toggle back display flag
    │
    └─> Score displayed on screen
```

**BCD Addition Example**:
```
Current score: 1000 (BCD: 0x00001000)
Add: 50 (BCD: 0x00000050)

Step-by-step BCD add:
  Byte 0: 0x00 + 0x50 = 0x50
  Byte 1: 0x10 + 0x00 = 0x10
  Byte 2: 0x00 + 0x00 = 0x00
  Byte 3: 0x00 + 0x00 = 0x00

Result: 0x00001050 (BCD)
Decimal: 1050

ASCII conversion:
  Nibbles: 0, 0, 0, 0, 1, 0, 5, 0
  ASCII:   ' ',' ',' ',' ','1',' ','5','0'
  → Display: "   1 50"

After removing leading zeros:
  → Display: "1050"
```

---

## 주요 발견사항 요약

1. **게임 상태 관리의 중심: FUN_1000_4780**:
   - 281바이트 거대 함수
   - 레벨 초기화 + 메인 루프 통합
   - 생명 관리, 게임오버, 리스폰 모두 처리
   - 타이틀 화면부터 게임 종료까지 전체 흐름 제어

2. **정교한 BCD 점수 시스템**:
   - 243바이트 순수 BCD 산술
   - 16-bit 입력 → 32-bit BCD 출력
   - Nibble 단위 조정 (+ 6/+0x60)
   - 최대 99,999,999점 지원

3. **생명 및 리스폰 시스템**:
   - 초기 생명: 5
   - HP: 5/20 (현재/최대)
   - 사망 시 대기 화면 (버튼 입력)
   - 생명 0 → 게임오버 → 타이틀

4. **사운드 시스템**:
   - PC Speaker 제어 (PIT Channel 2)
   - 주파수 기반 효과음
   - Port 0x43 (PIT command)
   - Port 0x61 (Speaker enable)

5. **서브시스템 관리**:
   - 프레임 기반 점수 업데이트 (75% rate)
   - 타이머 관리 (64 프레임마다)
   - 스테이지별 타이머 테이블 (0x448c)

6. **게임 종료 프로세스**:
   - INT 10h (BIOS: Text mode)
   - INT 21h (DOS: Terminate)
   - PIT 타이머 정리
   - 인터럽트 벡터 복원

7. **메인 게임 루프**:
   - 17개 서브시스템
   - 60 FPS 동기화
   - 타이머 틱 대기 (15)
   - 프레임 카운터 증가

8. **1P/2P 모드 관리**:
   - 메모리 0x0000: -1=1P
   - 타이틀 화면에서 선택
   - 플레이어별 독립적 생명/점수

---

## 다음 분석 대상

1. **AI 상태 머신 함수들**: 0x16ef jump table의 실제 AI 함수들
2. **충돌 함수 상세**: func_0x0001280c, 0x12821, 0x127f7
3. **스테이지 데이터 구조**: 0x3ff4 테이블, FUN_1000_3fe0 상세
4. **렌더링 함수**: 0x18c4 테이블의 나머지 20개 함수
5. **입력 처리**: FUN_1000_59a1, 키보드/조이스틱
6. **특수 효과**: 화면 플래시, 페이드 인/아웃

---

**분석자**: Claude Code
**문서 버전**: 1.0
**Phase**: 4.9 완료
**누적 문서**: 8개 (13,000+ 줄)
