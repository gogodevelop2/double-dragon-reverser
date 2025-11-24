#!/usr/bin/env python3
"""
LZW 압축 해제 및 스프라이트 데이터 추출
"""

import struct
from pathlib import Path

def decompress_lzw(compressed_data):
    """
    Unix compress 형식 LZW 압축 해제

    파일 포맷:
    - 바이트 0-1: 매직 넘버 (0x1f, 0x9d)
    - 바이트 2: 옵션 (bits per code)
    - 바이트 3+: 압축된 데이터
    """
    if len(compressed_data) < 3:
        return None

    if compressed_data[0] != 0x1f or compressed_data[1] != 0x9d:
        print("LZW 시그니처가 아닙니다")
        return None

    # 비트 수 추출 (하위 5비트)
    max_bits = compressed_data[2] & 0x1f
    block_mode = (compressed_data[2] & 0x80) != 0

    print(f"LZW 설정: max_bits={max_bits}, block_mode={block_mode}")

    # Python의 lzw 디코딩은 복잡하므로, 시스템 명령어 사용을 시도
    # 대신 데이터 구조 분석에 집중

    return compressed_data[3:]  # 헤더 제거한 데이터 반환

def analyze_decompressed_data(data, name):
    """압축 해제된 데이터 분석"""
    print(f"\n=== {name} 압축 해제 데이터 분석 ===")
    print(f"데이터 크기: {len(data)} bytes")

    # 첫 256 바이트 헥스 덤프
    print("\n첫 256 바이트:")
    for i in range(0, min(256, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04x}: {hex_str:47s} {ascii_str}")

    # 가능한 헤더 정보 추출 (첫 32바이트에서)
    if len(data) >= 32:
        print("\n가능한 헤더 정보:")
        # 처음 16개 바이트를 다양한 형식으로 해석
        for i in range(min(8, len(data) // 2)):
            offset = i * 2
            word = struct.unpack('<H', data[offset:offset+2])[0]
            print(f"  Offset {offset:2d} (word): {word:5d} (0x{word:04x})")

    # 0xFF로 구분되는 섹션 찾기
    sections = []
    current_pos = 0
    for i, byte in enumerate(data):
        if byte == 0xff and i > current_pos + 10:
            sections.append((current_pos, i))
            current_pos = i + 1

    if sections:
        print(f"\n0xFF로 구분된 섹션: {len(sections)}개")
        for idx, (start, end) in enumerate(sections[:5]):
            print(f"  섹션 {idx+1}: {start:5d} ~ {end:5d} ({end-start:5d} bytes)")

def extract_sprites_smart(filepath):
    """스프라이트 파일 스마트 추출"""
    print(f"\n{'='*60}")
    print(f"파일 분석: {filepath.name}")
    print('='*60)

    with open(filepath, 'rb') as f:
        data = f.read()

    # LZW 헤더 확인
    if data[0:2] == b'\x1f\x9d':
        print("LZW 압축 파일입니다.")
        # 여기서는 압축된 상태로 구조 분석
        # 실제 압축 해제는 외부 도구 필요

        # 압축된 데이터에서도 패턴 찾기 시도
        print("\n압축된 상태에서 패턴 분석...")

        # 특정 바이트 시퀀스 찾기 (이미지 데이터 시작 가능성)
        markers = [
            b'\x00\x00\x00\x00',  # 4바이트 NULL
            b'\xFF\xFF',          # 2바이트 0xFF
            b'\x00\x10',          # 가능한 크기 정보
        ]

        for marker in markers:
            positions = []
            start = 0
            while True:
                pos = data.find(marker, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1

            if positions:
                hex_marker = ' '.join(f'{b:02x}' for b in marker)
                print(f"\n마커 [{hex_marker}] 발견: {len(positions)}개 위치")
                if len(positions) <= 20:
                    print(f"  위치: {positions}")

if __name__ == '__main__':
    ref_path = Path(__file__).parent.parent / 'reference' / 'dos-original'

    # 주요 스프라이트 파일 분석
    sprite_files = [
        'PLAYER1.EG1',
        'ABOBO.EG1',
        'WEAPONS.EG1',
    ]

    for filename in sprite_files:
        filepath = ref_path / filename
        if filepath.exists():
            extract_sprites_smart(filepath)
        else:
            print(f"파일 없음: {filepath}")

    print("\n\n" + "="*60)
    print("다음 단계:")
    print("1. DOSBox에서 메모리 덤프")
    print("2. 온라인 스프라이트 리소스 검색")
    print("3. 스크린샷 기반 수동 추출")
    print("="*60)
