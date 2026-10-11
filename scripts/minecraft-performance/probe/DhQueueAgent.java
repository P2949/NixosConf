package local.minecraft.performance;

import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Collection;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/** One-shot read-only DH 3.3.4 queue observation, used only in functional clones. */
public final class DhQueueAgent {
    private static Object field(Object object, String name) throws Exception {
        for (Class<?> type = object.getClass(); type != null; type = type.getSuperclass()) {
            try {
                Field field = type.getDeclaredField(name);
                field.setAccessible(true);
                return field.get(object);
            } catch (NoSuchFieldException absent) { }
        }
        throw new NoSuchFieldException(name);
    }

    private static Object invoke(Object object, String name) throws Exception {
        var method = object.getClass().getMethod(name);
        method.setAccessible(true);
        return method.invoke(object);
    }

    private static Class<?> loaded(Instrumentation instrumentation, String name) throws Exception {
        for (Class<?> type : instrumentation.getAllLoadedClasses())
            if (type.getName().equals(name)) return type;
        throw new ClassNotFoundException(name);
    }

    private static int size(Object object) {
        if (object instanceof Map<?, ?> map) return map.size();
        return ((Collection<?>) object).size();
    }

    private static void count(Map<String, Long> counts, String name, Object number) {
        long value = ((Number) number).longValue();
        if (value < 0) throw new IllegalArgumentException("negative queue count");
        counts.put(name, value);
    }

    public static void agentmain(String output, Instrumentation instrumentation) throws Exception {
        // One attach avoids repeated JVM warning/log writes during observation.
        capture(output, instrumentation, 0);
        Thread worker = new Thread(() -> {
            for (int sequence = 1; sequence <= 91; sequence++) {
                try {
                    Thread.sleep(10_000);
                    if (Files.exists(Path.of(output).getParent().resolve("stop"))) return;
                    capture(output, instrumentation, sequence);
                } catch (Exception failure) { return; }
            }
        }, "DH Qualification Queue Observer");
        worker.setDaemon(true);
        worker.start();
    }

    private static void capture(String output, Instrumentation instrumentation, int sequence) throws Exception {
        Path path = Path.of(output);
        if (!path.isAbsolute() || !path.equals(path.normalize())
                || !path.startsWith("/run/minecraft-performance-queues")
                || !path.getParent().equals(path.getParent().toRealPath()) || Files.isSymbolicLink(path))
            throw new IllegalArgumentException("queue snapshots must use private tmpfs namespace");
        Map<String, Long> counts = new TreeMap<>();
        try {
            Class<?> shared = loaded(instrumentation, "com.seibel.distanthorizons.core.api.internal.SharedApi");
            Object manager = shared.getField("WORLD_CHUNK_UPDATE_MANAGER").get(null);
            count(counts, "chunk_updates", invoke(manager, "getTotalQueuedCount"));
            Object world = shared.getMethod("getAbstractDhWorld").invoke(null);
            Iterable<?> levels = (Iterable<?>) invoke(world, "getAllLoadedLevels");
            int levelCount = 0;
            for (Object level : levels) {
                String prefix = "level_" + levelCount++ + "_";
                count(counts, prefix + "worldgen_centers", size(field(level, "worldGenPlayerCenteringQueue")));
                Object handler = field(level, "requestHandler");
                count(counts, prefix + "requests_by_pos", size(field(handler, "requestGroupsByPos")));
                count(counts, prefix + "requests_by_future", size(field(handler, "requestGroupsByFutureId")));
                Object provider = invoke(level, "getFullDataProvider");
                count(counts, prefix + "retrieval_futures", size(field(provider, "queuedRetrievalFutureByPos")));
                Object cache = field(provider, "delayedFullDataSourceSaveCache");
                count(counts, prefix + "unsaved", invoke(cache, "getUnsavedCount"));
                Object updater = field(provider, "dataUpdater");
                long queuedUpdates = 0;
                for (Object number : ((Map<?, ?>) field(updater, "queuedUpdateCountsByPos")).values())
                    queuedUpdates += ((AtomicInteger) number).get();
                count(counts, prefix + "queued_updates", queuedUpdates);
                count(counts, prefix + "locked_positions", size(field(updater, "lockedPosSet")));
                Object propagator = field(provider, "updatePropagator");
                count(counts, prefix + "propagating", size(field(propagator, "updatingPosSet")));
                count(counts, prefix + "generating", size(field(propagator, "generatingPosSet")));
                Object retrieval = ((AtomicReference<?>) field(provider, "worldGenQueueRef")).get();
                for (String method : new String[]{"getWaitingTaskCount", "getInProgressTaskCount", "getQueuedChunkCount"})
                    count(counts, prefix + method, retrieval == null ? 0 : invoke(retrieval, method));
            }
            if (levelCount == 0) throw new IllegalStateException("no loaded DH levels");
            Class<?> pools = loaded(instrumentation, "com.seibel.distanthorizons.core.util.threading.ThreadPoolUtil");
            for (String method : new String[]{"getFileHandlerExecutor", "getUpdatePropagatorExecutor",
                    "getWorldGenExecutor", "getNetworkCompressionExecutor", "getChunkToLodBuilderExecutor"}) {
                Object pool = pools.getMethod(method).invoke(null);
                count(counts, method + "_queued", pool == null ? 0 : invoke(pool, "getQueueSize"));
                count(counts, method + "_running", pool == null ? 0 : invoke(pool, "getRunningTaskCount"));
            }
            StringBuilder json = new StringBuilder("{\"schema\":1,\"complete\":true,\"sequence\":")
                .append(sequence).append(",\"loaded_levels\":")
                .append(levelCount).append(",\"queues\":{");
            boolean first = true;
            for (var entry : counts.entrySet()) {
                if (!first) json.append(',');
                first = false;
                json.append('"').append(entry.getKey()).append("\":").append(entry.getValue());
            }
            writeSnapshot(path, json.append("}}\n").toString());
        } catch (Exception failure) {
            try {
                writeSnapshot(path, "{\"schema\":1,\"complete\":false,\"error_type\":\""
                    + failure.getClass().getSimpleName() + "\"}\n");
            } catch (Exception outputFailure) { failure.addSuppressed(outputFailure); }
            throw failure;
        }
    }

    private static void writeSnapshot(Path path, String json) throws Exception {
        Path temporary = path.resolveSibling(path.getFileName() + ".tmp");
        if (Files.isSymbolicLink(temporary)) throw new IllegalArgumentException("snapshot temporary alias");
        Files.writeString(temporary, json);
        Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }
}
