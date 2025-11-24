# Animation System (애니메이션 시스템)

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Complete

---

## 1. 개요

Double Dragon의 애니메이션 시스템은 **4방향 스프라이트**와 **링크드 리스트 기반 프레임 시퀀스**를 사용하여 캐릭터와 오브젝트의 움직임을 표현합니다. 각 엔티티는 상태에 따라 다른 애니메이션을 재생하며, 방향에 따라 적절한 스프라이트를 자동으로 선택합니다.

### 핵심 특징

1. **4방향 스프라이트**: 각 애니메이션 프레임은 4개 방향(오른쪽, 왼쪽, 위, 아래) + 기본 스프라이트 포함 (총 40 bytes)
2. **링크드 리스트 구조**: 프레임들이 포인터로 연결되어 가변 길이 애니메이션 지원
3. **Jump Table 디스패치**: 엔티티 타입과 상태에 따라 점프 테이블(@ 0x1930)로 애니메이션 선택
4. **화면 좌표 변환**: 엔티티 좌표 → 화면 좌표 변환 (스크롤 보정 + Y축 × 4 스케일)
5. **우선순위 시스템**: Z-order를 이용한 depth 정렬로 올바른 렌더링 순서 보장

### 시스템 연동

```
Entity Update Loop
    ↓
Animation System (이 문서)
    ├─> Sprite Frame Selection (FUN_0426)
    ├─> Animation State Lookup (FUN_04a9)
    └─> Frame Advancement (FUN_04e1)
    ↓
Rendering System (01_RENDERING.md)
    └─> Render List → Screen Blitting
```

---

## 2. 아키텍처

### 2.1 시스템 개요도

```
┌─────────────────────────────────────────────────────────────┐
│                     Entity Update Loop                       │
│                    (FUN_0360, 매 프레임)                      │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Animation State Invalid?     │
        │  (0x1695 == -1)               │
        └───────┬───────────────┬───────┘
                │ Yes           │ No
                ↓               │
    ┌───────────────────────┐  │
    │ FUN_04a9              │  │
    │ Animation State       │  │
    │ Lookup                │  │
    │                       │  │
    │ Jump Table @ 0x1930   │  │
    │ ↓                     │  │
    │ Set 0x1695 pointer    │  │
    └───────┬───────────────┘  │
            │                  │
            └──────┬───────────┘
                   ↓
        ┌─────────────────────────┐
        │ FUN_0426                │
        │ Sprite Frame Selector   │
        │                         │
        │ 1. Read animation data  │
        │ 2. Apply direction      │
        │ 3. Calculate screen XY  │
        │ 4. Set priority         │
        │ 5. Add to render list   │
        └──────────┬──────────────┘
                   ↓
        ┌─────────────────────────┐
        │ FUN_04e1                │
        │ Frame Advancer          │
        │                         │
        │ Advance to next frame   │
        │ (linked list traversal) │
        └──────────┬──────────────┘
                   ↓
        ┌─────────────────────────┐
        │ Render List Entry       │
        │ (screen_x, screen_y,    │
        │  width, height,         │
        │  sprite_ptr, priority)  │
        └─────────────────────────┘
```

### 2.2 데이터 구조 계층

```
Jump Table (0x1930)
    │
    │ Index = (animation_flags & 3 - 1) + entity_type
    ↓
Animation Sequence Pointer
    │
    ↓
┌─────────────────────────────────────────────┐
│ Animation Frame (linked list node)         │
├─────────────────────────────────────────────┤
│ DirectionalAnimation (40 bytes)             │
│   ├─ Default Frame (8 bytes)                │
│   ├─ Right Frame (8 bytes)                  │
│   ├─ Up Frame (8 bytes)                     │
│   ├─ Left Frame (8 bytes)                   │
│   └─ Down Frame (8 bytes)                   │
│                                             │
│ Next Frame Pointer (2 bytes)                │
└──────────────┬──────────────────────────────┘
               │
               ↓ (loop or next frame)
         Next Animation Frame
```

---

## 3. 애니메이션 시스템 세부사항

### 3.1 4방향 스프라이트 시스템

#### 방향 인코딩

각 방향은 고유한 값으로 인코딩되며, 해당 값에 따라 프레임 데이터의 오프셋이 결정됩니다:

```
Direction Code | Direction | Word Offset | Byte Offset
---------------|-----------|-------------|-------------
     0x00      | Default   |      +0     |      +0
     0x02      | Right     |      +4     |      +8
     0x06      | Up        |      +8     |     +16
     0x04      | Left      |     +12     |     +24
     0x08      | Down      |     +16     |     +32
```

#### DirectionalAnimation 구조

```c
struct AnimationFrameData {
    uint16_t sprite_data_ptr;    // +0: Sprite data address in memory
    uint16_t reserved;           // +2: Unused (alignment?)
    uint8_t  width;              // +4: Sprite width in pixels
    uint8_t  height;             // +5: Sprite height in pixels
    int8_t   offset_x;           // +6: X offset from entity position (signed)
    int8_t   offset_y;           // +7: Y offset from entity position (signed)
};  // Total: 8 bytes

struct DirectionalAnimation {
    AnimationFrameData default;  // +0:  Default direction
    AnimationFrameData right;    // +8:  Right-facing sprite
    AnimationFrameData up;       // +16: Upward-facing sprite
    AnimationFrameData left;     // +24: Left-facing sprite
    AnimationFrameData down;     // +32: Downward-facing sprite
};  // Total: 40 bytes
```

#### 방향 선택 알고리즘 (Pseudocode)

```python
function select_directional_sprite(direction_code):
    # Base pointer to current animation frame
    frame_ptr = animation_state_ptr

    # Apply direction offset
    if direction_code == 0x02:      # Right
        frame_ptr += 4 words (8 bytes)
    elif direction_code == 0x06:    # Up
        frame_ptr += 8 words (16 bytes)
    elif direction_code == 0x04:    # Left
        frame_ptr += 12 words (24 bytes)
    elif direction_code == 0x08:    # Down
        frame_ptr += 16 words (32 bytes)
    # else: use default (no offset)

    return frame_ptr
```

**참고**: 원본 코드는 순차적인 if문을 사용합니다(룩업 테이블이 아님). 이는 코드 크기 최소화를 우선했기 때문으로 추정됩니다.

---

### 3.2 애니메이션 상태 관리

#### 상태 플래그 (0x1693)

```
Bit Layout (8-bit value):
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ 7 │ 6 │ 5 │ 4 │ 3 │ 2 │ 1 │ 0 │
└───┴───┴───┴───┴─┬─┴───┴─┬─┴─┬─┘
                  │       │   │
                  │       │   └─> Bit 0-1: Animation state (0-3)
                  │       │       00 = Invalid (game termination)
                  │       │       01 = Animation slot 1
                  │       │       10 = Animation slot 2
                  │       │       11 = Animation slot 3
                  │       │
                  │       └─────> Bit 0-1: State index
                  │
                  └─────────────> Bit 3: Special offset flag
                                  1 = Apply +0x38 offset (types 0x02, 0x36 only)
```

#### 점프 테이블 인덱싱 (@ 0x1930)

```python
function lookup_animation_sequence(entity_type, animation_flags):
    # Extract state from flags
    state = animation_flags & 0x03

    # Invalid state check
    if state == 0:
        exit_to_dos()  # Game termination
        return

    # Calculate jump table index
    index = (state - 1) + entity_type
    table_offset = 0x1930 + (index * 2)

    # Read animation sequence pointer
    anim_seq_ptr = read_word(table_offset)

    # Special offset for player entities
    if (animation_flags & 0x08) != 0:
        if entity_type == 0x02 or entity_type == 0x36:
            anim_seq_ptr += 0x38  # +56 bytes (alternate animation set)

    # Set current animation state pointer
    animation_state_ptr = anim_seq_ptr  # Store at 0x1695
    return anim_seq_ptr
```

**점프 테이블 크기 추정**:
- Entity types: ~50 types
- Animation states: 3 states per type
- Total entries: ~150 pointers × 2 bytes = **~300 bytes**

**특수 오프셋 의미 (0x38 = 56 bytes)**:
- Type 0x02: Player 1 (추정)
- Type 0x36 (54): Player 2 (추정)
- +0x38 offset: 파워업 또는 무기 장착 상태의 대체 애니메이션 세트

---

### 3.3 링크드 리스트 프레임 시퀀스

#### 프레임 링크 구조

```c
struct AnimationFrameLink {
    DirectionalAnimation frame_data;  // +0:  40 bytes (5 directions × 8 bytes)
    uint16_t next_frame_ptr;          // +40: Pointer to next frame in sequence
};  // Total: 42 bytes
```

#### 프레임 진행 알고리즘

```python
function advance_animation_frame(entity_type, control_flags):
    # Fixed-frame entities (no animation)
    if entity_type == 0x2a or entity_type == 0x38:
        return  # Static sprites (items, obstacles)

    # Special conditional advancement (entity type 0x1a)
    if entity_type == 0x1a:
        # Check pause flags
        if control_flags_0 == 0 and control_flags_1 == 0:
            return  # Animation paused

        # Sub-animation sequence
        if control_flags_1 == 1:
            # Double indirection (linked sub-sequence)
            next_ptr = **(animation_state_ptr + 2) + 2)
            animation_state_ptr = next_ptr
            return

    # Normal frame advancement
    current_frame_ptr = animation_state_ptr
    next_frame_ptr = read_word(current_frame_ptr + 40)  # Offset +40 (after DirectionalAnimation)
    animation_state_ptr = next_frame_ptr
```

#### 애니메이션 루프 예시

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Frame 1     │      │ Frame 2     │      │ Frame 3     │      │ Frame 4     │
│ (Idle 1)    │      │ (Idle 2)    │      │ (Idle 3)    │      │ (Idle 2)    │
├─────────────┤      ├─────────────┤      ├─────────────┤      ├─────────────┤
│ Sprites × 5 │      │ Sprites × 5 │      │ Sprites × 5 │      │ Sprites × 5 │
│ Next ───────┼─────>│ Next ───────┼─────>│ Next ───────┼─────>│ Next ───────┼──┐
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘  │
      ↑                                                                           │
      └───────────────────────────────────────────────────────────────────────────┘
                                    (Loop back to Frame 1)
```

**장점**:
- 가변 길이 애니메이션 (2-20+ 프레임)
- 메모리 효율성 (사용 중인 프레임만 메모리에 존재)
- 동적 분기 가능 (조건에 따라 프레임 스킵 가능)

**단점**:
- 포인터 역참조 오버헤드 (캐시 미스 가능성)
- 메모리 단편화 가능성

---

### 3.4 화면 좌표 변환

#### 좌표 변환 공식

```python
function calculate_screen_coordinates(entity_x, entity_y, sprite_offset_x, sprite_offset_y,
                                      scroll_x, scroll_y):
    # X coordinate (pixel units, 1:1 mapping)
    screen_x = sprite_offset_x + entity_x - scroll_x

    # Y coordinate (4× scale)
    screen_y = sprite_offset_y + (entity_y - scroll_y) * 4

    return (screen_x, screen_y)
```

#### Y축 × 4 스케일의 의미

**가설 1: 고정소수점 연산 (가장 유력)**
```
내부 좌표계: 0.25 픽셀 정밀도 (1/4 pixel precision)
화면 좌표계: 1 픽셀 정밀도

Example:
  Entity Y = 100.75 pixels → Internal value = 403 (100.75 × 4)
  Screen Y = 403 / 4 = 100 pixels (truncated)

장점:
  - 부드러운 움직임 (sub-pixel movement)
  - 정수 연산만 사용 (부동소수점 불필요, 8086 CPU에 이상적)
  - 속도 계산 정밀도 향상 (vel_y = 0.5 pixels/frame = 2 units/frame)
```

**가설 2: CGA 인터레이스 보정**
```
CGA 4-color mode 메모리 레이아웃:
  Even scanlines: Buffer A (0xB800:0000)
  Odd scanlines:  Buffer B (0xB800:2000)

Y × 4 = 인터레이스 주소 계산을 위한 사전 스케일링?
```

**가설 3: 좌표계 변환**
```
World space: 픽셀 단위
Screen space: CGA word 단위 (2 bytes per pixel × 2 planes = 4)
```

**결론**: 가설 1(고정소수점)이 가장 타당합니다. 다른 DOS 게임들도 유사한 기법을 사용합니다.

---

### 3.5 렌더 우선순위 (Z-Order)

#### 우선순위 계산

```python
function calculate_priority(entity_state_byte):
    # Entity state byte: @ 0x168f (work buffer)
    # Negative offset: -0xb10 (-2832 decimal)

    priority_table_address = entity_state_byte - 0xb10
    priority_value = read_word(priority_table_address)

    return priority_value
```

#### 메모리 주소 계산 (추정)

```
Given:
  entity_state_byte = 0x168f (work buffer location)
  offset = -0xb10 (2832 decimal)

Calculation (16-bit arithmetic with segment):
  DS = 0x1988 (data segment, 추정)
  Effective address = DS:0x168f - 0xb10
                    = 0x1988:0x168f - 0xb10
                    = 0x1988:0x0b7f

Estimated priority table location: 0x1988:0x0b7f
```

#### 우선순위 값 추정

```
Entity Type       | Priority | Rendering Order
------------------|----------|------------------
Background tiles  |    0     | Back
Items on ground   |   10     | ↑
Player shadow     |   20     | │
Enemy shadow      |   30     | │
Player character  |   50     | │
Enemy character   |   60     | │
Thrown objects    |   70     | │
Effects (sparks)  |   80     | │
UI elements       |   90     | Front
```

**정렬 방식**: 렌더 리스트를 우선순위 값으로 정렬한 후 순차 렌더링 (낮은 값 = 먼저 그림 = 뒤에 위치)

---

### 3.6 렌더 리스트 엔트리

#### 구조체 정의

```c
struct RenderListEntry {
    int16_t screen_x;           // +0:  Screen X coordinate (pixels)
    int16_t screen_y;           // +2:  Screen Y coordinate (pixels, already × 4)
    int16_t width;              // +4:  Sprite width (pixels)
    int16_t height;             // +6:  Sprite height (pixels)
    uint16_t sprite_data_ptr;   // +8:  Pointer to sprite pixel data
    int16_t priority;           // +10: Z-order value (lower = rendered first)
};  // Total: 12 bytes (6 words)
```

#### 렌더 리스트 생성 과정

```python
function add_to_render_list(entity):
    # 1. Get animation frame data
    if animation_state_ptr == -1:
        lookup_animation_sequence(entity.type, entity.animation_flags)

    anim_frame_ptr = animation_state_ptr

    # 2. Apply direction offset
    frame_data_ptr = select_directional_sprite(entity.direction)

    # 3. Read frame data
    sprite_ptr = read_word(frame_data_ptr + 0)
    width = read_byte(frame_data_ptr + 4)
    height = read_byte(frame_data_ptr + 5)
    offset_x = read_signed_byte(frame_data_ptr + 6)
    offset_y = read_signed_byte(frame_data_ptr + 7)

    # 4. Calculate screen coordinates
    screen_x, screen_y = calculate_screen_coordinates(
        entity.x, entity.y, offset_x, offset_y,
        scroll_x, scroll_y
    )

    # 5. Calculate priority
    priority = calculate_priority(entity.state_byte)

    # 6. Create render list entry
    entry = RenderListEntry(
        screen_x=screen_x,
        screen_y=screen_y,
        width=width,
        height=height,
        sprite_data_ptr=sprite_ptr,
        priority=priority
    )

    # 7. Add to render list (@ 0x169f)
    render_list.append(entry)
```

---

## 4. 메모리 레이아웃

### 4.1 애니메이션 상태 변수 (0x168f - 0x16a1)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x168f   |  1   | entity_state_byte         | Entity state (used for priority calc)
0x1690   |  1   | entity_direction          | Direction code (0x00/0x02/0x04/0x06/0x08)
0x1691   |  1   | entity_type               | Entity type (animation table index)
0x1693   |  1   | animation_flags           | Bit 0-1: state, Bit 3: special offset
0x1695   |  2   | animation_state_ptr       | Current animation frame pointer
0x1697   |  2   | entity_x                  | Entity X coordinate (world space)
0x1699   |  2   | entity_y                  | Entity Y coordinate (world space)
0x169b   |  2   | animation_control_0       | Playback control flag 0 (pause, etc.)
0x169d   |  2   | animation_control_1       | Playback control flag 1 (sub-sequence)
0x169f   |  2   | render_list_entry_ptr     | Pointer to render list entry
0x16a1   |  -   | (end)                     | -
```

**총 크기**: 18 bytes

### 4.2 점프 테이블 (0x1930)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x1930   | ~300 | animation_sequence_table  | Animation sequence pointers
         |      |                           | ~150 entries × 2 bytes
         |      |                           | Index = (state - 1) + entity_type
```

### 4.3 스크롤 위치 (0xf396 - 0xf398)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0xf396   |  2   | scroll_x                  | Horizontal scroll position
0xf398   |  2   | scroll_y                  | Vertical scroll position
```

---

## 5. 함수 목록

### 5.1 핵심 함수

| Function | Address    | Size | Complexity | Called     | Description |
|----------|------------|------|------------|------------|-------------|
| FUN_0426 | 1000:0426  | 131  | High       | Every frame| Sprite frame selector |
| FUN_04a9 | 1000:04a9  | 55   | Medium     | State change| Animation state lookup |
| FUN_04e1 | 1000:04e1  | 54   | Medium     | Every frame| Frame advancer |

**총 코드 크기**: 240 bytes

### 5.2 함수별 상세 설명

#### FUN_0426 - Sprite Frame Selector

**역할**: 현재 애니메이션 상태와 방향을 기반으로 렌더링할 스프라이트 프레임을 선택하고 렌더 리스트에 추가합니다.

**입력**:
- `0x1695`: 애니메이션 상태 포인터 (또는 -1)
- `0x1690`: 엔티티 방향 (0x00/0x02/0x04/0x06/0x08)
- `0x1697`, `0x1699`: 엔티티 좌표 (x, y)
- `0xf396`, `0xf398`: 스크롤 위치 (scroll_x, scroll_y)

**출력**:
- `0x169f`가 가리키는 렌더 리스트 엔트리 업데이트:
  - `screen_x`, `screen_y`: 화면 좌표
  - `width`, `height`: 스프라이트 크기
  - `sprite_data_ptr`: 스프라이트 데이터 주소
  - `priority`: 렌더 우선순위

**알고리즘**:
1. 애니메이션 상태 무효(-1)이면 `FUN_04a9()` 호출하여 갱신
2. 현재 애니메이션 프레임 포인터 읽기
3. 방향에 따라 오프셋 적용 (0/+8/+16/+24/+32 bytes)
4. 프레임 데이터 읽기 (sprite_ptr, width, height, offset_x, offset_y)
5. 화면 좌표 계산 (스크롤 보정 + Y축 × 4)
6. 우선순위 계산 (entity_state_byte - 0xb10)
7. 렌더 리스트 엔트리에 값 기록

**호출 빈도**: 매 프레임 (엔티티당 1회)

---

#### FUN_04a9 - Animation State Lookup

**역할**: 엔티티 타입과 애니메이션 플래그를 기반으로 점프 테이블(0x1930)에서 애니메이션 시퀀스를 조회합니다.

**입력**:
- `0x1691`: 엔티티 타입
- `0x1693`: 애니메이션 플래그 (state + special offset)

**출력**:
- `0x1695`: 애니메이션 상태 포인터 갱신

**알고리즘**:
1. 플래그의 bit 0-1 추출 (state)
2. state가 0이면 게임 종료 (`FUN_1ba0()`)
3. 점프 테이블 인덱스 계산: `(state - 1) + entity_type`
4. 테이블에서 포인터 읽기: `*(0x1930 + index × 2)`
5. 특수 플래그(bit 3) 및 타입(0x02/0x36) 체크
6. 조건 만족 시 포인터에 +0x38 오프셋 추가
7. 결과를 `0x1695`에 저장

**호출 빈도**: 애니메이션 상태 변경 시 (전투 동작, 이동 시작/종료 등)

---

#### FUN_04e1 - Animation Frame Advancer

**역할**: 링크드 리스트를 따라 다음 애니메이션 프레임으로 진행합니다.

**입력**:
- `0x1691`: 엔티티 타입
- `0x1695`: 현재 프레임 포인터
- `0x169b`, `0x169d`: 애니메이션 제어 플래그

**출력**:
- `0x1695`: 다음 프레임 포인터로 갱신

**알고리즘**:
1. 특수 타입(0x2a, 0x38) 체크 → 고정 프레임이면 리턴
2. 타입 0x1a (발사체/이펙트) 특수 처리:
   - 플래그 0x169b, 0x169d가 모두 0이면 일시정지 → 리턴
   - 플래그 0x169d == 1이면 이중 간접 참조로 서브 시퀀스 진행
3. 일반 프레임 진행: `next_ptr = *(current_ptr + 40)`
4. `0x1695`에 next_ptr 저장

**호출 빈도**: 매 프레임 (엔티티당 1회, 일부 타입 제외)

---

## 6. 구현 가이드

### 6.1 데이터 구조 정의

```python
# Animation frame data (8 bytes per direction)
class AnimationFrameData:
    def __init__(self):
        self.sprite_data_ptr = 0      # uint16
        self.reserved = 0              # uint16 (unused)
        self.width = 0                 # uint8
        self.height = 0                # uint8
        self.offset_x = 0              # int8 (signed)
        self.offset_y = 0              # int8 (signed)

# Directional animation (40 bytes)
class DirectionalAnimation:
    def __init__(self):
        self.default = AnimationFrameData()
        self.right = AnimationFrameData()
        self.up = AnimationFrameData()
        self.left = AnimationFrameData()
        self.down = AnimationFrameData()

# Animation frame link (42 bytes)
class AnimationFrameLink:
    def __init__(self):
        self.frame_data = DirectionalAnimation()
        self.next_frame_ptr = 0        # uint16

# Render list entry (12 bytes)
class RenderListEntry:
    def __init__(self):
        self.screen_x = 0              # int16
        self.screen_y = 0              # int16
        self.width = 0                 # int16
        self.height = 0                # int16
        self.sprite_data_ptr = 0       # uint16
        self.priority = 0              # int16
```

### 6.2 핵심 함수 구현 (Pseudocode)

#### Sprite Frame Selector

```python
function sprite_frame_selector(entity, render_list):
    # 1. Validate animation state
    if entity.animation_state_ptr == -1:
        entity.animation_state_ptr = animation_state_lookup(
            entity.type, entity.animation_flags
        )

    # 2. Get current frame
    frame_link = read_animation_frame(entity.animation_state_ptr)

    # 3. Select directional frame
    direction_offset = 0
    if entity.direction == 0x02:    # Right
        direction_offset = 1
    elif entity.direction == 0x06:  # Up
        direction_offset = 2
    elif entity.direction == 0x04:  # Left
        direction_offset = 3
    elif entity.direction == 0x08:  # Down
        direction_offset = 4

    # Get the appropriate directional frame
    if direction_offset == 0:
        frame_data = frame_link.frame_data.default
    elif direction_offset == 1:
        frame_data = frame_link.frame_data.right
    elif direction_offset == 2:
        frame_data = frame_link.frame_data.up
    elif direction_offset == 3:
        frame_data = frame_link.frame_data.left
    else:  # direction_offset == 4
        frame_data = frame_link.frame_data.down

    # 4. Calculate screen coordinates
    screen_x = frame_data.offset_x + entity.x - scroll_x
    screen_y = frame_data.offset_y + (entity.y - scroll_y) * 4

    # 5. Calculate priority
    priority = read_word(entity.state_byte - 0xb10)

    # 6. Create render list entry
    entry = RenderListEntry()
    entry.screen_x = screen_x
    entry.screen_y = screen_y
    entry.width = frame_data.width
    entry.height = frame_data.height
    entry.sprite_data_ptr = frame_data.sprite_data_ptr
    entry.priority = priority

    # 7. Add to render list
    render_list.append(entry)
```

#### Animation State Lookup

```python
function animation_state_lookup(entity_type, animation_flags):
    # 1. Extract state bits
    state = animation_flags & 0x03

    # 2. Invalid state check
    if state == 0:
        exit_to_dos()  # Critical error: game termination
        return None

    # 3. Calculate jump table index
    index = (state - 1) + entity_type
    table_address = 0x1930 + (index * 2)

    # 4. Read animation sequence pointer
    anim_seq_ptr = read_word(table_address)

    # 5. Special offset for player entities
    if (animation_flags & 0x08) != 0:
        if entity_type == 0x02 or entity_type == 0x36:
            anim_seq_ptr += 0x38  # Alternate animation set (powered-up?)

    return anim_seq_ptr
```

#### Animation Frame Advancer

```python
function advance_animation_frame(entity):
    # 1. Fixed-frame entities
    if entity.type == 0x2a or entity.type == 0x38:
        return  # No advancement (static sprites)

    # 2. Special entity type 0x1a
    if entity.type == 0x1a:
        # Check pause flags
        if entity.control_flags_0 == 0 and entity.control_flags_1 == 0:
            return  # Animation paused

        # Sub-sequence handling
        if entity.control_flags_1 == 1:
            # Double indirection
            sub_seq_ptr = read_word(entity.animation_state_ptr + 2)
            next_ptr = read_word(sub_seq_ptr + 2)
            entity.animation_state_ptr = next_ptr
            return

    # 3. Normal frame advancement
    current_frame_link = read_animation_frame(entity.animation_state_ptr)
    entity.animation_state_ptr = current_frame_link.next_frame_ptr
```

### 6.3 애니메이션 데이터 로딩

```python
function load_animation_data(file_path):
    # 1. Read animation file (likely LZW compressed)
    compressed_data = read_file(file_path)
    decompressed_data = lzw_decompress(compressed_data)

    # 2. Parse animation frames
    animation_frames = []
    offset = 0

    while offset < len(decompressed_data):
        frame_link = AnimationFrameLink()

        # Parse DirectionalAnimation (40 bytes)
        for direction in range(5):  # default, right, up, left, down
            frame_data = AnimationFrameData()
            frame_data.sprite_data_ptr = read_uint16(decompressed_data, offset + 0)
            frame_data.reserved = read_uint16(decompressed_data, offset + 2)
            frame_data.width = read_uint8(decompressed_data, offset + 4)
            frame_data.height = read_uint8(decompressed_data, offset + 5)
            frame_data.offset_x = read_int8(decompressed_data, offset + 6)
            frame_data.offset_y = read_int8(decompressed_data, offset + 7)

            # Assign to appropriate direction
            if direction == 0:
                frame_link.frame_data.default = frame_data
            elif direction == 1:
                frame_link.frame_data.right = frame_data
            elif direction == 2:
                frame_link.frame_data.up = frame_data
            elif direction == 3:
                frame_link.frame_data.left = frame_data
            else:  # direction == 4
                frame_link.frame_data.down = frame_data

            offset += 8

        # Parse next frame pointer (2 bytes)
        frame_link.next_frame_ptr = read_uint16(decompressed_data, offset)
        offset += 2

        animation_frames.append(frame_link)

    return animation_frames
```

### 6.4 우선순위 테이블 초기화

```python
# Entity type priority mapping
ENTITY_PRIORITIES = {
    0x00: 0,    # Background
    0x01: 10,   # Ground items
    0x02: 50,   # Player 1
    0x36: 50,   # Player 2
    0x10: 60,   # Enemy type 1
    0x11: 60,   # Enemy type 2
    0x2a: 20,   # Static object
    0x38: 20,   # Static object 2
    # ... (add all entity types)
}

function initialize_priority_table():
    # Allocate priority table (estimated @ 0x1988:0x0b7f)
    priority_table = [0] * 256  # 256 entity types max

    for entity_type, priority in ENTITY_PRIORITIES.items():
        priority_table[entity_type] = priority

    return priority_table
```

---

## 7. 테스트 전략

### 7.1 Unit Tests

```python
# Test 1: Direction offset calculation
def test_directional_sprite_selection():
    anim_frame = DirectionalAnimation()
    # Set distinct values for each direction
    anim_frame.default.sprite_data_ptr = 0x1000
    anim_frame.right.sprite_data_ptr = 0x2000
    anim_frame.up.sprite_data_ptr = 0x3000
    anim_frame.left.sprite_data_ptr = 0x4000
    anim_frame.down.sprite_data_ptr = 0x5000

    assert select_directional_sprite(0x00).sprite_data_ptr == 0x1000
    assert select_directional_sprite(0x02).sprite_data_ptr == 0x2000
    assert select_directional_sprite(0x06).sprite_data_ptr == 0x3000
    assert select_directional_sprite(0x04).sprite_data_ptr == 0x4000
    assert select_directional_sprite(0x08).sprite_data_ptr == 0x5000

# Test 2: Jump table indexing
def test_animation_state_lookup():
    # Prepare mock jump table
    jump_table = [0] * 300
    jump_table[0] = 0x5000   # Entity type 0, state 1
    jump_table[1] = 0x5100   # Entity type 1, state 1
    jump_table[50] = 0x6000  # Entity type 0, state 2

    # Test normal lookup
    result = animation_state_lookup(entity_type=0, flags=0x01)
    assert result == 0x5000

    result = animation_state_lookup(entity_type=1, flags=0x01)
    assert result == 0x5100

    result = animation_state_lookup(entity_type=0, flags=0x02)
    assert result == 0x6000

    # Test special offset (player type 0x02, flag 0x08)
    jump_table[2] = 0x7000
    result = animation_state_lookup(entity_type=0x02, flags=0x09)  # state 1 + special
    assert result == 0x7000 + 0x38

# Test 3: Screen coordinate transformation
def test_screen_coordinate_calculation():
    entity_x = 100
    entity_y = 50
    sprite_offset_x = -8
    sprite_offset_y = -16
    scroll_x = 20
    scroll_y = 10

    screen_x, screen_y = calculate_screen_coordinates(
        entity_x, entity_y, sprite_offset_x, sprite_offset_y,
        scroll_x, scroll_y
    )

    assert screen_x == 100 + (-8) - 20 == 72
    assert screen_y == -16 + (50 - 10) * 4 == -16 + 160 == 144

# Test 4: Frame advancement
def test_animation_frame_advance():
    # Create linked frames
    frame1 = AnimationFrameLink()
    frame2 = AnimationFrameLink()
    frame3 = AnimationFrameLink()

    frame1.next_frame_ptr = id(frame2)
    frame2.next_frame_ptr = id(frame3)
    frame3.next_frame_ptr = id(frame1)  # Loop back

    entity = Entity()
    entity.animation_state_ptr = id(frame1)
    entity.type = 0x10  # Normal entity

    advance_animation_frame(entity)
    assert entity.animation_state_ptr == id(frame2)

    advance_animation_frame(entity)
    assert entity.animation_state_ptr == id(frame3)

    advance_animation_frame(entity)
    assert entity.animation_state_ptr == id(frame1)  # Looped
```

### 7.2 Integration Tests

```python
# Test: Full animation playback
def test_animation_playback_cycle():
    # Setup
    entity = create_test_entity(type=0x02, x=100, y=100)
    render_list = []
    scroll_x = 0
    scroll_y = 0

    # Load animation data
    animation_data = load_animation_data("test_walk.anim")
    entity.animation_state_ptr = animation_data[0]  # Start at frame 0

    # Simulate 30 frames (1 second @ 30 FPS)
    for frame in range(30):
        # Update direction (simulate movement)
        if frame < 10:
            entity.direction = 0x02  # Right
        elif frame < 20:
            entity.direction = 0x08  # Down
        else:
            entity.direction = 0x04  # Left

        # Select sprite frame
        sprite_frame_selector(entity, render_list)

        # Advance animation
        advance_animation_frame(entity)

    # Verify render list entries
    assert len(render_list) == 30
    assert all(entry.sprite_data_ptr != 0 for entry in render_list)

    # Verify direction changes reflected in sprite selection
    assert render_list[5].sprite_data_ptr != render_list[15].sprite_data_ptr
    assert render_list[15].sprite_data_ptr != render_list[25].sprite_data_ptr

# Test: Priority-based rendering order
def test_render_list_sorting():
    render_list = []

    # Create entities with different priorities
    player = create_test_entity(type=0x02, priority=50)
    enemy = create_test_entity(type=0x10, priority=60)
    item = create_test_entity(type=0x01, priority=10)

    # Add to render list (unsorted)
    sprite_frame_selector(player, render_list)
    sprite_frame_selector(enemy, render_list)
    sprite_frame_selector(item, render_list)

    # Sort by priority (low to high = back to front)
    render_list.sort(key=lambda entry: entry.priority)

    # Verify order
    assert render_list[0].priority == 10  # Item (back)
    assert render_list[1].priority == 50  # Player
    assert render_list[2].priority == 60  # Enemy (front)
```

### 7.3 Visual Verification Tests

```python
# Test: Animation consistency
def test_animation_visual_consistency():
    """
    Verify all frames in an animation sequence have consistent dimensions
    and proper linked list structure.
    """
    animation_data = load_animation_data("player_walk.anim")

    visited_frames = set()
    current_frame_ptr = animation_data[0]

    for iteration in range(100):  # Prevent infinite loop
        # Check for loop
        if id(current_frame_ptr) in visited_frames:
            break  # Loop detected (expected)

        visited_frames.add(id(current_frame_ptr))

        # Verify all directional frames have valid data
        frame_link = current_frame_ptr
        for direction in [frame_link.frame_data.default,
                          frame_link.frame_data.right,
                          frame_link.frame_data.up,
                          frame_link.frame_data.left,
                          frame_link.frame_data.down]:
            assert direction.width > 0
            assert direction.height > 0
            assert direction.sprite_data_ptr != 0

        # Advance to next frame
        current_frame_ptr = get_frame_by_ptr(frame_link.next_frame_ptr)

    assert len(visited_frames) > 0  # At least 1 frame
    assert len(visited_frames) < 100  # Loop should occur before 100 iterations

# Test: Screen coordinate edge cases
def test_screen_coordinate_edge_cases():
    """
    Test coordinate calculations at screen boundaries and overflow scenarios.
    """
    test_cases = [
        # (entity_x, entity_y, scroll_x, scroll_y, expected_screen_x, expected_screen_y)
        (0, 0, 0, 0, 0, 0),                    # Origin
        (320, 200, 0, 0, 320, 800),            # Screen bounds (320×200)
        (100, 100, 320, 200, -220, -400),      # Scrolled off-screen (left/up)
        (400, 300, 0, 0, 400, 1200),           # Beyond screen (right/down)
        (65535, 65535, 0, 0, 65535, 262140),   # 16-bit overflow
    ]

    for entity_x, entity_y, scroll_x, scroll_y, expected_x, expected_y in test_cases:
        screen_x, screen_y = calculate_screen_coordinates(
            entity_x, entity_y, 0, 0, scroll_x, scroll_y
        )
        assert screen_x == expected_x
        assert screen_y == expected_y
```

---

## 8. 참고

### 8.1 관련 시스템 문서

- **01_RENDERING.md**: 렌더 리스트 처리 및 스프라이트 블리팅 (이 시스템의 출력 소비자)
- **02_ENTITY_AI.md**: 엔티티 업데이트 루프 및 상태 머신 (이 시스템의 호출자)
- **05_INPUT_CAMERA.md**: 스크롤 위치 관리 (화면 좌표 변환에 필요)
- **07_COMPRESSION.md**: 애니메이션 데이터 압축 해제 (LZW 압축 사용)

### 8.2 원본 분석 문서

- `docs/function-analysis/ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md`: 초기 Phase 4 분석 (함수별 디컴파일 코드 포함)
- `docs/function-analysis/RENDERING_SCROLLING_SYSTEM_ANALYSIS.md`: 렌더링 시스템 분석 (Mode 1/2 차이점)
- `docs/function-analysis/ENTITY_SYSTEM_ANALYSIS.md`: 엔티티 업데이트 루프

### 8.3 메모리 맵 참고

```
Animation System Memory Regions:
┌─────────────────────────────────────────────────────────┐
│ 0x168f - 0x16a1  │ Animation state variables (18 bytes) │
│ 0x1930 - 0x1a5c  │ Jump table (~ 300 bytes)             │
│ 0xf396 - 0xf398  │ Scroll positions (4 bytes)           │
│ 0x0b7f (est.)    │ Priority table (~ 256 bytes)         │
└─────────────────────────────────────────────────────────┘

Total: ~578 bytes (static data)
```

### 8.4 성능 특성

**프레임당 오버헤드 (7개 엔티티 가정)**:
```
- FUN_0426 (Sprite Frame Selector):  131 bytes × 7 = 917 cycles (추정)
- FUN_04e1 (Frame Advancer):         54 bytes × 7 = 378 cycles
─────────────────────────────────────────────────────────────
Total:                                           ~1295 cycles/frame

At 4.77 MHz (original PC): ~0.27 ms/frame
At 60 FPS budget (16.67 ms): ~1.6% of frame time
```

**메모리 대역폭**:
- 애니메이션 상태 읽기: 18 bytes × 7 = 126 bytes/frame
- 프레임 데이터 읽기: 8 bytes × 7 = 56 bytes/frame
- 렌더 리스트 쓰기: 12 bytes × 7 = 84 bytes/frame
- **총합**: ~266 bytes/frame @ 60 FPS = ~16 KB/s

---

## 9. 구현 체크리스트

### Phase 1: 데이터 구조
- [ ] `AnimationFrameData` 구조체 정의 (8 bytes)
- [ ] `DirectionalAnimation` 구조체 정의 (40 bytes)
- [ ] `AnimationFrameLink` 구조체 정의 (42 bytes)
- [ ] `RenderListEntry` 구조체 정의 (12 bytes)

### Phase 2: 핵심 함수
- [ ] `select_directional_sprite()` 구현
- [ ] `animation_state_lookup()` 구현
- [ ] `advance_animation_frame()` 구현
- [ ] `calculate_screen_coordinates()` 구현
- [ ] `calculate_priority()` 구현
- [ ] `sprite_frame_selector()` 통합 구현

### Phase 3: 데이터 로딩
- [ ] 애니메이션 파일 포맷 파서 구현
- [ ] LZW 압축 해제 통합 (07_COMPRESSION.md 참조)
- [ ] 점프 테이블 초기화 로직
- [ ] 우선순위 테이블 초기화

### Phase 4: 테스트
- [ ] Unit tests (방향 선택, 테이블 인덱싱, 좌표 변환)
- [ ] Integration tests (전체 애니메이션 재생, 렌더 리스트 정렬)
- [ ] Visual tests (일관성 검증, 경계 조건)

### Phase 5: 최적화
- [ ] 프레임 데이터 캐싱 (중복 읽기 방지)
- [ ] 방향 선택 룩업 테이블 (if문 체인 대체)
- [ ] 렌더 리스트 사전 할당 (메모리 할당 오버헤드 제거)

---

**문서 작성**: Claude Code
**분석 기반**: Phase 4 함수 디컴파일 (161 functions)
**구현 독립성**: Language-agnostic (C, C++, JavaScript 모두 적용 가능)
