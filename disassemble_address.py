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
