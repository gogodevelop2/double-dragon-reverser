#!/usr/bin/env python3
"""
Phase 3: 게임 에셋 추출

.EG1, .PC1 파일에서 스프라이트 및 레벨 데이터 추출
Unix compress (LZW) 형식 압축 해제
"""

import struct
import sys
from pathlib import Path
from datetime import datetime

# 디렉토리
GAME_DIR = Path("reference/dos-original")
OUTPUT_DIR = Path("output/assets")
SPRITES_DIR = OUTPUT_DIR / "sprites"
LEVELS_DIR = OUTPUT_DIR / "levels"

def decompress_lzw(data):
    """
    Unix compress 형식 LZW 압축 해제

    파일 포맷:
    - 매직 넘버: 0x1F 0x9D
    - 최대 비트: 3번째 바이트
    """

    if len(data) < 3:
        raise ValueError("File too small")

    # 헤더 확인
    if data[0] != 0x1F or data[1] != 0x9D:
        raise ValueError(f"Invalid LZW header: {data[0]:02x} {data[1]:02x}")

    max_bits = data[2] & 0x1F
    block_mode = (data[2] & 0x80) != 0

    print(f"  LZW 설정: max_bits={max_bits}, block_mode={block_mode}")

    # Python의 내장 압축 해제 사용
    # Unix compress는 표준이므로 uncompress 명령 사용
    return None  # uncompress 명령으로 처리

def extract_with_uncompress(input_file, output_file):
    """Unix uncompress 명령 사용"""
    import subprocess

    # .Z 확장자가 필요함
    temp_z = input_file.with_suffix(input_file.suffix + '.Z')

    # 복사
    import shutil
    shutil.copy(input_file, temp_z)

    try:
        # uncompress 실행
        result = subprocess.run(
            ['uncompress', '-c', str(temp_z)],
            capture_output=True,
            check=False
        )

        if result.returncode == 0:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'wb') as f:
                f.write(result.stdout)
            return True
        else:
            print(f"    ⚠️ uncompress 실패: {result.stderr.decode()[:50]}")
            return False
    finally:
        # 임시 파일 삭제
        if temp_z.exists():
            temp_z.unlink()

def analyze_file_header(data):
    """압축 해제된 파일 헤더 분석"""

    if len(data) < 16:
        return {"type": "unknown", "size": len(data)}

    # 처음 16바이트 출력
    header = data[:16]
    hex_str = ' '.join(f'{b:02x}' for b in header)

    info = {
        "type": "data",
        "size": len(data),
        "header_hex": hex_str
    }

    # 패턴 감지
    if all(b == 0 for b in header[:8]):
        info["type"] = "zero_padded"
    elif max(header) < 16:
        info["type"] = "palette_or_metadata"

    return info

def extract_all_assets():
    """모든 에셋 추출"""

    print("\n" + "=" * 70)
    print("Phase 3: 게임 에셋 추출")
    print("=" * 70)

    # 출력 디렉토리 생성
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    LEVELS_DIR.mkdir(parents=True, exist_ok=True)

    # EG1 파일 (스프라이트)
    print("\n📦 스프라이트 파일 (.EG1) 추출:")
    eg1_files = sorted(GAME_DIR.glob("*.EG1"))

    eg1_success = 0
    for eg1_file in eg1_files:
        print(f"\n처리 중: {eg1_file.name}")

        output_file = SPRITES_DIR / f"{eg1_file.stem}.dat"

        if extract_with_uncompress(eg1_file, output_file):
            # 헤더 분석
            with open(output_file, 'rb') as f:
                data = f.read()

            info = analyze_file_header(data)
            print(f"  ✅ 추출 성공: {len(data):,} bytes")
            print(f"     타입: {info['type']}")
            print(f"     헤더: {info['header_hex']}")
            eg1_success += 1
        else:
            print(f"  ❌ 추출 실패")

    # PC1 파일 (레벨/배경)
    print("\n\n🗺️ 레벨 파일 (.PC1) 추출:")
    pc1_files = sorted(GAME_DIR.glob("*.PC1"))

    pc1_success = 0
    for pc1_file in pc1_files:
        print(f"\n처리 중: {pc1_file.name}")

        output_file = LEVELS_DIR / f"{pc1_file.stem}.dat"

        if extract_with_uncompress(pc1_file, output_file):
            with open(output_file, 'rb') as f:
                data = f.read()

            info = analyze_file_header(data)
            print(f"  ✅ 추출 성공: {len(data):,} bytes")
            print(f"     타입: {info['type']}")
            print(f"     헤더: {info['header_hex']}")
            pc1_success += 1
        else:
            print(f"  ❌ 추출 실패")

    # NW 파일 (문자/작은 스프라이트)
    print("\n\n🔤 문자 파일 (.NW*) 추출:")
    nw_files = sorted(GAME_DIR.glob("*.NW*"))[:5]  # 처음 5개만

    nw_success = 0
    for nw_file in nw_files:
        print(f"\n처리 중: {nw_file.name}")

        output_file = SPRITES_DIR / f"{nw_file.stem}_{nw_file.suffix[1:]}.dat"

        if extract_with_uncompress(nw_file, output_file):
            with open(output_file, 'rb') as f:
                data = f.read()

            print(f"  ✅ 추출 성공: {len(data):,} bytes")
            nw_success += 1

    # 요약
    print("\n" + "=" * 70)
    print("추출 요약")
    print("=" * 70)
    print(f"스프라이트 (.EG1): {eg1_success}/{len(eg1_files)}개 성공")
    print(f"레벨 (.PC1):       {pc1_success}/{len(pc1_files)}개 성공")
    print(f"문자 (.NW*):       {nw_success}/{min(5, len(nw_files))}개 성공 (샘플)")

    total_files = list(SPRITES_DIR.glob("*.dat")) + list(LEVELS_DIR.glob("*.dat"))
    total_size = sum(f.stat().st_size for f in total_files)

    print(f"\n총 추출: {len(total_files)}개 파일, {total_size:,} bytes ({total_size/1024:.1f} KB)")

    return {
        "sprites_success": eg1_success,
        "levels_success": pc1_success,
        "nw_success": nw_success,
        "total_files": len(total_files),
        "total_size": total_size
    }

def main():
    try:
        stats = extract_all_assets()

        # 체크포인트 저장
        checkpoint = {
            "phase": 3,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "stats": stats
        }

        import json
        checkpoint_file = Path("output/checkpoints/phase3.json")
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"\n💾 체크포인트 저장: {checkpoint_file}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
