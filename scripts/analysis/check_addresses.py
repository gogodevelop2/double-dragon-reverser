#!/usr/bin/env python3
"""주소들 확인"""
import os
from pathlib import Path
import pyghidra

os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

def main():
    with pyghidra.open_program(str(BINARY_PATH), project_location=PROJECT_PATH, project_name=PROJECT_NAME) as flat_api:
        program = flat_api.getCurrentProgram()
        memory = program.getMemory()
        listing = program.getListing()

        # FUN_1000_0b94에서 사용하는 주소들
        addrs_to_check = [0x1790, 0x179c, 0x17a8, 0x1786]

        for offset in addrs_to_check:
            addr = program.getAddressFactory().getDefaultAddressSpace().getAddress(0x1000 * 16 + offset)

            print(f"\n주소: 1000:{offset:04x} ({addr})")

            # 16 bytes 읽기
            try:
                bytes_data = []
                ascii_data = []
                for i in range(32):
                    b = memory.getByte(addr.add(i)) & 0xFF
                    bytes_data.append(f"{b:02x}")
                    if 32 <= b < 127:
                        ascii_data.append(chr(b))
                    else:
                        ascii_data.append('.')

                hex_str = ' '.join(bytes_data[:16])
                hex_str2 = ' '.join(bytes_data[16:32])
                ascii_str = ''.join(ascii_data[:16])
                ascii_str2 = ''.join(ascii_data[16:32])

                print(f"  {hex_str}  {ascii_str}")
                print(f"  {hex_str2}  {ascii_str2}")

                # 데이터 타입
                data = listing.getDataAt(addr)
                if data:
                    print(f"  타입: {data.getDataType()}")

            except Exception as e:
                print(f"  오류: {e}")

if __name__ == "__main__":
    main()
