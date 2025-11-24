#!/usr/bin/env python3
"""
LINDA 스프라이트 렌더링 (비트 재배열 적용 후)
FUN_1000_0cd1 변환 후 데이터를 PNG로 렌더링
"""

from PIL import Image
import sys

# CGA Palette 1 (Cyan/Magenta/White)
CGA_PALETTE_1 = [
    (0, 0, 0),       # 0: Black
    (0, 170, 170),   # 1: Cyan
    (170, 0, 170),   # 2: Magenta
    (170, 170, 170), # 3: White (light gray)
    (0, 0, 0),       # 4: Black
    (0, 255, 255),   # 5: Bright Cyan
    (255, 0, 255),   # 6: Bright Magenta
    (255, 255, 255), # 7: Bright White
    (85, 85, 85),    # 8: Dark Gray
    (85, 255, 255),  # 9: Light Cyan
    (255, 85, 255),  # A: Light Magenta
    (255, 255, 255), # B: White
    (85, 85, 85),    # C: Dark Gray
    (85, 255, 255),  # D: Light Cyan
    (255, 85, 255),  # E: Light Magenta
    (255, 255, 255), # F: White
]

# CGA Palette 0 (Green/Red/Brown)
CGA_PALETTE_0 = [
    (0, 0, 0),       # 0: Black
    (0, 170, 0),     # 1: Green
    (170, 0, 0),     # 2: Red
    (170, 85, 0),    # 3: Brown/Yellow
    (0, 0, 0),       # 4: Black
    (0, 255, 0),     # 5: Bright Green
    (255, 0, 0),     # 6: Bright Red
    (255, 255, 0),   # 7: Bright Yellow
    (85, 85, 85),    # 8: Dark Gray
    (85, 255, 85),   # 9: Light Green
    (255, 85, 85),   # A: Light Red
    (255, 255, 85),  # B: Light Yellow
    (85, 85, 85),    # C: Dark Gray
    (85, 255, 85),   # D: Light Green
    (255, 85, 85),   # E: Light Red
    (255, 255, 85),  # F: Light Yellow
]

def render_sprite(data, width, palette=CGA_PALETTE_1):
    """
    4-bit CGA 데이터를 PNG로 렌더링
    각 바이트 = 2픽셀 (4-bit per pixel)
    """
    pixels = []

    for byte in data:
        # 상위 4비트 = 첫 번째 픽셀
        pixel0 = (byte >> 4) & 0x0F
        pixels.append(palette[pixel0])

        # 하위 4비트 = 두 번째 픽셀
        pixel1 = byte & 0x0F
        pixels.append(palette[pixel1])

    total_pixels = len(pixels)
    height = total_pixels // width

    if total_pixels % width != 0:
        # 패딩 추가
        padding = width - (total_pixels % width)
        pixels.extend([(0, 0, 0)] * padding)
        height += 1

    img = Image.new('RGB', (width, height))
    img.putdata(pixels[:width * height])

    return img

def main():
    input_file = 'output/assets/processed/LINDA_processed.dat'

    print("=== LINDA 스프라이트 렌더링 (변환 후) ===\n")

    # 파일 읽기
    with open(input_file, 'rb') as f:
        data = f.read()

    print(f"입력 파일: {input_file}")
    print(f"파일 크기: {len(data)} bytes")
    print(f"총 픽셀 수: {len(data) * 2} pixels (4-bit per pixel)\n")

    # 다양한 폭으로 렌더링
    widths = [16, 20, 24, 32, 40, 48, 64]
    palettes = [
        ('pal1', CGA_PALETTE_1),
        ('pal0', CGA_PALETTE_0)
    ]

    for pal_name, palette in palettes:
        for width in widths:
            img = render_sprite(data, width, palette)
            output_file = f'output/assets/processed/LINDA_v2_w{width}_{pal_name}.png'
            img.save(output_file)
            print(f"저장: {output_file} ({width}x{img.height})")

    print("\n완료! 14개 PNG 생성 (7 widths × 2 palettes)")
    print("\n추천: output/assets/processed/LINDA_v2_w*.png 파일들을 확인해보세요.")

if __name__ == '__main__':
    main()
