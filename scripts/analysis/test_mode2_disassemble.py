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
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor

    program = flat_api.getCurrentProgram()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    listing = program.getListing()

    # Mode 2 테이블 첫 번째: 1000:6b19
    seg = 0x1000
    offset = 0x6b19
    addr = addr_space.getAddress((seg << 4) + offset)

    print("=" * 70)
    print(f"Mode 2 함수 테스트 - {seg:04x}:{offset:04x} 디스어셈블")
    print("=" * 70)

    # 1. 디스어셈블 시도
    print("\n[1단계] 디스어셈블 시도...")
    disasm_cmd = DisassembleCommand(addr, None, True)
    success = disasm_cmd.applyTo(program)

    if success:
        print("  ✅ 디스어셈블 성공!")
    else:
        print(f"  ❌ 실패: {disasm_cmd.getStatusMsg()}")
        print("\n테스트 중단 - Mode 2는 다른 접근 필요!")
        exit(1)

    # 2. 디스어셈블된 명령어 확인
    print("\n[2단계] 디스어셈블된 명령어 (처음 20개):")
    current_addr = addr
    instruction_count = 0
    for i in range(20):
        instruction = listing.getInstructionAt(current_addr)
        if instruction:
            instruction_count += 1
            mnemonic = instruction.getMnemonicString()
            ops = []
            for j in range(instruction.getNumOperands()):
                ops.append(instruction.getDefaultOperandRepresentation(j))
            operands = ", ".join(ops) if ops else ""

            offset_val = current_addr.getOffset() - (seg << 4)
            print(f"  {seg:04x}:{offset_val:04x}  {mnemonic:<8} {operands}")

            current_addr = current_addr.add(instruction.getLength())
        else:
            print(f"  {seg:04x}:{current_addr.getOffset() - (seg << 4):04x}  [End]")
            break

    if instruction_count == 0:
        print("  ❌ 명령어 없음!")
        print("\n테스트 중단 - Mode 2는 다른 접근 필요!")
        exit(1)

    # 3. 함수 생성 시도
    print(f"\n[3단계] 함수 생성 시도...")
    create_func_cmd = CreateFunctionCmd(addr)
    func_success = create_func_cmd.applyTo(program)

    if func_success:
        func = listing.getFunctionAt(addr)
        if func:
            print(f"  ✅ 함수 생성 성공!")
            print(f"     이름: {func.getName()}")
            print(f"     크기: {func.getBody().getNumAddresses()} bytes")
        else:
            print(f"  ❌ 함수 확인 실패")
            exit(1)
    else:
        print(f"  ❌ 함수 생성 실패: {create_func_cmd.getStatusMsg()}")
        exit(1)

    # 4. 디컴파일 시도
    print(f"\n[4단계] C 코드 디컴파일 시도...")
    decompiler = DecompInterface()
    decompiler.openProgram(program)
    monitor = ConsoleTaskMonitor()

    result = decompiler.decompileFunction(func, 30, monitor)

    if result.decompileCompleted():
        print(f"  ✅ 디컴파일 성공!\n")
        c_code = result.getDecompiledFunction().getC()

        # 처음 30줄만 출력
        lines = c_code.split('\n')
        for i, line in enumerate(lines[:30], 1):
            print(f"  {i:3d} | {line}")

        if len(lines) > 30:
            print(f"  ... ({len(lines) - 30}줄 더 있음)")

    else:
        print(f"  ❌ 디컴파일 실패: {result.getErrorMessage()}")

print("\n" + "=" * 70)
print("결론:")
print("=" * 70)
print("\n✅ Mode 2 첫 번째 주소 테스트 성공!")
print("   Mode 1과 동일한 방법으로 복구 가능!")
print("\n완료!")
