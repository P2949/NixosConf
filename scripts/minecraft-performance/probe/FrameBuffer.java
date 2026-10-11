package local.minecraft.telemetry;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Fixed storage allocated before measurement; no formatting or allocation per frame. */
public final class FrameBuffer {
    private final long[] samples;
    private int count;

    public FrameBuffer(int capacity) {
        if (capacity <= 0 || capacity > 4_000_000) throw new IllegalArgumentException("frame capacity");
        samples = new long[Math.multiplyExact(capacity, 2)];
    }

    public boolean add(long start, long duration) {
        if (duration < 0) throw new IllegalArgumentException("negative frame duration");
        if (count == samples.length / 2) return false;
        samples[count * 2] = start;
        samples[count * 2 + 1] = duration;
        count++;
        return true;
    }

    public void save(Path path) throws IOException {
        try (var writer = Files.newBufferedWriter(path)) {
            writer.write("monotonic_ns,frame_time_ms\n");
            for (int i = 0; i < count; i++) {
                writer.write(samples[i * 2] + "," + (samples[i * 2 + 1] / 1_000_000.0) + "\n");
            }
        }
    }
}
