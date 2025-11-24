#!/usr/bin/env python3
"""
FUN_1000_12c0 디스어셈블리 가져오기
"""

import os
from pathlib import Path

# 환경 변수 설정
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

import pyghidra

PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

print("Ghidra 초기화 중...")
pyghidra.start(verbose=False)

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

    # 1000:12c0 주소
    CODE_SEGMENT = 0x1000
    offset = 0x12c0
    physical_addr = (CODE_SEGMENT << 4) + offset
    target_addr = address_space.getAddress(physical_addr)

    func = flat_api.getFunctionAt(target_addr)

    if func:
        print(f"\n✅ FUN_1000_12c0 (89 bytes)")
        print(f"진입점: {func.getEntryPoint()}")
        print(f"\n=== 디스어셈블리 ===\n")

        # 함수의 모든 명령어 출력
        instructions = []
        code_units = listing.getCodeUnits(func.getBody(), True)

        for cu in code_units:
            if cu.toString().strip():  # 빈 줄 제외
                addr_str = str(cu.getAddress())
                instr_str = str(cu)
                instructions.append(f"{addr_str}  {instr_str}")
                print(f"{addr_str}  {instr_str}")

        # 파일로 저장
        output_file = Path("output/decompiled/FUN_1000_12c0.asm")
        output_file.write_text('\n'.join(instructions))
        print(f"\n✅ 저장: {output_file}")

        # 호출하는 함수 찾기
        print(f"\n=== 이 함수를 호출하는 곳 ===")
        references = flat_api.getReferencesTo(target_addr)
        callers = []
        for ref in references:
            from_addr = ref.getFromAddress()
            containing_func = flat_api.getFunctionContaining(from_addr)
            if containing_func and containing_func.getName() != func.getName():
                caller_info = f"{containing_func.getName()} @ {from_addr}"
                if caller_info not in callers:
                    callers.append(caller_info)
                    print(f"  {caller_info}")

        if not callers:
            print("  (호출자 없음 - 직접 호출되지 않는 함수)")

    else:
        print("❌ 함수를 찾을 수 없습니다")

print("\n완료!")
