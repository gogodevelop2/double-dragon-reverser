# 스테이지 생명주기 시스템 (Stage Lifecycle System)

**목적**: Double Dragon의 스테이지 초기화, 플레이어 리스폰, BCD 스코어링, 게임 상태 관리를 언어 중립적으로 설명합니다.

**관련 함수**: 15개
**의존성**: 압축 시스템 (07), 하드웨어 I/O (08)
**복잡도**: ⭐⭐⭐

---

## 📋 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [스테이지 초기화](#3-스테이지-초기화)
4. [플레이어 리스폰](#4-플레이어-리스폰)
5. [BCD 스코어링](#5-bcd-스코어링)
6. [게임 상태 머신](#6-게임-상태-머신)
7. [메모리 레이아웃](#7-메모리-레이아웃)
8. [함수 목록](#8-함수-목록)
9. [구현 가이드](#9-구현-가이드)
10. [테스트 전략](#10-테스트-전략)

---

## 1. 개요

### 1.1 역할

스테이지 생명주기 시스템은 게임의 **전체 흐름**을 관리:

1. **스테이지 초기화**: 테이블 기반 데이터 로딩
2. **플레이어 리스폰**: 사망 후 재배치
3. **스코어링**: BCD 산술을 통한 정확한 점수 계산
4. **게임 상태**: 타이틀 → 게임플레이 → 게임오버 전환
5. **생명 관리**: 컨티뉴 시스템

### 1.2 주요 기능

**스테이지 관리**:
- 5개 스테이지 (1-4: 일반, 5: 보스)
- 스테이지별 데이터 테이블
- 3개 파일 로딩 (메인 데이터, 타일맵, 추가 데이터)

**플레이어 관리**:
- 생명 5개 (초기)
- 사망 → 리스폰 → 생명 감소
- 생명 0 → 컨티뉴 화면
- 컨티뉴 실패 → 게임오버

**스코어링**:
- BCD (Binary-Coded Decimal) 형식
- 8자리 점수 (00000000-99999999)
- 적 처치, 보너스 아이템 점수

### 1.3 게임 흐름

```
게임 시작
  ↓
타이틀 화면 (1P/2P 선택)
  ↓
스테이지 1 초기화
  ↓
메인 게임 루프
  ├─ 입력 처리
  ├─ 엔티티 업데이트
  ├─ 렌더링
  └─ 플레이어 사망?
       ├─ NO → 계속 루프
       └─ YES → 리스폰
                  ├─ 생명 > 0 → 스폰 위치 찾기 → 계속
                  └─ 생명 = 0 → 컨티뉴 화면
                                  ├─ 버튼 → 생명 회복 → 계속
                                  └─ 타임아웃 → 게임오버 → 타이틀
```

---

## 2. 아키텍처

### 2.1 시스템 다이어그램

```
┌─────────────────────────────────────────────┐
│       Stage Lifecycle System                 │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ Stage Init   │  │ Player Spawn │         │
│  ├──────────────┤  ├──────────────┤         │
│  │ • 테이블 로딩│  │ • 위치 탐색  │         │
│  │ • 데이터 압축│  │ • 스파이럴   │         │
│  │   해제 (LZW) │  │ • 충돌 확인  │         │
│  │ • 엔티티 초기│  └──────────────┘         │
│  │   화         │                            │
│  └──────────────┘  ┌──────────────┐         │
│                     │ BCD Scoring  │         │
│  ┌──────────────┐  ├──────────────┤         │
│  │ Game State   │  │ • 8자리 BCD  │         │
│  ├──────────────┤  │ • 덧셈/곱셈  │         │
│  │ • 타이틀     │  │ • 표시 업데이트│        │
│  │ • 게임플레이 │  └──────────────┘         │
│  │ • 컨티뉴     │                            │
│  │ • 게임오버   │  ┌──────────────┐         │
│  └──────────────┘  │ Lives Mgmt   │         │
│                     ├──────────────┤         │
│                     │ • 5 lives    │         │
│                     │ • Continue   │         │
│                     └──────────────┘         │
└─────────────────────────────────────────────┘
```

### 2.2 데이터 흐름

```
스테이지 테이블 (ROM)
  ↓
스테이지 데이터 구조 (47+ bytes)
  ├─ 파일 1: 메인 데이터 (압축) → LZW 디코딩
  ├─ 파일 2: 타일맵 (압축)     → LZW 디코딩
  └─ 파일 3: 추가 데이터 (압축) → LZW 디코딩
  ↓
메모리 버퍼
  ├─ 플레이어 위치 (X, Y)
  ├─ 스크롤 위치 (Scroll X, Y)
  ├─ 타이머 값
  └─ 스테이지 데이터 포인터
  ↓
게임 실행
```

---

## 3. 스테이지 초기화

### 3.1 스테이지 데이터 구조

**메모리 레이아웃** (최소 47 bytes):
```
struct StageData {
    uint16 data_dest_1;      // +0:  메인 데이터 목적지
    uint16 tilemap_dest;     // +2:  타일맵 목적지
    uint16 data_dest_3;      // +4:  추가 데이터 목적지
    uint16 field_3;          // +6:  (용도 불명)
    uint16 field_4;          // +8:
    uint16 field_5;          // +10:
    uint16 scroll_field;     // +12: 스크롤 관련
    uint16 scroll_x;         // +14: 초기 스크롤 X
    uint16 scroll_y;         // +16: 초기 스크롤 Y
    uint16 player1_y;        // +18: P1 스폰 Y
    uint16 player1_x;        // +20: P1 스폰 X
    uint16 player2_y;        // +22: P2 스폰 Y
    uint16 player2_x;        // +24: P2 스폰 X
    uint8  player1_facing;   // +26: P1 방향 (0=right, 1=left)
    uint8  player2_facing;   // +27: P2 방향
    uint16 stage_data_ptr;   // +28: 스테이지 데이터 포인터
    uint16 scroll_data_ptr;  // +30: 스크롤 제한 포인터
    uint16 field_16-23;      // +32-45: 추가 필드들
    // Total: 47+ bytes
};
```

### 3.2 스테이지 테이블

**위치**: `0x3fce`

```
스테이지 테이블:
  0x3fce: [Stage 1 Data Pointer]  →  StageData 구조체
  0x3fd0: [Stage 2 Data Pointer]  →  StageData 구조체
  0x3fd2: [Stage 3 Data Pointer]  →  StageData 구조체
  0x3fd4: [Stage 4 Data Pointer]  →  StageData 구조체
  0x3fd6: [Stage 5 Data Pointer]  →  StageData 구조체 (보스)
```

**접근 방법**:
```python
current_stage = read_byte(0x38d0)  # 1-based (1-5)
table_offset = (current_stage - 1) * 2
stage_data_ptr = read_word(0x3fce + table_offset)
stage_data = StageData(stage_data_ptr)
```

### 3.3 초기화 알고리즘 (의사코드)

```python
function initialize_stage(stage_number):
    """
    스테이지 완전 초기화

    Args:
        stage_number: 1-5 (1-based)

    Steps:
        1. 엔티티 배열 클리어
        2. 스테이지 데이터 로딩 (3개 파일)
        3. 게임 상태 초기화
        4. 플레이어 위치 설정
        5. 그래픽 로딩
    """
    # 1. 엔티티 초기화
    clear_enemy_entities()  # 5 slots × 24 bytes
    copy_projectile_data()  # 6 slots × 18 bytes

    # 2. 스테이지 데이터 테이블 참조
    stage_data_ptr = stage_table[stage_number - 1]
    stage_data = read_stage_data(stage_data_ptr)

    # 3. 데이터 파일 로딩 (LZW 압축 해제)
    # 파일 1: 메인 데이터
    load_and_decompress_lzw(
        source_segment=0x1988,
        source_offset=0x5690,
        dest_segment=stage_data.data_dest_1
    )

    # 파일 2: 타일맵
    load_and_decompress_lzw(
        source_segment=0x1988,
        source_offset=0xe000,
        dest_segment=stage_data.tilemap_dest
    )

    # 파일 3: 추가 데이터
    load_and_decompress_lzw(
        source_segment=0x1988,
        source_offset=0x4e,
        dest_segment=stage_data.data_dest_3
    )

    # 4. 게임 상태 초기화 (from stage_data)
    scroll_x = stage_data.scroll_x
    scroll_y = stage_data.scroll_y
    player1.x = stage_data.player1_x
    player1.y = stage_data.player1_y
    player1.facing = stage_data.player1_facing
    player2.x = stage_data.player2_x
    player2.y = stage_data.player2_y
    player2.facing = stage_data.player2_facing

    # 5. 플레이어 엔티티 초기화
    for player in [player1, player2]:
        if player.exists:
            player.state = 0x2a  # Alive
            player.hp = 5
            player.max_hp = 20
            player.target = -1  # None

    # 6. 스크롤 및 렌더링 초기화
    vram_pointer = 0xb0d0
    scroll_offset = 0
    frame_counter = 0

    # 7. 타이머 로딩
    timer_value = timer_table[stage_number - 1]
    set_stage_timer(timer_value)

    # 8. 타일맵 주소 변환
    adjust_tilemap_pointers()

    # 9. 그래픽 로딩
    if stage_number == 5:
        load_boss_stage_graphics()
    else:
        load_normal_stage_graphics()

    # 10. 비디오 모드 설정 (INT 10h)
    if stage_number in [1, 2, 5]:
        set_video_mode_once()
    else:  # Stages 3, 4
        set_video_mode_twice()
```

### 3.4 스테이지별 차이점

| 스테이지 | 특징 | 그래픽 | 비디오 모드 |
|---------|------|--------|-------------|
| 1 | 거리 | 일반 | 1회 설정 |
| 2 | 공장 | 일반 | 1회 설정 |
| 3 | 숲 | 일반 | 2회 설정 (특수) |
| 4 | 엘리베이터 | 일반 | 2회 설정 (특수) |
| 5 | 보스 | **보스 전용** | 1회 설정 |

**Stage 5 보스 특징**:
- 별도 그래픽 세트
- 보스 AI 활성화
- 다른 음악 (사운드 시스템)

---

## 4. 플레이어 리스폰

### 4.1 사망 처리 흐름

```
플레이어 HP = 0
  ↓
State 0x2a (Normal) → State 0x1e (Dying)
  ↓
사망 애니메이션 재생 (Sprite 0x25f0)
  ↓
State 0x1e → State 0x00 (Dead)
  ↓
Lives Display--
  ↓
Lives Display < 0?
  ├─ NO  → 즉시 리스폰
  └─ YES → Actual Lives 확인
             ├─ > 0 → 컨티뉴 화면 → 버튼 → Lives 회복 → 리스폰
             └─ = 0 → 게임오버
```

### 4.2 리스폰 알고리즘 (의사코드)

```python
function handle_player_death(player_id):
    """
    플레이어 사망 및 리스폰 처리

    Args:
        player_id: 0 (P1) or 0x0a (P2)

    Returns:
        None (게임 상태 업데이트)
    """
    player = get_player(player_id)

    # 1. 상태 확인
    if player.state == 0:
        # 이미 죽음
        return

    if player.invincibility_counter > 0:
        # 무적 중
        return

    # 2. 사망 애니메이션 확인
    if player.state in [0x2a, 0x02]:  # Alive states
        # 사망 시작
        player.state = 0x1e  # Dying
        player.sprite = 0xffff  # None
        return

    if player.sprite == 0x25f0:
        # 사망 애니메이션 완료
        player.state = 0x00  # Dead

    # 3. Lives 감소
    if player_id == 0:  # Player 1
        lives_display = read_word(0x4428)
        lives_display -= 1
        write_word(0x4428, lives_display)
    else:  # Player 2
        lives_display = read_word(0x442a)
        lives_display -= 1
        write_word(0x442a, lives_display)

    # 4. Underflow 체크 (lives_display < 0)
    if lives_display < 0:
        actual_lives = read_word(0x442c)

        if actual_lives == 0:
            # 게임오버
            return

        # 컨티뉴 화면
        wait_for_continue_button(player_id)

        # 버튼 누름 → Lives 회복
        if player_id == 0:
            write_word(0x4428, 2)  # Display = 2
            write_word(0x4424, 0)  # Score low = 0
        else:
            write_word(0x442a, 2)
            write_word(0x4426, 0)

        actual_lives -= 1
        write_word(0x442c, actual_lives)

    # 5. 리스폰
    player.state = 0x20  # Respawning
    player.sprite = 0xffff
    player.counter = 20  # 무적 시간 (20 프레임)

    # 스폰 위치 찾기 (spiral search)
    spawn_pos = find_spawn_position(player)
    player.x = spawn_pos.x
    player.y = spawn_pos.y

    # 타이머 리로드
    timer_value = timer_table[current_stage - 1]
    set_stage_timer(timer_value)
```

### 4.3 스폰 위치 찾기 (Spiral Search)

**목적**: 적과 겹치지 않는 안전한 위치 찾기

**알고리즘** (스파이럴 검색):
```
중심점 (P1 또는 P2 현재 위치)
  ↓
반경 0 → 1 → 2 → 3 ... 최대 16
  ↓
각 반경에서 8방향 탐색:
  1. 중심
  2. 위
  3. 오른쪽
  4. 아래
  5. 왼쪽
  6. 오른쪽 위
  7. 오른쪽 아래
  8. 왼쪽 아래
  ↓
충돌 확인:
  - 적 엔티티와 거리
  - 프로젝타일과 거리
  - 맵 경계 내
  ↓
안전 위치 발견 → 반환
안전 위치 없음 → 중심점 반환 (최후 수단)
```

**의사코드**:
```python
function find_spawn_position(player):
    """
    스파이럴 검색으로 안전한 스폰 위치 찾기

    Args:
        player: 플레이어 객체

    Returns:
        (x, y): 스폰 위치
    """
    # 다른 플레이어 위치를 중심으로
    other_player = get_other_player(player)

    if other_player.state != 0:
        # 다른 플레이어 살아있음 → 그 위치 근처
        center_x = other_player.x
        center_y = other_player.y
    else:
        # 혼자 → 스테이지 초기 위치
        center_x = stage_data.player_x[player.id]
        center_y = stage_data.player_y[player.id]

    # 스파이럴 검색
    directions = [
        (0, 0),    # Center
        (0, -8),   # Up
        (8, 0),    # Right
        (0, 8),    # Down
        (-8, 0),   # Left
        (8, -8),   # Right-Up
        (8, 8),    # Right-Down
        (-8, 8),   # Left-Down
    ]

    max_radius = 16  # 최대 탐색 반경

    for radius in range(max_radius + 1):
        for dx, dy in directions:
            test_x = center_x + dx * radius
            test_y = center_y + dy * radius

            # 경계 확인
            if not in_bounds(test_x, test_y):
                continue

            # 적 충돌 확인
            safe = True
            for enemy in enemy_array:
                if enemy.active:
                    dist = manhattan_distance(
                        test_x, test_y,
                        enemy.x, enemy.y
                    )
                    if dist < 32:  # 안전 거리
                        safe = False
                        break

            # 프로젝타일 충돌 확인
            if safe:
                for proj in projectile_array:
                    if proj.active:
                        dist = manhattan_distance(
                            test_x, test_y,
                            proj.x, proj.y
                        )
                        if dist < 16:
                            safe = False
                            break

            if safe:
                return (test_x, test_y)

    # 안전한 위치 없음 → 중심 반환
    return (center_x, center_y)


function manhattan_distance(x1, y1, x2, y2):
    """맨하탄 거리 계산"""
    return abs(x1 - x2) + abs(y1 - y2)
```

### 4.4 무적 시간

**리스폰 후**:
```
Counter = 20 (프레임)
State = 0x20 (Respawning)
  ↓
매 프레임 Counter--
  ↓
Counter = 0
  ↓
State = 0x2a (Normal)
무적 해제
```

**시각 효과**:
- 깜빡임 (Blinking sprite)
- 반투명 (50% opacity, 구현 의존)

---

## 5. BCD 스코어링

### 5.1 BCD (Binary-Coded Decimal) 개요

**목적**: 10진수 산술의 정확한 표현

**포맷**:
```
Binary: 0000 0000 1010 (10 in binary)
BCD:    0001 0000      (10 in BCD, 2 nibbles)

각 nibble (4 bits)은 0-9 표현:
  0x00-0x09: 유효
  0x0A-0x0F: 무효 (사용 안 함)
```

**예시**:
```
점수 12345:
  Binary:   0011 0000 0011 1001 (0x3039)
  BCD:      0001 0010 0011 0100 0101 (0x12345)
          └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └┬┘
            1     2     3     4   5
```

### 5.2 BCD 덧셈 알고리즘

**문제**: 일반 이진 덧셈은 BCD에서 잘못된 결과 생성

**예시**:
```
  0x09 (9 in BCD)
+ 0x01 (1 in BCD)
------
  0x0A (10 in binary, but INVALID in BCD!)

올바른 BCD 결과: 0x10 (1과 0)
```

**BCD 보정**:
```
If (nibble_result > 9):
    nibble_result += 6  # 0x0A → 0x10

Example:
  0x09 + 0x01 = 0x0A
  0x0A > 9 → 0x0A + 6 = 0x10 ✓
```

**의사코드** (8자리 BCD 덧셈):
```python
function bcd_add(score, points):
    """
    BCD 형식 점수 덧셈

    Args:
        score: 현재 점수 (4 bytes BCD)
        points: 추가 점수 (2 bytes BCD)

    Returns:
        new_score: 업데이트된 점수
    """
    carry = 0

    # Byte 0 (lowest)
    sum0 = (score[0] & 0x0F) + (points[0] & 0x0F) + carry
    if sum0 > 9:
        sum0 += 6
        carry = 1
    else:
        carry = 0

    sum0_high = ((score[0] >> 4) & 0x0F) + ((points[0] >> 4) & 0x0F) + carry
    if sum0_high > 9:
        sum0_high += 6
        carry = 1
    else:
        carry = 0

    result[0] = (sum0_high << 4) | (sum0 & 0x0F)

    # Byte 1-3 (동일한 과정 반복)
    # ...

    # Overflow 확인
    if carry == 1:
        # 99999999 초과 → 클램프
        score = 0x99999999

    return score
```

### 5.3 점수 표시 시스템

**메모리 레이아웃**:
```
Player 1 Score:
  0x4424: Low word (2 bytes BCD)   # 하위 4자리
  [High]: High word (2 bytes BCD)  # 상위 4자리

Player 2 Score:
  0x4426: Low word (2 bytes BCD)
  [High]: High word (2 bytes BCD)

Example (12345678):
  Low  = 0x5678 (78 56)
  High = 0x1234 (34 12)
```

**표시 업데이트**:
```python
function update_score_display(player_id):
    """
    점수를 화면에 표시

    Args:
        player_id: 0 (P1) or 1 (P2)
    """
    if player_id == 0:
        score_addr = 0x4424
    else:
        score_addr = 0x4426

    score_low = read_word(score_addr)
    score_high = read_word(score_addr + 2)

    # BCD → ASCII 변환
    digits = [
        (score_high >> 12) & 0xF,  # 천만 자리
        (score_high >> 8) & 0xF,   # 백만 자리
        (score_high >> 4) & 0xF,   # 십만 자리
        (score_high >> 0) & 0xF,   # 만 자리
        (score_low >> 12) & 0xF,   # 천 자리
        (score_low >> 8) & 0xF,    # 백 자리
        (score_low >> 4) & 0xF,    # 십 자리
        (score_low >> 0) & 0xF,    # 일 자리
    ]

    # 화면 위치 (UI 영역)
    x = 10 if player_id == 0 else 170
    y = 10

    for i, digit in enumerate(digits):
        draw_digit(x + i * 8, y, digit)
```

### 5.4 점수 이벤트

| 이벤트 | 점수 (BCD) | 16진수 |
|--------|-----------|--------|
| 일반 적 처치 | 100 | 0x0100 |
| 강한 적 처치 | 500 | 0x0500 |
| 보스 처치 | 5000 | 0x5000 |
| 보너스 아이템 | 1000 | 0x1000 |
| 스테이지 클리어 | 10000 | 0x10000 (BCD) |

**점수 추가 예시**:
```python
def add_score_for_enemy_kill(enemy_type):
    if enemy_type == "normal":
        points = 0x0100  # 100 in BCD
    elif enemy_type == "strong":
        points = 0x0500  # 500 in BCD
    elif enemy_type == "boss":
        points = 0x5000  # 5000 in BCD

    player_score = bcd_add(current_score, points)
    update_score_display(player_id)
```

---

## 6. 게임 상태 머신

### 6.1 상태 전환 다이어그램

```
     ┌────────────┐
     │   TITLE    │ ← 게임 시작
     └─────┬──────┘
           │ 1P/2P 버튼
           ↓
     ┌────────────┐
     │  GAMEPLAY  │
     └─────┬──────┘
           │
           ├─→ 스테이지 클리어 → 다음 스테이지
           │
           ├─→ 플레이어 사망
           │      ├─ Lives > 0 → 리스폰 → GAMEPLAY
           │      └─ Lives = 0 ↓
           │
           ↓
     ┌────────────┐
     │  CONTINUE  │ (10초 타이머)
     └─────┬──────┘
           │
           ├─→ 버튼 누름 → Lives 회복 → GAMEPLAY
           └─→ 타임아웃 ↓
           ↓
     ┌────────────┐
     │ GAME OVER  │
     └─────┬──────┘
           │ 화면 플래시
           ↓
     ┌────────────┐
     │   TITLE    │ (다시 시작)
     └────────────┘
```

### 6.2 상태별 처리

**TITLE 상태**:
```python
function state_title():
    """타이틀 화면"""
    # 1. 타이틀 그래픽 표시
    load_title_screen()

    # 2. 입력 대기 (360 프레임 = 6초 타임아웃)
    timeout = 360

    while timeout > 0:
        if button_pressed(PLAYER1):
            # 1P 시작
            player2.state = 0  # 비활성화
            start_game(1)
            return

        if button_pressed(PLAYER2):
            # 2P 시작
            start_game(2)
            return

        wait_vsync()
        timeout -= 1

    # 타임아웃 → 데모 플레이 또는 반복
```

**GAMEPLAY 상태**:
```python
function state_gameplay():
    """메인 게임 루프"""
    while not exit_flag:
        # 타이머 틱 대기
        while timer_tick < 15:
            pass
        timer_tick = 0

        # 17개 서브시스템 순차 실행
        process_stage_management()   # 스테이지 데이터
        update_entities()            # 엔티티 업데이트
        prepare_rendering()          # 렌더링 준비
        sort_by_depth()              # 깊이 정렬
        render_sprites()             # 스프라이트 그리기
        update_animations()          # 애니메이션
        update_screen()              # 화면 업데이트
        poll_input()                 # 입력 처리
        update_timers()              # 타이머
        update_camera()              # 카메라 스크롤
        stream_stage_data()          # 스테이지 스트리밍
        increment_frame_counter()    # 프레임 카운터

        # 플레이어 사망 확인
        if all_players_dead():
            if lives > 0:
                state = CONTINUE
            else:
                state = GAME_OVER
            return
```

**CONTINUE 상태**:
```python
function state_continue():
    """컨티뉴 화면"""
    # 1. 화면 플래시 (160 프레임)
    for i in range(160):
        wait_vsync()

    # 2. 컨티뉴 텍스트 표시
    display_text("CONTINUE?")
    display_text("PRESS BUTTON")

    # 3. 타이머 (10초)
    timer = 600  # 10 seconds @ 60 FPS

    while timer > 0:
        # 타이머 표시 (카운트다운)
        display_number(timer // 60)

        if button_pressed(PLAYER1) or button_pressed(PLAYER2):
            # 컨티뉴
            lives = 5  # 회복
            actual_lives -= 1  # 크레딧 소모

            if actual_lives == 0:
                # 크레딧 소진 → 게임오버
                state = GAME_OVER
                return

            # 리스폰
            respawn_player()
            state = GAMEPLAY
            return

        wait_vsync()
        timer -= 1

    # 타임아웃 → 게임오버
    state = GAME_OVER
```

**GAME_OVER 상태**:
```python
function state_game_over():
    """게임오버"""
    # 1. 게임오버 텍스트
    display_text("GAME OVER")

    # 2. 화면 플래시 효과 (20회)
    for i in range(20):
        wait_vsync()
        wait_vsync()
        wait_vsync()
        set_cga_color(0x0e if i % 2 == 0 else 0x10)

    # 3. 점수 기록 (하이스코어?)
    # (구현 의존)

    # 4. 타이틀로 복귀
    state = TITLE
```

---

## 7. 메모리 레이아웃

### 7.1 스테이지 메모리

```
0x38d0: Current Stage (1 byte, 1-5)
0x38d1: Stage State Flag 1 (1 byte)
0x38d2: Stage State Flag 2 (1 byte)
0x38d3: (reserved)

0x38db: Stage Data Pointer (2 bytes)
0x38dd: Scroll Data Pointer (2 bytes)
0x38df: Stage Data Ready Flag (1 byte)

0x3fce: Stage Table (10 bytes)
  [0]: Stage 1 pointer
  [2]: Stage 2 pointer
  [4]: Stage 3 pointer
  [6]: Stage 4 pointer
  [8]: Stage 5 pointer

0x4404: Timer Table (10 bytes)
  [0]: Stage 1 timer
  [2]: Stage 2 timer
  ...
```

### 7.2 플레이어 메모리

```
Player 1 Entity (0x16c6, 24 bytes):
  +0x00: Sprite Pointer (2)
  +0x02: State (1)
    0x00: Dead
    0x1e: Dying
    0x20: Respawning
    0x2a: Alive (normal)
  +0x03: (reserved)
  +0x04: HP (1)
  +0x05: Max HP (1)
  +0x06: Target (2)
  +0x08: X Position (2)
  +0x0a: Y Position (2)
  +0x0c: Velocity X (2)
  +0x0e: Velocity Y (2)
  +0x10: Animation Frame (1)
  +0x11: Facing (1)
  +0x12-0x17: Additional fields

Player 2 Entity (0x16de, 24 bytes):
  (동일 구조)
```

### 7.3 점수 및 생명 메모리

```
0x4424: Player 1 Score Low (2 bytes, BCD)
0x4426: Player 2 Score Low (2 bytes, BCD)
0x4428: Player 1 Lives Display (2 bytes)
0x442a: Player 2 Lives Display (2 bytes)
0x442c: Actual Lives (2 bytes, 공유?)
0x442e: Stage Timer (2 bytes)
```

### 7.4 게임 상태 메모리

```
0x318e: Exit Flag (1 byte)
  0: 계속
  1: 종료

0x318a: Timer Tick Counter (2 bytes)
  0-15: 틱 카운터

0x16b0: Frame Counter (2 bytes)
  매 프레임 증가

0x3204: Player 1 Quit Flag (1 byte)
0x31c6: Player 1 Exit Flag (1 byte)
0x31d9: Player 2 Button Flag (1 byte)

0x3217: 2P Mode Flag (1 byte)
0x3220: 2P Active Flag (1 byte)
```

---

## 8. 함수 목록

### 8.1 스테이지 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:3c7e | Stage Init | 스테이지 초기화 마스터 | Very High |
| 1000:0a96 | Load Normal Graphics | 일반 스테이지 그래픽 | Medium |
| 1000:0af5 | Load Boss Graphics | 보스 스테이지 그래픽 | Medium |
| 1000:3e46 | Clear Enemies | 적 엔티티 배열 클리어 | Low |
| 1000:3e56 | Copy Projectile Data | 프로젝타일 데이터 복사 | Low |
| 1000:3e1a | Adjust Tilemap | 타일맵 주소 변환 | Medium |

### 8.2 플레이어 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:3e6d | Player Death/Respawn | 사망 및 리스폰 처리 | High |
| 1000:3f71 | Find Spawn Position | 스폰 위치 찾기 (스파이럴) | High |

### 8.3 스코어링 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:30d2 | BCD Addition | BCD 산술 연산 | Very High |
| 1000:3094 | Update Score Display 1 | 점수 표시 업데이트 | Medium |
| 1000:30ac | Update Score Display 2 | 점수 표시 업데이트 | Medium |

### 8.4 게임 상태 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:4780 | Game State Manager | 게임 상태 + 메인 루프 | Very High |
| 1000:1ba0 | Game Exit | 게임 종료 (INT 10h, 21h) | Low |
| 1000:1bad | Game Exit Wrapper | 게임 종료 래퍼 | Medium |
| 1000:468e | Subsystem 1 | 프레임 기반 서브시스템 | Medium |
| 1000:46cd | Subsystem 2 | 타이머 관리 | Medium |
| 1000:4711 | Subsystem 3 | 점수 표시 | Low |

**호출 관계**:
```
FUN_4780 (Game State Manager)
  ├─→ FUN_3c7e (Stage Init)
  │     ├─→ FUN_3e46 (Clear Enemies)
  │     ├─→ FUN_3e56 (Copy Projectiles)
  │     ├─→ FUN_1e8a (Load & Decompress) ×3
  │     ├─→ FUN_3e1a (Adjust Tilemap)
  │     └─→ FUN_0a96 / FUN_0af5 (Load Graphics)
  │
  ├─→ Main Loop (60 FPS)
  │     ├─→ FUN_3830 (Stage Management)
  │     ├─→ FUN_0360 (Entity Update)
  │     │     └─→ FUN_3e6d (Death/Respawn)
  │     │           └─→ FUN_3f71 (Find Spawn)
  │     ├─→ FUN_8135 (Screen Update)
  │     └─→ FUN_468e, 46cd, 4711 (Subsystems)
  │
  └─→ FUN_1ba0 (Game Exit)
```

---

## 9. 구현 가이드

### 9.1 현대적 구현 전략

**문제**: DOS 특화 로직 (INT 10h, INT 21h, BCD 산술)

**해결**:

#### 스테이지 데이터
```
DOS 방식: 테이블 → 포인터 → 메모리 주소
현대 방식: JSON/XML 파일 → 구조체 배열

TypeScript 예시:
interface StageData {
  dataFiles: string[];      // ["stage1_main.dat", ...]
  playerSpawn: {x, y}[];    // P1, P2 위치
  scrollInit: {x, y};
  timer: number;
  graphics: string;         // "normal" | "boss"
}

const stages: StageData[] = [
  { /* Stage 1 */ },
  { /* Stage 2 */ },
  ...
];
```

#### BCD 산술
```
DOS 방식: 하드웨어 BCD (DAA 명령어)
현대 방식: 소프트웨어 BCD 또는 문자열

Option 1: 정수 산술 (간단)
  score = 0;  // 일반 정수
  score += 100;  // 덧셈
  display = score.toString().padStart(8, '0');

Option 2: BCD 에뮬레이션 (정확)
  class BCDScore {
    value: Uint8Array;  // 4 bytes
    add(points: number) { /* BCD 알고리즘 */ }
    toString() { /* BCD → 문자열 */ }
  }
```

#### 리스폰 시스템
```
DOS 방식: 스파이럴 검색 (고정 알고리즘)
현대 방식: 동일하지만 최적화 가능

개선:
- 그리드 기반 공간 분할 (Spatial Hashing)
- 안전 존 미리 계산 (Pre-computed Safe Zones)
```

### 9.2 함정 (Pitfalls)

**스테이지 초기화**:
```
❌ 나쁜 예:
  # 매번 파일 읽기
  stage_data = load_from_disk("stage1.dat")

✅ 좋은 예:
  # 게임 시작 시 모두 로드 → 메모리에 캐시
  all_stages = [load_stage(i) for i in range(1, 6)]
  current_stage_data = all_stages[stage_number - 1]
```

**BCD 산술**:
```
❌ 나쁜 예:
  # 일반 덧셈
  score_bcd = 0x09
  score_bcd += 0x01  # = 0x0A (잘못됨!)

✅ 좋은 예:
  # BCD 보정
  score_bcd = 0x09
  temp = score_bcd + 0x01  # = 0x0A
  if (temp & 0x0F) > 9:
    temp += 6  # = 0x10 (올바름)
  score_bcd = temp
```

**리스폰 위치**:
```
❌ 나쁜 예:
  # 랜덤 위치 (적과 겹칠 수 있음)
  spawn_x = random(0, map_width)
  spawn_y = random(0, map_height)

✅ 좋은 예:
  # 스파이럴 검색 (안전 보장)
  spawn_pos = spiral_search(center_x, center_y, safe_distance=32)
```

---

## 10. 테스트 전략

### 10.1 스테이지 초기화 테스트

```python
def test_stage_initialization():
    """스테이지 초기화 테스트"""
    for stage_num in range(1, 6):
        initialize_stage(stage_num)

        # 플레이어 위치 확인
        assert player1.x > 0
        assert player1.y > 0

        # 스크롤 초기화 확인
        assert scroll_x >= 0
        assert scroll_y >= 0

        # 엔티티 클리어 확인
        for enemy in enemy_array:
            assert enemy.state == 0  # 모두 비활성

        # 타이머 로딩 확인
        assert stage_timer > 0
```

### 10.2 리스폰 테스트

```python
def test_player_respawn():
    """플레이어 리스폰 테스트"""
    # 플레이어 사망
    player1.hp = 0
    handle_player_death(0)

    # Lives 감소 확인
    assert lives < initial_lives

    # 리스폰 위치 확인
    spawn_pos = find_spawn_position(player1)
    assert in_bounds(spawn_pos.x, spawn_pos.y)

    # 적과 거리 확인
    for enemy in enemy_array:
        if enemy.active:
            dist = manhattan_distance(
                spawn_pos.x, spawn_pos.y,
                enemy.x, enemy.y
            )
            assert dist >= 32  # 안전 거리
```

### 10.3 BCD 산술 테스트

```python
def test_bcd_addition():
    """BCD 덧셈 테스트"""
    # 기본 케이스
    score = 0x0000
    score = bcd_add(score, 0x0100)  # +100
    assert score == 0x0100

    # 자리올림
    score = 0x0099
    score = bcd_add(score, 0x0001)  # +1
    assert score == 0x0100  # 99 + 1 = 100

    # 연속 덧셈
    score = 0x0000
    for i in range(10):
        score = bcd_add(score, 0x0100)  # +100 × 10
    assert score == 0x1000  # 1000

    # 오버플로우
    score = 0x99999999
    score = bcd_add(score, 0x0001)
    assert score == 0x99999999  # 클램프
```

---

## 11. 참고

### 11.1 관련 알고리즘

- [`../algorithms/MANHATTAN_AI.md`](../algorithms/MANHATTAN_AI.md) - 스폰 위치 거리 계산

### 11.2 관련 시스템

- [`07_COMPRESSION.md`](07_COMPRESSION.md) - LZW 압축 해제 (스테이지 로딩)
- [`08_HARDWARE_IO.md`](08_HARDWARE_IO.md) - DOS INT 21h (파일 I/O)
- [`02_ENTITY_AI.md`](02_ENTITY_AI.md) - 엔티티 상태 관리

### 11.3 원본 분석

- [`../archive/phase4-analysis/STAGE_INIT_RESPAWN_ANALYSIS.md`](../archive/phase4-analysis/STAGE_INIT_RESPAWN_ANALYSIS.md) - 스테이지 초기화
- [`../archive/phase4-analysis/GAME_STATE_SCORE_SOUND_ANALYSIS.md`](../archive/phase4-analysis/GAME_STATE_SCORE_SOUND_ANALYSIS.md) - BCD 스코어링

### 11.4 외부 참조

- [Binary-Coded Decimal (Wikipedia)](https://en.wikipedia.org/wiki/Binary-coded_decimal)
- [Game State Machine Patterns](https://gameprogrammingpatterns.com/state.html)

---

**작성일**: 2025-01-24
**버전**: 1.0
**언어 중립성**: 의사코드 기반, 모든 언어로 구현 가능

**다음 문서**: [03_ANIMATION.md](03_ANIMATION.md) - 애니메이션 시스템
**이전 문서**: [08_HARDWARE_IO.md](08_HARDWARE_IO.md) - 하드웨어 I/O
