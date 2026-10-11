package local.minecraft.performance;

import com.seibel.distanthorizons.core.network.messages.AbstractNetworkMessage;
import com.seibel.distanthorizons.core.network.messages.requests.ExceptionMessage;
import com.seibel.distanthorizons.core.network.session.NetworkSession;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Record packet types only; never record network payloads or credentials. */
@Mixin(NetworkSession.class)
public abstract class DhNetworkProbeMixin {
    @Inject(method = "tryHandleMessage", at = @At("HEAD"))
    private void incomingMessage(AbstractNetworkMessage message, CallbackInfo ci) throws IOException {
        Path directory = Path.of(System.getenv("MINECRAFT_PROBE_OUTPUT"));
        Files.createDirectories(directory);
        String exceptionType = message instanceof ExceptionMessage error && error.exception != null
            ? error.exception.getClass().getSimpleName() : "";
        Files.writeString(directory.resolve("dh-received.jsonl"),
            "{\"monotonic_ns\":" + System.nanoTime() + ",\"type\":\"" +
            message.getClass().getSimpleName() + "\",\"exception_type\":\"" + exceptionType + "\"}\n",
            StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }
}
