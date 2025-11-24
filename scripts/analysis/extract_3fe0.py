#!/usr/bin/env python3
import os
from pathlib import Path

os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

import pyghidra

PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

print("Ghidra 초기화...")
pyghidra.start(verbose=False)

with pyghidra.open_program(BINARY_PATH, project_location=PROJECT_PATH,
                           project_name=PROJECT_NAME, analyze=False) as flat_api:
    program = flat_api.getCurrentProgram()
    listing = program.getListing()
    address_space = program.getAddressFactory().getDefaultAddressSpace()

    CODE_SEGMENT = 0x1000
    offset = 0x3fe0
    addr = address_space.getAddress((CODE_SEGMENT << 4) + offset)

    func = flat_api.getFunctionAt(addr)
    if func:
        print(f"FUN_1000_3fe0 (20 bytes)\n")

        # 디스어셈블리
        lines = []
        code_units = listing.getCodeUnits(func.getBody(), True)
        for cu in code_units:
            if cu.toString().strip():
                instr = f"{cu.getAddress()}  {cu}"
                lines.append(instr)
                print(instr)

        # 저장
        Path("output/decompiled/FUN_1000_3fe0.asm").write_text('\n'.join(lines))

        # 호출자
        print(f"\n호출자:")
        refs = flat_api.getReferencesTo(addr)
        for ref in refs:
            from_addr = ref.getFromAddress()
            containing = flat_api.getFunctionContaining(from_addr)
            if containing:
                print(f"  {containing.getName()} @ {from_addr}")

print("\n완료!")
