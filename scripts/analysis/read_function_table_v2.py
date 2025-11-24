#!/usr/bin/env python3
"""
Ghidra에서 함수 포인터 테이블 데이터 읽기 (v2)
0x18da (Mode 1) 및 0x18f0 (Mode 2)의 11개 워드 확인
세그먼트:오프셋 형식으로 함수 찾기
"""

import pyghidra
import os
from pathlib import Path

# 환경 변수 설정
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# Ghidra 설치 경로 확인
ghidra_install_dir = os.environ.get('GHIDRA_INSTALL_DIR', '/opt/homebrew/Cellar/ghidra/11.4.2/libexec')

# 프로젝트 경로
project_path = Path("/Users/joejeon/Documents/develop/Double Dragon/ghidra-project").absolute()
project_name = "DoubleDragon"
binary_path = Path("/Users/joejeon/Documents/develop/Double Dragon/reference/dos-original/DDMAIN.EXE").absolute()

print("=" * 80)
print("함수 포인터 테이블 분석 v2")
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

    # 데이터 세그먼트 0x1988
    data_segment = 0x1988
    # 코드 세그먼트 0x1000
    code_segment = 0x1000

    print(f"\n데이터 세그먼트: 0x{data_segment:04x}")
    print(f"코드 세그먼트: 0x{code_segment:04x}")
    print("-" * 80)

    # Mode 1 테이블: 0x18da
    mode1_offset = 0x18da
    mode1_addr = address_space.getAddress((data_segment << 4) + mode1_offset)

    print(f"\n[Mode 1 함수 포인터 테이블]")
    print(f"주소: {data_segment:04x}:{mode1_offset:04x}")
    print("-" * 80)

    mode1_functions = []
    for i in range(11):
        addr = address_space.getAddress((data_segment << 4) + mode1_offset + (i * 2))
        try:
            # 2바이트 (워드) 읽기 - little endian
            low_byte = memory.getByte(addr) & 0xFF
            high_byte = memory.getByte(addr.add(1)) & 0xFF
            offset = (high_byte << 8) | low_byte

            mode1_functions.append(offset)

            # 코드 세그먼트 기준으로 함수 주소 계산
            # 1000:offset 형식
            func_addr = address_space.getAddress((code_segment << 4) + offset)
            function = flat_api.getFunctionAt(func_addr)

            if function:
                func_name = function.getName()
                func_size = function.getBody().getNumAddresses()
                print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → {func_name:<20} ({func_size} bytes)")
            else:
                # 함수가 없으면 근처 함수 찾기
                func_containing = flat_api.getFunctionContaining(func_addr)
                if func_containing:
                    print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → [내부: {func_containing.getName()}]")
                else:
                    print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → [UNKNOWN]")
        except Exception as e:
            print(f"  [{i:2d}] ERROR: {e}")

    # Mode 2 테이블: 0x18f0
    mode2_offset = 0x18f0
    mode2_addr = address_space.getAddress((data_segment << 4) + mode2_offset)

    print(f"\n[Mode 2 함수 포인터 테이블]")
    print(f"주소: {data_segment:04x}:{mode2_offset:04x}")
    print("-" * 80)

    mode2_functions = []
    for i in range(11):
        addr = address_space.getAddress((data_segment << 4) + mode2_offset + (i * 2))
        try:
            # 2바이트 (워드) 읽기 - little endian
            low_byte = memory.getByte(addr) & 0xFF
            high_byte = memory.getByte(addr.add(1)) & 0xFF
            offset = (high_byte << 8) | low_byte

            mode2_functions.append(offset)

            # 코드 세그먼트 기준으로 함수 주소 계산
            func_addr = address_space.getAddress((code_segment << 4) + offset)
            function = flat_api.getFunctionAt(func_addr)

            if function:
                func_name = function.getName()
                func_size = function.getBody().getNumAddresses()
                print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → {func_name:<20} ({func_size} bytes)")
            else:
                # 함수가 없으면 근처 함수 찾기
                func_containing = flat_api.getFunctionContaining(func_addr)
                if func_containing:
                    print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → [내부: {func_containing.getName()}]")
                else:
                    print(f"  [{i:2d}] {code_segment:04x}:{offset:04x} → [UNKNOWN]")
        except Exception as e:
            print(f"  [{i:2d}] ERROR: {e}")

    # 비교 분석
    print(f"\n[Mode 1 vs Mode 2 비교]")
    print("-" * 80)
    print(f"{'Idx':<5} {'테이블':<12} {'Mode 1 함수':<25} {'Mode 2 함수':<25} {'차이'}")
    print("-" * 80)

    table_offsets = [
        "0x18c4", "0x18c6", "0x18c8", "0x18ca", "0x18cc", "0x18ce",
        "0x18d0", "0x18d2", "0x18d4", "0x18d6", "0x18d8"
    ]

    for i in range(11):
        offset1 = mode1_functions[i]
        offset2 = mode2_functions[i]

        # 함수 이름 가져오기
        func_addr1 = address_space.getAddress((code_segment << 4) + offset1)
        func1 = flat_api.getFunctionAt(func_addr1)
        name1 = func1.getName() if func1 else f"0x{offset1:04x}"

        func_addr2 = address_space.getAddress((code_segment << 4) + offset2)
        func2 = flat_api.getFunctionAt(func_addr2)
        name2 = func2.getName() if func2 else f"0x{offset2:04x}"

        same = "  =" if offset1 == offset2 else "  ≠"
        print(f"[{i:2d}]  {table_offsets[i]:<12} {name1:<25} {name2:<25} {same}")

    # 디스패처 매핑
    print(f"\n[디스패처 함수 → 실제 타겟]")
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
        offset = mode1_functions[idx]
        func_addr = address_space.getAddress((code_segment << 4) + offset)
        func = flat_api.getFunctionAt(func_addr)
        func_name = func.getName() if func else "UNKNOWN"

        print(f"{disp_name:<20} → {table_addr} → {code_segment:04x}:{offset:04x} = {func_name}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)
