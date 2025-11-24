#!/usr/bin/env python3
"""
미분석 함수 복구 스크립트

Spice86 호출 그래프에서 발견한 중요 함수들을
pyghidra로 디컴파일하는 스크립트
"""

import json
import os
from pathlib import Path

# 가장 많이 호출되는데 디컴파일 안 된 함수들
MISSING_FUNCTIONS = [
    0x293e,  # 29회 호출 - 가장 중요!
    0x3824,  # 8회
    0x3265,  # 6회
    0x3384,  # 6회
    0x2711,  # 6회
    0x28c0,  # 4회
    0x28ef,  # 4회
    0x3818,  # 4회
    0x1ea2,  # 디스패처 호출
    0x1dfc,  #  디스패처 호출
    0x1dff,  # 디스패처 호출
    0x1e02,  # 디스패처 호출
    0x5fec,  # 디스패처 호출
    0x6009,  # 디스패처 호출
    0x6011,  # 디스패처 호출
]

def main():
    print("="*70)
    print("🔍 미분석 함수 복구")
    print("="*70)

    print(f"\n복구 대상: {len(MISSING_FUNCTIONS)}개 함수")

    for offset in MISSING_FUNCTIONS:
        c_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
        json_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.json")
        asm_file = Path(f"output/decompiled/FUN_1000_{offset:04x}.asm")

        status = ""
        if c_file.exists():
            status = "✅ C 파일 있음"
        elif asm_file.exists():
            status = "📝 ASM 파일만 있음 - 디컴파일 필요"
        else:
            status = "❌ 파일 없음 - 수동 복구 필요"

        print(f"  FUN_1000_{offset:04x}: {status}")

    print("\n" + "="*70)
    print("🛠️  복구 방법")
    print("="*70)
    print("""
pyghidra로 수동 디컴파일:

1. pyghidra 스크립트 실행:
   python3 manual_decompile.py <offset>

   예: python3 manual_decompile.py 0x293e

2. 또는 Ghidra GUI에서:
   - Window > Decompile
   - 주소 1000:293e로 이동
   - 우클릭 > Create Function
   - File > Export > C/C++

3. 자동 일괄 복구:
   python3 batch_decompile_missing.py
""")

if __name__ == "__main__":
    main()
