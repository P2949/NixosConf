package org.popcraft.chunky;
import java.nio.file.*;
import java.io.*;
public final class RetirementGate {
    public static void await(GenerationTask task) {
        if (!task.getSelection().world().getName().equals("minecraft:overworld") || task.getSelection().centerX() != 0) return;
        String path = System.getProperty("chunky.test.retirementGate");
        if (path == null || !Files.exists(Path.of(path + ".armed"))) return;
        try {
            Files.delete(Path.of(path + ".armed"));
            Files.writeString(Path.of(path + ".reached"), "old cancelled worker reached retirement");
            try (InputStream release = Files.newInputStream(Path.of(path + ".release"))) {
                if (release.read() < 0) throw new IOException("gate closed without release");
            }
            Files.writeString(Path.of(path + ".released"), "old worker released");
        } catch (IOException e) { throw new RuntimeException(e); }
    }
}
