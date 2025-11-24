#!/usr/bin/env python3
"""
디스패치 테이블 엔트리들을 직접 디스어셈블
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

    print(f"\n=== 0x16ef 테이블 엔트리 디스어셈블 ===\n")

    # 처음 5개만 확인
    for i in range(5):
        addr = table_addr.add(i * 2)

        # 포인터 읽기
        low = memory.getByte(addr) & 0xFF
        high = memory.getByte(addr.add(1)) & 0xFF
        ptr_offset = (high << 8) | low

        # 코드 주소
        code_addr = address_space.getAddress((CODE_SEGMENT << 4) + ptr_offset)

        print(f"[타입 {i}] 0x{ptr_offset:04x}")
        print(f"  주소: {code_addr}")

        # 10 명령어 디스어셈블
        try:
            current_addr = code_addr
            for j in range(10):
                cu = listing.getCodeUnitAt(current_addr)
                if cu and str(cu).strip() and not str(cu).startswith('??'):
                    print(f"    {current_addr}  {cu}")
                    # 다음 명령어로
                    current_addr = current_addr.add(cu.getLength())
                else:
                    # 디스어셈블 안 된 부분 - 바이트만 표시
                    byte_val = memory.getByte(current_addr) & 0xFF
                    print(f"    {current_addr}  ?? {byte_val:02x}h")
                    current_addr = current_addr.add(1)
        except:
            pass

        print()

print("완료!")
