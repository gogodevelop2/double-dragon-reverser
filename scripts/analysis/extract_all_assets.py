#!/usr/bin/env python3
"""
모든 게임 에셋 추출

LZW 압축 해제 프로그램을 사용하여 모든 .EG1, .PC1 파일 추출
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

# 디렉토리
GAME_DIR = Path("reference/dos-original")
OUTPUT_DIR = Path("output/assets")
SPRITES_DIR = OUTPUT_DIR / "raw_sprites"
LEVELS_DIR = OUTPUT_DIR / "raw_levels"

# LZW 압축 해제 프로그램
DECOMPRESSOR = "./dd_lzw_decompress"

def extract_file(input_file, output_file):
    """파일 압축 해제"""
    try:
        result = subprocess.run(
            [DECOMPRESSOR, str(input_file), str(output_file)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            # 마지막 줄에서 크기 추출
            for line in result.stdout.split('\n'):
                if 'SUCCESS' in line:
                    size = int(line.split('(')[1].split()[0])
                    return size
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None

def main():
    print("=" * 70)
    print("게임 에셋 추출")
    print("=" * 70)

    # 디렉토리 생성
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    LEVELS_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "sprites": {},
        "levels": {},
        "total_extracted": 0,
        "total_size": 0
    }

    # EG1 파일 (스프라이트)
    print("\n📦 스프라이트 파일 (.EG1) 추출:")
    eg1_files = sorted(GAME_DIR.glob("*.EG1"))

    for eg1_file in eg1_files:
        name = eg1_file.stem
        output_file = SPRITES_DIR / f"{name}.dat"

        print(f"\n  {name:15s} ", end="", flush=True)

        size = extract_file(eg1_file, output_file)
        if size:
            print(f"✅ {size:,} bytes")
            results["sprites"][name] = size
            results["total_extracted"] += 1
            results["total_size"] += size
        else:
            print("❌ FAILED")

    # PC1 파일 (레벨/배경)
    print("\n\n🗺️  레벨 파일 (.PC1) 추출:")
    pc1_files = sorted(GAME_DIR.glob("*.PC1"))

    for pc1_file in pc1_files:
        name = pc1_file.stem
        output_file = LEVELS_DIR / f"{name}.dat"

        print(f"\n  {name:15s} ", end="", flush=True)

        size = extract_file(pc1_file, output_file)
        if size:
            print(f"✅ {size:,} bytes")
            results["levels"][name] = size
            results["total_extracted"] += 1
            results["total_size"] += size
        else:
            print("❌ FAILED")

    # 요약
    print("\n" + "=" * 70)
    print("추출 요약")
    print("=" * 70)
    print(f"스프라이트 (.EG1): {len(results['sprites'])}개 파일")
    print(f"레벨 (.PC1):       {len(results['levels'])}개 파일")
    print(f"\n총 {results['total_extracted']}개 파일, {results['total_size']:,} bytes ({results['total_size']/1024:.1f} KB)")

    # 체크포인트 저장
    checkpoint = {
        "phase": 3,
        "timestamp": datetime.now().isoformat(),
        "status": "lzw_extraction_completed",
        "results": results
    }

    checkpoint_file = Path("output/checkpoints/phase3_lzw.json")
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    print(f"\n💾 체크포인트 저장: {checkpoint_file}")

if __name__ == "__main__":
    main()
