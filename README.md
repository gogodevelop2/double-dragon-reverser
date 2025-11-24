# Double Dragon DOS 리버스 엔지니어링 프로젝트

1988년 DOS 게임 "Double Dragon"을 완전히 분석하여 현대 C++ 소스 코드로 재구성하는 프로젝트입니다.

---

## 🎯 프로젝트 목표

- ✅ 원본 DOS 바이너리 완전 분석
- 🔄 모든 게임 에셋 추출 (스프라이트, 레벨)
- ⏳ 컴파일 가능한 C++ 소스 코드 재구성
- ⏳ 웹 버전으로 이식 가능한 구조

---

## 📊 현재 진행 상황

**단계**: Phase 4 완료 → Phase 5 준비
**진행률**: 85%

| Phase | 작업 | 상태 |
|-------|------|------|
| 0 | 환경 준비 | ✅ 완료 |
| 1 | 코드 추출 (118개 함수) | ✅ 완료 |
| 2 | 코드 분석 및 설계 | ✅ 완료 |
| 3 | 에셋 분석 (LZW 압축) | ✅ 완료 |
| 4 | 게임 로직 완전 분석 | ✅ 완료 |
| 4.5 | 호출 그래프 복구 (+15개) | ✅ 완료 |
| 4.6 | 0x18c6 점프 테이블 (+9개) | ✅ 완료 |
| 5 | C++ 구현 | ⏳ 대기 |
| 6 | 통합 검증 | ⏳ 대기 |

**자세한 내용**: [진행 상황](docs/PROGRESS.md)

---

## 🚀 빠른 시작

### 필요 환경

```bash
# macOS
brew install ghidra openjdk@21 python@3.13

# Python 가상환경
python3 -m venv venv
source venv/bin/activate
pip install pyghidra

# 환경 변수 설정
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
```

### 코드 디컴파일 실행

```bash
source venv/bin/activate
python3 phase1_pyghidra_extract.py
```

**결과**:
- 164개 C 파일 생성 (`output/decompiled/*.c`)
- 118개 (Phase 1) + 22개 (Mode 1/2) + 15개 (Phase 4.5) + 9개 (Phase 4.6)
- 4,412+줄의 디컴파일 코드
- 100% 성공률

---

## 📁 프로젝트 구조

```
Double Dragon/
├── README.md                  # 프로젝트 개요 (여기)
│
├── docs/                      # 문서
│   ├── WORK_PRINCIPLES.md     # ⭐ 작업 원칙
│   ├── PROGRESS.md            # 진행 상황
│   ├── MASTER_PLAN.md         # 실행 계획
│   │
│   ├── technical/             # 기술 분석
│   │   ├── EXECUTION_PATH.md  # 실행 경로 분석
│   │   ├── LZW_COMPRESSION.md # LZW 압축 분석
│   │   └── SPRITE_FORMAT.md   # 스프라이트 포맷
│   │
│   ├── reports/               # Phase 리포트
│   │   ├── PHASE0_SETUP.md
│   │   ├── PHASE1_DECOMPILE.md
│   │   ├── PHASE3_ASSETS.md
│   │   └── PHASE4_SPRITES.md
│   │
│   └── guides/                # 도구 가이드
│       ├── GHIDRA_GUIDE.md
│       └── DOSBOX_GUIDE.md
│
├── output/                    # 출력 결과
│   ├── decompiled/            # 118개 C 파일
│   ├── assets/                # 추출된 에셋
│   └── checkpoints/           # 체크포인트
│
├── reference/                 # 원본 게임 파일
│   └── dos-original/          # DDMAIN.EXE + 데이터 파일 36개
│
└── ghidra-project/            # Ghidra 프로젝트
```

---

## 🛠️ 기술 스택

### 분석 도구
- **Ghidra 11.4.2**: 바이너리 디컴파일
- **pyghidra 2.2.0**: Python 자동화
- **Spice86**: DOS 에뮬레이션
- **DOSBox-X**: 실행 및 검증

### 개발
- **언어**: C++17, Python 3.13
- **빌드**: CMake
- **목표 플랫폼**: 웹 (Emscripten), Native

---

## 🎮 게임 정보

**원본 게임**: Double Dragon (1988, DOS)
- **개발사**: Technos Japan
- **플랫폼**: IBM PC (DOS)
- **그래픽**: CGA 320x200 4색
- **실행 파일**: DDMAIN.EXE (103KB)
- **데이터 파일**: 36개 (.EG1, .PC1, .NW1~5)

---

## 🔍 주요 발견 사항

### 1. 완전한 렌더링 파이프라인 (Phase 4 완료)
**5단계 파이프라인 발견**:
```
FUN_1000_029a: Depth-sorted 렌더링 루프
    ↓
FUN_1000_48e0: 렌더링 디스패처 (0x18c6 점프 테이블, 30개 엔트리)
    ↓
FUN_1000_293e: 모드 선택 (29회 호출)
    ↓
FUN_1000_28c0/28ef: Blit 함수 × 4 (CGA 4-plane)
    ↓
비디오 메모리 (0xB8000)
```

### 2. 점프 테이블 시스템
**5개 점프 테이블 발견**:
- **0x18c4**: 함수 디스패처 (11개?)
- **0x18c6**: 렌더링 디스패처 (30개) ← Phase 4.6에서 완전 분석
- **0x18d0**: 함수 디스패처
- **0x1319**: 타일맵 디스패처
- **0x3ff4**: 스테이지 디스패처

### 3. 커스텀 LZW 압축
- Unix compress 호환 (0x1F 0x9D)
- MSB-first 비트 순서
- Code 256 = 비트 크기 증가

### 4. 메모리 맵 완전 분석
**50+ 주소 파악**:
- **0x16c6**: 엔티티 배열 (7개 × 24B) - 플레이어 + 적
- **0x3542**: 투사체 배열 (6개 × 18B) - 발사체 + 아이템
- **0xf396/0xf398**: X/Y 스크롤 위치
- **0x18c6**: 렌더링 점프 테이블

### 5. 실행 경로 완전 추적
```
entry() → FUN_1000_0660() → FUN_1000_0b94()
    ├─ LZW 압축 해제 × 4
    ├─ 비트 재배열 × 4
    └─ 메인 루프
        ├─ 입력 처리
        ├─ 게임 로직
        └─ 렌더링 (5단계 파이프라인)
```

**자세한 내용**: [기술 분석 문서](docs/technical/)

---

## 📖 주요 문서

### 시작하기
- [진행 상황](docs/PROGRESS.md) - 현재 진행 상황
- [작업 원칙](docs/WORK_PRINCIPLES.md) - ⭐ 필독

### 기술 분석
- [렌더링 시스템](docs/technical/RENDERING_SYSTEM.md) ⭐ **신규**
- [메모리 맵](docs/technical/MEMORY_MAP.md) ⭐ **신규**
- [실행 경로 분석](docs/technical/EXECUTION_PATH.md)
- [LZW 압축 분석](docs/technical/LZW_COMPRESSION.md)
- [스프라이트 포맷](docs/technical/SPRITE_FORMAT.md)

### Phase 리포트
- [Phase 0: 환경 준비](docs/reports/PHASE0_SETUP.md)
- [Phase 1: 코드 추출](docs/reports/PHASE1_DECOMPILE.md)
- [Phase 3: 에셋 분석](docs/reports/PHASE3_ASSETS.md)
- [Phase 4: 게임 로직 완전 분석](docs/reports/PHASE4_COMPLETE.md) ⭐ **신규**

---

## 📜 라이선스

이 프로젝트는 **분석 및 교육 목적**입니다.

- 원본 게임 저작권: © 1988 Technos Japan
- 분석 코드 및 문서: MIT License
- 추출된 에셋: 원작자 저작권 적용

**주의**: 상업적 사용 금지

---

## 🤝 기여

현재 개인 프로젝트입니다. 분석 결과는 오픈소스로 공유됩니다.

---

## 📧 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/gogodevelop2/double-dragon-reverser/issues)

---

**생성일**: 2025-11-24
**마지막 업데이트**: 2025-11-24
**상태**: ✅ Phase 4 완료 (85%) → Phase 5 준비
