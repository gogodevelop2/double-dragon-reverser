#!/usr/bin/env python3
"""
Unicorn 엔진을 사용한 Double Dragon 압축 해제

DDMAIN.EXE의 실제 압축 해제 루틴을 x86 에뮬레이터로 실행
"""

from unicorn import *
from unicorn.x86_const import *
from pathlib import Path
import struct

def decompress_with_unicorn(compressed_file_path, output_path=None):
    """
    Unicorn 엔진으로 DOS 압축 해제 루틴 실행
    """
    # 파일 읽기
    with open(compressed_file_path, 'rb') as f:
        compressed_data = f.read()

    print(f"압축 파일: {compressed_file_path.name}")
    print(f"압축 크기: {len(compressed_data)} bytes")

    # 압축 해제 루틴 로드
    routine_path = Path(__file__).parent / 'decompress_routine.bin'
    with open(routine_path, 'rb') as f:
        routine_code = f.read()

    print(f"루틴 크기: {len(routine_code)} bytes")

    try:
        # Unicorn 초기화 (x86 16비트 모드)
        uc = Uc(UC_ARCH_X86, UC_MODE_16)

        # 메모리 맵 (1MB)
        BASE = 0x10000
        SIZE = 0x100000
        uc.mem_map(BASE, SIZE)

        # 코드 세그먼트 (압축 해제 루틴)
        CODE_ADDR = BASE + 0x1000
        uc.mem_write(CODE_ADDR, routine_code)

        # 데이터 세그먼트 (압축된 데이터)
        DATA_ADDR = BASE + 0x10000
        uc.mem_write(DATA_ADDR, compressed_data)

        # 출력 버퍼
        OUTPUT_ADDR = BASE + 0x20000
        OUTPUT_SIZE = 0x10000  # 64KB

        # 레지스터 초기화
        uc.reg_write(UC_X86_REG_SI, DATA_ADDR)      # 입력 포인터
        uc.reg_write(UC_X86_REG_DI, OUTPUT_ADDR)    # 출력 포인터
        uc.reg_write(UC_X86_REG_DS, BASE >> 4)      # 데이터 세그먼트
        uc.reg_write(UC_X86_REG_ES, BASE >> 4)      # 출력 세그먼트
        uc.reg_write(UC_X86_REG_SS, (BASE + 0x8000) >> 4)  # 스택
        uc.reg_write(UC_X86_REG_SP, 0x1000)         # 스택 포인터

        # 실행 (압축 해제 루틴의 시작 오프셋은 0x00)
        # 원래 오프셋 0x6DE0이지만, 추출한 루틴은 0부터 시작
        print("\n압축 해제 실행 중...")

        # 최대 100만 명령어 실행
        uc.emu_start(CODE_ADDR, CODE_ADDR + len(routine_code), timeout=10*UC_SECOND_SCALE, count=1000000)

        # 결과 읽기
        decompressed = uc.mem_read(OUTPUT_ADDR, OUTPUT_SIZE)

        # 실제 데이터 크기 찾기 (0으로 채워진 부분 제외)
        actual_size = len(decompressed)
        for i in range(len(decompressed) - 1, -1, -1):
            if decompressed[i] != 0:
                actual_size = i + 1
                break

        decompressed = bytes(decompressed[:actual_size])

        print(f"✓ 압축 해제 성공!")
        print(f"  원본: {len(compressed_data):6d} bytes")
        print(f"  해제: {len(decompressed):6d} bytes")
        print(f"  비율: {len(decompressed)/len(compressed_data):.2f}x")

        # 저장
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(decompressed)
            print(f"  저장: {output_path}")

        return decompressed

    except UcError as e:
        print(f"✗ 에뮬레이션 에러: {e}")
        print("  원인: 압축 해제 루틴이 불완전하거나 메모리 설정 문제")
        return None

def test_all_files():
    """모든 압축 파일 테스트"""

    ref_path = Path(__file__).parent.parent / 'reference' / 'dos-original'
    output_path = Path(__file__).parent / 'decompressed_unicorn'
    output_path.mkdir(exist_ok=True)

    print("="*60)
    print("Unicorn 엔진을 사용한 압축 해제")
    print("="*60)

    # 테스트할 파일들
    test_files = [
        'CHARSET.BIN',   # 가장 작은 파일부터
        'LINDA.EG1',
        'PLAYER1.EG1',
        'LEVEL11.PC1',
    ]

    for filename in test_files:
        filepath = ref_path / filename
        if filepath.exists():
            print()
            output_file = output_path / f"{filepath.stem}.raw"
            result = decompress_with_unicorn(filepath, output_file)

            if result:
                # 처음 64바이트 출력
                print(f"\n  처음 64 바이트:")
                for i in range(0, min(64, len(result)), 16):
                    hex_str = ' '.join(f'{b:02x}' for b in result[i:i+16])
                    print(f"    {i:04x}: {hex_str}")
        else:
            print(f"파일 없음: {filename}")

        print("-"*60)

    print("\n압축 해제 완료!")
    print(f"출력 디렉토리: {output_path}")

if __name__ == '__main__':
    test_all_files()
