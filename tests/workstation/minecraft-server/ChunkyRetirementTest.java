import org.popcraft.chunky.*;
import org.popcraft.chunky.iterator.ChunkIterator;
import org.popcraft.chunky.platform.*;
import org.popcraft.chunky.util.ChunkCoordinate;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;

public final class ChunkyRetirementTest {
    static Object defaultValue(Class<?> type) {
        if (type == boolean.class) return false;
        if (type == int.class) return 0;
        if (type == double.class) return 0d;
        if (type == long.class) return 0L;
        if (type == Optional.class) return Optional.empty();
        if (type == String.class) return "test";
        return null;
    }
    @SuppressWarnings("unchecked")
    static <T> T proxy(Class<T> type, Map<String,Object> values) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type},
            (p,m,a) -> values.getOrDefault(m.getName(), defaultValue(m.getReturnType())));
    }
    static GenerationTask task(Chunky chunky, World world, int x) throws Exception {
        GenerationTask t = new GenerationTask(chunky, Selection.builder(chunky, world).center(x,0).radius(10000).build());
        Field iterator = GenerationTask.class.getDeclaredField("chunkIterator");
        iterator.setAccessible(true);
        iterator.set(t, new ChunkIterator() {
            public boolean hasNext() { return false; }
            public ChunkCoordinate next() { throw new NoSuchElementException(); }
            public long total() { return 1; }
            public String name() { return "region"; }
        });
        return t;
    }
    static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("chunky-retirement-");
        World world = proxy(World.class, Map.of("getName","minecraft:overworld","getKey","minecraft:overworld"));
        Config config = proxy(Config.class, Map.of("getDirectory",dir,"getLanguage","en","getUpdateInterval",1));
        Sender console = proxy(Sender.class, Map.of());
        Server server = proxy(Server.class, Map.of("getWorlds",List.of(world),"getConsole",console,"getConfig",config,"getMaxWorldSize",30000000,"getIntegrations",Map.of()));
        Chunky chunky = new Chunky(server,config);
        try {
            GenerationTask old = task(chunky,world,0), replacement = task(chunky,world,9000);
            chunky.getGenerationTasks().put(world.getName(),replacement);
            chunky.getTaskLoader().saveTask(replacement);
            old.stop(true);
            old.run();
            boolean registry = chunky.getGenerationTasks().get(world.getName()) == replacement;
            boolean checkpoint = chunky.getTaskLoader().loadTask(world).orElseThrow().getSelection().centerX() == 9000;
            System.out.printf("late old retirement: replacement registered=%s, replacement checkpoint=%s%n",registry,checkpoint);
            require(registry && checkpoint,"retiring A removed B or overwrote B's checkpoint");
            replacement.stop(false);
            replacement.run();
            require(!chunky.getGenerationTasks().containsKey(world.getName()),"normal retirement retained a stopped task");
            GenerationTask saved = chunky.getTaskLoader().loadTask(world).orElseThrow();
            require(saved.getSelection().centerX()==9000 && !saved.isCancelled(),"paused replacement cannot resume after restart");
            old.run();
            require(chunky.getTaskLoader().loadTask(world).orElseThrow().getSelection().centerX()==9000,"unregistered old worker overwrote the saved replacement");
            System.out.println("PASS: identity-safe retirement, checkpoint ownership and normal pause persistence");
        } finally { chunky.disable(); }
    }
}
