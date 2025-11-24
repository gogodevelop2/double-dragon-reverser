# Entity & AI System (엔티티 및 AI 시스템)

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Complete

---

## 1. 개요

Double Dragon의 엔티티 및 AI 시스템은 **작업 버퍼 패턴**과 **점프 테이블 기반 상태 머신**을 사용하여 플레이어와 적 캐릭터를 관리합니다. 모든 엔티티는 동일한 업데이트 파이프라인을 거치며, 상태에 따라 다른 AI 함수가 실행됩니다.

### 핵심 특징

1. **작업 버퍼 패턴**: 엔티티 → 버퍼 → 처리 → 엔티티 (안전한 업데이트, 롤백 가능)
2. **AI 상태 머신**: 점프 테이블 기반 O(1) 디스패치 (@ 0x16ef, 256 states)
3. **7개 엔티티 슬롯**: 플레이어 2명 + 적 5명 (24 bytes/entity)
4. **충돌 디스패처**: 타입별 충돌 처리 (@ 0xe3f, 256 types)
5. **링크 시스템**: 부모-자식 관계 (무기, 투사체, 이펙트)
6. **타이머 시스템**: 플레이어별 타이머, 라이프 관리, 상태 전환

### 시스템 연동

```
Main Loop (60 FPS)
    ↓
Entity Update Loop (7 entities)
    ├─> Entity → Work Buffer (24 bytes)
    ├─> AI State Machine (jump table @ 0x16ef)
    ├─> Collision Dispatcher (jump table @ 0xe3f)
    ├─> Physics & Animation Update
    ├─> Sprite Rendering Prep
    └─> Work Buffer → Entity
    ↓
Rendering System (sprite blitting)
```

---

## 2. 아키텍처

### 2.1 엔티티 업데이트 파이프라인

```
┌───────────────────────────────────────────────────────────┐
│  Entity Array (7 slots × 24 bytes @ 0x16c6-0x1756)       │
│  [P1] [P2] [Enemy1] [Enemy2] [Enemy3] [Enemy4] [Enemy5]  │
└────────────────────┬──────────────────────────────────────┘
                     ↓
        For each entity (index 0-6):
                     ↓
        ┌────────────────────────────┐
        │ FUN_0412                   │
        │ Copy to Work Buffer        │
        │ memcpy(0x168f, entity, 24) │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Active Check               │
        │ if (entity[+2] != 0)       │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_16e0                   │
        │ AI State Machine           │
        │ jump_table[state]()        │
        │ @ 0x16ef                   │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_0e30                   │
        │ Collision Dispatcher       │
        │ jump_table[type]()         │
        │ @ 0xe3f                    │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_3e6d                   │
        │ Physics & Animation        │
        │ - State transitions        │
        │ - Timer management         │
        │ - Sprite update            │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_0426                   │
        │ Sprite Rendering Prep      │
        │ - Direction select         │
        │ - Screen coords            │
        │ - Add to render list       │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_041b                   │
        │ Copy from Work Buffer      │
        │ memcpy(entity, 0x168f, 24) │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_1668                   │
        │ Entity Commit              │
        │ - Link management          │
        │ - Render data init         │
        └────────────────────────────┘
```

### 2.2 엔티티 슬롯 배치

```
Memory Layout @ 0x16c6 - 0x1756:

Slot 0: 0x16c6 (24 bytes) → Player 1
Slot 1: 0x16de (24 bytes) → Player 2
Slot 2: 0x16f6 (24 bytes) → Enemy 1
Slot 3: 0x170e (24 bytes) → Enemy 2
Slot 4: 0x1726 (24 bytes) → Enemy 3
Slot 5: 0x173e (24 bytes) → Enemy 4
Slot 6: 0x1756 (24 bytes) → Enemy 5

Total: 7 slots × 24 bytes = 168 bytes
End marker: 0x176e
```

---

## 3. 엔티티 데이터 구조

### 3.1 Entity 구조체 (24 bytes)

```c
struct Entity {
    uint8_t  state;          // +0x00: AI state (jump table index @ 0x16ef)
    uint8_t  direction;      // +0x01: Direction (0x02/0x04/0x06/0x08)
    uint8_t  type;           // +0x02: Entity type (collision table index @ 0xe3f)
    uint8_t  depth_offset;   // +0x03: Z-order offset for rendering
    int16_t  field_04;       // +0x04: (unknown)
    int16_t  sprite_ptr;     // +0x06: Current sprite pointer
    int16_t  x_pos;          // +0x08: X position (world space)
    int16_t  y_pos;          // +0x0a: Y position (world space)
    int16_t  dir_flag;       // +0x0c: Direction flag (-1/0/1 for mirroring)
    int16_t  field_0e;       // +0x0e: (unknown)
    int16_t  render_data1;   // +0x10: Render list pointer
    int16_t  link_ptr;       // +0x12: Link to child entity (weapon, projectile, effect)
    int16_t  field_14;       // +0x14: (unknown)
    int16_t  field_16;       // +0x16: (unknown)
};  // Total: 24 bytes (0x18)
```

**필드 설명**:
- `state` (0x00): AI 상태 머신 인덱스 (0-255)
- `direction` (0x01): 방향 (0x02=Down, 0x04=Left, 0x06=Up, 0x08=Right)
- `type` (0x02): 엔티티 타입 (충돌 처리 인덱스, 0=inactive)
- `sprite_ptr` (0x06): 현재 애니메이션 프레임 스프라이트
- `x_pos`, `y_pos` (0x08, 0x0a): 월드 좌표
- `link_ptr` (0x12): 자식 엔티티 포인터 (-1 = none)

### 3.2 작업 버퍼 (Work Buffer @ 0x168f)

```
Work Buffer @ 0x168f (24+ bytes):
┌────────────────────────────────────────────────────┐
│ Offset | Address | Size | Field                   │
├────────┼─────────┼──────┼─────────────────────────┤
│ +0x00  │ 0x168f  │  1   │ state (AI index)        │
│ +0x01  │ 0x1690  │  1   │ direction (2/4/6/8)     │
│ +0x02  │ 0x1691  │  1   │ type (collision index)  │
│ +0x03  │ 0x1692  │  1   │ depth_offset            │
│ +0x04  │ 0x1693  │  2   │ (unknown)               │
│ +0x05  │ 0x1694  │  1   │ counter/timer           │
│ +0x06  │ 0x1695  │  2   │ sprite_ptr              │
│ +0x08  │ 0x1697  │  2   │ x_pos (world)           │
│ +0x0a  │ 0x1699  │  2   │ y_pos (world)           │
│ +0x0c  │ 0x169b  │  2   │ dir_flag (-1/0/1)       │
│ +0x0e  │ 0x169d  │  2   │ (unknown)               │
│ +0x10  │ 0x169f  │  2   │ render_list_ptr         │
│ +0x12  │ 0x16a1  │  2   │ link_ptr                │
│ +0x14  │ 0x16a3  │  2   │ (unknown)               │
│ +0x16  │ 0x16a5  │  2   │ (unknown)               │
└────────────────────────────────────────────────────┘

Extended fields (used by rendering):
│ +0x18  │ 0x16a7  │  2   │ calculated_x (screen)   │
│ +0x1a  │ 0x16a9  │  2   │ calculated_y (screen)   │
│ +0x1f  │ 0x16ae  │  1   │ collision_flag          │
```

**작업 버퍼의 목적**:
1. **안전한 업데이트**: 원본 엔티티 데이터 보호
2. **롤백 가능**: 업데이트 실패 시 복원
3. **고정 주소**: AI/물리 함수가 항상 동일한 주소 접근 (0x168f)
4. **원자성**: 복사 → 처리 → 복사 (중간 상태 노출 없음)

---

## 4. AI 상태 머신

### 4.1 점프 테이블 디스패처 (@ 0x16ef)

```python
function ai_dispatch():
    """
    AI state machine dispatcher using jump table.
    O(1) dispatch based on entity state.
    """
    # Read state from work buffer
    state = read_byte(0x168f)  # Entity state (0-255)

    # Calculate jump table address
    table_offset = 0x16ef + state  # Byte-indexed table
    func_ptr = read_word(table_offset)

    # Call AI function
    call(func_ptr)
```

#### 점프 테이블 구조

```
Jump Table @ 0x16ef:
┌────────┬──────────────┬──────────────────────────┐
│ State  │ Address      │ AI Function              │
├────────┼──────────────┼──────────────────────────┤
│ 0x00   │ 0x16ef[0x00] │ AI_Idle                  │
│ 0x01   │ 0x16ef[0x01] │ AI_Walk                  │
│ 0x02   │ 0x16ef[0x02] │ AI_Attack                │
│ 0x03   │ 0x16ef[0x03] │ AI_Hit                   │
│ 0x04   │ 0x16ef[0x04] │ AI_Jump                  │
│ 0x05   │ 0x16ef[0x05] │ AI_Fall                  │
│ 0x06   │ 0x16ef[0x06] │ AI_Dead                  │
│ 0x0a   │ 0x16ef[0x0a] │ AI_Special (Player 2)    │
│  ...   │     ...      │          ...             │
│ 0xFF   │ 0x16ef[0xFF] │ AI_State_255             │
└────────┴──────────────┴──────────────────────────┘

Table size: 256 entries × 2 bytes = 512 bytes
```

### 4.2 AI 상태 예시

```python
# State 0x00: Idle (standing still)
function ai_idle():
    # Check input
    if input_detected():
        # Transition to Walk
        write_byte(0x168f, 0x01)  # state = Walk
        return

    # Check nearby enemies
    if enemy_in_range():
        # Face toward enemy
        direction = calculate_direction_to_enemy()
        write_byte(0x1690, direction)


# State 0x01: Walk (moving)
function ai_walk():
    # Read direction from input/AI decision
    direction = read_byte(0x1690)

    # Apply movement velocity
    if direction == 0x02:  # Down
        y_pos = read_word(0x1699)
        write_word(0x1699, y_pos + WALK_SPEED)
    elif direction == 0x04:  # Left
        x_pos = read_word(0x1697)
        write_word(0x1697, x_pos - WALK_SPEED)
    # ... (Up, Right)

    # Check attack input
    if attack_button_pressed():
        write_byte(0x168f, 0x02)  # state = Attack
        write_byte(0x1694, 0)     # counter = 0


# State 0x02: Attack (punching/kicking)
function ai_attack():
    counter = read_byte(0x1694)

    # Animation frame progression
    if counter < ATTACK_DURATION:
        write_byte(0x1694, counter + 1)

        # Hitbox active frames (e.g., frames 3-5)
        if 3 <= counter <= 5:
            create_attack_hitbox()
    else:
        # Attack complete, return to Idle
        write_byte(0x168f, 0x00)  # state = Idle
        write_byte(0x1694, 0)


# State 0x03: Hit (taking damage)
function ai_hit():
    counter = read_byte(0x1694)

    # Hitstun duration
    if counter < HIT_STUN_FRAMES:
        write_byte(0x1694, counter + 1)
    else:
        # Check HP
        hp = read_byte(entity + 0x05)  # Hypothetical HP field
        if hp <= 0:
            write_byte(0x168f, 0x06)  # state = Dead
        else:
            write_byte(0x168f, 0x00)  # state = Idle


# State 0x06: Dead (death animation)
function ai_dead():
    counter = read_byte(0x1694)

    if counter < DEATH_ANIM_FRAMES:
        write_byte(0x1694, counter + 1)
    else:
        # Deactivate entity
        write_byte(0x1691, 0)  # type = 0 (inactive)
```

### 4.3 적 AI 예시 (Enemy Behavior)

```python
# State 0x10: Enemy Idle (patrol)
function ai_enemy_idle():
    # Simple AI: move toward player
    player_x = read_word(0x16d0)  # Player 1 X
    player_y = read_word(0x16ce)  # Player 1 Y
    enemy_x = read_word(0x1697)
    enemy_y = read_word(0x1699)

    # Calculate direction
    if abs(player_x - enemy_x) > abs(player_y - enemy_y):
        # Move horizontally
        if player_x > enemy_x:
            write_byte(0x1690, 0x08)  # Right
        else:
            write_byte(0x1690, 0x04)  # Left
        write_byte(0x168f, 0x11)  # state = Enemy Walk
    else:
        # Move vertically
        if player_y > enemy_y:
            write_byte(0x1690, 0x02)  # Down
        else:
            write_byte(0x1690, 0x06)  # Up
        write_byte(0x168f, 0x11)  # state = Enemy Walk

    # Random attack chance
    lcg_random()
    if (read_word(0x16b2) & 0x1F) == 0:  # ~3% chance per frame
        # Within attack range?
        distance = calculate_distance_to_player()
        if distance < ATTACK_RANGE:
            write_byte(0x168f, 0x12)  # state = Enemy Attack


# State 0x11: Enemy Walk (chase player)
function ai_enemy_walk():
    # Similar to player walk, but AI-controlled
    direction = read_byte(0x1690)

    if direction == 0x02:  # Down
        y_pos = read_word(0x1699)
        write_word(0x1699, y_pos + ENEMY_SPEED)
    # ... (other directions)

    # Check if close enough to attack
    distance = calculate_distance_to_player()
    if distance < ATTACK_RANGE:
        write_byte(0x168f, 0x12)  # state = Enemy Attack
    elif distance > CHASE_RANGE:
        write_byte(0x168f, 0x10)  # state = Enemy Idle


# State 0x12: Enemy Attack
function ai_enemy_attack():
    # Same as player attack, but different animation/damage
    counter = read_byte(0x1694)

    if counter < ENEMY_ATTACK_DURATION:
        write_byte(0x1694, counter + 1)

        if counter == ENEMY_ATTACK_HITFRAME:
            create_attack_hitbox(damage=ENEMY_DAMAGE)
    else:
        write_byte(0x168f, 0x10)  # state = Enemy Idle
        write_byte(0x1694, 0)
```

---

## 5. 충돌 디스패처

### 5.1 타입별 충돌 처리 (@ 0xe3f)

```python
function collision_dispatch():
    """
    Collision dispatcher using type-based jump table.
    O(1) dispatch based on entity type.
    """
    # Read type from work buffer
    entity_type = read_byte(0x1691)  # Entity type (0-255)

    # Calculate jump table address
    table_offset = 0xe3f + entity_type  # Byte-indexed table
    func_ptr = read_word(table_offset)

    # Call collision function
    call(func_ptr)
```

#### 충돌 테이블 구조

```
Collision Jump Table @ 0xe3f:
┌────────┬──────────────┬──────────────────────────┐
│ Type   │ Address      │ Collision Function       │
├────────┼──────────────┼──────────────────────────┤
│ 0x00   │ 0xe3f[0x00]  │ Collision_Inactive       │
│ 0x01   │ 0xe3f[0x01]  │ Collision_Player         │
│ 0x02   │ 0xe3f[0x02]  │ Collision_Enemy          │
│ 0x03   │ 0xe3f[0x03]  │ Collision_Item           │
│ 0x04   │ 0xe3f[0x04]  │ Collision_Projectile     │
│  ...   │     ...      │          ...             │
│ 0xFF   │ 0xe3f[0xFF]  │ Collision_Type_255       │
└────────┴──────────────┴──────────────────────────┘

Table size: 256 entries × 2 bytes = 512 bytes
```

### 5.2 충돌 처리 예시

```python
# Type 0x01: Player collision
function collision_player():
    # Check collision with all enemies
    for i in range(2, 7):  # Enemy slots 2-6
        enemy = entities[i]
        if enemy.type != 0:  # Active enemy
            if check_collision(work_buffer, enemy):
                # Player hit by enemy
                apply_damage(work_buffer, enemy.damage)
                write_byte(0x168f, 0x03)  # state = Hit


# Type 0x02: Enemy collision
function collision_enemy():
    # Check collision with players
    for i in range(0, 2):  # Player slots 0-1
        player = entities[i]
        if player.type != 0:  # Active player
            if check_collision(work_buffer, player):
                # Enemy hit by player
                apply_damage(work_buffer, player.attack_damage)
                write_byte(0x168f, 0x03)  # state = Hit


# Type 0x04: Projectile collision
function collision_projectile():
    # Check collision with all entities
    for i in range(0, 7):
        entity = entities[i]
        if entity.type != 0 and i != current_entity_index:
            if check_collision(work_buffer, entity):
                # Projectile hit target
                apply_damage(entity, work_buffer.damage)
                # Deactivate projectile
                write_byte(0x1691, 0)  # type = 0
                return
```

---

## 6. 물리 및 애니메이션 업데이트

### 6.1 FUN_3e6d - Physics & Animation System

```python
function physics_animation_update():
    """
    Update physics, timers, and animation for current entity.
    Handles state transitions and player respawn logic.
    """
    state = read_byte(0x168f)
    entity_type = read_byte(0x1691)
    counter = read_byte(0x1694)
    sprite_ptr = read_word(0x1695)

    # === Special State Checks ===
    if state != 0 and state != 0x0a:  # Not Player 1 or Player 2 state
        if counter != 0:
            return  # Wait for timer

        # Check specific sprites
        if sprite_ptr != 0x1b6c and sprite_ptr != 0x1b81:
            return

        # Deactivate
        write_byte(0x1691, 0)
        return

    # === Active Entity Processing ===
    if entity_type != 0:
        if counter > 0:
            return  # Wait for timer

        # Special type transitions
        if entity_type == 0x2a or entity_type == 0x02:
            write_byte(0x1691, 0x1e)  # Transition to type 0x1e
            write_word(0x1695, 0xFFFF)  # Reset sprite
            return

        # Sprite check
        if sprite_ptr != 0x25f0:
            return

        # Deactivate
        write_byte(0x1691, 0)
        return

    # === Player Timer Management ===
    if state == 0x0a:  # Player 2
        timer = read_word(0x442a)
        timer -= 1
        write_word(0x442a, timer)

        if timer == 0xFFFF:  # Underflow
            handle_player_respawn(player=2)
    else:  # Player 1 (state == 0x00)
        timer = read_word(0x4428)
        timer -= 1
        write_word(0x4428, timer)

        if timer == 0xFFFF:  # Underflow
            handle_player_respawn(player=1)


function handle_player_respawn(player):
    """
    Handle player respawn when timer expires.
    """
    lives_left = read_word(0x442c)

    if lives_left == 0:
        return  # Game over

    # Check respawn conditions
    if player == 2:
        if read_byte(0x31d9) != 0:
            return  # Condition not met
        write_word(0x442a, 2)  # Reset timer = 2
        write_word(0x4426, 0)
    else:  # Player 1
        if read_byte(0x3204) != 0 and read_byte(0x31c6) != 0:
            return  # Condition not met
        write_word(0x4428, 2)  # Reset timer = 2
        write_word(0x4424, 0)

    # Set respawn state
    write_byte(0x1694, 20)       # counter = 20
    write_byte(0x1691, 0x20)     # type = 0x20 (respawn)
    write_word(0x1695, 0xFFFF)   # sprite = -1 (reset)

    # Decrement lives
    write_word(0x442c, lives_left - 1)

    # Trigger respawn event
    trigger_respawn_event()  # FUN_3f71

    # Set stage timer
    stage_num = read_byte(0x38d0)
    stage_timer_value = read_word(0x4404 + (stage_num << 1))
    write_word(0x442e, stage_timer_value)
```

### 6.2 타이머 시스템

```
Player Timers:
┌────────────────────────────────────────────────────┐
│ Address | Size | Name           | Description     │
├─────────┼──────┼────────────────┼─────────────────┤
│ 0x4424  │  2   │ p1_backup      │ P1 timer backup │
│ 0x4426  │  2   │ p2_backup      │ P2 timer backup │
│ 0x4428  │  2   │ p1_timer       │ P1 active timer │
│ 0x442a  │  2   │ p2_timer       │ P2 active timer │
│ 0x442c  │  2   │ lives_left     │ Remaining lives │
│ 0x442e  │  2   │ stage_timer    │ Stage time      │
└────────────────────────────────────────────────────┘

Timer decrements every frame (60 FPS).
When timer reaches 0xFFFF (underflow), trigger respawn.
```

---

## 7. 링크 시스템 (부모-자식 관계)

### 7.1 FUN_1668 - Entity Commit & Link Management

```python
function entity_commit_and_link():
    """
    Commit entity updates and manage linked entities.
    Used for weapons, projectiles, and effects.
    """
    # Get link pointer from current entity
    current_entity_ptr = SI  # Register (entity address)
    link_ptr = read_word(current_entity_ptr + 0x12)

    if link_ptr != -1:  # Has linked child
        # 1. Clear link from parent
        write_word(current_entity_ptr + 0x12, 0xFFFF)

        # 2. Initialize child entity
        write_word(link_ptr + 0x10, 0xFFFF)  # render_data1 = -1
        write_byte(link_ptr + 0x02, 0x04)    # type = 4 (projectile?)
        write_word(link_ptr + 0x04, 0xFFFF)  # field_04 = -1
        write_word(link_ptr + 0x0c, 0xFFFE)  # field_0c = -2

        # 3. Calculate child Y position
        y_pos = calculate_y_position()  # FUN_1b92
        write_word(link_ptr + 0x0a, y_pos)  # Set Y coordinate
```

### 7.2 링크 사용 예시

```python
# Example: Player attack creates hitbox entity
function player_attack_start():
    # Find free entity slot
    for i in range(2, 7):
        if entities[i].type == 0:  # Inactive
            # Create hitbox entity
            hitbox = entities[i]
            hitbox.type = 0x05  # Hitbox type
            hitbox.x_pos = work_buffer.x_pos + ATTACK_OFFSET_X
            hitbox.y_pos = work_buffer.y_pos + ATTACK_OFFSET_Y
            hitbox.sprite_ptr = HITBOX_SPRITE
            hitbox.state = 0x20  # Hitbox state

            # Link to player
            write_word(0x16a1, entity_address(i))  # link_ptr
            break


# Example: Player throws weapon
function player_throw_weapon():
    # Find free entity slot
    for i in range(2, 7):
        if entities[i].type == 0:
            # Create thrown weapon
            weapon = entities[i]
            weapon.type = 0x04  # Projectile type
            weapon.x_pos = work_buffer.x_pos
            weapon.y_pos = work_buffer.y_pos
            weapon.vel_x = THROW_VELOCITY_X * direction
            weapon.vel_y = THROW_VELOCITY_Y
            weapon.sprite_ptr = WEAPON_SPRITE
            weapon.state = 0x30  # Projectile state

            # Link to player
            write_word(0x16a1, entity_address(i))
            break
```

---

## 8. 메모리 레이아웃

### 8.1 엔티티 배열 (0x16c6 - 0x1756)

```
Entity Array @ 0x16c6:
┌────────────────────────────────────────────────────┐
│ Address | Slot | Size | Entity                    │
├─────────┼──────┼──────┼───────────────────────────┤
│ 0x16c6  │  0   │  24  │ Player 1                  │
│ 0x16de  │  1   │  24  │ Player 2                  │
│ 0x16f6  │  2   │  24  │ Enemy 1                   │
│ 0x170e  │  3   │  24  │ Enemy 2                   │
│ 0x1726  │  4   │  24  │ Enemy 3                   │
│ 0x173e  │  5   │  24  │ Enemy 4                   │
│ 0x1756  │  6   │  24  │ Enemy 5                   │
│ 0x176e  │  -   │  -   │ End marker                │
└────────────────────────────────────────────────────┘

Total: 168 bytes (7 × 24)
```

### 8.2 작업 버퍼 (0x168f - 0x16ae+)

```
Work Buffer @ 0x168f:
┌────────────────────────────────────────────────────┐
│ Offset | Address | Field                          │
├────────┼─────────┼────────────────────────────────┤
│ +0x00  │ 0x168f  │ state (AI jump table index)    │
│ +0x01  │ 0x1690  │ direction (2/4/6/8)            │
│ +0x02  │ 0x1691  │ type (collision index, 0=off)  │
│ +0x03  │ 0x1692  │ depth_offset                   │
│ +0x04  │ 0x1693  │ (unknown)                      │
│ +0x05  │ 0x1694  │ counter (timer/frame delay)    │
│ +0x06  │ 0x1695  │ sprite_ptr                     │
│ +0x08  │ 0x1697  │ x_pos (world space)            │
│ +0x0a  │ 0x1699  │ y_pos (world space)            │
│ +0x0c  │ 0x169b  │ dir_flag (-1/0/1)              │
│ +0x0e  │ 0x169d  │ (unknown)                      │
│ +0x10  │ 0x169f  │ render_list_ptr                │
│ +0x12  │ 0x16a1  │ link_ptr (child entity)        │
└────────────────────────────────────────────────────┘
```

### 8.3 점프 테이블 (0x16ef, 0xe3f)

```
AI Jump Table @ 0x16ef:
  Size: 256 entries × 2 bytes = 512 bytes
  Index: entity.state (0-255)

Collision Jump Table @ 0xe3f:
  Size: 256 entries × 2 bytes = 512 bytes
  Index: entity.type (0-255)

Total: 1024 bytes
```

### 8.4 플레이어 타이머 (0x4424 - 0x442e)

```
Player Timers @ 0x4424:
┌────────────────────────────────────────────────────┐
│ Address | Size | Name                             │
├─────────┼──────┼──────────────────────────────────┤
│ 0x4424  │  2   │ player1_timer_backup             │
│ 0x4426  │  2   │ player2_timer_backup             │
│ 0x4428  │  2   │ player1_timer (active)           │
│ 0x442a  │  2   │ player2_timer (active)           │
│ 0x442c  │  2   │ lives_remaining                  │
│ 0x442e  │  2   │ stage_timer                      │
└────────────────────────────────────────────────────┘

Total: 12 bytes
```

---

## 9. 함수 목록

### 9.1 핵심 함수

| Function | Address    | Size | Complexity | Description |
|----------|------------|------|------------|-------------|
| FUN_0360 | 1000:0360  | 62   | Medium     | Entity update loop (7 entities) |
| FUN_0412 | 1000:0412  | 9    | Low        | Copy entity → work buffer |
| FUN_16e0 | 1000:16e0  | 15   | Low        | AI state machine dispatcher |
| FUN_0e30 | 1000:0e30  | ?    | Low        | Collision dispatcher |
| FUN_3e6d | 1000:3e6d  | 258  | High       | Physics & animation update |
| FUN_0426 | 1000:0426  | 131  | High       | Sprite rendering prep |
| FUN_041b | 1000:041b  | 11   | Low        | Copy work buffer → entity |
| FUN_1668 | 1000:1668  | 44   | Medium     | Entity commit & link mgmt |

**총 코드 크기**: ~530 bytes

### 9.2 함수별 상세 설명

#### FUN_0360 - Entity Update Loop

**역할**: 7개 엔티티를 순회하며 업데이트 파이프라인 실행

**알고리즘**:
```python
for entity_addr in range(0x16c6, 0x176e, 24):  # 7 entities
    # 1. Copy to work buffer
    copy_to_work_buffer(entity_addr)

    # 2. Check if active
    if read_byte(entity_addr + 2) != 0:
        # 3. AI dispatch
        ai_dispatch()

        # 4. Collision dispatch
        collision_dispatch()

        # 5. Physics & animation
        physics_animation_update()

        # 6. Sprite prep
        sprite_rendering_prep()

        # 7. Copy back
        copy_from_work_buffer(entity_addr)

        # 8. Commit & link
        entity_commit_and_link()
```

**호출 빈도**: 매 프레임 (60 FPS)

---

#### FUN_0412 - Copy Entity to Work Buffer

**역할**: 엔티티 데이터를 작업 버퍼로 복사

**알고리즘**:
```python
function copy_to_work_buffer(entity_addr):
    src = entity_addr  # SI register
    dst = 0x168f       # Work buffer

    # Copy 12 words (24 bytes)
    for i in range(12):
        write_word(dst, read_word(src))
        dst += 2
        src += 2
```

**호출 빈도**: 엔티티당 1회/프레임 (7회/프레임)

---

#### FUN_16e0 - AI State Machine Dispatcher

**역할**: 상태 기반 AI 함수 호출

**알고리즘**:
```python
function ai_dispatch():
    state = read_byte(0x168f)
    func_ptr = read_word(0x16ef + state)
    call(func_ptr)
```

**호출 빈도**: 활성 엔티티당 1회/프레임 (~7회/프레임)

---

## 10. 구현 가이드

### 10.1 데이터 구조 정의

```python
class Entity:
    def __init__(self):
        self.state = 0          # AI state (0-255)
        self.direction = 0      # Direction (0x02/0x04/0x06/0x08)
        self.type = 0           # Entity type (0=inactive)
        self.depth_offset = 0
        self.field_04 = 0
        self.sprite_ptr = 0
        self.x_pos = 0
        self.y_pos = 0
        self.dir_flag = 0
        self.field_0e = 0
        self.render_data1 = 0
        self.link_ptr = -1      # -1 = no link
        self.field_14 = 0
        self.field_16 = 0


class EntitySystem:
    def __init__(self):
        # Entity slots
        self.entities = [Entity() for _ in range(7)]

        # Work buffer
        self.work_buffer = Entity()

        # AI jump table (256 function pointers)
        self.ai_jump_table = [None] * 256

        # Collision jump table (256 function pointers)
        self.collision_jump_table = [None] * 256

        # Initialize tables
        self.setup_ai_table()
        self.setup_collision_table()
```

### 10.2 엔티티 업데이트 루프

```python
function update_all_entities():
    for i in range(7):
        entity = entities[i]

        # Copy to work buffer
        work_buffer = copy.deepcopy(entity)

        # Check if active
        if entity.type != 0:
            # AI state machine
            ai_func = ai_jump_table[work_buffer.state]
            if ai_func:
                ai_func(work_buffer)

            # Collision handling
            collision_func = collision_jump_table[work_buffer.type]
            if collision_func:
                collision_func(work_buffer, i)

            # Physics & animation
            physics_animation_update(work_buffer)

            # Sprite rendering prep
            sprite_rendering_prep(work_buffer)

            # Copy back
            entity = copy.deepcopy(work_buffer)

            # Link management
            entity_commit_and_link(entity, i)
```

### 10.3 AI 점프 테이블 초기화

```python
function setup_ai_table():
    ai_jump_table[0x00] = ai_idle
    ai_jump_table[0x01] = ai_walk
    ai_jump_table[0x02] = ai_attack
    ai_jump_table[0x03] = ai_hit
    ai_jump_table[0x04] = ai_jump
    ai_jump_table[0x05] = ai_fall
    ai_jump_table[0x06] = ai_dead
    ai_jump_table[0x0a] = ai_player2_state
    ai_jump_table[0x10] = ai_enemy_idle
    ai_jump_table[0x11] = ai_enemy_walk
    ai_jump_table[0x12] = ai_enemy_attack
    # ... (fill all 256 states)

function setup_collision_table():
    collision_jump_table[0x00] = collision_inactive
    collision_jump_table[0x01] = collision_player
    collision_jump_table[0x02] = collision_enemy
    collision_jump_table[0x03] = collision_item
    collision_jump_table[0x04] = collision_projectile
    # ... (fill all 256 types)
```

---

## 11. 테스트 전략

### 11.1 Unit Tests

```python
# Test 1: Entity copy to/from work buffer
def test_entity_copy():
    entity = Entity()
    entity.state = 0x02
    entity.type = 0x01
    entity.x_pos = 100
    entity.y_pos = 50

    # Copy to work buffer
    work_buffer = copy.deepcopy(entity)

    # Modify work buffer
    work_buffer.x_pos = 110

    # Copy back
    entity = copy.deepcopy(work_buffer)

    assert entity.x_pos == 110
    assert entity.state == 0x02


# Test 2: AI dispatch
def test_ai_dispatch():
    global ai_called
    ai_called = False

    def test_ai_func(work_buffer):
        global ai_called
        ai_called = True

    ai_jump_table[0x05] = test_ai_func

    work_buffer.state = 0x05
    ai_dispatch()

    assert ai_called == True


# Test 3: Link system
def test_link_system():
    parent = entities[0]
    child = entities[2]

    # Create link
    parent.link_ptr = 2  # Index of child

    # Commit
    entity_commit_and_link(parent, 0)

    # Verify child initialized
    assert child.type == 0x04
    assert child.render_data1 == -1
    assert parent.link_ptr == -1  # Link cleared
```

### 11.2 Integration Tests

```python
# Test: Full entity update cycle
def test_entity_update_cycle():
    # Setup player entity
    player = entities[0]
    player.state = 0x00  # Idle
    player.type = 0x01   # Player type
    player.x_pos = 100
    player.y_pos = 100

    # Simulate attack input
    input_state = 0x10  # Attack button

    # Update
    update_all_entities()

    # Player should transition to attack state
    assert player.state == 0x02  # Attack state


# Test: Enemy AI behavior
def test_enemy_ai():
    # Setup player
    entities[0].type = 0x01
    entities[0].x_pos = 100
    entities[0].y_pos = 100

    # Setup enemy
    entities[2].state = 0x10  # Enemy idle
    entities[2].type = 0x02   # Enemy type
    entities[2].x_pos = 50
    entities[2].y_pos = 100

    # Update enemy AI
    update_all_entities()

    # Enemy should move toward player (right)
    assert entities[2].direction == 0x08  # Right
    assert entities[2].state == 0x11      # Enemy walk
```

---

## 12. 구현 체크리스트

### Phase 1: 데이터 구조
- [ ] Entity 구조체 정의 (24 bytes)
- [ ] 작업 버퍼 (24 bytes @ 0x168f)
- [ ] 엔티티 배열 (7 slots)
- [ ] AI 점프 테이블 (256 entries)
- [ ] Collision 점프 테이블 (256 entries)

### Phase 2: 업데이트 파이프라인
- [ ] Copy to work buffer (FUN_0412)
- [ ] Copy from work buffer (FUN_041b)
- [ ] Entity update loop (FUN_0360)
- [ ] Link management (FUN_1668)

### Phase 3: AI 시스템
- [ ] AI dispatcher (FUN_16e0)
- [ ] Player states (Idle, Walk, Attack, Hit, Jump, Dead)
- [ ] Enemy states (Idle, Chase, Attack)
- [ ] AI behavior functions

### Phase 4: 충돌 시스템
- [ ] Collision dispatcher (FUN_0e30)
- [ ] Player collision handler
- [ ] Enemy collision handler
- [ ] Projectile collision handler

### Phase 5: 물리 및 애니메이션
- [ ] Physics update (FUN_3e6d)
- [ ] Timer management
- [ ] State transitions
- [ ] Player respawn logic

### Phase 6: 테스트
- [ ] Unit tests (copy, dispatch, link)
- [ ] Integration tests (full cycle, AI)
- [ ] Visual tests (entity rendering)

---

## 13. 참고

### 13.1 관련 시스템 문서

- **03_ANIMATION.md**: 스프라이트 프레임 선택 및 방향 처리
- **04_PHYSICS_COLLISION.md**: 충돌 검출 알고리즘
- **05_INPUT_CAMERA.md**: 플레이어 입력 처리

### 13.2 원본 분석 문서

- `docs/function-analysis/ENTITY_SYSTEM_ANALYSIS.md`: 엔티티 시스템 초기 분석
- `docs/function-analysis/MAIN_LOOP_COMPLETE_ANALYSIS.md`: 메인 루프 및 업데이트 순서

### 13.3 성능 특성

**프레임당 오버헤드 (7개 엔티티)**:
```
- Copy to buffer:      9 bytes × 7 = ~63 cycles
- AI dispatch:         15 bytes × 7 = ~105 cycles
- Collision dispatch:  ~15 bytes × 7 = ~105 cycles
- Physics update:      258 bytes × 7 = ~1806 cycles
- Sprite prep:         131 bytes × 7 = ~917 cycles
- Copy from buffer:    11 bytes × 7 = ~77 cycles
────────────────────────────────────────────────────
Total: ~3073 cycles/frame

At 4.77 MHz: ~0.64 ms/frame
At 60 FPS budget (16.67 ms): ~3.8% of frame time
```

---

**문서 작성**: Claude Code
**분석 기반**: Phase 4 함수 디컴파일 (161 functions)
**구현 독립성**: Language-agnostic (모든 플랫폼 적용 가능)
