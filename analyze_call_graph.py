#!/usr/bin/env python3
"""
함수 호출 그래프 분석 - Spice86 ExecutionFlow.json 활용

목적:
1. 가장 많이 호출되는 함수 찾기 (게임 로직 후보)
2. 중요한 함수 간 관계 파악
3. Blit 함수 후보 추천
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

def linear_to_segment_offset(linear):
    """Linear 주소를 세그먼트:오프셋으로 변환"""
    # Spice86: Segment 0x0170 = Linear base 5888
    # Ghidra: Segment 0x1000 (리베이스됨)
    # Offset은 동일
    spice86_base = 0x0170 * 16  # = 5888
    offset = linear - spice86_base
    if offset < 0 or offset > 0xFFFF:
        return None
    return f"1000:{offset:04x}"

def analyze_call_graph():
    """호출 그래프 분석"""
    flow_file = Path("spice86-dumps/E06625593A0E4A57396DF846E686BC063D03668F1CFB6B8D6B75E14FFCE5D07A/spice86dumpExecutionFlow.json")

    if not flow_file.exists():
        print(f"❌ {flow_file} 파일이 없습니다.")
        return

    print("📂 ExecutionFlow.json 로딩중...")
    with open(flow_file) as f:
        data = json.load(f)

    calls_from_to = data.get("CallsFromTo", {})

    # 통계 수집
    caller_count = Counter()  # 호출하는 횟수
    callee_count = Counter()  # 호출당하는 횟수
    call_pairs = []

    for caller_str, callees in calls_from_to.items():
        caller = int(caller_str)
        for callee_info in callees:
            callee = callee_info["Linear"]

            caller_count[caller] += 1
            callee_count[callee] += 1
            call_pairs.append((caller, callee))

    print(f"\n✅ 총 {len(call_pairs)}개의 함수 호출 발견")
    print(f"   고유 함수: {len(set(caller_count.keys()) | set(callee_count.keys()))}개")

    # 가장 많이 호출되는 함수 (게임 로직 후보)
    print("\n" + "="*70)
    print("🔥 가장 많이 호출되는 함수 TOP 20 (그래픽/게임 로직 후보)")
    print("="*70)

    for linear, count in callee_count.most_common(20):
        seg_off = linear_to_segment_offset(linear)
        # 디컴파일된 함수와 매칭
        if seg_off:
            offset = int(seg_off.split(':')[1], 16)
            decompiled = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
            status = "✅" if decompiled.exists() else "❌"
            print(f"  {status} 0x{linear:06x} (FUN_1000_{offset:04x}): {count:3d}회 호출")
        else:
            print(f"  ⚠️  0x{linear:06x}: {count:3d}회 호출")

    # 가장 많이 호출하는 함수 (메인 루프 후보)
    print("\n" + "="*70)
    print("🎮 가장 많이 호출하는 함수 TOP 10 (메인 루프/디스패처 후보)")
    print("="*70)

    for linear, count in caller_count.most_common(10):
        seg_off = linear_to_segment_offset(linear)
        if seg_off:
            offset = int(seg_off.split(':')[1], 16)
            decompiled = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
            status = "✅" if decompiled.exists() else "❌"
            print(f"  {status} 0x{linear:06x} (FUN_1000_{offset:04x}): {count:3d}개 함수 호출")
        else:
            print(f"  ⚠️  0x{linear:06x}: {count:3d}개 함수 호출")

    # Blit 함수 후보 추천
    print("\n" + "="*70)
    print("🖼️  Blit 함수 후보 (많이 호출 + 디컴파일 있음)")
    print("="*70)

    blit_candidates = []
    for linear, count in callee_count.most_common(50):
        seg_off = linear_to_segment_offset(linear)
        if seg_off:
            offset = int(seg_off.split(':')[1], 16)
            decompiled = Path(f"output/decompiled/FUN_1000_{offset:04x}.c")
            if decompiled.exists() and count >= 5:
                # 함수 크기 체크 (Blit 함수는 보통 중간 크기)
                size = decompiled.stat().st_size
                if 200 < size < 2000:  # 적당한 크기
                    blit_candidates.append({
                        'offset': offset,
                        'calls': count,
                        'size': size,
                        'linear': linear
                    })

    blit_candidates.sort(key=lambda x: x['calls'], reverse=True)

    for i, cand in enumerate(blit_candidates[:10], 1):
        print(f"  {i:2d}. FUN_1000_{cand['offset']:04x}: {cand['calls']:3d}회 호출, {cand['size']:4d} bytes")
        print(f"      → output/decompiled/FUN_1000_{cand['offset']:04x}.c 확인하세요")

    # 결과 저장
    output = {
        "most_called": [
            {"linear": linear, "offset": linear - 0x10000, "calls": count}
            for linear, count in callee_count.most_common(30)
        ],
        "blit_candidates": blit_candidates[:10],
        "total_calls": len(call_pairs),
        "unique_functions": len(set(caller_count.keys()) | set(callee_count.keys()))
    }

    output_file = Path("output/checkpoints/call_graph_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ 결과 저장: {output_file}")

if __name__ == "__main__":
    analyze_call_graph()
