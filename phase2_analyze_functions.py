#!/usr/bin/env python3
"""
Phase 2: 디컴파일된 함수 분석 및 분류

118개의 디컴파일된 C 함수를 분석하여:
1. 함수 크기 및 복잡도 측정
2. 호출 패턴 분석
3. 데이터 접근 패턴 분석
4. 함수 분류 (렌더링, 입력, AI, 압축 등)
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 디렉토리
DECOMPILED_DIR = Path("output/decompiled")
OUTPUT_DIR = Path("output")
ANALYSIS_DIR = OUTPUT_DIR / "analysis"

def analyze_function(c_file):
    """개별 함수 분석"""

    with open(c_file, 'r') as f:
        content = f.read()

    # 기본 정보 추출
    lines = content.split('\n')
    func_name = None
    address = None
    size = None

    for line in lines[:10]:
        if line.startswith("// Function:"):
            func_name = line.split(":")[1].strip()
        elif line.startswith("// Address:"):
            address = line.split(":")[1].strip()
        elif line.startswith("// Size:"):
            size_str = line.split(":")[1].strip()
            size = int(re.search(r'(\d+)', size_str).group(1))

    # 코드 라인 수
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]
    loc = len(code_lines)

    # 함수 호출 찾기
    function_calls = re.findall(r'FUN_\w+\(', content)
    function_calls = list(set(function_calls))  # 중복 제거
    num_calls = len(function_calls)

    # 데이터 접근 패턴
    dat_references = re.findall(r'DAT_\w+', content)
    dat_references = list(set(dat_references))
    num_data_refs = len(dat_references)

    # 메모리 접근 패턴 (포인터 역참조)
    pointer_derefs = len(re.findall(r'\*\(', content))

    # 루프 검출
    has_while = 'while' in content
    has_for = 'for' in content
    has_do = 'do {' in content
    num_loops = sum([has_while, has_for, has_do])

    # 조건문 검출
    num_ifs = len(re.findall(r'\bif\s*\(', content))

    # 복잡도 점수 (간단한 휴리스틱)
    complexity = num_loops * 3 + num_ifs * 1 + num_calls * 0.5

    # 패턴 기반 분류
    category = categorize_function(content, func_name, function_calls, dat_references)

    return {
        "name": func_name,
        "address": address,
        "size": size,
        "loc": loc,
        "num_calls": num_calls,
        "called_functions": function_calls,
        "num_data_refs": num_data_refs,
        "data_references": dat_references[:10],  # 처음 10개만
        "pointer_derefs": pointer_derefs,
        "num_loops": num_loops,
        "num_ifs": num_ifs,
        "complexity": complexity,
        "category": category
    }

def categorize_function(content, func_name, calls, data_refs):
    """함수를 카테고리로 분류"""

    # 압축 관련 (이미 알려진 함수)
    if func_name in ["FUN_1000_605b", "FUN_1000_6091", "FUN_1000_2865"]:
        return "compression"

    # CGA 그래픽 관련
    if func_name in ["FUN_1000_0786", "FUN_1000_09d1", "FUN_1000_0cd1"]:
        return "graphics_cga"

    # 비디오 메모리 접근 (0xB8000)
    if "0xb8000" in content.lower() or "0xb800" in content.lower():
        return "graphics_video"

    # 포트 I/O (키보드, 타이머 등)
    if "inp(" in content or "outp(" in content:
        return "io"

    # 많은 데이터 참조 + 적은 로직 = 데이터 초기화
    if len(data_refs) > 10 and content.count('if') < 3:
        return "initialization"

    # 많은 루프 + 메모리 접근 = 렌더링 or 데이터 처리
    if "while" in content or "for" in content:
        if len(data_refs) > 5:
            return "rendering"
        return "data_processing"

    # 많은 조건문 = 게임 로직 or AI
    if content.count('if') > 5:
        return "game_logic"

    # 작은 함수 (< 10줄) = 헬퍼/유틸리티
    if content.count('\n') < 20:
        return "utility"

    return "unknown"

def generate_analysis_report(analyses):
    """분석 리포트 생성"""

    print("\n" + "=" * 70)
    print("Phase 2: 함수 분석 리포트")
    print("=" * 70)

    # 카테고리별 통계
    categories = defaultdict(list)
    for analysis in analyses:
        categories[analysis['category']].append(analysis)

    print(f"\n📊 총 {len(analyses)}개 함수 분석 완료\n")

    print("카테고리별 분류:")
    for cat, funcs in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cat:20s}: {len(funcs):3d}개")

    # 복잡도 Top 10
    print("\n⚙️ 복잡도 Top 10:")
    top_complex = sorted(analyses, key=lambda x: x['complexity'], reverse=True)[:10]
    for i, func in enumerate(top_complex, 1):
        print(f"  {i:2d}. {func['name']:30s} (복잡도: {func['complexity']:.1f})")

    # 크기 Top 10
    print("\n📏 크기 Top 10:")
    top_size = sorted(analyses, key=lambda x: x['size'] or 0, reverse=True)[:10]
    for i, func in enumerate(top_size, 1):
        size = func['size'] or 0
        print(f"  {i:2d}. {func['name']:30s} ({size} bytes)")

    # 함수 호출 네트워크
    print("\n🔗 함수 호출이 가장 많은 Top 10:")
    top_calls = sorted(analyses, key=lambda x: x['num_calls'], reverse=True)[:10]
    for i, func in enumerate(top_calls, 1):
        print(f"  {i:2d}. {func['name']:30s} ({func['num_calls']}개 호출)")

    # 카테고리별 상세
    print("\n" + "=" * 70)
    print("카테고리별 상세 분석")
    print("=" * 70)

    for cat, funcs in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n### {cat} ({len(funcs)}개)")
        for func in funcs[:5]:  # 각 카테고리에서 처음 5개만
            print(f"  - {func['name']}")

    return categories

def save_analysis_results(analyses, categories):
    """분석 결과 저장"""

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # JSON 저장
    json_file = ANALYSIS_DIR / "function_analysis.json"
    with open(json_file, 'w') as f:
        json.dump(analyses, f, indent=2)
    print(f"\n💾 분석 결과 저장: {json_file}")

    # 카테고리별 함수 목록 저장
    category_file = ANALYSIS_DIR / "function_categories.json"
    category_data = {
        cat: [f['name'] for f in funcs]
        for cat, funcs in categories.items()
    }
    with open(category_file, 'w') as f:
        json.dump(category_data, f, indent=2)
    print(f"💾 카테고리 저장: {category_file}")

    # 마크다운 리포트
    md_file = ANALYSIS_DIR / "function_analysis.md"
    with open(md_file, 'w') as f:
        f.write("# Double Dragon - 함수 분석 리포트\n\n")
        f.write(f"**분석 일시**: {datetime.now().isoformat()}\n")
        f.write(f"**총 함수**: {len(analyses)}개\n\n")

        f.write("## 카테고리별 분류\n\n")
        for cat, funcs in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"### {cat} ({len(funcs)}개)\n\n")
            for func in funcs:
                f.write(f"- `{func['name']}` - {func['size'] or 0}B, 복잡도 {func['complexity']:.1f}\n")
            f.write("\n")

    print(f"💾 마크다운 리포트: {md_file}")

def main():
    """메인 실행"""

    print("\n" + "=" * 70)
    print("Phase 2: 함수 분석 시작")
    print("=" * 70)

    # 모든 C 파일 찾기
    c_files = sorted(DECOMPILED_DIR.glob("*.c"))
    print(f"\n📂 {len(c_files)}개 C 파일 발견")

    # 각 함수 분석
    analyses = []
    for i, c_file in enumerate(c_files, 1):
        if i % 20 == 0 or i == 1:
            print(f"[{i}/{len(c_files)}] 분석 중... ({i*100//len(c_files)}%)")

        try:
            analysis = analyze_function(c_file)
            analyses.append(analysis)
        except Exception as e:
            print(f"  ⚠️ {c_file.name}: {e}")

    # 리포트 생성
    categories = generate_analysis_report(analyses)

    # 결과 저장
    save_analysis_results(analyses, categories)

    print("\n" + "=" * 70)
    print("✅ Phase 2 분석 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()
