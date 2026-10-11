package local.minecraft.performance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.function.BooleanSupplier;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(MinecraftServer.class)
public abstract class ServerTickProbeMixin {
    @Unique private final TickBuffer probeTicks = new TickBuffer();
    @Unique private long probeTickStart;
    @Inject(method = "tickServer", at = @At("HEAD"))
    private void tickStart(BooleanSupplier keepTicking, CallbackInfo ci) {
        probeTickStart = System.nanoTime();
    }
    @Inject(method = "tickServer", at = @At("RETURN"))
    private void tickEnd(BooleanSupplier keepTicking, CallbackInfo ci) {
        probeTicks.add(probeTickStart, System.nanoTime());
    }
    @Inject(method = "stopServer", at = @At("HEAD"))
    private void saveTicks(CallbackInfo ci) throws IOException {
        probeTicks.save(Path.of(System.getenv("MINECRAFT_TICK_OUTPUT")));
    }
}
