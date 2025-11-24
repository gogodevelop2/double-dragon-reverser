# Double Dragon 시스템 구조

**목적**: 게임을 구성하는 8개 핵심 시스템을 **언어 중립적**으로 설명하여, 어떤 프로그래밍 언어로든 재구현 가능하게 만듭니다.

---

## 📋 시스템 목록

### [01_RENDERING.md](01_RENDERING.md)
**렌더링 파이프라인**
- 5단계 렌더링 파이프라인
- Dual Mode: EGA (Mode 1) vs CGA (Mode 2)
- 4-plane 스프라이트 블리팅
- VRAM 래핑 처리
- Depth-sorted 렌더링

**관련 함수**: 29개
**원본 문서**: `RENDERING_SCROLLING_SYSTEM_ANALYSIS.md`, `RENDERING_HELPERS_ANALYSIS.md`, `MODE2_COMPLETE_ANALYSIS.md`

---

### [02_ENTITY_AI.md](02_ENTITY_AI.md)
**엔티티 시스템 + AI**
- 7-슬롯 엔티티 배열 (24 bytes/slot)
- Work Buffer 패턴
- 맨하탄 거리 기반 AI
- 애니메이션 매핑
- 엔티티 템플릿 시스템

**관련 함수**: 18개
**원본 문서**: `ENTITY_SYSTEM_ANALYSIS.md`, `FINAL_SYSTEMS_ANALYSIS.md` (AI 부분)

---

### [03_ANIMATION.md](03_ANIMATION.md)
**애니메이션 시스템**
- 4-방향 스프라이트 (40 bytes/frame)
- 링크드 리스트 애니메이션
- 프레임 시퀀스 관리
- 점프 테이블 @ 0x1930

**관련 함수**: 7개
**원본 문서**: `ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md`

---

### [04_PHYSICS_COLLISION.md](04_PHYSICS_COLLISION.md)
**물리 + 충돌 검사**
- 6-슬롯 프로젝타일 배열 (18 bytes/slot)
- 점프 테이블 @ 0x2264 (Physics)
- 점프 테이블 @ 0x0e3f (Collision)
- AABB 충돌 검사
- 투사체 궤적 계산

**관련 함수**: 12개
**원본 문서**: `INPUT_CAMERA_PHYSICS_ANALYSIS.md`, `ANIMATION_PROJECTILE_SYSTEM_ANALYSIS.md`

---

### [05_INPUT_CAMERA.md](05_INPUT_CAMERA.md)
**입력 처리 + 카메라**
- 키보드/조이스틱 입력
- 2-플레이어 협동 카메라
- 바운딩 박스 알고리즘
- 데드존 스크롤링
- 4-방향 스크롤

**관련 함수**: 11개
**원본 문서**: `INPUT_CAMERA_PHYSICS_ANALYSIS.md`, `CAMERA_VSYNC_SYSTEM_ANALYSIS.md`

---

### [06_STAGE_LIFECYCLE.md](06_STAGE_LIFECYCLE.md)
**스테이지 생명주기**
- 스테이지 초기화
- 플레이어 리스폰
- 스파이럴 스폰 알고리즘
- 게임 상태 관리
- BCD 스코어링

**관련 함수**: 15개
**원본 문서**: `STAGE_INIT_RESPAWN_ANALYSIS.md`, `GAME_STATE_SCORE_SOUND_ANALYSIS.md`

---

### [07_COMPRESSION.md](07_COMPRESSION.md)
**압축 시스템**
- RLE 압축 (스프라이트)
- LZW 압축 (에셋 파일)
- 압축 해제 알고리즘
- 매직 넘버: 0x9d1f (LZW)

**관련 함수**: 10개
**원본 문서**: `FINAL_SYSTEMS_ANALYSIS.md` (RLE), `STAGE_INIT_RESPAWN_ANALYSIS.md` (LZW)

---

### [08_HARDWARE_IO.md](08_HARDWARE_IO.md)
**하드웨어 I/O**
- PIT 타이머 (Mode 0/1 전환)
- VSync 동기화 (Port 0x3DA)
- DOS INT 21h 래퍼
- 조이스틱 입력 (Port 0x201)
- 3-계층 에러 처리

**관련 함수**: 15개
**원본 문서**: `SYSTEM_SERVICES_HARDWARE_IO_ANALYSIS.md`

---

## 🎯 문서 구조 (모든 시스템 공통)

각 시스템 문서는 다음 구조를 따릅니다:

```markdown
# 시스템 이름

## 1. 개요
- 목적 및 역할
- 주요 기능
- 시스템 간 관계

## 2. 아키텍처
- 컴포넌트 구조도
- 데이터 흐름
- 제어 흐름

## 3. 핵심 로직
- 알고리즘 설명 (의사코드)
- 처리 단계
- 엣지 케이스

## 4. 메모리 레이아웃
- 주요 메모리 주소
- 데이터 구조 (바이트 단위)
- 점프 테이블 (해당 시)

## 5. 함수 목록
- 관련 함수 전체 목록
- 함수 간 호출 관계
- 원본 Phase 4 문서 참조

## 6. 구현 시 고려사항
- 언어 무관 가이드
- 성능 최적화 팁
- 함정 (pitfalls)

## 7. 테스트 전략
- 검증 방법
- 테스트 케이스
- 예상 결과

## 8. 참고
- 원본 문서 링크
- 관련 알고리즘 링크
```

---

## 🔗 시스템 간 의존성

```
입력 (05)
  ↓
카메라 (05)
  ↓
엔티티 AI (02)
  ↓
물리/충돌 (04)
  ↓
애니메이션 (03)
  ↓
렌더링 (01)
  ↓
VSync (08)

병렬:
  스테이지 (06) ← 초기화/리스폰
  압축 (07) ← 에셋 로딩
  하드웨어 (08) ← 타이머/입력
```

---

## 📊 시스템별 복잡도

| 시스템 | 함수 수 | 복잡도 | 우선순위 |
|--------|---------|--------|----------|
| 07_COMPRESSION | 10 | ⭐⭐ | 1 (독립적) |
| 08_HARDWARE_IO | 15 | ⭐⭐ | 1 (독립적) |
| 06_STAGE_LIFECYCLE | 15 | ⭐⭐⭐ | 2 |
| 03_ANIMATION | 7 | ⭐⭐⭐ | 3 |
| 05_INPUT_CAMERA | 11 | ⭐⭐⭐⭐ | 4 |
| 02_ENTITY_AI | 18 | ⭐⭐⭐⭐ | 5 |
| 04_PHYSICS_COLLISION | 12 | ⭐⭐⭐⭐⭐ | 6 |
| 01_RENDERING | 29 | ⭐⭐⭐⭐⭐ | 7 (마지막) |

**권장 구현 순서**: 07 → 08 → 06 → 03 → 05 → 02 → 04 → 01

---

## 🧩 언어 중립성 원칙

### ✅ 사용하는 것
- **의사코드**: Python-like 구문
- **바이트 오프셋**: 메모리 주소 + 크기
- **추상 데이터 구조**: "배열", "링크드 리스트"
- **플로우차트**: 제어 흐름 다이어그램

### ❌ 사용하지 않는 것
- 특정 언어 구문 (C++, TypeScript, Rust 등)
- 언어별 타입 시스템 (int32_t, number, u32)
- 언어별 메모리 모델 (포인터, 참조)
- 언어별 라이브러리 (STL, Array.prototype)

### 예시: 좋은 문서

```markdown
## 엔티티 배열 구조

**메모리 레이아웃**:
```
Offset 0x16c6: Entity Array (7 slots × 24 bytes)
  [0] Player 1 (24 bytes)
    +0x00: Sprite Pointer (2 bytes)
    +0x02: X Position (2 bytes)
    +0x04: Y Position (2 bytes)
    +0x06: Health (2 bytes)
    ...
  [1] Player 2 (24 bytes)
  [2-6] Enemies (24 bytes each)
```

**의사코드**:
```
for each entity in entity_array:
  if entity.active:
    update_position(entity)
    check_collision(entity)
    update_animation(entity)
```
```

---

## 🔍 원본 문서 매핑

Phase 4 분석 → 시스템 문서 변환:

| Phase 4 문서 | 시스템 문서 | 변환 방법 |
|--------------|-------------|-----------|
| RENDERING_SCROLLING_SYSTEM | 01_RENDERING | 통합 |
| RENDERING_HELPERS | 01_RENDERING | 통합 |
| MODE2_COMPLETE | 01_RENDERING | 통합 |
| ENTITY_SYSTEM | 02_ENTITY_AI | 분할 (Entity) |
| FINAL_SYSTEMS (AI) | 02_ENTITY_AI | 분할 (AI) |
| ANIMATION_PROJECTILE | 03_ANIMATION | 분할 (Animation) |
| ANIMATION_PROJECTILE | 04_PHYSICS | 분할 (Projectile) |
| INPUT_CAMERA_PHYSICS | 04_PHYSICS | 분할 (Physics) |
| INPUT_CAMERA_PHYSICS | 05_INPUT_CAMERA | 분할 (Input/Camera) |
| CAMERA_VSYNC_SYSTEM | 05_INPUT_CAMERA | 통합 (Camera) |
| STAGE_INIT_RESPAWN | 06_STAGE_LIFECYCLE | 통합 |
| GAME_STATE_SCORE_SOUND | 06_STAGE_LIFECYCLE | 통합 |
| FINAL_SYSTEMS (RLE) | 07_COMPRESSION | 분할 (RLE) |
| STAGE_INIT (LZW) | 07_COMPRESSION | 분할 (LZW) |
| SYSTEM_SERVICES_HARDWARE_IO | 08_HARDWARE_IO | 직접 |

---

## 📚 추가 자료

### 알고리즘 상세
- [`../algorithms/`](../algorithms/) - 핵심 알고리즘 의사코드

### 완전한 참조
- [`../reference/MEMORY_MAP.md`](../reference/MEMORY_MAP.md) - 전체 메모리 맵
- [`../reference/FUNCTION_LIST.md`](../reference/FUNCTION_LIST.md) - 161개 함수 목록
- [`../reference/JUMP_TABLES.md`](../reference/JUMP_TABLES.md) - 5개 점프 테이블

### 원본 분석
- [`../archive/phase4-analysis/`](../archive/phase4-analysis/) - Phase 4 원본 14개 문서

---

## 💡 사용 가이드

### 시스템 이해하기
1. 의존성 낮은 시스템부터 (07, 08)
2. README 먼저, 그 다음 상세 문서
3. 의사코드 중심으로 읽기
4. 막히면 원본 문서 참조

### 구현하기
1. 시스템 문서 완독
2. 관련 알고리즘 문서 읽기
3. 메모리 레이아웃 재현
4. 의사코드 → 선택 언어로 변환
5. 테스트 전략 적용

### 디버깅
1. 메모리 값 비교 (원본 vs 구현)
2. 실행 흐름 추적
3. 엣지 케이스 검증
4. 원본 Phase 4 문서에서 힌트 찾기

---

## ⚠️ 주의사항

1. **순서 중요**: 의존성 고려하여 구현
2. **완벽주의 지양**: 80% 동작하면 다음 시스템으로
3. **점진적 개선**: 일단 돌아가게, 나중에 최적화
4. **테스트 우선**: 각 시스템 독립적으로 검증

---

## 🚀 빠른 시작

### 처음 읽는 사람
1. 이 README 읽기
2. `07_COMPRESSION.md` 읽기 (가장 단순)
3. `01_RENDERING.md` 읽기 (가장 복잡)
4. 관심 시스템 선택

### 구현자
1. `07_COMPRESSION.md` 구현 (독립적)
2. `08_HARDWARE_IO.md` 구현 (독립적)
3. 나머지 순차적으로 (의존성 따라)

---

**작성 상태**:
- [x] README.md (이 파일)
- [ ] 01_RENDERING.md
- [ ] 02_ENTITY_AI.md
- [ ] 03_ANIMATION.md
- [ ] 04_PHYSICS_COLLISION.md
- [ ] 05_INPUT_CAMERA.md
- [ ] 06_STAGE_LIFECYCLE.md
- [ ] 07_COMPRESSION.md
- [ ] 08_HARDWARE_IO.md

**다음 작업**: 시스템 문서 하나씩 작성

**관련 문서**:
- [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- [../methodology/README.md](../methodology/README.md)
- [../algorithms/README.md](../algorithms/README.md)
