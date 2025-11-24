# 엔티티 시스템 완전 분석

**작성일**: 2025-11-24
**Phase**: 4.6+ 함수 분석 계속
**분석 함수**: 7개 (엔티티 업데이트 파이프라인)

---

## 🎯 개요

Double Dragon DOS의 **엔티티 시스템** 완전 분석입니다. 작업 버퍼 패턴, AI 상태 머신, 물리/애니메이션 시스템을 포함한 완전한 업데이트 파이프라인을 파악했습니다.

---

## 📊 엔티티 업데이트 파이프라인

### 전체 흐름
```
┌─────────────────────────────────────────────────┐
│  엔티티 (24 bytes @ 0x16c6 + i×24)              │
│  - 타입, 방향, 상태                              │
│  - X/Y 좌표, HP, 스프라이트 포인터              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  1. FUN_1000_0412 (9 bytes)                     │
│     memcpy(작업버퍼, 엔티티, 24)                │
│     └─> 0x168f ← SI (엔티티 주소)               │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  2. FUN_1000_16e0 (15 bytes)                    │
│     AI 상태 머신 디스패처                        │
│     └─> Jump table @ 0x16ef[state]              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  3. FUN_1000_3e6d (258 bytes)                   │
│     물리 & 애니메이션 시스템                     │
│     ├─> 상태 전환                               │
│     ├─> 타이머 관리                             │
│     └─> 애니메이션 프레임                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  4. FUN_1000_0426 (131 bytes)                   │
│     스프라이트 렌더링 준비                       │
│     ├─> 방향별 스프라이트 선택                  │
│     ├─> 월드 좌표 → 화면 좌표                   │
│     └─> 렌더 리스트에 추가                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  5. FUN_1000_041b (11 bytes)                    │
│     memcpy(엔티티, 작업버퍼, 24)                │
│     └─> SI ← 0x168f (작업버퍼 주소)             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  6. FUN_1000_1668 (44 bytes)                    │
│     엔티티 커밋 & 링크 설정                      │
│     └─> 렌더 데이터 초기화                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  엔티티 (24 bytes @ 0x16c6 + i×24)              │
│  - 업데이트된 상태                               │
└─────────────────────────────────────────────────┘
```

---

## 🔍 상세 분석

### 1. FUN_1000_0412 - 엔티티 → 작업 버퍼

**주소**: 1000:0412
**크기**: 9 bytes
**역할**: 엔티티를 작업 버퍼로 복사

#### 코드
```c
void FUN_1000_0412(void) {
    undefined2 *src = unaff_SI;        // 소스: 엔티티 주소 (레지스터)
    undefined2 *dst = (undefined2 *)0x168f;  // 대상: 작업 버퍼

    // 12 words (24 bytes) 복사
    for (int i = 0xc; i != 0; i = i - 1) {
        *dst = *src;
        dst++;
        src++;
    }
}
```

#### 메모리 레이아웃
```
복사 전:
  SI (엔티티) → [타입][방향][상태]...[X][Y]...
  0x168f      → [이전 데이터]

복사 후:
  0x168f      → [타입][방향][상태]...[X][Y]...
```

#### 추정 용도
- **안전한 업데이트**: 원본 보존
- **충돌 시 롤백**: 필요 시 복원 가능
- **작업 공간**: AI/물리 계산용

---

### 2. FUN_1000_16e0 - AI 상태 머신 디스패처

**주소**: 1000:16e0
**크기**: 15 bytes
**역할**: 엔티티 상태 기반 AI 함수 호출

#### 코드
```c
void FUN_1000_16e0(void) {
    byte state = *(byte *)0x168f;           // 엔티티 상태
    code *func = *(code **)(state + 0x16ef);  // 점프 테이블 @ 0x16ef

    // WARNING: Treating indirect jump as call
    (*func)();  // 상태별 AI 함수 호출
}
```

#### 점프 테이블 구조
```
0x16ef: 점프 테이블 베이스

상태 인덱스:
  0x168f = 0x00 → func @ 0x16ef[0]
  0x168f = 0x01 → func @ 0x16ef[1]
  0x168f = 0x02 → func @ 0x16ef[2]
  ...
  0x168f = 0xFF → func @ 0x16ef[255]
```

#### 추정 상태들
```
0x00: IDLE       - 대기
0x01: WALK       - 이동
0x02: ATTACK     - 공격
0x03: HIT        - 피격
0x04: JUMP       - 점프
0x05: FALL       - 낙하
0x06: DEAD       - 사망
0x0A: SPECIAL    - 특수 동작
...
```

#### 동작 원리
1. **상태 읽기**: 0x168f에서 현재 상태
2. **점프 테이블 참조**: 0x16ef[state] → 함수 포인터
3. **AI 함수 호출**: 상태별 로직 실행
4. **상태 전환**: AI 함수 내에서 0x168f 업데이트 가능

---

### 3. FUN_1000_3e6d - 물리 & 애니메이션 시스템

**주소**: 1000:3e6d
**크기**: 258 bytes
**역할**: 엔티티 물리 및 애니메이션 업데이트

#### 코드
```c
void FUN_1000_3e6d(void) {
    // === 특수 상태 체크 (0x168f) ===
    if ((*(char *)0x168f != '\0') &&      // 상태 != 0
        (*(char *)0x168f != '\n'))        // 상태 != 10
    {
        // 카운터 체크
        if (*(char *)0x1694 != '\0') {    // 타이머 > 0
            return;  // 대기
        }

        // 특정 상태만 처리
        if ((*(int *)0x1695 != 0x1b6c) &&  // 스프라이트 != 0x1b6c
            (*(int *)0x1695 != 0x1b81))    // 스프라이트 != 0x1b81
        {
            return;
        }

        // 비활성화
        *(undefined1 *)0x1691 = 0;
        return;
    }

    // === 활성 엔티티 처리 ===
    if (*(char *)0x1691 != '\0') {         // 활성 플래그
        // 타이머 체크
        if ('\0' < *(char *)0x1694) {
            return;  // 대기
        }

        // 특수 상태 전환
        if ((*(char *)0x1691 == '*') ||    // 타입 = 0x2a
            (*(char *)0x1691 == '\x02'))   // 타입 = 0x02
        {
            *(undefined1 *)0x1691 = 0x1e;   // → 0x1e
            *(undefined2 *)0x1695 = 0xffff; // 스프라이트 리셋
            return;
        }

        // 특정 스프라이트 체크
        if (*(int *)0x1695 != 0x25f0) {
            return;
        }

        // 비활성화
        *(undefined1 *)0x1691 = 0;
    }

    // === 플레이어 타이머 관리 ===
    if (*(char *)0x168f == '\n') {  // Player 2 (상태 = 10)
        // 타이머 감소
        int *timer = (int *)0x442a;
        int val = *timer;
        *timer = val - 1;

        uint new_val = *(uint *)0x442a;
        bool carry = CARRY2(new_val, (uint)(val == 0));
        *(uint *)0x442a = new_val + (val == 0);
    } else {  // Player 1 (상태 = 0)
        // 타이머 감소
        int *timer = (int *)0x4428;
        int val = *timer;
        *timer = val - 1;

        uint new_val = *(uint *)0x4428;
        bool carry = CARRY2(new_val, (uint)(val == 0));
        *(uint *)0x4428 = new_val + (val == 0);
    }

    // === 타이머 만료 처리 ===
    if (carry) {  // 타이머 언더플로우
        if (*(int *)0x442c == 0) {  // 재시작 불가
            return;
        }

        if (*(char *)0x168f == '\n') {  // Player 2
            if (*(char *)0x31d9 != '\0') {
                return;  // 조건 미충족
            }
            *(undefined2 *)0x442a = 2;    // 타이머 리셋 = 2
            *(undefined2 *)0x4426 = 0;
        } else {  // Player 1
            if ((*(char *)0x3204 != '\0') &&
                (*(char *)0x31c6 != '\0')) {
                return;  // 조건 미충족
            }
            *(undefined2 *)0x4428 = 2;    // 타이머 리셋 = 2
            *(undefined2 *)0x4424 = 0;
        }

        // === 상태 전환 ===
        *(undefined1 *)0x1694 = 0x14;     // 카운터 = 20
        *(undefined1 *)0x1691 = 0x20;     // 타입 = 0x20
        *(undefined2 *)0x1695 = 0xffff;   // 스프라이트 리셋
        *(int *)0x442c = *(int *)0x442c + -1;  // 라이프 --

        FUN_1000_3f71();  // 이벤트 트리거

        // 스테이지별 타이머 설정
        *(undefined2 *)0x442e =
            *(undefined2 *)((byte)(*(char *)0x38d0 << 1) + 0x4404);
        return;
    }

    // === 정상 상태 업데이트 ===
    *(undefined1 *)0x1691 = 0x20;     // 타입 = 0x20
    *(undefined2 *)0x1695 = 0xffff;   // 스프라이트 리셋
    *(undefined1 *)0x1694 = 0x14;     // 카운터 = 20

    FUN_1000_3f71();  // 이벤트 트리거
}
```

#### 상태 변수

| 주소 | 크기 | 이름 | 용도 |
|------|------|------|------|
| **0x168f** | 1B | entity_state | 엔티티 상태 (0, 10, ...) |
| **0x1691** | 1B | entity_type | 엔티티 타입 |
| **0x1694** | 1B | counter | 범용 카운터 / 타이머 |
| **0x1695** | 2B | sprite_ptr | 현재 스프라이트 포인터 |
| **0x4428** | 2B | p1_timer | Player 1 타이머 |
| **0x442a** | 2B | p2_timer | Player 2 타이머 |
| **0x442c** | 2B | lives_left | 남은 라이프 |
| **0x442e** | 2B | stage_timer | 스테이지 타이머 |
| **0x38d0** | 1B | stage_num | 현재 스테이지 |

#### 동작 원리

**1. 상태 체크**:
- 0x168f = 0 또는 10: 정상 업데이트
- 그 외: 특수 처리 또는 스킵

**2. 타이머 관리**:
- 0x1694 (카운터): 애니메이션 프레임 딜레이
- 0x4428/442a: 플레이어별 타이머
- 타이머 만료 시 상태 전환

**3. 상태 전환**:
```
타입 0x2a/0x02 → 0x1e (특수 동작)
스프라이트 0x25f0 → 0 (비활성화)
타이머 만료 → 타입 0x20 (리스폰?)
```

---

### 4. FUN_1000_0426 - 스프라이트 렌더링 준비

**주소**: 1000:0426
**크기**: 131 bytes
**역할**: 방향별 스프라이트 선택 및 화면 좌표 계산

#### 코드
```c
void FUN_1000_0426(void) {
    // 1. 스프라이트 포인터 가져오기
    if (*(int *)0x1695 == -1) {
        FUN_1000_04a9();  // 기본 스프라이트 설정
    }

    int *sprite_table = *(int **)*(int *)0x1695;

    // 2. 방향별 오프셋 계산
    byte direction = *(char *)0x1690;

    if (direction == '\x02') {  // DOWN (2)
        sprite_table = sprite_table + 4;  // +8 bytes
    }
    if (direction == '\x06') {  // UP (6)
        sprite_table = sprite_table + 8;  // +16 bytes
    }
    if (direction == '\x04') {  // LEFT (4)
        sprite_table = sprite_table + 0xc;  // +24 bytes
    }
    if (direction == '\b') {  // RIGHT (8)
        sprite_table = sprite_table + 0x10;  // +32 bytes
    }

    // 3. 렌더 리스트 포인터
    int *render_list = *(int **)0x169f;

    // 4. 스프라이트 데이터 복사
    render_list[4] = *sprite_table;  // [+8] 스프라이트 주소

    // 5. Width & Height
    int wh = sprite_table[2];
    render_list[2] = (int)(char)wh;        // [+4] Width (low byte)
    render_list[3] = (int)(char)(wh >> 8); // [+6] Height (high byte)

    // 6. 화면 좌표 계산
    int offset = sprite_table[3];

    // X 좌표 = (offset_x + entity_x) - scroll_x
    render_list[0] = ((int)(char)offset + *(int *)0x1697) -
                     *(int *)0xf396;

    // Y 좌표 = (offset_y + entity_y - scroll_y) * 4
    render_list[1] = (int)(char)(offset >> 8) +
                     (*(int *)0x1699 - *(int *)0xf398) * 4;

    // 7. 깊이 레이어
    render_list[5] = *(int *)(*(char *)0x168f + -0xb10);
}
```

#### 스프라이트 테이블 구조
```
스프라이트 테이블 @ 0x1695:
┌────────────────────────────────────┐
│ [0x00] Direction 0 (기본)          │
│   [+0] 스프라이트 주소              │
│   [+2] Width + Height (16-bit)     │
│   [+4] Offset X + Y (16-bit)       │
│   [+6] ?                           │
├────────────────────────────────────┤
│ [0x08] Direction DOWN (2)          │
│   [+0] 스프라이트 주소              │
│   [+2] Width + Height              │
│   [+4] Offset X + Y                │
│   [+6] ?                           │
├────────────────────────────────────┤
│ [0x10] Direction UP (6)            │
│ [0x18] Direction LEFT (4)          │
│ [0x20] Direction RIGHT (8)         │
└────────────────────────────────────┘
```

#### 렌더 리스트 구조 (0x169f)
```
render_list[0] (+0): X 좌표 (화면 상대)
render_list[1] (+2): Y 좌표 (화면 상대 × 4)
render_list[2] (+4): Width
render_list[3] (+6): Height
render_list[4] (+8): 스프라이트 데이터 주소
render_list[5] (+10): 깊이 레이어
```

#### 방향 매핑
```
0x1690 값  →  오프셋
─────────────────────
  0x00     →  +0      (기본)
  0x02     →  +8      (⬇️ DOWN)
  0x04     →  +24     (⬅️ LEFT)
  0x06     →  +16     (⬆️ UP)
  0x08     →  +32     (➡️ RIGHT)
```

#### 좌표 계산 방식
```
화면 X = (sprite_offset_x + entity_world_x) - scroll_x
화면 Y = (sprite_offset_y + entity_world_y - scroll_y) × 4

× 4 곱셈: CGA scanline interlacing
```

---

### 5. FUN_1000_041b - 작업 버퍼 → 엔티티

**주소**: 1000:041b
**크기**: 11 bytes
**역할**: 작업 버퍼를 엔티티로 복사 (역방향)

#### 코드
```c
void FUN_1000_041b(void) {
    undefined2 *src = (undefined2 *)0x168f;  // 소스: 작업 버퍼
    undefined2 *dst = unaff_SI;              // 대상: 엔티티 (레지스터)

    // 12 words (24 bytes) 복사
    for (int i = 0xc; i != 0; i = i - 1) {
        *dst = *src;
        dst++;
        src++;
    }
}
```

#### 메모리 레이아웃
```
복사 전:
  0x168f      → [업데이트된 상태]...[X][Y]...
  SI (엔티티) → [이전 데이터]

복사 후:
  SI (엔티티) → [업데이트된 상태]...[X][Y]...
```

#### 추정 용도
- **업데이트 커밋**: AI/물리 결과 반영
- **상태 저장**: 다음 프레임을 위해

---

### 6. FUN_1000_1668 - 엔티티 커밋 & 링크

**주소**: 1000:1668
**크기**: 44 bytes
**역할**: 엔티티 렌더 데이터 초기화 및 링크 설정

#### 코드
```c
void FUN_1000_1668(void) {
    int link_addr = *(int *)(unaff_SI + 0x12);  // +18: 링크 포인터

    if (link_addr != -1) {
        // 1. 링크 해제
        *(undefined2 *)(unaff_SI + 0x12) = 0xffff;  // 자신의 링크 = -1

        // 2. 대상 엔티티 초기화
        *(undefined2 *)(link_addr + 0x10) = 0xffff;  // 렌더 데이터 1 = -1
        *(undefined1 *)(link_addr + 2) = 4;          // 상태 = 4
        *(undefined2 *)(link_addr + 4) = 0xffff;     // ? = -1
        *(undefined2 *)(link_addr + 0xc) = 0xfffe;   // ? = -2

        // 3. Y 좌표 설정
        uVar1 = FUN_1000_1b92();  // Y 좌표 계산?
        *(undefined2 *)(link_addr + 10) = uVar1;  // +10: Y 좌표
    }
}
```

#### 엔티티 구조체 (24 bytes)
```
+0x00 (1B): 타입
+0x01 (1B): 방향
+0x02 (1B): 상태
+0x03 (1B): 깊이 오프셋
+0x04 (2B): ?
+0x06 (2B): 스프라이트 테이블 포인터
+0x08 (2B): X 좌표
+0x0a (2B): Y 좌표
+0x0c (2B): ?
+0x0e (2B): ?
+0x10 (2B): 렌더 데이터 1
+0x12 (2B): 렌더 데이터 2 / 링크 포인터
+0x14 (2B): ?
+0x16 (2B): ?
```

#### 동작 원리
1. **링크 체크**: +0x12에 링크 주소 있는지
2. **링크 해제**: 자신의 링크 = -1
3. **대상 초기화**: 링크된 엔티티 상태 리셋
4. **Y 좌표 설정**: FUN_1000_1b92()로 계산

#### 추정 용도
- **부모-자식 관계**: 무기와 캐릭터
- **연결 엔티티**: 투사체 발사 시
- **이펙트 생성**: 히트 이펙트 등

---

## 🧩 작업 버퍼 시스템 (0x168f)

### 메모리 레이아웃
```
작업 버퍼 @ 0x168f (24 bytes):
┌────────────────────────────────────┐
│ +0x00: 상태 (0, 10, ...)            │  ← AI 디스패처 인덱스
│ +0x01: 방향 (2,4,6,8)               │  ← 스프라이트 선택
│ +0x02: 타입                         │
│ +0x03: 깊이 오프셋                  │
│ +0x04: ?                            │
│ +0x05: 카운터 (0x1694)              │  ← 타이머
│ +0x06: 스프라이트 포인터 (0x1695)    │  ← 렌더링
│ +0x08: X 좌표 (0x1697)              │  ← 월드 좌표
│ +0x0a: Y 좌표 (0x1699)              │
│ +0x0c: 방향 플래그 (0x169b)         │  ← -1/0/1
│ +0x0e: ?                            │
│ +0x10: 렌더 리스트 포인터 (0x169f)   │
│ +0x12: ?                            │
│ +0x14: ?                            │
│ +0x16: ?                            │
└────────────────────────────────────┘
```

### 주요 오프셋
| 오프셋 | 주소 | 이름 | 용도 |
|--------|------|------|------|
| +0x00 | 0x168f | state | AI 상태 |
| +0x01 | 0x1690 | direction | 방향 (2,4,6,8) |
| +0x02 | 0x1691 | type | 엔티티 타입 |
| +0x05 | 0x1694 | counter | 범용 카운터 |
| +0x06 | 0x1695 | sprite_ptr | 스프라이트 포인터 |
| +0x08 | 0x1697 | x_pos | X 좌표 |
| +0x0a | 0x1699 | y_pos | Y 좌표 |
| +0x0c | 0x169b | dir_flag | 방향 플래그 |
| +0x10 | 0x169f | render_list | 렌더 리스트 |

---

## 💡 핵심 발견

### 1. 작업 버퍼 패턴
```
memcpy(버퍼, 엔티티, 24)
    ↓
AI + 물리 업데이트 (버퍼 조작)
    ↓
memcpy(엔티티, 버퍼, 24)
```
- **안전성**: 업데이트 실패 시 롤백 가능
- **격리**: 엔티티 간 간섭 방지
- **디버깅**: 중간 상태 검사 용이

### 2. AI 상태 머신 (Jump Table)
```c
state = entity->state;
ai_func = jump_table[state];
ai_func();  // 상태별 로직 실행
```
- **유연성**: 상태 추가 용이
- **성능**: O(1) 디스패치
- **모듈화**: 상태별 함수 분리

### 3. 방향 기반 스프라이트
```
방향 2 (DOWN)  → sprite_table + 8
방향 4 (LEFT)  → sprite_table + 24
방향 6 (UP)    → sprite_table + 16
방향 8 (RIGHT) → sprite_table + 32
```
- **4방향 지원**: 상하좌우
- **자동 선택**: 방향 값으로 오프셋 계산
- **메모리 효율**: 테이블 기반

### 4. 화면 좌표 계산
```c
screen_x = (sprite_offset_x + world_x) - scroll_x
screen_y = (sprite_offset_y + world_y - scroll_y) × 4
```
- **월드 좌표**: 절대 위치
- **스크롤 보정**: 카메라 이동 반영
- **CGA 보정**: Y × 4 (인터레이스)

### 5. 타이머 시스템
- **플레이어별 타이머**: 0x4428, 0x442a
- **라이프 관리**: 0x442c
- **상태 전환**: 타이머 만료 → 리스폰

### 6. 링크 시스템
- **부모-자식**: +0x12 오프셋
- **초기화**: 링크 해제 시 상태 리셋
- **용도**: 무기, 투사체, 이펙트

---

## 🔧 C++ 재구현 가이드

### 클래스 설계
```cpp
// 엔티티 구조체
struct Entity {
    uint8_t  type;         // +0x00
    uint8_t  direction;    // +0x01: 2,4,6,8
    uint8_t  state;        // +0x02
    uint8_t  depth_offset; // +0x03
    int16_t  field_04;     // +0x04
    int16_t  sprite_ptr;   // +0x06
    int16_t  x_pos;        // +0x08
    int16_t  y_pos;        // +0x0a
    int16_t  field_0c;     // +0x0c
    int16_t  field_0e;     // +0x0e
    int16_t  render_data1; // +0x10
    int16_t  link_ptr;     // +0x12
    int16_t  field_14;     // +0x14
    int16_t  field_16;     // +0x16
};

// 엔티티 시스템
class EntitySystem {
public:
    void updateEntity(int index);

private:
    // 작업 버퍼
    Entity work_buffer;  // 0x168f

    // 업데이트 파이프라인
    void copyToWorkBuffer(const Entity& src);   // FUN_1000_0412
    void dispatchAI();                          // FUN_1000_16e0
    void updatePhysics();                       // FUN_1000_3e6d
    void prepareSprite();                       // FUN_1000_0426
    void copyFromWorkBuffer(Entity& dst);       // FUN_1000_041b
    void commitEntity();                        // FUN_1000_1668

    // AI 점프 테이블
    using AIFunc = void (EntitySystem::*)();
    std::array<AIFunc, 256> ai_jump_table;  // 0x16ef
};
```

### 업데이트 루프
```cpp
void EntitySystem::updateEntity(int index) {
    Entity& entity = entities[index];

    // 1. 작업 버퍼로 복사
    copyToWorkBuffer(entity);

    // 2. AI 상태 머신
    dispatchAI();

    // 3. 물리 & 애니메이션
    updatePhysics();

    // 4. 스프라이트 준비
    prepareSprite();

    // 5. 엔티티로 복사
    copyFromWorkBuffer(entity);

    // 6. 커밋
    commitEntity();
}
```

### AI 디스패처
```cpp
void EntitySystem::dispatchAI() {
    uint8_t state = work_buffer.state;
    AIFunc func = ai_jump_table[state];
    (this->*func)();  // 멤버 함수 포인터 호출
}

// AI 상태 등록
void EntitySystem::setupAI() {
    ai_jump_table[0x00] = &EntitySystem::aiIdle;
    ai_jump_table[0x01] = &EntitySystem::aiWalk;
    ai_jump_table[0x02] = &EntitySystem::aiAttack;
    // ...
}
```

---

## 📊 성능 분석

### 시간 복잡도 (엔티티당)
- memcpy (to): O(1) - 24 bytes
- AI dispatch: O(1) - 점프 테이블
- Physics: O(1) - 고정 로직
- Sprite prep: O(1) - 방향 선택
- memcpy (from): O(1) - 24 bytes
- **전체**: O(1) per entity

### 메모리 사용
- 작업 버퍼: 24 bytes (고정)
- 엔티티 배열: 168 bytes (7×24)
- AI 점프 테이블: 512 bytes (256×2)
- **총합**: ~700 bytes

### CPU 사이클 (추정, 엔티티당)
- memcpy × 2: ~100 사이클
- AI logic: ~500 사이클
- Physics: ~200 사이클
- Sprite prep: ~150 사이클
- **전체**: ~1,000 사이클/엔티티
- **7개 엔티티**: ~7,000 사이클/프레임

---

## 🎓 역사적 의의

### 1988년 설계 패턴

1. **작업 버퍼 패턴**: 현대 ECS의 원형
2. **점프 테이블 AI**: 함수 포인터 배열
3. **방향 기반 스프라이트**: 자동 애니메이션
4. **링크 시스템**: 부모-자식 관계
5. **타이머 기반 상태 전환**: 이벤트 기반

이는 1988년 DOS 게임으로는 **매우 체계적인 설계**입니다.

---

**분석 완료일**: 2025-11-24
**다음 분석**: AI 상태 함수들 (0x16ef 점프 테이블), 충돌 검사 시스템
**참고 문서**: [MAIN_GAME_LOOP_ANALYSIS.md](MAIN_GAME_LOOP_ANALYSIS.md), [MEMORY_MAP.md](../technical/MEMORY_MAP.md)
