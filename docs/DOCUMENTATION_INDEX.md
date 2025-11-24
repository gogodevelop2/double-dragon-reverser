# Double Dragon DOS - 문서 인덱스

**최종 업데이트**: 2025-11-24
**프로젝트 상태**: Phase 4 완료 (100%), 문서 정리 중

---

## 📚 문서 구조 개요

이 문서 저장소는 **두 가지 목적**을 가지고 있습니다:

1. **주목적**: Double Dragon DOS 게임의 완전한 구조 분석 및 재구현 가이드
2. **보조목적**: DOS 게임 리버스 엔지니어링 방법론 기록 (다른 프로젝트 재사용)

---

## 🎯 목적별 가이드

### A. Double Dragon 재구현하려면?
**읽는 순서**:
1. [`IMPLEMENTATION_GUIDE.md`](IMPLEMENTATION_GUIDE.md) - 시작점
2. [`systems/`](systems/) - 8개 시스템별 구조
3. [`algorithms/`](algorithms/) - 핵심 알고리즘
4. [`reference/`](reference/) - 상세 참고 자료

### B. 다른 DOS 게임 리버스 엔지니어링 하려면?
**읽는 순서**:
1. [`methodology/01_PROCESS_OVERVIEW.md`](methodology/01_PROCESS_OVERVIEW.md) - 전체 프로세스
2. [`methodology/02_TOOLS_AND_SETUP.md`](methodology/02_TOOLS_AND_SETUP.md) - 도구 세팅
3. [`methodology/04_ANALYSIS_TECHNIQUES.md`](methodology/04_ANALYSIS_TECHNIQUES.md) - 분석 기법
4. [`methodology/06_LESSONS_LEARNED.md`](methodology/06_LESSONS_LEARNED.md) - 실수와 배운 점

### C. Phase 4 원본 분석 문서 보려면?
- [`archive/phase4-analysis/`](archive/phase4-analysis/) - 161개 함수 상세 분석 (18,096줄)

---

## 📂 디렉토리 구조

```
docs/
│
├── DOCUMENTATION_INDEX.md           ← 📍 여기 (이 파일)
├── IMPLEMENTATION_GUIDE.md          ← 재구현 시작점
├── PROGRESS.md                      ← 프로젝트 진행 상황
├── WORK_PRINCIPLES.md               ← 작업 원칙
│
├── methodology/                     ← 🔬 리버스 엔지니어링 방법론
│   ├── README.md
│   ├── 01_PROCESS_OVERVIEW.md       # Phase 0-4 프로세스
│   ├── 02_TOOLS_AND_SETUP.md        # Ghidra, pyghidra, Spice86
│   ├── 03_DECOMPILATION.md          # 디컴파일 전략
│   ├── 04_ANALYSIS_TECHNIQUES.md    # 함수 분석 기법
│   ├── 05_DOCUMENTATION.md          # 문서화 방법
│   └── 06_LESSONS_LEARNED.md        # 실수와 교훈
│
├── systems/                         ← 🎮 게임 시스템 구조 (언어 중립)
│   ├── README.md
│   ├── 01_RENDERING.md              # 렌더링 파이프라인
│   ├── 02_ENTITY_AI.md              # 엔티티 + AI
│   ├── 03_ANIMATION.md              # 애니메이션 시스템
│   ├── 04_PHYSICS_COLLISION.md      # 물리 + 충돌
│   ├── 05_INPUT_CAMERA.md           # 입력 + 카메라
│   ├── 06_STAGE_LIFECYCLE.md        # 스테이지 생명주기
│   ├── 07_COMPRESSION.md            # RLE + LZW
│   └── 08_HARDWARE_IO.md            # 하드웨어 I/O
│
├── algorithms/                      ← ⚙️ 핵심 알고리즘 (의사코드)
│   ├── README.md
│   ├── RLE_COMPRESSION.md           # Run-Length Encoding
│   ├── LZW_COMPRESSION.md           # Lempel-Ziv-Welch
│   ├── SPRITE_BLITTING.md           # 4-plane CGA 블리팅
│   ├── MANHATTAN_AI.md              # 맨하탄 거리 AI
│   └── VSYNC_TIMING.md              # VSync 동기화
│
├── reference/                       ← 📖 참고 자료 (완전한 목록)
│   ├── README.md
│   ├── MEMORY_MAP.md                # 전체 메모리 맵
│   ├── FUNCTION_LIST.md             # 161개 함수 목록
│   ├── JUMP_TABLES.md               # 5개 점프 테이블
│   └── EXECUTION_FLOW.md            # 실행 흐름도
│
├── reports/                         ← 📊 Phase 리포트
│   ├── PHASE0_SETUP.md
│   ├── PHASE1_DECOMPILE.md
│   ├── PHASE3_ASSETS.md
│   └── PHASE4_COMPLETE.md
│
├── technical/                       ← 🔧 기술 문서 (기존)
│   ├── RENDERING_SYSTEM.md
│   ├── MEMORY_MAP.md
│   ├── EXECUTION_PATH.md
│   ├── SPRITE_FORMAT.md
│   └── LZW_COMPRESSION.md
│
└── archive/                         ← 🗄️ 역사 기록
    ├── phase4-analysis/             # Phase 4 원본 14개 문서
    ├── sessions/                    # 작업 세션 기록
    ├── tools/                       # 도구 가이드
    └── early-analysis/              # 초기 분석
```

---

## 🔄 문서 간 관계

### 정보의 흐름

```
방법론 (methodology/)
    ↓
프로세스 적용
    ↓
Phase 4 분석 완료 (archive/phase4-analysis/)
    ↓
추출 & 통합
    ↓
시스템 구조 (systems/) + 알고리즘 (algorithms/)
    ↓
구현 가이드 (IMPLEMENTATION_GUIDE.md)
    ↓
재구현
```

### 참조 관계

- **systems/*.md** → 원본: `archive/phase4-analysis/`
- **algorithms/*.md** → 원본: `archive/phase4-analysis/FINAL_SYSTEMS_ANALYSIS.md`
- **methodology/*.md** → 경험: Phase 0-4 전체 과정
- **reference/*.md** → 통합: 14개 문서에 흩어진 정보

---

## 📏 문서 작성 원칙

### 언어 중립성
- **의사코드** 사용 (특정 언어 구문 금지)
- **추상적 설명** (구현 세부사항 분리)
- **바이트 단위 메모리 맵** (언어별 타입 시스템 무관)

### 재사용 가능성
- **DOS 게임 일반론** 우선 (Double Dragon 특수사항 명시)
- **도구 사용법** 체계화 (다른 프로젝트 재활용)
- **실수 기록** (같은 실수 반복 방지)

### 단계적 작성
- **하나씩 완성** (완벽주의 지양)
- **점진적 개선** (초안 → 검토 → 정제)
- **Git 커밋 단위** (시스템별 또는 문서별)

---

## 🎓 핵심 개념

### Phase 4에서 배운 것
1. **실행 경로 추적이 핵심** - entry point부터 순차적으로
2. **함수 포인터 시스템** - 5개 점프 테이블 발견
3. **Work Buffer 패턴** - 엔티티, 프로젝타일, 스프라이트
4. **Dual Mode 렌더링** - EGA vs CGA
5. **압축 시스템** - RLE (스프라이트) + LZW (에셋)

### 리버스 엔지니어링 방법론
1. **Phase 0**: 환경 준비 (Ghidra + pyghidra)
2. **Phase 1**: 자동 디컴파일 (118개 함수)
3. **Phase 2**: 코드 분석 (카테고리 분류)
4. **Phase 3**: 에셋 분석 (LZW 압축)
5. **Phase 4**: 완전 분석 (161개 함수, 100%)

---

## 📊 통계

### Phase 4 완료 시점
- **함수 수**: 161개 (100%)
- **분석 문서**: 14개
- **총 줄 수**: 18,096줄
- **소요 시간**: 14시간
- **메모리 주소**: 80+ 개 식별
- **점프 테이블**: 5개 완전 발견

### 문서 정리 후 (예상)
- **방법론 문서**: 6개
- **시스템 문서**: 8개
- **알고리즘 문서**: 5개
- **참고 문서**: 4개
- **총 핵심 문서**: ~25개
- **아카이브**: 50+ 개 (보존)

---

## 🚀 다음 단계

### 즉시 (문서 정리)
1. ✅ 디렉토리 구조 생성
2. ⏳ 방법론 문서 작성
3. ⏳ 시스템 문서 통합
4. ⏳ 알고리즘 추출
5. ⏳ Phase 4 문서 아카이브

### 단기 (재구현 준비)
1. 구현 언어 결정 (TypeScript? C++? Rust?)
2. IMPLEMENTATION_GUIDE.md 작성
3. 첫 시스템 구현 (압축 시스템 추천)

### 장기 (다른 게임)
1. 방법론 문서 개선 (이번 경험 반영)
2. 도구 체인 자동화
3. 템플릿화

---

## 💡 사용 팁

### 처음 보는 사람이라면
1. `PROGRESS.md` 읽기 (전체 맥락)
2. `methodology/01_PROCESS_OVERVIEW.md` 읽기 (방법 이해)
3. 목적에 따라 A 또는 B 경로 선택

### 구현자라면
1. `IMPLEMENTATION_GUIDE.md` (작성 예정)
2. `systems/` 순차적으로
3. `algorithms/` 참조
4. 막히면 `archive/phase4-analysis/` 원본 참조

### 다른 DOS 게임 작업자라면
1. `methodology/` 전체 읽기
2. `methodology/06_LESSONS_LEARNED.md` 필독
3. 도구 세팅 (`methodology/02_TOOLS_AND_SETUP.md`)
4. 프로젝트에 적용

---

## 📞 문서 피드백

문서 개선 제안, 오류 발견, 추가 설명 필요 시:
- GitHub Issues (프로젝트 리포지토리)
- 또는 문서 내 TODO 섹션에 메모

---

**최종 목표**:
1. Double Dragon 완벽 재구현
2. DOS 게임 리버스 엔지니어링 표준 방법론 확립

**현재 위치**: Phase 4 완료 → 문서 정리 중 → Phase 5 준비

---

**관련 문서**:
- [PROGRESS.md](PROGRESS.md) - 프로젝트 진행 상황
- [WORK_PRINCIPLES.md](WORK_PRINCIPLES.md) - 작업 원칙
- [methodology/README.md](methodology/README.md) - 방법론 소개
- [systems/README.md](systems/README.md) - 시스템 구조 소개
