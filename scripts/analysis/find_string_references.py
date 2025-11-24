#!/usr/bin/env python3
"""
Ghidra를 사용하여 특정 문자열의 참조를 찾는 스크립트
"""

import jpype
import jpype.imports
from pathlib import Path

# Ghidra 경로
GHIDRA_INSTALL_DIR = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
PROJECT_PATH = str(Path.home() / ".ghidra" / ".ghidra_11.4.2_PUBLIC" / "projects" / "DoubleDragon")
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = "reference/dos-original/DDMAIN.EXE"

def find_string_refs():
    """문자열 참조 찾기"""
    import ghidra
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    from ghidra.program.model.data import StringDataInstance

    # 현재 프로그램 가져오기
    from ghidra.program.flatapi import FlatProgramAPI

    # pyghidra로 프로젝트 열기
    import pyghidra

    with pyghidra.open_program(BINARY_PATH, project_location=PROJECT_PATH, project_name=PROJECT_NAME) as flat_api:
        program = flat_api.getCurrentProgram()
        listing = program.getListing()
        memory = program.getMemory()

        print(f"프로그램: {program.getName()}")
        print(f"이미지 베이스: {program.getImageBase()}")
        print()

        # 찾을 문자열들
        search_strings = [
            "LINDA.EG1",
            "ABOBO.EG1",
            "PLAYER1.EG1",
            "WEAPONS.EG1"
        ]

        for search_str in search_strings:
            print(f"\n{'='*70}")
            print(f"검색 문자열: {search_str}")
            print(f"{'='*70}")

            # 메모리에서 문자열 찾기
            found_addr = memory.findBytes(
                program.getMinAddress(),
                search_str.encode('ascii'),
                None,  # mask
                True,  # forward search
                ConsoleTaskMonitor()
            )

            if found_addr is None:
                print(f"  문자열을 찾을 수 없음")
                continue

            print(f"  문자열 주소: {found_addr}")

            # 이 주소를 참조하는 모든 위치 찾기
            refs = program.getReferenceManager().getReferencesTo(found_addr)

            ref_count = 0
            for ref in refs:
                from_addr = ref.getFromAddress()
                ref_count += 1

                print(f"\n  참조 #{ref_count}:")
                print(f"    From: {from_addr}")
                print(f"    Type: {ref.getReferenceType()}")

                # 이 참조가 속한 함수 찾기
                func = flat_api.getFunctionContaining(from_addr)
                if func:
                    print(f"    함수: {func.getName()} @ {func.getEntryPoint()}")
                    print(f"    크기: {func.getBody().getNumAddresses()} bytes")

                    # 함수 주변 코드 보기
                    print(f"\n    주변 어셈블리:")
                    # from_addr 전후 5개 instruction
                    instr = listing.getInstructionAt(from_addr)
                    if instr:
                        # 이전 5개
                        prev_addr = from_addr
                        prev_instrs = []
                        for i in range(5):
                            prev_instr = listing.getInstructionBefore(prev_addr)
                            if prev_instr:
                                prev_instrs.insert(0, prev_instr)
                                prev_addr = prev_instr.getAddress()

                        for pi in prev_instrs:
                            print(f"      {pi.getAddress()}: {pi}")

                        # 현재
                        print(f"   >> {instr.getAddress()}: {instr} <<")

                        # 이후 5개
                        next_addr = from_addr
                        for i in range(5):
                            next_instr = listing.getInstructionAfter(next_addr)
                            if next_instr:
                                print(f"      {next_instr.getAddress()}: {next_instr}")
                                next_addr = next_instr.getAddress()
                else:
                    print(f"    함수를 찾을 수 없음 (데이터 영역?)")

            if ref_count == 0:
                print(f"  참조를 찾을 수 없음")

if __name__ == "__main__":
    find_string_refs()
