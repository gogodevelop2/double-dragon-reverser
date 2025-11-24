#!/usr/bin/env python3
"""
미분석 함수 일괄 디컴파일 스크립트

Spice86에서 발견한 중요 함수들을 pyghidra로 자동 디컴파일
"""

import os
import json
from pathlib import Path

# Java 환경 설정
os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
os.environ["GHIDRA_INSTALL_DIR"] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"

def decompile_function(program, offset_hex):
    """단일 함수 디컴파일"""
    from ghidra.app.decompiler import DecompInterface
    from ghidra.app.cmd.disassemble import DisassembleCommand
    from ghidra.app.cmd.function import CreateFunctionCmd
    from ghidra.util.task import ConsoleTaskMonitor

    # 주소 생성 (Segment:Offset 형식)
    # 1000:293e -> Linear = 0x1000 * 16 + 0x293e = 0x1293e
    linear_addr = 0x1000 * 16 + offset_hex
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    addr = addr_space.getAddress(linear_addr)

    # 함수 존재 확인
    listing = program.getListing()
    func = listing.getFunctionAt(addr)

    # 함수가 없으면 생성
    if func is None:
        print(f"    ⚠️  함수 없음, 생성 시도...")

        # 1. 먼저 디스어셈블
        print(f"    → 디스어셈블 중...")
        disasm_cmd = DisassembleCommand(addr, None, True)
        if not disasm_cmd.applyTo(program):
            print(f"    ❌ 디스어셈블 실패: {disasm_cmd.getStatusMsg()}")
            return None
        print(f"    ✅ 디스어셈블 완료")

        # 2. 함수 생성
        print(f"    → 함수 생성 중...")
        from ghidra.program.model.symbol import SourceType
        func_cmd = CreateFunctionCmd(f"FUN_1000_{offset_hex:04x}", addr, None,
                                      SourceType.USER_DEFINED)
        if not func_cmd.applyTo(program):
            print(f"    ❌ 함수 생성 실패: {func_cmd.getStatusMsg()}")
            return None

        func = listing.getFunctionAt(addr)
        if func is None:
            print(f"    ❌ 함수 생성 후에도 함수 없음")
            return None
        print(f"    ✅ 함수 생성 완료")

    # 디컴파일
    monitor = ConsoleTaskMonitor()
    decompiler = DecompInterface()
    decompiler.openProgram(program)

    result = decompiler.decompileFunction(func, 30, monitor)

    if not result or not result.decompileCompleted():
        error_msg = result.getErrorMessage() if result else "Unknown error"
        print(f"    ❌ 디컴파일 실패: {error_msg}")
        return None

    c_code = result.getDecompiledFunction().getC()
    decompiler.dispose()

    return c_code

def main():
    """메인 함수"""
    print("="*70)
    print("🚀 미분석 함수 일괄 디컴파일")
    print("="*70)

    # pyghidra import
    try:
        import pyghidra
    except ImportError:
        print("\n❌ pyghidra를 찾을 수 없습니다.")
        print("\n설치:")
        print("  source venv/bin/activate")
        print("  pip install pyghidra")
        return

    # 미분석 함수 목록
    missing_offsets = [
        0x293e,  # 29회 호출 - 최우선!
        0x3824,  # 8회
        0x3265,  # 6회
        0x3384,  # 6회
        0x2711,  # 6회
        0x28c0,  # 4회
        0x28ef,  # 4회
        0x3818,  # 4회
        0x1ea2,  # 디스패처
        0x1dfc,  # 디스패처
        0x1dff,  # 디스패처
        0x1e02,  # 디스패처
        0x5fec,  # 디스패처
        0x6009,  # 디스패처
        0x6011,  # 디스패처
    ]

    print(f"\n대상: {len(missing_offsets)}개 함수")

    # Ghidra 프로젝트 열기
    project_path = "ghidra-project/DoubleDragon"
    project_name = "DoubleDragon"

    if not Path(project_path).exists():
        print(f"\n❌ Ghidra 프로젝트를 찾을 수 없습니다: {project_path}")
        return

    print(f"\n📂 Ghidra 프로젝트 로딩: {project_path}")

    binary_path = "reference/dos-original/DDMAIN.EXE"

    with pyghidra.open_program(binary_path, project_location=project_path, project_name=project_name) as flat_api:
        program = flat_api.getCurrentProgram()
        print(f"   프로그램: {program.getName()}")

        success_count = 0
        fail_count = 0

        # 각 함수 디컴파일
        for offset in missing_offsets:
            print(f"\n[{success_count+fail_count+1}/{len(missing_offsets)}] FUN_1000_{offset:04x} 처리 중...")

            c_code = decompile_function(program, offset)

            if c_code:
                # C 파일 저장
                output_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
                with open(output_file, 'w') as f:
                    f.write(c_code)

                # JSON 메타데이터 저장
                json_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.json")
                metadata = {
                    "function_name": f"FUN_1000_{offset:04x}",
                    "address": f"1000:{offset:04x}",
                    "source": "batch_decompile_missing.py",
                    "size": len(c_code)
                }
                with open(json_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                print(f"    ✅ 저장: {output_file} ({len(c_code)} bytes)")
                success_count += 1
            else:
                fail_count += 1

    print("\n" + "="*70)
    print("📊 결과")
    print("="*70)
    print(f"  성공: {success_count}개")
    print(f"  실패: {fail_count}개")

    if success_count > 0:
        print(f"\n✅ {success_count}개 함수 디컴파일 완료!")
        print(f"   output/decompiled/ 디렉토리 확인하세요.")

if __name__ == "__main__":
    main()
