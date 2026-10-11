package local.minecraft.performance;

import java.nio.file.Files;
import local.minecraft.telemetry.TickBuffer;

public final class TickBufferTest {
    public static void main(String[] args) throws Exception {
        var buffer = new TickBuffer();
        buffer.add(100_000_000, 101_000_000);
        buffer.add(200_000_000, 275_000_000);
        var file = Files.createTempFile("tick-buffer-test", ".csv");
        try {
            buffer.save(file);
            String csv = Files.readString(file);
            if (!csv.equals("monotonic_ns,tick_ms\n100000000,1.0\n200000000,75.0\n")) {
                throw new AssertionError("incorrect tick units or missing slow tick");
            }
            try {
                buffer.add(2, 1);
                throw new AssertionError("negative duration accepted");
            } catch (IllegalArgumentException expected) { }
        } finally { Files.delete(file); }
    }
}
