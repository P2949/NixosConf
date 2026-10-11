package local.minecraft.performance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;

public final class TickBuffer {
    private final ArrayList<long[]> samples = new ArrayList<>();
    public void add(long start, long end) {
        if (end < start) throw new IllegalArgumentException("negative tick duration");
        samples.add(new long[] {start, end - start});
    }
    public void save(Path path) throws IOException {
        try (var writer = Files.newBufferedWriter(path)) {
            writer.write("monotonic_ns,tick_ms\n");
            for (long[] sample : samples) {
                writer.write(sample[0] + "," + (sample[1] / 1_000_000.0) + "\n");
            }
        }
    }
}
