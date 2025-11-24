# 하드웨어 I/O 시스템 (Hardware I/O System)

**목적**: Double Dragon의 저수준 하드웨어 접근 및 DOS 시스템 호출 인터페이스를 언어 중립적으로 설명합니다.

**관련 함수**: 15개
**의존성**: 독립적 (다른 시스템의 기반)
**복잡도**: ⭐⭐ (개념적으로 단순, 구현 시 주의 필요)

---

## 📋 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [타이머 시스템](#3-타이머-시스템)
4. [DOS 시스템 호출](#4-dos-시스템-호출)
5. [조이스틱 입력](#5-조이스틱-입력)
6. [메모리 레이아웃](#6-메모리-레이아웃)
7. [함수 목록](#7-함수-목록)
8. [구현 가이드](#8-구현-가이드)
9. [테스트 전략](#9-테스트-전략)

---

## 1. 개요

### 1.1 역할

하드웨어 I/O 시스템은 게임과 하드웨어 사이의 **추상화 계층**을 제공:

1. **PIT 타이머 제어**: 게임 타이밍 vs DOS 호환 모드 전환
2. **DOS 시스템 호출**: INT 21h 래퍼 + 에러 처리
3. **조이스틱 입력**: Port 0x201 폴링
4. **VSync 동기화**: Port 0x3DA CGA 상태 레지스터

### 1.2 주요 기능

**타이머 관리**:
- Mode 0: 291 Hz (게임 플레이, 빠름)
- Mode 1: 18.2 Hz (DOS I/O, 느림, 안전)
- 자동 전환 및 복원

**에러 처리**:
- Carry Flag 기반 재시도
- 무한 루프 (성공할 때까지)
- 타이머 상태 복원

**입력 처리**:
- 조이스틱 (2개, 2축 + 2버튼 각)
- 키보드 (스캔코드)

### 1.3 설계 철학

```
"하드웨어는 실패할 수 있다. 재시도하라."

- 모든 DOS 호출은 재시도 로직 포함
- 타이머 모드는 작업에 따라 자동 전환
- 조이스틱 읽기는 타임아웃 보호
```

---

## 2. 아키텍처

### 2.1 시스템 다이어그램

```
┌─────────────────────────────────────────────────┐
│         Application Layer                        │
│  (게임 로직, 엔티티, 렌더링)                      │
└───────────────────┬─────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│      System Services Layer                       │
│  • FUN_1df2, 1dfc, 1dff, 1e02 (서비스 래퍼)      │
│  • FUN_1e8a, 1ea2 (고수준 파일 I/O)              │
└───────────────────┬─────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│    Hardware Abstraction Layer                    │
│  • FUN_1e26, 1e60, 1e7f (DOS INT 21h 래퍼)      │
│  • FUN_1c0c, 1c1e, 1c43 (타이머 PIT)            │
│  • FUN_1eb8, 1faa, 1ffd (조이스틱)              │
└───────────────────┬─────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          Hardware Layer                          │
│  • DOS (INT 21h) - 파일, 메모리 관리             │
│  • PIT (Port 0x43, 0x40) - 타이머                │
│  • Game Port (Port 0x201) - 조이스틱             │
│  • CGA (Port 0x3DA) - VSync                      │
└─────────────────────────────────────────────────┘
```

### 2.2 제어 흐름

```
게임 초기화
  ↓
Timer Mode 0 (291 Hz)  ← 게임 플레이 모드
  ↓
메인 게임 루프
  ├─ 입력 읽기 (조이스틱/키보드)
  ├─ 게임 로직
  └─ 렌더링 + VSync
  ↓
DOS 호출 필요 시:
  1. Timer Mode 1 (18.2 Hz)  ← DOS 호환 모드
  2. DOS INT 21h 호출
  3. 에러 시 재시도
  4. Timer Mode 0 복원
  ↓
계속 루프
```

### 2.3 에러 처리 흐름

```
DOS 작업 시도
  ↓
Success? (CF = 0)
  ├─ YES → 반환
  └─ NO  → 에러 처리
             ↓
         타이머 복원 (FUN_1c43)
             ↓
         INT 0 트리거 (디버그?)
             ↓
         DOS 재시도
             ↓
         Success?
           ├─ YES → 반환
           └─ NO  → 무한 반복
```

---

## 3. 타이머 시스템

### 3.1 PIT (Programmable Interval Timer) 개요

**하드웨어**: Intel 8253/8254 PIT
**포트**:
- `0x43`: 제어 포트 (명령)
- `0x40`: Channel 0 데이터 (시스템 타이머)
- `0x41`: Channel 1 데이터 (DRAM 리프레시)
- `0x42`: Channel 2 데이터 (스피커)

**기준 주파수**: 1.193182 MHz (1193182 Hz)

### 3.2 타이머 Mode 0 (게임 모드)

**설정**:
```
Port 0x43 = 0x36 (00110110b)
  Bits 7-6: 00 = Channel 0
  Bits 5-4: 11 = Access mode (LSB then MSB)
  Bits 3-1: 011 = Mode 3 (Square Wave)
  Bit 0:    0 = Binary counter

Port 0x40 = 0x00 (LSB)
Port 0x40 = 0x10 (MSB)
  → Counter = 0x1000 = 4096
```

**계산**:
```
Output Frequency = 1,193,182 Hz / 4,096
                 = 291.4 Hz
Period = 3.43 ms
```

**특성**:
- **빠른 인터럽트**: 초당 291회
- **정밀 타이밍**: 게임 프레임 제어
- **비표준**: DOS와 호환성 문제 가능

**의사코드**:
```python
function timer_mode_0():
    """
    게임 플레이용 고속 타이머 설정

    Returns:
        0x10 (카운터 MSB)
    """
    # 메모리 플래그 설정
    timer_mode_flag = 0  # @ 0x318c

    # PIT 명령
    out_byte(0x43, 0x36)  # Ch0, LSB+MSB, Mode 3, Binary

    # 카운터 설정 (4096)
    out_byte(0x40, 0x00)  # LSB
    out_byte(0x40, 0x10)  # MSB

    return 0x10
```

### 3.3 타이머 Mode 1 (DOS 모드)

**설정**:
```
Port 0x43 = 0x36 (동일)
Port 0x40 = 0x00 (LSB)
Port 0x40 = 0x00 (MSB)
  → Counter = 0x0000 = 65536 (overflow)
```

**계산**:
```
Output Frequency = 1,193,182 Hz / 65,536
                 = 18.2 Hz
Period = 54.9 ms
```

**특성**:
- **표준 DOS 타이머**: 18.2 Hz (INT 08h)
- **느린 인터럽트**: 초당 18.2회
- **안전 모드**: DOS 함수 호출 시 필수

**의사코드**:
```python
function timer_mode_1():
    """
    DOS 호환 표준 타이머 설정

    Returns:
        0x00 (카운터 MSB)
    """
    # 메모리 플래그 설정
    timer_mode_flag = 1  # @ 0x318c

    # PIT 명령
    out_byte(0x43, 0x36)

    # 카운터 설정 (65536)
    out_byte(0x40, 0x00)  # LSB
    out_byte(0x40, 0x00)  # MSB (0 = 65536)

    return 0x00
```

### 3.4 타이머 복원

**목적**: 에러 발생 시 안전한 상태로 복구

**조건**:
```python
if memory[0x24] == 0x1db5:  # 매직 넘버 체크
    # 타이머 상태 복원
    restore_state()
```

**의사코드**:
```python
function restore_timer():
    """
    타이머 상태를 안전 모드로 복원
    """
    # 매직 넘버 확인
    if read_word(0x24) == 0x1db5:
        # 백업된 상태 복원
        write_word(0x24, read_word(0x3180))
        write_word(0x26, read_word(0x3182))

        # Timer Mode 1로 전환 (안전 모드)
        timer_mode_1()

        # 추가 상태 복원
        write_word(0x20, read_word(0x3184))
        write_word(0x22, read_word(0x3186))
```

**사용 시나리오**:
```
게임 중 → Timer Mode 0 (291 Hz)
  ↓
DOS 파일 읽기 필요
  ↓
Timer Mode 1 (18.2 Hz) → 안전 모드
  ↓
DOS INT 21h 호출
  ↓
에러 발생! (Carry Flag = 1)
  ↓
restore_timer() 호출
  ↓
Timer Mode 1 유지 (이미 안전 모드)
  ↓
재시도
```

### 3.5 Mode 0 vs Mode 1 비교

| 속성 | Mode 0 (게임) | Mode 1 (DOS) |
|------|--------------|--------------|
| **주파수** | 291.4 Hz | 18.2 Hz |
| **주기** | 3.43 ms | 54.9 ms |
| **카운터** | 4096 | 65536 |
| **용도** | 게임 타이밍 | DOS 호환 |
| **인터럽트** | 초당 291회 | 초당 18.2회 |
| **안정성** | 불안정 (DOS) | 안정 |
| **플래그** | 0x318c = 0 | 0x318c = 1 |

**전환 패턴**:
```
게임 시작 → Mode 0
  ↓
DOS 호출 전 → Mode 1
  ↓
DOS 호출 후 → Mode 0
  ↓
게임 종료 → Mode 1 (시스템 복구)
```

---

## 4. DOS 시스템 호출

### 4.1 DOS INT 21h 개요

**인터페이스**: BIOS Interrupt 21h (DOS Services)
**사용 예시**:
- 파일 열기/닫기 (AH=3Dh, 3Eh)
- 파일 읽기/쓰기 (AH=3Fh, 40h)
- 메모리 할당 (AH=48h)
- 프로그램 종료 (AH=4Ch)

**Carry Flag**:
```
CF = 0: 성공
CF = 1: 실패 (AX = 에러 코드)
```

### 4.2 재시도 메커니즘

Double Dragon은 **3가지 재시도 전략**을 사용:

#### 레벨 1: Minimal Retry (FUN_1e7f)

**전략**: 빠른 성공 경로 + 전체 재시도

```python
function dos_call_minimal_retry():
    """
    1차 시도 → 성공 시 즉시 반환
    실패 시 전체 재시도 루프
    """
    # 1차 시도
    dos_int_21h()
    if carry_flag == 0:
        return  # 성공

    # 실패 → 전체 재시도
    while True:
        # 내부 루프
        while True:
            restore_timer()
            trigger_int_0()     # 디버그 트리거?
            dos_int_21h()
            dos_int_21h()
            if carry_flag == 0:
                break

        # 최종 확인
        dos_int_21h()
        if carry_flag == 0:
            break
```

**특징**:
- **최적화**: 대부분 1차 시도 성공
- **복잡도**: Low
- **사용처**: 일반적인 DOS 호출

---

#### 레벨 2: Simple Retry (FUN_1e60)

**전략**: 단일 루프 재시도

```python
function dos_call_simple_retry():
    """
    2단계 DOS 호출 + 단일 재시도 루프
    """
    while True:
        # 1차 DOS 호출
        dos_int_21h()
        if carry_flag == 0:
            # 2차 DOS 호출
            dos_int_21h()
            if carry_flag == 0:
                return  # 성공

        # 에러 처리
        restore_timer()
        trigger_int_0()
        dos_int_21h()  # 재시도
```

**특징**:
- **2단계 호출**: 초기화 + 실제 작업
- **단일 루프**: 간단한 구조
- **사용처**: 파일 닫기, flush

---

#### 레벨 3: Full Retry (FUN_1e26)

**전략**: 중첩 루프 + 결과 저장

```python
function dos_call_full_retry():
    """
    2단계 DOS 호출 + 중첩 재시도 + 결과 저장
    """
    # 1차 시도
    dos_int_21h()
    if carry_flag == 0:
        dos_int_21h()
        if carry_flag == 0:
            result = get_ax_register()
            write_word(0x3215, result)  # 결과 저장
            return

    # 에러 → 중첩 재시도
    while True:
        # 내부 루프
        while True:
            restore_timer()
            trigger_int_0()
            dos_int_21h()
            dos_int_21h()
            if carry_flag == 0:
                break

        # 최종 확인
        dos_int_21h()
        if carry_flag == 0:
            break
```

**특징**:
- **중첩 루프**: 가장 견고
- **결과 저장**: 0x3215에 반환값 저장
- **사용처**: 중요한 파일 I/O

---

### 4.3 INT 0 호출의 의미

**INT 0**: Division by Zero Exception

**가능한 용도**:
1. **디버거 트리거**: 개발 중 디버깅
2. **CPU 상태 리셋**: 인터럽트 재설정
3. **Watchdog**: 무한 루프 탈출 메커니즘
4. **레거시 코드**: 제거되지 않은 디버그 코드

**실제 동작**:
```
INT 0 호출
  ↓
CPU는 0x0000:0x0000 주소의 인터럽트 벡터 참조
  ↓
벡터가 설정되어 있으면:
  → 핸들러 실행
벡터가 없으면:
  → 무시 (NOP)
```

**Double Dragon에서**:
```
에러 발생
  ↓
restore_timer()
  ↓
INT 0  ← 이 부분
  ↓
DOS 재시도
```

**추정**: 디버그 빌드에서 브레이크포인트, 릴리스에서는 무해

---

### 4.4 서비스 래퍼 계층

**계층 구조**:
```
Application
  ↓
FUN_1df2, 1dfc, 1dff, 1e02 (서비스 래퍼)
  ↓
FUN_1e26, 1e60, 1e7f (DOS 래퍼)
  ↓
INT 21h (DOS)
```

**서비스 래퍼 공통 패턴**:
```python
function service_wrapper():
    """
    DOS 호출 전후 처리
    """
    # 1. 인터럽트 벡터 백업
    old_vector = read_word(0x00)
    write_word(0x00, 0xFFFF)  # 비활성화

    # 2. Timer Mode 1로 전환
    timer_mode_1()

    # 3. DOS 호출 (재시도 포함)
    dos_call_with_retry()

    # 4. Timer Mode 0 복원
    timer_mode_0()

    # 5. 인터럽트 벡터 복원
    write_word(0x00, old_vector)
```

**인터럽트 벡터 비활성화 이유**:
- DOS 호출 중 게임 인터럽트 방지
- 타이머 인터럽트와 충돌 회피
- 재진입(reentrant) 문제 방지

---

## 5. 조이스틱 입력

### 5.1 게임 포트 (Port 0x201)

**하드웨어**: IBM PC Game Port
**연결**: 조이스틱 최대 2개 (각 2축 + 2버튼)

**포트 레이아웃**:
```
Port 0x201 (Read):
  Bit 7: Joystick B, Button 2
  Bit 6: Joystick B, Button 1
  Bit 5: Joystick A, Button 2
  Bit 4: Joystick A, Button 1
  Bit 3: Joystick B, Y-axis (타이머)
  Bit 2: Joystick B, X-axis (타이머)
  Bit 1: Joystick A, Y-axis (타이머)
  Bit 0: Joystick A, X-axis (타이머)

Port 0x201 (Write):
  Any value → 타이머 리셋
```

### 5.2 축 읽기 (저항 기반)

**원리**: 가변 저항 (potentiometer) → RC 충전 시간

```
1. Port 0x201에 쓰기 → 타이머 리셋
2. 비트 폴링 (0→1 전환 대기)
3. 전환 시간 측정 → 축 위치

충전 시간 (0-100kΩ):
  최소: ~24 µs (0kΩ)
  최대: ~1.1 ms (100kΩ)
```

**의사코드**:
```python
function read_joystick_axis(axis_bit):
    """
    조이스틱 축 위치 읽기

    Args:
        axis_bit: 0-3 (A-X, A-Y, B-X, B-Y)

    Returns:
        0-255 (축 위치)
    """
    # 1. 타이머 리셋
    out_byte(0x201, 0x00)

    # 2. 충전 대기
    timeout = 10000  # CPU 사이클
    counter = 0

    while timeout > 0:
        value = in_byte(0x201)

        # 해당 비트가 1로 전환?
        if (value & (1 << axis_bit)) != 0:
            break

        counter += 1
        timeout -= 1

    # 3. 타임아웃 체크
    if timeout == 0:
        return 255  # 조이스틱 없음

    # 4. 카운터 → 0-255 정규화
    return min(counter // 40, 255)
```

### 5.3 버튼 읽기 (디지털)

**원리**: 버튼 누름 = 비트 0, 안 누름 = 비트 1

```python
function read_joystick_buttons():
    """
    조이스틱 버튼 상태 읽기

    Returns:
        Dictionary: {
            'a_button_1': bool,
            'a_button_2': bool,
            'b_button_1': bool,
            'b_button_2': bool
        }
    """
    value = in_byte(0x201)

    return {
        'a_button_1': (value & 0x10) == 0,  # Bit 4 (active low)
        'a_button_2': (value & 0x20) == 0,  # Bit 5
        'b_button_1': (value & 0x40) == 0,  # Bit 6
        'b_button_2': (value & 0x80) == 0   # Bit 7
    }
```

### 5.4 완전한 조이스틱 읽기

```python
function read_joystick_full(joystick_id):
    """
    조이스틱 완전 읽기 (축 + 버튼)

    Args:
        joystick_id: 0 (A) or 1 (B)

    Returns:
        Dictionary: {
            'x': 0-255,
            'y': 0-255,
            'button1': bool,
            'button2': bool
        }
    """
    if joystick_id == 0:  # Joystick A
        x = read_joystick_axis(0)  # Bit 0
        y = read_joystick_axis(1)  # Bit 1
        button1_bit = 4
        button2_bit = 5
    else:  # Joystick B
        x = read_joystick_axis(2)  # Bit 2
        y = read_joystick_axis(3)  # Bit 3
        button1_bit = 6
        button2_bit = 7

    port_value = in_byte(0x201)

    return {
        'x': x,
        'y': y,
        'button1': (port_value & (1 << button1_bit)) == 0,
        'button2': (port_value & (1 << button2_bit)) == 0
    }
```

### 5.5 캘리브레이션

**문제**: 조이스틱마다 저항 범위 다름

**해결**:
```python
function calibrate_joystick():
    """
    조이스틱 캘리브레이션
    """
    # 1. 센터 위치 읽기
    center_x = read_joystick_axis(0)
    center_y = read_joystick_axis(1)

    # 2. 최소값 (왼쪽 위)
    print("Move joystick to top-left")
    wait_for_button_press()
    min_x = read_joystick_axis(0)
    min_y = read_joystick_axis(1)

    # 3. 최대값 (오른쪽 아래)
    print("Move joystick to bottom-right")
    wait_for_button_press()
    max_x = read_joystick_axis(0)
    max_y = read_joystick_axis(1)

    # 4. 저장
    calibration_data = {
        'center_x': center_x,
        'center_y': center_y,
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y
    }

    return calibration_data
```

---

## 6. 메모리 레이아웃

### 6.1 타이머 메모리

```
0x318c: Timer Mode Flag (1 byte)
  0 = Mode 0 (게임, 291 Hz)
  1 = Mode 1 (DOS, 18.2 Hz)

0x3180-0x3186: 타이머 백업 (8 bytes)
  0x3180: 이전 타이머 상태 (2 bytes)
  0x3182: 이전 플래그 (2 bytes)
  0x3184: 예비 데이터 (2 bytes)
  0x3186: 예비 데이터 (2 bytes)

0x0024: 매직 넘버 체크 (2 bytes)
  0x1db5 = 타이머 복원 필요
```

### 6.2 DOS 호출 메모리

```
0x0000: 인터럽트 벡터 (2 bytes)
  백업/복원됨 (DOS 호출 전후)

0x3215: DOS 반환값 (2 bytes)
  FUN_1e26에서 저장
  파일 핸들 또는 에러 코드

0x0020-0x0026: 상태 저장 (8 bytes)
  타이머 복원 시 사용
```

### 6.3 조이스틱 메모리

```
(메모리 없음, Port I/O만 사용)

Port 0x201: Game Port
  Read: 버튼 + 축 타이머 상태
  Write: 축 타이머 리셋
```

---

## 7. 함수 목록

### 7.1 타이머 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:1c0c | Timer Mode 0 | 게임 모드 (291 Hz) | Low |
| 1000:1c1e | Timer Mode 1 | DOS 모드 (18.2 Hz) | Low |
| 1000:1c43 | Timer Restore | 에러 시 복원 | Medium |

### 7.2 DOS 래퍼 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:1e26 | DOS Full Retry | 중첩 재시도 + 결과 저장 | High |
| 1000:1e60 | DOS Simple Retry | 단일 재시도 | Medium |
| 1000:1e7f | DOS Minimal Retry | 빠른 경로 + 재시도 | Medium |

### 7.3 서비스 래퍼 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:1df2 | Service Wrapper 1 | DOS 호출 + 타이머 전환 | Medium |
| 1000:1dfc | Service Wrapper 2 | 대체 래퍼 | Medium |
| 1000:1dff | Service Wrapper 3 | 대체 래퍼 | Medium |
| 1000:1e02 | Service Wrapper 4 | 대체 래퍼 | Medium |
| 1000:1e8a | High-level File I/O | 파일 로딩 | High |
| 1000:1ea2 | High-level File I/O | 파일 처리 | High |

### 7.4 조이스틱 함수

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:1eb8 | Joystick Init | 조이스틱 초기화 | Low |
| 1000:1faa | Read Axis | 축 읽기 (타이머) | Medium |
| 1000:1ffd | Read Buttons | 버튼 읽기 | Low |

**호출 관계**:
```
Application
  ↓
FUN_1df2 (Service Wrapper)
  ├─→ FUN_1c1e (Timer Mode 1)
  ├─→ FUN_1e26 (DOS Full Retry)
  │     ├─→ FUN_1c43 (Timer Restore)
  │     └─→ INT 21h (DOS)
  └─→ FUN_1c0c (Timer Mode 0)
```

---

## 8. 구현 가이드

### 8.1 현대적 구현 전략

**문제**: 현대 OS는 직접 하드웨어 접근 불가

**해결 방법**:

#### 타이머
```
DOS PIT → 현대 타이머 API

Windows: QueryPerformanceCounter()
Linux:   clock_gettime(CLOCK_MONOTONIC)
Web:     performance.now()
```

#### DOS 호출
```
INT 21h → 표준 파일 API

C:    fopen(), fread(), fwrite()
C++:  std::ifstream, std::ofstream
JS:   FileReader API
```

#### 조이스틱
```
Port 0x201 → 게임패드 API

Windows: XInput, DirectInput
Linux:   /dev/input/js*
Web:     Gamepad API
```

### 8.2 에뮬레이션 접근

**옵션 1: DOSBox 사용**
```
- 완벽한 하드웨어 에뮬레이션
- Port I/O, INT 21h 모두 지원
- 성능 오버헤드
```

**옵션 2: 하드웨어 추상화**
```
Hardware Abstraction Layer (HAL):
  - Timer: 추상 인터페이스
  - File I/O: 추상 인터페이스
  - Input: 추상 인터페이스

각 플랫폼에 구현:
  - DOS: 직접 Port I/O
  - Modern: OS API 사용
```

### 8.3 함정 (Pitfalls)

**타이머**:
```
❌ 나쁜 예:
  # 타이머 전환 없이 DOS 호출
  dos_file_open()  # Mode 0에서 호출 → 충돌

✅ 좋은 예:
  timer_mode_1()   # 안전 모드
  dos_file_open()
  timer_mode_0()   # 게임 모드 복원
```

**조이스틱**:
```
❌ 나쁜 예:
  # 무한 대기
  while (in_byte(0x201) & 1) == 0:
    pass  # 조이스틱 없으면 영원히 대기

✅ 좋은 예:
  timeout = 10000
  while timeout > 0:
    if (in_byte(0x201) & 1) != 0:
      break
    timeout -= 1

  if timeout == 0:
    return ERROR  # 조이스틱 없음
```

---

## 9. 테스트 전략

### 9.1 타이머 테스트

**기본 테스트**:
```python
def test_timer_mode_0():
    """Mode 0 설정 테스트"""
    timer_mode_0()

    # 플래그 확인
    assert read_byte(0x318c) == 0

    # 주파수 측정 (실제 하드웨어 필요)
    # 291 Hz 근처여야 함
```

**전환 테스트**:
```python
def test_timer_switching():
    """Mode 0 ↔ Mode 1 전환"""
    timer_mode_0()
    assert read_byte(0x318c) == 0

    timer_mode_1()
    assert read_byte(0x318c) == 1

    timer_mode_0()
    assert read_byte(0x318c) == 0
```

### 9.2 DOS 호출 테스트

**재시도 테스트** (모의 환경):
```python
def test_dos_retry():
    """재시도 메커니즘 테스트"""
    fail_count = 0

    def mock_dos_call():
        nonlocal fail_count
        fail_count += 1

        if fail_count < 3:
            set_carry_flag(1)  # 실패
        else:
            set_carry_flag(0)  # 성공

    dos_call_with_retry(mock_dos_call)

    assert fail_count == 3  # 3번째 성공
```

### 9.3 조이스틱 테스트

**버튼 테스트**:
```python
def test_joystick_buttons():
    """버튼 읽기 테스트"""
    buttons = read_joystick_buttons()

    assert 'a_button_1' in buttons
    assert 'a_button_2' in buttons
    assert isinstance(buttons['a_button_1'], bool)
```

**축 테스트** (실제 하드웨어):
```
1. 조이스틱 센터 위치
2. 축 읽기
3. 값이 중간 범위(~128)인지 확인

4. 조이스틱 왼쪽 위로
5. 축 읽기
6. X < 64, Y < 64 확인
```

---

## 10. 참고

### 10.1 관련 알고리즘

- [`../algorithms/VSYNC_TIMING.md`](../algorithms/VSYNC_TIMING.md) - VSync 동기화 (Port 0x3DA)

### 10.2 관련 시스템

- [`05_INPUT_CAMERA.md`](05_INPUT_CAMERA.md) - 조이스틱 입력 사용
- [`06_STAGE_LIFECYCLE.md`](06_STAGE_LIFECYCLE.md) - DOS 파일 로딩

### 10.3 원본 분석

- [`../archive/phase4-analysis/SYSTEM_SERVICES_HARDWARE_IO_ANALYSIS.md`](../archive/phase4-analysis/SYSTEM_SERVICES_HARDWARE_IO_ANALYSIS.md) - 완전한 분석

### 10.4 외부 참조

- [Intel 8253 PIT (Wikipedia)](https://en.wikipedia.org/wiki/Intel_8253)
- [DOS INT 21h Reference](https://en.wikipedia.org/wiki/DOS_API)
- [IBM PC Game Port (Wikipedia)](https://en.wikipedia.org/wiki/Game_port)

---

**작성일**: 2025-01-24
**버전**: 1.0
**언어 중립성**: 의사코드 기반, 모든 언어로 구현 가능

**다음 문서**: [06_STAGE_LIFECYCLE.md](06_STAGE_LIFECYCLE.md) - 스테이지 생명주기
**이전 문서**: [07_COMPRESSION.md](07_COMPRESSION.md) - 압축 시스템
