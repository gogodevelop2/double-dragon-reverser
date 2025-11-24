#!/usr/bin/env python3
"""
함수 포인터가 far pointer (4 bytes: segment:offset)인지 확인
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
print("FAR POINTER 분석 (segment:offset 4바이트)")
print("=" * 80)

pyghidra.start(verbose=False)

with pyghidra.open_program(BINARY_PATH, project_location=PROJECT_PATH, project_name=PROJECT_NAME, analyze=False) as flat_api:
    program = flat_api.getCurrentProgram()
    memory = program.getMemory()
    func_manager = program.getFunctionManager()
    addr_factory = program.getAddressFactory()
    addr_space = addr_factory.getDefaultAddressSpace()

    DATA_SEG = 0x1988

    # Mode 1 테이블: 1988:18da
    mode1_offset = 0x18da
    mode1_addr = addr_space.getAddress((DATA_SEG << 4) + mode1_offset)

    print("\n[Mode 1 테이블 @ 1988:18da]")
    print("-" * 80)
    print("2바이트 (near pointer) vs 4바이트 (far pointer) 비교\n")

    for i in range(11):
        addr = addr_space.getAddress((DATA_SEG << 4) + mode1_offset + (i * 4))  # 4바이트씩

        # 4바이트 읽기 (far pointer: offset:segment in little endian)
        byte0 = memory.getByte(addr) & 0xFF
        byte1 = memory.getByte(addr.add(1)) & 0xFF
        byte2 = memory.getByte(addr.add(2)) & 0xFF
        byte3 = memory.getByte(addr.add(3)) & 0xFF

        # Little endian: [offset_low, offset_high, segment_low, segment_high]
        offset = (byte1 << 8) | byte0
        segment = (byte3 << 8) | byte2

        print(f"[{i:2d}] @ {DATA_SEG:04x}:{mode1_offset + i*4:04x}")
        print(f"     Raw bytes: {byte0:02x} {byte1:02x} {byte2:02x} {byte3:02x}")
        print(f"     As FAR:    {segment:04x}:{offset:04x}")
        print(f"     Physical:  0x{(segment << 4) + offset:05x}")

        # 해당 주소에 함수가 있는지 확인
        physical_addr = addr_space.getAddress((segment << 4) + offset)
        func = func_manager.getFunctionAt(physical_addr)
        func_containing = func_manager.getFunctionContaining(physical_addr)

        if func:
            print(f"     ✅ 함수: {func.getName()}")
        elif func_containing:
            print(f"     📍 포함: {func_containing.getName()}")
        else:
            print(f"     ❌ 함수 없음")
        print()

    # 2바이트 (near pointer) 다시 확인
    print("\n[2바이트 (near pointer) 재확인]")
    print("-" * 80)

    mode1_addr = addr_space.getAddress((DATA_SEG << 4) + mode1_offset)

    for i in range(5):  # 처음 5개만
        addr = addr_space.getAddress((DATA_SEG << 4) + mode1_offset + (i * 2))

        byte0 = memory.getByte(addr) & 0xFF
        byte1 = memory.getByte(addr.add(1)) & 0xFF
        offset = (byte1 << 8) | byte0

        print(f"[{i:2d}] @ {DATA_SEG:04x}:{mode1_offset + i*2:04x}")
        print(f"     Raw: {byte0:02x} {byte1:02x}")
        print(f"     Offset: {offset:04x}")
        print()

print("=" * 80)
print("분석 완료!")
print("=" * 80)
