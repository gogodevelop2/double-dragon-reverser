#!/usr/bin/env python3
"""
Phase 1: 전체 코드 추출

GhidraMCP를 통해 모든 함수를 디컴파일하여 C 파일로 저장
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# MCP 클라이언트 import 시도
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import anyio
except ImportError:
    print("❌ MCP 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install mcp")
    sys.exit(1)

# 출력 디렉토리
OUTPUT_DIR = Path("output")
DECOMPILED_DIR = OUTPUT_DIR / "decompiled"
DOCS_DIR = OUTPUT_DIR / "docs"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

# 통계
stats = {
    "total_functions": 0,
    "decompiled": 0,
    "failed": 0,
    "start_time": None,
    "end_time": None,
    "functions": []
}

async def list_functions_mcp(session, program_name="DDMAIN.EXE"):
    """MCP를 통해 함수 목록 조회"""
    try:
        result = await session.call_tool(
            "ghidra_list_functions",
            arguments={"program": program_name}
        )
        return result
    except Exception as e:
        print(f"❌ 함수 목록 조회 실패: {e}")
        return None

async def decompile_function_mcp(session, program_name, address):
    """MCP를 통해 함수 디컴파일"""
    try:
        result = await session.call_tool(
            "ghidra_decompile",
            arguments={
                "program": program_name,
                "address": address
            }
        )
        return result
    except Exception as e:
        print(f"❌ 디컴파일 실패 (0x{address:08x}): {e}")
        return None

async def extract_all_functions():
    """모든 함수 추출 메인 로직"""

    print("\n" + "=" * 70)
    print("Phase 1: 전체 코드 추출")
    print("=" * 70)

    stats["start_time"] = datetime.now()

    # MCP 서버 연결 (stdio 방식)
    server_params = StdioServerParameters(
        command="uvx",
        args=[
            "pyghidra-mcp",
            "reference/dos-original/DDMAIN.EXE",
            "reference/dos-original/DUAL.EXE",
            "reference/dos-original/SHOW.EXE"
        ],
        env={
            "GHIDRA_INSTALL_DIR": "/opt/homebrew/Cellar/ghidra/11.4.2/libexec",
            "JAVA_HOME": "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
        }
    )

    print("\n📡 GhidraMCP 서버 연결 중...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("✅ MCP 연결 성공!\n")

            # 1. 함수 목록 조회
            print("📋 Step 1: DDMAIN.EXE 함수 목록 조회...")
            functions_result = await list_functions_mcp(session, "DDMAIN.EXE")

            if not functions_result:
                print("❌ 함수 목록을 가져올 수 없습니다.")
                return

            # 결과 파싱
            functions = []
            if hasattr(functions_result, 'content'):
                for content in functions_result.content:
                    if hasattr(content, 'text'):
                        # JSON 파싱
                        try:
                            data = json.loads(content.text)
                            if isinstance(data, list):
                                functions = data
                        except:
                            pass

            stats["total_functions"] = len(functions)
            print(f"✅ 총 {len(functions)}개 함수 발견\n")

            # 2. 각 함수 디컴파일
            print(f"🔄 Step 2: {len(functions)}개 함수 디컴파일 시작...")
            print("-" * 70)

            for i, func in enumerate(functions, 1):
                func_name = func.get("name", f"FUN_{func.get('address', '0000')}")
                func_addr = func.get("address")

                if not func_addr:
                    continue

                # 주소 변환 (hex string → int)
                if isinstance(func_addr, str):
                    func_addr = int(func_addr, 16)

                print(f"[{i}/{len(functions)}] {func_name} (0x{func_addr:08x})...", end=" ")

                # 디컴파일
                start = time.time()
                result = await decompile_function_mcp(session, "DDMAIN.EXE", f"0x{func_addr:08x}")
                elapsed = time.time() - start

                if result:
                    # C 코드 추출
                    c_code = ""
                    if hasattr(result, 'content'):
                        for content in result.content:
                            if hasattr(content, 'text'):
                                c_code = content.text
                                break

                    if c_code:
                        # 파일 저장
                        output_file = DECOMPILED_DIR / f"{func_name}.c"
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(f"// Function: {func_name}\n")
                            f.write(f"// Address: 0x{func_addr:08x}\n")
                            f.write(f"// Decompiled: {datetime.now().isoformat()}\n\n")
                            f.write(c_code)

                        # 메타데이터 저장
                        meta = {
                            "name": func_name,
                            "address": f"0x{func_addr:08x}",
                            "size": func.get("size", 0),
                            "decompile_time": elapsed
                        }
                        meta_file = DECOMPILED_DIR / f"{func_name}.json"
                        with open(meta_file, "w", encoding="utf-8") as f:
                            json.dump(meta, f, indent=2)

                        stats["decompiled"] += 1
                        stats["functions"].append({
                            "name": func_name,
                            "address": f"0x{func_addr:08x}",
                            "time": elapsed
                        })

                        print(f"✅ ({elapsed:.2f}s)")
                    else:
                        print("⚠️ 코드 없음")
                        stats["failed"] += 1
                else:
                    print("❌ 실패")
                    stats["failed"] += 1

                # 진행률 표시
                if i % 10 == 0:
                    progress = (i / len(functions)) * 100
                    print(f"\n진행률: {progress:.1f}% ({i}/{len(functions)})")
                    print("-" * 70)

    stats["end_time"] = datetime.now()

    print("\n" + "=" * 70)
    print("✅ Phase 1 완료!")
    print("=" * 70)

def create_phase1_report():
    """Phase 1 리포트 생성"""

    duration = (stats["end_time"] - stats["start_time"]).total_seconds()
    avg_time = duration / stats["total_functions"] if stats["total_functions"] > 0 else 0

    # JSON 저장
    report = {
        "phase": 1,
        "title": "전체 코드 추출",
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "stats": {
            "total_functions": stats["total_functions"],
            "decompiled": stats["decompiled"],
            "failed": stats["failed"],
            "success_rate": f"{(stats['decompiled'] / stats['total_functions'] * 100):.1f}%",
            "total_time_seconds": duration,
            "average_time_per_function": avg_time
        },
        "functions": stats["functions"]
    }

    checkpoint_file = CHECKPOINT_DIR / "phase1.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Markdown 리포트
    md_report = f"""# Phase 1 체크포인트 리포트

**날짜**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**상태**: ✅ 완료

## 📊 실행 결과

### 전체 통계

- **총 함수 개수**: {stats['total_functions']}개
- **디컴파일 성공**: {stats['decompiled']}개
- **실패**: {stats['failed']}개
- **성공률**: {(stats['decompiled'] / stats['total_functions'] * 100):.1f}%

### 소요 시간

- **총 소요 시간**: {duration:.1f}초 ({duration/60:.1f}분)
- **함수당 평균**: {avg_time:.2f}초
- **시작**: {stats['start_time'].strftime("%H:%M:%S")}
- **종료**: {stats['end_time'].strftime("%H:%M:%S")}

### 산출물

```
output/decompiled/
├── FUN_1000_xxxx.c     ({stats['decompiled']}개 C 파일)
└── FUN_1000_xxxx.json  ({stats['decompiled']}개 메타데이터)
```

## 🎯 다음 단계: Phase 2

### Phase 2 작업 내용

1. **코드 분석 및 분류**
   - 압축 시스템 함수 식별
   - 그래픽 렌더링 함수 식별
   - 게임 로직 함수 식별

2. **데이터 구조 역산**
   - 플레이어, 적, 아이템 구조체
   - 레벨 데이터 구조
   - 메모리 맵 분석

3. **C++ 프로젝트 재구성**
   - 모던 C++ 클래스 설계
   - 시스템별 모듈화
   - CMake 프로젝트 생성

**예상 소요 시간**: 4-6시간

## ✅ Phase 1 체크포인트 승인 대기

**사용자 확인 필요**:
- [ ] 디컴파일 결과 검토
- [ ] 성공률 확인 ({(stats['decompiled'] / stats['total_functions'] * 100):.1f}%)
- [ ] Phase 2 진행 승인

**저장 위치**:
- JSON: `output/checkpoints/phase1.json`
- 리포트: `output/docs/phase1_report.md`
- 디컴파일 코드: `output/decompiled/` ({stats['decompiled']}개 파일)

---

**생성**: {datetime.now().isoformat()}
**상태**: 체크포인트 대기 중
"""

    report_file = DOCS_DIR / "phase1_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\n📊 통계:")
    print(f"   - 총 함수: {stats['total_functions']}개")
    print(f"   - 성공: {stats['decompiled']}개")
    print(f"   - 실패: {stats['failed']}개")
    print(f"   - 성공률: {(stats['decompiled'] / stats['total_functions'] * 100):.1f}%")
    print(f"   - 소요 시간: {duration:.1f}초 ({duration/60:.1f}분)")
    print(f"   - 평균 속도: {avg_time:.2f}초/함수")
    print(f"\n✅ 리포트 저장:")
    print(f"   - JSON: {checkpoint_file}")
    print(f"   - 리포트: {report_file}")

if __name__ == "__main__":
    try:
        anyio.run(extract_all_functions)
        create_phase1_report()

        print("\n" + "=" * 70)
        print("✅ Phase 1 체크포인트: 사용자 승인 대기")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자 중단")
        if stats["decompiled"] > 0:
            create_phase1_report()
            print("📊 부분 결과 저장됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
