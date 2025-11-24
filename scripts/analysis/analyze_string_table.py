#!/usr/bin/env python3
"""
문자열 테이블 주변 분석
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
    """문자열 테이블 분석"""

    print("=" * 70)
    print("문자열 테이블 영역 분석")
    print("=" * 70)

    with pyghidra.open_program(str(BINARY_PATH), project_location=PROJECT_PATH, project_name=PROJECT_NAME) as flat_api:
        program = flat_api.getCurrentProgram()
        listing = program.getListing()
        memory = program.getMemory()

        # LINDA.EG1이 있는 주소: 1000:affc
        # 이 주변 영역 분석
        from ghidra.program.model.address import GenericAddress

        # 주소 생성
        addr_space = program.getAddressFactory().getDefaultAddressSpace()

        # 1000:afe0 부터 1000:b0a0 까지 분석 (약 200 bytes)
        start_offset = 0xafe0
        end_offset = 0xb0a0

        print(f"\n분석 범위: 1000:{start_offset:04x} - 1000:{end_offset:04x}")
        print()

        # 데이터 읽기
        for offset in range(start_offset, end_offset, 16):
            addr = addr_space.getAddress(0x1000 * 16 + offset)

            # 16 bytes 읽기
            bytes_data = []
            ascii_data = []
            for i in range(16):
                try:
                    byte = memory.getByte(addr.add(i))
                    bytes_data.append(f"{byte & 0xFF:02x}")

                    # ASCII 변환
                    b = byte & 0xFF
                    if 32 <= b < 127:
                        ascii_data.append(chr(b))
                    else:
                        ascii_data.append('.')
                except:
                    bytes_data.append("  ")
                    ascii_data.append(' ')

            hex_str = ' '.join(bytes_data)
            ascii_str = ''.join(ascii_data)

            print(f"1000:{offset:04x}  {hex_str}  {ascii_str}")

            # 데이터 타입 체크
            data = listing.getDataAt(addr)
            if data:
                print(f"         → 데이터 타입: {data.getDataType()}")

        print("\n\n" + "=" * 70)
        print("문자열 주소들:")
        print("=" * 70)

        # 각 문자열의 정확한 주소 출력
        strings = [
            b"WILLIAM.EG1",
            b"LINDA.EG1",
            b"ABOBO.EG1",
            b"PLAYER1.EG1",
            b"WEAPONS.EG1",
            b"BIGBWLY.EG1"
        ]

        from ghidra.util.task import ConsoleTaskMonitor

        string_addrs = []
        for s in strings:
            found = memory.findBytes(
                program.getMinAddress(),
                s,
                None,
                True,
                ConsoleTaskMonitor()
            )
            if found:
                print(f"{s.decode('ascii'):15s} @ {found}")
                string_addrs.append((s.decode('ascii'), found))

        # 이 주소들 사이의 간격 분석
        print("\n간격 분석:")
        for i in range(len(string_addrs) - 1):
            name1, addr1 = string_addrs[i]
            name2, addr2 = string_addrs[i+1]
            gap = addr2.subtract(addr1)
            print(f"  {name1} → {name2}: {gap} bytes")

        # 문자열 테이블 시작 전 영역 확인
        # WILLIAM.EG1 이전 영역에 포인터 테이블이 있을 가능성
        if string_addrs:
            first_str_addr = string_addrs[0][1]

            # 64 bytes 이전부터 확인
            table_start = first_str_addr.subtract(64)

            print(f"\n\n문자열 테이블 이전 영역 (포인터 테이블?): {table_start}")
            print("="*70)

            for i in range(32):  # 32 워드 (64 bytes) 확인
                addr = table_start.add(i * 2)
                try:
                    word = memory.getShort(addr) & 0xFFFF
                    print(f"  [{i:2d}] {addr}: 0x{word:04x} ({word:5d})")
                except:
                    pass

if __name__ == "__main__":
    main()
