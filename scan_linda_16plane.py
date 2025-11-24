#!/usr/bin/env python3
"""
LINDA.dat을 16-plane interleaved로 디코딩
"""

from pathlib import Path
from PIL import Image

# EGA 16-color 팔레트
EGA_PALETTE = [
    (0, 0, 0),        # 0: Black
    (0, 0, 170),      # 1: Blue
    (0, 170, 0),      # 2: Green
    (0, 170, 170),    # 3: Cyan
    (170, 0, 0),      # 4: Red
    (170, 0, 170),    # 5: Magenta
    (170, 85, 0),     # 6: Brown
    (170, 170, 170),  # 7: Light Gray
    (85, 85, 85),     # 8: Dark Gray
    (85, 85, 255),    # 9: Light Blue
    (85, 255, 85),    # 10: Light Green
    (85, 255, 255),   # 11: Light Cyan
    (255, 85, 85),    # 12: Light Red
    (255, 85, 255),   # 13: Light Magenta (핑크)
    (255, 255, 85),   # 14: Yellow
    (255, 255, 255)   # 15: White
]

def decode_4plane(data, width, height):
    """
    4-plane 디코딩 (각 평면 = 1bpp)
    CGA/EGA 표준 방식
    """
    pixels = [0] * (width * height)
    plane_size = (width * height) // 8  # bits to bytes

    for plane in range(4):
        plane_offset = plane * plane_size

        for y in range(height):
            for x in range(0, width, 8):
                byte_offset = plane_offset + y * (width // 8) + (x // 8)
                if byte_offset >= len(data):
                    continue

                byte_val = data[byte_offset]
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if (byte_val >> (7 - bit)) & 1:
                            pixels[pixel_idx] |= (1 << plane)

    # 4-bit 색상 (16 colors)
    img = Image.new('RGB', (width, height))
    img_data = [EGA_PALETTE[p % 16] for p in pixels]
    img.putdata(img_data)
    return img

def main():
    filepath = Path("output/assets/raw_sprites/LINDA.dat")
    output_dir = Path("output/linda_4plane")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"LINDA.dat 크기: {filepath.stat().st_size} bytes")

    with open(filepath, 'rb') as f:
        data = f.read()

    width, height = 16, 24
    bytes_needed = (width * height) // 2  # 4 planes × 1bpp

    count = 0
    # 1바이트씩 스캔
    for offset in range(0, len(data) - bytes_needed):
        try:
            chunk = data[offset:offset + bytes_needed]
            img = decode_4plane(chunk, width, height)

            filename = f"LINDA_4plane_off{offset:04x}_16x24.png"
            output_path = output_dir / filename
            img.save(output_path)
            count += 1

            if count % 50 == 0:
                print(f"  생성: {count}개...")

        except Exception as e:
            pass

    print(f"✅ 완료! 총 {count}개 이미지 생성")
    print(f"출력: {output_dir}")

if __name__ == "__main__":
    main()
