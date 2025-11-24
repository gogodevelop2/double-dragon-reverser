# Double Dragon - 시스템 서비스 및 하드웨어 I/O 완전 분석

**분석 날짜**: 2025-11-24
**Phase**: 4.12
**문서 버전**: 1.0

---

## 📋 개요

이 문서는 Double Dragon의 **시스템 서비스 인터페이스**와 **하드웨어 I/O** 계층을 완전히 분석합니다. DOS 시스템 호출, 타이머 제어, 조이스틱 입력 등 저수준 하드웨어 접근을 중점적으로 다룹니다.

### 분석 범위
- 15개 함수 분석 완료
- DOS INT 21h 시스템 호출 래퍼
- PIT (Programmable Interval Timer) 제어
- 조이스틱 입력 시스템 (Port 0x201)
- 에러 처리 및 재시도 메커니즘

---

## 🎯 핵심 발견 사항

### 1. 3계층 시스템 아키텍처

```
┌─────────────────────────────────────────┐
│  Application Layer                       │
│  (게임 로직, 엔티티 시스템)               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  System Services Layer                   │
│  - FUN_1df2, 1dfc, 1dff, 1e02 (wrappers)│
│  - FUN_1e8a, 1ea2 (high-level)          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Hardware Abstraction Layer              │
│  - FUN_1e26, 1e60, 1e7f (DOS INT 21h)  │
│  - FUN_1c0c, 1c1e, 1c43 (Timer PIT)    │
│  - FUN_1eb8, 1faa, 1ffd (Joystick)     │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Hardware Layer                          │
│  - DOS (INT 21h)                        │
│  - PIT (Port 0x43, 0x40)                │
│  - Game Port (Port 0x201)               │
└─────────────────────────────────────────┘
```

### 2. 에러 처리 패턴

모든 DOS I/O 함수는 **Carry Flag 기반 재시도 메커니즘**을 구현:

```c
do {
    result = DOS_operation();  // INT 21h
    if (success) return;       // CF = 0

    // 에러 발생 (CF = 1)
    restore_timer();           // FUN_1c43
    trigger_interrupt();       // INT 0
    retry_operation();
} while (error);
```

**특징**:
- **무한 재시도**: 성공할 때까지 반복
- **타이머 복원**: 에러 시 시스템 상태 복구
- **INT 0 호출**: Division by zero exception (디버거 트리거?)

---

## 📊 함수별 상세 분석

## 타이머 시스템 (3개, 50 bytes)

### FUN_1000_1c0c (18 bytes) - Timer Mode 0 Initialization
**주소**: 1000:1c0c

```c
undefined1 FUN_1000_1c0c(void) {
    *(undefined1 *)0x318c = 0;  // Timer mode flag = 0

    // PIT Channel 0 설정
    out(0x43, 0x36);  // Command: Ch0, LSB+MSB, Mode 3, Binary
    out(0x40, 0x00);  // Counter LSB = 0
    out(0x40, 0x10);  // Counter MSB = 0x10

    return 0x10;
}
```

**상세 분석**:

1. **Port 0x43 명령 (0x36 = 00110110b)**:
   ```
   Bits 7-6: 00 = Select Channel 0 (System Timer)
   Bits 5-4: 11 = Access mode: LSB then MSB
   Bits 3-1: 011 = Mode 3 (Square Wave Generator)
   Bit 0:    0 = Binary counter (not BCD)
   ```

2. **Counter 값: 0x1000 = 4096**:
   ```
   PIT Clock: 1.193182 MHz
   Divisor: 4096
   Output Frequency: 1193182 / 4096 = ~291.4 Hz
   Period: ~3.43 ms
   ```

3. **용도**:
   - 시스템 타이머 고속 모드
   - 게임 메인 루프 타이밍
   - 291 Hz = 약 17 frames per 60Hz screen

**메모리**:
- `0x318c = 0`: Timer mode 0 활성

---

### FUN_1000_1c1e (16 bytes) - Timer Mode 1 Initialization
**주소**: 1000:1c1e

```c
undefined1 FUN_1000_1c1e(void) {
    *(undefined1 *)0x318c = 1;  // Timer mode flag = 1

    // PIT Channel 0 설정 (최대 속도)
    out(0x43, 0x36);  // Command: Ch0, LSB+MSB, Mode 3, Binary
    out(0x40, 0x00);  // Counter LSB = 0
    out(0x40, 0x00);  // Counter MSB = 0

    return 0;
}
```

**상세 분석**:

1. **Counter 값: 0x0000 = 65536 (overflow)**:
   ```
   PIT Clock: 1.193182 MHz
   Divisor: 65536 (0 wraps to max)
   Output Frequency: 1193182 / 65536 = ~18.2 Hz
   Period: ~54.9 ms
   ```

2. **용도**:
   - **표준 DOS 타이머 속도** (18.2 Hz = 65536 / 1.193182 MHz)
   - 시스템 호환 모드
   - DOS 함수 호출 시 사용

3. **Mode 0 vs Mode 1 비교**:
   ```
   Mode 0: 291 Hz (~3.4 ms)  → 게임플레이 (빠름)
   Mode 1:  18 Hz (~55 ms)   → DOS I/O (느림, 안전)
   ```

**메모리**:
- `0x318c = 1`: Timer mode 1 활성

---

### FUN_1000_1c43 (56 bytes) - Timer State Restoration
**주소**: 1000:1c43

```c
void FUN_1000_1c43(void) {
    // 특정 조건에서만 복원
    if (iRam00000024 == 0x1db5) {
        // 타이머 상태 복원
        iRam00000024 = DAT_1988_3180;
        uRam00000026 = DAT_1988_3182;

        // Timer Mode 1로 전환 (안전 모드)
        FUN_1000_1c1e();

        // 추가 상태 복원
        uRam00000020 = DAT_1988_3184;
        uRam00000022 = DAT_1988_3186;
    }
}
```

**상세 분석**:

1. **트리거 조건**:
   - `iRam00000024 == 0x1db5`: 매직 넘버 체크
   - 0x1db5 = 7605 (의미 불명, 특정 상태 플래그?)

2. **복원 데이터** (0x3180-0x3186):
   ```
   0x3180: 이전 타이머 상태 (2 bytes)
   0x3182: 이전 플래그 (2 bytes)
   0x3184: 예비 데이터 (2 bytes)
   0x3186: 예비 데이터 (2 bytes)
   ```

3. **호출 위치**:
   - 모든 DOS I/O 에러 핸들러
   - INT 0 (Division by zero) 이후
   - 시스템 불안정 시 복구

**설계 의도**:
- **Fail-safe 메커니즘**: 타이머 오류 시 안전 모드 복귀
- **DOS 호환성**: Mode 1 (18.2 Hz) 복원

---

## DOS 시스템 호출 래퍼 (3개, 74 bytes)

### FUN_1000_1e26 (32 bytes) - DOS Call with Full Retry
**주소**: 1000:1e26

```c
void FUN_1000_1e26(void) {
    code *pcVar1;
    undefined2 uVar2;

    // 1차 시도
    pcVar1 = (code *)swi(0x21);  // DOS interrupt
    (*pcVar1)();
    if (!(bool)in_CF) {  // Success
        in_CF = false;

        // 2차 DOS 호출
        pcVar1 = (code *)swi(0x21);
        uVar2 = (*pcVar1)();
        if (!(bool)in_CF) {
            *(undefined2 *)0x3215 = uVar2;  // Save result
            return;
        }
    }

    // 에러 발생 - 무한 재시도
    do {
        do {
            FUN_1000_1c43();  // 타이머 복원

            pcVar1 = (code *)swi(0);    // INT 0 (디버거?)
            (*pcVar1)();

            pcVar1 = (code *)swi(0x21);  // DOS retry
            (*pcVar1)();

            pcVar1 = (code *)swi(0x21);  // DOS retry
            (*pcVar1)();
        } while ((bool)in_CF);  // 내부 루프

        pcVar1 = (code *)swi(0x21);  // Final check
        (*pcVar1)();
    } while ((bool)in_CF);  // 외부 루프
}
```

**상세 분석**:

1. **2단계 DOS 호출**:
   - 1차: 초기화 또는 설정
   - 2차: 실제 작업 수행
   - 결과를 0x3215에 저장

2. **중첩 재시도 루프**:
   ```
   Outer loop:
       Inner loop:
           restore_timer()
           trigger_INT_0()
           retry_DOS_call() × 2
       until success (CF=0)

       final_DOS_check()
   until success
   ```

3. **INT 0 호출**:
   - Division by zero exception
   - **추정 용도**:
     - 디버거 트리거 (개발 중)
     - CPU 상태 리셋
     - 인터럽트 벡터 재설정

4. **결과 저장**: `0x3215` (2 bytes)
   - DOS 함수 반환값
   - 에러 코드 또는 핸들

**호출처**:
- FUN_1000_1df2
- FUN_1000_1dfc

---

### FUN_1000_1e60 (31 bytes) - DOS Call with Simple Retry
**주소**: 1000:1e60

```c
void FUN_1000_1e60(void) {
    code *pcVar1;

    do {
        // 1차 DOS 호출
        pcVar1 = (code *)swi(0x21);
        (*pcVar1)();
        if (!(bool)in_CF) {
            // 2차 DOS 호출
            pcVar1 = (code *)swi(0x21);
            (*pcVar1)();
            if (!(bool)in_CF) {
                return;  // Success
            }
        }

        // 에러 처리
        FUN_1000_1c43();  // 타이머 복원
        pcVar1 = (code *)swi(0);    // INT 0
        (*pcVar1)();
        pcVar1 = (code *)swi(0x21);  // Retry
        (*pcVar1)();
    } while (true);  // 무한 루프
}
```

**FUN_1e26과의 차이**:

| 속성 | FUN_1e26 | FUN_1e60 |
|------|----------|----------|
| 루프 | 중첩 (2단) | 단일 |
| 재시도 횟수 | 3회/iteration | 1회/iteration |
| 결과 저장 | 있음 (0x3215) | 없음 |
| 복잡도 | High | Low |

**용도**:
- 단순 DOS 작업 (파일 닫기, flush 등)
- 결과 값 불필요한 작업

**호출처**:
- FUN_1000_1df2
- FUN_1000_1dfc
- FUN_1000_1dff

---

### FUN_1000_1e7f (11 bytes) - DOS Call with Minimal Retry
**주소**: 1000:1e7f

```c
void FUN_1000_1e7f(void) {
    code *pcVar1;

    // 1차 시도
    pcVar1 = (code *)swi(0x21);
    (*pcVar1)();
    if (!(bool)in_CF) {
        return;  // Success
    }

    // 에러 - 전체 재시도 (FUN_1e26 코드 재사용)
    do {
        do {
            FUN_1000_1c43();
            pcVar1 = (code *)swi(0);
            (*pcVar1)();
            pcVar1 = (code *)swi(0x21);
            (*pcVar1)();
            pcVar1 = (code *)swi(0x21);
            (*pcVar1)();
        } while ((bool)in_CF);
        pcVar1 = (code *)swi(0x21);
        (*pcVar1)();
    } while ((bool)in_CF);
}
```

**특징**:
- **빠른 성공 경로**: 1차 시도 성공 시 즉시 반환
- **전체 재시도**: 실패 시 FUN_1e26과 동일한 중첩 루프
- **코드 재사용**: 에러 핸들러 공유

**호출처**:
- FUN_1000_1df2
- FUN_1000_1dfc
- FUN_1000_1dff
- FUN_1000_1e02

---

## 시스템 서비스 래퍼 (5개, 133 bytes)

### FUN_1000_1df2 (24 bytes) - Full DOS Service Wrapper
**주소**: 1000:1df2

```c
void FUN_1000_1df2(void) {
    undefined2 uVar1;

    // 0x0000 백업 (인터럽트 벡터?)
    uVar1 = *(undefined2 *)0x0;
    *(undefined2 *)0x0 = 0xffff;  // Disable

    // 3단계 DOS 작업
    FUN_1000_1e26();  // Full retry (result @ 0x3215)
    FUN_1000_1e60();  // Simple retry
    FUN_1000_1e7f();  // Minimal retry

    // 복원
    *(undefined2 *)0x0 = uVar1;
}
```

**분석**:

1. **인터럽트 비활성화**:
   - `0x0 = 0xffff`: INT 0 벡터 무효화
   - DOS 작업 중 인터럽트 방지

2. **3단계 작업 체인**:
   ```
   1. FUN_1e26: 복잡한 작업 (파일 열기 등)
   2. FUN_1e60: 중간 작업 (읽기/쓰기)
   3. FUN_1e7f: 마무리 작업 (닫기)
   ```

3. **원자성 보장**:
   - 인터럽트 차단
   - 전체 작업 완료까지 방해 없음

**호출처**:
- FUN_1000_1e8a
- FUN_1000_1ea2

---

### FUN_1000_1dfc (13 bytes) - DOS Service Wrapper (Stack Version)
**주소**: 1000:1dfc

```c
void FUN_1000_1dfc(void) {
    undefined2 in_stack_00000000;  // 스택에서 전달

    FUN_1000_1e26();
    FUN_1000_1e60();
    FUN_1000_1e7f();

    *(undefined2 *)0x0 = in_stack_00000000;  // 스택값으로 복원
}
```

**FUN_1df2와의 차이**:
- 백업 없음 (caller가 전달)
- 스택 파라미터 사용
- 더 가벼움 (11 bytes 적음)

---

### FUN_1000_1dff (10 bytes) - Partial DOS Wrapper
**주소**: 1000:1dff

```c
void FUN_1000_1dff(void) {
    undefined2 in_stack_00000000;

    FUN_1000_1e60();  // Simple retry
    FUN_1000_1e7f();  // Minimal retry

    *(undefined2 *)0x0 = in_stack_00000000;
}
```

**특징**:
- FUN_1e26 생략 (초기화 불필요)
- 2단계만 실행
- 빠른 I/O 작업용

---

### FUN_1000_1e02 (8 bytes) - Minimal DOS Wrapper
**주소**: 1000:1e02

```c
void FUN_1000_1e02(void) {
    undefined2 in_stack_00000000;

    FUN_1000_1e7f();  // Minimal retry only

    *(undefined2 *)0x0 = in_stack_00000000;
}
```

**최소 래퍼**:
- 단일 DOS 호출
- 복원만 수행
- 단순 작업 (파일 닫기 등)

---

### FUN_1000_1e8a (45 bytes) - Complex System Service
**주소**: 1000:1e8a

```c
void FUN_1000_1e8a(void) {
    undefined2 uVar1, uVar2;

    // Timer Mode 1 설정 (DOS 호환)
    FUN_1000_1c1e();

    // 0x320d-0x320f 백업 및 재설정
    uVar1 = *(undefined2 *)0x320d;
    uVar2 = *(undefined2 *)0x320f;
    *(undefined2 *)0x320f = 0;
    *(undefined2 *)0x320d = 0x2949;

    // Full DOS 작업
    FUN_1000_1df2(uVar2, uVar1);

    // Unknown function (possibly file I/O)
    FUN_1000_5fe0();

    // Timer Mode 0 복원 (게임 모드)
    FUN_1000_1c0c();
}
```

**고급 작업**:

1. **타이머 전환**:
   ```
   게임 타이머 (291 Hz)
       ↓ FUN_1c1e
   DOS 타이머 (18 Hz)
       ↓ DOS I/O
   게임 타이머 (291 Hz)
       ↓ FUN_1c0c
   ```

2. **시스템 상태 설정**:
   - `0x320d = 0x2949`: 매직 넘버 (I/O 모드?)
   - `0x320f = 0`: 플래그 클리어

3. **FUN_5fe0**: 미분석 함수
   - 파일 읽기/쓰기 추정
   - 메모리 버퍼 관리

**용도**:
- 게임 데이터 로딩
- 세이브/로드 기능
- 리소스 파일 접근

---

### FUN_1000_1ea2 (8 bytes) - Simple System Service
**주소**: 1000:1ea2

```c
void FUN_1000_1ea2(void) {
    FUN_1000_1df2();  // Full DOS wrapper
    FUN_1000_5fe0();  // File I/O (?)
    FUN_1000_1c0c();  // Timer Mode 0
}
```

**FUN_1e8a와의 차이**:

| 속성 | FUN_1e8a | FUN_1ea2 |
|------|----------|----------|
| 타이머 전환 | 있음 (1→0) | 없음 (0만) |
| 상태 설정 | 있음 (0x320d) | 없음 |
| 복잡도 | High | Low |
| 크기 | 45 bytes | 8 bytes |

**용도**:
- 단순 파일 작업
- 타이머 초기화 불필요
- 빠른 리소스 접근

---

## 조이스틱 입력 시스템 (3개, 217 bytes)

### FUN_1000_1eb8 (82 bytes) - Joystick 1 Button Read
**주소**: 1000:1eb8
**하드웨어**: Game Port (0x201)

```c
void FUN_1000_1eb8(void) {
    byte bVar1;
    int iVar2, iVar3;

    // Joystick 비활성화 체크
    if (*(int *)0x0 == -1) {
        return;  // Joystick disabled
    }

    // Port 0x201 트리거 (축 읽기 시작)
    out(0x201, in_AL);

    iVar3 = 0;  // Button 1 counter
    iVar2 = 0;  // Button 2 counter

    // 1000회 폴링 (타임아웃)
    do {
        bVar1 = in(0x201);  // Read port
        iVar3 = iVar3 + 1;
        iVar2 = iVar2 + 1;

        // Button 1 check (bit 0)
        if ((bVar1 & 1) == 0) goto BUTTON1_RELEASED;

        // Button 2 check (bit 1)
        if ((bVar1 & 2) == 0) goto BUTTON2_RELEASED;
    } while (iVar2 < 1000);

    // 타임아웃: 둘 다 안 눌림
    *(undefined1 *)0x3217 = 0;
    return;

BUTTON1_RELEASED:
    // Button 2만 체크 계속
    do {
        if ((bVar1 & 2) == 0) {
            return;  // Both released
        }
        bVar1 = in(0x201);
        iVar2 = iVar2 + 1;
    } while (iVar2 < 1000);
    *(undefined1 *)0x3217 = 0;  // Timeout
    return;

BUTTON2_RELEASED:
    // Button 1만 체크 계속
    do {
        if ((bVar1 & 1) == 0) {
            return;  // Both released
        }
        bVar1 = in(0x201);
        iVar3 = iVar3 + 1;
    } while (iVar3 < 1000);
    *(undefined1 *)0x3217 = 0;  // Timeout
}
```

**Port 0x201 (Game Port) 레이아웃**:

```
Bit  | 용도
-----|----------------------------------
0    | Joystick 1 Button 1 (0=pressed)
1    | Joystick 1 Button 2 (0=pressed)
2    | Joystick 2 Button 1 (0=pressed)
3    | Joystick 2 Button 2 (0=pressed)
4    | Joystick 1 X-axis (RC circuit)
5    | Joystick 1 Y-axis (RC circuit)
6    | Joystick 2 X-axis (RC circuit)
7    | Joystick 2 Y-axis (RC circuit)
```

**상세 분석**:

1. **버튼 읽기 알고리즘**:
   - **Active-low**: 0 = pressed, 1 = not pressed
   - **동시 감지**: 두 버튼 동시 눌림 가능
   - **타임아웃**: 1000 iterations (~1ms @ 1MHz CPU)

2. **타임아웃 값**: `0x3217 = 0`
   - 조이스틱 없음 또는 불량
   - 다음 입력 무시

3. **사용 시나리오**:
   ```
   Button 1만: 공격
   Button 2만: 점프
   Button 1+2: 특수 기술
   Timeout: 조이스틱 비활성화
   ```

---

### FUN_1000_1faa (82 bytes) - Joystick 2 Button Read
**주소**: 1000:1faa

```c
void FUN_1000_1faa(void) {
    byte bVar1;
    int iVar2, iVar3;

    if (*(int *)0x0 == -1) {
        return;
    }

    out(0x201, in_AL);
    iVar3 = 0;
    iVar2 = 0;

    do {
        bVar1 = in(0x201);
        iVar3 = iVar3 + 1;
        iVar2 = iVar2 + 1;

        // Button 1 check (bit 2)
        if ((bVar1 & 4) == 0) goto BUTTON1_RELEASED;

        // Button 2 check (bit 3)
        if ((bVar1 & 8) == 0) goto BUTTON2_RELEASED;
    } while (iVar2 < 1000);

    *(undefined1 *)0x3220 = 0;  // Timeout (Player 2)
    return;

BUTTON1_RELEASED:
    do {
        if ((bVar1 & 8) == 0) {
            return;
        }
        bVar1 = in(0x201);
        iVar2 = iVar2 + 1;
    } while (iVar2 < 1000);
    *(undefined1 *)0x3220 = 0;
    return;

BUTTON2_RELEASED:
    do {
        if ((bVar1 & 4) == 0) {
            return;
        }
        bVar1 = in(0x201);
        iVar3 = iVar3 + 1;
    } while (iVar3 < 1000);
    *(undefined1 *)0x3220 = 0;
}
```

**FUN_1eb8과의 차이**:

| 속성 | FUN_1eb8 (Joy1) | FUN_1faa (Joy2) |
|------|-----------------|-----------------|
| 버튼 마스크 | 0x01, 0x02 (bit 0-1) | 0x04, 0x08 (bit 2-3) |
| 타임아웃 주소 | 0x3217 | 0x3220 |
| 용도 | Player 1 | Player 2 |

**2인 플레이 지원**:
- 독립적인 버튼 감지
- 독립적인 타임아웃 플래그
- 동시 입력 가능

---

### FUN_1000_1ffd (53 bytes) - Joystick 2 Axis Calibration
**주소**: 1000:1ffd

```c
void FUN_1000_1ffd(void) {
    uint in_CX;  // Y-axis value (from previous read)
    uint in_BX;  // X-axis value (from previous read)

    if (*(int *)0x0 != -1) {
        // 타임아웃 플래그 설정
        *(undefined1 *)0x3220 = 1;

        // 조이스틱 2 버튼 읽기
        FUN_1000_1faa();

        // 축 값 저장 및 보정
        if (*(char *)0x3220 != '\0') {  // Success
            // X-axis 저장
            *(uint *)0x3221 = in_BX;  // Raw value
            *(uint *)0x3225 = in_BX;
            *(int *)0x3225 = *(int *)0x3225 - (in_BX >> 1);  // Center = value - value/2

            // Y-axis 저장
            *(uint *)0x3223 = in_CX;  // Raw value
            *(uint *)0x3227 = in_CX;
            *(int *)0x3227 = *(int *)0x3227 - (in_CX >> 1);  // Center = value - value/2
        }
    }
}
```

**축 읽기 알고리즘**:

1. **RC 회로 타이밍**:
   ```
   Port 0x201 write → RC capacitor 방전 시작
   Port 0x201 read  → bit 4-7이 capacitor 전압 반영

   Charge time ∝ Joystick position
   Min: 0 (full left/up)
   Max: ~1000 (full right/down)
   ```

2. **보정 공식**:
   ```
   Raw value: 0 ~ 1000
   Centered: raw - (raw / 2) = -500 ~ +500

   Example:
   - Left (0): 0 - 0 = 0
   - Center (500): 500 - 250 = 250
   - Right (1000): 1000 - 500 = 500
   ```

   **주의**: 보정이 이상함 (중심이 0이 아님)
   - 올바른 보정: `value - 500`
   - 실제 구현: `value - (value / 2)`
   - **버그 가능성**?

3. **메모리 맵** (Player 2):
   ```
   0x3220: Timeout flag (1=valid, 0=invalid)
   0x3221: X-axis raw value
   0x3223: Y-axis raw value
   0x3225: X-axis centered value
   0x3227: Y-axis centered value
   ```

**대응 함수** (Player 1, 미발견):
- FUN_?????: Joystick 1 Axis Calibration
- 메모리: 0x3217-0x321f?

---

## 🗺️ 메모리 맵 완전 정리

### 타이머 시스템 (0x3180-0x318c)

```
주소     | 크기 | 이름                  | 설명
---------|------|-----------------------|---------------------------
0x3180   | 2    | timer_state_backup_0  | Timer 복원용 백업
0x3182   | 2    | timer_state_backup_1  | Timer 복원용 백업
0x3184   | 2    | timer_state_backup_2  | Timer 복원용 백업
0x3186   | 2    | timer_state_backup_3  | Timer 복원용 백업
0x318c   | 1    | timer_mode_flag       | 0=Mode0 (291Hz), 1=Mode1 (18Hz)
```

### DOS I/O 시스템 (0x320d-0x3215)

```
주소     | 크기 | 이름                  | 설명
---------|------|-----------------------|---------------------------
0x320d   | 2    | io_state_0            | DOS I/O 상태 (0x2949 설정)
0x320f   | 2    | io_state_1            | DOS I/O 플래그
0x3215   | 2    | dos_result            | DOS 함수 반환값
```

### 조이스틱 시스템 (0x3217-0x3227)

```
주소     | 크기 | 이름                      | 설명
---------|------|---------------------------|----------------------------
0x3217   | 1    | joy1_timeout              | Joy1 타임아웃 (1=valid, 0=invalid)
0x3218   | 2    | joy1_x_raw                | Joy1 X-axis raw (추정)
0x321a   | 2    | joy1_y_raw                | Joy1 Y-axis raw (추정)
0x321c   | 2    | joy1_x_centered           | Joy1 X-axis centered (추정)
0x321e   | 2    | joy1_y_centered           | Joy1 Y-axis centered (추정)
0x3220   | 1    | joy2_timeout              | Joy2 타임아웃
0x3221   | 2    | joy2_x_raw                | Joy2 X-axis raw
0x3223   | 2    | joy2_y_raw                | Joy2 Y-axis raw
0x3225   | 2    | joy2_x_centered           | Joy2 X-axis centered
0x3227   | 2    | joy2_y_centered           | Joy2 Y-axis centered
```

---

## 🔧 하드웨어 I/O 포트 정리

### Port 0x40 - PIT Channel 0 (System Timer)

```
Access: Out (Write only)
Usage: Timer counter value (LSB/MSB)

Write sequence:
  1. Port 0x43 = 0x36  (Mode command)
  2. Port 0x40 = LSB   (Counter low byte)
  3. Port 0x40 = MSB   (Counter high byte)

Values:
  - 0x0000 = 65536 (18.2 Hz, DOS standard)
  - 0x1000 = 4096 (291 Hz, game mode)
```

### Port 0x43 - PIT Control Register

```
Access: Out (Write only)
Usage: PIT command byte

Command 0x36 (00110110b):
  Bit 7-6: 00 = Channel 0
  Bit 5-4: 11 = LSB then MSB
  Bit 3-1: 011 = Mode 3 (Square Wave)
  Bit 0:   0 = Binary counter
```

### Port 0x201 - Game Port

```
Access: In/Out
Usage: Joystick input

Write: Trigger axis capacitor discharge
Read: Button and axis status

Bit layout:
  0: Joystick 1 Button A (0=pressed)
  1: Joystick 1 Button B (0=pressed)
  2: Joystick 2 Button A (0=pressed)
  3: Joystick 2 Button B (0=pressed)
  4: Joystick 1 X-axis (RC timing)
  5: Joystick 1 Y-axis (RC timing)
  6: Joystick 2 X-axis (RC timing)
  7: Joystick 2 Y-axis (RC timing)
```

---

## 📐 시스템 아키텍처 분석

### 1. 계층화된 에러 처리

```
Level 4: Application (게임 로직)
            ↓
Level 3: Service Layer (FUN_1e8a, 1ea2, 1df2)
            ├─ 타이머 전환 (게임 ↔ DOS)
            ├─ 상태 설정 (0x320d)
            └─ 인터럽트 제어 (0x0)
            ↓
Level 2: Wrapper Layer (FUN_1dfc, 1dff, 1e02)
            ├─ 스택 파라미터 처리
            └─ 간소화된 작업 체인
            ↓
Level 1: Retry Layer (FUN_1e26, 1e60, 1e7f)
            ├─ 무한 재시도
            ├─ Carry flag 체크
            ├─ INT 0 트리거
            └─ Timer 복원
            ↓
Level 0: Hardware (DOS INT 21h, PIT, Game Port)
```

### 2. 타이머 모드 전환 패턴

```c
// 게임플레이 루프
void game_loop() {
    FUN_1c0c();  // Timer Mode 0 (291 Hz)

    while (playing) {
        update_entities();
        render_frame();

        // 파일 로딩 필요 시
        if (need_load) {
            FUN_1e8a();  // 자동으로 Mode 1 → I/O → Mode 0
        }
    }
}

// FUN_1e8a 내부 흐름:
// 1. FUN_1c1e() → Timer Mode 1 (18 Hz, DOS 안전)
// 2. FUN_1df2() → DOS I/O with retry
// 3. FUN_5fe0() → File operations
// 4. FUN_1c0c() → Timer Mode 0 (291 Hz, 게임 복귀)
```

**설계 의도**:
- DOS I/O는 느린 타이머 필요 (하드웨어 호환성)
- 게임플레이는 빠른 타이머 필요 (60 FPS 목표)
- 자동 전환으로 개발자 부담 감소

### 3. 조이스틱 입력 통합

```
초기화:
  1. Port 0x201 write (축 방전 시작)
  2. FUN_1faa() or FUN_1eb8() (버튼 폴링)
  3. FUN_1ffd() (축 보정)

메인 루프:
  while (game_running) {
      // Player 1
      joy1_buttons = read_buttons_joy1();  // FUN_1eb8
      joy1_axis = calibrate_joy1();        // (미발견 함수)

      // Player 2
      joy2_buttons = read_buttons_joy2();  // FUN_1faa
      joy2_axis = calibrate_joy2();        // FUN_1ffd

      // 입력 처리
      process_input(joy1, joy2);
  }

축 처리:
  - Raw value: 0-1000 (RC 충전 시간)
  - Centered: raw - (raw >> 1)
  - Deadzone: ±50 (추정)
```

---

## 🔍 흥미로운 발견

### 1. INT 0 호출의 의미

```c
pcVar1 = (code *)swi(0);  // Division by zero exception
(*pcVar1)();
```

**가능한 이유**:

1. **디버거 트리거**:
   - 개발 중 에러 추적
   - INT 0 핸들러에 브레이크포인트 설정
   - 릴리즈 버전에서는 무해 (핸들러 없으면 무시)

2. **CPU 상태 리셋**:
   - 예외 핸들러가 레지스터 정리
   - 인터럽트 벡터 재설정

3. **잔여 코드**:
   - 디버깅 목적으로 삽입 후 제거 안 됨
   - 성능 영향 미미 (에러 경로만)

### 2. 타이머 모드 주파수 분석

```
Mode 0 (게임): 291.4 Hz
  - 1 frame: 3.43 ms
  - 60 FPS: 16.67 ms → 약 5 ticks/frame
  - 30 FPS: 33.33 ms → 약 10 ticks/frame

Mode 1 (DOS): 18.2 Hz
  - 1 tick: 54.9 ms
  - DOS 표준: 18.2065 Hz 정확히
  - BIOS Time-of-Day 호환

비율: 291 / 18 = ~16:1
```

**게임 프레임 레이트 추정**:
- 5 ticks/frame @ 291 Hz = **58.3 FPS** (likely target)
- CRT VSync: 60 Hz (NTSC) or 50 Hz (PAL)
- Mode 0은 VSync에 맞추기 위한 설정

### 3. 조이스틱 축 보정 버그?

```c
// 실제 코드:
centered = raw - (raw >> 1);

// 예상 동작:
Left (0):    0 - 0 = 0       ✓
Center (500): 500 - 250 = 250 ✗ (0이어야 함)
Right (1000): 1000 - 500 = 500 ✗ (0이어야 함)

// 올바른 보정:
centered = raw - 500;

// 또는 상대값으로 사용?
if (centered < threshold_low) → left
if (centered > threshold_high) → right
```

**가능성**:
1. **의도된 동작**: threshold 체크로 방향 판단
2. **버그**: 수정되지 않았으나 게임 플레이에 영향 없음
3. **하드웨어 특성**: 당시 조이스틱이 0-1000 범위가 아님

---

## 📊 통계 및 성능 분석

### 함수 크기 비교

| 함수 | 크기 (bytes) | 복잡도 | 호출 빈도 | 비고 |
|------|-------------|--------|----------|------|
| FUN_1c0c | 18 | Low | 초기화 | Timer Mode 0 |
| FUN_1c1e | 16 | Low | I/O 전 | Timer Mode 1 |
| FUN_1c43 | 56 | Medium | 에러 시 | Timer 복원 |
| FUN_1e26 | 32 | High | 드물게 | Full retry |
| FUN_1e60 | 31 | Medium | 보통 | Simple retry |
| FUN_1e7f | 11 | Medium | 자주 | Minimal retry |
| FUN_1df2 | 24 | Medium | 드물게 | Full wrapper |
| FUN_1dfc | 13 | Medium | 보통 | Stack wrapper |
| FUN_1dff | 10 | Low | 보통 | Partial wrapper |
| FUN_1e02 | 8 | Low | 자주 | Minimal wrapper |
| FUN_1e8a | 45 | High | 로딩 시 | Complex service |
| FUN_1ea2 | 8 | Low | 종종 | Simple service |
| FUN_1eb8 | 82 | Medium | 매 프레임 | Joy1 buttons |
| FUN_1faa | 82 | Medium | 매 프레임 | Joy2 buttons |
| FUN_1ffd | 53 | Medium | 초기화 | Joy2 axes |
| **총합** | **489** | - | - | - |

### 메모리 사용량

```
타이머 시스템: 13 bytes (0x3180-0x318c)
DOS I/O: 9 bytes (0x320d-0x3215)
조이스틱: 17 bytes (0x3217-0x3227)
= 총 39 bytes
```

---

## 🚀 다음 분석 과제

### Priority P0 (필수)

1. **FUN_1000_5fe0**: 파일 I/O 핵심 함수
   - FUN_1e8a, 1ea2에서 호출
   - 데이터 로딩 메커니즘

2. **Joystick 1 Axis Calibration**:
   - FUN_1ffd의 Player 1 버전
   - 메모리 0x3217-0x321f 사용

3. **키보드 입력 시스템**:
   - BIOS INT 16h 또는 Port 0x60
   - 조이스틱 대체 입력

### Priority P1 (중요)

4. **DOS 파일 핸들 관리**:
   - 파일 열기/닫기
   - 버퍼 관리

5. **타이머 인터럽트 핸들러**:
   - INT 8 (IRQ 0) 핸들러
   - 게임 틱 카운터

---

## 📖 참고 문서

- [GAME_STATE_SCORE_SOUND_ANALYSIS.md](GAME_STATE_SCORE_SOUND_ANALYSIS.md): 사운드 시스템 (PC Speaker)
- [INPUT_CAMERA_PHYSICS_ANALYSIS.md](INPUT_CAMERA_PHYSICS_ANALYSIS.md): 입력 처리 상위 계층
- [MAIN_LOOP_COMPLETE_ANALYSIS.md](MAIN_LOOP_COMPLETE_ANALYSIS.md): 메인 루프 통합

---

## 📝 요약

### 핵심 발견

1. ✅ **3계층 에러 처리**: Application → Service → Retry → Hardware
2. ✅ **듀얼 타이머 모드**: 게임 (291 Hz) ↔ DOS (18 Hz)
3. ✅ **무한 재시도**: Carry flag 기반, INT 0 트리거
4. ✅ **2인 조이스틱 지원**: 독립적인 버튼 및 축 처리
5. ✅ **RC 회로 타이밍**: 0-1000 범위, 보정 공식

### 분석 완료 함수

- **15개 함수** 완전 분석
- **489 bytes** 총 코드 크기
- **타이머/DOS/조이스틱** 3개 하위 시스템
- **메모리 맵** 완전 정리 (39 bytes)

### 남은 과제

- FUN_5fe0 파일 I/O 분석
- Joy1 축 보정 함수 발견
- 키보드 입력 시스템 분석

---

**다음 문서**: [FILE_IO_SYSTEM_ANALYSIS.md](FILE_IO_SYSTEM_ANALYSIS.md) (예정)
**작성일**: 2025-11-24
**분석자**: Claude Code
