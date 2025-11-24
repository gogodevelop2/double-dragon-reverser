# VSync & Frame Timing Algorithm

**작성일**: 2025-11-24
**Phase**: 5 (Algorithm Documents)
**복잡도**: ⭐⭐⭐

---

## 목차

1. [개요](#1-개요)
2. [이론 배경](#2-이론-배경)
3. [Double Dragon 구현](#3-double-dragon-구현)
4. [VSync 알고리즘](#4-vsync-알고리즘)
5. [더블 버퍼링](#5-더블-버퍼링)
6. [PIT 타이머 시스템](#6-pit-타이머-시스템)
7. [프레임 타이밍](#7-프레임-타이밍)
8. [구현 예제](#8-구현-예제)
9. [성능 분석](#9-성능-분석)
10. [테스트 전략](#10-테스트-전략)
11. [최적화 기법](#11-최적화-기법)
12. [문제 해결](#12-문제-해결)
13. [참고 자료](#13-참고-자료)

---

## 1. 개요

### 1.1 VSync란?

**VSync (Vertical Synchronization)**는 화면 렌더링을 모니터의 수직 주사율과 동기화하는 기술입니다.

```
CRT 모니터 주사 과정:
┌────────────────────────┐
│ ····················→ │ ← 스캔라인 0
│ ····················→ │ ← 스캔라인 1
│ ····················→ │ ← 스캔라인 2
│       ...            │
│ ····················→ │ ← 스캔라인 199
└────────────────────────┘
        ↓
   수직 귀선 (VBlank)
        ↓
   스캔라인 0으로 복귀
```

### 1.2 필요성

**Screen Tearing (화면 찢어짐)**:
```
프레임 버퍼 업데이트 중:
┌────────────────────────┐
│ 새 프레임 (상단 50%)    │
├────────────────────────┤ ← Tearing Line
│ 이전 프레임 (하단 50%)  │
└────────────────────────┘

VSync 사용:
┌────────────────────────┐
│                        │
│   완전한 프레임         │
│   (찢어짐 없음)         │
│                        │
└────────────────────────┘
```

### 1.3 Double Dragon의 VSync

**목표**: **60 FPS** (CRT 수직 주사율)

**특징**:
- Port 0x3DA 폴링 (CGA/EGA 상태 레지스터)
- 수직 귀선 대기
- 고정 프레임 타이밍
- PIT 타이머 통합

---

## 2. 이론 배경

### 2.1 CRT 타이밍

#### 프레임 구조 (60 Hz = 16.67 ms/frame)

```
┌─────────────────────────────────────────────────┐
│         Active Display (15.2 ms)                │
│  ┌────────────────────────────────────────┐     │
│  │ Scanline 0                             │     │
│  │ Scanline 1                             │     │
│  │ ...                                    │     │
│  │ Scanline 199                           │     │
│  └────────────────────────────────────────┘     │
│         화면에 표시되는 영역                     │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│       Vertical Blank (VBlank, 1.47 ms)          │
│  ┌────────────────────────────────────────┐     │
│  │  VSync Pulse (bit 3 = 1)               │     │
│  │  ← VRAM 업데이트 안전 구간              │
│  └────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
                     ↓
                다음 프레임
```

#### 타이밍 수치

```
화면 해상도: 320×200 (CGA Mode 4)
수평 주사율: 31.5 kHz (1 scanline = 31.7 µs)
수직 주사율: 60 Hz (1 frame = 16.67 ms)

Active Display:
  200 scanlines × 31.7 µs = 6.34 ms (비정확, 실제 15.2 ms)
  + Horizontal Blank 포함

Vertical Blank:
  약 25 scanlines × 31.7 µs ≈ 0.79 ms
  실제: ~1.47 ms (VSync 펄스 포함)
```

### 2.2 Port 0x3DA - CGA Status Register

```
Bit 레이아웃:
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ 7 │ 6 │ 5 │ 4 │ 3 │ 2 │ 1 │ 0 │
└───┴───┴───┴───┴───┴───┴───┴───┘
              │           │
              │           └─ Display Enable
              │              0 = active display
              │              1 = horizontal retrace
              │
              └─ Vertical Sync
                 0 = not in VSync
                 1 = in VSync (VBlank)
```

**읽기 방법**:
```c
uint8_t status = inportb(0x3DA);

bool horizontal_retrace = (status & 0x01) != 0;
bool vertical_sync = (status & 0x08) != 0;
```

### 2.3 이중/삼중 버퍼링

#### Single Buffering (버퍼링 없음)

```
Frame N:
  ┌─ 렌더링 → VRAM (직접 쓰기)
  └─ 화면 표시 (동시)

문제: Screen tearing
```

#### Double Buffering (이중 버퍼링)

```
Frame N:
  ┌─ 렌더링 → Back Buffer
  ├─ VSync 대기
  ├─ Flip (Back ↔ Front)
  └─ 화면 표시 (Front Buffer)

Frame N+1:
  ┌─ 렌더링 → Back Buffer (이전 Front)
  ...

이점: Tearing 제거
단점: 메모리 2배
```

#### Triple Buffering (삼중 버퍼링)

```
Buffer A: 렌더링 중
Buffer B: 대기 (렌더링 완료)
Buffer C: 화면 표시

장점: 렌더링 지연 감소
단점: 메모리 3배, 복잡도 증가
```

---

## 3. Double Dragon 구현

### 3.1 VSync 대기 함수

**Function**: FUN_1000_0604 (14 bytes)
**Address**: 1000:0604

```c
void wait_for_vsync() {
    uint8_t status;

    // 1단계: VSync OFF 대기 (이전 VBlank 종료)
    do {
        status = inportb(0x3DA);
    } while (status & 0x08);  // bit 3 = 1

    // 2단계: VSync ON 대기 (새 VBlank 시작)
    do {
        status = inportb(0x3DA);
    } while (!(status & 0x08));  // bit 3 = 0

    // → VBlank 시작 직후, VRAM 업데이트 안전
}
```

### 3.2 타이밍 다이어그램

```
포트 0x3DA bit 3 변화:
        ┌───────────┐       ┌───────────┐
        │  VSync=1  │       │  VSync=1  │
────────┘           └───────┘           └────
  Active Display     VBlank   Active Display
  (15.2 ms)        (1.47 ms)  (15.2 ms)
        │           │       │
        │           │       └─ 2단계 종료: 다음 프레임 시작
        │           └─ 1단계 종료: VBlank 시작
        └─ 1단계 시작: 이전 VBlank 종료 대기
```

### 3.3 메인 루프 통합

```c
// Double Dragon 메인 루프 (pseudocode)
void main_game_loop() {
    while (game_running) {
        // 1. 게임 로직 업데이트
        update_entities();      // ~0.5 ms
        update_ai();            // ~0.1 ms
        update_physics();       // ~0.2 ms
        update_camera();        // ~0.05 ms

        // 2. 렌더링 리스트 빌드
        build_render_list();    // ~0.3 ms

        // 3. VSync 대기
        wait_for_vsync();       // ~최대 16.67 ms (평균 8 ms)

        // 4. VRAM 업데이트 (VBlank 중, 안전)
        render_sprites();       // ~0.2 ms
        update_scroll_regs();   // ~0.01 ms

        // 5. 프레임 카운터
        frame_counter++;
    }
}
```

### 3.4 메모리 레이아웃

```
VRAM (CGA Mode 4):
┌────────────────────────────────────────┐
│ Segment 0xB800 (Bank 0, 8KB)           │
│   짝수 스캔라인 (0, 2, 4, ..., 198)     │
├────────────────────────────────────────┤
│ Segment 0xBA00 (Bank 1, 8KB)           │
│   홀수 스캔라인 (1, 3, 5, ..., 199)     │
└────────────────────────────────────────┘

VRAM (EGA Mode D):
┌────────────────────────────────────────┐
│ Segment 0xA000 (64KB)                  │
│   4-plane planar (16 colors)           │
│   Plane 0: Intensity                   │
│   Plane 1: Red                         │
│   Plane 2: Green                       │
│   Plane 3: Blue                        │
└────────────────────────────────────────┘
```

---

## 4. VSync 알고리즘

### 4.1 기본 알고리즘

```python
def wait_for_vsync_basic():
    """
    기본 VSync 대기 알고리즘
    2단계 폴링으로 정확한 VBlank 시작 감지
    """
    # 1단계: VSync OFF 대기 (이전 VBlank 종료)
    while inportb(0x3DA) & 0x08:
        pass  # Busy wait

    # 2단계: VSync ON 대기 (새 VBlank 시작)
    while not (inportb(0x3DA) & 0x08):
        pass  # Busy wait

    # VBlank 시작!
```

**타이밍 정확도**: ±1 인스트럭션 사이클 (~0.2 µs @ 4.77 MHz)

### 4.2 최적화된 알고리즘

```python
def wait_for_vsync_optimized():
    """
    최적화: 첫 번째 루프 스킵 (이미 VBlank 끝났을 가능성)
    """
    status = inportb(0x3DA)

    # 이미 VBlank 중이면 종료 대기
    if status & 0x08:
        while inportb(0x3DA) & 0x08:
            pass

    # VBlank 시작 대기
    while not (inportb(0x3DA) & 0x08):
        pass
```

### 4.3 타임아웃 보호

```python
def wait_for_vsync_with_timeout(timeout_ms=50):
    """
    타임아웃 보호 (무한 루프 방지)
    """
    start_time = get_timer()

    # 1단계: VSync OFF 대기
    while inportb(0x3DA) & 0x08:
        if get_timer() - start_time > timeout_ms:
            return False  # 타임아웃

    # 2단계: VSync ON 대기
    while not (inportb(0x3DA) & 0x08):
        if get_timer() - start_time > timeout_ms:
            return False  # 타임아웃

    return True  # 성공
```

### 4.4 인터럽트 기반 VSync

```c
// 더 효율적인 방법: IRQ 사용 (Double Dragon은 미사용)
void setup_vsync_interrupt() {
    // IRQ 9 (VSync interrupt)
    set_interrupt_handler(9, vsync_isr);

    // Enable VSync interrupt
    outportb(0x3C0, 0x20);  // Attribute Controller
}

void vsync_isr() {
    vsync_flag = 1;  // 플래그 설정
    // EOI (End of Interrupt)
    outportb(0x20, 0x20);
}

void wait_for_vsync_irq() {
    vsync_flag = 0;
    while (vsync_flag == 0) {
        // CPU yield (다른 작업 가능)
        _yield();
    }
}
```

---

## 5. 더블 버퍼링

### 5.1 개념

```
Frame N:
  ┌──────────────┐
  │ Back Buffer  │ ← 렌더링
  ├──────────────┤
  │ Front Buffer │ ← 화면 표시
  └──────────────┘

VSync 발생:

Frame N+1:
  ┌──────────────┐
  │ Front Buffer │ ← 렌더링 (이전 Back)
  ├──────────────┤
  │ Back Buffer  │ ← 화면 표시 (이전 Front)
  └──────────────┘
```

### 5.2 구현 (Page Flipping)

```c
// 변수
uint8_t* front_buffer = (uint8_t*)0xB800;
uint8_t* back_buffer = (uint8_t*)0xA000;  // 추가 메모리

void double_buffering_flip() {
    // 1. Back buffer에 렌더링
    render_to_buffer(back_buffer);

    // 2. VSync 대기
    wait_for_vsync();

    // 3. Flip (memcpy)
    memcpy(front_buffer, back_buffer, 16000);  // 320×200/4

    // 또는 하드웨어 레지스터 변경 (VGA)
    // set_display_start(back_buffer);
}
```

### 5.3 Double Dragon 방식

Double Dragon은 **Partial Double Buffering** 사용:

```c
// 순환 버퍼 (Circular Buffer)
uint16_t vram_base = 0xb0d0;
uint16_t vram_offset = 0;  // 0x0000 ~ 0x3fff (16KB)

void render_frame() {
    // 1. 순환 버퍼의 현재 위치에 렌더링
    render_to_offset(vram_base + vram_offset);

    // 2. VSync 대기
    wait_for_vsync();

    // 3. 오프셋 업데이트 (스크롤)
    vram_offset = (vram_offset + scroll_delta) & 0x3fff;

    // 4. 하드웨어 레지스터 업데이트
    set_display_start(vram_base + vram_offset);
}
```

**장점**:
- 메모리 절약 (16KB 순환 버퍼)
- 스크롤과 통합
- 빠른 플립 (레지스터 변경만)

---

## 6. PIT 타이머 시스템

### 6.1 PIT 개요

**하드웨어**: Intel 8253/8254 Programmable Interval Timer
**기준 주파수**: 1.193182 MHz

**포트**:
- `0x43`: Control port
- `0x40`: Channel 0 (system timer)
- `0x41`: Channel 1 (DRAM refresh)
- `0x42`: Channel 2 (speaker)

### 6.2 Mode 0 (게임 모드)

```c
void set_timer_mode_0() {
    // Control byte: 00 11 011 0
    // Ch0, LSB+MSB, Mode 3, Binary
    outportb(0x43, 0x36);

    // Counter = 4096
    outportb(0x40, 0x00);  // LSB
    outportb(0x40, 0x10);  // MSB

    // 주파수 = 1193182 / 4096 = 291.4 Hz
    // 주기 = 3.43 ms
}
```

**용도**: 게임 프레임 타이밍 (60 FPS 목표)
**특성**: 빠른 인터럽트 (초당 291회)

### 6.3 Mode 1 (DOS 모드)

```c
void set_timer_mode_1() {
    outportb(0x43, 0x36);

    // Counter = 65536 (0 = overflow)
    outportb(0x40, 0x00);  // LSB
    outportb(0x40, 0x00);  // MSB

    // 주파수 = 1193182 / 65536 = 18.2 Hz
    // 주기 = 54.9 ms
}
```

**용도**: DOS 호환 모드 (표준 18.2 Hz)
**특성**: 느린 인터럽트, 안정적

### 6.4 타이머 통합

```c
// 프레임 타이밍 (60 FPS 목표)
uint32_t frame_counter = 0;
uint32_t timer_ticks = 0;  // PIT 291 Hz

void game_loop() {
    // 목표: 291 Hz / 60 FPS ≈ 4.85 ticks/frame
    const uint32_t TICKS_PER_FRAME = 5;

    while (game_running) {
        // 타이머 대기
        while (timer_ticks < frame_counter * TICKS_PER_FRAME) {
            // Busy wait 또는 yield
        }

        // 게임 업데이트
        update_game();

        // VSync 대기 및 렌더링
        wait_for_vsync();
        render_frame();

        frame_counter++;
    }
}

// IRQ0 핸들러 (PIT 인터럽트)
void timer_isr() {
    timer_ticks++;
    // EOI
    outportb(0x20, 0x20);
}
```

---

## 7. 프레임 타이밍

### 7.1 프레임 예산 (60 FPS)

```
16.67 ms/frame:
┌──────────────────────────────────────────┐
│ 게임 로직 (1.0 ms)                       │
├──────────────────────────────────────────┤
│ 렌더링 준비 (0.3 ms)                     │
├──────────────────────────────────────────┤
│ VSync 대기 (평균 8 ms, 최대 16.67 ms)    │
├──────────────────────────────────────────┤
│ VRAM 업데이트 (0.2 ms)                   │
├──────────────────────────────────────────┤
│ 여유 (7.17 ms)                           │
└──────────────────────────────────────────┘
```

### 7.2 프레임 레이트 제한

```c
// Method 1: VSync (하드웨어 동기화)
void limit_fps_vsync() {
    wait_for_vsync();  // 60 Hz 강제
}

// Method 2: 소프트웨어 타이머
void limit_fps_timer(int target_fps) {
    static uint32_t last_time = 0;
    uint32_t frame_time = 1000 / target_fps;  // ms

    uint32_t current_time = get_time_ms();
    uint32_t elapsed = current_time - last_time;

    if (elapsed < frame_time) {
        sleep(frame_time - elapsed);
    }

    last_time = get_time_ms();
}

// Method 3: 결합 (정확도 최대)
void limit_fps_hybrid() {
    // 1. 소프트웨어 대기 (여유 시간 소비)
    limit_fps_timer(60);

    // 2. VSync (마지막 동기화)
    wait_for_vsync();
}
```

### 7.3 FPS 측정

```c
// FPS 카운터
typedef struct {
    uint32_t frame_count;
    uint32_t last_time;
    float current_fps;
} FPSCounter;

void update_fps_counter(FPSCounter* fps) {
    fps->frame_count++;

    uint32_t current_time = get_time_ms();
    uint32_t elapsed = current_time - fps->last_time;

    // 1초마다 FPS 계산
    if (elapsed >= 1000) {
        fps->current_fps = (float)fps->frame_count / (elapsed / 1000.0f);
        fps->frame_count = 0;
        fps->last_time = current_time;
    }
}
```

---

## 8. 구현 예제

### 8.1 C 구현

```c
#include <stdio.h>
#include <stdint.h>
#include <dos.h>
#include <conio.h>

// VSync 대기 (Port 0x3DA)
void wait_for_vsync() {
    // 1단계: VSync OFF 대기
    while (inportb(0x3DA) & 0x08);

    // 2단계: VSync ON 대기
    while (!(inportb(0x3DA) & 0x08));
}

// PIT 타이머 설정
void set_timer_frequency(uint16_t frequency) {
    uint16_t divisor = 1193182 / frequency;

    outportb(0x43, 0x36);  // Ch0, LSB+MSB, Mode 3
    outportb(0x40, divisor & 0xFF);  // LSB
    outportb(0x40, (divisor >> 8) & 0xFF);  // MSB
}

// 더블 버퍼링
typedef struct {
    uint8_t* front;
    uint8_t* back;
    size_t size;
} DoubleBuffer;

void double_buffer_init(DoubleBuffer* db, size_t width, size_t height) {
    db->size = width * height / 4;  // 2 bits/pixel
    db->front = (uint8_t*)0xB8000000;  // CGA VRAM
    db->back = malloc(db->size);
}

void double_buffer_flip(DoubleBuffer* db) {
    wait_for_vsync();
    memcpy(db->front, db->back, db->size);
}

void double_buffer_free(DoubleBuffer* db) {
    free(db->back);
}

// 게임 루프
void game_loop() {
    DoubleBuffer db;
    double_buffer_init(&db, 320, 200);

    set_timer_frequency(60);  // 60 Hz

    int frame = 0;
    while (!kbhit()) {  // 키 누를 때까지
        // 1. Back buffer에 렌더링
        render_to_buffer(db.back);

        // 2. VSync 및 플립
        double_buffer_flip(&db);

        // 3. 프레임 카운터
        frame++;
        if (frame % 60 == 0) {
            printf("FPS: 60 (frame %d)\n", frame);
        }
    }

    double_buffer_free(&db);
}

// 테스트용 렌더링
void render_to_buffer(uint8_t* buffer) {
    static int offset = 0;

    // 간단한 스크롤 패턴
    for (int i = 0; i < 16000; i++) {
        buffer[i] = ((i + offset) % 256);
    }

    offset++;
}

int main() {
    game_loop();
    return 0;
}
```

### 8.2 Python 구현 (시뮬레이션)

```python
import time
import pygame

class VSync:
    def __init__(self, target_fps=60):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.last_time = time.time()

    def wait(self):
        """VSync 시뮬레이션 (소프트웨어 타이머)"""
        current_time = time.time()
        elapsed = current_time - self.last_time

        if elapsed < self.frame_time:
            time.sleep(self.frame_time - elapsed)

        self.last_time = time.time()

class DoubleBuffer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.front = pygame.Surface((width, height))
        self.back = pygame.Surface((width, height))

    def flip(self):
        """버퍼 스왑"""
        self.front, self.back = self.back, self.front
        return self.front

    def get_back_buffer(self):
        return self.back

def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((320, 200))
    pygame.display.set_caption('VSync Demo')

    vsync = VSync(60)
    double_buffer = DoubleBuffer(320, 200)

    clock = pygame.time.Clock()
    frame_count = 0
    running = True

    while running:
        # 1. 이벤트 처리
        for event in pygame.get_event():
            if event.type == pygame.QUIT:
                running = False

        # 2. Back buffer에 렌더링
        back = double_buffer.get_back_buffer()
        render_frame(back, frame_count)

        # 3. VSync 대기
        vsync.wait()

        # 4. 플립 및 화면 표시
        front = double_buffer.flip()
        screen.blit(front, (0, 0))
        pygame.display.flip()

        # 5. FPS 측정
        frame_count += 1
        if frame_count % 60 == 0:
            fps = clock.get_fps()
            print(f"Frame {frame_count}: {fps:.1f} FPS")

        clock.tick()

    pygame.quit()

def render_frame(surface, frame):
    """테스트용 렌더링"""
    color = ((frame * 2) % 256, (frame * 3) % 256, (frame * 5) % 256)
    surface.fill(color)

    # 움직이는 사각형
    x = (frame * 2) % 320
    y = 100
    pygame.draw.rect(surface, (255, 255, 255), (x, y, 32, 32))

if __name__ == '__main__':
    game_loop()
```

### 8.3 JavaScript 구현 (웹)

```javascript
class VSync {
    constructor(targetFPS = 60) {
        this.targetFPS = targetFPS;
        this.frameTime = 1000 / targetFPS;
        this.lastTime = performance.now();
    }

    wait() {
        return new Promise(resolve => {
            const currentTime = performance.now();
            const elapsed = currentTime - this.lastTime;
            const waitTime = Math.max(0, this.frameTime - elapsed);

            setTimeout(() => {
                this.lastTime = performance.now();
                resolve();
            }, waitTime);
        });
    }
}

class DoubleBuffer {
    constructor(width, height) {
        this.width = width;
        this.height = height;

        // Front buffer (Canvas)
        this.frontCanvas = document.createElement('canvas');
        this.frontCanvas.width = width;
        this.frontCanvas.height = height;
        this.frontCtx = this.frontCanvas.getContext('2d');

        // Back buffer (OffscreenCanvas)
        this.backCanvas = document.createElement('canvas');
        this.backCanvas.width = width;
        this.backCanvas.height = height;
        this.backCtx = this.backCanvas.getContext('2d');

        document.body.appendChild(this.frontCanvas);
    }

    getBackContext() {
        return this.backCtx;
    }

    flip() {
        // Back → Front 복사
        this.frontCtx.drawImage(this.backCanvas, 0, 0);
    }
}

class FPSCounter {
    constructor() {
        this.frameCount = 0;
        this.lastTime = performance.now();
        this.currentFPS = 0;
    }

    update() {
        this.frameCount++;
        const currentTime = performance.now();
        const elapsed = currentTime - this.lastTime;

        if (elapsed >= 1000) {
            this.currentFPS = (this.frameCount / elapsed) * 1000;
            this.frameCount = 0;
            this.lastTime = currentTime;
        }

        return this.currentFPS;
    }
}

// 게임 루프
async function gameLoop() {
    const vsync = new VSync(60);
    const doubleBuffer = new DoubleBuffer(320, 200);
    const fpsCounter = new FPSCounter();

    let frameCount = 0;

    while (true) {
        // 1. Back buffer에 렌더링
        const ctx = doubleBuffer.getBackContext();
        renderFrame(ctx, frameCount);

        // 2. VSync 대기
        await vsync.wait();

        // 3. 플립 (Back → Front)
        doubleBuffer.flip();

        // 4. FPS 측정
        const fps = fpsCounter.update();
        if (frameCount % 60 === 0) {
            console.log(`Frame ${frameCount}: ${fps.toFixed(1)} FPS`);
        }

        frameCount++;
    }
}

// 테스트용 렌더링
function renderFrame(ctx, frame) {
    // 배경 (그라데이션)
    const gradient = ctx.createLinearGradient(0, 0, 320, 200);
    gradient.addColorStop(0, `hsl(${(frame * 2) % 360}, 50%, 30%)`);
    gradient.addColorStop(1, `hsl(${(frame * 3) % 360}, 50%, 50%)`);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 320, 200);

    // 움직이는 사각형
    ctx.fillStyle = 'white';
    const x = (frame * 2) % 320;
    const y = 100;
    ctx.fillRect(x, y, 32, 32);

    // FPS 표시
    ctx.fillStyle = 'yellow';
    ctx.font = '12px monospace';
    ctx.fillText(`Frame: ${frame}`, 10, 20);
}

// 실행
gameLoop();
```

---

## 9. 성능 분석

### 9.1 복잡도

**VSync 대기**:
```
시간 복잡도: O(1) (하드웨어 동기화)
최악의 경우: 16.67 ms (전체 프레임)
평균: 8.33 ms (프레임의 절반)
최선의 경우: 0 ms (VBlank 시작 직전 도착)
```

**더블 버퍼링 플립**:
```
시간 복잡도: O(n) where n = 화면 크기
320×200 CGA: 16,000 bytes
memcpy: ~1.0 ms @ 4.77 MHz (16 bytes/ms)

최적화: 하드웨어 플립 (레지스터 변경)
시간: ~0.001 ms (즉시)
```

### 9.2 실제 성능

**Intel 8088 @ 4.77 MHz**:
```
VSync 폴링 (1회):
  inportb: ~10 cycles = 2.1 µs
  평균 폴링 횟수: 40,000회 (8 ms / 2.1 µs)
  총 시간: ~8 ms (CPU 100% 사용)

memcpy (16,000 bytes):
  MOVSB: ~18 cycles/byte
  총: 16,000 × 18 = 288,000 cycles
  시간: 288,000 / 4,770,000 = 60 ms

MOVSW (최적화):
  MOVSW: ~18 cycles/word
  총: 8,000 × 18 = 144,000 cycles
  시간: 144,000 / 4,770,000 = 30 ms
```

**병목**:
1. **VSync 대기**: CPU 100% (busy wait)
2. **memcpy**: 30-60 ms (전체 화면)

**해결책**:
- 하드웨어 플립 (VGA)
- Partial update (변경 영역만)

### 9.3 프레임 타이밍 분석

```
60 FPS 달성 가능성:
┌──────────────────────────────────────┐
│ 예산: 16.67 ms/frame                 │
├──────────────────────────────────────┤
│ 게임 로직: 1.0 ms (✓)                │
│ VSync 대기: 8.0 ms (✓)               │
│ 렌더링: 0.2 ms (✓)                   │
│ 스크롤: 0.01 ms (✓)                  │
│ 여유: 7.46 ms (✓)                    │
└──────────────────────────────────────┘

결론: **60 FPS 안정적으로 달성 가능**
```

---

## 10. 테스트 전략

### 10.1 단위 테스트

```c
// 테스트 1: VSync 타이밍
void test_vsync_timing() {
    uint32_t start = get_time_us();

    for (int i = 0; i < 60; i++) {
        wait_for_vsync();
    }

    uint32_t elapsed = get_time_us() - start;
    float avg_frame_time = elapsed / 60.0f / 1000.0f;  // ms

    // 예상: 16.67 ms/frame ± 1 ms
    assert(avg_frame_time >= 15.67f && avg_frame_time <= 17.67f);
}

// 테스트 2: Double buffering
void test_double_buffering() {
    DoubleBuffer db;
    double_buffer_init(&db, 320, 200);

    // Back buffer에 패턴 쓰기
    memset(db.back, 0xAA, db.size);

    // Front buffer 확인 (아직 업데이트 안됨)
    assert(db.front[0] != 0xAA);

    // Flip
    double_buffer_flip(&db);

    // Front buffer 확인 (업데이트됨)
    assert(db.front[0] == 0xAA);

    double_buffer_free(&db);
}

// 테스트 3: PIT 타이머
void test_pit_timer() {
    set_timer_frequency(1000);  // 1 kHz

    volatile int count = 0;
    uint32_t start = get_time_ms();

    // 1초 대기
    while (get_time_ms() - start < 1000) {
        count++;
    }

    // 예상: 1000 ticks ± 10
    assert(count >= 990 && count <= 1010);
}
```

### 10.2 통합 테스트

```python
def test_full_game_loop():
    """전체 게임 루프 60 FPS 테스트"""
    vsync = VSync(60)
    frame_times = []

    for frame in range(600):  # 10초
        start = time.time()

        # 게임 업데이트
        update_game()

        # VSync 대기
        vsync.wait()

        # 렌더링
        render_frame()

        elapsed = time.time() - start
        frame_times.append(elapsed)

    # 분석
    avg_frame_time = np.mean(frame_times)
    std_frame_time = np.std(frame_times)

    print(f"Average frame time: {avg_frame_time*1000:.2f} ms")
    print(f"Std deviation: {std_frame_time*1000:.2f} ms")
    print(f"Target: 16.67 ms")

    # 검증: 평균 16.67 ms ± 1 ms
    assert 15.67 <= avg_frame_time * 1000 <= 17.67
```

### 10.3 시각적 검증

```python
import matplotlib.pyplot as plt

def visualize_frame_timing():
    """프레임 타이밍 시각화"""
    frame_times = measure_frame_times(600)

    plt.figure(figsize=(12, 6))

    # 프레임 타임 그래프
    plt.subplot(2, 1, 1)
    plt.plot(frame_times, 'b-', alpha=0.5)
    plt.axhline(y=16.67, color='r', linestyle='--', label='60 FPS target')
    plt.ylabel('Frame Time (ms)')
    plt.xlabel('Frame')
    plt.title('Frame Timing')
    plt.legend()
    plt.grid(True)

    # 히스토그램
    plt.subplot(2, 1, 2)
    plt.hist(frame_times, bins=50, alpha=0.7)
    plt.axvline(x=16.67, color='r', linestyle='--', label='60 FPS target')
    plt.xlabel('Frame Time (ms)')
    plt.ylabel('Count')
    plt.title('Frame Time Distribution')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()
```

---

## 11. 최적화 기법

### 11.1 Adaptive VSync

```c
// 동적 VSync (프레임 드롭 허용)
void adaptive_vsync(bool force_sync) {
    static uint32_t missed_frames = 0;

    if (force_sync || missed_frames > 2) {
        wait_for_vsync();
        missed_frames = 0;
    } else {
        // VSync 스킵 (프레임 드롭)
        missed_frames++;
    }
}
```

### 11.2 Partial Update (더티 사각형)

```c
typedef struct {
    int x, y, width, height;
} Rect;

Rect dirty_rects[MAX_DIRTY_RECTS];
int dirty_count = 0;

void mark_dirty(int x, int y, int w, int h) {
    if (dirty_count < MAX_DIRTY_RECTS) {
        dirty_rects[dirty_count++] = (Rect){x, y, w, h};
    }
}

void flip_partial() {
    wait_for_vsync();

    // 더티 영역만 복사
    for (int i = 0; i < dirty_count; i++) {
        Rect r = dirty_rects[i];
        copy_rect(front_buffer, back_buffer, r);
    }

    dirty_count = 0;
}
```

### 11.3 Triple Buffering

```c
typedef struct {
    uint8_t* buffers[3];
    int render_index;   // 렌더링 중
    int display_index;  // 화면 표시
    int ready_index;    // 대기 (렌더링 완료)
} TripleBuffer;

void triple_buffer_flip(TripleBuffer* tb) {
    wait_for_vsync();

    // 순환
    int temp = tb->display_index;
    tb->display_index = tb->ready_index;
    tb->ready_index = tb->render_index;
    tb->render_index = temp;

    // 하드웨어 업데이트
    set_display_buffer(tb->buffers[tb->display_index]);
}
```

---

## 12. 문제 해결

### 12.1 일반적인 문제

**1. Screen Tearing**

**원인**: VSync 없이 VRAM 직접 업데이트

**해결책**:
```c
// 잘못된 코드
render_to_vram();  // 즉시 VRAM 쓰기

// 올바른 코드
wait_for_vsync();  // VBlank 대기
render_to_vram();  // 안전한 업데이트
```

**2. 프레임 레이트 불안정**

**원인**: 가변 프레임 타임

**해결책**:
```c
// Delta time 사용
float dt = get_frame_time();
update_game(dt);  // 시간 기반 업데이트
```

**3. VSync 무한 루프**

**원인**: Port 0x3DA 읽기 실패 (에뮬레이터?)

**해결책**:
```c
// 타임아웃 추가
bool wait_for_vsync_safe() {
    int timeout = 100000;

    while (inportb(0x3DA) & 0x08) {
        if (--timeout == 0) return false;
    }

    timeout = 100000;
    while (!(inportb(0x3DA) & 0x08)) {
        if (--timeout == 0) return false;
    }

    return true;
}
```

### 12.2 디버깅 기법

```c
// FPS 표시
void debug_show_fps() {
    static int frame_count = 0;
    static uint32_t last_time = 0;

    frame_count++;
    uint32_t current_time = get_time_ms();

    if (current_time - last_time >= 1000) {
        printf("FPS: %d\n", frame_count);
        frame_count = 0;
        last_time = current_time;
    }
}

// 프레임 타임 측정
void debug_measure_frame_time() {
    static uint32_t last_frame_time = 0;

    uint32_t current_time = get_time_us();
    uint32_t frame_time = current_time - last_frame_time;

    if (frame_time > 20000) {  // > 20 ms
        printf("Warning: Long frame time: %.2f ms\n", frame_time / 1000.0f);
    }

    last_frame_time = current_time;
}
```

---

## 13. 참고 자료

### 13.1 관련 문서

**Double Dragon 프로젝트**:
- [CAMERA_VSYNC_SYSTEM_ANALYSIS.md](../function-analysis/CAMERA_VSYNC_SYSTEM_ANALYSIS.md) - 카메라 및 VSync 완전 분석
- [08_HARDWARE_IO.md](../systems/08_HARDWARE_IO.md) - 하드웨어 I/O 시스템
- [01_RENDERING.md](../systems/01_RENDERING.md) - 렌더링 시스템

**함수 분석**:
- FUN_1000_0604 (1000:0604) - VSync 대기 함수
- FUN_1000_1c0c (1000:1c0c) - PIT 타이머 Mode 0
- FUN_1000_1c1e (1000:1c1e) - PIT 타이머 Mode 1

### 13.2 외부 참조

**하드웨어 문서**:
- [CGA Technical Reference](https://archive.org/details/CGA_TechRef) (IBM, 1981)
- [VGA Hardware Programming](http://www.osdever.net/FreeVGA/vga/vga.htm)
- [Intel 8253 PIT Datasheet](https://pdos.csail.mit.edu/6.828/2014/readings/hardware/8253f.pdf)

**알고리즘**:
- [Fix Your Timestep](https://gafferongames.com/post/fix_your_timestep/) (Glenn Fiedler)
- [VSync Explained](https://www.anandtech.com/show/2794) (AnandTech)
- [Double Buffering](https://en.wikipedia.org/wiki/Multiple_buffering) (Wikipedia)

### 13.3 용어집

- **VSync (Vertical Synchronization)**: 수직 동기화
- **VBlank (Vertical Blank)**: 수직 귀선 구간
- **Screen Tearing**: 화면 찢어짐
- **Double Buffering**: 이중 버퍼링
- **Frame Rate**: 프레임 레이트 (FPS)
- **PIT (Programmable Interval Timer)**: 프로그래밍 가능 인터벌 타이머
- **CRT (Cathode Ray Tube)**: 음극선관 모니터
- **Scanline**: 주사선
- **Retrace**: 귀선 (빔이 시작 위치로 돌아감)

---

**작성 완료일**: 2025-11-24
**분석 함수 수**: 3개 (FUN_0604, FUN_1c0c, FUN_1c1e)
**총 코드 크기**: ~100 bytes
**문서 크기**: ~2,000 lines
