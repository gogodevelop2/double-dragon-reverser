# Double Dragon 프로젝트 구조

**업데이트**: 2025-11-24
**상태**: 정리 완료

---

## 📁 디렉토리 구조

```
Double Dragon/
│
├── 📚 docs/                    ← 모든 문서 (메인)
│   ├── function-analysis/      ← 함수 분석 (최신 작업)
│   │   ├── MODE1_FUNCTIONS_SUMMARY.md
│   │   ├── MODE2_COMPLETE_ANALYSIS.md (34KB - 핵심!)
│   │   ├── RECOVERING_MISSED_FUNCTIONS.md
│   │   ├── ANALYSIS_MISTAKES.md
│   │   ├── CALL_GRAPH.md
│   │   └── INDEX.md
│   │
│   ├── guides/                 ← 사용 가이드
│   │   ├── DOSBOX_GUIDE.md
│   │   └── GHIDRA_GUIDE.md
│   │
│   ├── reports/                ← Phase별 리포트
│   │   ├── PHASE0_SETUP.md
│   │   ├── PHASE1_DECOMPILE.md
│   │   ├── PHASE3_ASSETS.md
│   │   └── PHASE4_SPRITES.md
│   │
│   ├── technical/              ← 기술 분석
│   │   ├── LZW_COMPRESSION.md
│   │   ├── SPRITE_FORMAT.md
│   │   └── EXECUTION_PATH.md
│   │
│   ├── archive/                ← 오래된 문서 보관
│   │   ├── old-reports/        ← output/docs 이동됨
│   │   └── early-analysis/     ← analysis 이동됨
│   │
│   ├── PYGHIDRA_GUIDE.md       ← pyghidra 사용법
│   ├── PROGRESS.md             ← 전체 진행 상황
│   └── WORK_PRINCIPLES.md      ← 작업 원칙
│
├── 💾 output/                  ← 생성된 결과물
│   ├── analysis/               ← JSON 데이터
│   │   ├── mode1_recovery_results.json
│   │   ├── mode2_recovery_results.json
│   │   └── function_analysis.json
│   │
│   ├── decompiled/             ← C 소스 코드 (137개)
│   │   ├── FUN_1000_*.c        ← Ghidra 디컴파일
│   │   └── ... (137 files)
│   │
│   ├── assets/                 ← 추출된 게임 에셋
│   │   ├── sprites/
│   │   ├── levels/
│   │   └── raw_sprites/
│   │
│   └── checkpoints/            ← Phase별 체크포인트
│       ├── phase1.json
│       ├── phase2.json
│       └── phase3.json
│
├── 📦 reference/               ← 원본 바이너리
│   └── dos-original/
│       ├── DDMAIN.EXE          ← 메인 실행 파일
│       ├── *.EG1               ← 압축된 스프라이트
│       └── *.Z                 ← LZW 압축 파일
│
├── 🔧 ghidra-project/          ← Ghidra 프로젝트
│   └── DoubleDragon/
│
├── 🐍 Python 스크립트 (루트)
│   ├── recover_all_mode1_functions.py
│   ├── recover_all_mode2_functions.py
│   ├── find_main_loop.py
│   └── ... (분석 스크립트들)
│
├── 📦 archive/                 ← 기타 아카이브
│
├── 🌐 double-dragon-web/       ← 웹 포팅 (미사용)
├── 🔨 tools/                   ← 외부 도구
├── 📊 spice86-dumps/           ← 디버거 덤프
└── 📝 README.md                ← 프로젝트 설명

```

---

## 🎯 주요 문서 위치

### 시작하기
- `README.md` - 프로젝트 개요
- `docs/PROGRESS.md` - 전체 진행 상황
- `docs/WORK_PRINCIPLES.md` - 작업 원칙

### 최신 분석 결과 (2025-11-24)
- `docs/function-analysis/MODE2_COMPLETE_ANALYSIS.md` (34KB) ⭐⭐⭐
  - Mode 1 vs Mode 2 완전 비교
  - CGA vs EGA 그래픽 시스템
  - VGA 하드웨어 프로그래밍
  - 22개 함수 복구 과정

- `docs/function-analysis/MODE1_FUNCTIONS_SUMMARY.md`
  - Mode 1 (CGA) 11개 함수 분석

- `docs/function-analysis/CALL_GRAPH.md`
  - 메인 게임 루프 구조
  - 디스패처 호출 지점

### 방법론
- `docs/function-analysis/RECOVERING_MISSED_FUNCTIONS.md`
  - Ghidra가 놓친 함수 복구 3단계

- `docs/function-analysis/ANALYSIS_MISTAKES.md`
  - 실수 기록 및 교훈

### 기술 문서
- `docs/technical/LZW_COMPRESSION.md` - LZW 압축 해제
- `docs/technical/SPRITE_FORMAT.md` - 스프라이트 포맷
- `docs/PYGHIDRA_GUIDE.md` - pyghidra 사용법

---

## 📊 통계 (2025-11-24 기준)

### 코드
- **디컴파일된 C 파일**: 137개
  - 원래 Ghidra 인식: 118개
  - Mode 1 복구: 10개
  - Mode 2 복구: 10개

### 문서
- **Markdown 문서**: ~4,000줄
- **핵심 분석 문서**: 10개
- **기술 문서**: 3개
- **가이드**: 3개

### 데이터
- **JSON 파일**: 5개
- **추출 에셋**: 수십 개
- **체크포인트**: 3개

---

## 🗂️ 아카이브된 내용

### docs/archive/old-reports/
오래된 Phase 리포트 (output/docs에서 이동):
- phase0_report.md
- phase1_report.md
- phase3_assets_analysis.md
- phase4_execution_path.md

### docs/archive/early-analysis/
초기 바이너리 분석 (analysis에서 이동):
- BINARY_ANALYSIS_REPORT.md
- DECOMPRESSION_FINDINGS.md
- 초기 분석 스크립트들

**참고**: 필요시 참조 가능, 최신 문서는 상위 디렉토리 사용

---

## 🚀 빠른 시작

### 1. 최신 분석 결과 보기
```bash
cat "docs/function-analysis/MODE2_COMPLETE_ANALYSIS.md"
```

### 2. 전체 진행 상황 확인
```bash
cat "docs/PROGRESS.md"
```

### 3. 함수 목록 보기
```bash
cat "docs/function-analysis/INDEX.md"
```

### 4. 디컴파일된 코드 보기
```bash
ls output/decompiled/
```

---

## 🎓 다음 단계

1. **메인 게임 루프 상세 분석**
   - `docs/function-analysis/CALL_GRAPH.md` 참조
   - FUN_1000_3830, FUN_1000_0360 등

2. **디스패처 호출 지점 분석**
   - 11개 디스패처가 언제 호출되는지

3. **나머지 함수 분석**
   - 137개 중 주요 함수들

---

**정리 완료**: 2025-11-24
**정리 방식**: 최소 정리 (중복 제거, 아카이브 이동)
