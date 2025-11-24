#!/usr/bin/env python3
"""
Phase 4: 스프라이트 구조 상세 분석

스프라이트 파일의 정확한 구조를 파악하기 위한 심층 분석
"""

from pathlib import Path
import struct

def analyze_sprite_structure(file_path):
    """스프라이트 파일의 상세 구조 분석"""
    with open(file_path, 'rb') as f:
        data = f.read()

    print(f"\n{'='*70}")
    print(f"파일: {file_path.name}")
    print(f"전체 크기: {len(data)} bytes")
    print(f"{'='*70}")

    # 첫 32 bytes 헥스 덤프
    print("\n첫 32 bytes:")
    for i in range(min(32, len(data))):
        if i % 16 == 0:
            print(f"\n  {i:04x}:", end="")
        print(f" {data[i]:02x}", end="")
    print()

    # 가능한 헤더 필드 분석
    print("\n\n헤더 분석:")

    if len(data) >= 1:
        print(f"  [0] = 0x{data[0]:02x} ({data[0]:3d})")
        if data[0] == 0xC8:
            print(f"       → 스캔라인 개수: 200")
        elif data[0] == 0x3D:
            print(f"       → 폭 또는 프레임 개수: 61")

    if len(data) >= 2:
        print(f"  [1] = 0x{data[1]:02x} ({data[1]:3d})")

    if len(data) >= 3:
        print(f"  [2] = 0x{data[2]:02x} ({data[2]:3d})")

    # 2바이트 조합
    if len(data) >= 2:
        val16_le_0 = struct.unpack('<H', data[0:2])[0]
        val16_be_0 = struct.unpack('>H', data[0:2])[0]
        print(f"\n  [0-1] uint16 LE: {val16_le_0} (0x{val16_le_0:04x})")
        print(f"  [0-1] uint16 BE: {val16_be_0} (0x{val16_be_0:04x})")

    if len(data) >= 4:
        val16_le_2 = struct.unpack('<H', data[2:4])[0]
        print(f"  [2-3] uint16 LE: {val16_le_2} (0x{val16_le_2:04x})")

    # 바이트 분포 분석
    print("\n\n바이트 값 분포:")
    byte_counts = {}
    for b in data:
        byte_counts[b] = byte_counts.get(b, 0) + 1

    # 가장 많은 값들
    sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
    print("  상위 10개 값:")
    for val, count in sorted_bytes[:10]:
        percent = count / len(data) * 100
        print(f"    0x{val:02x} ({val:3d}): {count:4d}회 ({percent:5.2f}%)")

    # 0x00의 비율 (배경색/투명 가능성)
    zero_count = byte_counts.get(0, 0)
    zero_percent = zero_count / len(data) * 100
    print(f"\n  0x00 (투명/배경) 비율: {zero_percent:.2f}%")

    # 패턴 찾기 - 반복되는 시퀀스
    print("\n\n반복 패턴:")
    max_same_run = 0
    current_run = 1
    for i in range(1, len(data)):
        if data[i] == data[i-1]:
            current_run += 1
            max_same_run = max(max_same_run, current_run)
        else:
            current_run = 1
    print(f"  최대 동일 바이트 연속: {max_same_run}")

    # 가능한 픽셀 데이터 시작 위치 추정
    print("\n\n픽셀 데이터 시작 추정:")
    # 0xC8로 시작하면 헤더가 있을 가능성
    if data[0] == 0xC8:
        print(f"  → 0xC8 (200) 발견, 스캔라인 기반 포맷")
        print(f"  → 가능한 헤더 크기: 1, 2, 3 bytes")
        for header_size in [1, 2, 3, 4]:
            pixels_bytes = len(data) - header_size
            pixels_count = pixels_bytes * 4  # 2bpp
            print(f"     헤더 {header_size} bytes → 픽셀 데이터 {pixels_bytes} bytes → {pixels_count} pixels")
    else:
        print(f"  → 첫 바이트: 0x{data[0]:02x}")
        print(f"  → 헤더 없이 바로 픽셀 데이터일 가능성")

    # 가능한 폭 계산
    print("\n\n가능한 스프라이트 폭:")
    for header_size in [0, 1, 2, 3, 4]:
        pixel_bytes = len(data) - header_size
        pixel_count = pixel_bytes * 4  # 2bpp = 4 pixels per byte

        print(f"\n  헤더 {header_size} bytes일 때:")
        for width in [16, 20, 24, 32, 40, 48, 64]:
            if pixel_count % width == 0:
                height = pixel_count // width
                print(f"    {width}x{height} (총 {pixel_count} pixels)")

def main():
    """모든 스프라이트 상세 분석"""
    sprites_dir = Path("output/assets/raw_sprites")

    test_files = [
        "LINDA.dat",
        "ABOBO.dat",
        "PLAYER1.dat"
    ]

    for filename in test_files:
        sprite_file = sprites_dir / filename
        if sprite_file.exists():
            analyze_sprite_structure(sprite_file)

if __name__ == "__main__":
    main()
