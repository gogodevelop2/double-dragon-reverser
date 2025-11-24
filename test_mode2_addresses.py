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
    memory = program.getMemory()
    listing = program.getListing()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()

    # Mode 2 테이블: 1988:0x18f0
    data_seg = 0x1988
    table_offset = 0x18f0
    table_addr = addr_space.getAddress((data_seg << 4) + table_offset)

    print("=" * 70)
    print("Mode 2 함수 포인터 테이블 - 데이터 읽기")
    print(f"테이블 주소: {data_seg:04x}:{table_offset:04x}")
    print("=" * 70)

    # 11개 워드 (2 bytes each) 읽기
    mode2_addresses = []
    print("\n읽은 주소:")
    for i in range(11):
        word_addr = table_addr.add(i * 2)
        low = memory.getByte(word_addr) & 0xFF
        high = memory.getByte(word_addr.add(1)) & 0xFF
        word = (high << 8) | low
        mode2_addresses.append(word)
        print(f"  [{i:2d}] 1000:{word:04x}")

    # 첫 2개 주소 상세 확인
    print("\n" + "=" * 70)
    print("상세 테스트: 첫 2개 주소")
    print("=" * 70)

    code_seg = 0x1000
    for idx in [0, 1]:
        offset = mode2_addresses[idx]
        addr = addr_space.getAddress((code_seg << 4) + offset)

        print(f"\n[{idx}] {code_seg:04x}:{offset:04x} 분석:")
        print("-" * 50)

        # 1. 기존 함수 확인
        func = listing.getFunctionAt(addr)
        if func:
            print(f"  ✅ 함수 존재: {func.getName()}")
            print(f"     크기: {func.getBody().getNumAddresses()} bytes")
        else:
            print(f"  ❌ 함수 없음")

        # 2. 명령어 확인
        print(f"\n  명령어 확인 (처음 10개):")
        current_addr = addr
        has_instructions = False
        for i in range(10):
            inst = listing.getInstructionAt(current_addr)
            if inst:
                has_instructions = True
                mnemonic = inst.getMnemonicString()
                ops = []
                for j in range(inst.getNumOperands()):
                    ops.append(inst.getDefaultOperandRepresentation(j))
                operands = ", ".join(ops) if ops else ""

                offset_val = current_addr.getOffset() - (code_seg << 4)
                print(f"     {code_seg:04x}:{offset_val:04x}  {mnemonic:<8} {operands}")

                current_addr = current_addr.add(inst.getLength())
            else:
                print(f"     {code_seg:04x}:{current_addr.getOffset() - (code_seg << 4):04x}  [No instruction]")
                break

        # 3. Raw bytes 확인 (명령어 없으면)
        if not has_instructions:
            print(f"\n  Raw bytes (16 bytes):")
            print(f"     ", end="")
            for i in range(16):
                byte = memory.getByte(addr.add(i)) & 0xFF
                print(f"{byte:02x} ", end="")
                if i == 7:
                    print("\n     ", end="")
            print()

        # 4. 데이터 타입 확인
        data = listing.getDataAt(addr)
        if data:
            print(f"\n  데이터로 정의됨: {data.getDataType().getName()}")
        else:
            print(f"\n  데이터 아님 (undefined)")

        # 5. 참조 확인
        refs = list(program.getReferenceManager().getReferencesTo(addr))
        if refs:
            print(f"\n  참조 ({len(refs)}개):")
            for ref in refs[:3]:
                print(f"     From: {ref.getFromAddress()}")
        else:
            print(f"\n  참조 없음")

print("\n" + "=" * 70)
print("결론:")
print("=" * 70)

if mode2_addresses:
    print(f"\n✅ Mode 2 테이블 읽기 성공 (11개 주소)")
    print(f"\n첫 2개 주소 테스트 완료.")
    print(f"위 결과를 보고 Mode 2가 Mode 1과 같은 방식으로")
    print(f"복구 가능한지 판단하세요.")

print("\n완료!")
