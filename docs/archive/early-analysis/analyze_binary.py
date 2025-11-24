#!/usr/bin/env python3
"""
Double Dragon DOS 바이너리 파일 분석 도구
"""

import struct
import sys
from pathlib import Path

def analyze_header(filepath):
    """파일 헤더 분석"""
    with open(filepath, 'rb') as f:
        # 첫 128 바이트 읽기
        header = f.read(128)

        print(f"\n=== {filepath.name} 분석 ===")
        print(f"파일 크기: {filepath.stat().st_size} bytes")

        # 첫 16 바이트 헥스 덤프
        print("\n첫 16 바이트:")
        for i in range(0, min(16, len(header)), 8):
            hex_str = ' '.join(f'{b:02x}' for b in header[i:i+8])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in header[i:i+8])
            print(f"  {i:04x}: {hex_str:23s} {ascii_str}")

        # 시그니처 확인
        if header[0:2] == b'\x1f\x9d':
            print("\n시그니처: LZW 압축 (Unix compress)")
            print(f"압축 비트: {header[2]}")
        elif header[0:2] == b'MZ' or header[0:2] == b'ZM':
            print("\n시그니처: DOS EXE 실행 파일")
        else:
            print(f"\n시그니처: 알 수 없음 ({header[0]:02x} {header[1]:02x})")

        # 바이트 분포 분석
        f.seek(0)
        data = f.read()
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1

        # 가장 많이 사용된 바이트 top 10
        print("\n가장 많이 사용된 바이트 (Top 10):")
        sorted_bytes = sorted(enumerate(byte_counts), key=lambda x: x[1], reverse=True)
        for i, (byte_val, count) in enumerate(sorted_bytes[:10]):
            pct = count * 100.0 / len(data)
            char = chr(byte_val) if 32 <= byte_val < 127 else '.'
            print(f"  {i+1}. 0x{byte_val:02x} ({char}): {count:5d} ({pct:5.2f}%)")

        # 엔트로피 추정 (압축률 판단)
        import math
        entropy = 0
        for count in byte_counts:
            if count > 0:
                p = count / len(data)
                entropy -= p * math.log2(p)
        print(f"\n엔트로피: {entropy:.2f} bits/byte (8.0이 최대 무작위)")

        return header

def find_patterns(filepath, pattern_size=4):
    """반복 패턴 찾기"""
    with open(filepath, 'rb') as f:
        data = f.read()

    patterns = {}
    for i in range(len(data) - pattern_size):
        pattern = data[i:i+pattern_size]
        if pattern in patterns:
            patterns[pattern].append(i)
        else:
            patterns[pattern] = [i]

    # 3번 이상 반복되는 패턴만 출력
    repeated = {p: positions for p, positions in patterns.items() if len(positions) >= 3}

    if repeated:
        print(f"\n반복 패턴 (최소 3회, {pattern_size} 바이트):")
        sorted_patterns = sorted(repeated.items(), key=lambda x: len(x[1]), reverse=True)
        for pattern, positions in sorted_patterns[:5]:
            hex_str = ' '.join(f'{b:02x}' for b in pattern)
            print(f"  {hex_str}: {len(positions)}회 (위치: {positions[:5]}...)")

def analyze_structure(filepath):
    """파일 구조 추정"""
    with open(filepath, 'rb') as f:
        data = f.read()

    # 0x00이 연속으로 나타나는 구간 찾기 (패딩/구분자일 가능성)
    zero_runs = []
    run_start = None
    run_length = 0

    for i, byte in enumerate(data):
        if byte == 0:
            if run_start is None:
                run_start = i
            run_length += 1
        else:
            if run_length >= 4:  # 4바이트 이상 연속 0
                zero_runs.append((run_start, run_length))
            run_start = None
            run_length = 0

    if zero_runs:
        print(f"\n연속된 0x00 구간 (4바이트 이상):")
        for start, length in zero_runs[:10]:
            print(f"  위치 0x{start:04x}: {length} 바이트")

if __name__ == '__main__':
    # 레퍼런스 파일 경로
    ref_path = Path(__file__).parent.parent / 'reference' / 'dos-original'

    # 분석할 파일들
    files_to_analyze = [
        'PLAYER1.EG1',  # 플레이어 스프라이트
        'ABOBO.EG1',    # 보스 스프라이트
        'LEVEL11.PC1',  # 레벨 데이터
        'LDSCRN.CGA',   # 로딩 화면
        'CHARSET.BIN',  # 문자 세트
    ]

    for filename in files_to_analyze:
        filepath = ref_path / filename
        if filepath.exists():
            analyze_header(filepath)
            find_patterns(filepath)
            analyze_structure(filepath)
            print("\n" + "="*60)
        else:
            print(f"파일 없음: {filepath}")
