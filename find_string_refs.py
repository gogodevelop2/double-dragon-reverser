#!/usr/bin/env python3
"""
문자열 참조 찾기 - pyghidra 사용
"""

import os
from pathlib import Path
import pyghidra

# 환경 변수 설정
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# 경로 설정
PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

def main():
    """문자열 참조 찾기"""

    print("=" * 70)
    print("문자열 참조 검색")
    print("=" * 70)

    # pyghidra로 프로젝트 열기
    with pyghidra.open_program(str(BINARY_PATH), project_location=PROJECT_PATH, project_name=PROJECT_NAME) as flat_api:
        program = flat_api.getCurrentProgram()
        listing = program.getListing()
        memory = program.getMemory()
        ref_mgr = program.getReferenceManager()

        print(f"\n프로그램: {program.getName()}")
        print(f"이미지 베이스: {program.getImageBase()}")

        # 찾을 문자열들
        search_strings = [
            b"LINDA.EG1",
            b"ABOBO.EG1",
            b"PLAYER1.EG1"
        ]

        from ghidra.util.task import ConsoleTaskMonitor

        for search_bytes in search_strings:
            search_str = search_bytes.decode('ascii')
            print(f"\n{'='*70}")
            print(f"검색: {search_str}")
            print(f"{'='*70}")

            # 메모리에서 바이트 찾기
            found_addr = memory.findBytes(
                program.getMinAddress(),
                search_bytes,
                None,
                True,
                ConsoleTaskMonitor()
            )

            if found_addr is None:
                print(f"  문자열을 찾을 수 없음")
                continue

            print(f"\n문자열 위치: {found_addr}")

            # 이 주소를 참조하는 모든 코드 찾기
            refs = ref_mgr.getReferencesTo(found_addr)
            ref_list = list(refs)
            print(f"참조 개수: {len(ref_list)}")

            for idx, ref in enumerate(ref_list, 1):
                from_addr = ref.getFromAddress()

                print(f"\n참조 #{idx}:")
                print(f"  From: {from_addr}")
                print(f"  Type: {ref.getReferenceType()}")

                # 함수 찾기
                func = flat_api.getFunctionContaining(from_addr)
                if func:
                    print(f"  함수: {func.getName()}")
                    print(f"  함수 주소: {func.getEntryPoint()}")
                    print(f"  함수 크기: {func.getBody().getNumAddresses()} bytes")

                    # 주변 어셈블리 보기
                    print(f"\n  주변 어셈블리:")
                    instr = listing.getInstructionAt(from_addr)
                    if instr:
                        # 이전 3개
                        prev_addr = from_addr
                        for i in range(3):
                            prev_instr = listing.getInstructionBefore(prev_addr)
                            if prev_instr:
                                print(f"    {prev_instr.getAddress()}: {prev_instr}")
                                prev_addr = prev_instr.getAddress()

                        # 현재 (참조하는 instruction)
                        print(f" >> {instr.getAddress()}: {instr}")

                        # 이후 5개
                        next_addr = from_addr
                        for i in range(5):
                            next_instr = listing.getInstructionAfter(next_addr)
                            if next_instr:
                                print(f"    {next_instr.getAddress()}: {next_instr}")
                                next_addr = next_instr.getAddress()

                    # 디컴파일
                    print(f"\n  디컴파일:")
                    from ghidra.app.decompiler import DecompInterface

                    decompiler = DecompInterface()
                    decompiler.openProgram(program)

                    result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())
                    if result.decompileCompleted():
                        decompiled = result.getDecompiledFunction()
                        c_code = decompiled.getC()

                        lines = c_code.split('\n')
                        for i, line in enumerate(lines[:60]):  # 처음 60줄
                            print(f"    {line}")

                    decompiler.dispose()

                else:
                    print(f"  (데이터 영역)")

if __name__ == "__main__":
    main()
