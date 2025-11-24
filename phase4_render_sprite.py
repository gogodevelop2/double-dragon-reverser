#!/usr/bin/env python3
"""
Phase 4: 스프라이트 렌더링 테스트

간단한 CGA 2bpp 렌더러로 스프라이트 구조 파악
"""

from pathlib import Path
from PIL import Image

# CGA 팔레트 (Palette 1: Cyan/Magenta/White)
CGA_PALETTE_1 = [
    (0, 0, 0),       # 0: Black
    (0, 255, 255),   # 1: Cyan
    (255, 0, 255),   # 2: Magenta
    (255, 255, 255)  # 3: White
]

# CGA 팔레트 (Palette 0: Green/Red/Brown)
CGA_PALETTE_0 = [
    (0, 0, 0),       # 0: Black
    (0, 255, 0),     # 1: Green
    (255, 0, 0),     # 2: Red
    (170, 85, 0)     # 3: Brown/Yellow
]

def render_sprite_simple(data, width=40, palette=CGA_PALETTE_1):
    """
    간단한 2bpp 렌더링

    Args:
        data: 픽셀 데이터
        width: 폭 (픽셀 수)
        palette: 4색 팔레트
    """
    pixels = []

    for byte in data:
        # 2 bits per pixel, 4 pixels per byte
        # MSB first
        for shift in [6, 4, 2, 0]:
            color_index = (byte >> shift) & 0x03
            pixels.append(palette[color_index])

    # 이미지 크기 계산
    total_pixels = len(pixels)
    height = total_pixels // width

    if height == 0:
        return None

    # PIL 이미지 생성
    img = Image.new('RGB', (width, height))
    img.putdata(pixels[:width * height])

    return img

def analyze_and_render(sprite_file, output_dir):
    """스프라이트 분석 및 렌더링"""
    with open(sprite_file, 'rb') as f:
        data = f.read()

    print(f"\n{'='*70}")
    print(f"파일: {sprite_file.name}")
    print(f"크기: {len(data)} bytes")

    # 첫 바이트가 0xC8 (200)이면 스캔라인 개수
    if data[0] == 0xC8:
        print(f"  → 스캔라인 기반 포맷 감지 (200 lines)")
        # 헤더 스킵하고 렌더링
        pixel_data = data[3:]  # 처음 3바이트 스킵
    else:
        print(f"  → 일반 포맷")
        pixel_data = data

    # 여러 폭으로 시도
    widths = [32, 40, 48, 64, 80, 96, 128, 160]

    for width in widths:
        try:
            # 팔레트 1로 렌더링
            img1 = render_sprite_simple(pixel_data, width, CGA_PALETTE_1)
            if img1:
                output_file = output_dir / f"{sprite_file.stem}_w{width}_pal1.png"
                img1.save(output_file)
                print(f"  ✓ 생성: {width}px 폭, 팔레트1 → {img1.height}px 높이")

            # 팔레트 0로도 렌더링
            img0 = render_sprite_simple(pixel_data, width, CGA_PALETTE_0)
            if img0:
                output_file = output_dir / f"{sprite_file.stem}_w{width}_pal0.png"
                img0.save(output_file)

        except Exception as e:
            pass

    print(f"{'='*70}")

def main():
    """모든 스프라이트 렌더링"""
    sprites_dir = Path("output/assets/raw_sprites")
    output_dir = Path("output/assets/rendered_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("스프라이트 렌더링 테스트\n")
    print("여러 폭과 팔레트로 시도하여 올바른 조합 찾기...\n")

    # 작은 파일부터 테스트
    test_files = [
        "LINDA.dat",      # 237 bytes (가장 작음)
        "ABOBO.dat",      # 508 bytes
        "PLAYER1.dat"     # 2711 bytes (가장 큼)
    ]

    for filename in test_files:
        sprite_file = sprites_dir / filename
        if sprite_file.exists():
            analyze_and_render(sprite_file, output_dir)

    print(f"\n결과 파일: {output_dir}/")
    print("PNG 파일들을 열어서 올바른 폭/팔레트 조합을 확인하세요.")

if __name__ == "__main__":
    main()
