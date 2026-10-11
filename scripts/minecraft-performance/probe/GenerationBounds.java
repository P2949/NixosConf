import net.minecraft.world.level.chunk.status.ChunkPyramid;
import net.minecraft.world.level.chunk.status.ChunkStatus;

/** Read the pinned game's own cumulative generation dependency radii. */
public final class GenerationBounds {
    public static void main(String[] args) {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        var step = ChunkPyramid.GENERATION_PYRAMID.getStepTo(ChunkStatus.FULL);
        for (var status : ChunkStatus.getStatusList())
            System.out.println("GENERATION_BOUND " + status.getName() + "=" + step.getAccumulatedRadiusOf(status));
    }
}
