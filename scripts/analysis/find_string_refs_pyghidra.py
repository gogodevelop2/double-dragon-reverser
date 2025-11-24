#!/usr/bin/env python3
"""
pyghidra를 사용하여 문자열 참조 찾기
"""

import pyghidra
from pathlib import Path

# 경로 설정
BINARY_PATH = "reference/dos-original/DDMAIN.EXE"

def main():
    """문자열 참조 찾기"""

    # pyghidra 실행
    with pyghidra.open_program(BINARY_PATH) as flat_api:
        program = flat_api.getCurrentProgram()
        listing = program.getListing()
        memory = program.getMemory()
        ref_mgr = program.getReferenceManager()

        print(f"프로그램: {program.getName()}")
        print(f"이미지 베이스: {program.getImageBase()}")
        print()

        # 찾을 문자열들
        search_strings = [
            b"LINDA.EG1",
            b"ABOBO.EG1",
            b"PLAYER1.EG1"
        ]

        from ghidra.program.model.address import AddressSet
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

                    # 디컴파일
                    from ghidra.app.decompiler import DecompInterface
                    from ghidra.util.task import ConsoleTaskMonitor

                    decompiler = DecompInterface()
                    decompiler.openProgram(program)

                    result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())
                    if result.decompileCompleted():
                        decompiled = result.getDecompiledFunction()
                        c_code = decompiled.getC()

                        print(f"\n  디컴파일된 C 코드:")
                        print("  " + "-"*66)
                        for line in c_code.split('\n')[:50]:  # 처음 50줄만
                            print(f"  {line}")
                        print("  " + "-"*66)

                    decompiler.dispose()

                else:
                    print(f"  (데이터 영역)")

if __name__ == "__main__":
    main()
