import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
import pyghidra
import json

pyghidra.start(verbose=False)

# Mode 1 테이블의 11개 주소
mode1_addresses = [
    0x5f07,  # index 0
    0x5e55,  # index 1 (이미 복구됨)
    0x8492,  # index 2
    0x84ee,  # index 3
    0x8583,  # index 4
    0x853d,  # index 5
    0x8622,  # index 6
    0x7eb0,  # index 7
    0x5aaa,  # index 8
    0x5b5f,  # index 9
    0x5c0a,  # index 10
]

results = []

with pyghidra.open_program(
    Path("reference/dos-original/DDMAIN.EXE").absolute(),
    project_location=Path("ghidra-project").absolute(),
    project_name="DoubleDragon",
    analyze=False
) as flat_api:

    from ghidra.app.cmd.disassemble import DisassembleCommand
    from ghidra.app.cmd.function import CreateFunctionCmd
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor

    program = flat_api.getCurrentProgram()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    listing = program.getListing()

    # 디컴파일러 초기화 (한 번만)
    decompiler = DecompInterface()
    decompiler.openProgram(program)
    monitor = ConsoleTaskMonitor()

    seg = 0x1000

    print("=" * 70)
    print("Mode 1 함수 포인터 테이블 - 전체 복구 시작")
    print("=" * 70)

    for idx, offset in enumerate(mode1_addresses):
        addr = addr_space.getAddress((seg << 4) + offset)

        print(f"\n[{idx:2d}/11] {seg:04x}:{offset:04x} 처리 중...")

        result = {
            "index": idx,
            "address": f"{seg:04x}:{offset:04x}",
            "offset": offset,
            "status": "unknown"
        }

        # 1. 기존 함수 확인
        existing_func = listing.getFunctionAt(addr)
        if existing_func:
            print(f"  ✅ 이미 존재: {existing_func.getName()}")
            result["status"] = "already_exists"
            result["function_name"] = existing_func.getName()
            result["size"] = existing_func.getBody().getNumAddresses()
            results.append(result)
            continue

        # 2. 디스어셈블 시도
        print(f"  → 디스어셈블 시도...")
        disasm_cmd = DisassembleCommand(addr, None, True)
        if not disasm_cmd.applyTo(program):
            print(f"  ❌ 디스어셈블 실패: {disasm_cmd.getStatusMsg()}")
            result["status"] = "disassemble_failed"
            result["error"] = disasm_cmd.getStatusMsg()
            results.append(result)
            continue

        print(f"  ✅ 디스어셈블 성공")

        # 3. 함수 생성 시도
        print(f"  → 함수 생성 시도...")
        create_func_cmd = CreateFunctionCmd(addr)
        if not create_func_cmd.applyTo(program):
            print(f"  ❌ 함수 생성 실패: {create_func_cmd.getStatusMsg()}")
            result["status"] = "function_creation_failed"
            result["error"] = create_func_cmd.getStatusMsg()
            results.append(result)
            continue

        func = listing.getFunctionAt(addr)
        if not func:
            print(f"  ❌ 함수 생성 확인 실패")
            result["status"] = "function_not_found"
            results.append(result)
            continue

        print(f"  ✅ 함수 생성: {func.getName()} ({func.getBody().getNumAddresses()} bytes)")
        result["status"] = "recovered"
        result["function_name"] = func.getName()
        result["size"] = func.getBody().getNumAddresses()

        # 4. 디컴파일 시도
        print(f"  → 디컴파일 시도...")
        decompile_result = decompiler.decompileFunction(func, 30, monitor)

        if decompile_result.decompileCompleted():
            c_code = decompile_result.getDecompiledFunction().getC()

            # C 코드 파일로 저장
            output_dir = Path("output/decompiled")
            output_file = output_dir / f"{func.getName()}.c"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(c_code)

            print(f"  ✅ 디컴파일 완료: {output_file}")
            result["decompiled"] = True
            result["output_file"] = str(output_file)
            result["code_preview"] = c_code[:200] + "..." if len(c_code) > 200 else c_code
        else:
            print(f"  ❌ 디컴파일 실패: {decompile_result.getErrorMessage()}")
            result["decompiled"] = False
            result["error"] = decompile_result.getErrorMessage()

        results.append(result)

print("\n" + "=" * 70)
print("복구 완료 - 요약")
print("=" * 70)

# 통계
total = len(results)
already_exists = len([r for r in results if r["status"] == "already_exists"])
recovered = len([r for r in results if r["status"] == "recovered"])
failed = len([r for r in results if r["status"] not in ["already_exists", "recovered"]])

print(f"\n총 {total}개 주소:")
print(f"  ✅ 이미 존재: {already_exists}개")
print(f"  🔧 새로 복구: {recovered}개")
print(f"  ❌ 실패: {failed}개")

print("\n상세 결과:")
for r in results:
    status_icon = {
        "already_exists": "✅",
        "recovered": "🔧",
    }.get(r["status"], "❌")

    func_info = f"{r.get('function_name', 'N/A')} ({r.get('size', 0)} bytes)" if r.get('function_name') else "실패"
    print(f"  {status_icon} [{r['index']:2d}] {r['address']} - {func_info}")

# JSON으로 저장
output_json = Path("output/analysis/mode1_recovery_results.json")
output_json.parent.mkdir(parents=True, exist_ok=True)
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n결과 저장: {output_json}")
print("\n완료!")
