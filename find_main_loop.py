import os
from pathlib import Path
os.environ['GHIDRA_INSTALL_DIR'] = "/opt/homebrew/Cellar/ghidra/11.4.2/libexec"
os.environ['JAVA_HOME'] = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
import pyghidra

pyghidra.start(verbose=False)

with pyghidra.open_program(
    Path("reference/dos-original/DDMAIN.EXE").absolute(),
    project_location=Path("ghidra-project").absolute(),
    project_name="DoubleDragon",
    analyze=False
) as flat_api:

    program = flat_api.getCurrentProgram()
    listing = program.getListing()
    func_manager = program.getFunctionManager()
    ref_manager = program.getReferenceManager()

    print("=" * 70)
    print("Double Dragon - 메인 게임 루프 찾기")
    print("=" * 70)

    # 1. Entry Point 찾기
    print("\n[1단계] Entry Point 확인")
    print("-" * 70)

    entry_points = program.getSymbolTable().getExternalEntryPointIterator()
    entry_func = None

    for symbol in entry_points:
        addr = symbol.getAddress()
        func = listing.getFunctionAt(addr)
        if func:
            print(f"  Entry Point: {func.getName()} @ {addr}")
            entry_func = func
            break

    if not entry_func:
        print("  Entry point를 못 찾았습니다. 대신 'main' 또는 'entry' 검색...")
        for func in func_manager.getFunctions(True):
            name = func.getName().lower()
            if 'main' in name or 'entry' in name:
                print(f"  발견: {func.getName()} @ {func.getEntryPoint()}")
                entry_func = func
                break

    # 2. Entry Point에서 호출하는 함수들
    if entry_func:
        print(f"\n[2단계] {entry_func.getName()}에서 호출하는 함수들 (직접 호출)")
        print("-" * 70)

        called_funcs = []
        for ref in ref_manager.getReferencesFrom(entry_func.getBody().getMinAddress()):
            if ref.getReferenceType().isCall():
                to_addr = ref.getToAddress()
                to_func = listing.getFunctionAt(to_addr)
                if to_func:
                    called_funcs.append(to_func)
                    print(f"  → {to_func.getName()} @ {to_addr}")

        # 3. 무한 루프가 있는 함수 찾기
        print(f"\n[3단계] 무한 루프 패턴 함수 찾기")
        print("-" * 70)
        print("  (JMP 자기 자신 또는 JMP 이전 주소 패턴)")

        loop_candidates = []

        # 모든 함수 검사
        for func in func_manager.getFunctions(True):
            body = func.getBody()

            # 함수 내의 모든 명령어 검사
            inst_iter = listing.getInstructions(body, True)
            for inst in inst_iter:
                mnemonic = inst.getMnemonicString()

                # JMP 명령어 찾기
                if mnemonic == "JMP":
                    # 점프 대상 주소
                    flows = inst.getFlows()
                    if flows and len(flows) > 0:
                        target = flows[0]

                        # 자기 자신 또는 이전 주소로 점프 (루프)
                        if target <= inst.getAddress():
                            # 함수 내부로 점프인지 확인
                            if body.contains(target):
                                loop_candidates.append((func, inst, target))
                                break  # 이 함수는 루프 있음

        print(f"  무한 루프 후보: {len(loop_candidates)}개 함수")
        for func, inst, target in loop_candidates[:10]:  # 처음 10개만
            offset_from = inst.getAddress().getOffset() - (0x1000 << 4)
            offset_to = target.getOffset() - (0x1000 << 4)
            print(f"    {func.getName()}")
            print(f"      @ 1000:{offset_from:04x}: JMP 1000:{offset_to:04x}")

        # 4. 디스패처 호출하는 함수 찾기
        print(f"\n[4단계] 디스패처(FUN_1000_48e0 등) 호출하는 함수 찾기")
        print("-" * 70)

        # 알려진 디스패처들
        dispatchers = [
            0x499b,  # Index 0
            0x48e0,  # Index 1
            0x81c2,  # Index 2
            0x822a,  # Index 3
            0x8277,  # Index 4
            0x82f4,  # Index 5
            0x8135,  # Index 6
            0x810b,  # Index 7
            0x5860,  # Index 8
            0x590a,  # Index 9
            0x599d,  # Index 10
        ]

        dispatcher_callers = {}

        for disp_offset in dispatchers:
            disp_addr = program.getAddressFactory().getDefaultAddressSpace().getAddress((0x1000 << 4) + disp_offset)
            disp_func = listing.getFunctionAt(disp_addr)

            if disp_func:
                refs = ref_manager.getReferencesTo(disp_addr)
                callers = set()

                for ref in refs:
                    if ref.getReferenceType().isCall():
                        from_addr = ref.getFromAddress()
                        caller = listing.getFunctionContaining(from_addr)
                        if caller:
                            callers.add(caller)

                if callers:
                    dispatcher_callers[disp_func.getName()] = list(callers)

        print(f"  디스패처를 호출하는 함수: {len(dispatcher_callers)}개 디스패처")

        for disp_name, callers in sorted(dispatcher_callers.items())[:5]:  # 처음 5개
            print(f"\n  {disp_name} 호출자 ({len(callers)}개):")
            for caller in callers[:3]:  # 각 디스패처당 3개만
                print(f"    ← {caller.getName()}")

        # 5. 가장 많이 호출되는 함수 (메인 루프 후보)
        print(f"\n[5단계] 가장 많이 호출되는 함수 찾기 (메인 루프 후보)")
        print("-" * 70)

        call_counts = {}

        for func in func_manager.getFunctions(True):
            refs = ref_manager.getReferencesTo(func.getEntryPoint())
            call_count = sum(1 for ref in refs if ref.getReferenceType().isCall())
            if call_count > 0:
                call_counts[func] = call_count

        # 상위 20개
        sorted_funcs = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)

        print(f"  가장 많이 호출되는 함수 (Top 20):")
        for func, count in sorted_funcs[:20]:
            print(f"    {func.getName():<30} - {count:3d}회 호출")

        # 6. 종합 추천
        print(f"\n[6단계] 메인 루프 후보 종합")
        print("=" * 70)

        # 무한 루프 + 디스패처 호출 + 많이 호출됨
        main_loop_candidates = []

        loop_func_names = {f.getName() for f, _, _ in loop_candidates}
        dispatcher_caller_names = set()
        for callers in dispatcher_callers.values():
            for caller in callers:
                dispatcher_caller_names.add(caller.getName())

        for func, count in sorted_funcs[:30]:  # 상위 30개 중에서
            name = func.getName()
            score = 0
            reasons = []

            if name in loop_func_names:
                score += 3
                reasons.append("무한루프")

            if name in dispatcher_caller_names:
                score += 2
                reasons.append("디스패처호출")

            if count >= 10:
                score += 1
                reasons.append(f"{count}회호출")

            if score >= 3:
                main_loop_candidates.append((func, score, reasons))

        main_loop_candidates.sort(key=lambda x: x[1], reverse=True)

        if main_loop_candidates:
            print("\n🎯 메인 루프 최종 후보:")
            for func, score, reasons in main_loop_candidates[:5]:
                print(f"\n  {func.getName()} (점수: {score})")
                print(f"    주소: {func.getEntryPoint()}")
                print(f"    크기: {func.getBody().getNumAddresses()} bytes")
                print(f"    이유: {', '.join(reasons)}")
        else:
            print("\n  명확한 메인 루프 후보를 못 찾았습니다.")
            print("\n  다음 함수들을 수동으로 확인해보세요:")
            print("\n  1. 무한 루프가 있는 함수:")
            for func, _, _ in loop_candidates[:3]:
                print(f"     - {func.getName()}")

            print("\n  2. 많이 호출되는 함수:")
            for func, count in sorted_funcs[:3]:
                print(f"     - {func.getName()} ({count}회)")

print("\n완료!")
