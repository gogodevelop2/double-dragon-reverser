#!/usr/bin/env python3
"""
Ghidra에서 함수 포인터 테이블 데이터 읽기
0x18da (Mode 1) 및 0x18f0 (Mode 2)의 11개 워드 확인
"""

import pyghidra
import os

# 환경 변수 설정
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# Ghidra 설치 경로 확인
ghidra_install_dir = os.environ.get('GHIDRA_INSTALL_DIR', '/opt/homebrew/Cellar/ghidra/11.4.2/libexec')

# 프로젝트 경로
from pathlib import Path
project_path = Path("/Users/joejeon/Documents/develop/Double Dragon/ghidra-project").absolute()
project_name = "DoubleDragon"
binary_path = Path("/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/DDMAIN.EXE").absolute()

print("=" * 80)
print("함수 포인터 테이블 분석")
print("=" * 80)

# Ghidra 초기화
pyghidra.start(install_dir=ghidra_install_dir, verbose=False)

with pyghidra.open_program(binary_path, project_location=project_path, project_name=project_name, analyze=False) as flat_api:
    program = flat_api.getCurrentProgram()
    memory = program.getMemory()
    listing = program.getListing()
    address_factory = program.getAddressFactory()

    # 기본 주소 공간 가져오기
    address_space = address_factory.getDefaultAddressSpace()

    # 세그먼트 0x1988 기준
    segment = 0x1988

    print(f"\n세그먼트: 0x{segment:04x}")
    print("-" * 80)

    # Mode 1 테이블: 0x18da
    mode1_offset = 0x18da
    mode1_addr = address_space.getAddress((segment << 4) + mode1_offset)

    print(f"\n[Mode 1 함수 포인터 테이블]")
    print(f"주소: {segment:04x}:{mode1_offset:04x} (실제: 0x{(segment << 4) + mode1_offset:05x})")
    print("-" * 80)

    mode1_functions = []
    for i in range(11):
        addr = address_space.getAddress((segment << 4) + mode1_offset + (i * 2))
        try:
            # 2바이트 (워드) 읽기 - little endian
            low_byte = memory.getByte(addr) & 0xFF
            high_byte = memory.getByte(addr.add(1)) & 0xFF
            func_addr = (high_byte << 8) | low_byte

            mode1_functions.append(func_addr)

            # 해당 주소에 함수가 있는지 확인
            func_location = address_space.getAddress(func_addr)
            function = flat_api.getFunctionAt(func_location)

            if function:
                func_name = function.getName()
                func_size = function.getBody().getNumAddresses()
                print(f"  [{i:2d}] 0x{func_addr:04x} → {func_name} ({func_size} bytes)")
            else:
                # 함수가 없으면 데이터 확인
                data = listing.getDataAt(func_location)
                if data:
                    print(f"  [{i:2d}] 0x{func_addr:04x} → [DATA: {data.getDataType().getName()}]")
                else:
                    print(f"  [{i:2d}] 0x{func_addr:04x} → [UNKNOWN]")
        except Exception as e:
            print(f"  [{i:2d}] ERROR: {e}")

    # Mode 2 테이블: 0x18f0
    mode2_offset = 0x18f0
    mode2_addr = address_space.getAddress((segment << 4) + mode2_offset)

    print(f"\n[Mode 2 함수 포인터 테이블]")
    print(f"주소: {segment:04x}:{mode2_offset:04x} (실제: 0x{(segment << 4) + mode2_offset:05x})")
    print("-" * 80)

    mode2_functions = []
    for i in range(11):
        addr = address_space.getAddress((segment << 4) + mode2_offset + (i * 2))
        try:
            # 2바이트 (워드) 읽기 - little endian
            low_byte = memory.getByte(addr) & 0xFF
            high_byte = memory.getByte(addr.add(1)) & 0xFF
            func_addr = (high_byte << 8) | low_byte

            mode2_functions.append(func_addr)

            # 해당 주소에 함수가 있는지 확인
            func_location = address_space.getAddress(func_addr)
            function = flat_api.getFunctionAt(func_location)

            if function:
                func_name = function.getName()
                func_size = function.getBody().getNumAddresses()
                print(f"  [{i:2d}] 0x{func_addr:04x} → {func_name} ({func_size} bytes)")
            else:
                # 함수가 없으면 데이터 확인
                data = listing.getDataAt(func_location)
                if data:
                    print(f"  [{i:2d}] 0x{func_addr:04x} → [DATA: {data.getDataType().getName()}]")
                else:
                    print(f"  [{i:2d}] 0x{func_addr:04x} → [UNKNOWN]")
        except Exception as e:
            print(f"  [{i:2d}] ERROR: {e}")

    # 비교 분석
    print(f"\n[Mode 1 vs Mode 2 비교]")
    print("-" * 80)
    print(f"{'인덱스':<8} {'테이블 오프셋':<15} {'Mode 1':<20} {'Mode 2':<20} {'차이'}")
    print("-" * 80)

    table_offsets = [
        "0x18c4 (0)", "0x18c6 (1)", "0x18c8 (2)", "0x18ca (3)",
        "0x18cc (4)", "0x18ce (5)", "0x18d0 (6)", "0x18d2 (7)",
        "0x18d4 (8)", "0x18d6 (9)", "0x18d8 (10)"
    ]

    for i in range(11):
        mode1_addr = mode1_functions[i]
        mode2_addr = mode2_functions[i]
        same = "같음" if mode1_addr == mode2_addr else "다름 ⭐"
        print(f"{i:<8} {table_offsets[i]:<15} 0x{mode1_addr:04x} {'':<15} 0x{mode2_addr:04x} {'':<15} {same}")

    # 디스패처 매핑
    print(f"\n[디스패처 함수 매핑]")
    print("-" * 80)

    dispatchers = [
        ("FUN_1000_499b", 0, "0x18c4"),
        ("FUN_1000_48e0", 1, "0x18c6"),
        ("FUN_1000_81c2", 2, "0x18c8"),
        ("FUN_1000_822a", 3, "0x18ca"),
        ("FUN_1000_8277", 4, "0x18cc"),
        ("FUN_1000_82f4", 5, "0x18ce"),
        ("FUN_1000_8135", 6, "0x18d0"),
        ("FUN_1000_810b", 7, "0x18d2"),
        ("FUN_1000_5860", 8, "0x18d4"),
        ("FUN_1000_590a", 9, "0x18d6"),
        ("FUN_1000_599d", 10, "0x18d8"),
    ]

    for disp_name, idx, table_addr in dispatchers:
        mode1_target = mode1_functions[idx]
        mode2_target = mode2_functions[idx]

        # 함수 정보 가져오기
        func_loc = address_space.getAddress(mode1_target)
        func = flat_api.getFunctionAt(func_loc)
        func_name = func.getName() if func else "UNKNOWN"

        print(f"{disp_name:<20} calls {table_addr} → Mode1: {func_name}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
