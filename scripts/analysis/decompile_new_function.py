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
    
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    
    program = flat_api.getCurrentProgram()
    addr_space = program.getAddressFactory().getDefaultAddressSpace()
    listing = program.getListing()
    
    # 1000:5e55 함수
    addr = addr_space.getAddress((0x1000 << 4) + 0x5e55)
    func = listing.getFunctionAt(addr)
    
    if not func:
        print("함수 없음!")
    else:
        print(f"=== {func.getName()} 디컴파일 ===\n")
        
        # 디컴파일러 초기화
        decompiler = DecompInterface()
        decompiler.openProgram(program)
        
        # 디컴파일 실행
        monitor = ConsoleTaskMonitor()
        result = decompiler.decompileFunction(func, 30, monitor)  # 30초 타임아웃
        
        if result.decompileCompleted():
            print("✅ 디컴파일 성공!\n")
            c_code = result.getDecompiledFunction().getC()
            print(c_code)
        else:
            print(f"❌ 디컴파일 실패: {result.getErrorMessage()}")

print("\n완료!")
