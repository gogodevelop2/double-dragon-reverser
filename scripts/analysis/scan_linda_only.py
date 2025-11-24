#!/usr/bin/env python3
"""
LINDA.dat만 정밀 스캔
"""

import os
from pathlib import Path
from PIL import Image

# CGA 4-color 팔레트
CGA_PALETTE_1 = [
    (0, 0, 0),        # 0: Black
    (0, 255, 255),    # 1: Cyan
    (255, 0, 255),    # 2: Magenta
    (255, 255, 255)   # 3: White
]

def decode_cga_mode4(data, width, height, palette=CGA_PALETTE_1):
    """CGA Mode 4 디코딩"""
    pixels = []
    bytes_per_row = width // 4

    for y in range(height):
        for x in range(0, width, 4):
            byte_offset = y * bytes_per_row + x // 4
            if byte_offset >= len(data):
                pixels.extend([0, 0, 0, 0])
                continue

            byte_val = data[byte_offset]
            for shift in [6, 4, 2, 0]:
                color_idx = (byte_val >> shift) & 0x03
                pixels.append(color_idx)

    img = Image.new('RGB', (width, height))
    img_data = [palette[p % len(palette)] for p in pixels]
    img.putdata(img_data)
    return img

def main():
    filepath = Path("output/assets/raw_sprites/LINDA.dat")
    output_dir = Path("output/linda_scan")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"LINDA.dat 크기: {filepath.stat().st_size} bytes")

    with open(filepath, 'rb') as f:
        data = f.read()

    # 시도할 크기
    sizes = [(16, 16), (16, 24), (16, 32)]

    count = 0
    # 1바이트씩 스캔
    for offset in range(0, len(data) // 2):
        for width, height in sizes:
            bytes_needed = (width * height) // 4  # 2bpp

            if offset + bytes_needed > len(data):
                continue

            try:
                chunk = data[offset:offset + bytes_needed]
                img = decode_cga_mode4(chunk, width, height)

                filename = f"LINDA_off{offset:04x}_{width}x{height}.png"
                output_path = output_dir / filename
                img.save(output_path)
                count += 1

                if count % 100 == 0:
                    print(f"  생성: {count}개...")

            except Exception as e:
                pass

    print(f"✅ 완료! 총 {count}개 이미지 생성")
    print(f"출력: {output_dir}")

if __name__ == "__main__":
    main()
