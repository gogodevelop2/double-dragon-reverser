//Batch Decompiler for Double Dragon
//@category Analysis

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileAll extends GhidraScript {

    @Override
    public void run() throws Exception {

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        String outputDir = "/Users/joejeon/Documents/develop/Double Dragon/output/decompiled/";
        File dir = new File(outputDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        FunctionManager funcMgr = currentProgram.getFunctionManager();

        int total = 0;
        int success = 0;

        println("Starting batch decompilation...");
        println("Output: " + outputDir);
        println("");

        for (Function func : funcMgr.getFunctions(true)) {
            total++;
            String funcName = func.getName();

            if (total % 50 == 0) {
                println("Progress: " + total + " functions processed...");
            }

            try {
                DecompileResults results = decompiler.decompileFunction(func, 30, monitor);

                if (results != null && results.decompileCompleted()) {
                    String cCode = results.getDecompiledFunction().getC();

                    // C 파일 저장
                    File cFile = new File(outputDir + funcName + ".c");
                    PrintWriter writer = new PrintWriter(new FileWriter(cFile));
                    writer.println("// Function: " + funcName);
                    writer.println("// Address: " + func.getEntryPoint());
                    writer.println("");
                    writer.println(cCode);
                    writer.close();

                    success++;
                }
            } catch (Exception e) {
                // 무시하고 계속
            }
        }

        println("");
        println("================================================");
        println("Decompilation Complete!");
        println("Total: " + total);
        println("Success: " + success);
        println("================================================");

        decompiler.dispose();
    }
}
