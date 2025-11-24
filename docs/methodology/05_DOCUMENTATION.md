# 문서화 방법론

**목적**: 리버스 엔지니어링 분석 결과를 효과적으로 문서화하여, 이해 가능하고 재사용 가능한 지식으로 만드는 방법을 설명합니다.

**대상 독자**:
- 분석 결과를 체계적으로 정리하려는 리버스 엔지니어
- 팀과 분석 지식을 공유해야 하는 개발자
- 다른 DOS 게임 프로젝트에 방법론을 적용하려는 사람

**소요 시간**: Phase 2-4 동안 지속적 (전체 작업의 ~30%)

---

## 📋 목차

1. [문서화 철학](#문서화-철학)
2. [문서 구조](#문서-구조)
3. [함수 분석 문서화](#함수-분석-문서화)
4. [시스템 분석 문서화](#시스템-분석-문서화)
5. [메모리 맵 문서화](#메모리-맵-문서화)
6. [Markdown 모범 사례](#markdown-모범-사례)
7. [버전 관리](#버전-관리)
8. [워크플로우](#워크플로우)

---

## 💡 문서화 철학

### 핵심 원칙

**1. 즉시 문서화 (Document Immediately)**
```
❌ 나쁜 방식:
  함수 10개 분석 → (기억에 의존) → 나중에 문서 작성
  문제: 세부사항 망각, 불완전한 기록

✅ 좋은 방식:
  함수 1개 분석 → 즉시 문서 작성 → 다음 함수
  효과: 완전한 기록, 컨텍스트 보존
```

**통계**: Double Dragon에서 즉시 문서화 시 재작성 시간 70% 감소

---

**2. 미래의 자신을 위해 (Write for Future You)**
```
3개월 후 이 코드를 다시 볼 때:
- 이 함수가 왜 중요한가?
- 어떻게 동작하는가?
- 다른 시스템과 어떤 관계인가?
- 엣지 케이스는 무엇인가?

→ 이 질문들에 답하는 문서 작성
```

---

**3. 계층적 정보 구조 (Hierarchical Information)**
```
README (1분)
  ↓ 더 알고 싶으면
시스템 개요 (5분)
  ↓ 더 알고 싶으면
상세 함수 분석 (30분)
  ↓ 더 알고 싶으면
디컴파일 코드 (2시간)
```

**목표**: 각 레벨에서 독립적으로 이해 가능

---

**4. 코드보다 의도 (Intent over Code)**
```
❌ 나쁜 문서:
  "이 함수는 0x16c6에서 값을 읽고 AX 레지스터에 넣습니다."
  → 코드 그대로 설명 (의미 없음)

✅ 좋은 문서:
  "플레이어 1의 체력(0x16c6+6)을 읽어 생존 여부를 판단합니다."
  → 의도와 맥락 설명
```

---

**5. 실행 가능한 문서 (Actionable Documentation)**
```
독자가 할 수 있어야 하는 것:
1. 시스템 이해하기
2. 해당 부분 재구현하기
3. 버그 찾기
4. 다른 게임에 동일 기법 적용하기

→ 추상적 설명만으로는 부족, 구체적 예시 필수
```

---

### Double Dragon 문서화 통계

| 항목 | 값 | 비고 |
|------|-----|------|
| 총 문서 수 | 72+ | Phase 0-4 |
| 총 라인 수 | ~40,000 | Markdown |
| Phase 4 문서 | 14개 | 18,096줄 |
| 평균 문서 크기 | 1,292줄 | Phase 4 기준 |
| 함수당 문서 | 112줄 | 디컴파일 포함 |
| 문서 작성 시간 | ~6시간 | 전체 17시간 중 35% |

**인사이트**:
- 문서 작성 = 분석 시간의 ~35%
- 즉시 문서화 시 재작업 최소화
- 템플릿 사용으로 일관성 확보

---

## 📁 문서 구조

### Double Dragon 문서 계층

```
docs/
├── DOCUMENTATION_INDEX.md       # 📌 마스터 인덱스 (시작점)
├── PROGRESS.md                  # 진행 상황 추적
│
├── methodology/                 # 🎓 RE 방법론 (다른 프로젝트 재사용)
│   ├── README.md
│   ├── 01_PROCESS_OVERVIEW.md
│   ├── 02_TOOLS_AND_SETUP.md
│   ├── 03_DECOMPILATION.md
│   ├── 04_ANALYSIS_TECHNIQUES.md
│   ├── 05_DOCUMENTATION.md      # (이 문서)
│   └── 06_LESSONS_LEARNED.md
│
├── systems/                     # 🎮 게임 시스템 (언어 중립적)
│   ├── README.md
│   ├── 01_RENDERING.md
│   ├── 02_ENTITY_AI.md
│   ├── 03_ANIMATION.md
│   ├── 04_PHYSICS_COLLISION.md
│   ├── 05_INPUT_CAMERA.md
│   ├── 06_STAGE_LIFECYCLE.md
│   ├── 07_COMPRESSION.md
│   └── 08_HARDWARE_IO.md
│
├── algorithms/                  # 🔢 핵심 알고리즘 (의사코드)
│   ├── README.md
│   ├── RLE_COMPRESSION.md
│   ├── LZW_COMPRESSION.md
│   ├── SPRITE_BLITTING.md
│   ├── MANHATTAN_AI.md
│   └── VSYNC_TIMING.md
│
├── reference/                   # 📖 완전한 참조
│   ├── MEMORY_MAP.md            # 전체 메모리 맵
│   ├── FUNCTION_LIST.md         # 161개 함수 목록
│   ├── JUMP_TABLES.md           # 5개 점프 테이블
│   └── DATA_STRUCTURES.md       # 바이트 레벨 구조
│
└── archive/                     # 🗄️ 원본 분석 기록
    ├── phase4-analysis/         # Phase 4 원본 14개 문서
    ├── sessions/                # 세션별 작업 로그
    └── tools/                   # 도구 가이드
```

---

### 문서 유형별 목적

| 유형 | 목적 | 독자 | 예시 |
|------|------|------|------|
| **Index** | 전체 네비게이션 | 모든 사람 | DOCUMENTATION_INDEX.md |
| **Methodology** | 재사용 가능한 기법 | RE 학습자 | 04_ANALYSIS_TECHNIQUES.md |
| **System** | 게임 구조 이해 | 구현자 | 01_RENDERING.md |
| **Algorithm** | 언어 중립적 로직 | 구현자 | LZW_COMPRESSION.md |
| **Reference** | 완전한 데이터 | 디버거 | MEMORY_MAP.md |
| **Archive** | 분석 과정 기록 | 역사 추적 | ENTITY_SYSTEM_ANALYSIS.md |

---

## 📝 함수 분석 문서화

### 함수 분석 템플릿

```markdown
## FUN_1000_XXXX - [함수명]

**주소**: 1000:XXXX
**호출자**: N개 (주요: FUN_1000_YYYY)
**피호출자**: M개 (주요: FUN_1000_ZZZZ)
**복잡도**: [Low/Medium/High]
**카테고리**: [System Category]

### 목적
[한 문장으로 이 함수가 하는 일]

### 동작
[3-5 단락으로 상세 설명]

1. **초기화**: ...
2. **메인 로직**: ...
3. **종료**: ...

### 중요 메모리 주소
- `0x16c6`: Entity Array (7 slots × 24 bytes)
- `0x18c4`: Jump Table (11 entries)

### 의사코드
\```
function update_entity(entity_id):
  entity = ENTITY_ARRAY[entity_id]

  if entity.active:
    update_position(entity)
    check_collision(entity)
    update_animation(entity)
\```

### 엣지 케이스
- entity_id >= 7: 무시 (배열 범위 초과)
- entity.active == 0: 스킵
- 애니메이션 NULL: 기본 스프라이트 사용

### 호출 흐름
\```
main_loop (0a8b)
  └─> update_all_entities (3824)
       └─> update_entity (XXXX) ← 이 함수
            ├─> update_position (3265)
            ├─> check_collision (0e3f)
            └─> update_animation (1930)
\```

### 관련 함수
- `FUN_1000_3824`: 엔티티 배치 업데이트
- `FUN_1000_3265`: 위치 업데이트
- `FUN_1000_0e3f`: 충돌 검사

### 디컴파일 코드
\```c
void FUN_1000_XXXX(byte entity_id) {
  // [Ghidra 디컴파일 결과]
  ...
}
\```

### 분석 노트
- [2025-01-20] 초기 분석: 엔티티 업데이트로 추정
- [2025-01-22] 호출 그래프 확인: 초당 60회 호출 (메인 루프)
- [2025-01-24] 완전 분석: 7개 엔티티 순회 확인
```

---

### 실제 예시: FUN_1000_0a8b (Main Loop)

```markdown
## FUN_1000_0a8b - Main Game Loop

**주소**: 1000:0a8b
**호출자**: 1개 (FUN_1000_0000 - Entry Point)
**피호출자**: 47개 (거의 모든 시스템)
**복잡도**: High
**카테고리**: Game Loop

### 목적
게임의 메인 루프. 매 프레임마다 입력, 물리, AI, 렌더링을 순차 처리합니다.

### 동작

1. **입력 처리** (0x0a8b-0x0a9f)
   - 키보드 스캔코드 읽기 (Port 0x60)
   - 조이스틱 입력 읽기 (Port 0x201)
   - 2P 입력 병합

2. **게임 로직** (0x0aa0-0x0b8f)
   - 엔티티 업데이트 (플레이어 + 적 7명)
   - 물리 시뮬레이션 (중력, 충돌)
   - AI 결정 (맨하탄 거리 기반)
   - 투사체 업데이트 (최대 6개)

3. **카메라** (0x0b90-0x0bb0)
   - 플레이어 위치 기반 스크롤
   - 바운딩 박스 계산 (2P 협동 시)

4. **렌더링** (0x0bb1-0x0c2f)
   - 백그라운드 스크롤
   - Depth-sorted 스프라이트 블리팅
   - UI 렌더링 (체력, 스코어)

5. **VSync** (0x0c30-0x0c35)
   - Port 0x3DA 폴링 (수직 동기화)
   - 60 FPS 타이밍 보장

### 실행 흐름 (간략)
\```
loop forever:
  read_input()           # 10ms
  update_entities()      # 5ms
  update_physics()       # 3ms
  update_ai()            # 2ms
  update_camera()        # 1ms
  render_all()           # 8ms
  wait_vsync()           # ~16.6ms (60 FPS)
  # 총 ~16.6ms/frame
\```

### 호출 빈도
- **초당 60회** (60 FPS)
- 게임 1분 = 3,600회 호출
- 테스트 플레이 5분 = 18,000회 호출

→ **가장 중요한 함수** (ExecutionFlow.json 분석)

### 성능 프로파일 (추정)
| 단계 | 비율 | 시간 (60 FPS) |
|------|------|---------------|
| 입력 | 10% | 1.0ms |
| 로직 | 30% | 3.0ms |
| 렌더링 | 50% | 5.0ms |
| VSync | 10% | 1.0ms |
| **합계** | 100% | **10ms** (나머지 6.6ms는 대기) |

### 의사코드
\```python
def main_game_loop():
  while not game_over:
    # 입력
    p1_input = read_keyboard()
    p2_input = read_joystick()

    # 게임 로직
    for entity in entity_array:
      if entity.active:
        update_entity(entity, p1_input, p2_input)
        apply_physics(entity)
        if entity.is_enemy:
          run_ai(entity)

    # 투사체
    for projectile in projectile_array:
      if projectile.active:
        update_projectile(projectile)
        check_projectile_collision(projectile)

    # 카메라
    camera_x = calculate_camera_position(player1, player2)

    # 렌더링
    clear_screen()
    render_background(camera_x)
    for entity in depth_sorted(entity_array):
      blit_sprite(entity.sprite, entity.x - camera_x, entity.y)
    render_ui()

    # 타이밍
    wait_for_vsync()
\```

### 관련 시스템
- **Input** (05_INPUT_CAMERA.md)
- **Entity AI** (02_ENTITY_AI.md)
- **Physics** (04_PHYSICS_COLLISION.md)
- **Rendering** (01_RENDERING.md)
- **Hardware I/O** (08_HARDWARE_IO.md)

### 분석 노트
- [2025-01-20] ExecutionFlow.json에서 최다 호출 확인
- [2025-01-22] 프레임 타이밍 측정: 평균 16.4ms (60.9 FPS)
- [2025-01-24] 전체 흐름 이해: 이 함수가 게임의 심장
```

---

## 🎮 시스템 분석 문서화

### 시스템 문서 템플릿

```markdown
# [시스템명]

**목적**: [한 문장으로 시스템 역할]

**관련 함수**: N개
**의존성**: [다른 시스템 목록]
**복잡도**: [⭐⭐⭐⭐⭐ 등급]

---

## 1. 개요

### 역할
[2-3 단락으로 시스템 설명]

### 주요 기능
1. 기능 A
2. 기능 B
3. 기능 C

### 시스템 다이어그램
\```
[입력] → [처리 단계] → [출력]
\```

---

## 2. 아키텍처

### 컴포넌트 구조
\```
Component A
  ├─ Subcomponent A1
  └─ Subcomponent A2
Component B
  └─ Subcomponent B1
\```

### 데이터 흐름
\```
Input → Buffer → Process → Output Buffer → Display
\```

---

## 3. 메모리 레이아웃

### 주요 메모리 영역
\```
0x16c6: Entity Array (7 × 24 bytes)
  [0] Player 1
    +0x00: Sprite Pointer (2 bytes)
    +0x02: X Position (2 bytes)
    +0x04: Y Position (2 bytes)
    +0x06: Health (2 bytes)
    ...
\```

### 점프 테이블 (해당 시)
\```
0x18c4: Render Dispatcher (11 entries)
  [0] @ 0x28c0: Blit Sprite
  [1] @ 0x28ef: Blit with Mask
  ...
\```

---

## 4. 핵심 알고리즘

### 알고리즘 1: [이름]
\```
function algorithm_name(input):
  step 1
  step 2
  return output
\```

**복잡도**: O(n)
**설명**: ...

---

## 5. 함수 목록

| 주소 | 함수명 | 역할 | 복잡도 |
|------|--------|------|--------|
| 1000:28c0 | Blit Sprite | 스프라이트 그리기 | High |
| 1000:28ef | Blit Masked | 마스크 블리팅 | High |
| ... | ... | ... | ... |

**함수 간 호출 관계**:
\```
FUN_1000_28c0 (main)
  ├─> FUN_1000_28ef (masked)
  └─> FUN_1000_293e (clipping)
\```

---

## 6. 구현 가이드

### 언어 중립적 접근
[의사코드 중심으로 구현 가이드]

### 최적화 포인트
1. ...
2. ...

### 함정 (Pitfalls)
1. ...
2. ...

---

## 7. 테스트 전략

### 단위 테스트
- 테스트 케이스 1: ...
- 테스트 케이스 2: ...

### 통합 테스트
- 다른 시스템과의 상호작용 검증

---

## 8. 참고

### 관련 문서
- [../algorithms/SPRITE_BLITTING.md](../algorithms/SPRITE_BLITTING.md)
- [../reference/MEMORY_MAP.md](../reference/MEMORY_MAP.md)

### 원본 분석
- [../archive/phase4-analysis/RENDERING_SYSTEM_ANALYSIS.md]

### 외부 참조
- CGA Graphics: https://en.wikipedia.org/wiki/Color_Graphics_Adapter
```

---

## 🗺️ 메모리 맵 문서화

### 메모리 맵 포맷

```markdown
# 메모리 맵

## 세그먼트 개요

| 세그먼트 | 시작 | 끝 | 크기 | 용도 |
|----------|------|-----|------|------|
| CODE (1000h) | 1000:0000 | 1000:8fff | 36 KB | 실행 코드 |
| DATA (2000h) | 2000:0000 | 2000:4fff | 20 KB | 데이터 |
| STACK (3000h) | 3000:0000 | 3000:0fff | 4 KB | 스택 |

---

## 주요 메모리 영역

### 0x16c6 - Entity Array
\```
Offset: 0x16c6
Size: 168 bytes (7 slots × 24 bytes)
Format:
  [0] Player 1 (24 bytes)
    +0x00: word sprite_pointer
    +0x02: word x_position
    +0x04: word y_position
    +0x06: word health
    +0x08: byte animation_frame
    +0x09: byte direction (0=right, 1=left)
    +0x0a: byte state
    +0x0b: byte flags
    +0x0c: word velocity_x
    +0x0e: word velocity_y
    +0x10: word ai_state
    +0x12: word ai_target
    +0x14: dword animation_timer
  [1] Player 2 (24 bytes)
  [2-6] Enemies (24 bytes each)
\```

**사용처**:
- FUN_1000_3824: 엔티티 업데이트
- FUN_1000_3265: 위치 계산
- FUN_1000_3384: AI 타겟 선택

**검증 방법**:
\```bash
# DOSBox-X 디버거
d 16c6:0000 00a8  # 168 bytes 덤프
\```

---

### 0x18c4 - Render Dispatch Table
\```
Offset: 0x18c4
Size: 22 bytes (11 entries × 2 bytes)
Format: Array of function pointers
  [0] @ 0x28c0: Blit Sprite (Direct)
  [1] @ 0x28ef: Blit Sprite (Masked)
  [2] @ 0x293e: Blit Sprite (Clipped)
  [3] @ 0x2965: Blit Sprite (Wrapped)
  [4] @ 0x29a8: Blit Tile
  [5] @ 0x29e1: Clear Region
  [6] @ 0x2a12: Fill Region
  [7] @ 0x2a3f: Draw Line
  [8] @ 0x2a7c: Draw Rectangle
  [9] @ 0x2ab9: Scroll Background
  [10] @ 0x2af6: Copy Buffer
\```

**사용처**:
- FUN_1000_2116: 디스패처 (간접 호출)

**예시 호출**:
\```c
// 0x2116에서
word func_index = 3;  // Clipped blit
word func_ptr = *(word*)(0x18c4 + func_index * 2);
call_function(func_ptr);  // → 0x2965
\```

---

## 비트 플래그

### Entity Flags (offset +0x0b)
\```
Bit 0 (0x01): Active
Bit 1 (0x02): Visible
Bit 2 (0x04): Player Control
Bit 3 (0x08): Enemy
Bit 4 (0x10): Invincible
Bit 5 (0x20): Attacking
Bit 6 (0x40): Hit Stun
Bit 7 (0x80): Dead
\```

**사용 예시**:
\```c
if (entity.flags & 0x01) {  // Active?
  if (entity.flags & 0x08) {  // Enemy?
    run_ai(entity);
  }
}
\```
```

---

## 📐 Markdown 모범 사례

### 1. 헤더 계층 사용

```markdown
✅ 좋은 예:
# 문서 제목 (H1 - 한 번만)

## 주요 섹션 (H2)

### 하위 섹션 (H3)

#### 세부 항목 (H4)

❌ 나쁜 예:
### 이것
### 저것
### 또 다른 것
(계층 없음, 평평한 구조)
```

---

### 2. 코드 블록 언어 지정

```markdown
✅ 좋은 예:
\```python
def foo():
    return 42
\```

\```c
void bar(int x) {
    printf("%d", x);
}
\```

❌ 나쁜 예:
\```
def foo():
    return 42
\```
(언어 미지정 → 하이라이팅 없음)
```

---

### 3. 테이블 정렬

```markdown
✅ 좋은 예:
| 함수 | 주소 | 크기 |
|------|------|------|
| main | 0a8b | 456 |
| blit | 28c0 | 127 |

❌ 나쁜 예:
|함수|주소|크기|
|---|---|---|
|main|0a8b|456|
(가독성 낮음, 정렬 없음)
```

---

### 4. 링크 사용

```markdown
✅ 좋은 예:
자세한 내용은 [렌더링 시스템](../systems/01_RENDERING.md)을 참조하세요.

❌ 나쁜 예:
자세한 내용은 ../systems/01_RENDERING.md 파일을 보세요.
(클릭 불가능한 일반 텍스트)
```

---

### 5. 목록 들여쓰기

```markdown
✅ 좋은 예:
1. 첫 번째
   - 하위 항목 A
   - 하위 항목 B
2. 두 번째
   a. 세부 항목
   b. 세부 항목

❌ 나쁜 예:
1. 첫 번째
- 하위 항목 A (들여쓰기 없음)
- 하위 항목 B
2. 두 번째
```

---

### 6. 이미지/다이어그램

```markdown
✅ 좋은 예:
\```
[Input] → [Process] → [Output]
   ↓         ↓           ↓
 Buffer    Logic      Display
\```

또는:
![Architecture](./diagrams/architecture.png)

❌ 나쁜 예:
입력이 처리되고 출력됩니다. (다이어그램 없음)
```

---

### 7. 경고/노트 블록

```markdown
✅ 좋은 예:
**⚠️ 주의**: 이 함수는 스택을 오버플로우할 수 있습니다.

**💡 팁**: 타임아웃을 증가시켜 보세요.

**📌 중요**: 반드시 VSync 후에 호출하세요.

❌ 나쁜 예:
주의: 이 함수는 위험합니다.
(강조 없음, 시각적 구분 없음)
```

---

## 🔄 버전 관리

### Git 커밋 전략

**규칙**:
```bash
# Phase 단위 커밋 (큰 마일스톤)
git commit -m "Phase 1 완료: 161개 함수 디컴파일"

# 문서 단위 커밋 (중간)
git commit -m "Docs: ENTITY_SYSTEM_ANALYSIS.md 추가 (18개 함수)"

# 함수 분석 커밋 (작은 단위)
git commit -m "Analysis: FUN_1000_0a8b (Main Loop) 완료"
```

**커밋 메시지 포맷**:
```
[타입]: [요약] ([상세])

타입:
- Phase: Phase 0-4 마일스톤
- Docs: 문서 추가/수정
- Analysis: 함수 분석
- Fix: 오류 수정
- Refactor: 문서 재구성

예시:
Phase 2: 코드 분석 및 분류 완료
- 118개 함수 8개 카테고리 분류
- function_categorization.md 작성
- 각 카테고리별 README 추가
```

---

### 브랜치 전략 (선택)

```bash
main          # 완료된 Phase만
├─ phase1     # Phase 1 작업 브랜치
├─ phase2     # Phase 2 작업 브랜치
├─ phase3     # Phase 3 작업 브랜치
└─ phase4     # Phase 4 작업 브랜치

# Phase 완료 후 merge
git checkout main
git merge phase2
git tag "Phase2-Complete"
```

---

### 문서 버전 관리

```markdown
<!-- 문서 하단에 메타데이터 -->

---

**작성일**: 2025-01-24
**최종 수정**: 2025-01-25
**버전**: 1.2
**작성자**: [이름]

**변경 이력**:
- v1.2 (2025-01-25): 함수 3개 추가 분석
- v1.1 (2025-01-24): 메모리 맵 수정
- v1.0 (2025-01-20): 초기 작성
```

---

## 🔁 워크플로우

### Phase 2-4 문서화 흐름

```
1. 함수 분석
   ↓
2. 즉시 Markdown 작성 (템플릿 사용)
   ↓
3. 관련 함수 링크 추가
   ↓
4. Git 커밋 (함수 단위)
   ↓
5. 10-20개 함수 완료 시:
   a. 시스템 문서 작성/업데이트
   b. PROGRESS.md 업데이트
   c. Git 커밋 (문서 단위)
   ↓
6. Phase 완료 시:
   a. 전체 검토
   b. README 업데이트
   c. Git tag 생성
```

---

### 일일 워크플로우 (실제 Double Dragon)

```
08:00 - 시작
  ├─ PROGRESS.md 확인 (어디까지 했나?)
  ├─ 오늘 목표 설정 (함수 10개)
  └─ Git pull (팀 작업 시)

08:10 - 함수 분석 시작
  ├─ 함수 1개 분석 (30분)
  ├─ 즉시 문서 작성 (10분)
  ├─ Git 커밋
  └─ 반복 × 10개

14:00 - 점심 휴식

15:00 - 시스템 문서 작성
  ├─ 오전 분석한 10개 함수 통합
  ├─ 시스템 개요 작성 (1시간)
  ├─ 다이어그램 추가
  └─ Git 커밋

17:00 - 검토 및 정리
  ├─ 오늘 작성한 문서 재읽기
  ├─ 링크 확인
  ├─ PROGRESS.md 업데이트
  └─ Git push

17:30 - 종료
```

---

### 자동화 스크립트

```python
#!/usr/bin/env python3
# create_function_doc.py
"""
함수 분석 문서 템플릿 자동 생성
"""

import sys
from pathlib import Path

TEMPLATE = """## FUN_1000_{addr} - [함수명 입력]

**주소**: 1000:{addr}
**호출자**: N개 (주요: )
**피호출자**: M개 (주요: )
**복잡도**: [Low/Medium/High]
**카테고리**: [System]

### 목적
[한 문장 설명]

### 동작
[상세 설명]

### 의사코드
```
function name(params):
  ...
```

### 관련 함수
-

### 분석 노트
- [{date}] 초기 분석:
"""

def create_doc(addr: str):
    """함수 문서 템플릿 생성"""
    from datetime import date

    content = TEMPLATE.format(
        addr=addr,
        date=date.today().isoformat()
    )

    filename = f"FUN_1000_{addr}_analysis.md"
    Path(filename).write_text(content)
    print(f"Created: {filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_function_doc.py <addr>")
        print("Example: python create_function_doc.py 0a8b")
        sys.exit(1)

    create_doc(sys.argv[1])
```

사용:
```bash
python create_function_doc.py 0a8b
# → FUN_1000_0a8b_analysis.md 생성
```

---

## 📊 문서 품질 체크리스트

### 함수 문서 체크리스트

- [ ] 함수 목적이 한 문장으로 명확히 설명됨
- [ ] 동작이 3-5 단락으로 상세 설명됨
- [ ] 의사코드가 포함됨
- [ ] 중요 메모리 주소 명시됨
- [ ] 호출 관계가 명확함 (caller/callee)
- [ ] 엣지 케이스가 문서화됨
- [ ] 관련 함수 링크됨
- [ ] 디컴파일 코드 포함됨

### 시스템 문서 체크리스트

- [ ] 시스템 역할이 명확함
- [ ] 아키텍처 다이어그램 포함
- [ ] 메모리 레이아웃 문서화
- [ ] 핵심 알고리즘 의사코드
- [ ] 함수 목록 및 호출 관계
- [ ] 구현 가이드 (언어 중립적)
- [ ] 테스트 전략 제시
- [ ] 관련 문서 링크

### 전체 문서 체크리스트

- [ ] DOCUMENTATION_INDEX.md 존재
- [ ] README.md 각 디렉토리에 존재
- [ ] 문서 간 링크 동작
- [ ] Markdown 문법 올바름
- [ ] Git 커밋 이력 명확
- [ ] PROGRESS.md 최신 상태
- [ ] 모든 함수 문서화됨

---

## 💡 실전 팁

### Tip 1: 템플릿 활용

```bash
# 템플릿 디렉토리 생성
mkdir -p templates/

# 함수 분석 템플릿
templates/function_analysis_template.md

# 시스템 분석 템플릿
templates/system_analysis_template.md

# 사용 시 복사
cp templates/function_analysis_template.md docs/FUN_1000_0a8b.md
```

---

### Tip 2: 스니펫 활용 (VS Code)

```json
// .vscode/markdown.code-snippets
{
  "Function Analysis": {
    "prefix": "func",
    "body": [
      "## FUN_1000_$1 - $2",
      "",
      "**주소**: 1000:$1",
      "**호출자**: $3",
      "**피호출자**: $4",
      "**복잡도**: $5",
      "",
      "### 목적",
      "$6",
      "",
      "### 동작",
      "$0"
    ]
  }
}
```

사용: Markdown 파일에서 `func` 입력 후 Tab

---

### Tip 3: 문서 일관성 검증

```python
#!/usr/bin/env python3
# verify_docs.py
"""문서 일관성 검증"""

import sys
from pathlib import Path

def verify_function_doc(filepath):
    """함수 문서 필수 섹션 확인"""
    content = Path(filepath).read_text()

    required_sections = [
        "## FUN_1000_",
        "**주소**:",
        "### 목적",
        "### 동작",
    ]

    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)

    return missing

# 모든 함수 문서 검증
docs_dir = Path("docs/archive/phase4-analysis/")
for doc in docs_dir.glob("*_ANALYSIS.md"):
    missing = verify_function_doc(doc)
    if missing:
        print(f"❌ {doc.name}: Missing {missing}")
    else:
        print(f"✅ {doc.name}")
```

---

## 🎯 체크리스트

### Phase 2-4 문서화 완료 기준

- [ ] 모든 분석된 함수 문서화됨
- [ ] 시스템 문서 8개 작성됨
- [ ] 알고리즘 문서 5개 작성됨
- [ ] MEMORY_MAP.md 완성됨
- [ ] FUNCTION_LIST.md 완성됨
- [ ] DOCUMENTATION_INDEX.md 최신 상태
- [ ] 모든 문서 링크 동작 확인
- [ ] Git 커밋 이력 정리됨
- [ ] README 각 디렉토리에 존재

---

## 📚 다음 단계

문서화 완료 후:

1. **[06_LESSONS_LEARNED.md](06_LESSONS_LEARNED.md)** - 실수 및 교훈 정리
2. **[01_PROCESS_OVERVIEW.md](01_PROCESS_OVERVIEW.md)** - 전체 프로세스 복습
3. **Implementation** - 실제 구현 시작

---

## 🔗 참고 자료

### 내부 문서
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - 문서 전체 구조
- [PROGRESS.md](../PROGRESS.md) - 진행 상황 추적

### 외부 참조
- [GitHub Markdown Guide](https://docs.github.com/en/get-started/writing-on-github)
- [Markdown Cheatsheet](https://www.markdownguide.org/cheat-sheet/)

---

**작성일**: 2025-01-24
**버전**: 1.0
**검증 환경**: VS Code, GitHub, Markdown Preview

**다음 문서**: [06_LESSONS_LEARNED.md](06_LESSONS_LEARNED.md) - 실수 및 교훈
**이전 문서**: [04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md) - 분석 기법
