package local.minecraft.performance;

import java.io.BufferedWriter;
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
    @Unique private BufferedWriter probeFrames;
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
            probeFrames = Files.newBufferedWriter(probeOutput.resolve("client-frametimes.csv"));
            probeFrames.write("monotonic_ns,frame_time_ms\n");
            Files.writeString(probeOutput.resolve("pid"), Long.toString(ProcessHandle.current().pid()));
        }
        boolean connected = client.level != null && client.player != null && !client.hasSingleplayerServer();
        if (connected && probeJoined == 0) probeJoined = now;
        if (connected && probeLastFrame != 0 && render) {
            probeFrames.write(now + "," + ((now - probeLastFrame) / 1_000_000.0) + "\n");
        }
        probeLastFrame = connected && render ? now : 0;
        if (now - probeHeartbeat >= 1_000_000_000L) {
            probeHeartbeat = now;
            Files.writeString(probeOutput.resolve("heartbeat.json"),
                "{\"connected\":" + connected + ",\"elapsed_seconds\":" + ((now - probeStarted) / 1e9) + "}\n");
            probeFrames.flush();
        }
        double duration = Double.parseDouble(System.getenv("MINECRAFT_PROBE_DURATION"));
        String result = null;
        if (probeJoined != 0 && !connected) result = "FAIL_DISCONNECTED";
        else if (probeJoined == 0 && now - probeStarted > 180_000_000_000L) result = "FAIL_NO_LOGIN";
        else if (probeJoined != 0 && now - probeJoined >= duration * 1e9) result = "PASS";
        if (result != null) {
            probeFinished = true;
            probeFrames.close();
            Files.writeString(probeOutput.resolve("result.json"), "{\"result\":\"" + result + "\"}\n");
            if (connected) client.disconnectWithSavingScreen();
            client.stop();
        }
    }
}
