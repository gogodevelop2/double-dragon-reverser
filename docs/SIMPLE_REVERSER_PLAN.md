# Double Dragon 리버스 엔지니어링 실행 계획 (단순화 버전)

**버전**: 2.0
**작성일**: 2025-11-24
**핵심**: GhidraMCP 직접 디컴파일 활용 → 1-2일 완성

---

## 🎯 핵심 아이디어

### ✅ GhidraMCP가 이미 C 코드로 변환해줌!

```python
# 바이너리 분석 불필요! 바로 C 코드 가져오기
functions = mcp.list_functions("DDMAIN.EXE")  # 200개
c_code = mcp.decompile(func.address)  # C 코드 바로 나옴!

# 200개 × 2초 = 7분이면 전체 코드 추출 완료!
```

### 📊 예상 소요 시간

| Phase | 작업 | 시간 |
|-------|------|------|
| 0 | 환경 준비 | 10분 |
| 1 | 전체 코드 추출 (GhidraMCP) | 1-2시간 |
| 2 | AI 분석 및 C++ 재구성 | 4-6시간 |
| 3 | 에셋 추출 | 2-4시간 |
| 4 | 통합 및 검증 | 2-3시간 |
| **합계** | | **9-15시간 (1-2일)** |

---

## Phase 0: 환경 준비 (10분)

### 실행

```bash
# 1. GhidraMCP 시작
cd "/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original"
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
uvx pyghidra-mcp DDMAIN.EXE DUAL.EXE SHOW.EXE
```

### 검증

```
질문 1: "DDMAIN.EXE에 몇 개의 함수가 있어?"
예상: 200개 이상

질문 2: "FUN_1000_6091 함수를 디컴파일해줘"
예상: C 코드가 바로 출력됨
```

### 산출물

```
output/
├── phase0_report.md
└── test_function.c
```

### 📊 CHECKPOINT #0

**사용자 확인**:
- [ ] GhidraMCP 연결 성공
- [ ] 디컴파일 테스트 성공
- [ ] Phase 1 진행 승인

---

## Phase 1: 전체 코드 추출 (1-2시간)

### 목표

**모든 함수 디컴파일 → 파일로 저장**

### 실행

```python
# 자동 실행 스크립트
import os
import json

# 1. 모든 함수 가져오기
functions = mcp.list_functions("DDMAIN.EXE")
print(f"총 {len(functions)}개 함수")

# 2. 각 함수 디컴파일
for i, func in enumerate(functions, 1):
    print(f"[{i}/{len(functions)}] {func.name}")

    # Ghidra가 C 코드로 변환
    c_code = mcp.decompile("DDMAIN.EXE", func.address)

    # 저장
    with open(f"output/decompiled/{func.name}.c", "w") as f:
        f.write(c_code)

    # 메타데이터
    meta = {
        "name": func.name,
        "address": hex(func.address),
        "size": func.size
    }
    with open(f"output/decompiled/{func.name}.json", "w") as f:
        json.dump(meta, f, indent=2)

print("완료!")
```

### 산출물

```
output/
├── decompiled/
│   ├── FUN_1000_6091.c     # LZW 비트 읽기
│   ├── FUN_1000_605b.c     # LZW 디코딩
│   ├── FUN_1000_2865.c     # RLE
│   ├── FUN_1000_0786.c     # CGA 변환
│   └── ... (200개)
│
└── phase1_report.md
```

### 📊 CHECKPOINT #1

**보고 내용**:
- 디컴파일된 함수: 203개
- C 코드 라인: ~15,000 lines
- 분류: 압축(15), 그래픽(23), 게임로직(87), 등

**사용자 확인**:
- [ ] 모든 함수 추출 완료
- [ ] Phase 2 진행 승인

---

## Phase 2: 코드 분석 및 재구성 (4-6시간)

### 목표

**AI가 C 코드 읽고 → C++ 프로젝트 생성**

### 실행 방식

```
AI에게 요청:

"output/decompiled/ 폴더의 200개 C 파일을 모두 읽고 분석해줘.

작업:
1. 함수 간 관계 파악
2. 데이터 구조 역산
3. 게임 로직 이해
4. 모던 C++ 프로젝트로 재구성

output/src/에 완전한 프로젝트 생성:
- src/main.cpp
- src/entities/ (플레이어, 적)
- src/systems/ (충돌, AI, 렌더링)
- src/assets/ (LZW, RLE 압축 해제)
- CMakeLists.txt

컴파일 가능한 코드로 만들어줘!"
```

### 세부 단계

#### Step 2.1: 압축 시스템 분석 (1시간)

```
"FUN_1000_6091.c, FUN_1000_605b.c, FUN_1000_2865.c를 읽고:

1. LZW 알고리즘 이해
2. RLE 알고리즘 이해
3. 완전한 C++ 구현 작성

output/src/assets/compression.h
output/src/assets/compression.cpp
"
```

#### Step 2.2: 데이터 구조 역산 (2시간)

```
"메모리 덤프와 Execution Flow JSON을 활용해서:

1. 플레이어 구조체 찾기
2. 적 구조체 찾기
3. 레벨 구조체 찾기

output/src/data/structures.h 생성
"
```

#### Step 2.3: 게임 로직 재구성 (2시간)

```
"게임 로직 함수들을 분석해서:

1. 플레이어 시스템 (이동, 공격, 점프)
2. 적 AI 시스템
3. 충돌 감지 시스템
4. 레벨 관리 시스템

각각 C++ 클래스로 구현해줘"
```

### 산출물

```
output/src/
├── main.cpp
├── game.h / .cpp
│
├── entities/
│   ├── player.h / .cpp
│   ├── enemy.h / .cpp
│   └── item.h / .cpp
│
├── systems/
│   ├── collision.h / .cpp
│   ├── ai.h / .cpp
│   └── renderer.h / .cpp
│
├── assets/
│   ├── compression.h / .cpp
│   └── loader.h / .cpp
│
├── data/
│   └── structures.h
│
└── CMakeLists.txt
```

### 📊 CHECKPOINT #2

**보고 내용**:
- C++ 클래스: 25개
- 총 코드 라인: ~8,000 lines
- 컴파일 성공: ✅

**사용자 확인**:
- [ ] 코드 구조 검토
- [ ] Phase 3 진행 승인

---

## Phase 3: 에셋 추출 (2-4시간)

### 목표

**36개 데이터 파일 → PNG + JSON**

### 실행

```python
# LZW 압축 해제 (이미 구현됨)
for file in ["*.EG1", "*.PC1", "*.NW1", "*.NW2", ...]:
    # 1. LZW 압축 해제
    decompressed = lzw_decompress(file)

    # 2. 헤더 파싱
    header = parse_header(decompressed)

    # 3. CGA → PNG 변환
    png = cga_to_png(decompressed, header.width, header.height)

    # 4. 저장
    save(f"output/assets/{file}.png", png)
```

### 산출물

```
output/assets/
├── sprites/
│   ├── PLAYER1.png
│   ├── LINDA.png
│   ├── ABOBO.png
│   └── ... (17개)
│
├── levels/
│   ├── LEVEL11.png
│   └── ... (4개)
│
└── animations/
    └── ... (10개)
```

### 📊 CHECKPOINT #3

**보고 내용**:
- 추출된 파일: 36/36
- PNG 생성: 성공
- 전체 에셋 준비 완료

**사용자 확인**:
- [ ] 에셋 품질 검토
- [ ] Phase 4 진행 승인

---

## Phase 4: 통합 및 검증 (2-3시간)

### 목표

**완전한 프로젝트 빌드 및 테스트**

### 실행

```bash
# 1. 빌드
cd output
mkdir build && cd build
cmake ..
make

# 2. 실행
./double_dragon

# 3. 테스트
make test
```

### 검증 항목

- ✅ 컴파일 성공
- ✅ 에셋 로드 성공
- ✅ 게임 실행 가능
- ✅ 기본 동작 확인 (플레이어 이동, 적 AI)

### 📊 CHECKPOINT #4: 완료!

**최종 보고서**:

```markdown
# 프로젝트 완료

## 통계
- 총 소요 시간: 12시간
- C++ 코드: 8,347 lines
- 파일: 67개
- 에셋: 36개

## 산출물
- 컴파일 가능한 C++ 프로젝트 ✅
- 모든 게임 에셋 (PNG) ✅
- 완전한 문서 ✅

## 사용 방법
cd output/build
./double_dragon
```

---

## 체크포인트 시스템

### 각 Phase 종료 시

1. **자동 보고서 생성**
   - `output/docs/phaseN_report.md`

2. **실행 중지**
   - 사용자 검토 대기

3. **사용자 결정**
   ```bash
   # 다음 Phase 진행
   python resume.py --checkpoint phaseN --decision approve

   # 저장하고 나중에
   python resume.py --checkpoint phaseN --decision pause

   # 중단
   python resume.py --checkpoint phaseN --decision stop
   ```

### 중단/재개

```bash
# 언제든 중단 가능 (Ctrl+C)
# 자동으로 체크포인트 저장됨

# 재개
python resume.py --auto
```

---

## 최종 산출물

```
output/
├── src/                    # 완전한 C++ 프로젝트
│   ├── main.cpp
│   ├── entities/
│   ├── systems/
│   └── assets/
│
├── assets/                 # 모든 게임 에셋
│   ├── sprites/
│   ├── levels/
│   └── animations/
│
├── docs/                   # 자동 생성 문서
│   ├── phase0_report.md
│   ├── phase1_report.md
│   ├── phase2_report.md
│   ├── phase3_report.md
│   └── phase4_report.md
│
├── decompiled/             # 원본 디컴파일 C 코드
│   └── ... (200개)
│
├── checkpoints/            # 체크포인트 데이터
│   ├── phase0.json
│   ├── phase1.json
│   ├── phase2.json
│   └── phase3.json
│
├── CMakeLists.txt
└── README.md
```

---

## 시작 방법

```bash
# Phase 0부터 시작
python start.py

# 또는 특정 Phase부터
python start.py --phase 1

# 이전 작업 재개
python resume.py --auto
```

---

## 예상 일정

**풀타임 작업 (하루 8시간)**:
- Day 1: Phase 0-2 (환경 + 코드 추출 + 분석)
- Day 2: Phase 3-4 (에셋 추출 + 통합)

**파트타임 (하루 4시간)**:
- Day 1: Phase 0-1
- Day 2: Phase 2
- Day 3: Phase 3-4

**실제 AI 작업 시간**: 9-15시간 (무인 실행)
**사용자 검토 시간**: 4번 × 15분 = 1시간

---

**작성**: 2025-11-24
**버전**: 2.0 Simple
**상태**: 실행 준비 완료 ✅
