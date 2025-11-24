#!/usr/bin/env python3
"""
DOSBox-X 메모리 덤프 분석 도구

사용법:
  python analyze_memdump.py <dump_file>
"""

import sys
from pathlib import Path
import struct

def find_compressed_files(data):
    """1F 9D 시그니처 찾기"""
    positions = []
    for i in range(len(data) - 2):
        if data[i] == 0x1F and data[i+1] == 0x9D:
            positions.append(i)
    return positions

def find_graphics_data(data, min_size=1000):
    """그래픽 데이터 패턴 찾기"""
    candidates = []

    for i in range(0, len(data) - min_size, 256):
        chunk = data[i:i+min_size]

        # 빈 메모리 제외
        if chunk.count(0x00) > len(chunk) * 0.9:
            continue
        if chunk.count(0xFF) > len(chunk) * 0.9:
            continue

        # 적당한 다양성 (그래픽은 반복 패턴 있음)
        unique = len(set(chunk))
        if 10 < unique < 200:
            candidates.append({
                'offset': i,
                'size': len(chunk),
                'unique_bytes': unique,
                'entropy': calculate_entropy(chunk)
            })

    return candidates

def calculate_entropy(data):
    """엔트로피 계산 (0-8)"""
    if len(data) == 0:
        return 0

    import math
    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1

    entropy = 0
    for count in byte_counts:
        if count > 0:
            p = count / len(data)
            entropy -= p * math.log2(p)

    return entropy

def analyze_dump(dump_path):
    """메모리 덤프 분석"""
    print(f"\n{'='*60}")
    print(f"메모리 덤프 분석: {dump_path.name}")
    print('='*60)

    with open(dump_path, 'rb') as f:
        data = f.read()

    print(f"\n파일 크기: {len(data):,} bytes ({len(data)//1024}KB)")

    # 압축 파일 시그니처 찾기
    print("\n[1] 압축 파일 시그니처 (0x1F 0x9D) 검색...")
    compressed = find_compressed_files(data)
    print(f"  발견: {len(compressed)}개")
    if compressed:
        for i, pos in enumerate(compressed[:10]):
            print(f"    {i+1}. 오프셋 0x{pos:08x}")
            # 주변 바이트 보기
            context = data[pos:pos+16]
            hex_str = ' '.join(f'{b:02x}' for b in context)
            print(f"       {hex_str}")

    # 그래픽 데이터 찾기
    print("\n[2] 그래픽 데이터 패턴 검색...")
    graphics = find_graphics_data(data)
    print(f"  후보: {len(graphics)}개")
    if graphics:
        # 엔트로피 기준 정렬
        graphics.sort(key=lambda x: abs(x['entropy'] - 5.5))
        for i, g in enumerate(graphics[:10]):
            print(f"    {i+1}. 오프셋 0x{g['offset']:08x}, "
                  f"고유 바이트: {g['unique_bytes']}, "
                  f"엔트로피: {g['entropy']:.2f}")

    # 통계
    print("\n[3] 바이트 분포 (Top 10):")
    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1

    sorted_bytes = sorted(enumerate(byte_counts), key=lambda x: x[1], reverse=True)
    for i, (byte_val, count) in enumerate(sorted_bytes[:10]):
        pct = count * 100.0 / len(data)
        char = chr(byte_val) if 32 <= byte_val < 127 else '.'
        print(f"    {i+1}. 0x{byte_val:02x} ({char}): {count:6d} ({pct:5.2f}%)")

    # 첫 256바이트 덤프
    print("\n[4] 첫 256 바이트:")
    for i in range(0, min(256, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04x}: {hex_str:47s} {ascii_str}")

    print("\n" + "="*60)

def extract_region(dump_path, offset, size, output_path):
    """특정 영역 추출"""
    with open(dump_path, 'rb') as f:
        f.seek(offset)
        data = f.read(size)

    with open(output_path, 'wb') as f:
        f.write(data)

    print(f"추출 완료: {output_path}")
    print(f"  오프셋: 0x{offset:08x}")
    print(f"  크기: {size} bytes")

def main():
    if len(sys.argv) < 2:
        print("사용법: python analyze_memdump.py <dump_file> [offset] [size] [output]")
        print("\n예제:")
        print("  python analyze_memdump.py memory.bin")
        print("  python analyze_memdump.py memory.bin 0x1000 0x4000 output.bin")
        return

    dump_path = Path(sys.argv[1])

    if not dump_path.exists():
        print(f"파일 없음: {dump_path}")
        return

    if len(sys.argv) == 5:
        # 추출 모드
        offset = int(sys.argv[2], 16 if sys.argv[2].startswith('0x') else 10)
        size = int(sys.argv[3], 16 if sys.argv[3].startswith('0x') else 10)
        output = Path(sys.argv[4])
        extract_region(dump_path, offset, size, output)
    else:
        # 분석 모드
        analyze_dump(dump_path)

if __name__ == '__main__':
    main()
