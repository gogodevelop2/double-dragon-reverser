# Double Dragon DOS 리버스 엔지니어링 프로젝트

1988년 DOS 게임 "Double Dragon"을 완전히 분석하여 현대 C++ 소스 코드로 재구성하는 프로젝트입니다.

## 🎯 프로젝트 목표

- 원본 DOS 바이너리 완전 분석
- 모든 게임 에셋 추출 (스프라이트, 레벨)
- 컴파일 가능한 C++ 소스 코드 재구성
- 웹 버전으로 이식 가능한 구조

## 📊 현재 진행 상황

**단계**: 계획 수립 완료
**진행률**: 5%

- [x] 프로젝트 구조 설계
- [x] Ghidra 분석 환경 구축
- [x] Spice86 메모리 덤프 수집
- [x] 마스터 플랜 수립
- [ ] GhidraMCP 자동화 시스템 구축
- [ ] 전체 코드 추출
- [ ] 에셋 추출
- [ ] 게임 로직 재구성

## 🛠️ 기술 스택

### 분석 도구
- **Ghidra 11.4.2**: 바이너리 디컴파일
- **GhidraMCP**: AI 자동 분석
- **Spice86**: DOS 에뮬레이션 및 메모리 덤프
- **DOSBox-X**: 실행 및 검증

### 개발
- **언어**: C++17, Python 3.13
- **빌드**: CMake
- **목표 플랫폼**: 웹 (Emscripten), Native

## 📁 프로젝트 구조

```
Double Dragon/
├── docs/                          # 프로젝트 문서
│   ├── SIMPLE_REVERSER_PLAN.md   # 실행 계획 (v2.0)
│   ├── GHIDRA_FINDINGS.md        # Ghidra 분석 결과
│   └── PROJECT_STATUS.md         # 상세 진행 상황
│
├── reference/                     # 원본 게임 파일
│   └── dos-original/             # DDMAIN.EXE + 데이터 파일 36개
│
├── analysis/                      # 분석 스크립트
│   └── analyze_memdump.py
│
├── spice86-dumps/                # 메모리 덤프 자료
│   └── E06625593.../
│       ├── spice86dumpMemoryDump.bin
│       ├── spice86dumpExecutionFlow.json
│       └── spice86dumpGhidraSymbols.txt
│
├── ghidra-project/               # Ghidra 프로젝트
│   └── DoubleDragon.gpr
│
└── tools/                        # 개발 도구
    └── Spice86/
```

## 🚀 시작하기

### 필요 환경

```bash
# macOS
brew install ghidra
brew install python@3.13
brew install cmake

# Python 가상환경
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# GhidraMCP
brew install uv
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
```

### 실행 계획

전체 프로세스는 **1-2일** 소요 예상:

```bash
# Phase 0: 환경 준비 (10분)
python start.py --phase 0

# Phase 1: 전체 코드 추출 (1-2시간)
python start.py --phase 1

# Phase 2: 코드 분석 및 재구성 (4-6시간)
python start.py --phase 2

# Phase 3: 에셋 추출 (2-4시간)
python start.py --phase 3

# Phase 4: 통합 및 검증 (2-3시간)
python start.py --phase 4
```

자세한 내용은 [docs/SIMPLE_REVERSER_PLAN.md](docs/SIMPLE_REVERSER_PLAN.md) 참조

## 📖 주요 문서

### 기술 분석
- [Ghidra 분석 결과](docs/GHIDRA_FINDINGS.md) - 디컴파일된 함수 분석
- [바이너리 분석 요약](analysis/SUMMARY.md) - 압축 알고리즘 발견
- [프로젝트 현황](docs/PROJECT_STATUS.md) - 상세 진행 상황

### 실행 계획
- [단순화 실행 계획](docs/SIMPLE_REVERSER_PLAN.md) ⭐ 최신 v2.0
- [완전 자율 플랜](docs/AUTONOMOUS_REVERSER_MASTER_PLAN.md) - 상세 버전

## 🎮 게임 정보

**원본 게임**: Double Dragon (1988, DOS)
- **개발사**: Technos Japan
- **플랫폼**: IBM PC (DOS)
- **그래픽**: CGA 320x200 4색
- **실행 파일**: DDMAIN.EXE (103KB)
- **데이터 파일**: 36개 (.EG1, .PC1, .NW1~5)

## 🔍 분석 발견 사항

### 압축 시스템
- **LZW 변형**: Unix compress 호환 (0x1F 0x9D)
- **RLE 추가**: 선택적 2차 압축
- **CGA 평면**: 16-plane interleaved 구조

### 주요 함수
- `FUN_1000_6091`: LZW 비트 읽기
- `FUN_1000_605b`: LZW 디코딩
- `FUN_1000_2865`: RLE 압축 해제
- `FUN_1000_0786`: CGA 평면 변환

## 📜 라이선스

이 프로젝트는 **분석 및 교육 목적**입니다.

- 원본 게임 저작권: © 1988 Technos Japan
- 분석 코드 및 문서: MIT License
- 추출된 에셋: 원작자 저작권 적용

**주의**: 상업적 사용 금지

## 🤝 기여

현재 개인 프로젝트입니다. 분석 결과는 오픈소스로 공유됩니다.

## 📧 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/gogodevelop2/double-dragon-reverser/issues)

---

**생성일**: 2025-11-24
**마지막 업데이트**: 2025-11-24
**상태**: 🚧 진행 중
