#!/usr/bin/env python3
"""
0x16ef 영역 직접 확인
"""

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
    memory = program.getMemory()
    listing = program.getListing()
    address_space = program.getAddressFactory().getDefaultAddressSpace()

    CODE_SEGMENT = 0x1000
    table_offset = 0x16ef
    table_addr = address_space.getAddress((CODE_SEGMENT << 4) + table_offset)

    print(f"\n=== 1000:16ef 영역 디스어셈블리 ===\n")

    # 테이블 시작 부근 100 bytes 디스어셈블
    for i in range(50):
        addr = table_addr.add(i)
        cu = listing.getCodeUnitAt(addr)
        if cu:
            print(f"{addr}  {cu}")

print("\n완료!")
