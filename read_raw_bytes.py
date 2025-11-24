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
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    
    # 1988:18da 주소 계산
    seg = 0x1988
    offset = 0x18da
    addr = addr_space.getAddress((seg << 4) + offset)
    
    print(f"주소 {seg:04x}:{offset:04x} (물리: 0x{(seg << 4) + offset:05x})")
    print("\n22 bytes (11 words):")
    
    for i in range(11):
        word_addr = addr.add(i * 2)
        low = memory.getByte(word_addr) & 0xFF
        high = memory.getByte(word_addr.add(1)) & 0xFF
        word = (high << 8) | low
        print(f"  [{i:2d}] @ +{i*2:02x}: {high:02x} {low:02x} = 0x{word:04x}")
