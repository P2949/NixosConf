# Minecraft server performance qualification

The performance stack is undergoing staged qualification. No new server mod,
memory limit or collector has been activated in production. A stage advances only
after its automated correctness, recovery and performance gates pass.

## Original baseline

The source baseline is `832014a91a0e467f527a56ac773f2a872b2cf288`, running
Minecraft 26.3, Fabric Loader 0.19.5 and OpenJDK 25.0.4.1+1. The workstation has an
Intel Core i5-10600K, AMD Radeon RX 9070 XT and approximately 32 GiB RAM. The
kernel is 6.18.55. The existing display is 3440 × 1440 at 155 Hz.

The original JVM uses `-Xms1G -Xmx6G` and the Java 25 default G1 collector.
`MemoryHigh=8G`, `MemoryMax=10G`, `Nice=5`, and the Minecraft slice's CPU and IO
weights are both 50. Normal view distance is 12, simulation distance is 8 and
empty-server pause is 60 seconds.

| Mod ID | Declared version |
| --- | --- |
| fabric-api | 0.162.0+26.3 |
| ferritecore | 9.0.0 |
| lithium | 0.26.2+mc26.3 |
| servercore | 1.5.20+26.3 |
| spark | 1.10.187 |

A fresh backup completed at 2026-10-11 01:13:42 UTC and passed live verification.
The project retains an independent read-only Btrfs copy outside the managed
backup namespace, protecting its fixed world baseline from normal retention.

The fresh idle sample measured 300 seconds at one-second intervals with no
players and the server paused. Median service CPU was 0.382% of one core, p95
was 0.415%, and maximum was 0.759%. Median Java RSS was 1,559,687,168 bytes and
median cgroup memory was 1,612,419,072 bytes. All memory-event deltas were zero.
Host CPU median was 2.85%; concurrent repository/tool inspection produced a
79.76% maximum, so this is not evidence of a continuously quiet host. Comparative
performance runs require a separate quiet-environment gate.

Private raw baseline evidence is retained under
`/var/lib/minecraft-performance-agent`; the earlier artifact and schema evidence
is under `/persist/minecraft-performance/2026-10-11`. These locations contain no
repository-published credentials. Exact receipts and evidence digests will be
recorded after final qualification.

## Automated workload policy

Production worlds are excluded from terrain-generation and comparative runs.
Each comparable run starts from a fresh writable Btrfs snapshot of the same
read-only baseline, with loopback-only game and management endpoints and RCON
disabled. Isolation overrides remain constant across variants.

Disposable Prism profiles clone the normal client's mods and settings, retaining
its Java 25 and ZGC configuration. One profile contains DH; the other omits DH.
Prism's `--launch` and `--server` options perform automatic connection. A
disposable probe records connection heartbeats, frame intervals and process PID,
then disconnects and exits after the specified duration. It is absent from the
normal client and all production server mod inventories. MangoHud CSV logging
is collected independently.

Workloads use management commands for spectator mode, position, yaw and pitch.
They do not depend on keyboard input or subjective smoothness judgments.
Client 1% low is defined as `1000 / p99_frame_time_ms`. Confidence intervals
resample independent runs, not individual frames.

The prior observation of approximately 2.5–5% better client 1% lows with ZGC
motivates holding client ZGC fixed. It is prior client evidence and cannot
substitute for server collector measurements.

## Required acceptance

Krypton/DH acceptance requires exact runtime inventory, DH negotiation,
clean-cache synchronization, real-time data propagation, non-DH compatibility,
no unwanted distant terrain generation, paused idle and memory limits, healthy
backup databases and an isolated restore with a fresh client cache.

C2ME acceptance additionally requires deterministic A/B world generation,
structural region/NBT validation, restart, backup, both maintenance modes and
client performance non-regression. Its target executor parallelism is four.

The server collector remains undecided. Five valid runs per collector per
material workload, identical world/configuration state, JFR and client frame
measurements, and the executable decision policy are required. Missing evidence
is INCONCLUSIVE; a statistical tie selects G1. No candidate is persistent or
merged until its required gates pass.
