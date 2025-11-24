#!/usr/bin/env python3
"""
Double Dragon 커스텀 압축 해제 루틴 재구현

DDMAIN.EXE의 압축 해제 코드를 분석하여 재구현
오프셋 0x6DE0 부근의 어셈블리 코드 기반
"""

from pathlib import Path
import struct

def analyze_decompression_code():
    """
    압축 해제 루틴 어셈블리 분석

    0x6DE0: 8B 04         MOV AX, [SI]      ; 헤더 읽기
    0x6DE2: 3D 1F 9D      CMP AX, 0x9D1F    ; LZW 시그니처 확인
    0x6DE5: 74 05         JZ  short_jump    ; 일치하면 점프
    0x6DE7: B9 00 00      MOV CX, 0         ; 실패 시 0 반환
    0x6DEA: F9            STC               ; Carry 플래그 설정
    0x6DEB: C3            RET

    압축 해제 로직:
    - 헤더 확인 (0x1F 0x9D)
    - 비트 스트림 읽기
    - 딕셔너리 기반 디코딩
    """

    print("=== DDMAIN.EXE 압축 해제 루틴 분석 ===\n")

    print("주요 발견:")
    print("1. 시그니처 확인: CMP AX, 0x9D1F (리틀 엔디안)")
    print("2. 비트 단위 읽기 루틴 존재")
    print("3. 딕셔너리 테이블 사용 (LZW 변형)")
    print("4. 버퍼 주소: 0x6538, 0x653A, 0x6534")
    print()

def custom_decompress(data):
    """
    커스텀 압축 해제 시도

    분석된 어셈블리 코드를 기반으로 구현
    """
    if len(data) < 3:
        return None

    # 헤더 확인 (리틀 엔디안)
    if data[0] != 0x1f or data[1] != 0x9d:
        print("시그니처 불일치")
        return None

    # 세 번째 바이트: 플래그/옵션
    flags = data[2]
    max_bits = flags & 0x1F

    print(f"플래그: 0x{flags:02x}")
    print(f"최대 비트: {max_bits}")

    # 실제 압축 데이터는 3바이트부터
    compressed = data[3:]

    # 여기서부터 커스텀 로직 필요
    # DDMAIN.EXE의 0x6E90~ 루틴 참조

    # 비트 버퍼 초기화
    bit_buffer = 0
    bits_in_buffer = 0
    pos = 0

    output = bytearray()

    # 간단한 시도: RLE 또는 비트 패킹 체크
    print(f"압축 데이터 크기: {len(compressed)} bytes")
    print(f"첫 16 바이트: {' '.join(f'{b:02x}' for b in compressed[:16])}")

    return None  # 아직 완전 구현 안됨

def find_decompression_routine():
    """DDMAIN.EXE에서 압축 해제 루틴 추출"""

    exe_path = Path(__file__).parent.parent / 'reference' / 'dos-original' / 'DDMAIN.EXE'

    with open(exe_path, 'rb') as f:
        exe_data = f.read()

    # 압축 해제 루틴 시작 지점 (0x6DE0)
    offset = 0x6DE0
    routine_size = 0x200  # 약 512 바이트

    routine = exe_data[offset:offset + routine_size]

    print(f"\n=== 압축 해제 루틴 코드 (오프셋 0x{offset:04x}) ===\n")

    # 중요한 바이트 시퀀스 찾기
    patterns = {
        b'\x3D\x1F\x9D': 'LZW 시그니처 체크 (CMP AX, 0x9D1F)',
        b'\x74\x05': '점프 명령 (JZ)',
        b'\xB9\x00\x00': '카운터 초기화 (MOV CX, 0)',
        b'\xD1\xE0': '시프트 연산 (SHL AX, 1)',
        b'\xD0\xD3': '비트 시프트 (ROL BL, 1)',
    }

    for pattern, desc in patterns.items():
        pos = routine.find(pattern)
        if pos != -1:
            print(f"0x{offset+pos:04x}: {pattern.hex()} - {desc}")

    # 압축 해제 루틴 추출
    output_path = Path(__file__).parent / 'decompress_routine.bin'
    with open(output_path, 'wb') as f:
        f.write(routine)

    print(f"\n압축 해제 루틴 저장: {output_path}")

    return routine

def test_with_real_file():
    """실제 파일로 테스트"""

    test_file = Path(__file__).parent.parent / 'reference' / 'dos-original' / 'CHARSET.BIN'

    print(f"\n=== 테스트: {test_file.name} ===\n")

    with open(test_file, 'rb') as f:
        data = f.read()

    print(f"파일 크기: {len(data)} bytes")
    print(f"헤더: {' '.join(f'{b:02x}' for b in data[:16])}")

    result = custom_decompress(data)

    if result:
        print(f"\n압축 해제 성공: {len(result)} bytes")
    else:
        print("\n압축 해제 실패 또는 미구현")

def extract_and_document():
    """전체 분석 및 문서화"""

    print("="*60)
    print("Double Dragon 커스텀 압축 포맷 리버스 엔지니어링")
    print("="*60)

    # 1. 압축 해제 코드 분석
    analyze_decompression_code()

    # 2. DDMAIN.EXE에서 루틴 추출
    routine = find_decompression_routine()

    # 3. 실제 파일로 테스트
    test_with_real_file()

    print("\n" + "="*60)
    print("다음 단계:")
    print("1. 어셈블리 코드 완전 디스어셈블 (IDA Pro, Ghidra)")
    print("2. 비트 스트림 읽기 로직 재구현")
    print("3. LZW 딕셔너리 재구성 알고리즘 구현")
    print("="*60)

if __name__ == '__main__':
    extract_and_document()
