package local.minecraft.performance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Disposable client instrumentation. Never install in a normal Prism profile. */
@Mixin(Minecraft.class)
public abstract class ClientProbeMixin {
    @Unique private long probeStarted;
    @Unique private long probeJoined;
    @Unique private long probeLastFrame;
    @Unique private long probeHeartbeat;
    @Unique private FrameBuffer probeFrames;
    @Unique private boolean probeOverflow;
    @Unique private double probeDuration;
    @Unique private Path probeOutput;
    @Unique private boolean probeFinished;

    @Inject(method = "runTick", at = @At("HEAD"))
    private void performanceFrame(boolean render, CallbackInfo ci) throws IOException {
        Minecraft client = (Minecraft) (Object) this;
        if (probeFinished) return;
        long now = System.nanoTime();
        if (probeStarted == 0) {
            probeStarted = now;
            probeOutput = Path.of(System.getenv("MINECRAFT_PROBE_OUTPUT"));
            Files.createDirectories(probeOutput);
            probeDuration = Double.parseDouble(System.getenv("MINECRAFT_PROBE_DURATION"));
            if (!Double.isFinite(probeDuration) || probeDuration <= 0 || probeDuration > 3600)
                throw new IllegalArgumentException("probe duration outside 0..3600 seconds");
            probeFrames = new FrameBuffer((int) Math.ceil((probeDuration + 180) * 1000));
            Files.writeString(probeOutput.resolve("pid"), Long.toString(ProcessHandle.current().pid()));
        }
        boolean connected = client.level != null && client.player != null && !client.hasSingleplayerServer();
        if (connected && probeJoined == 0) probeJoined = now;
        if (connected && probeLastFrame != 0 && render) {
            if (!probeFrames.add(now, now - probeLastFrame)) probeOverflow = true;
        }
        probeLastFrame = connected && render ? now : 0;
        if (now - probeHeartbeat >= 1_000_000_000L) {
            probeHeartbeat = now;
            Files.writeString(probeOutput.resolve("heartbeat.json"),
                "{\"connected\":" + connected + ",\"elapsed_seconds\":" + ((now - probeStarted) / 1e9) + "}\n");
        }
        String result = null;
        if (probeOverflow) result = "FAIL_FRAME_BUFFER_OVERFLOW";
        else if (probeJoined != 0 && !connected) result = "FAIL_DISCONNECTED";
        else if (probeJoined == 0 && now - probeStarted > 180_000_000_000L) result = "FAIL_NO_LOGIN";
        else if (probeJoined != 0 && now - probeJoined >= probeDuration * 1e9) result = "PASS";
        if (result != null) {
            probeFinished = true;
            probeFrames.save(probeOutput.resolve("client-frametimes.csv"));
            Files.writeString(probeOutput.resolve("result.json"), "{\"result\":\"" + result + "\"}\n");
            if (connected) client.disconnectWithSavingScreen();
            client.stop();
        }
    }
}
