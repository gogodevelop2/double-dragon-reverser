#!/usr/bin/env python3
"""
FUN_1000_12c0 (Blit 함수) 찾기

목적: 1000:12c0 주소에 함수가 있는지 확인하고, 있다면 디컴파일
"""

import os
from pathlib import Path

# ⭐ 1. 환경 변수 설정 (가장 먼저!)
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# ⭐ 2. pyghidra import
import pyghidra

# ⭐ 3. 프로젝트 경로 설정
PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

# ⭐ 4. Ghidra 시작
print("Ghidra 초기화 중...")
pyghidra.start(verbose=False)

# ⭐ 5. 프로젝트 열기
with pyghidra.open_program(
    BINARY_PATH,
    project_location=PROJECT_PATH,
    project_name=PROJECT_NAME,
    analyze=False
) as flat_api:

    program = flat_api.getCurrentProgram()
    memory = program.getMemory()
    listing = program.getListing()
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    func_manager = program.getFunctionManager()

    # ⭐ 6. 세그먼트 정의
    CODE_SEGMENT = 0x1000

    # ⭐ 7. 1000:12c0 주소 계산
    offset = 0x12c0
    physical_addr = (CODE_SEGMENT << 4) + offset  # 0x112c0
    target_addr = address_space.getAddress(physical_addr)

    print(f"\n=== 1000:12c0 검색 ===")
    print(f"물리 주소: 0x{physical_addr:x}")
    print(f"Target: {target_addr}")

    # 정확히 해당 주소에 함수가 있는지 확인
    func = flat_api.getFunctionAt(target_addr)

    if func:
        print(f"\n✅ 함수 발견!")
        print(f"  이름: {func.getName()}")
        print(f"  진입점: {func.getEntryPoint()}")
        print(f"  크기: {func.getBody().getNumAddresses()} bytes")

        # 디컴파일
        from ghidra.app.decompiler import DecompInterface
        decompiler = DecompInterface()
        decompiler.openProgram(program)

        print(f"\n디컴파일 중...")
        result = decompiler.decompileFunction(func, 30, None)

        if result.decompileCompleted():
            code = result.getDecompiledFunction().getC()

            # 파일로 저장
            output_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
            output_file.write_text(code)
            print(f"✅ 저장: {output_file}")

            # 코드 미리보기 (첫 20줄)
            lines = code.split('\n')[:20]
            print("\n--- 코드 미리보기 ---")
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}→{line}")
        else:
            print(f"❌ 디컴파일 실패: {result.getErrorMessage()}")
    else:
        print(f"\n❌ 1000:12c0에 함수 없음")

        # 혹시 중간 주소인지 확인
        containing_func = flat_api.getFunctionContaining(target_addr)
        if containing_func:
            print(f"  → 이 주소는 {containing_func.getName()} 내부에 포함됨")
            print(f"  → 진입점: {containing_func.getEntryPoint()}")
        else:
            print(f"  → 함수로 인식되지 않은 코드")

            # 메모리 덤프 (첫 32바이트)
            print(f"\n  메모리 내용:")
            for i in range(0, 32, 16):
                line_addr = target_addr.add(i)
                print(f"  {line_addr}: ", end="")
                for j in range(16):
                    byte = memory.getByte(line_addr.add(j)) & 0xFF
                    print(f"{byte:02x} ", end="")
                print()

    # 추가: 1000:12c0 근처 함수들 검색 (±100 bytes)
    print(f"\n=== 1000:12c0 근처 함수들 ===")
    nearby_funcs = []

    for offset_delta in range(-100, 100):
        check_addr = target_addr.add(offset_delta)
        nearby_func = flat_api.getFunctionAt(check_addr)
        if nearby_func and nearby_func not in nearby_funcs:
            nearby_funcs.append(nearby_func)
            distance = offset_delta
            print(f"  {nearby_func.getName()}: {nearby_func.getEntryPoint()} (거리: {distance:+4d} bytes)")

print("\n완료!")
