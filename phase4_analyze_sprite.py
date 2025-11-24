#!/usr/bin/env python3
"""
Phase 4: 스프라이트 데이터 분석

LZW 압축 해제된 데이터를 분석하여 포맷 파악
"""

from pathlib import Path
import struct

def analyze_sprite(file_path):
    """스프라이트 파일 분석"""
    with open(file_path, 'rb') as f:
        data = f.read()

    print(f"\n{'='*70}")
    print(f"파일: {file_path.name}")
    print(f"크기: {len(data)} bytes")
    print(f"{'='*70}")

    # 헤더 분석 (처음 32 bytes)
    print("\n헤더 (처음 32 bytes):")
    print("  Offset  Hex                                       ASCII")
    for i in range(0, min(32, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  0x{i:04x}: {hex_str:48s} {ascii_str}")

    # 가능한 헤더 필드
    print("\n가능한 헤더 필드:")

    if len(data) >= 2:
        val16_0 = struct.unpack('<H', data[0:2])[0]
        print(f"  [0-1] uint16 LE: {val16_0} (0x{val16_0:04x})")

        if val16_0 == len(data):
            print(f"    → 파일 크기와 일치!")
        elif val16_0 == len(data) - 2:
            print(f"    → 데이터 크기 (헤더 제외)")

    if len(data) >= 4:
        val16_2 = struct.unpack('<H', data[2:4])[0]
        val8_2 = data[2]
        val8_3 = data[3]
        print(f"  [2-3] uint16 LE: {val16_2} (0x{val16_2:04x})")
        print(f"  [2] uint8: {val8_2} (0x{val8_2:02x})")
        print(f"  [3] uint8: {val8_3} (0x{val8_3:02x})")

        # 폭/높이 가능성
        if val8_2 > 0 and val8_3 > 0:
            pixels = val8_2 * val8_3
            bytes_needed = pixels // 4  # 2 bpp = 4 pixels per byte
            print(f"    → 만약 폭={val8_2}, 높이={val8_3}: {pixels} pixels, {bytes_needed} bytes 필요")

    if len(data) >= 6:
        val16_4 = struct.unpack('<H', data[4:6])[0]
        print(f"  [4-5] uint16 LE: {val16_4} (0x{val16_4:04x})")

    # 데이터 패턴 분석
    print("\n데이터 통계:")
    byte_counts = {}
    for b in data:
        byte_counts[b] = byte_counts.get(b, 0) + 1

    print(f"  고유 바이트 값: {len(byte_counts)}")
    print(f"  가장 많은 값 (top 10):")
    sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
    for val, count in sorted_bytes[:10]:
        percent = count / len(data) * 100
        print(f"    0x{val:02x}: {count:4d}회 ({percent:5.2f}%)")

    # RLE 패턴 감지
    print("\n반복 패턴:")
    max_run = 0
    current_run = 1
    for i in range(1, len(data)):
        if data[i] == data[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    print(f"  최대 연속 반복: {max_run} bytes")
    if max_run > 10:
        print(f"    → RLE 압축 가능성 낮음 (이미 압축 해제됨)")
    else:
        print(f"    → 데이터가 다양함")

def main():
    """모든 스프라이트 분석"""
    sprites_dir = Path("output/assets/raw_sprites")

    for sprite_file in sorted(sprites_dir.glob("*.dat")):
        analyze_sprite(sprite_file)

if __name__ == "__main__":
    main()
