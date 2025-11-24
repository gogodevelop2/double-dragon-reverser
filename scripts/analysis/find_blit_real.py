#!/usr/bin/env python3
"""
실제 Blit 함수 찾기

전략:
1. 비디오 메모리 세그먼트 참조하는 함수 검색 (0xA000, 0xB800)
2. FUN_1000_3e6d, FUN_1000_3f71에서 호출하는 다른 함수들
3. 반복 쓰기 패턴이 있는 함수
"""

import os
from pathlib import Path

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
    listing = program.getListing()
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    func_manager = program.getFunctionManager()

    CODE_SEGMENT = 0x1000

    # 1. FUN_1000_3e6d가 호출하는 함수들
    print("\n=== 1. FUN_1000_3e6d가 호출하는 함수들 ===")
    addr_3e6d = address_space.getAddress((CODE_SEGMENT << 4) + 0x3e6d)
    func_3e6d = flat_api.getFunctionAt(addr_3e6d)

    if func_3e6d:
        called_funcs = set()
        for called in func_3e6d.getCalledFunctions(None):
            called_funcs.add(called)
            print(f"  {called.getName()} @ {called.getEntryPoint()}")

    # 2. FUN_1000_3f71이 호출하는 함수들
    print("\n=== 2. FUN_1000_3f71이 호출하는 함수들 ===")
    addr_3f71 = address_space.getAddress((CODE_SEGMENT << 4) + 0x3f71)
    func_3f71 = flat_api.getFunctionAt(addr_3f71)

    if func_3f71:
        for called in func_3f71.getCalledFunctions(None):
            print(f"  {called.getName()} @ {called.getEntryPoint()}")

    # 3. 비디오 메모리 세그먼트 참조 검색
    print("\n=== 3. 비디오 메모리 세그먼트 참조 (0xA000, 0xB800) ===")

    video_segments = [0xA000, 0xB800, 0xB000]  # EGA, CGA Text, Mono

    for func in func_manager.getFunctions(True):
        func_body = func.getBody()
        code_units = listing.getCodeUnits(func_body, True)

        for cu in code_units:
            instr_str = str(cu)

            # MOV ES, segment 또는 ES: 접두사 찾기
            if 'ES' in instr_str or 'es' in instr_str:
                for seg in video_segments:
                    if f'{seg:x}' in instr_str.lower() or f'0x{seg:x}' in instr_str.lower():
                        print(f"  {func.getName()} @ {func.getEntryPoint()}: {instr_str.strip()}")
                        break

    # 4. 특정 패턴: REP STOSB/STOSW/MOVSB/MOVSW (블록 복사)
    print("\n=== 4. 블록 복사 명령 사용하는 함수 ===")

    for func in func_manager.getFunctions(True):
        func_body = func.getBody()
        code_units = listing.getCodeUnits(func_body, True)

        has_rep = False
        for cu in code_units:
            instr_str = str(cu).upper()
            if 'REP' in instr_str or 'STOSB' in instr_str or 'STOSW' in instr_str or 'MOVSB' in instr_str or 'MOVSW' in instr_str:
                if not has_rep:
                    print(f"  {func.getName()} @ {func.getEntryPoint()}")
                    has_rep = True

    # 5. FUN_1000_0786 확인 (CGA 평면 변환 - 이것도 Blit와 관련?)
    print("\n=== 5. FUN_1000_0786 (CGA 평면 변환) ===")
    addr_0786 = address_space.getAddress((CODE_SEGMENT << 4) + 0x0786)
    func_0786 = flat_api.getFunctionAt(addr_0786)

    if func_0786:
        print(f"  크기: {func_0786.getBody().getNumAddresses()} bytes")
        print(f"  호출하는 함수:")
        for called in func_0786.getCalledFunctions(None):
            print(f"    {called.getName()} @ {called.getEntryPoint()}")

        print(f"  이 함수를 호출하는 곳:")
        refs = flat_api.getReferencesTo(addr_0786)
        for ref in refs:
            from_addr = ref.getFromAddress()
            containing = flat_api.getFunctionContaining(from_addr)
            if containing:
                print(f"    {containing.getName()} @ {from_addr}")

print("\n완료!")
