# pyghidra 사용 가이드

**작성일**: 2025-11-24

---

## ⚠️ 자주 하는 실수 (Common Mistakes)

### 1. 환경 변수 미설정

**문제**:
```python
import pyghidra
pyghidra.start()  # ❌ Java not found 에러
```

**해결**:
```python
import os

# 반드시 pyghidra import 전에 설정!
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

import pyghidra
pyghidra.start()  # ✅ 정상 작동
```

**중요**: 환경 변수는 `pyghidra` import **전에** 또는 import 직후에 설정해야 합니다!

---

### 2. 가상 환경 미활성화

**문제**:
```bash
$ python3 script.py
ModuleNotFoundError: No module named 'pyghidra'
```

**해결**:
```bash
$ source venv/bin/activate  # ✅ 가상 환경 활성화
(venv) $ python3 script.py
```

**확인**:
```bash
$ which python3
/Users/joejeon/Documents/develop/Double Dragon/venv/bin/python3  # ✅ venv 경로
```

---

### 3. 프로젝트 열기 실패 (파일 경로 오류)

**문제**:
```python
# ❌ 잘못된 방법
pyghidra.open_program("DoubleDragon", project_location="ghidra-project")
# 에러: File not found: DoubleDragon
```

**해결**:
```python
from pathlib import Path

# ✅ 올바른 방법
binary_path = Path("reference/dos-original/DDMAIN.EXE").absolute()
project_path = Path("ghidra-project").absolute()
project_name = "DoubleDragon"

pyghidra.open_program(
    binary_path,                    # 바이너리 파일 경로 (필수!)
    project_location=project_path,  # 프로젝트 디렉토리
    project_name=project_name,      # 프로젝트 이름
    analyze=False                   # 이미 분석 완료된 경우
)
```

**핵심**:
- **첫 번째 인자**는 바이너리 파일 경로 (DDMAIN.EXE)
- 프로젝트 이름이 아님!

---

### 4. DOS 세그먼트:오프셋 주소 계산 오류

**문제**:
```python
# ❌ 잘못된 주소 계산
addr = address_space.getAddress(0x18da)  # 데이터가 안 보임
```

**해결**:
```python
# ✅ 올바른 주소 계산
segment = 0x1988  # 데이터 세그먼트
offset = 0x18da   # 오프셋

# DOS real mode: segment * 16 + offset
physical_addr = (segment << 4) + offset  # 0x1b15a
addr = address_space.getAddress(physical_addr)
```

**세그먼트 구분**:
- **코드 세그먼트**: `0x1000` (함수 주소)
- **데이터 세그먼트**: `0x1988` (변수, 테이블)

**예시**:
```python
# 함수 주소: 1000:5f07
code_segment = 0x1000
offset = 0x5f07
func_addr = address_space.getAddress((code_segment << 4) + offset)

# 데이터 주소: 1988:18da
data_segment = 0x1988
offset = 0x18da
data_addr = address_space.getAddress((data_segment << 4) + offset)
```

---

### 5. 함수가 UNKNOWN으로 나오는 경우

**문제**:
```python
func = flat_api.getFunctionAt(some_address)
if func:
    print(func.getName())
else:
    print("UNKNOWN")  # ❌ 항상 UNKNOWN
```

**원인**:
1. 주소 계산 오류 (세그먼트 누락)
2. 함수 진입점이 아닌 중간 주소
3. Ghidra가 함수로 인식하지 못함

**해결 방법들**:

#### A. 주소 계산 다시 확인
```python
# DOS segment:offset → physical address
physical = (segment << 4) + offset
```

#### B. 함수 포함 여부 확인
```python
func = flat_api.getFunctionAt(addr)
if not func:
    # 해당 주소를 포함하는 함수 찾기
    func = flat_api.getFunctionContaining(addr)
    if func:
        print(f"[내부: {func.getName()}]")
```

#### C. 디컴파일 파일과 비교
```python
# 1000:5f07 → FUN_1000_5f07.c 파일 확인
offset_hex = f"{offset:04x}"
filename = f"output/decompiled/FUN_1000_{offset_hex}.c"
# 파일이 없으면 Ghidra가 함수로 인식 안 한 것
```

#### D. 메모리 덤프로 확인
```python
# 해당 주소의 바이트 확인
for i in range(10):
    byte = memory.getByte(addr.add(i)) & 0xFF
    print(f"{byte:02x}", end=" ")
```

---

## ✅ 표준 템플릿

프로젝트에서 사용할 표준 pyghidra 스크립트 템플릿:

```python
#!/usr/bin/env python3
"""
스크립트 설명
"""

import os
from pathlib import Path

# ⭐ 1. 환경 변수 설정 (가장 먼저!)
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# ⭐ 2. pyghidra import
import pyghidra

# ⭐ 3. 프로젝트 경로 설정
PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

# ⭐ 4. Ghidra 시작
print("Ghidra 초기화 중...")
pyghidra.start(verbose=False)

# ⭐ 5. 프로젝트 열기
with pyghidra.open_program(
    BINARY_PATH,
    project_location=PROJECT_PATH,
    project_name=PROJECT_NAME,
    analyze=False
) as flat_api:

    program = flat_api.getCurrentProgram()
    memory = program.getMemory()
    listing = program.getListing()
    address_space = program.getAddressFactory().getDefaultAddressSpace()

    # ⭐ 6. 세그먼트 정의
    CODE_SEGMENT = 0x1000   # 코드
    DATA_SEGMENT = 0x1988   # 데이터

    # ⭐ 7. 작업 수행
    # 함수 주소 예시: 1000:5f07
    offset = 0x5f07
    func_addr = address_space.getAddress((CODE_SEGMENT << 4) + offset)
    func = flat_api.getFunctionAt(func_addr)

    if func:
        print(f"함수: {func.getName()}")
    else:
        print("함수를 찾을 수 없습니다")

print("완료!")
```

---

## 🔧 실행 방법

### 터미널에서 실행
```bash
cd "/Users/joejeon/Documents/develop/Double Dragon"
source venv/bin/activate
python3 your_script.py
```

### 한 줄로 실행
```bash
cd "/Users/joejeon/Documents/develop/Double Dragon" && source venv/bin/activate && python3 your_script.py
```

---

## 📚 유용한 pyghidra API

### 주소 관련
```python
# 주소 생성
addr = address_space.getAddress(0x10000)

# 주소 이동
next_addr = addr.add(10)  # +10 bytes
prev_addr = addr.subtract(5)  # -5 bytes
```

### 함수 관련
```python
# 주소에 있는 함수
func = flat_api.getFunctionAt(addr)

# 주소를 포함하는 함수
func = flat_api.getFunctionContaining(addr)

# 함수 정보
if func:
    name = func.getName()                     # 함수 이름
    size = func.getBody().getNumAddresses()   # 크기
    entry = func.getEntryPoint()              # 진입점
```

### 메모리 읽기
```python
# 1바이트 읽기
byte = memory.getByte(addr) & 0xFF

# 2바이트 (워드) 읽기 - little endian
low = memory.getByte(addr) & 0xFF
high = memory.getByte(addr.add(1)) & 0xFF
word = (high << 8) | low

# 4바이트 (더블워드) 읽기
dword = memory.getInt(addr)
```

### 데이터 구조
```python
# 주소의 데이터 타입 확인
data = listing.getDataAt(addr)
if data:
    data_type = data.getDataType()
    print(f"타입: {data_type.getName()}")
```

---

## 🐛 디버깅 팁

### 1. verbose 모드 활성화
```python
pyghidra.start(verbose=True)  # 상세 로그 출력
```

### 2. 주소 확인
```python
print(f"주소: {addr}")
print(f"Hex: 0x{addr.getOffset():x}")
```

### 3. 메모리 덤프
```python
def dump_memory(addr, size=16):
    """메모리를 hexdump 형식으로 출력"""
    for i in range(0, size, 16):
        line_addr = addr.add(i)
        print(f"{line_addr}: ", end="")

        for j in range(16):
            if i + j < size:
                byte = memory.getByte(line_addr.add(j)) & 0xFF
                print(f"{byte:02x} ", end="")
            else:
                print("   ", end="")
        print()

dump_memory(some_address, 64)
```

### 4. 함수 목록
```python
# 모든 함수 출력
func_manager = program.getFunctionManager()
for func in func_manager.getFunctions(True):  # True = forward
    print(f"{func.getEntryPoint()}: {func.getName()}")
```

---

## 📖 참고 자료

- **pyghidra 공식 문서**: https://github.com/Defense-Cyber-Crime-Center/pyhidra
- **Ghidra API**: `$GHIDRA_INSTALL_DIR/docs/GhidraAPI_javadoc.zip`
- **프로젝트 예제**: `phase1_pyghidra_extract.py`, `find_string_refs_pyghidra.py`

---

**작성일**: 2025-11-24
**최종 업데이트**: 2025-11-24
