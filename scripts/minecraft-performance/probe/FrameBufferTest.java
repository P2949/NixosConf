package local.minecraft.performance;

import java.nio.file.Files;

public final class FrameBufferTest {
    public static void main(String[] args) throws Exception {
        FrameBuffer buffer = new FrameBuffer(2);
        if (!buffer.add(100, 1_000_000) || !buffer.add(200, 2_000_000) || buffer.add(300, 1))
            throw new AssertionError("bounded buffer did not report overflow");
        var path = Files.createTempFile("frame-buffer", ".csv");
        try {
            buffer.save(path);
            if (!Files.readString(path).equals("monotonic_ns,frame_time_ms\n100,1.0\n200,2.0\n"))
                throw new AssertionError("raw frame conversion changed");
        } finally {
            Files.delete(path);
        }
        try {
            buffer.add(0, -1);
            throw new AssertionError("negative frame interval accepted");
        } catch (IllegalArgumentException expected) { }
    }
}
