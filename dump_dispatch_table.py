#!/usr/bin/env python3
"""
0x18c4 디스패치 테이블 덤프
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
    address_space = program.getAddressFactory().getDefaultAddressSpace()

    CODE_SEGMENT = 0x1000
    table_offset = 0x18c4
    table_addr = address_space.getAddress((CODE_SEGMENT << 4) + table_offset)

    print(f"\n=== 0x18c4 디스패치 테이블 ===\n")

    # 테이블 크기 추정: 11개 (FUNCTION_POINTERS.md 언급)
    for i in range(11):
        addr = table_addr.add(i * 2)  # 워드 단위 (2 bytes)

        # 포인터 읽기 (little endian)
        low = memory.getByte(addr) & 0xFF
        high = memory.getByte(addr.add(1)) & 0xFF
        ptr_offset = (high << 8) | low

        # 함수 주소 계산 (코드 세그먼트 내)
        func_addr = address_space.getAddress((CODE_SEGMENT << 4) + ptr_offset)
        func = flat_api.getFunctionAt(func_addr)

        if func:
            func_name = func.getName()
            size = func.getBody().getNumAddresses()
            print(f"  [{i:2d}] 0x{ptr_offset:04x} → {func_name} ({size} bytes)")
        else:
            print(f"  [{i:2d}] 0x{ptr_offset:04x} → 함수 없음")

print("\n완료!")
