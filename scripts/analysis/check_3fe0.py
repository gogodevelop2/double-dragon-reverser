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
    address_space = program.getAddressFactory().getDefaultAddressSpace()

    CODE_SEGMENT = 0x1000
    offset = 0x3fe0
    addr = address_space.getAddress((CODE_SEGMENT << 4) + offset)

    func = flat_api.getFunctionAt(addr)
    if func:
        print(f"✅ FUN_1000_3fe0 존재!")
        print(f"  크기: {func.getBody().getNumAddresses()} bytes")
    else:
        containing = flat_api.getFunctionContaining(addr)
        if containing:
            print(f"❌ 1000:3fe0은 {containing.getName()} 내부")
        else:
            print(f"❌ 함수 없음")

print("완료!")
