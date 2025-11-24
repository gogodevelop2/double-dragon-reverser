#!/usr/bin/env python3
"""
0x16ef 디스패치 테이블 탐색
FUN_1000_16e0에서 사용: (*(byte *)0x168f + 0x16ef)
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

    # 0x16ef 테이블 위치
    table_offset = 0x16ef
    table_addr = address_space.getAddress((CODE_SEGMENT << 4) + table_offset)

    print(f"\n=== 0x16ef 디스패치 테이블 (객체 타입별 업데이트) ===")
    print(f"위치: 1000:16ef\n")

    # 테이블 크기를 알 수 없으므로 처음 20개만 시도
    for i in range(20):
        addr = table_addr.add(i * 2)  # 워드 단위

        # 포인터 읽기
        low = memory.getByte(addr) & 0xFF
        high = memory.getByte(addr.add(1)) & 0xFF
        ptr_offset = (high << 8) | low

        # 코드 세그먼트 내 주소로 가정
        func_addr = address_space.getAddress((CODE_SEGMENT << 4) + ptr_offset)

        # 함수 확인
        func = flat_api.getFunctionAt(func_addr)

        if func:
            size = func.getBody().getNumAddresses()
            print(f"[타입 {i:2d}] 0x{ptr_offset:04x} → {func.getName()} ({size} bytes)")
        else:
            # 함수가 아니면 해당 주소 디스어셈블해보기
            cu = listing.getCodeUnitAt(func_addr)
            if cu:
                print(f"[타입 {i:2d}] 0x{ptr_offset:04x} → {cu} (함수 아님)")
            else:
                # 데이터일 수도
                data = listing.getDataAt(func_addr)
                if data:
                    print(f"[타입 {i:2d}] 0x{ptr_offset:04x} → 데이터: {data}")
                else:
                    # 메모리 내용 확인
                    byte1 = memory.getByte(func_addr) & 0xFF
                    byte2 = memory.getByte(func_addr.add(1)) & 0xFF
                    print(f"[타입 {i:2d}] 0x{ptr_offset:04x} → 메모리: {byte1:02x} {byte2:02x} (미정의)")

                    # 0x0000이면 테이블 끝일 가능성
                    if ptr_offset == 0:
                        print("\n→ 0x0000 발견, 테이블 끝으로 추정")
                        break

print("\n완료!")
