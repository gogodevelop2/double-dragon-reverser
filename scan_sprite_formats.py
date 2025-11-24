#!/usr/bin/env python3
"""
.dat 파일을 여러 DOS 그래픽 포맷으로 디코딩 시도
오프셋을 스캔하며 이미지를 찾아냄
"""

import os
from pathlib import Path
from PIL import Image
import struct

# CGA 4-color 팔레트 (Mode 4, Palette 1 - Cyan/Magenta/White)
CGA_PALETTE_1 = [
    (0, 0, 0),        # 0: Black
    (0, 255, 255),    # 1: Cyan
    (255, 0, 255),    # 2: Magenta
    (255, 255, 255)   # 3: White
]

# CGA 4-color 팔레트 (Mode 4, Palette 0 - Green/Red/Yellow)
CGA_PALETTE_0 = [
    (0, 0, 0),        # 0: Black
    (0, 255, 0),      # 1: Green
    (255, 0, 0),      # 2: Red
    (255, 255, 0)     # 3: Yellow
]

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
    (255, 85, 255),   # 13: Light Magenta
    (255, 255, 85),   # 14: Yellow
    (255, 255, 255)   # 15: White
]


def decode_cga_mode4(data, width, height, palette=CGA_PALETTE_1):
    """
    CGA Mode 4 디코딩 (2bpp, 4-color)
    각 바이트 = 4픽셀 (2bits per pixel)
    """
    pixels = []
    bytes_per_row = width // 4

    for y in range(height):
        for x in range(0, width, 4):
            byte_offset = y * bytes_per_row + x // 4
            if byte_offset >= len(data):
                pixels.extend([0, 0, 0, 0])
                continue

            byte_val = data[byte_offset]
            # 4픽셀 추출 (MSB first)
            for shift in [6, 4, 2, 0]:
                color_idx = (byte_val >> shift) & 0x03
                pixels.append(color_idx)

    # PIL 이미지 생성
    img = Image.new('RGB', (width, height))
    img_data = []
    for pixel in pixels:
        img_data.append(palette[pixel % len(palette)])
    img.putdata(img_data)
    return img


def decode_cga_planar(data, width, height, palette=CGA_PALETTE_1):
    """
    CGA Planar 디코딩 (4 planes)
    각 평면 = 1bpp
    """
    pixels = [0] * (width * height)
    bytes_per_plane = (width * height) // 8

    # 4개 평면 처리
    for plane in range(min(4, len(data) * 8 // (width * height))):
        plane_offset = plane * bytes_per_plane

        for y in range(height):
            for x in range(0, width, 8):
                byte_offset = plane_offset + y * (width // 8) + x // 8
                if byte_offset >= len(data):
                    continue

                byte_val = data[byte_offset]
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if (byte_val >> (7 - bit)) & 1:
                            pixels[pixel_idx] |= (1 << plane)

    # PIL 이미지 생성
    img = Image.new('RGB', (width, height))
    img_data = [palette[p % len(palette)] for p in pixels]
    img.putdata(img_data)
    return img


def decode_16plane_interleaved(data, width, height):
    """
    16-plane interleaved 디코딩 (FUN_1000_0786 방식)
    각 평면 = 1bpp, 16개 평면 인터리브
    """
    pixels = [0] * (width * height)
    plane_size = (width * height) // 8

    # 16개 평면 처리
    for plane in range(16):
        plane_offset = plane * plane_size

        for y in range(height):
            for x in range(0, width, 8):
                byte_offset = plane_offset + y * (width // 8) + x // 8
                if byte_offset >= len(data):
                    continue

                byte_val = data[byte_offset]
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if (byte_val >> (7 - bit)) & 1:
                            pixels[pixel_idx] |= (1 << plane)

    # 16-color EGA 팔레트
    img = Image.new('RGB', (width, height))
    img_data = [EGA_PALETTE[p % 16] for p in pixels]
    img.putdata(img_data)
    return img


def decode_chunky_8bit(data, width, height):
    """
    Chunky 8-bit (1 byte per pixel)
    """
    pixels = []
    for y in range(height):
        for x in range(width):
            offset = y * width + x
            if offset >= len(data):
                pixels.append(0)
            else:
                pixels.append(data[offset])

    img = Image.new('RGB', (width, height))
    img_data = [EGA_PALETTE[p % 16] for p in pixels]
    img.putdata(img_data)
    return img


def scan_file(filepath, output_dir):
    """
    파일을 스캔하며 여러 포맷 시도
    """
    print(f"\n=== {filepath.name} ===")
    print(f"크기: {filepath.stat().st_size} bytes")

    with open(filepath, 'rb') as f:
        data = f.read()

    file_stem = filepath.stem
    output_subdir = output_dir / file_stem
    output_subdir.mkdir(parents=True, exist_ok=True)

    # 시도할 크기들 (width, height)
    # 16x16, 16x24, 16x32
    sizes = [(16, 16), (16, 24), (16, 32)]

    # 시도할 포맷들
    formats = [
        ("cga_mode4_pal1", lambda d, w, h: decode_cga_mode4(d, w, h, CGA_PALETTE_1)),
        ("cga_mode4_pal0", lambda d, w, h: decode_cga_mode4(d, w, h, CGA_PALETTE_0)),
        ("cga_planar_pal1", lambda d, w, h: decode_cga_planar(d, w, h, CGA_PALETTE_1)),
        ("cga_planar_pal0", lambda d, w, h: decode_cga_planar(d, w, h, CGA_PALETTE_0)),
        ("16plane_interleaved", decode_16plane_interleaved),
        ("chunky_8bit", decode_chunky_8bit),
    ]

    results = []

    for width, height in sizes:
        bytes_needed_cga = (width * height) // 4  # 2bpp
        bytes_needed_planar = (width * height) // 2  # 4 planes × 1bpp
        bytes_needed_16plane = (width * height) * 2  # 16 planes × 1bpp
        bytes_needed_chunky = width * height  # 8bpp

        # 오프셋 스캔 (전체 파일, 1바이트씩)
        max_offset = len(data) // 2  # 파일의 절반까지

        for offset in range(0, max_offset, 1):  # 1바이트씩 스캔
            remaining = len(data) - offset

            for format_name, decode_func in formats:
                # 필요한 바이트 수 계산
                if "cga_mode4" in format_name:
                    bytes_needed = bytes_needed_cga
                elif "cga_planar" in format_name:
                    bytes_needed = bytes_needed_planar
                elif "16plane" in format_name:
                    bytes_needed = bytes_needed_16plane
                elif "chunky" in format_name:
                    bytes_needed = bytes_needed_chunky
                else:
                    bytes_needed = remaining

                if remaining < bytes_needed:
                    continue

                try:
                    chunk = data[offset:offset + bytes_needed]
                    img = decode_func(chunk, width, height)

                    # 파일명 생성
                    filename = f"{file_stem}_off{offset:04x}_{width}x{height}_{format_name}.png"
                    output_path = output_subdir / filename
                    img.save(output_path)

                    results.append({
                        'offset': offset,
                        'size': (width, height),
                        'format': format_name,
                        'file': filename
                    })
                except Exception as e:
                    # 디코딩 실패 시 무시
                    pass

    print(f"생성된 이미지: {len(results)}개")

    # 결과 요약 저장
    summary_path = output_subdir / f"{file_stem}_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(f"파일: {filepath.name}\n")
        f.write(f"크기: {len(data)} bytes\n")
        f.write(f"생성된 이미지: {len(results)}개\n\n")

        for r in results:
            f.write(f"- {r['file']}\n")
            f.write(f"  오프셋: 0x{r['offset']:04x}\n")
            f.write(f"  크기: {r['size'][0]}x{r['size'][1]}\n")
            f.write(f"  포맷: {r['format']}\n\n")

    return results


def main():
    raw_sprites_dir = Path("output/assets/raw_sprites")
    output_dir = Path("output/sprites_scan")
    output_dir.mkdir(parents=True, exist_ok=True)

    dat_files = sorted(raw_sprites_dir.glob("*.dat"))

    if not dat_files:
        print("❌ .dat 파일을 찾을 수 없습니다.")
        return

    print(f"발견한 .dat 파일: {len(dat_files)}개")

    total_images = 0

    for dat_file in dat_files:
        results = scan_file(dat_file, output_dir)
        total_images += len(results)

    print(f"\n✅ 완료!")
    print(f"총 생성된 이미지: {total_images}개")
    print(f"출력 디렉토리: {output_dir}")
    print("\n각 파일의 summary.txt에서 상세 정보를 확인하세요.")


if __name__ == "__main__":
    main()
