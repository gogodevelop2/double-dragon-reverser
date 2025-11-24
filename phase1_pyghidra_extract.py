#!/usr/bin/env python3
"""
Phase 1: pyghidra로 모든 함수 디컴파일

pyghidra를 사용하여 Ghidra 프로젝트에서 모든 함수를 직접 디컴파일합니다.
"""

import os
import json
from datetime import datetime
from pathlib import Path

# pyghidra import
import pyghidra

# 출력 디렉토리
OUTPUT_DIR = Path("output")
DECOMPILED_DIR = OUTPUT_DIR / "decompiled"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

# Ghidra 프로젝트 경로
PROJECT_PATH = Path("ghidra-project").absolute()
PROJECT_NAME = "DoubleDragon"
BINARY_PATH = Path("reference/dos-original/DDMAIN.EXE").absolute()

# 환경 변수
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"

def decompile_all_functions():
    """모든 함수 디컴파일"""

    print("\n" + "=" * 70)
    print("Phase 1: pyghidra를 통한 함수 디컴파일")
    print("=" * 70)

    # 출력 디렉토리 생성
    DECOMPILED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n📂 Ghidra 프로젝트: {PROJECT_PATH}/{PROJECT_NAME}")
    print(f"📂 출력 디렉토리: {DECOMPILED_DIR}")
    print(f"🎯 대상 바이너리: {BINARY_PATH}")

    start_time = datetime.now()

    # pyghidra로 프로젝트 열기
    print(f"\n🚀 pyghidra 초기화 중...")

    with pyghidra.open_program(str(BINARY_PATH), project_location=PROJECT_PATH, project_name=PROJECT_NAME) as flat_api:

        program = flat_api.getCurrentProgram()
        func_manager = program.getFunctionManager()

        # Decompiler 인터페이스
        from ghidra.app.decompiler import DecompInterface
        decompiler = DecompInterface()
        decompiler.openProgram(program)

        print(f"✅ 프로그램 로드 완료: {program.getName()}")

        # 모든 함수 가져오기
        functions = list(func_manager.getFunctions(True))
        total = len(functions)

        print(f"\n📊 총 {total}개 함수 발견")
        print(f"⏱️ 예상 시간: {total * 2}초 ({total * 2 / 60:.1f}분)\n")

        success = 0
        failed = 0

        # 각 함수 디컴파일
        for i, func in enumerate(functions, 1):
            func_name = func.getName()
            func_addr = func.getEntryPoint()

            # 진행 상황 표시
            if i % 50 == 0 or i == 1:
                print(f"[{i}/{total}] 진행 중... ({i*100//total}%)")

            try:
                # 디컴파일 실행
                results = decompiler.decompileFunction(func, 30, None)

                if results and results.decompileCompleted():
                    c_code = results.getDecompiledFunction().getC()

                    # C 파일 저장
                    c_file = DECOMPILED_DIR / f"{func_name}.c"
                    with open(c_file, 'w') as f:
                        f.write(f"// Function: {func_name}\n")
                        f.write(f"// Address: {func_addr}\n")
                        f.write(f"// Size: {func.getBody().getNumAddresses()} bytes\n")
                        f.write(f"\n{c_code}\n")

                    # JSON 메타데이터
                    json_file = DECOMPILED_DIR / f"{func_name}.json"
                    metadata = {
                        "name": func_name,
                        "address": str(func_addr),
                        "size": func.getBody().getNumAddresses(),
                        "timestamp": datetime.now().isoformat()
                    }
                    with open(json_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

                    success += 1
                else:
                    failed += 1

            except Exception as e:
                failed += 1
                print(f"  ⚠️ [{i}] {func_name}: {str(e)[:50]}")

        # Decompiler 정리
        decompiler.dispose()

        # 최종 통계
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 70)
        print("✅ Phase 1 완료!")
        print("=" * 70)
        print(f"\n📊 통계:")
        print(f"   총 함수: {total}개")
        print(f"   성공: {success}개")
        print(f"   실패: {failed}개")
        print(f"   성공률: {success*100//total}%")
        print(f"   소요 시간: {duration:.1f}초 ({duration/60:.1f}분)")
        print(f"   평균 속도: {duration/total:.2f}초/함수")

        # 체크포인트 저장
        checkpoint = {
            "phase": 1,
            "timestamp": end_time.isoformat(),
            "binary": str(BINARY_PATH),
            "stats": {
                "total_functions": total,
                "success": success,
                "failed": failed,
                "duration_seconds": duration,
                "avg_time_per_function": duration / total
            }
        }

        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint_file = CHECKPOINT_DIR / "phase1.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"\n💾 체크포인트 저장: {checkpoint_file}")

        # 샘플 파일 표시
        c_files = sorted(DECOMPILED_DIR.glob("*.c"))
        if c_files:
            print(f"\n📄 생성된 파일 예시 (처음 5개):")
            for i, f in enumerate(c_files[:5], 1):
                size = f.stat().st_size
                print(f"   {i}. {f.name} ({size} bytes)")

if __name__ == "__main__":
    try:
        decompile_all_functions()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
