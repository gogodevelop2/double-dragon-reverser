#!/usr/bin/env python3
"""
0x18c6 렌더링 점프 테이블 덤프
FUN_1000_48e0에서 사용하는 점프 테이블 분석
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

    # ⭐ 6. 세그먼트 정의
    CODE_SEGMENT = 0x1000   # 코드
    DATA_SEGMENT = 0x1988   # 데이터

    print("=" * 70)
    print("렌더링 점프 테이블 @ 0x18c6")
    print("=" * 70)
    print()

    # 0x18c6은 데이터 세그먼트에 있음
    table_offset = 0x18c6
    table_addr = address_space.getAddress((DATA_SEGMENT << 4) + table_offset)

    print(f"테이블 주소 (데이터 세그먼트): 1988:{table_offset:04x}")
    print(f"Physical 주소: 0x{table_addr.getOffset():x}")
    print()

    # 점프 테이블 읽기 (최대 30개 엔트리)
    entries = []
    for i in range(30):
        try:
            current_addr = table_addr.add(i * 2)

            # 2바이트 읽기 (little-endian)
            byte1 = memory.getByte(current_addr) & 0xFF
            byte2 = memory.getByte(current_addr.add(1)) & 0xFF

            # 오프셋 값
            offset = byte1 | (byte2 << 8)

            # 0이거나 너무 작으면 종료 (함수는 최소 0x100 이상)
            if offset == 0 or offset < 0x100:
                break

            # 타겟 주소 계산 (코드 세그먼트 1000 기준)
            target_linear = (CODE_SEGMENT << 4) + offset
            target_addr = address_space.getAddress(target_linear)

            # 함수 찾기
            func = flat_api.getFunctionAt(target_addr)
            func_name = func.getName() if func else "???"

            # 코드 확인
            code_unit = listing.getCodeUnitAt(target_addr)
            first_instr = code_unit.toString() if code_unit else "???"

            entries.append({
                'index': i,
                'table_addr': f"0x{current_addr.getOffset():x}",
                'offset': f"0x{offset:04x}",
                'target': f"1000:{offset:04x}",
                'function': func_name,
                'instruction': first_instr[:60]
            })

        except Exception as e:
            print(f"⚠️  Index {i}: 읽기 실패 - {e}")
            break

    # 결과 출력
    print(f"발견된 엔트리: {len(entries)}개\n")

    for entry in entries:
        print(f"[{entry['index']:2d}] @ {entry['table_addr']}")
        print(f"     Offset: {entry['offset']}")
        print(f"     Target: {entry['target']}")
        print(f"     Function: {entry['function']}")
        print(f"     First Instruction: {entry['instruction']}")
        print()

    # 요약 테이블
    print("=" * 70)
    print("요약")
    print("=" * 70)
    print()
    print("| Index | Offset | Target | Function |")
    print("|-------|--------|--------|----------|")
    for entry in entries:
        print(f"| {entry['index']:5d} | {entry['offset']} | {entry['target']} | {entry['function']:20s} |")

    print()
    print(f"✅ 완료: {len(entries)}개 함수 포인터 덤프됨")
