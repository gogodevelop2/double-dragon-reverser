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
    
    # 2. 명령어로 해석
    print("Disassembly:")
    for i in range(10):  # 10개 명령어
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
    
    # 4. 참조 확인
    print("\nReferences TO this address:")
    refs = program.getReferenceManager().getReferencesTo(addr)
    count = 0
    for ref in refs:
        from_addr = ref.getFromAddress()
        print(f"  From: {from_addr}")
        count += 1
        if count >= 5:
            break
    if count == 0:
        print("  (none)")

print("\n완료!")
