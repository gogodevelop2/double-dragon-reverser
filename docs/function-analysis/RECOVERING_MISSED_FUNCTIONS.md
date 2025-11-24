# Ghidra가 놓친 함수 복구 과정

**날짜**: 2025-11-24
**대상**: 함수 포인터 테이블이 가리키는 숨겨진 함수들
**첫 사례**: `1000:5e55` (Mode 1 테이블 인덱스 1)

---

## 🎯 문제 발견

### 상황
함수 포인터 테이블 분석 중, 테이블에 저장된 주소들이 디컴파일된 함수 목록에 **없음**을 발견:

```python
# Mode 1 테이블 (1988:18da)에서 읽은 주소들
0x5f07, 0x5e55, 0x8492, 0x84ee, 0x8583, 0x853d,
0x8622, 0x7eb0, 0x5aaa, 0x5b5f, 0x5c0a

# 확인:
$ ls output/decompiled/FUN_1000_5e55.c
ls: FUN_1000_5e55.c: No such file or directory
```

### 초기 가설들
1. 함수가 실제로 없다? ❌
2. 데이터 영역이다? ❌
3. 동적 코드 생성? ❓
4. Ghidra 분석 실패? ⭐ **정답!**

---

## 🔍 원인 분석

### 왜 Ghidra가 놓쳤는가?

#### 1. 간접 점프만 존재
```c
// FUN_1000_48e0 (디스패처 함수)
void FUN_1000_48e0(void) {
    /* WARNING: Could not recover jumptable */
    /* WARNING: Treating indirect jump as call */
    (*(code *)*(undefined2 *)0x18c6)();
}
```

- 직접 `CALL 1000:5e55` 없음
- 함수 포인터를 통한 **간접 점프**만 존재
- Ghidra의 자동 제어 흐름 분석이 추적 실패

#### 2. Entry Point에서 도달 불가
- `DDMAIN.EXE` 진입점에서 시작하는 제어 흐름 그래프에 포함 안 됨
- 함수 포인터 테이블이 초기화된 **후**에만 도달 가능
- Ghidra가 "도달 불가능한 코드"로 간주

#### 3. Ghidra 경고 메시지
```
WARNING: Could not recover jumptable at 0x000148e0
```
이게 핵심 힌트였음!

---

## ✅ 복구 과정 (단계별)

### Phase 1: 존재 확인

**목적**: 해당 주소에 실제로 코드가 있는지 확인

**도구**: `check_address.py`

```python
import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
import pyghidra

pyghidra.start(verbose=False)

with pyghidra.open_program(
    Path("reference/dos-original/DDMAIN.EXE").absolute(),
    project_location=Path("ghidra-project").absolute(),
    project_name="DoubleDragon",
    analyze=False
) as flat_api:
    program = flat_api.getCurrentProgram()
    memory = program.getMemory()
    listing = program.getListing()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()

    # 1000:5e55 확인
    seg = 0x1000
    offset = 0x5e55
    addr = addr_space.getAddress((seg << 4) + offset)

    print(f"=== 주소 {seg:04x}:{offset:04x} 분석 ===\n")

    # 1. 바이트 확인 (32 bytes)
    print("Raw bytes (32 bytes):")
    for i in range(32):
        byte = memory.getByte(addr.add(i)) & 0xFF
        if i % 16 == 0:
            print(f"\n{seg:04x}:{offset+i:04x}  ", end="")
        print(f"{byte:02x} ", end="")
    print("\n")

    # 2. 명령어로 해석 시도
    print("Disassembly:")
    for i in range(10):
        inst_addr = addr.add(i)
        instruction = listing.getInstructionAt(inst_addr)
        if instruction:
            mnemonic = instruction.getMnemonicString()
            operands = instruction.getDefaultOperandRepresentation(0) if instruction.getNumOperands() > 0 else ""
            print(f"{seg:04x}:{offset+i:04x}  {mnemonic:<8} {operands}")
        else:
            print(f"{seg:04x}:{offset+i:04x}  [No instruction]")
            break

    # 3. 데이터 타입 확인
    print("\nData type:")
    data = listing.getDataAt(addr)
    if data:
        print(f"  Type: {data.getDataType().getName()}")
    else:
        print(f"  Not defined as data")

print("\n완료!")
```

**실행**:
```bash
source venv/bin/activate
python check_address.py
```

**결과**:
```
=== 주소 1000:5e55 분석 ===

Raw bytes (32 bytes):
1000:5e55  bf 40 46 b9 07 00 8a 05 8a e0 d0 e8 d0 e8 03 c0
1000:5e65  03 c0 bb 00 88 2e 8b 5f 0e d7 47 47 49 75 e9 5f

Disassembly:
1000:5e55  [No instruction]
1000:5e56  [No instruction]
...

Data type:
  Not defined as data
```

**결론**:
- ✅ 바이트 데이터 존재 (`bf 40 46 b9 07 00...`)
- ❌ Ghidra가 명령어로 해석 안 함
- ❌ 데이터로도 정의 안 됨
- 🎯 **분류되지 않은 영역** (undefined)

**수동 디스어셈블**:
```
bf 40 46     MOV  DI, 0x4640
b9 07 00     MOV  CX, 0x0007
8a 05        MOV  AL, byte ptr [DI]
8a e0        MOV  AH, AL
...
```
→ **유효한 x86 코드!**

---

### Phase 2: 강제 디스어셈블

**목적**: Ghidra에게 강제로 코드 분석시키기

**도구**: `disassemble_address.py`

```python
import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
import pyghidra

pyghidra.start(verbose=False)

with pyghidra.open_program(
    Path("reference/dos-original/DDMAIN.EXE").absolute(),
    project_location=Path("ghidra-project").absolute(),
    project_name="DoubleDragon",
    analyze=False
) as flat_api:

    from ghidra.app.cmd.disassemble import DisassembleCommand
    from ghidra.app.cmd.function import CreateFunctionCmd

    program = flat_api.getCurrentProgram()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    listing = program.getListing()

    # 1000:5e55 주소
    seg = 0x1000
    offset = 0x5e55
    addr = addr_space.getAddress((seg << 4) + offset)

    print(f"=== {seg:04x}:{offset:04x} 강제 디스어셈블 ===\n")

    # 1. 디스어셈블 명령 실행
    print("1. 디스어셈블 시도...")
    disasm_cmd = DisassembleCommand(addr, None, True)  # True = 재귀적 디스어셈블
    success = disasm_cmd.applyTo(program)

    if success:
        print("   ✅ 디스어셈블 성공!")
    else:
        print(f"   ❌ 실패: {disasm_cmd.getStatusMsg()}")

    # 2. 명령어 확인
    print("\n2. 디스어셈블된 명령어 (처음 20개):")
    current_addr = addr
    for i in range(20):
        instruction = listing.getInstructionAt(current_addr)
        if instruction:
            mnemonic = instruction.getMnemonicString()
            ops = []
            for j in range(instruction.getNumOperands()):
                ops.append(instruction.getDefaultOperandRepresentation(j))
            operands = ", ".join(ops) if ops else ""

            offset_val = current_addr.getOffset() - (seg << 4)
            print(f"   {seg:04x}:{offset_val:04x}  {mnemonic:<8} {operands}")

            current_addr = current_addr.add(instruction.getLength())
        else:
            print(f"   {seg:04x}:{current_addr.getOffset() - (seg << 4):04x}  [No instruction]")
            break

    # 3. 함수 생성 시도
    print("\n3. 함수 생성 시도...")
    create_func_cmd = CreateFunctionCmd(addr)
    func_success = create_func_cmd.applyTo(program)

    if func_success:
        print("   ✅ 함수 생성 성공!")
        func = listing.getFunctionAt(addr)
        if func:
            print(f"   함수 이름: {func.getName()}")
            print(f"   함수 크기: {func.getBody().getNumAddresses()} bytes")
    else:
        print(f"   ❌ 실패: {create_func_cmd.getStatusMsg()}")

print("\n완료!")
```

**실행**:
```bash
python disassemble_address.py
```

**결과**:
```
=== 1000:5e55 강제 디스어셈블 ===

1. 디스어셈블 시도...
   ✅ 디스어셈블 성공!

2. 디스어셈블된 명령어 (처음 20개):
   1000:5e55  MOV      DI, 0x4640
   1000:5e58  MOV      CX, 0x7
   1000:5e5b  MOV      AL, byte ptr [DI]
   1000:5e5d  MOV      AH, AL
   1000:5e5f  SHR      AL, 1
   1000:5e61  SHR      AL, 1
   1000:5e63  ADD      AX, AX
   1000:5e65  ADD      AX, AX
   1000:5e67  MOV      BX, 0x8800
   1000:5e6a  MOV      BX, word ptr CS:[BX + 0xe]
   1000:5e6e  XLAT
   1000:5e6f  INC      DI
   1000:5e70  INC      DI
   1000:5e71  DEC      CX
   1000:5e72  JNZ      0x5e5b
   1000:5e74  POP      DI
   ...

3. 함수 생성 시도...
   ✅ 함수 생성 성공!
   함수 이름: FUN_1000_5e55
   함수 크기: 178 bytes
```

**결론**:
- ✅ 디스어셈블 성공
- ✅ 유효한 x86 명령어 확인
- ✅ 함수 생성 성공 (178 bytes)
- 🎯 **Ghidra 프로젝트에 함수 추가됨**

---

### Phase 3: C 코드 디컴파일

**목적**: 어셈블리를 읽기 쉬운 C 코드로 변환

**도구**: `decompile_new_function.py`

```python
import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
import pyghidra

pyghidra.start(verbose=False)

with pyghidra.open_program(
    Path("reference/dos-original/DDMAIN.EXE").absolute(),
    project_location=Path("ghidra-project").absolute(),
    project_name="DoubleDragon",
    analyze=False
) as flat_api:

    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor

    program = flat_api.getCurrentProgram()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    listing = program.getListing()

    # 1000:5e55 함수
    addr = addr_space.getAddress((0x1000 << 4) + 0x5e55)
    func = listing.getFunctionAt(addr)

    if not func:
        print("함수 없음!")
    else:
        print(f"=== {func.getName()} 디컴파일 ===\n")

        # 디컴파일러 초기화
        decompiler = DecompInterface()
        decompiler.openProgram(program)

        # 디컴파일 실행
        monitor = ConsoleTaskMonitor()
        result = decompiler.decompileFunction(func, 30, monitor)  # 30초 타임아웃

        if result.decompileCompleted():
            print("✅ 디컴파일 성공!\n")
            c_code = result.getDecompiledFunction().getC()
            print(c_code)
        else:
            print(f"❌ 디컴파일 실패: {result.getErrorMessage()}")

print("\n완료!")
```

**실행**:
```bash
python decompile_new_function.py
```

**결과**:
```
=== FUN_1000_5e55 디컴파일 ===

✅ 디컴파일 성공!

void FUN_1000_5e55(void)
{
  byte bVar1;
  uint uVar2;
  byte *pbVar3;
  uint uVar4;
  byte *pbVar5;
  undefined2 uStack_02;

  pbVar3 = (byte *)0x4640;
  for (uVar4 = 7; uVar4 != 0; uVar4 = uVar4 - 1) {
    bVar1 = *pbVar3;
    uVar2 = (uint)CONCAT11(bVar1,bVar1 >> 2) * 4;
    pbVar3 = pbVar3 + 2;
    bVar1 = (&DAT_1000_8800)
            [(int)*(undefined2 *)
                   ((int)&DAT_1000_8800 + (uint)*(byte *)((int)&DAT_1000_8800 + 0xe) * 2) +
            uVar2];
    pbVar5 = (byte *)((uint)uStack_02 * 0x50);
    pbVar5[(int)(short)DAT_1988_0010] = bVar1;
    pbVar5[(int)((short)DAT_1988_0010 + 1)] = bVar1;
    ...
  }
  return;
}
```

**결론**:
- ✅ C 코드 생성 성공
- 🎯 **그래픽 렌더링 함수**로 추정:
  - 0x4640 주소에서 데이터 읽기
  - 팔레트 테이블 (0x8800) 참조
  - 비디오 메모리 조작
  - 7회 반복 루프

---

## 📊 복구 결과

### FUN_1000_5e55 정보
- **주소**: `1000:5e55`
- **크기**: 178 bytes
- **기능**: 그래픽 데이터 처리 (추정)
- **특징**:
  - 팔레트 룩업 (`0x8800`)
  - 비디오 메모리 쓰기
  - 픽셀 데이터 변환

### 복구 전 vs 후

| 항목 | 복구 전 | 복구 후 |
|------|---------|---------|
| Ghidra 함수 인식 | ❌ 없음 | ✅ FUN_1000_5e55 |
| 디스어셈블리 | ❌ [No instruction] | ✅ 완전한 어셈블리 |
| 디컴파일 | ❌ 불가능 | ✅ C 코드 |
| 크기 | ❓ 알 수 없음 | ✅ 178 bytes |
| 제어 흐름 | ❓ 미추적 | ✅ 7-iteration 루프 |

---

## 🔧 사용된 Ghidra API

### 1. DisassembleCommand
```python
from ghidra.app.cmd.disassemble import DisassembleCommand

disasm_cmd = DisassembleCommand(addr, None, True)
success = disasm_cmd.applyTo(program)
```
- **목적**: 주소를 강제로 코드로 해석
- **매개변수**:
  - `addr`: 시작 주소
  - `None`: AddressSet (None = 자동)
  - `True`: 재귀적 디스어셈블 (제어 흐름 따라가기)

### 2. CreateFunctionCmd
```python
from ghidra.app.cmd.function import CreateFunctionCmd

create_func_cmd = CreateFunctionCmd(addr)
func_success = create_func_cmd.applyTo(program)
```
- **목적**: 디스어셈블된 코드를 함수로 그룹화
- **동작**:
  - 함수 경계 감지 (RET 명령어까지)
  - 스택 프레임 분석
  - 호출 규약 추론

### 3. DecompInterface
```python
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

decompiler = DecompInterface()
decompiler.openProgram(program)

monitor = ConsoleTaskMonitor()
result = decompiler.decompileFunction(func, 30, monitor)

if result.decompileCompleted():
    c_code = result.getDecompiledFunction().getC()
```
- **목적**: 어셈블리를 C 코드로 변환
- **매개변수**:
  - `func`: Function 객체
  - `30`: 타임아웃 (초)
  - `monitor`: 진행 상황 모니터

---

## 💡 핵심 교훈

### 1. Ghidra의 한계 이해
- 자동 분석은 **직접 제어 흐름**만 추적
- 함수 포인터, 점프 테이블, 동적 디스패치 → 추적 실패
- **수동 개입 필요**

### 2. 경고 메시지 주의
```
WARNING: Could not recover jumptable
WARNING: Treating indirect jump as call
```
→ 이런 경고가 나오면 **함수 포인터 테이블 존재** 의심!

### 3. 복구 가능성
- "함수가 없다" ≠ "코드가 없다"
- Ghidra가 못 찾았을 뿐, **바이너리에는 존재**
- pyghidra API로 복구 가능

### 4. 3단계 검증
1. **존재 확인**: 바이트 데이터 읽기
2. **디스어셈블**: 유효한 명령어인지 확인
3. **디컴파일**: 함수 로직 이해

### 5. 패턴 재사용
이제 동일한 방법으로 나머지 10개 주소 복구 가능:
- `1000:5f07`
- `1000:8492`
- `1000:84ee`
- ... (총 11개)

---

## 📋 다음 작업

### 즉시 진행
1. **나머지 10개 Mode 1 함수 복구**
   - 동일한 3단계 프로세스 적용
   - 각 함수 크기, 기능 기록

2. **Mode 2 테이블 (0x18f0) 11개 함수 복구**
   - Mode 1과 비교 분석
   - 차이점 문서화

### 후속 분석
3. **함수 기능 분류**
   - 그래픽 렌더링?
   - 입력 처리?
   - 게임 로직?

4. **호출 관계 매핑**
   - 어느 디스패처가 어느 함수를 호출?
   - 언제 Mode 1 vs Mode 2?

---

## 📂 생성된 파일

### 스크립트 (프로젝트 루트)
- `check_address.py` - 주소 존재 확인
- `disassemble_address.py` - 강제 디스어셈블
- `decompile_new_function.py` - C 코드 생성

### 문서 (docs/)
- `docs/function-analysis/FUNCTION_POINTER_TABLE_ANALYSIS.md` - 테이블 분석
- `docs/function-analysis/ANALYSIS_MISTAKES.md` - 분석 과정 실수 기록
- `docs/PYGHIDRA_GUIDE.md` - pyghidra 사용법
- **이 문서** - 함수 복구 과정

### Ghidra 프로젝트 변경
- `ghidra-project/DoubleDragon.rep/` - FUN_1000_5e55 추가됨

---

**작성일**: 2025-11-24
**상태**: 1/11 Mode 1 함수 복구 완료 (FUN_1000_5e55)
**방법론**: 확립됨 (재사용 가능)
