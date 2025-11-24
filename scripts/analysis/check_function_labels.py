#!/usr/bin/env python3
"""
함수 포인터 테이블의 주소가 어느 함수 안에 있는지 확인
"""

import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

import pyghidra

PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

print("=" * 80)
print("함수 포인터 테이블 주소 분석")
print("=" * 80)

pyghidra.start(verbose=False)

# Mode 1 및 Mode 2 주소들
mode1_offsets = [0x5f07, 0x5e55, 0x8492, 0x84ee, 0x8583, 0x853d, 0x8622, 0x7eb0, 0x5aaa, 0x5b5f, 0x5c0a]
mode2_offsets = [0x6b19, 0x60d0, 0x2e86, 0x2ee2, 0x2f75, 0x2f31, 0x2fbf, 0x2c2f, 0x29af, 0x2ba1, 0x2b2e]

dispatcher_names = [
    "FUN_1000_499b", "FUN_1000_48e0", "FUN_1000_81c2", "FUN_1000_822a",
    "FUN_1000_8277", "FUN_1000_82f4", "FUN_1000_8135", "FUN_1000_810b",
    "FUN_1000_5860", "FUN_1000_590a", "FUN_1000_599d"
]

with pyghidra.open_program(BINARY_PATH, project_location=PROJECT_PATH, project_name=PROJECT_NAME, analyze=False) as flat_api:
    program = flat_api.getCurrentProgram()
    listing = program.getListing()
    func_manager = program.getFunctionManager()
    addr_factory = program.getAddressFactory()
    addr_space = addr_factory.getDefaultAddressSpace()

    CODE_SEG = 0x1000

    print("\n[Mode 1 함수 포인터 테이블 주소 분석]")
    print("-" * 80)

    for i, offset in enumerate(mode1_offsets):
        addr = addr_space.getAddress((CODE_SEG << 4) + offset)

        # 정확히 그 주소에서 시작하는 함수
        func_at = func_manager.getFunctionAt(addr)

        # 그 주소를 포함하는 함수
        func_containing = func_manager.getFunctionContaining(addr)

        # 그 주소의 instruction 또는 data
        instruction = listing.getInstructionAt(addr)
        data = listing.getDataAt(addr)

        print(f"\n[{i:2d}] {dispatcher_names[i]:<20} → 1000:{offset:04x}")

        if func_at:
            print(f"     ✅ 함수 진입점: {func_at.getName()}")
        elif func_containing:
            entry = func_containing.getEntryPoint()
            entry_offset = entry.getOffset() - (CODE_SEG << 4)
            print(f"     📍 포함 함수: {func_containing.getName()} (entry: 1000:{entry_offset:04x})")
            print(f"        오프셋: +{offset - entry_offset} bytes from entry")
        else:
            print(f"     ❌ 함수 없음")

        if instruction:
            print(f"     🔹 Instruction: {instruction}")
        elif data:
            print(f"     🔸 Data: {data.getDataType().getName()}")

    print("\n\n[Mode 2 함수 포인터 테이블 주소 분석]")
    print("-" * 80)

    for i, offset in enumerate(mode2_offsets):
        addr = addr_space.getAddress((CODE_SEG << 4) + offset)

        func_at = func_manager.getFunctionAt(addr)
        func_containing = func_manager.getFunctionContaining(addr)
        instruction = listing.getInstructionAt(addr)
        data = listing.getDataAt(addr)

        print(f"\n[{i:2d}] {dispatcher_names[i]:<20} → 1000:{offset:04x}")

        if func_at:
            print(f"     ✅ 함수 진입점: {func_at.getName()}")
        elif func_containing:
            entry = func_containing.getEntryPoint()
            entry_offset = entry.getOffset() - (CODE_SEG << 4)
            print(f"     📍 포함 함수: {func_containing.getName()} (entry: 1000:{entry_offset:04x})")
            print(f"        오프셋: +{offset - entry_offset} bytes from entry")
        else:
            print(f"     ❌ 함수 없음")

        if instruction:
            print(f"     🔹 Instruction: {instruction}")
        elif data:
            print(f"     🔸 Data: {data.getDataType().getName()}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
