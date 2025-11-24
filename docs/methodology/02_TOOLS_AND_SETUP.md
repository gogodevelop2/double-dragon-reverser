# 도구 및 환경 설정

**목적**: DOS 게임 리버스 엔지니어링에 필요한 도구를 설치하고, 올바르게 작동하는지 검증하는 방법을 설명합니다.

**대상 독자**:
- 처음 DOS 게임 RE를 시작하는 개발자
- 다른 DOS 게임 프로젝트를 준비하는 사람
- Double Dragon 분석 환경을 재현하려는 사람

**소요 시간**: 30분 ~ 1시간 (OS 및 경험에 따라)

---

## 📋 목차

1. [도구 스택 개요](#도구-스택-개요)
2. [필수 도구](#필수-도구)
3. [선택 도구](#선택-도구)
4. [환경 검증](#환경-검증)
5. [일반적인 문제 해결](#일반적인-문제-해결)
6. [고급 설정](#고급-설정)
7. [빠른 시작 체크리스트](#빠른-시작-체크리스트)

---

## 🎯 도구 스택 개요

### 도구 분류

| 도구 | 필수성 | 평가 | 주용도 | 대안 |
|------|--------|------|--------|------|
| **Ghidra** | ⭐⭐⭐⭐⭐ | 필수 | 디컴파일, 분석 | IDA Pro, Binary Ninja |
| **pyghidra** | ⭐⭐⭐⭐⭐ | 필수 | 자동화 (~100배 속도) | 수동 작업 |
| **Python 3.9+** | ⭐⭐⭐⭐⭐ | 필수 | 스크립팅, 자동화 | - |
| **Spice86** | ⭐⭐⭐⭐ | 강력 추천 | 호출 그래프, 디버깅 | DOSBox Debugger |
| **DOSBox-X** | ⭐⭐⭐ | 선택 | 게임 실행, 디버깅 | DOSBox, dosemu2 |
| **HxD / Hex Editor** | ⭐⭐⭐ | 선택 | 바이너리 검사 | xxd, hexdump |
| **Git** | ⭐⭐⭐⭐ | 추천 | 버전 관리 | - |

### 효율 기여도

```
Ghidra (기본):             1x (수동 디컴파일 베이스라인)
  + pyghidra:            100x (자동 배치 디컴파일)
  + Spice86:              2x (호출 그래프로 우선순위 결정)
  + 스크립트 자동화:        1.5x (메모리 패턴 자동 탐지)
-----------------------------------------------------------
총 효율:                ~300x (이론적 최대)
실제 효율:              ~200x (17시간 vs 예상 3,400시간)
```

**핵심 인사이트**:
- Ghidra 없이는 불가능 (어셈블리 수동 읽기는 비현실적)
- pyghidra 없으면 118개 함수 디컴파일에 ~20시간 소요
- Spice86 없으면 중요 함수 찾기에 2배 시간 소요

---

## 🔧 필수 도구

### 1. Ghidra 11.4.2

**왜 필수인가?**
- 무료 오픈소스 디컴파일러 (NSA 개발)
- x86 16-bit DOS 바이너리 완벽 지원
- Python/Java API로 자동화 가능
- 프로젝트 기반 작업 (분석 저장)

#### 설치: macOS

```bash
# Homebrew 사용
brew install ghidra

# 수동 설치
# 1. https://ghidra-sre.org/ 에서 11.4.2 다운로드
# 2. 압축 해제
unzip ghidra_11.4.2_PUBLIC_20250207.zip
sudo mv ghidra_11.4.2_PUBLIC /opt/ghidra

# 환경 변수 설정 (~/.zshrc 또는 ~/.bashrc)
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
export PATH="$GHIDRA_INSTALL_DIR:$PATH"

# Java 확인 (Ghidra는 Java 17+ 필요)
java --version
# 없으면: brew install openjdk@17
```

#### 설치: Ubuntu/Debian

```bash
# Java 설치
sudo apt update
sudo apt install default-jdk

# Ghidra 다운로드 및 설치
wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.4.2_build/ghidra_11.4.2_PUBLIC_20250207.zip
unzip ghidra_11.4.2_PUBLIC_20250207.zip
sudo mv ghidra_11.4.2_PUBLIC /opt/ghidra

# 환경 변수 (~/.bashrc)
export GHIDRA_INSTALL_DIR="/opt/ghidra"
export PATH="$GHIDRA_INSTALL_DIR:$PATH"

source ~/.bashrc
```

#### 설치: Windows

```powershell
# 1. Java 17+ 설치
# https://adoptium.net/ 에서 다운로드

# 2. Ghidra 다운로드
# https://ghidra-sre.org/ 에서 11.4.2 다운로드

# 3. C:\ghidra 에 압축 해제

# 4. 환경 변수 설정
# 시스템 속성 → 고급 → 환경 변수
# GHIDRA_INSTALL_DIR = C:\ghidra\ghidra_11.4.2_PUBLIC
# Path에 추가: %GHIDRA_INSTALL_DIR%
```

#### 검증

```bash
# Ghidra 실행 확인
ghidraRun

# 또는 (수동 설치 시)
$GHIDRA_INSTALL_DIR/ghidraRun
```

**성공 시**: Ghidra GUI가 열립니다.

#### Ghidra 초기 설정

1. **프로젝트 생성**
   - File → New Project → Non-Shared Project
   - 프로젝트명: `DoubleDragon`
   - 위치: 작업 디렉토리

2. **바이너리 임포트**
   - File → Import File
   - 파일 선택: `DDMAIN.EXE`
   - Format: `MS-DOS Executable (MZ)`
   - Language: `x86:Real Mode:16:default`
   - Options: 기본값 유지

3. **자동 분석 설정**
   - Analysis → Auto Analyze
   - 옵션 확인:
     - ✅ Decompiler Parameter ID
     - ✅ Function Start Search
     - ✅ Stack
     - ✅ x86 Constant Reference Analyzer
   - Analyze 클릭 (5-10분 소요)

4. **세그먼트 확인**
   - Window → Memory Map
   - 확인사항:
     - `1000:0000` - Code Segment (CS)
     - Data Segments (DS, ES)
     - Stack Segment (SS)

---

### 2. pyghidra 2.2.0

**왜 필수인가?**
- Python에서 Ghidra API 직접 호출
- 배치 디컴파일 자동화 (~100배 속도)
- 118개 함수를 2.2분에 디컴파일 (수동: ~20시간)

#### 설치

```bash
# Python 3.9+ 확인
python3 --version

# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# pyghidra 설치
pip install pyghidra==2.2.0

# Jpype 의존성 확인 (자동 설치됨)
pip list | grep jpype
```

#### 설정

```bash
# 환경 변수 확인 (중요!)
echo $GHIDRA_INSTALL_DIR
# 출력: /opt/homebrew/Cellar/ghidra/11.4.2/libexec (또는 설치 경로)

# 없으면 설정
export GHIDRA_INSTALL_DIR="/opt/ghidra"  # 본인 경로
```

#### 검증

```python
# test_pyghidra.py
import pyghidra

print(f"pyghidra version: {pyghidra.__version__}")
print(f"Ghidra path: {pyghidra.get_install_path()}")

# 간단한 테스트
with pyghidra.open_program("path/to/DDMAIN.EXE") as flat_api:
    program = flat_api.getCurrentProgram()
    print(f"Program: {program.getName()}")
    print(f"Language: {program.getLanguageID()}")
    print(f"Functions: {program.getFunctionManager().getFunctionCount()}")
```

실행:
```bash
python test_pyghidra.py
```

**성공 시**:
```
pyghidra version: 2.2.0
Ghidra path: /opt/homebrew/Cellar/ghidra/11.4.2/libexec
Program: DDMAIN.EXE
Language: x86:Real Mode:16:default
Functions: 161
```

---

### 3. Python 환경

**필수 패키지**:
```bash
pip install pyghidra==2.2.0
pip install jpype1  # pyghidra 의존성
```

**유용한 추가 패키지**:
```bash
pip install rich         # 터미널 출력 포매팅
pip install tqdm         # 프로그레스 바
pip install click        # CLI 인터페이스
pip install networkx     # 호출 그래프 분석
pip install matplotlib   # 시각화
```

#### requirements.txt

```text
pyghidra==2.2.0
jpype1>=1.4.1
rich>=13.0.0
tqdm>=4.65.0
click>=8.1.0
networkx>=3.0
matplotlib>=3.7.0
```

설치:
```bash
pip install -r requirements.txt
```

---

## 🎨 선택 도구

### 4. Spice86 (강력 추천)

**왜 유용한가?**
- x86 에뮬레이터 + 디컴파일러
- **호출 그래프 생성** (ExecutionFlow.json)
- 실행 흐름 추적으로 중요 함수 빠르게 파악
- Double Dragon에서 2배 효율 증가 확인

#### 설치

```bash
# .NET 8.0 SDK 설치 (Spice86 요구사항)
# macOS
brew install dotnet@8

# 환경 변수
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"

# Ubuntu/Debian
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --version 8.0
export DOTNET_ROOT=$HOME/.dotnet
export PATH=$PATH:$DOTNET_ROOT

# Windows
# https://dotnet.microsoft.com/download/dotnet/8.0 에서 다운로드
```

```bash
# Spice86 다운로드
# https://github.com/OpenRakis/Spice86/releases
wget https://github.com/OpenRakis/Spice86/releases/download/v2.x.x/Spice86-linux-x64.tar.gz

# 압축 해제
tar -xzf Spice86-linux-x64.tar.gz
sudo mv Spice86 /opt/spice86
export PATH="/opt/spice86:$PATH"
```

#### 검증

```bash
# Spice86 실행
./Spice86 --help

# 게임 실행 테스트
./Spice86 DDMAIN.EXE --dumpDataOnExit --recordedDataDirectory ./output
```

**성공 시**: 게임이 실행되고, 종료 시 `./output/ExecutionFlow.json` 생성

#### ExecutionFlow.json 사용

```python
# analyze_callgraph.py
import json
from collections import Counter

with open('output/ExecutionFlow.json') as f:
    data = json.load(f)

# 함수 호출 빈도 분석
call_counts = Counter()
for call in data.get('calls', []):
    target = call.get('target')
    if target:
        call_counts[target] += 1

# 상위 20개 함수 (가장 중요)
print("Top 20 Most Called Functions:")
for addr, count in call_counts.most_common(20):
    print(f"  0x{addr:04x}: {count:>6,} calls")
```

**출력 예시**:
```
Top 20 Most Called Functions:
  0x28c0:  4,127 calls  (스프라이트 블리팅)
  0x0a8b:  3,892 calls  (엔티티 업데이트)
  0x2865:  2,456 calls  (RLE 압축 해제)
  ...
```

**활용**:
- 호출 빈도 = 중요도
- 상위 20개 함수를 우선 분석 → 전체 흐름 80% 이해

---

### 5. DOSBox-X

**왜 유용한가?**
- DOS 게임 실행 및 테스트
- 내장 디버거 (breakpoint, memory inspection)
- 레거시 동작 완벽 재현

#### 설치

```bash
# macOS
brew install dosbox-x

# Ubuntu/Debian
sudo add-apt-repository ppa:dosbox-x/ppa
sudo apt update
sudo apt install dosbox-x

# Windows
# https://dosbox-x.com/ 에서 다운로드
```

#### 검증

```bash
# DOSBox-X 실행
dosbox-x

# 게임 실행
dosbox-x DDMAIN.EXE
```

#### 디버거 사용

DOSBox-X 실행 중:
```
Alt+Pause  # 디버거 열기

# 디버거 명령어
bp 1000:0000     # Breakpoint at CS:IP
r                # 레지스터 보기
d 1000:16c6      # 메모리 덤프 (엔티티 배열)
s 1000:0 ffff AA # 메모리 검색 (0xAA)
g                # 계속 실행
```

**활용**:
- 특정 메모리 주소 실시간 관찰
- 브레이크포인트로 실행 흐름 추적
- Ghidra 분석 결과 검증

---

### 6. Hex Editor (HxD, xxd)

**왜 유용한가?**
- 바이너리 구조 직접 확인
- 압축 데이터 매직 넘버 탐지
- 오프셋 계산 검증

#### 설치

```bash
# macOS/Linux (xxd 내장)
xxd DDMAIN.EXE | head -20

# HxD (Windows 전용)
# https://mh-nexus.de/en/hxd/ 에서 다운로드

# ImHex (크로스플랫폼)
brew install imhex  # macOS
```

#### 사용 예시

```bash
# 매직 넘버 찾기 (LZW 압축)
xxd LINDA.EG1 | grep "1f 9d"

# 특정 오프셋 확인
xxd -s 0x1000 -l 256 DDMAIN.EXE

# 바이너리 비교
xxd file1.bin > file1.hex
xxd file2.bin > file2.hex
diff file1.hex file2.hex
```

---

## ✅ 환경 검증

### 통합 검증 스크립트

```bash
#!/bin/bash
# verify_environment.sh

echo "=== DOS Game RE Environment Verification ==="
echo ""

# 1. Python
echo "[1/6] Python 3.9+"
python3 --version || echo "❌ Python not found"
echo ""

# 2. Ghidra
echo "[2/6] Ghidra 11.4.2"
if [ -z "$GHIDRA_INSTALL_DIR" ]; then
    echo "❌ GHIDRA_INSTALL_DIR not set"
else
    echo "✅ $GHIDRA_INSTALL_DIR"
    ls "$GHIDRA_INSTALL_DIR/Ghidra/Features/" > /dev/null 2>&1 || echo "❌ Invalid path"
fi
echo ""

# 3. pyghidra
echo "[3/6] pyghidra"
python3 -c "import pyghidra; print(f'✅ version {pyghidra.__version__}')" 2>/dev/null || echo "❌ pyghidra not installed"
echo ""

# 4. Spice86 (optional)
echo "[4/6] Spice86 (optional)"
command -v Spice86 > /dev/null && echo "✅ Spice86 found" || echo "⚠️  Spice86 not found (optional)"
echo ""

# 5. DOSBox-X (optional)
echo "[5/6] DOSBox-X (optional)"
command -v dosbox-x > /dev/null && echo "✅ DOSBox-X found" || echo "⚠️  DOSBox-X not found (optional)"
echo ""

# 6. Git
echo "[6/6] Git"
git --version || echo "❌ Git not found"
echo ""

echo "=== Verification Complete ==="
```

실행:
```bash
chmod +x verify_environment.sh
./verify_environment.sh
```

**예상 출력**:
```
=== DOS Game RE Environment Verification ===

[1/6] Python 3.9+
Python 3.11.5
✅

[2/6] Ghidra 11.4.2
✅ /opt/homebrew/Cellar/ghidra/11.4.2/libexec

[3/6] pyghidra
✅ version 2.2.0

[4/6] Spice86 (optional)
✅ Spice86 found

[5/6] DOSBox-X (optional)
✅ DOSBox-X found

[6/6] Git
git version 2.39.2

=== Verification Complete ===
```

---

### 기능 검증 테스트

#### 1. Ghidra + pyghidra 통합 테스트

```python
# test_decompile.py
import pyghidra
import sys

def test_decompile(exe_path):
    """단일 함수 디컴파일 테스트"""
    print(f"Testing decompilation on {exe_path}")

    with pyghidra.open_program(exe_path) as flat_api:
        program = flat_api.getCurrentProgram()
        fm = program.getFunctionManager()

        # 첫 번째 함수 찾기
        func = fm.getFunctions(True).next()
        if func:
            print(f"✅ Found function: {func.getName()} @ {func.getEntryPoint()}")

            # 디컴파일 시도
            from ghidra.app.decompiler import DecompInterface
            decompiler = DecompInterface()
            decompiler.openProgram(program)
            result = decompiler.decompileFunction(func, 30, None)

            if result.decompileCompleted():
                print(f"✅ Decompilation successful")
                print(f"   First 3 lines:")
                code = result.getDecompiledFunction().getC()
                for line in code.split('\n')[:3]:
                    print(f"   {line}")
                return True
            else:
                print(f"❌ Decompilation failed")
                return False
        else:
            print(f"❌ No functions found")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_decompile.py <path_to_exe>")
        sys.exit(1)

    success = test_decompile(sys.argv[1])
    sys.exit(0 if success else 1)
```

실행:
```bash
python test_decompile.py DDMAIN.EXE
```

**성공 시**:
```
Testing decompilation on DDMAIN.EXE
✅ Found function: FUN_1000_0000 @ 1000:0000
✅ Decompilation successful
   First 3 lines:
   undefined2 FUN_1000_0000(void)
   {
     uint uVar1;
```

#### 2. Spice86 호출 그래프 테스트

```bash
# 게임 실행 후 호출 그래프 생성
./Spice86 DDMAIN.EXE --dumpDataOnExit --recordedDataDirectory ./test_output

# ExecutionFlow.json 생성 확인
ls -lh test_output/ExecutionFlow.json

# JSON 유효성 검사
python3 -m json.tool test_output/ExecutionFlow.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
```

---

## 🔧 일반적인 문제 해결

### 문제 1: pyghidra 임포트 실패

**증상**:
```python
>>> import pyghidra
Traceback (most recent call last):
  ...
jpype._jvmfinder.JVMNotFoundException: No JVM shared library file found
```

**원인**: Java가 설치되지 않았거나 경로 문제

**해결**:
```bash
# macOS
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Ubuntu
sudo apt install default-jdk

# Windows
# https://adoptium.net/ 에서 JDK 17 설치
# 환경 변수 JAVA_HOME 설정
```

검증:
```bash
echo $JAVA_HOME
java --version
```

---

### 문제 2: GHIDRA_INSTALL_DIR 인식 안됨

**증상**:
```python
>>> import pyghidra
RuntimeError: Failed to find Ghidra installation
```

**원인**: 환경 변수 미설정 또는 잘못된 경로

**해결**:
```bash
# Ghidra 설치 위치 찾기
# macOS Homebrew
brew info ghidra  # 경로 확인
export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"

# 수동 설치
export GHIDRA_INSTALL_DIR="/opt/ghidra"  # 실제 경로로 변경

# 영구 설정 (~/.zshrc 또는 ~/.bashrc에 추가)
echo 'export GHIDRA_INSTALL_DIR="/opt/homebrew/Cellar/ghidra/11.4.2/libexec"' >> ~/.zshrc
source ~/.zshrc
```

검증:
```bash
ls $GHIDRA_INSTALL_DIR/Ghidra/Features/
# Decompiler/, Base/ 등이 보여야 함
```

---

### 문제 3: Ghidra 자동 분석 실패

**증상**: "Analysis failed" 또는 함수가 제대로 인식되지 않음

**원인**: x86 Real Mode 16-bit 설정 누락

**해결**:
1. Ghidra에서 바이너리 다시 임포트
2. Format: `MS-DOS Executable (MZ)` 확인
3. Language: `x86:Real Mode:16:default` 선택 (중요!)
4. Auto Analysis 옵션 확인:
   - ✅ Decompiler Parameter ID
   - ✅ Function Start Search
   - ✅ Subroutine References
5. 재분석: Analysis → Auto Analyze → "Analyze Now"

---

### 문제 4: Spice86 .NET 런타임 오류

**증상**:
```
You must install .NET to run this application.
```

**원인**: .NET 8.0 SDK 없음

**해결**:
```bash
# macOS
brew install dotnet@8
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"

# Ubuntu
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --version 8.0
export DOTNET_ROOT=$HOME/.dotnet
export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools

# 검증
dotnet --version
```

---

### 문제 5: pyghidra 디컴파일 시 타임아웃

**증상**: 큰 함수 디컴파일 시 `DecompileException: Timeout`

**해결**:
```python
# 타임아웃 증가 (기본 30초)
result = decompiler.decompileFunction(func, 120, None)  # 120초로 증가

# 또는 간단한 함수만 처리 (조건부 스킵)
if func.getBody().getNumAddresses() > 1000:
    print(f"Skipping large function: {func.getName()}")
    continue
```

---

### 문제 6: ExecutionFlow.json 생성 안됨

**증상**: Spice86 실행 후 JSON 파일 없음

**원인**:
- `--dumpDataOnExit` 플래그 누락
- 게임이 정상 종료되지 않음
- 권한 문제

**해결**:
```bash
# 올바른 명령어
./Spice86 DDMAIN.EXE --dumpDataOnExit --recordedDataDirectory ./output

# 게임 정상 종료 확인 (ESC로 나가기)
# 강제 종료(Ctrl+C)하면 JSON 생성 안됨

# 권한 확인
chmod -R 755 ./output
```

---

## 🚀 고급 설정

### Docker 환경 (재현성 보장)

**장점**:
- 모든 의존성 포함
- OS 무관하게 동일한 환경
- 팀 협업 시 유용

```dockerfile
# Dockerfile
FROM ubuntu:22.04

# 기본 도구 설치
RUN apt update && apt install -y \
    python3.11 python3-pip \
    default-jdk \
    git wget unzip

# Ghidra 설치
RUN wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.4.2_build/ghidra_11.4.2_PUBLIC_20250207.zip \
    && unzip ghidra_11.4.2_PUBLIC_20250207.zip \
    && mv ghidra_11.4.2_PUBLIC /opt/ghidra \
    && rm ghidra_11.4.2_PUBLIC_20250207.zip

ENV GHIDRA_INSTALL_DIR=/opt/ghidra

# Python 패키지
RUN pip3 install pyghidra==2.2.0 rich tqdm

WORKDIR /workspace

CMD ["/bin/bash"]
```

빌드 및 실행:
```bash
docker build -t dos-re-env .
docker run -it -v $(pwd):/workspace dos-re-env

# 컨테이너 내부
python3 test_pyghidra.py DDMAIN.EXE
```

---

### 자동화된 설정 스크립트

```bash
#!/bin/bash
# setup_all.sh - 모든 도구 한번에 설치 (Ubuntu/Debian)

set -e

echo "=== Installing DOS Game RE Tools ==="

# 1. 기본 도구
sudo apt update
sudo apt install -y python3 python3-pip default-jdk git wget unzip

# 2. Ghidra
GHIDRA_VERSION="11.4.2"
GHIDRA_ZIP="ghidra_${GHIDRA_VERSION}_PUBLIC_20250207.zip"
wget "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/${GHIDRA_ZIP}"
unzip "$GHIDRA_ZIP"
sudo mv "ghidra_${GHIDRA_VERSION}_PUBLIC" /opt/ghidra
rm "$GHIDRA_ZIP"

# 3. 환경 변수
echo 'export GHIDRA_INSTALL_DIR="/opt/ghidra"' >> ~/.bashrc
echo 'export PATH="$GHIDRA_INSTALL_DIR:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Python 패키지
pip3 install pyghidra==2.2.0 rich tqdm click networkx matplotlib

# 5. Spice86 (optional)
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --version 8.0
echo 'export DOTNET_ROOT=$HOME/.dotnet' >> ~/.bashrc
echo 'export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools' >> ~/.bashrc
source ~/.bashrc

# 6. DOSBox-X (optional)
sudo add-apt-repository ppa:dosbox-x/ppa -y
sudo apt update
sudo apt install dosbox-x -y

echo "=== Installation Complete ==="
echo "Run: source ~/.bashrc"
echo "Test: python3 test_pyghidra.py"
```

실행:
```bash
chmod +x setup_all.sh
./setup_all.sh
```

---

### GitHub Actions CI (자동 검증)

```yaml
# .github/workflows/verify-environment.yml
name: Verify RE Environment

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Java
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '17'

    - name: Install Ghidra
      run: |
        wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.4.2_build/ghidra_11.4.2_PUBLIC_20250207.zip
        unzip ghidra_11.4.2_PUBLIC_20250207.zip
        mv ghidra_11.4.2_PUBLIC /opt/ghidra
        echo "GHIDRA_INSTALL_DIR=/opt/ghidra" >> $GITHUB_ENV

    - name: Install Python dependencies
      run: |
        pip install pyghidra==2.2.0

    - name: Test environment
      run: |
        python test_pyghidra.py DDMAIN.EXE
```

---

## 📋 빠른 시작 체크리스트

### Phase 0 준비 (5분)

- [ ] **Python 3.9+** 설치 확인 (`python3 --version`)
- [ ] **Java 17+** 설치 확인 (`java --version`)
- [ ] **Ghidra 11.4.2** 설치 및 `GHIDRA_INSTALL_DIR` 설정
- [ ] **pyghidra 2.2.0** 설치 (`pip install pyghidra==2.2.0`)
- [ ] **환경 검증 스크립트** 실행 (`./verify_environment.sh`)
- [ ] **통합 테스트** 성공 (`python test_decompile.py DDMAIN.EXE`)

### Phase 0+ 선택 도구 (15분)

- [ ] **Spice86** 설치 (.NET 8.0 + Spice86 바이너리)
- [ ] **DOSBox-X** 설치 (게임 실행 테스트)
- [ ] **Hex Editor** 설치 (xxd, HxD, ImHex 중 선택)
- [ ] **Git** 저장소 초기화 (`git init`)

### Phase 0++ 고급 설정 (30분, 선택)

- [ ] **Docker** 환경 구축 (팀 협업 시)
- [ ] **GitHub Actions** 설정 (CI/CD)
- [ ] **자동화 스크립트** 준비 (`batch_decompile.py` 등)

---

## 🎯 다음 단계

환경 설정 완료 후:

1. **[03_DECOMPILATION.md](03_DECOMPILATION.md)** - 디컴파일 전략 및 자동화
2. **[04_ANALYSIS_TECHNIQUES.md](04_ANALYSIS_TECHNIQUES.md)** - 9가지 핵심 분석 기법
3. **[01_PROCESS_OVERVIEW.md](01_PROCESS_OVERVIEW.md)** - 전체 프로세스 확인

---

## 📚 추가 자료

### 공식 문서
- [Ghidra 공식 사이트](https://ghidra-sre.org/)
- [pyghidra GitHub](https://github.com/VDOO-Connected-Trust/pyghidra)
- [Spice86 GitHub](https://github.com/OpenRakis/Spice86)

### 커뮤니티
- [Ghidra 커뮤니티](https://github.com/NationalSecurityAgency/ghidra/discussions)
- [r/ReverseEngineering](https://www.reddit.com/r/ReverseEngineering/)

### 참고 프로젝트
- Double Dragon 분석: `../archive/phase4-analysis/`
- 호출 그래프 스크립트: `scripts/analyze_callgraph.py`
- 배치 디컴파일: `scripts/batch_decompile.py`

---

## ⚠️ 주의사항

1. **버전 중요**: Ghidra 11.4.2, pyghidra 2.2.0 추천 (검증됨)
2. **환경 변수 필수**: `GHIDRA_INSTALL_DIR` 반드시 설정
3. **Java 버전**: 17 이상 필요 (Ghidra 요구사항)
4. **가상환경 권장**: Python 패키지 충돌 방지
5. **경로에 공백 금지**: Ghidra/Java 경로에 공백 있으면 오류

---

**작성일**: 2025-01-24
**버전**: 1.0
**검증 환경**: macOS 14.x, Ubuntu 22.04, Python 3.11, Ghidra 11.4.2, pyghidra 2.2.0

**다음 문서**: [03_DECOMPILATION.md](03_DECOMPILATION.md) - 배치 디컴파일 전략
**이전 문서**: [01_PROCESS_OVERVIEW.md](01_PROCESS_OVERVIEW.md) - 프로세스 개요
