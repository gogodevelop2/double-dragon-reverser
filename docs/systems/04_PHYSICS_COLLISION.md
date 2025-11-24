# Physics & Collision System (물리 및 충돌 시스템)

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Complete

---

## 1. 개요

Double Dragon의 물리 및 충돌 시스템은 **발사체(projectiles)**와 **엔티티 간 상호작용**을 처리합니다. 엔티티 시스템과 유사한 작업 버퍼 패턴을 사용하며, 점프 테이블 기반 물리 디스패처로 타입별 물리 시뮬레이션을 수행합니다.

### 핵심 특징

1. **발사체 시스템**: 6개 슬롯, 18 bytes/projectile, 작업 버퍼 패턴
2. **물리 디스패처**: 점프 테이블 @ 0x2264, 타입별 물리 함수 (256 entries)
3. **3단계 충돌 검사**: 엔티티 유효성 → 타겟 검증 → 3-phase collision test
4. **충돌 응답**: 데미지 적용, 히트 이펙트 생성, 상태 전환
5. **물리 시뮬레이션**: 위치 업데이트, 중력 적용, 수명 관리
6. **히트박스 시스템**: 공격 판정, 무적 프레임, 히트스턴

### 시스템 연동

```
Main Loop (60 FPS)
    ↓
Entity Update (7 entities)
    └─> Collision Dispatcher (@ 0xe3f)
    ↓
Projectile Update (6 projectiles)
    ├─> Projectile → Work Buffer
    ├─> Physics Dispatcher (@ 0x2264)
    │   ├─> Position update (pos += vel)
    │   ├─> Gravity application
    │   └─> Collision check
    └─> Work Buffer → Projectile
    ↓
Collision Processing (FUN_2711)
    ├─> 3-stage collision test
    ├─> Damage application
    └─> Hit effect creation
```

---

## 2. 아키텍처

### 2.1 발사체 시스템 개요도

```
┌───────────────────────────────────────────────────────────┐
│  Projectile Array (6 slots × 18 bytes @ 0x3542-0x35ae)   │
│  [Proj0] [Proj1] [Proj2] [Proj3] [Proj4] [Proj5]         │
└────────────────────┬──────────────────────────────────────┘
                     ↓
        For each projectile (index 0-5):
                     ↓
        ┌────────────────────────────┐
        │ Active Check               │
        │ if (projectile[+2] != 0)   │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_2189                   │
        │ Copy to Work Buffer        │
        │ memcpy(0x3530, proj, 18)   │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_2255                   │
        │ Physics Dispatcher         │
        │ jump_table[type]()         │
        │ @ 0x2264                   │
        │                            │
        │ Physics Functions:         │
        │ - Update position          │
        │ - Apply gravity            │
        │ - Check collision          │
        │ - Decrement lifetime       │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ FUN_2192                   │
        │ Copy from Work Buffer      │
        │ memcpy(proj, 0x3530, 18)   │
        └────────────────────────────┘
```

### 2.2 충돌 검사 파이프라인

```
┌───────────────────────────────────────────────────────────┐
│  FUN_2711: Collision Processing Loop                      │
│  (Iterate through all entities 0x16c6-0x176e)             │
└────────────────────┬──────────────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Stage 1: Entity Validation │
        │ - Entity exists?           │
        │ - Not type 0x18 or 0x3c?   │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Stage 2: Target Validation │
        │ - Has valid target?        │
        │ - Target vulnerable?       │
        │   (flag bit 2 set)         │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Stage 3: 3-Phase Test      │
        │ - func_0x1280c() → bVar5   │
        │ - func_0x12821() → bVar5   │
        │ - func_0x127f7() → bVar5   │
        │ All must return true       │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │ Collision Response         │
        │ - func_0x127eb()           │
        │ - Apply damage             │
        │ - Create hit effect        │
        │ - State transition         │
        └────────────────────────────┘
```

---

## 3. 발사체 데이터 구조

### 3.1 Projectile 구조체 (18 bytes)

```c
struct Projectile {
    uint16_t pos_x;          // +0x00: X position (world space)
    uint16_t active_flag;    // +0x02: Active flag (0=inactive, !=0=active)
    uint16_t pos_y;          // +0x04: Y position (world space)
    uint16_t vel_x;          // +0x06: X velocity (signed)
    uint16_t vel_y;          // +0x08: Y velocity (signed)
    uint16_t type;           // +0x0a: Projectile type (physics jump table index)
    uint16_t sprite_id;      // +0x0c: Sprite ID for rendering
    uint16_t owner;          // +0x0e: Owner entity index (0-6)
    uint16_t damage;         // +0x10: Damage value
};  // Total: 18 bytes (0x12)
```

**필드 설명**:
- `pos_x`, `pos_y`: 월드 좌표계 위치
- `active_flag`: 0이 아니면 활성화 (업데이트 대상)
- `vel_x`, `vel_y`: 프레임당 이동 속도 (signed, 음수 = 역방향)
- `type`: 물리 디스패처 인덱스 (0x00-0xFF)
- `owner`: 발사한 엔티티 (피아 식별용)
- `damage`: 충돌 시 적용할 데미지

### 3.2 발사체 슬롯 배치

```
Projectile Array @ 0x3542 - 0x35ae:

Slot 0: 0x3542 (18 bytes) → Projectile 0
Slot 1: 0x3554 (18 bytes) → Projectile 1
Slot 2: 0x3566 (18 bytes) → Projectile 2
Slot 3: 0x3578 (18 bytes) → Projectile 3
Slot 4: 0x358a (18 bytes) → Projectile 4
Slot 5: 0x359c (18 bytes) → Projectile 5

Total: 6 slots × 18 bytes = 108 bytes
End marker: 0x35ae
```

### 3.3 발사체 작업 버퍼 (@ 0x3530)

```
Work Buffer @ 0x3530 (18 bytes):
┌────────────────────────────────────────────────────┐
│ Offset | Address | Field                          │
├────────┼─────────┼────────────────────────────────┤
│ +0x00  │ 0x3530  │ pos_x                          │
│ +0x02  │ 0x3532  │ active_flag                    │
│ +0x04  │ 0x3534  │ pos_y (or sprite_ptr)          │
│ +0x06  │ 0x3536  │ vel_x                          │
│ +0x08  │ 0x3538  │ vel_y (or adjusted value)      │
│ +0x0a  │ 0x353a  │ type (physics index)           │
│ +0x0c  │ 0x353c  │ sprite_id                      │
│ +0x0e  │ 0x353e  │ owner                          │
│ +0x10  │ 0x3540  │ damage                         │
└────────────────────────────────────────────────────┘

Note: Some fields may be reused for different purposes
depending on projectile type.
```

---

## 4. 물리 시뮬레이션

### 4.1 물리 디스패처 (@ 0x2264)

```python
function physics_dispatch():
    """
    Physics dispatcher using jump table.
    O(1) dispatch based on projectile type.
    """
    # Read type from work buffer
    projectile_type = read_byte(0x3530)  # First byte of work buffer

    # Calculate jump table address
    table_offset = 0x2264 + projectile_type
    func_ptr = read_word(table_offset)

    # Call physics function
    call(func_ptr)
```

#### 물리 점프 테이블 구조

```
Physics Jump Table @ 0x2264:
┌────────┬──────────────┬──────────────────────────┐
│ Type   │ Address      │ Physics Function         │
├────────┼──────────────┼──────────────────────────┤
│ 0x00   │ 0x2264[0x00] │ Physics_Hitbox           │
│ 0x01   │ 0x2264[0x01] │ Physics_ThrownWeapon     │
│ 0x02   │ 0x2264[0x02] │ Physics_Arrow            │
│ 0x03   │ 0x2264[0x03] │ Physics_Grenade          │
│ 0x04   │ 0x2264[0x04] │ Physics_Special          │
│  ...   │     ...      │          ...             │
│ 0xFF   │ 0x2264[0xFF] │ Physics_Type_255         │
└────────┴──────────────┴──────────────────────────┘

Table size: 256 entries × 2 bytes = 512 bytes
```

### 4.2 물리 함수 예시

```python
# Type 0x00: Hitbox (punch/kick collision box)
function physics_hitbox():
    """
    Hitbox stays with owner entity, no movement.
    Decrements lifetime and deactivates when expired.
    """
    lifetime = read_byte(0x3530 + 0x0a)  # Reuse type field as lifetime

    if lifetime > 0:
        write_byte(0x3530 + 0x0a, lifetime - 1)
    else:
        # Deactivate
        write_word(0x3532, 0)  # active_flag = 0


# Type 0x01: Thrown weapon (straight line, gravity)
function physics_thrown_weapon():
    """
    Linear projectile with gravity.
    Updates position, applies gravity, checks bounds.
    """
    # Read current state
    pos_x = read_word(0x3530)
    pos_y = read_word(0x3534)
    vel_x = read_signed_word(0x3536)
    vel_y = read_signed_word(0x3538)

    # Apply velocity
    pos_x += vel_x
    pos_y += vel_y

    # Apply gravity
    vel_y += GRAVITY  # e.g., +1 or +2 per frame

    # Update work buffer
    write_word(0x3530, pos_x)
    write_word(0x3534, pos_y)
    write_word(0x3538, vel_y)

    # Check bounds (deactivate if off-screen)
    if pos_y > MAX_Y or pos_x < MIN_X or pos_x > MAX_X:
        write_word(0x3532, 0)  # active_flag = 0


# Type 0x02: Arrow (straight line, no gravity)
function physics_arrow():
    """
    Linear projectile, no gravity.
    Fast, straight trajectory.
    """
    pos_x = read_word(0x3530)
    pos_y = read_word(0x3534)
    vel_x = read_signed_word(0x3536)
    vel_y = read_signed_word(0x3538)

    # Apply velocity (no gravity)
    pos_x += vel_x
    pos_y += vel_y

    write_word(0x3530, pos_x)
    write_word(0x3534, pos_y)

    # Check bounds
    if out_of_bounds(pos_x, pos_y):
        write_word(0x3532, 0)  # Deactivate


# Type 0x03: Grenade (parabolic arc)
function physics_grenade():
    """
    Parabolic trajectory with explosion on impact.
    """
    pos_x = read_word(0x3530)
    pos_y = read_word(0x3534)
    vel_x = read_signed_word(0x3536)
    vel_y = read_signed_word(0x3538)

    # Apply velocity
    pos_x += vel_x
    pos_y += vel_y

    # Apply gravity (stronger than thrown weapon)
    vel_y += GRENADE_GRAVITY  # e.g., +3

    write_word(0x3530, pos_x)
    write_word(0x3534, pos_y)
    write_word(0x3538, vel_y)

    # Check ground collision
    ground_y = get_ground_y(pos_x)
    if pos_y >= ground_y:
        # Explode
        create_explosion_effect(pos_x, pos_y)
        write_word(0x3532, 0)  # Deactivate


# Type 0x04: Special attack (custom behavior)
function physics_special():
    """
    Special projectile with unique behavior.
    Example: Homing missile, boomerang, etc.
    """
    # Custom logic based on game design
    # ...
```

### 4.3 중력 및 물리 상수

```python
# Physics constants (estimated values)
GRAVITY = 2              # Pixels/frame² for normal projectiles
GRENADE_GRAVITY = 3      # Stronger gravity for grenades
TERMINAL_VELOCITY = 20   # Max falling speed

FRICTION_AIR = 0.98      # Air resistance (velocity *= 0.98)
FRICTION_GROUND = 0.8    # Ground friction

# Bounds
MIN_X = 0
MAX_X = 2560  # Stage width
MIN_Y = 0
MAX_Y = 200   # Ground level
```

---

## 5. 충돌 검출

### 5.1 3단계 충돌 검사

```python
function collision_detection():
    """
    Three-stage collision check for entities.
    All three tests must pass for collision to be confirmed.
    """
    # Iterate through all entities
    for entity_addr in range(0x16c6, 0x176e, 24):
        # Stage 1: Entity validation
        if not validate_entity(entity_addr):
            continue

        # Stage 2: Target validation
        if not validate_target(entity_addr):
            continue

        # Stage 3: 3-phase collision test
        collision_result = False

        # Phase 1
        collision_result = collision_test_phase1()
        if not collision_result:
            continue

        # Phase 2
        collision_result = collision_test_phase2()
        if not collision_result:
            continue

        # Phase 3
        collision_result = collision_test_phase3()
        if not collision_result:
            continue

        # All tests passed → Collision confirmed
        handle_collision(entity_addr)


function validate_entity(entity_addr):
    """
    Stage 1: Check if entity is valid for collision.
    """
    # Check if entity exists
    if read_byte(entity_addr) == -1:
        return False

    # Exclude specific types
    entity_type = read_byte(entity_addr + 2)
    if entity_type == 0x18 or entity_type == 0x3c:
        return False  # Types 24 and 60 are excluded

    return True


function validate_target(entity_addr):
    """
    Stage 2: Check if entity has valid target and target is vulnerable.
    """
    # Get target pointer
    target_ptr = read_word(entity_addr + 6)  # +6: target field

    if target_ptr == -1:
        return False  # No target

    # Check vulnerable flag (bit 2 of target's field +6)
    target_flags = read_byte(target_ptr + 6)
    if (target_flags & 0x02) == 0:
        return False  # Not vulnerable

    return True


function collision_test_phase1():
    """
    Phase 1: Preliminary collision check.
    Details unknown (black box function).
    """
    # func_0x1280c()
    # Likely: Bounding box overlap test
    return True  # Placeholder


function collision_test_phase2():
    """
    Phase 2: Secondary collision check.
    Details unknown (black box function).
    """
    # func_0x12821()
    # Likely: Distance check or precise hitbox test
    return True  # Placeholder


function collision_test_phase3():
    """
    Phase 3: Final collision check.
    Details unknown (black box function).
    """
    # func_0x127f7()
    # Likely: Special conditions (invincibility frames, etc.)
    return True  # Placeholder
```

### 5.2 히트박스 충돌 (추정 구현)

```python
function check_hitbox_collision(entity_a, entity_b):
    """
    Bounding box collision detection (AABB).
    """
    # Entity A bounding box
    a_left = entity_a.x_pos
    a_right = entity_a.x_pos + entity_a.width
    a_top = entity_a.y_pos
    a_bottom = entity_a.y_pos + entity_a.height

    # Entity B bounding box
    b_left = entity_b.x_pos
    b_right = entity_b.x_pos + entity_b.width
    b_top = entity_b.y_pos
    b_bottom = entity_b.y_pos + entity_b.height

    # AABB overlap test
    if a_right < b_left or a_left > b_right:
        return False  # No X overlap

    if a_bottom < b_top or a_top > b_bottom:
        return False  # No Y overlap

    return True  # Collision


function get_distance(entity_a, entity_b):
    """
    Calculate Manhattan distance between two entities.
    """
    dx = abs(entity_a.x_pos - entity_b.x_pos)
    dy = abs(entity_a.y_pos - entity_b.y_pos)
    return dx + dy
```

---

## 6. 충돌 응답

### 6.1 충돌 처리 (FUN_2711)

```python
function handle_collision(entity_addr):
    """
    Process collision and apply effects.
    """
    projectile_type = read_byte(0x3530)  # Projectile work buffer
    entity_type = read_byte(entity_addr + 2)

    # Call collision response function
    collision_response()  # func_0x127eb

    # Special case: Projectile type 4 vs Entity type 6
    if projectile_type == 0x04 and entity_type == 0x06:
        # Special interaction
        special_interaction()
        check_value = read_word(0x353a) + calculate_y_position()

        if check_value == 0:
            # Adjust velocity
            vel_x = read_word(0x3536)
            write_word(0x3536, vel_x + calculate_y_position() * 4)
            trigger_special_event()
            return  # Skip normal damage

    # Apply damage to entity
    apply_damage_to_entity(entity_addr)

    # Create hit effect
    create_hit_effect(entity_addr)


function apply_damage_to_entity(entity_addr):
    """
    Apply damage and update entity state.
    """
    damage = read_word(0x3540)  # Projectile damage

    # Reduce HP (assumed field +5)
    hp = read_byte(entity_addr + 5)
    hp -= damage
    write_byte(entity_addr + 5, hp)

    # Check death
    if hp <= 0:
        # Transition to dead state
        write_byte(entity_addr, 0x06)  # state = Dead


function create_hit_effect(entity_addr):
    """
    Create visual hit effect (spark, blood, etc.).
    """
    # Copy entity to work buffer
    copy_to_work_buffer(entity_addr)

    # Set effect type
    write_byte(0x1691, 0x32)  # type = 50 (effect)

    # Adjust position
    depth_offset = read_byte(0x1692)
    write_byte(0x1692, depth_offset + 3)  # +3 to depth

    y_pos = read_word(0x1699)
    write_word(0x1699, y_pos - 3)  # -3 to Y position

    # Set effect sprite
    write_word(0x1695, 0xFFFF)  # sprite_ptr = -1 (reset)
    write_word(0x169d, 0xFFFE)  # field = -2

    # Copy projectile velocity to effect
    projectile_vel_y = read_word(0x353a)
    write_word(0x169b, projectile_vel_y)

    # Prepare sprite
    sprite_rendering_prep()  # FUN_0426
    advance_animation_frame()  # FUN_04e1

    # Decrement effect counter
    counter = read_byte(0x1694)
    counter -= 2
    if counter < 0:
        counter = 0
    write_byte(0x1694, counter)

    # Commit effect entity
    copy_from_work_buffer(entity_addr)
    entity_commit_and_link()  # FUN_1668
```

### 6.2 데미지 계산

```python
function calculate_damage(attacker, target, base_damage):
    """
    Calculate final damage with modifiers.
    """
    damage = base_damage

    # Attacker strength modifier (hypothetical)
    strength = get_entity_strength(attacker)
    damage = damage * strength / 10

    # Target defense modifier
    defense = get_entity_defense(target)
    damage = damage - defense

    # Minimum damage
    if damage < 1:
        damage = 1

    # Critical hit chance (5%)
    lcg_random()
    if (read_word(0x16b2) & 0x1F) == 0:
        damage *= 2  # Double damage

    return damage
```

---

## 7. 발사체 생성 및 관리

### 7.1 발사체 생성

```python
function create_projectile(owner, type, pos_x, pos_y, vel_x, vel_y, damage):
    """
    Create a new projectile in the first available slot.
    """
    # Find free projectile slot
    for i in range(6):
        projectile_addr = 0x3542 + (i * 18)
        active_flag = read_word(projectile_addr + 2)

        if active_flag == 0:  # Inactive slot
            # Initialize projectile
            write_word(projectile_addr + 0x00, pos_x)
            write_word(projectile_addr + 0x02, 1)  # active_flag = 1
            write_word(projectile_addr + 0x04, pos_y)
            write_word(projectile_addr + 0x06, vel_x)
            write_word(projectile_addr + 0x08, vel_y)
            write_byte(projectile_addr + 0x0a, type)
            write_word(projectile_addr + 0x0c, get_projectile_sprite(type))
            write_word(projectile_addr + 0x0e, owner)
            write_word(projectile_addr + 0x10, damage)
            return True  # Success

    return False  # No free slots


# Example: Player throws weapon
function player_throw_weapon(player):
    # Calculate throw position (in front of player)
    throw_x = player.x_pos + (player.direction == RIGHT ? 10 : -10)
    throw_y = player.y_pos

    # Calculate velocity based on direction
    vel_x = player.direction == RIGHT ? 5 : -5
    vel_y = -3  # Initial upward velocity

    # Create projectile
    create_projectile(
        owner=player.index,
        type=0x01,  # Thrown weapon
        pos_x=throw_x,
        pos_y=throw_y,
        vel_x=vel_x,
        vel_y=vel_y,
        damage=10
    )
```

### 7.2 발사체 업데이트 루프

```python
function update_all_projectiles():
    """
    Update all active projectiles (FUN_20fb).
    """
    for i in range(6):
        projectile_addr = 0x3542 + (i * 18)

        # Check if active
        active_flag = read_word(projectile_addr + 2)
        if active_flag != 0:
            # Copy to work buffer
            copy_projectile_to_buffer(projectile_addr)  # FUN_2189

            # Physics update
            physics_dispatch()  # FUN_2255

            # Copy back
            copy_buffer_to_projectile(projectile_addr)  # FUN_2192


function copy_projectile_to_buffer(projectile_addr):
    """
    Copy projectile data to work buffer (FUN_2189).
    """
    src = projectile_addr
    dst = 0x3530  # Work buffer

    # Copy 9 words (18 bytes)
    for i in range(9):
        write_word(dst, read_word(src))
        dst += 2
        src += 2


function copy_buffer_to_projectile(projectile_addr):
    """
    Copy work buffer back to projectile (FUN_2192).
    """
    src = 0x3530  # Work buffer
    dst = projectile_addr

    # Copy 9 words (18 bytes)
    for i in range(9):
        write_word(dst, read_word(src))
        dst += 2
        src += 2
```

---

## 8. 메모리 레이아웃

### 8.1 발사체 배열 (0x3542 - 0x35ae)

```
Projectile Array @ 0x3542:
┌────────────────────────────────────────────────────┐
│ Address | Slot | Size | Projectile                │
├─────────┼──────┼──────┼───────────────────────────┤
│ 0x3542  │  0   │  18  │ Projectile 0              │
│ 0x3554  │  1   │  18  │ Projectile 1              │
│ 0x3566  │  2   │  18  │ Projectile 2              │
│ 0x3578  │  3   │  18  │ Projectile 3              │
│ 0x358a  │  4   │  18  │ Projectile 4              │
│ 0x359c  │  5   │  18  │ Projectile 5              │
│ 0x35ae  │  -   │  -   │ End marker                │
└────────────────────────────────────────────────────┘

Total: 108 bytes (6 × 18)
```

### 8.2 발사체 작업 버퍼 (0x3530)

```
Work Buffer @ 0x3530 (18 bytes):
┌────────────────────────────────────────────────────┐
│ Offset | Address | Field                          │
├────────┼─────────┼────────────────────────────────┤
│ +0x00  │ 0x3530  │ pos_x (or type for dispatcher) │
│ +0x02  │ 0x3532  │ active_flag                    │
│ +0x04  │ 0x3534  │ pos_y (sprite_ptr in col code) │
│ +0x06  │ 0x3536  │ vel_x                          │
│ +0x08  │ 0x3538  │ vel_y                          │
│ +0x0a  │ 0x353a  │ type / lifetime                │
│ +0x0c  │ 0x353c  │ sprite_id                      │
│ +0x0e  │ 0x353e  │ owner                          │
│ +0x10  │ 0x3540  │ damage                         │
└────────────────────────────────────────────────────┘
```

### 8.3 물리 점프 테이블 (0x2264)

```
Physics Jump Table @ 0x2264:
  Size: 256 entries × 2 bytes = 512 bytes
  Index: projectile.type (0-255)

Total: 512 bytes
```

---

## 9. 함수 목록

### 9.1 핵심 함수

| Function | Address    | Size | Complexity | Description |
|----------|------------|------|------------|-------------|
| FUN_20fb | 1000:20fb  | 32   | Low        | Projectile update loop (6 slots) |
| FUN_2189 | 1000:2189  | 9    | Low        | Copy projectile → work buffer |
| FUN_2255 | 1000:2255  | 15   | Low        | Physics dispatcher |
| FUN_2192 | 1000:2192  | 11   | Low        | Copy work buffer → projectile |
| FUN_2711 | 1000:2711  | ?    | High       | Collision processing loop |

**총 코드 크기**: ~67 bytes (projectile core) + collision code

---

## 10. 구현 가이드

### 10.1 데이터 구조 정의

```python
class Projectile:
    def __init__(self):
        self.pos_x = 0
        self.active_flag = 0
        self.pos_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.type = 0
        self.sprite_id = 0
        self.owner = 0
        self.damage = 0


class PhysicsSystem:
    def __init__(self):
        # Projectile slots
        self.projectiles = [Projectile() for _ in range(6)]

        # Work buffer
        self.work_buffer = Projectile()

        # Physics jump table (256 function pointers)
        self.physics_jump_table = [None] * 256

        # Initialize tables
        self.setup_physics_table()
```

### 10.2 물리 시스템 초기화

```python
function setup_physics_table():
    physics_jump_table[0x00] = physics_hitbox
    physics_jump_table[0x01] = physics_thrown_weapon
    physics_jump_table[0x02] = physics_arrow
    physics_jump_table[0x03] = physics_grenade
    physics_jump_table[0x04] = physics_special
    # ... (fill all 256 types)
```

### 10.3 테스트

```python
# Test 1: Projectile creation
def test_create_projectile():
    success = create_projectile(
        owner=0, type=0x01, pos_x=100, pos_y=100,
        vel_x=5, vel_y=-3, damage=10
    )
    assert success == True
    assert projectiles[0].active_flag != 0
    assert projectiles[0].pos_x == 100


# Test 2: Physics update
def test_physics_update():
    projectiles[0].pos_x = 100
    projectiles[0].vel_x = 5
    projectiles[0].type = 0x02  # Arrow

    update_all_projectiles()

    assert projectiles[0].pos_x == 105  # pos += vel


# Test 3: Collision detection
def test_collision():
    player.x_pos = 100
    player.y_pos = 100
    enemy.x_pos = 105
    enemy.y_pos = 105

    collision = check_hitbox_collision(player, enemy)
    assert collision == True
```

---

## 11. 구현 체크리스트

### Phase 1: 발사체 시스템
- [ ] Projectile 구조체 (18 bytes)
- [ ] 발사체 배열 (6 slots)
- [ ] 작업 버퍼 (18 bytes)
- [ ] Copy functions (to/from buffer)

### Phase 2: 물리 시뮬레이션
- [ ] Physics dispatcher
- [ ] Physics jump table (256 entries)
- [ ] Type 0x00: Hitbox
- [ ] Type 0x01: Thrown weapon
- [ ] Type 0x02: Arrow
- [ ] Type 0x03: Grenade

### Phase 3: 충돌 검출
- [ ] 3-stage validation
- [ ] AABB collision test
- [ ] Distance check
- [ ] Invincibility frames

### Phase 4: 충돌 응답
- [ ] Damage application
- [ ] Hit effect creation
- [ ] State transitions
- [ ] Special interactions

### Phase 5: 테스트
- [ ] Unit tests (create, physics, collision)
- [ ] Integration tests (full cycle)
- [ ] Visual tests (effects)

---

## 12. 참고

### 12.1 관련 시스템 문서

- **02_ENTITY_AI.md**: 엔티티 시스템 및 작업 버퍼 패턴
- **03_ANIMATION.md**: 스프라이트 렌더링
- **06_STAGE_LIFECYCLE.md**: 히트 이펙트 및 상태 관리

### 12.2 원본 분석 문서

- `docs/function-analysis/ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md`: 발사체 시스템 초기 분석
- `docs/function-analysis/INPUT_CAMERA_PHYSICS_ANALYSIS.md`: 물리 디스패처 발견

### 12.3 성능 특성

**프레임당 오버헤드 (6개 발사체)**:
```
- Copy to buffer:      9 bytes × 6 = ~54 cycles
- Physics dispatch:    15 bytes × 6 = ~90 cycles
- Physics functions:   ~200 bytes × 6 = ~1200 cycles
- Copy from buffer:    11 bytes × 6 = ~66 cycles
────────────────────────────────────────────────────
Total: ~1410 cycles/frame

At 4.77 MHz: ~0.30 ms/frame
At 60 FPS budget (16.67 ms): ~1.8% of frame time
```

---

**문서 작성**: Claude Code
**분석 기반**: Phase 4 함수 디컴파일 (161 functions)
**구현 독립성**: Language-agnostic (모든 플랫폼 적용 가능)
