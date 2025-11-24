#!/usr/bin/env python3
"""
0x18c6 점프 테이블의 미인식 함수 9개 일괄 디컴파일
Phase 4.5 방식 적용
"""

import os
from pathlib import Path
import json

# ⭐ 1. 환경 변수 설정 (가장 먼저!)
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

# ⭐ 2. pyghidra import
import pyghidra

# ⭐ 3. 프로젝트 경로 설정
PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

# 복구할 함수 오프셋 목록 (0x18c6 테이블에서 발견)
MISSING_FUNCTIONS = [
    0x48e4,  # Index 0
    0x81c6,  # Index 1
    0x822e,  # Index 2
    0x827b,  # Index 3
    0x82f8,  # Index 4
    0x8139,  # Index 5
    0x810f,  # Index 6
    0x5864,  # Index 7
    0x591d,  # Index 8
]

print("=" * 70)
print("0x18c6 점프 테이블 미인식 함수 복구")
print("=" * 70)
print(f"복구 대상: {len(MISSING_FUNCTIONS)}개 함수")
print()

# ⭐ 4. Ghidra 시작
print("Ghidra 초기화 중...")
pyghidra.start(verbose=False)

# Ghidra API import
from ghidra.app.decompiler import DecompInterface
from ghidra.program.model.listing import Function
from ghidra.program.model.symbol import SourceType
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.util.task import ConsoleTaskMonitor

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

    # Transaction 시작
    txid = program.startTransaction("Recover 0x18c6 Missing Functions")

    try:
        # 디컴파일러 초기화
        decompiler = DecompInterface()
        decompiler.openProgram(program)
        monitor = ConsoleTaskMonitor()

        # 세그먼트
        CODE_SEGMENT = 0x1000

        results = {
            'success': [],
            'failed': [],
            'already_exists': []
        }

        for i, offset_hex in enumerate(MISSING_FUNCTIONS):
            func_name = f"FUN_1000_{offset_hex:04x}"

            print(f"\n[{i+1}/{len(MISSING_FUNCTIONS)}] {func_name}")
            print("-" * 70)

            # 주소 계산
            linear_addr = (CODE_SEGMENT << 4) + offset_hex
            addr = address_space.getAddress(linear_addr)

            print(f"  주소: 1000:{offset_hex:04x} (linear: 0x{linear_addr:x})")

            # 이미 함수가 있는지 확인
            existing_func = flat_api.getFunctionAt(addr)
            if existing_func:
                print(f"  ⚠️  이미 존재: {existing_func.getName()}")
                results['already_exists'].append({
                    'offset': f"0x{offset_hex:04x}",
                    'name': existing_func.getName()
                })
                continue

            try:
                # 1단계: 디스어셈블
                print(f"  1️⃣  디스어셈블 중...")
                disasm_cmd = DisassembleCommand(addr, None, True)
                disasm_success = disasm_cmd.applyTo(program)

                if not disasm_success:
                    raise Exception(f"디스어셈블 실패: {disasm_cmd.getStatusMsg()}")

                # 2단계: 함수 생성
                print(f"  2️⃣  함수 생성 중...")
                func_cmd = CreateFunctionCmd(func_name, addr, None, SourceType.USER_DEFINED)
                func_success = func_cmd.applyTo(program)

                if not func_success:
                    raise Exception(f"함수 생성 실패: {func_cmd.getStatusMsg()}")

                # 3단계: 함수 가져오기
                func = flat_api.getFunctionAt(addr)
                if not func:
                    raise Exception("함수 생성 후 가져오기 실패")

                func_size = func.getBody().getNumAddresses()
                print(f"  3️⃣  함수 크기: {func_size} bytes")

                # 4단계: 디컴파일
                print(f"  4️⃣  디컴파일 중...")
                result = decompiler.decompileFunction(func, 30, monitor)

                if not result or not result.decompileCompleted():
                    error_msg = result.getErrorMessage() if result else "Unknown error"
                    raise Exception(f"디컴파일 실패: {error_msg}")

                c_code = result.getDecompiledFunction().getC()

                # 5단계: C 파일 저장
                output_path = Path(f"output/decompiled/{func_name}.c")
                output_path.write_text(c_code, encoding='utf-8')
                print(f"  ✅ 저장: {output_path}")

                results['success'].append({
                    'offset': f"0x{offset_hex:04x}",
                    'name': func_name,
                    'size': func_size,
                    'file': str(output_path)
                })

            except Exception as e:
                print(f"  ❌ 실패: {e}")
                results['failed'].append({
                    'offset': f"0x{offset_hex:04x}",
                    'name': func_name,
                    'error': str(e)
                })

        # Transaction 완료
        program.endTransaction(txid, True)

    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        program.endTransaction(txid, False)
        raise

    finally:
        decompiler.dispose()

# 결과 출력
print("\n" + "=" * 70)
print("📊 결과")
print("=" * 70)
print(f"  성공: {len(results['success'])}개")
print(f"  실패: {len(results['failed'])}개")
print(f"  이미 존재: {len(results['already_exists'])}개")

if results['success']:
    print("\n✅ 성공한 함수:")
    for item in results['success']:
        print(f"  - {item['name']} ({item['size']} bytes)")

if results['failed']:
    print("\n❌ 실패한 함수:")
    for item in results['failed']:
        print(f"  - {item['name']}: {item['error']}")

if results['already_exists']:
    print("\n⚠️  이미 존재하는 함수:")
    for item in results['already_exists']:
        print(f"  - {item['name']}")

# JSON 저장
checkpoint_path = Path("output/checkpoints/phase4_6_18c6_recovery.json")
checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

checkpoint_data = {
    "phase": "4.6",
    "title": "0x18c6 점프 테이블 미인식 함수 복구",
    "timestamp": "2025-11-24",
    "target": "0x18c6 렌더링 점프 테이블",
    "missing_functions": len(MISSING_FUNCTIONS),
    "results": results,
    "success_rate": len(results['success']) / len(MISSING_FUNCTIONS) * 100
}

checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n💾 체크포인트 저장: {checkpoint_path}")

print(f"\n✅ 완료!")
