# 메인 게임 루프 완전 분석

**작성일**: 2025-11-24
**Phase**: 4.6+ 함수 분석 계속
**분석 함수**: 6개 (핵심 게임 루프 시스템)

---

## 🎯 개요

Double Dragon DOS의 **메인 게임 루프 시스템** 완전 분석입니다. FUN_1000_3830을 중심으로 입력, 업데이트, 렌더링의 전체 프레임 파이프라인을 파악했습니다.

---

## 📊 메인 루프 구조

### 호출 그래프
```
DOS Entry Point
    ↓
FUN_1000_0b94 (초기화 후 메인 루프 시작)
    ↓
╔════════════════════════════════════════════════════════╗
║  FUN_1000_3830 - 메인 게임 루프 (447 bytes)           ║
╠════════════════════════════════════════════════════════╣
║  1. VSync Wait (60 FPS)                                ║
║  2. FUN_1000_3830() - 입력 처리 (자기 호출)            ║
║  3. FUN_1000_0360() - 엔티티 업데이트                  ║
║  4. FUN_1000_03ca() - 엔티티 렌더링 준비               ║
║  5. FUN_1000_20fb() - 투사체 렌더링 준비               ║
║  6. FUN_1000_039e() - 방향 플래그 업데이트             ║
║  7. FUN_1000_211b() - 투사체 추가 처리                 ║
║  8. FUN_1000_029a() - Depth-sorted 렌더링              ║
║  9. FUN_1000_03ea() - 엔티티 후처리                    ║
║ 10. FUN_1000_213b() - 투사체 후처리                    ║
║ 11. FUN_1000_8135() - 화면 업데이트                    ║
║ 12. FUN_1000_034b() - ?                                ║
║ 13. FUN_1000_462a() - ?                                ║
║ 14. FUN_1000_0518() - ?                                ║
║ 15. FUN_1000_4640() - ?                                ║
║ 16. FUN_1000_3fe0() - 스테이지 로직                    ║
║ 17. FUN_1000_05e9() - ?                                ║
║  → 프레임 카운터 증가 (0x16b0)                         ║
╚════════════════════════════════════════════════════════╝
    ↓
Loop (until 0x318e != 0)
```

---

## 🔍 상세 분석

### 1. FUN_1000_3830 - 메인 게임 루프 & 상태 머신

**주소**: 1000:3830
**크기**: 447 bytes
**역할**: 게임 전체 제어, 상태 관리, 메인 루프

#### 핵심 구조
```c
void FUN_1000_3830(void) {
    // === 입력 처리 ===
    FUN_1000_3a20();  // 키보드/조이스틱 입력 읽기

    // === 상태 체크 ===
    if (*(char *)0x38d1 == '\x01') {  // 게임 상태
        // 플레이어 활성 체크
        if (*(char *)0x16c8 == '\0') {  // Player 1 비활성
            goto player1_inactive;
        }
        if (*(char *)0x16e0 == '\0') {  // Player 2 비활성
            goto player2_inactive;
        }

        // 정상 게임 진행
        if (*(int *)0x38d3 != 999) {  // 스크롤 제한 체크
            FUN_1000_39ee();  // 카메라/스크롤 업데이트

            // 특수 이벤트 처리
            if ((*(int *)0x35a0 == 0x2e7a) &&
                (*(char *)0x359e != '\0')) {
                FUN_1000_1d57();  // 이벤트 트리거
            }
            return;
        }

        // === 스테이지 전환 ===
        *(char *)0x38d0 = *(char *)0x38d0 + '\x01';  // 스테이지 ++

        if (*(char *)0x38d0 != '\x06') {  // 스테이지 < 6
            FUN_1000_489a();  // 스테이지 로드
            FUN_1000_3c7e();  // 스테이지 초기화
            FUN_1000_810b();  // 화면 초기화
            goto main_loop;
        }

        // === 스테이지 6 (엔딩) ===
        if (*(char *)0x16c8 == '\0') goto player1_inactive;
        if (*(char *)0x16e0 == '\0') {
            // 엔딩 시퀀스 초기화
            *(char *)0x38d0 = *(char *)0x38d0 + -1;
            *(undefined1 *)0x38d1 = 1;
            // ... 엔딩 데이터 설정 ...

            // === 플레이어 위치 설정 ===
            FUN_1000_1668();  // Entity 1 초기화
            *(undefined1 *)0x16c8 = 0x2a;  // 타입
            *(undefined1 *)0x16c9 = 4;     // 방향
            *(undefined2 *)0x16ce = 0x1e0; // X = 480
            *(undefined2 *)0x16d0 = 0x2d;  // Y = 45

            FUN_1000_1668();  // Entity 2 초기화
            *(undefined1 *)0x16e0 = 0x2a;
            *(undefined2 *)0x16e6 = 500;   // X = 500
            *(undefined2 *)0x16e8 = 0x2d;  // Y = 45

            // === VSync 대기 (320 프레임) ===
            FUN_1000_599d();
            FUN_1000_599d();
            int frames = 0x140;  // 320
            do {
                // VBlank 시작 대기
                do {
                    byte status = in(0x3da);  // CGA status port
                } while ((status & 8) == 0);

                // VBlank 끝 대기
                do {
                    byte status = in(0x3da);
                } while ((status & 8) != 0);

                frames--;
            } while (frames != 0);

            goto main_loop;
        }
    }

    // === 플레이어 비활성 처리 ===
player1_inactive:
    *(undefined1 *)0x38d1 = 1;
    if (*(char *)0x16c8 == '\0') {
        FUN_1000_4780();  // Game Over / Continue
        return;
    }

    // 플레이어 재생성
    int entity_addr = 0x16c6;  // or 0x16de
player2_inactive:
    *(undefined1 *)(entity_addr + 2) = 0x2c;     // 활성화
    *(undefined1 *)(entity_addr + 3) = 3;        // 깊이
    *(undefined2 *)(entity_addr + 6) = 0x19cf;   // 스프라이트 포인터
    *(undefined2 *)(entity_addr + 8) = 0x1cc;    // X = 460
    *(undefined2 *)(entity_addr + 10) = 0x2f;    // Y = 47
    FUN_1000_1668();

    // 스크롤 보정
    if (0x1a4 < *(int *)0xf396) {  // X > 420
        FUN_1000_82f4();  // 스크롤 왼쪽
        if (0xf < *(int *)0xf398) {  // Y > 15
            FUN_1000_822a();  // 스크롤 위
        }
        return;
    }
    if (0xf < *(int *)0xf398) {
        FUN_1000_822a();
        return;
    }

    // === 타이틀 화면 전환 ===
    FUN_1000_3ac0();
    if (*(char *)0x38d2 != '<') {
        return;
    }

    // VSync 대기 (480 프레임)
    FUN_1000_599d();
    int frames = 0x1e0;  // 480
    do {
        // VBlank 대기...
        frames--;
    } while (frames != 0);

    // === 게임 초기화 ===
    // ... 많은 변수 초기화 ...
    DAT_1988_38d0 = 1;    // 스테이지 = 1
    DAT_1988_38d1 = 0;    // 상태 = 0
    DAT_1988_16c8 = 0x2a; // Player 1 활성
    DAT_1988_16e0 = 0x2a; // Player 2 활성
    // ... 더 많은 초기화 ...

    // === 타이틀 루프 ===
    do {
        FUN_1000_59a1();  // 입력 체크

        // 120 프레임 대기
        int wait = 0x78;  // 120
        do {
            if (DAT_1988_318f == '\0') goto start_p1_only;
            if (DAT_1988_3190 == '\0') goto start_2p_mode;

            FUN_1000_0604();  // 대기
            wait--;
        } while (wait != 0);

        // 3번 반복 (총 360 프레임)
    } while (true);

start_p1_only:
    // 플레이어 1만 시작
    if (DAT_1988_0000 == -1) {
        DAT_1988_16e0 = 0;  // Player 2 비활성
        DAT_1988_442a = 0;
    } else {
        DAT_1988_16c8 = 0;  // Player 1 비활성
        DAT_1988_4428 = 0;
        FUN_1000_1c2e();
        DAT_1988_3217 = 1;
    }
    goto setup_game;

start_2p_mode:
    // 2인 플레이 시작
    if (DAT_1988_0000 != -1) {
        FUN_1000_1c2e();
        DAT_1988_3217 = 1;
        DAT_1988_3220 = 1;
    }

setup_game:
    DAT_1988_16b2 = ...;
    FUN_1000_3c7e();  // 게임 초기화
    FUN_1000_810b();  // 화면 초기화

    // === 메인 게임 루프 ===
main_loop:
    do {
        // === VSync 대기 (60 FPS) ===
        do {
        } while (*(byte *)0x318a < 0xf);  // 15 프레임 대기
        *(undefined2 *)0x318a = 0;

        // === 프레임 업데이트 ===
        FUN_1000_3830();  // 입력 처리 (재귀!)
        FUN_1000_0360();  // 엔티티 업데이트
        FUN_1000_03ca();  // 엔티티 렌더링 준비
        FUN_1000_20fb();  // 투사체 렌더링 준비
        FUN_1000_039e();  // 방향 플래그
        FUN_1000_211b();  // 투사체 추가
        FUN_1000_029a();  // Depth-sorted 렌더링
        FUN_1000_03ea();  // 엔티티 후처리
        FUN_1000_213b();  // 투사체 후처리
        FUN_1000_8135();  // 화면 업데이트
        FUN_1000_034b();  // ?
        FUN_1000_462a();  // ?
        FUN_1000_0518();  // ?
        FUN_1000_4640();  // ?
        FUN_1000_3fe0();  // 스테이지 로직

        *(int *)0x16b0 = *(int *)0x16b0 + 1;  // 프레임 카운터++

        FUN_1000_05e9();  // 프레임 종료

    } while (*(char *)0x318e != '\0');  // 게임 종료 체크

    FUN_1000_1ba0();  // 게임 종료 처리
}
```

#### 상태 변수

| 주소 | 크기 | 이름 | 용도 |
|------|------|------|------|
| **0x38d0** | 1B | stage_num | 현재 스테이지 (1~6) |
| **0x38d1** | 1B | game_state | 게임 상태 |
| **0x38d2** | 1B | title_flag | 타이틀 화면 플래그 |
| **0x38d3** | 2B | scroll_min_x | X 스크롤 최소값 |
| **0x16b0** | 2B | frame_counter | 프레임 카운터 |
| **0x16c8** | 1B | player1_active | Player 1 활성 플래그 |
| **0x16e0** | 1B | player2_active | Player 2 활성 플래그 |
| **0x318a** | 2B | vsync_counter | VSync 카운터 |
| **0x318e** | 1B | quit_flag | 게임 종료 플래그 |

#### VSync 동기화
```c
// CGA Status Port (0x3da)
// Bit 3 (0x08): Vertical Retrace
//   1 = VBlank (안전하게 그릴 수 있음)
//   0 = 화면 그리는 중 (기다려야 함)

// 60 FPS 대기
do {
    // VBlank 시작 대기
    do {
        status = in(0x3da);
    } while ((status & 8) == 0);

    // VBlank 끝 대기
    do {
        status = in(0x3da);
    } while ((status & 8) != 0);

    frame_count--;
} while (frame_count != 0);
```

---

### 2. FUN_1000_0360 - 엔티티 업데이트 루프

**주소**: 1000:0360
**크기**: 62 bytes
**역할**: 7개 엔티티 순회하며 게임 로직 업데이트

#### 코드
```c
void FUN_1000_0360(void) {
    int entity_addr = 0x16c6;  // 엔티티 배열 시작

    do {
        // 플레이어 2명(0x16c6~16dd) 또는 활성 엔티티만 처리
        if ((entity_addr < 0x16f6) ||             // Player 1/2
            (*(char *)(entity_addr + 2) != '\0')) // Active flag
        {
            // 1. 엔티티 → 작업 버퍼
            FUN_1000_0412();

            if (*(char *)0x1691 != '\0') {
                // 2. 게임 로직 업데이트
                FUN_1000_16e0();  // AI / 상태 머신

                if (entity_addr < 0x16f6) {  // 플레이어만
                    // 3. 플레이어 전용 로직
                    FUN_1000_039e();  // 방향 체크
                }

                // 4. 충돌 검사
                entity_addr = 0x38b;
                FUN_1000_0e30();  // 충돌 검사
            }

            // 5. 물리 업데이트
            FUN_1000_3e6d();  // 이동, 중력 등

            // 6. 작업 버퍼 → 엔티티
            FUN_1000_041b();
        }

        entity_addr = entity_addr + 0x18;  // +24 bytes
    } while (entity_addr != 0x176e);  // 7개 엔티티
}
```

#### 처리 순서
```
각 엔티티마다:
1. memcpy(작업버퍼, 엔티티, 24)   [FUN_1000_0412]
2. AI / 상태 머신 업데이트         [FUN_1000_16e0]
3. 플레이어 전용 로직 (플레이어만) [FUN_1000_039e]
4. 충돌 검사                       [FUN_1000_0e30]
5. 물리 업데이트 (이동, 중력)      [FUN_1000_3e6d]
6. memcpy(엔티티, 작업버퍼, 24)   [FUN_1000_041b]
```

---

### 3. FUN_1000_0590 - 카메라/뷰포트 계산

**주소**: 1000:0590
**크기**: 89 bytes
**역할**: 플레이어 위치 기반 카메라 계산

#### 코드
```c
void FUN_1000_0590(void) {
    int player1_x, player1_y;
    int player2_x, player2_y;
    int min_x, max_x, min_y, max_y;

    // 1. Player 1 위치 읽기
    player1_x = *(int *)0x16ce;
    player1_y = *(int *)0x16d0;
    if (*(char *)0x16c8 == '\0') {  // P1 비활성
        player1_x = *(int *)0x16e6;  // P2 위치 사용
        player1_y = *(int *)0x16e8;
    }

    // 2. Player 2 위치 읽기
    player2_x = *(int *)0x16e6;
    player2_y = *(int *)0x16e8;
    if (*(char *)0x16e0 == '\0') {  // P2 비활성
        player2_x = player1_x;  // P1 위치 사용
        player2_y = player1_y;
    }

    // 3. Min/Max 계산
    if (player1_x < player2_x) {
        min_x = player1_x;
        max_x = player2_x;
    } else {
        min_x = player2_x;
        max_x = player1_x;
    }

    if (player1_y < player2_y) {
        min_y = player1_y;
        max_y = player2_y;
    } else {
        min_y = player2_y;
        max_y = player1_y;
    }

    // 4. 카메라 경계 업데이트
    if (*(int *)0x16bc < max_x) {
        *(int *)0x16bc = max_x;  // 우측 경계
    }

    // 5. 스크롤 오프셋 적용
    int scroll_x = *(int *)0xf396;
    int scroll_y = *(int *)0xf398;

    *(int *)0x16b6 = max_x - scroll_x;  // 우측 상대 위치
    *(int *)0x16b4 = min_x - scroll_x;  // 좌측 상대 위치
    *(int *)0x16ba = max_y - scroll_y;  // 하단 상대 위치
    *(int *)0x16b8 = min_y - scroll_y;  // 상단 상대 위치
}
```

#### 카메라 계산 방식
```
2인 플레이 카메라:
┌──────────────────────────┐
│                          │
│  P1 ●                    │
│       └─ min_x / min_y   │
│                          │
│               max_x / max_y ─┐
│                    ● P2  │   │
│                          │   │
└──────────────────────────┘   │
                               │
카메라 중심 = (min + max) / 2  ←┘
```

#### 메모리 레이아웃
```
입력:
  0x16ce: Player 1 X
  0x16d0: Player 1 Y
  0x16e6: Player 2 X
  0x16e8: Player 2 Y
  0xf396: 스크롤 X
  0xf398: 스크롤 Y

출력:
  0x16b4: 좌측 경계 (화면 상대)
  0x16b6: 우측 경계 (화면 상대)
  0x16b8: 상단 경계 (화면 상대)
  0x16ba: 하단 경계 (화면 상대)
  0x16bc: 카메라 우측 절대 위치
```

---

### 4. FUN_1000_2711 - 충돌/상호작용 시스템

**주소**: 1000:2711
**크기**: ~150 bytes
**역할**: 엔티티 간 충돌 검사 및 상호작용 (Phase 4.5: 6회 호출)

#### 코드
```c
void FUN_1000_2711(void) {
    char *entity = (char *)0x16c6;  // 엔티티 배열

    do {
        // 1. 활성 엔티티 체크
        if (((*entity != -1) &&              // 유효
             (entity[2] != '\x18') &&        // 상태 != 0x18
             (entity[2] != '<')) &&          // 상태 != 0x3c
            (*(int *)(entity + 6) != -1) &&  // 스프라이트 포인터 유효
            ((*(byte *)(*(int *)(entity + 6) + 6) & 2) != 0)) // 플래그 체크
        {
            // 2. 충돌 검사 함수들
            func_0x0001280c();  // 충돌 타입 1
            if (!success) goto next_entity;

            func_0x00012821();  // 충돌 타입 2
            if (!success) goto next_entity;

            func_0x000127f7();  // 충돌 타입 3
            if (!success) goto next_entity;

            // 3. 충돌 반응
            func_0x000127eb();  // 충돌 처리

            // 4. 특수 케이스: 투사체(0x04)
            if (*(char *)0x3530 == '\x04') {
                if (entity[2] == '\x06') {  // 상태 = 6
                    func_0x00011d84();  // 투사체 반응 1
                    int result = FUN_1000_1b92();

                    if (*(int *)0x353a + result == 0) {
                        *(int *)0x3536 += result * 4;
                        func_0x000123fa();
                        goto next_entity;
                    }
                }

                // 투사체 히트
                *(undefined2 *)0x3534 = 0x2e9e;  // 히트 사운드?
                *(undefined2 *)0x353a = 0;
                entity[5] -= 10;  // HP -10
                func_0x00011d72();  // 히트 이펙트
            }

            // 5. 엔티티 업데이트
            FUN_1000_0412(entity);  // entity → 작업버퍼

            *(undefined1 *)0x1691 = 0x32;     // 타입?
            *(char *)0x1692 += '\x03';         // +3
            *(int *)0x1699 += -3;              // -3
            *(undefined2 *)0x1695 = 0xffff;
            *(undefined2 *)0x169d = 0xfffe;
            *(undefined2 *)0x169b = *(undefined2 *)0x353a;

            FUN_1000_0426();  // 좌표 계산
            FUN_1000_04e1();  // 렌더링 준비

            // 6. 카운터 감소
            char *counter = (char *)0x1694;
            char val = *counter;
            *counter = val - 2;
            if (SBORROW1(val, '\x02') != *counter < '\0') {
                *(undefined1 *)0x1694 = 0;
            }

            FUN_1000_041b();  // 작업버퍼 → entity
            FUN_1000_1668();  // 엔티티 커밋
        }

next_entity:
        entity = entity + 0x18;  // +24 bytes
        if ((char *)0x176d < entity) {
            return;
        }
    } while (true);
}
```

#### 충돌 검사 파이프라인
```
각 엔티티마다:
1. 활성 체크 (타입, 상태, 스프라이트)
2. func_0x0001280c() - 충돌 타입 1 체크
3. func_0x00012821() - 충돌 타입 2 체크
4. func_0x000127f7() - 충돌 타입 3 체크
5. func_0x000127eb() - 충돌 반응 처리
6. 특수 케이스 (투사체 히트 등)
7. 엔티티 상태 업데이트
```

---

### 5. FUN_1000_039e - 방향 플래그 업데이트

**주소**: 1000:039e
**크기**: 44 bytes
**역할**: 엔티티 방향 플립 결정

#### 코드
```c
void FUN_1000_039e(void) {
    int entity_x = *(int *)0x1697;   // 엔티티 X 좌표
    int scroll_x = *(int *)0xf396;   // 스크롤 X
    int relative_x = entity_x - scroll_x;

    // 1. 좌측 경계 (< 12 pixels)
    if ((relative_x < 0xc) &&        // X < 12
        (*(int *)0x169b == -1))      // 현재 왼쪽 향함
    {
        *(undefined2 *)0x169b = 0;   // 방향 초기화
    }

    // 2. 우측 경계 (> 48 pixels)
    if ((0x30 < relative_x) &&       // X > 48
        (*(int *)0x169b == 1))       // 현재 오른쪽 향함
    {
        *(undefined2 *)0x169b = 0;   // 방향 초기화
    }
}
```

#### 동작 원리
```
화면 상대 좌표:
┌──────────────────────────┐
│←12px→                ←48px│
│ [왼쪽 금지]    [오른쪽 금지]│
│                          │
│      [자유 영역]         │
│                          │
└──────────────────────────┘

- X < 12이면서 왼쪽 향함: 방향 리셋
- X > 48이면서 오른쪽 향함: 방향 리셋
→ 화면 밖으로 나가지 않도록 제한
```

---

### 6. FUN_1000_20fb - 투사체 업데이트 루프

**주소**: 1000:20fb
**크기**: 32 bytes
**역할**: 6개 투사체 순회하며 업데이트

#### 코드
```c
void FUN_1000_20fb(void) {
    int projectile = 0x3542;  // 투사체 배열 시작

    do {
        if (*(char *)(projectile + 2) != '\0') {  // 활성 체크
            FUN_1000_2189();  // 투사체 → 작업 버퍼
            FUN_1000_2255();  // 물리 업데이트 (이동, 중력)
            FUN_1000_2192();  // 작업 버퍼 → 투사체
        }

        projectile = projectile + 0x12;  // +18 bytes
    } while (projectile != 0x35ae);  // 6개 투사체
}
```

#### 투사체 구조체 (18 bytes)
```
+0x00 (1B): 타입
+0x01 (1B): ?
+0x02 (1B): 활성 플래그
+0x03 (1B): 깊이 오프셋
+0x04 (2B): ?
+0x06 (2B): X 좌표
+0x08 (2B): Y 좌표
+0x0a (2B): ?
+0x0c (2B): ?
+0x0e (2B): 렌더 데이터 1
+0x10 (2B): 렌더 데이터 2
```

---

## 🧩 전체 프레임 파이프라인

### 완전한 실행 흐름
```
┌─────────────────────────────────────────────────┐
│  1. VSync Wait (60 FPS)                         │
│     └─ Port 0x3da bit 3 체크                    │
├─────────────────────────────────────────────────┤
│  2. 입력 처리                                    │
│     └─ FUN_1000_3a20() - 키보드/조이스틱       │
├─────────────────────────────────────────────────┤
│  3. 카메라 계산                                  │
│     └─ FUN_1000_0590() - 플레이어 위치 기반    │
├─────────────────────────────────────────────────┤
│  4. 엔티티 업데이트 (7개)                       │
│     └─ FUN_1000_0360()                          │
│         ├─ AI / 상태 머신                       │
│         ├─ 충돌 검사                            │
│         └─ 물리 업데이트                        │
├─────────────────────────────────────────────────┤
│  5. 투사체 업데이트 (6개)                       │
│     └─ FUN_1000_20fb()                          │
│         └─ 물리 업데이트 (이동, 중력)           │
├─────────────────────────────────────────────────┤
│  6. 충돌/상호작용                                │
│     └─ FUN_1000_2711()                          │
│         ├─ 엔티티 간 충돌                       │
│         ├─ 투사체 히트                          │
│         └─ 데미지 처리                          │
├─────────────────────────────────────────────────┤
│  7. 렌더링 준비                                  │
│     ├─ FUN_1000_03ca() - 엔티티                │
│     ├─ FUN_1000_20fb() - 투사체                │
│     └─ FUN_1000_039e() - 방향 플래그           │
├─────────────────────────────────────────────────┤
│  8. Depth-sorted 렌더링                         │
│     └─ FUN_1000_029a()                          │
│         ├─ 깊이별 정렬                          │
│         ├─ 렌더링 디스패처 (0x18c6)             │
│         └─ Blit × 4 planes                      │
├─────────────────────────────────────────────────┤
│  9. 화면 업데이트                                │
│     └─ FUN_1000_8135() - VRAM → 화면 버퍼      │
├─────────────────────────────────────────────────┤
│ 10. 스테이지 로직                                │
│     └─ FUN_1000_3fe0() - 스테이지별 이벤트     │
├─────────────────────────────────────────────────┤
│ 11. 프레임 완료                                  │
│     ├─ 프레임 카운터++ (0x16b0)                 │
│     └─ FUN_1000_05e9() - 프레임 종료           │
└─────────────────────────────────────────────────┘
    ↓
Loop (60 FPS)
```

---

## 💡 핵심 발견

### 1. 재귀적 메인 루프
- **FUN_1000_3830이 자기 자신 호출**
- 입력 처리 부분에서 재귀 발생
- 스택 사용 주의 필요

### 2. 60 FPS VSync 동기화
- **CGA Status Port (0x3da)** 사용
- Bit 3으로 VBlank 감지
- 하드웨어 동기화로 정확한 60 FPS

### 3. 이중 배열 시스템
- **엔티티** (7개 × 24B): 플레이어 + 적
- **투사체** (6개 × 18B): 발사체 + 아이템
- 각각 독립적 업데이트 루프

### 4. 작업 버퍼 패턴
```
memcpy(버퍼, 엔티티, 24) → 업데이트 → memcpy(엔티티, 버퍼, 24)
```
- 안전한 상태 관리
- 충돌 시 롤백 가능

### 5. 2인 플레이 카메라
- 두 플레이어 중간 추적
- Min/Max 계산으로 경계 설정
- 동적 스크롤 조정

### 6. 스테이지 전환 시스템
- 스테이지 6 = 엔딩
- VSync 대기로 페이드 효과
- 플레이어 위치 초기화

---

## 🔧 C++ 재구현 가이드

### 클래스 설계
```cpp
class GameLoop {
public:
    void run();           // FUN_1000_3830 메인 루프

private:
    // 서브시스템
    void processInput();       // 입력 처리
    void updateEntities();     // FUN_1000_0360
    void updateProjectiles();  // FUN_1000_20fb
    void updateCamera();       // FUN_1000_0590
    void checkCollisions();    // FUN_1000_2711
    void renderFrame();        // FUN_1000_029a
    void updateStage();        // FUN_1000_3fe0

    // 상태
    GameState state;
    int frame_counter;
    bool quit_flag;
};

class GameState {
public:
    int stage_num;        // 0x38d0
    int game_state;       // 0x38d1
    Entity entities[7];   // 0x16c6
    Projectile projectiles[6];  // 0x3542
    Camera camera;
};

class Camera {
public:
    void update(const Entity& p1, const Entity& p2);  // FUN_1000_0590

    int scroll_x;         // 0xf396
    int scroll_y;         // 0xf398
    int min_x, max_x;     // 0x16b4, 0x16b6
    int min_y, max_y;     // 0x16b8, 0x16ba
};
```

### 60 FPS 타이밍
```cpp
void GameLoop::run() {
    using namespace std::chrono;

    auto frame_time = 16ms;  // 60 FPS = 16.67ms
    auto next_frame = steady_clock::now();

    while (!quit_flag) {
        // VSync 대기
        std::this_thread::sleep_until(next_frame);
        next_frame += frame_time;

        // 프레임 업데이트
        processInput();
        updateEntities();
        updateProjectiles();
        checkCollisions();
        updateCamera();
        renderFrame();
        updateStage();

        frame_counter++;
    }
}
```

---

## 📊 성능 분석

### 시간 복잡도 (프레임당)
- 입력 처리: O(1)
- 엔티티 업데이트: O(n) = O(7)
- 투사체 업데이트: O(m) = O(6)
- 충돌 검사: O(n×m) = O(7×6) = O(42)
- 렌더링: O(n+m) × depth_layers
- **전체**: O(n×m) ≈ O(50) per frame

### 메모리 사용
- 엔티티: 168 bytes (7×24)
- 투사체: 108 bytes (6×18)
- 작업 버퍼: 24 bytes
- 상태 변수: ~100 bytes
- **총합**: ~400 bytes

### CPU 사이클 (추정)
- VSync 대기: ~79,500 사이클 (16.67ms @ 4.77MHz)
- 게임 로직: ~10,000 사이클
- 렌더링: ~30,000 사이클
- **총합**: ~120,000 사이클/프레임
- **여유**: ~40% CPU 여유 있음

---

## 🎓 역사적 의의

### 1988년 게임 구조
1. **재귀적 메인 루프**: 현대적 구조
2. **VSync 동기화**: 하드웨어 직접 제어
3. **이중 배열**: 엔티티 vs 투사체 분리
4. **작업 버퍼 패턴**: 안전한 상태 관리
5. **2인 플레이 카메라**: 동적 추적

이는 1988년 DOS 게임으로는 **매우 정교한 구조**입니다.

---

**분석 완료일**: 2025-11-24
**다음 분석**: AI 상태 머신 (FUN_1000_16e0), 물리 시스템 (FUN_1000_3e6d)
**참고 문서**: [RENDERING_SYSTEM.md](../technical/RENDERING_SYSTEM.md), [MEMORY_MAP.md](../technical/MEMORY_MAP.md)
