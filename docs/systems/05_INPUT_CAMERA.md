# Input & Camera System (입력 및 카메라 시스템)

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Complete

---

## 1. 개요

Double Dragon의 입력 및 카메라 시스템은 **2인 협동 플레이**를 지원하기 위해 설계되었습니다. 키보드와 조이스틱 입력을 동시에 처리하며, 두 플레이어를 모두 화면에 유지하는 동적 카메라 시스템을 제공합니다. 화면 깜빡임(tearing)을 방지하기 위해 CRT VSync 동기화를 사용합니다.

### 핵심 특징

1. **이중 입력 지원**: 키보드 (Player 1) + 조이스틱 (Player 2) 동시 처리
2. **2인 협동 카메라**: Bounding box 기반 자동 추적, 두 플레이어 모두 화면 안에 유지
3. **Dead Zone 스크롤**: Threshold 기반 부드러운 카메라 이동
4. **스크롤 경계**: 스테이지별 맵 한계 보호
5. **VSync 동기화**: Port 0x3DA 폴링으로 60 FPS 고정, 화면 깜빡임 방지
6. **난수 생성**: LCG (Linear Congruential Generator) 기반 AI 랜덤화

### 시스템 연동

```
Input Polling (Keyboard + Joystick)
    ↓
Player Movement Update
    ↓
Camera System (이 문서)
    ├─> Calculate 2-Player Bounds
    ├─> Check Dead Zones
    ├─> Execute Scroll (with boundary check)
    └─> Update Scroll Registers
    ↓
VSync Wait
    ↓
Rendering (sprite blitting, no tearing)
```

---

## 2. 아키텍처

### 2.1 시스템 개요도

```
┌────────────────────────────────────────────────────────────┐
│                   Main Loop (60 FPS)                       │
└───────────────────────┬────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Input Polling                │
        │  ┌─────────────┬────────────┐ │
        │  │ Keyboard    │ Joystick   │ │
        │  │ (Player 1)  │ (Player 2) │ │
        │  └──────┬──────┴─────┬──────┘ │
        │         ↓            ↓         │
        │    Input State   Input State  │
        │    (0x31c6)      (0x31c8)     │
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Player Movement Update       │
        │  - P1: (0x16ce, 0x16d0)       │
        │  - P2: (0x16e6, 0x16e8)       │
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Camera System                │
        │  FUN_0518: Camera Controller  │
        │     ↓                          │
        │  FUN_0590: Calculate Bounds   │
        │     ├─> Bounding Box          │
        │     ├─> Screen Coordinates    │
        │     └─> Dead Zone Check       │
        │     ↓                          │
        │  Scroll Decision               │
        │     ├─> X: Left/Right/None    │
        │     └─> Y: Up/Down/None       │
        │     ↓                          │
        │  Boundary Check                │
        │     ├─> Min/Max Scroll X/Y    │
        │     └─> Execute Scroll         │
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │  Rendering                    │
        │  - Build render list          │
        │  - VSync Wait (FUN_0604)      │
        │  - Blit sprites to VRAM       │
        │  - Update scroll registers    │
        └───────────────────────────────┘
```

### 2.2 카메라 추적 모드

```
┌─────────────────────────────────────────────────────────────┐
│  1인 플레이 (Single Player)                                  │
├─────────────────────────────────────────────────────────────┤
│  Player 1 Active, Player 2 Inactive                         │
│  → Camera follows Player 1 only                             │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │  Screen              │                                   │
│  │     [P1]             │ ← Camera centered on P1           │
│  │                      │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2인 플레이 - 플레이어 가까이 (Close Together)                │
├─────────────────────────────────────────────────────────────┤
│  Both players within dead zone                              │
│  → Camera stays fixed                                       │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │  Screen              │                                   │
│  │    [P1] [P2]         │ ← Both in dead zone, no scroll    │
│  │                      │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2인 플레이 - 플레이어 멀리 (Spread Apart)                   │
├─────────────────────────────────────────────────────────────┤
│  Players near opposite edges                                │
│  → Camera adjusts to keep both on screen                    │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │  Screen              │                                   │
│  │ [P1]          [P2]   │ ← Bounding box includes both      │
│  │                      │                                   │
│  └──────────────────────┘                                   │
│                                                              │
│  If P1 or P2 hits edge → Camera scrolls                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2인 플레이 - 한 명 사망 (One Player Down)                   │
├─────────────────────────────────────────────────────────────┤
│  Player 1 Dead, Player 2 Active                             │
│  → Camera switches to follow P2 only                        │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │  Screen              │                                   │
│  │  [P1💀]      [P2]    │ ← Camera follows P2               │
│  │                      │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 입력 시스템

### 3.1 키보드 입력

#### 키보드 레이아웃 (Player 1)

```
Movement:
  Arrow Keys
    ↑ : Up
  ← ↓ → : Left, Down, Right

Actions:
  Ctrl  : Attack (punch/kick)
  Alt   : Jump
  Space : Special attack
```

#### 입력 처리 (BIOS INT 16h)

```python
function poll_keyboard_input():
    # BIOS keyboard service
    # INT 16h, AH=01h: Check for keystroke (non-blocking)
    # Returns: ZF=1 if no key, ZF=0 if key available

    if bios_int16h_check_keystroke():
        # INT 16h, AH=00h: Read keystroke (blocking)
        scancode = bios_int16h_read_keystroke()

        # Map scancode to input state
        input_state = 0x0000

        # Arrow keys (scancodes)
        if scancode == 0x48:  # Up arrow
            input_state |= 0x01
        if scancode == 0x50:  # Down arrow
            input_state |= 0x02
        if scancode == 0x4B:  # Left arrow
            input_state |= 0x04
        if scancode == 0x4D:  # Right arrow
            input_state |= 0x08

        # Action keys
        if scancode == 0x1D:  # Ctrl
            input_state |= 0x10  # Attack
        if scancode == 0x38:  # Alt
            input_state |= 0x20  # Jump
        if scancode == 0x39:  # Space
            input_state |= 0x40  # Special

        # Store input state
        write_word(0x31c6, input_state)  # Player 1 input
```

#### 입력 상태 비트맵 (0x31c6)

```
Bit | Input    | Description
----|----------|---------------------------
0   | Up       | Move up
1   | Down     | Move down
2   | Left     | Move left
3   | Right    | Move right
4   | Attack   | Punch/kick
5   | Jump     | Jump
6   | Special  | Special attack
7   | (unused) | -
```

---

### 3.2 조이스틱 입력

#### 조이스틱 인터페이스 (Port 0x201)

```
IBM PC Game Port (0x201):
┌────────────────────────────────────────────┐
│  Bit 7 6 5 4 | 3 2 1 0                     │
│  ───────────────────────────               │
│  B4 B3 B2 B1 | Y2 X2 Y1 X1                 │
│  │  │  │  │    │  │  │  └─ Joystick 1 X    │
│  │  │  │  │    │  │  └─── Joystick 1 Y     │
│  │  │  │  │    │  └────── Joystick 2 X     │
│  │  │  │  │    └───────── Joystick 2 Y     │
│  │  │  │  └────────────── Button 1         │
│  │  │  └───────────────── Button 2         │
│  │  └──────────────────── Button 3 (rare)  │
│  └─────────────────────── Button 4 (rare)  │
└────────────────────────────────────────────┘

Axes (bits 0-3): RC charging time (0-255)
Buttons (bits 4-7): Active LOW (0 = pressed)
```

#### 조이스틱 축 읽기 (RC Charging)

```python
function read_joystick_axis(axis_bit):
    # 1. Trigger RC circuit charge cycle
    out_byte(0x201, 0xFF)  # Write any value to reset

    # 2. Wait for axis bit to go HIGH (charge start)
    start_time = read_timer()

    # 3. Poll until axis bit goes LOW (charge complete)
    while (in_byte(0x201) & axis_bit) != 0:
        if read_timer() - start_time > 255:
            return 255  # Timeout (joystick disconnected?)

    # 4. Elapsed time = axis position (0-255)
    elapsed = read_timer() - start_time
    return elapsed


function poll_joystick_input():
    # Read axes (0-255 range)
    x_axis = read_joystick_axis(0x01)  # Bit 0 (X1)
    y_axis = read_joystick_axis(0x02)  # Bit 1 (Y1)

    # Read buttons (active LOW)
    buttons = in_byte(0x201)

    # Convert axes to directional input
    input_state = 0x0000

    # Dead zone calibration (center ≈ 127-128)
    if x_axis < 64:       # Left
        input_state |= 0x04
    elif x_axis > 192:    # Right
        input_state |= 0x08

    if y_axis < 64:       # Up
        input_state |= 0x01
    elif y_axis > 192:    # Down
        input_state |= 0x02

    # Buttons (invert because active LOW)
    if (buttons & 0x10) == 0:  # Button 1 (Bit 4)
        input_state |= 0x10  # Attack
    if (buttons & 0x20) == 0:  # Button 2 (Bit 5)
        input_state |= 0x20  # Jump

    # Store input state
    write_word(0x31c8, input_state)  # Player 2 input
```

#### 조이스틱 캘리브레이션

```python
# Typical calibration values (varies by joystick)
JOYSTICK_CALIBRATION = {
    'x_min': 0,       # Full left
    'x_center': 127,  # Neutral
    'x_max': 255,     # Full right
    'y_min': 0,       # Full up
    'y_center': 127,  # Neutral
    'y_max': 255,     # Full down
    'deadzone': 32    # ±32 around center = no input
}

function calibrate_axis(raw_value, axis):
    center = JOYSTICK_CALIBRATION[axis + '_center']
    deadzone = JOYSTICK_CALIBRATION['deadzone']

    # Dead zone check
    if abs(raw_value - center) < deadzone:
        return 0  # Neutral

    # Negative direction
    if raw_value < center:
        return -1

    # Positive direction
    return 1
```

---

### 3.3 입력 통합

```python
function update_player_inputs():
    # Poll both input devices
    poll_keyboard_input()    # → 0x31c6 (Player 1)
    poll_joystick_input()    # → 0x31c8 (Player 2)

    # Merge inputs with player states
    if player1_active:
        player1_input = read_word(0x31c6)
        update_player_movement(player1, player1_input)

    if player2_active:
        player2_input = read_word(0x31c8)
        update_player_movement(player2, player2_input)


function update_player_movement(player, input_state):
    # Directional movement (4-way)
    if input_state & 0x01:  # Up
        player.vel_y = -MOVE_SPEED
    elif input_state & 0x02:  # Down
        player.vel_y = +MOVE_SPEED
    else:
        player.vel_y = 0

    if input_state & 0x04:  # Left
        player.vel_x = -MOVE_SPEED
        player.direction = DIR_LEFT
    elif input_state & 0x08:  # Right
        player.vel_x = +MOVE_SPEED
        player.direction = DIR_RIGHT
    else:
        player.vel_x = 0

    # Actions
    if input_state & 0x10:  # Attack button
        trigger_attack(player)
    if input_state & 0x20:  # Jump button
        trigger_jump(player)
    if input_state & 0x40:  # Special button
        trigger_special(player)

    # Apply velocity
    player.x += player.vel_x
    player.y += player.vel_y
```

---

## 4. 카메라 시스템

### 4.1 2-플레이어 바운딩 박스 계산

```python
function calculate_2player_bounds():
    """
    Calculate bounding box that includes both players.
    Returns: (min_x, max_x, min_y, max_y) in screen coordinates
    """
    # Read player positions
    p1_x = read_word(0x16d0)  # Player 1 X
    p1_y = read_word(0x16ce)  # Player 1 Y
    p2_x = read_word(0x16e8)  # Player 2 X
    p2_y = read_word(0x16e6)  # Player 2 Y

    # Check player active status
    p1_active = read_byte(0x16c8)  # 0 = dead, 1 = active
    p2_active = read_byte(0x16e0)

    # Fallback: if one player dead, use the other's position
    if p1_active == 0:
        p1_x = p2_x
        p1_y = p2_y

    if p2_active == 0:
        p2_x = p1_x
        p2_y = p1_y

    # Calculate bounding box
    min_x = min(p1_x, p2_x)
    max_x = max(p1_x, p2_x)
    min_y = min(p1_y, p2_y)
    max_y = max(p1_y, p2_y)

    # Read current scroll position
    scroll_x = read_word(0xf396)
    scroll_y = read_word(0xf398)

    # Convert to screen coordinates
    screen_min_x = min_x - scroll_x
    screen_max_x = max_x - scroll_x
    screen_min_y = min_y - scroll_y
    screen_max_y = max_y - scroll_y

    # Store screen-relative bounds (used by camera controller)
    write_word(0x16b4, screen_min_x)  # Left player screen X
    write_word(0x16b6, screen_max_x)  # Right player screen X
    write_word(0x16b8, screen_min_y)  # Top player screen Y
    write_word(0x16ba, screen_max_y)  # Bottom player screen Y

    # Update max Y reached (for progression tracking)
    current_max_y = read_word(0x16bc)
    if max_y > current_max_y:
        write_word(0x16bc, max_y)  # Track furthest Y position

    return (screen_min_x, screen_max_x, screen_min_y, screen_max_y)
```

**메모리 맵**:
```
0x16c8: Player 1 active flag (0=dead, 1=active)
0x16ce: Player 1 Y position (world space)
0x16d0: Player 1 X position (world space)
0x16e0: Player 2 active flag
0x16e6: Player 2 Y position
0x16e8: Player 2 X position

0x16b4: Left player screen X (min_x - scroll_x)
0x16b6: Right player screen X (max_x - scroll_x)
0x16b8: Top player screen Y (min_y - scroll_y)
0x16ba: Bottom player screen Y (max_y - scroll_y)
0x16bc: Max Y position reached (progression)

0xf396: Current scroll X
0xf398: Current scroll Y
```

---

### 4.2 카메라 컨트롤러 (Dead Zone Scrolling)

```python
# Camera dead zone thresholds (pixels from screen edge)
CAMERA_THRESHOLDS = {
    'left_edge': 13,     # 0x0d
    'right_edge': 47,    # 0x2f
    'top_edge': 16,      # 0x10
    'bottom_edge': 32    # 0x20
}


function camera_controller():
    """
    Main camera update function. Called every frame.
    Implements dead zone scrolling with 2-player tracking.
    """
    # 1. Calculate 2-player bounds
    min_x, max_x, min_y, max_y = calculate_2player_bounds()

    # 2. Initialize scroll direction flags
    scroll_x_dir = 0  # -1=left, 0=none, +1=right
    scroll_y_dir = 0  # -1=up, 0=none, +1=down

    # 3. Check X-axis thresholds
    if max_x > CAMERA_THRESHOLDS['right_edge']:
        scroll_x_dir = +1  # Scroll right

    if min_x < CAMERA_THRESHOLDS['left_edge']:
        scroll_x_dir = -1  # Scroll left

    # 4. Check Y-axis thresholds
    if max_y > CAMERA_THRESHOLDS['bottom_edge']:
        scroll_y_dir = +1  # Scroll down

    if min_y < CAMERA_THRESHOLDS['top_edge']:
        scroll_y_dir = -1  # Scroll up

    # 5. Store scroll direction flags
    write_byte(0x16be, scroll_x_dir)
    write_byte(0x16bf, scroll_y_dir)

    # 6. Execute scrolling (with boundary checks)
    execute_scroll(scroll_x_dir, scroll_y_dir)
```

#### Dead Zone 시각화

```
Screen (320×200 pixels):
┌────────────────────────────────────────────────────┐
│ ↑                                                  │
│ │ top_edge (16px)                                  │
│ ↓                                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │    DEAD ZONE (no scroll)                     │  │
│  │                                               │  │
│←─→│    If both players in this zone,            │←─→│
│13px    camera stays fixed                      47px│
│  │                                               │  │
│  │    [P1]            [P2]                      │  │
│  │                                               │  │
│  └──────────────────────────────────────────────┘  │
│ ↑                                                  │
│ │ bottom_edge (32px)                               │
│ ↓                                                  │
└────────────────────────────────────────────────────┘

If P1 or P2 exceeds threshold → Camera scrolls
```

---

### 4.3 스크롤 실행 (Boundary Protection)

```python
# Scroll boundaries (set per stage)
SCROLL_LIMITS = {
    'min_x': 0,      # @ 0x38d3
    'max_x': 0,      # @ 0x38d5
    'min_y': 0,      # @ 0x38d7
    'max_y': 0       # @ 0x38d9
}


function execute_scroll(scroll_x_dir, scroll_y_dir):
    """
    Execute camera scroll with boundary checking.
    Prevents scrolling beyond stage limits.
    """
    scroll_x = read_word(0xf396)
    scroll_y = read_word(0xf398)

    # === X-axis scrolling ===
    if scroll_x_dir != 0:
        if scroll_x_dir < 0:  # Scroll LEFT
            # Check left boundary
            if SCROLL_LIMITS['min_x'] < scroll_x:
                scroll_left()  # Call Mode 1/2 scroll function
        else:  # Scroll RIGHT
            # Check right boundary
            if scroll_x < SCROLL_LIMITS['max_x']:
                scroll_right()

    # === Y-axis scrolling ===
    if scroll_y_dir != 0:
        if scroll_y_dir < 0:  # Scroll UP
            # Check top boundary
            if SCROLL_LIMITS['min_y'] < scroll_y:
                scroll_up()
        else:  # Scroll DOWN
            # Check bottom boundary
            if scroll_y < SCROLL_LIMITS['max_y']:
                scroll_down()


# Scroll functions (Mode 1 - EGA)
function scroll_left():
    # Decrement scroll X
    scroll_x = read_word(0xf396)
    write_word(0xf396, scroll_x - 1)

    # Update VRAM address (see 01_RENDERING.md)
    # Call FUN_1000_82f4() in original code

function scroll_right():
    scroll_x = read_word(0xf396)
    write_word(0xf396, scroll_x + 1)
    # Call FUN_1000_8277()

function scroll_up():
    scroll_y = read_word(0xf398)
    write_word(0xf398, scroll_y - 1)
    # Call FUN_1000_822a()

function scroll_down():
    scroll_y = read_word(0xf398)
    write_word(0xf398, scroll_y + 1)
    # Call FUN_1000_81c2()
```

#### 스크롤 경계 초기화 (Stage Load)

```python
function load_stage_scroll_limits(stage_id):
    """
    Load stage-specific scroll boundaries.
    Called when entering a new stage.
    """
    # Stage table @ 0x3fce (5 stages)
    stage_data_ptr = 0x3fce + (stage_id * STAGE_DATA_SIZE)

    # Read scroll limits from stage data
    min_x = read_word(stage_data_ptr + OFFSET_MIN_X)
    max_x = read_word(stage_data_ptr + OFFSET_MAX_X)
    min_y = read_word(stage_data_ptr + OFFSET_MIN_Y)
    max_y = read_word(stage_data_ptr + OFFSET_MAX_Y)

    # Store in memory
    write_word(0x38d3, min_x)
    write_word(0x38d5, max_x)
    write_word(0x38d7, min_y)
    write_word(0x38d9, max_y)

    # Example values (Stage 1)
    # min_x = 0    (cannot scroll left of start)
    # max_x = 2560 (stage width in pixels)
    # min_y = 0    (fixed vertical scroll in most stages)
    # max_y = 200  (or 0 if no vertical scrolling)
```

---

## 5. VSync 동기화

### 5.1 수직 동기화 (Vertical Blank)

#### CRT 타이밍 다이어그램

```
CRT Display Timing (60 Hz):
┌───────────────────────────────────────────────────────┐
│  Frame Duration: 16.67 ms                             │
├───────────────────────────────────────────────────────┤
│  Active Display: 15.20 ms (200 scanlines @ 31.5 kHz) │
│  ┌───────────────────────────────────────────────┐   │
│  │ Scanline 0   ████████████████████████████████ │   │
│  │ Scanline 1   ████████████████████████████████ │   │
│  │ Scanline 2   ████████████████████████████████ │   │
│  │     ...                                       │   │
│  │ Scanline 199 ████████████████████████████████ │   │
│  └───────────────────────────────────────────────┘   │
│              ↓                                        │
│  Vertical Blank: 1.47 ms (VSync pulse)                │
│  ┌───────────────────────────────────────────────┐   │
│  │ VSync ON (bit 3 = 1)                          │   │
│  │ ← SAFE TO UPDATE VRAM (no tearing)            │   │
│  └───────────────────────────────────────────────┘   │
│              ↓                                        │
│  Next Frame Start                                     │
└───────────────────────────────────────────────────────┘

Port 0x3DA (CGA/EGA Status Register):
  Bit 0: Display Enable (0=active, 1=retrace)
  Bit 3: Vertical Sync (1=VSync ON, 0=VSync OFF)
```

### 5.2 VSync 대기 함수

```python
function wait_for_vsync():
    """
    Wait for vertical blank period (VSync).
    Ensures no screen tearing during rendering.
    """
    # 1. Wait for VSync OFF (exit any previous VBlank)
    while (in_byte(0x3DA) & 0x08) != 0:
        pass  # Busy wait

    # 2. Wait for VSync ON (enter new VBlank)
    while (in_byte(0x3DA) & 0x08) == 0:
        pass  # Busy wait

    # → Now in VBlank period, safe to update VRAM
```

**타이밍 정확도**:
- ±1 scanline (~31.5 µs @ 31.5 kHz horizontal scan)
- 화면 깜빡임(tearing) 완전 방지
- 고정 60 FPS (CRT VSync 주기)

### 5.3 메인 루프 통합

```python
function main_game_loop():
    while game_running:
        # 1. Input and logic (< 15 ms to stay under 60 FPS)
        update_player_inputs()
        update_entities()
        update_camera()  # Camera controller
        update_physics()
        build_render_list()

        # 2. Wait for VSync (blocks until VBlank)
        wait_for_vsync()

        # 3. Rendering (during VBlank, ~1.47 ms window)
        clear_vram()
        blit_sprites_to_vram()
        update_scroll_registers()

        # 4. Frame complete, loop to next frame
```

**성능 고려사항**:
- VBlank 기간: 1.47 ms (짧음!)
- 복잡한 렌더링은 VBlank 전에 준비 (렌더 리스트)
- VBlank 동안: VRAM 쓰기만 수행

---

## 6. 난수 생성기 (RNG)

### 6.1 Linear Congruential Generator (LCG)

```python
# RNG state (global seed)
rng_seed = 0  # @ 0x16b2 (16-bit)


function lcg_random():
    """
    Generate next random number using LCG algorithm.

    Formula: X(n+1) = (X(n) × 77) mod 65536

    Returns: 16-bit pseudo-random value (0-65535)
    """
    global rng_seed

    # Special case: seed = 0
    if rng_seed == 0:
        rng_seed = -77  # 0xFFB3 = 65459
        return rng_seed

    # LCG formula with unusual modulo implementation
    result_32bit = rng_seed * 77  # 32-bit product

    low_word = result_32bit & 0xFFFF          # Bits 0-15
    high_word = (result_32bit >> 16) & 0xFFFF # Bits 16-31

    # Subtract high word from low word (unusual!)
    new_seed = low_word - high_word

    # Carry correction
    if low_word < high_word:
        new_seed += 1

    rng_seed = new_seed & 0xFFFF
    return rng_seed


function seed_rng(initial_seed):
    """Initialize RNG with seed value."""
    global rng_seed
    rng_seed = initial_seed if initial_seed != 0 else -77
```

### 6.2 RNG 사용 예시

```python
# Example 1: Random enemy spawn position
function spawn_enemy():
    lcg_random()
    x_offset = rng_seed % 160  # Random X offset (0-159)

    lcg_random()
    y_offset = rng_seed % 100  # Random Y offset (0-99)

    enemy.x = stage_start_x + x_offset
    enemy.y = stage_start_y + y_offset


# Example 2: Random AI decision (50% probability)
function enemy_ai_decision():
    lcg_random()

    if rng_seed & 0x01:  # Bit 0 (50% chance)
        attack_player()
    else:
        retreat()


# Example 3: Random attack delay
function random_attack_delay():
    lcg_random()
    delay_frames = 30 + (rng_seed % 60)  # 30-89 frames (0.5-1.5 seconds)
    return delay_frames
```

### 6.3 RNG 품질 분석

**LCG 파라미터**:
```
Multiplier (a): 77
Modulus (m):    65536 (2^16, implicit)
Increment (c):  0
```

**품질 평가**:
- **주기**: ~16384 (65536 / 4, 상대적으로 짧음)
- **분포**: 불균등 (multiplier 77은 소수가 아님)
- **예측 가능성**: 높음 (단순한 공식)

**적합한 용도**:
- ✅ 적 스폰 위치 랜덤화
- ✅ AI 행동 타이밍 변화
- ✅ 아이템 드롭 위치
- ❌ 암호학적 보안 (절대 안 됨)
- ❌ 공정한 확률 (카지노 게임 등)

**개선 가능성**:
```python
# Better LCG parameters (for reference only, not original code)
# Park and Miller "Minimal Standard" LCG:
#   a = 16807, m = 2^31 - 1, c = 0
#   Period: 2^31 - 2 (much longer)
```

---

## 7. 메모리 레이아웃

### 7.1 입력 시스템 (0x31c6 - 0x31c8)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x31c6   |  2   | player1_input_state       | Keyboard input bitmap (P1)
0x31c8   |  2   | player2_input_state       | Joystick input bitmap (P2)
```

### 7.2 카메라 시스템 (0x16b4 - 0x16bf)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x16b4   |  2   | screen_min_x              | Left player screen X (min_x - scroll_x)
0x16b6   |  2   | screen_max_x              | Right player screen X (max_x - scroll_x)
0x16b8   |  2   | screen_min_y              | Top player screen Y (min_y - scroll_y)
0x16ba   |  2   | screen_max_y              | Bottom player screen Y (max_y - scroll_y)
0x16bc   |  2   | max_y_reached             | Furthest Y position (progression)
0x16be   |  1   | scroll_x_direction        | X scroll flag (-1/0/+1)
0x16bf   |  1   | scroll_y_direction        | Y scroll flag (-1/0/+1)
```

### 7.3 플레이어 위치 (0x16c8 - 0x16e8)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x16c8   |  1   | player1_active            | P1 active flag (0=dead, 1=active)
0x16ce   |  2   | player1_y                 | P1 Y position (world space)
0x16d0   |  2   | player1_x                 | P1 X position (world space)
0x16e0   |  1   | player2_active            | P2 active flag
0x16e6   |  2   | player2_y                 | P2 Y position
0x16e8   |  2   | player2_x                 | P2 X position
```

### 7.4 스크롤 위치 및 경계 (0x38d3 - 0xf398)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x38d3   |  2   | scroll_limit_min_x        | Left scroll boundary
0x38d5   |  2   | scroll_limit_max_x        | Right scroll boundary
0x38d7   |  2   | scroll_limit_min_y        | Top scroll boundary
0x38d9   |  2   | scroll_limit_max_y        | Bottom scroll boundary
0xf396   |  2   | scroll_x                  | Current scroll X (pixels)
0xf398   |  2   | scroll_y                  | Current scroll Y (pixels)
```

### 7.5 RNG State (0x16b2)

```
Address  | Size | Name                      | Description
---------|------|---------------------------|----------------------------------
0x16b2   |  2   | rng_seed                  | LCG random number seed
```

---

## 8. 함수 목록

### 8.1 핵심 함수

| Function | Address    | Size | Complexity | Called     | Description |
|----------|------------|------|------------|------------|-------------|
| FUN_0518 | 1000:0518  | 118  | High       | Every frame| Camera controller (dead zone scroll) |
| FUN_0590 | 1000:0590  | 89   | Medium     | Every frame| Calculate 2-player bounds |
| FUN_0604 | 1000:0604  | 14   | Low        | Every frame| Wait for VSync |
| FUN_05e9 | 1000:05e9  | 26   | Low        | As needed  | LCG random number generator |

**총 코드 크기**: 247 bytes

### 8.2 함수별 상세 설명

#### FUN_0518 - Camera Controller

**역할**: 2인 협동 플레이를 위한 자동 카메라 제어. Dead zone 기반 스크롤 결정 및 실행.

**입력**:
- `0x16b4-0x16ba`: 플레이어 화면 상대 위치 (FUN_0590 출력)
- `0xf396`, `0xf398`: 현재 스크롤 위치
- `0x38d3-0x38d9`: 스크롤 경계값

**출력**:
- `0x16be`: X축 스크롤 방향 (-1/0/+1)
- `0x16bf`: Y축 스크롤 방향 (-1/0/+1)
- 스크롤 함수 호출 (Mode 1: FUN_82f4, FUN_8277, FUN_822a, FUN_81c2)

**알고리즘**:
1. FUN_0590 호출하여 2-플레이어 바운딩 박스 계산
2. 데드존 임계값 체크 (X: 13-47, Y: 16-32)
3. 스크롤 방향 플래그 설정
4. 경계값 체크 후 스크롤 함수 호출

**호출 빈도**: 매 프레임 (60 FPS)

---

#### FUN_0590 - Calculate 2-Player Camera Bounds

**역할**: 두 플레이어의 위치를 분석하여 카메라가 추적할 바운딩 박스를 계산합니다.

**입력**:
- `0x16c8`: Player 1 활성화 플래그
- `0x16ce`, `0x16d0`: Player 1 위치 (Y, X)
- `0x16e0`: Player 2 활성화 플래그
- `0x16e6`, `0x16e8`: Player 2 위치 (Y, X)
- `0xf396`, `0xf398`: 현재 스크롤 위치

**출력**:
- `0x16b4`: min_x - scroll_x (왼쪽 플레이어 화면 X)
- `0x16b6`: max_x - scroll_x (오른쪽 플레이어 화면 X)
- `0x16b8`: min_y - scroll_y (위쪽 플레이어 화면 Y)
- `0x16ba`: max_y - scroll_y (아래쪽 플레이어 화면 Y)
- `0x16bc`: max_y (진행도 추적)

**알고리즘**:
1. 플레이어 활성화 상태 체크 (사망 시 다른 플레이어 위치 사용)
2. min/max 계산으로 바운딩 박스 생성
3. 스크롤 위치를 뺀 화면 상대 좌표 계산
4. 최대 Y 위치 기록 (레벨 진행도)

**호출 빈도**: 매 프레임 (FUN_0518에서 호출)

---

#### FUN_0604 - Wait for VSync

**역할**: CRT 수직 귀선 기간(VBlank)까지 대기하여 화면 깜빡임(tearing)을 방지합니다.

**입력**:
- Port 0x3DA: CGA/EGA 상태 레지스터 (bit 3 = VSync)

**출력**:
- 없음 (VBlank 진입 후 리턴)

**알고리즘**:
1. VSync OFF 대기 (이전 VBlank 종료)
2. VSync ON 대기 (새 VBlank 시작)
3. 리턴 (VRAM 업데이트 안전 구간)

**호출 빈도**: 매 프레임 (렌더링 전)

---

#### FUN_05e9 - LCG Random Number Generator

**역할**: Linear Congruential Generator 알고리즘으로 의사 난수를 생성합니다.

**입력**:
- `0x16b2`: 현재 RNG seed (16-bit)

**출력**:
- `0x16b2`: 갱신된 RNG seed (16-bit)

**알고리즘**:
1. seed == 0 체크 → -77로 초기화
2. seed × 77 계산 (32-bit)
3. low_word - high_word (특이한 modulo 구현)
4. 캐리 보정 후 seed 갱신

**호출 빈도**: 랜덤 이벤트 발생 시 (적 스폰, AI 결정 등)

---

## 9. 구현 가이드

### 9.1 입력 시스템 초기화

```python
function initialize_input_system():
    # Clear input state
    write_word(0x31c6, 0x0000)  # Player 1 input
    write_word(0x31c8, 0x0000)  # Player 2 input

    # Calibrate joystick (optional, improves accuracy)
    calibrate_joystick()


function calibrate_joystick():
    """
    Calibrate joystick center position.
    User must leave joystick at neutral position.
    """
    print("Calibrating joystick... Leave joystick centered.")

    # Sample center position (average of 10 reads)
    x_sum = 0
    y_sum = 0

    for i in range(10):
        x_sum += read_joystick_axis(0x01)
        y_sum += read_joystick_axis(0x02)
        delay(10)  # 10 ms between samples

    JOYSTICK_CALIBRATION['x_center'] = x_sum / 10
    JOYSTICK_CALIBRATION['y_center'] = y_sum / 10

    print("Calibration complete!")
```

### 9.2 카메라 시스템 초기화

```python
function initialize_camera_system(stage_id):
    # Load stage-specific scroll limits
    load_stage_scroll_limits(stage_id)

    # Reset scroll position
    write_word(0xf396, 0)  # scroll_x = 0
    write_word(0xf398, 0)  # scroll_y = 0

    # Reset player bounds
    write_word(0x16b4, 0)
    write_word(0x16b6, 0)
    write_word(0x16b8, 0)
    write_word(0x16ba, 0)
    write_word(0x16bc, 0)  # max_y_reached

    # Clear scroll direction flags
    write_byte(0x16be, 0)
    write_byte(0x16bf, 0)
```

### 9.3 RNG 초기화

```python
function initialize_rng():
    # Seed with current timer value (pseudo-random)
    timer_value = read_bios_timer()  # DOS timer tick count
    seed_rng(timer_value & 0xFFFF)

    # Or use fixed seed for deterministic behavior (testing)
    # seed_rng(12345)
```

---

## 10. 테스트 전략

### 10.1 Input System Tests

```python
# Test 1: Keyboard input mapping
def test_keyboard_input():
    test_cases = [
        (0x48, 0x01),  # Up arrow → bit 0
        (0x50, 0x02),  # Down arrow → bit 1
        (0x4B, 0x04),  # Left arrow → bit 2
        (0x4D, 0x08),  # Right arrow → bit 3
        (0x1D, 0x10),  # Ctrl → bit 4 (attack)
    ]

    for scancode, expected_bit in test_cases:
        inject_keyboard_scancode(scancode)
        poll_keyboard_input()
        input_state = read_word(0x31c6)
        assert (input_state & expected_bit) != 0


# Test 2: Joystick calibration
def test_joystick_calibration():
    # Test center position (dead zone)
    x_axis = 127  # Center
    y_axis = 128  # Center

    direction = calibrate_axis(x_axis, 'x')
    assert direction == 0  # Neutral

    # Test left direction
    x_axis = 30
    direction = calibrate_axis(x_axis, 'x')
    assert direction == -1

    # Test right direction
    x_axis = 220
    direction = calibrate_axis(x_axis, 'x')
    assert direction == 1


# Test 3: Simultaneous inputs (2-player)
def test_simultaneous_inputs():
    # Player 1: Move right + attack
    inject_keyboard_scancode(0x4D)  # Right
    inject_keyboard_scancode(0x1D)  # Ctrl

    # Player 2: Move up
    inject_joystick_state(y_axis=30, buttons=0xFF)

    poll_keyboard_input()
    poll_joystick_input()

    p1_input = read_word(0x31c6)
    p2_input = read_word(0x31c8)

    assert (p1_input & 0x08) != 0  # Right
    assert (p1_input & 0x10) != 0  # Attack
    assert (p2_input & 0x01) != 0  # Up
```

### 10.2 Camera System Tests

```python
# Test 1: Single player tracking
def test_single_player_camera():
    # Setup: Player 1 active, Player 2 dead
    write_byte(0x16c8, 1)  # P1 active
    write_byte(0x16e0, 0)  # P2 dead

    # P1 at (100, 50)
    write_word(0x16d0, 100)
    write_word(0x16ce, 50)

    # Calculate bounds
    min_x, max_x, min_y, max_y = calculate_2player_bounds()

    # Both min and max should equal P1's position
    assert min_x == 100
    assert max_x == 100
    assert min_y == 50
    assert max_y == 50


# Test 2: 2-player bounding box
def test_2player_bounding_box():
    # Setup: Both players active
    write_byte(0x16c8, 1)
    write_byte(0x16e0, 1)

    # P1 at (50, 30), P2 at (200, 80)
    write_word(0x16d0, 50)
    write_word(0x16ce, 30)
    write_word(0x16e8, 200)
    write_word(0x16e6, 80)

    # Current scroll: (0, 0)
    write_word(0xf396, 0)
    write_word(0xf398, 0)

    min_x, max_x, min_y, max_y = calculate_2player_bounds()

    assert min_x == 50   # P1.x
    assert max_x == 200  # P2.x
    assert min_y == 30   # P1.y
    assert max_y == 80   # P2.y


# Test 3: Dead zone scrolling
def test_dead_zone_scrolling():
    # Setup: P1 inside dead zone
    write_word(0x16b4, 20)  # min_x (inside dead zone 13-47)
    write_word(0x16b6, 30)  # max_x
    write_word(0x16b8, 20)  # min_y (inside dead zone 16-32)
    write_word(0x16ba, 25)  # max_y

    camera_controller()

    # No scroll should occur
    assert read_byte(0x16be) == 0  # X direction
    assert read_byte(0x16bf) == 0  # Y direction

    # P1 exceeds right edge
    write_word(0x16b6, 50)  # max_x > 47

    camera_controller()

    # Should scroll right
    assert read_byte(0x16be) == 1


# Test 4: Scroll boundary protection
def test_scroll_boundary_protection():
    # Setup: Scroll at left boundary
    write_word(0xf396, 0)  # scroll_x = min
    write_word(0x38d3, 0)  # min_x limit

    # Request scroll left
    write_byte(0x16be, -1)

    execute_scroll(-1, 0)

    # Scroll should NOT change (at boundary)
    assert read_word(0xf396) == 0
```

### 10.3 VSync Tests

```python
# Test 1: VSync timing
def test_vsync_timing():
    start_time = current_time_ms()

    # Wait for 10 VSync cycles
    for i in range(10):
        wait_for_vsync()

    elapsed = current_time_ms() - start_time

    # 10 frames @ 60 FPS = ~167 ms
    assert 160 < elapsed < 180  # ±10 ms tolerance


# Test 2: No tearing visual check
def test_no_tearing_visual():
    """
    Visual test: Display scrolling animation.
    Observer should see no horizontal tearing.
    """
    for frame in range(600):  # 10 seconds
        # Update scroll
        scroll_x = (frame * 2) % 320

        # Wait for VSync
        wait_for_vsync()

        # Update VRAM during VBlank
        write_word(0xf396, scroll_x)
        render_test_pattern()

        # Observer: Check for horizontal tear lines
```

### 10.4 RNG Tests

```python
# Test 1: Seed initialization
def test_rng_seed_initialization():
    # Test zero seed special case
    write_word(0x16b2, 0)
    lcg_random()
    assert read_word(0x16b2) == 65459  # -77 in 16-bit


# Test 2: Distribution test
def test_rng_distribution():
    seed_rng(12345)

    # Generate 1000 random numbers
    counts = [0] * 4  # Count bits 0-1 (0-3 values)

    for i in range(1000):
        lcg_random()
        value = read_word(0x16b2)
        counts[value & 0x03] += 1

    # Each bucket should have ~250 counts (±50 tolerance)
    for count in counts:
        assert 200 < count < 300


# Test 3: Period test (detect repetition)
def test_rng_period():
    seed_rng(42)
    initial_seed = 42

    for iteration in range(1, 20000):
        lcg_random()
        if read_word(0x16b2) == initial_seed:
            print(f"Period detected: {iteration} iterations")
            break
    else:
        print("No period found in 20000 iterations")
```

---

## 11. 구현 체크리스트

### Phase 1: 입력 시스템
- [ ] 키보드 입력 폴링 (BIOS INT 16h)
- [ ] 조이스틱 입력 폴링 (Port 0x201)
- [ ] 입력 상태 비트맵 생성
- [ ] 조이스틱 캘리브레이션
- [ ] 2-플레이어 동시 입력 처리

### Phase 2: 카메라 시스템
- [ ] 2-플레이어 바운딩 박스 계산
- [ ] 화면 상대 좌표 변환
- [ ] 데드존 임계값 체크
- [ ] 스크롤 방향 결정 로직
- [ ] 스크롤 경계 보호 로직
- [ ] 스테이지별 경계값 로딩

### Phase 3: VSync 동기화
- [ ] Port 0x3DA 폴링 구현
- [ ] VSync OFF 대기
- [ ] VSync ON 대기
- [ ] 메인 루프 통합 (렌더링 전 호출)

### Phase 4: RNG
- [ ] LCG 알고리즘 구현
- [ ] Seed 초기화 (0 체크)
- [ ] 타이머 기반 시드 생성
- [ ] AI 시스템 통합

### Phase 5: 테스트
- [ ] Unit tests (입력, 카메라, RNG)
- [ ] Integration tests (2-player gameplay)
- [ ] Visual tests (VSync 검증)

---

## 12. 참고

### 12.1 관련 시스템 문서

- **01_RENDERING.md**: 스크롤 함수 상세 (Mode 1/2)
- **02_ENTITY_AI.md**: 입력 → 플레이어 이동 처리
- **03_ANIMATION.md**: 화면 좌표 변환 (scroll_x/y 사용)
- **08_HARDWARE_IO.md**: 조이스틱 하드웨어 세부사항

### 12.2 원본 분석 문서

- `docs/function-analysis/INPUT_CAMERA_PHYSICS_ANALYSIS.md`: 카메라 시스템 초기 분석
- `docs/function-analysis/CAMERA_VSYNC_SYSTEM_ANALYSIS.md`: VSync 및 RNG 상세 분석

### 12.3 하드웨어 레퍼런스

**Port 0x201 (Game Port)**:
- IBM PC Technical Reference Manual
- RC time constant: ~100 µs - 1 ms (varies by joystick resistance)

**Port 0x3DA (CGA/EGA Status)**:
- IBM Color Graphics Adapter Technical Reference
- VSync timing: 60 Hz ± 0.1 Hz (CRT standard)

---

**문서 작성**: Claude Code
**분석 기반**: Phase 4 함수 디컴파일 (161 functions)
**구현 독립성**: Language-agnostic (모든 플랫폼 적용 가능)
