#!/usr/bin/env python3
"""
Double Dragon 모든 파일 압축 해제 및 분석
"""

import unlzw3
from pathlib import Path
import struct

def decompress_file(input_path, output_path):
    """LZW 압축 파일 해제"""
    try:
        with open(input_path, 'rb') as f:
            compressed = f.read()

        # unlzw3로 압축 해제
        decompressed = unlzw3.unlzw(compressed)

        # 결과 저장
        with open(output_path, 'wb') as f:
            f.write(decompressed)

        print(f"✓ {input_path.name}")
        print(f"  압축:   {len(compressed):6d} bytes")
        print(f"  해제:   {len(decompressed):6d} bytes")
        print(f"  비율:   {len(decompressed)/len(compressed):.2f}x")

        return decompressed

    except Exception as e:
        print(f"✗ {input_path.name}: {e}")
        return None

def analyze_raw_data(data, name):
    """압축 해제된 원시 데이터 분석"""
    if not data:
        return

    print(f"\n  --- {name} 원시 데이터 분석 ---")

    # 첫 64바이트 덤프
    print("  첫 64 바이트:")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"    {i:04x}: {hex_str:47s} {ascii_str}")

    # 가능한 헤더 정보 (16비트 리틀 엔디안 워드들)
    if len(data) >= 16:
        print("\n  가능한 헤더 값:")
        for i in range(8):
            if i * 2 + 1 < len(data):
                word = struct.unpack('<H', data[i*2:i*2+2])[0]
                print(f"    Word {i}: {word:5d} (0x{word:04x})")

def main():
    # 경로 설정
    base_path = Path(__file__).parent.parent
    ref_path = base_path / 'reference' / 'dos-original'
    output_path = base_path / 'analysis' / 'decompressed'
    output_path.mkdir(exist_ok=True)

    print("="*60)
    print("Double Dragon LZW 압축 해제")
    print("="*60)

    # 모든 압축 파일 찾기
    file_patterns = ['*.EG1', '*.EG2', '*.PC1', '*.CGA', '*.BIN', '*.NW*', '*.ABO', '*.BOS', '*.LIN', '*.PL1', '*.WEP', '*.WIL']
    all_files = []
    for pattern in file_patterns:
        all_files.extend(ref_path.glob(pattern))

    # 중복 제거 및 정렬
    all_files = sorted(set(all_files))

    print(f"\n총 {len(all_files)}개 파일 발견\n")

    # 각 파일 압축 해제
    for filepath in all_files:
        output_file = output_path / f"{filepath.stem}.raw"
        decompressed = decompress_file(filepath, output_file)

        # 중요 파일은 상세 분석
        if filepath.name in ['PLAYER1.EG1', 'LEVEL11.PC1', 'LDSCRN.CGA']:
            analyze_raw_data(decompressed, filepath.name)

        print()

    print("="*60)
    print(f"압축 해제 완료: {output_path}")
    print("="*60)

if __name__ == '__main__':
    main()
