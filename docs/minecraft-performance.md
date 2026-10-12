# Minecraft server performance qualification

The performance stack is undergoing staged qualification. The first candidate
was transiently activated and subsequently rolled back. Production currently
runs the original baseline. A stage advances only after its automated
correctness, recovery and performance gates pass.

## Qualification status

Phase A is accepted for the frozen `a0f0921dc47d2aa57eb74d94f86ebfe53bc35515`
candidate only. All eight independently verified functional proofs pass. The
fixed eleven-pair idle study passes with median DH-on interval CPU 3.0121% of
one core, median run p95 CPU 3.7525%, and mean paired package-power increase
0.04449 W (nominal 95% Student t interval 0.01471–0.07427 W). Host, I/O, memory
events and world invariance gates pass. One invalid pair attempt was retained
and retried within the declared bound; thresholds were unchanged.

The immutable functional bundle digest is
`0d865f3782e013a345bb163df2694c33c2117f4f134f2a18a74bf2dd5f59e517`,
qualification identity
`aef9bc92755846d32fd9b004016e3f6cdaefa66f6b168ae7647270aefaded029`.
Private evidence is in `/persist/minecraft-performance-candidate-a0f0921` and
`/persist/minecraft-performance-dh-attribution-a0f0921`. Independent analysis
matched the recorded result; recovery completed without cleanup errors, the
controller exited successfully, production and its backup timer are active,
live backup verification passes, and the qualification port is closed.
Production still uses the safe original closure. C2ME, maintenance-mode and
collector qualification, final exact-head CI and deployment remain outstanding.
Earlier failures below retain their original outcomes.

C2ME release resolution on 2026-10-12 selected official Modrinth version
`ODMLK8M9`, `0.4.2-alpha.0.90+26.3`, published 2026-10-07, with metadata
explicitly listing Fabric and Minecraft 26.3. Its `fabric.mod.json` declares
ID `c2me`, Fabric Loader >=0.18.3, Java >=25, Minecraft >1.21.11 and bundled
`c2me-base`. The downloaded artifact matches upstream SHA-512; its SHA-256 is
`69c89a014b12428e5c8b3cff1d00f78ec0141fce5f3997ab1a70ee8168999291`.
The pin is qualification-only in `scripts/minecraft-performance/c2me.nix`.
`candidate.nix` defaults to the accepted stack and adds C2ME only with
`withC2ME = true`; both normal and Chunky inventories receive the same pin.
Pinned bytecode confirms root-level `globalExecutorParallelism` and config
schema version 3. The initial policy sets four, with no experimental overrides
or OpenCL addon. Generated runtime config and startup evidence must still
prove the effective value before correctness or performance acceptance.
Source: https://modrinth.com/mod/c2me-fabric/version/ODMLK8M9.

Production remains on the original baseline. The eight-gate receipt at
`da0be1e` is historical evidence for that harness, not final Phase-A acceptance:
client SQLite usefulness, controlled distant updates, and restored DH data still
require stronger automated proofs. The interrupted idle study completed zero
valid pairs; its private cancellation receipt records INCONCLUSIVE, preserves
partial evidence, and records healthy production recovery.

The stronger `b70c14a` candidate passed ordinary-client compatibility but failed
DH qualification when the cached reconnect received one `RateLimitedException`
before the landmark mutation. Both bounded clients completed and the landmark
was restored; production and live backup health recovered. That exception remains
a failure. The next candidate freezes the disposable DH client synchronization
rate at 20 requests/second against the server's unchanged global 50/second
ceiling and requires received session-config telemetry to confirm negotiation.
Pinned DH 3.3.4 bytecode uses the minimum client/server session rate while its
server limiter reads the global server setting. This gives request scheduling
headroom; fresh qualification must establish whether it resolves the burst.
The `b408cea` run verified synchronization at 20 but still failed on the separate
full-data request limiter, identified by its client log as 20 on both ends.
The next frozen client uses synchronization/full-data rates 20/8 against the
unchanged server defaults 50/20 and verifies both negotiated values. Failed
attempts remain FAIL; no additional exception is allowed.

Recovery binds client templates to the manifest digest captured when the guard
is armed. Disposable unit, slice, and client-template errors are recorded and
reported only after safe production restoration and live backup verification.
A failed client stop prevents template writes. Qualification tool paths come
from the frozen Nix input rather than a remembered store path. Idle measurement
requires an explicit verified eight-gate functional bundle; measurement outcome,
final adjudication, and recovery status are separate fields.

The revised DH driver checks finalized fresh-client SQLite copies and pairs a
bounded distant gold-block landmark update with partial-update telemetry and
changed terrain-data fingerprints. It verifies original air blocks and restores
them before accepting the run. The restore driver requires aggregate useful server DH data in the stopped
recovery clone before boot and binds server SQLite checks,
fresh DH data responses, and client SQLite usefulness alongside the ordinary
client test. These stronger drivers still require fresh authoritative runtime
qualification before a new Phase-A conclusion. C2ME release
selection will re-query the official Fabric 26.3 release source instead of
assuming the historical requested version exists.

## Revised DH idle attribution policy

The authorized continuation replaces the historical 1% binary DH idle gate with
paired CPU and package-energy attribution before adopting a production change. The
checkpoint `31bf61c3bab50954ef283e31ec08b53c5426b240` is preserved remotely on
`wip/minecraft-server-performance-dh-idle`. Historical failed samples remain
evidence of their original gates, rather than being retroactively marked PASS.

Exactly eleven valid paired, fresh-JVM runs use equivalent writable snapshots of the
frozen world, identical non-DH mods, 1/8 GiB G1 heaps, 10/12 GiB cgroup limits,
normal 60-second empty pause, 90-second settling, and 600-second intervals.
Pair order alternates. Clean acceptance reads cgroup CPU directly, package RAPL,
memory events, cgroup I/O and aggregate host CPU; samples stay in memory until
the interval ends. It performs no JFR recording, thread scans, `jcmd`, per-sample
`systemctl`, cpuidle scans or persistent sample writes. Diagnostic attribution
runs occur only after a definitive clean resource failure, with per-thread CPU,
Java dumps and memory-backed JFR.
All raw measurements and world/database identities stay outside the repository.
Logical-CPU idle residency is supplemental evidence, not package C-state proof.
Real-time updates, synchronization on load, generation, and all optional server
features are disabled in separate disposable diagnostic variants only.

Acceptance requires the median of DH-on interval-average CPU measurements at
most 5% of one core, median run p95 CPU at most 10%, and the upper nominal 95% Student t
bound of mean paired package-power increase at most 1 W. The fixed design analyzes
once after all eleven valid pairs; it has no inferential looks at pairs 5/7/9.
An interval whose lower bound exceeds 1 W fails; a straddling interval remains
INCONCLUSIVE. The interval assumes independent paired deltas with approximately
normal run means; fixed sampling does not eliminate host confounding or model
uncertainty. Raw deltas, range and median accompany the primary mean. The method
follows [NIST mean confidence limits](https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm). These CPU limits
are project budgets rather than upstream DH guarantees. Normal
pause, no continued generation, sustained database growth or disk I/O, memory
pressure/OOM events, or unbounded work queues. No correctness, backup or recovery
gate is relaxed. Confounding host load or inconsistent controls require a
methodology correction before attribution or acceptance. A pair is invalid if
unrelated host CPU differs by over 0.5 percentage points between run medians,
unrelated host p95 exceeds 5% or maximum exceeds 20%, or a Minecraft client
overlaps the run. At most three fresh-pair environmental retries are allowed.
Memory or world/database mutations are failures and are not retried as noise.

The disposable `minecraftperformance.slice` is a top-level sibling of the
production slice with CPU/IO weights 50; benchmark services use Nice 5 and the
same memory limits. Slice names containing hyphens would imply nesting.
RAPL must identify enabled `package-0` with a readable positive counter range;
reset-like decreases or physically implausible readings invalidate the data.
Burst statistics accompany interval accounting rather than replacing it.

I/O acceptance requires zero p95 read/write rates, unchanged world/database
content, no discards, and no DH-on read excess. The control reveals unavoidable
JVM performance-counter writeback, approximately 4 KiB every 30 seconds. DH-on
writes may exceed matched control by at most four metadata pages (16 KiB); this
allows intermittent JVM bookkeeping without waiving sustained DH database work.
Functional compatibility, backup, restore, identity restart, queue behavior and
Chunky-to-normal-DH catch-up remain separate required gates in the final
adjudicator. Passing resources alone cannot accept DH or unlock C2ME.

The profiled and environmentally confounded pilot runs remain excluded. This
host-specific harness and chronology are disposable qualification machinery:
before PR creation remove them, move durable operating results to
`docs/minecraft-server.md` and `docs/status.md`, and preserve detail in Git/PR
history. Performance clients retain only the frame probe; packet logging is
reserved for functional acceptance. The existing backup architecture is unchanged.

The latest review interrupted the first partial clean run in the `20261011g`
experiment; it is excluded before qualification under the revised provenance
requirements. Nix now evaluates an exact committed Git revision to produce
candidate paths, JVM flags, generated policy files and service limits. The
enriched manifest hashes all mod and policy artifacts and records the readonly
baseline filesystem/subvolume UUIDs and immutable content manifest. Its canonical
SHA256 is the qualification identity. Functional proofs must bind that identity,
Git revision, named gate, test-source hash, baseline UUID and nonempty hashed
evidence array. Historical correctly hashed PASS receipts cannot qualify a new
candidate. World fingerprints precede the 90-second settling period.

Authoritative package-power comparisons temporarily stop production and its
backup timer after a verified recovery point. An independent 45-minute recovery
timer is installed before either stop, refreshed before each bounded run, and
retained until restoration and live backup health succeed. Normal exit,
exceptions and SIGTERM restore production and remove the disposable slice.
Unexpected slice definitions or occupied recovery unit names fail closed.
The revised runner has not yet completed authoritative paired qualification;
functional restart, post-Chunky catch-up and bounded queues remain unproven.

The provenance/decision checkpoint passed 35 Python performance tests, the
Minecraft configuration check (including prerequisite, identity, management and
backup suites), Nix formatting and disposable probe compilation. The client
frame probe now preallocates a raw-long buffer, formats CSV only after the
measurement, and fails on overflow; its standalone Java test verifies bounded
storage and conversion. Independent MangoHud agreement is still unproven.
The abandoned slice from earlier pilots was stopped and its exact known unit
definition removed; production and its timer remained active throughout these
implementation checks. These are local checks, not runtime gate or CI evidence.

The committed manifest generator and independent recovery timer passed live
preflights against checkpoint `c0643544e7c348ddc430c8270ffd375457a73277`.
The preflight manifest identity is
`72186dafed27f2a2469982f4bad869e905fc61336926a08d58ed265a57eb79ae`;
it is explicitly excluded from acceptance because the functional drivers are
not yet complete. The guard armed, restoration verified both production units
and live backup health, and both transient guard units unloaded after disarming.
Production was not stopped during this preflight.

The terrain parser now distinguishes explicitly verified zero-byte region shells
from actual chunk entries and nonempty unexplained regions. It parsed the fixed
readonly baseline's 16 region files and 4,964 terrain/entity/POI entries; this is
parser preflight evidence, not a terrain-generation PASS. Valid final sectors may
end at the payload rather than a sector boundary; truncated payloads still fail.

A disposable one-shot Java attach agent reads DH 3.3.4's concrete update,
retrieval, request, delayed-save and executor counters. It writes snapshots to
private tmpfs and is reserved for functional queue experiments; authoritative
clean idle samples never attach it. The executable convergence policy requires
180 seconds of stable zero queues, unchanged database fingerprints and resources
within the project idle budget, inside a 900-second observation bound, with
10,000 a conservative backlog ceiling for the bounded workload. Missing counters,
changed queue identities or observation gaps remain INCONCLUSIVE. Persistent
backlog, growth, I/O or CPU at the timeout fails. Forty Python tests and updated
probe compilation pass; queue observation and post-Chunky runtime remain unproven.

The live counter preflight subsequently read 47 counters across three loaded DH
levels, all zero in that single snapshot. Its first attempt was excluded after
the private tmpfs directory inherited mode 0700; applying explicit mode 0750
allowed service-user access. Both attempts stopped their disposable server and
left production active. This verifies counter access, not workload convergence.
The manifest now includes the exact Chunky maintenance inventory and generated
DH-disabled policy. A disposable lifecycle helper preserves DH identity while
replacing the sparse Nix policy across maintenance and normal restarts; its
cleanup tests cover identity failure and occupied units. The timed observer
includes SQLite parent/child/regeneration backlog flags and hashes database/WAL
content. Forty-two Python tests, probe compilation, Nix formatting and the
Minecraft configuration check pass. The post-Chunky driver and its complete
runtime acceptance remain pending; no authoritative clean pair has completed.

The post-Chunky executable driver now specifies a square centered at block
8192/8192 with radius 256, outside the fixed baseline's generated region. It
requires a machine-parsed 100% completion marker, at least 1,024 new terrain
chunks inside the bounded extent, the DH-disabled maintenance policy, normal
PRE_EXISTING_ONLY/CHUNKS_ONLY after restart, unchanged DH identity, no added
normal-mode region/chunk entries, and the timed convergence gate. It writes
qualification-bound receipts only after those observations. Runtime remains
unproven until this driver executes against a newly frozen manifest.

The queue agent now attaches once and observes for at most 910 seconds, avoiding
repeated JVM attach warnings in measured server I/O. Its snapshots are atomic
tmpfs replacements, with sequence checks and a stop marker. One-second resource
samples remain separate from ten-second queue/database observations, so a
periodic JVM metadata write is not misclassified as sustained I/O by coarse
sampling. The exact agent is built by Nix from the frozen Git source and hashed
into the candidate manifest; arbitrary externally supplied agent JARs are
rejected. Forty-four Python tests and the Minecraft configuration check pass.

The guarded runtime pilot at committed checkpoint
`acb6cf14fcb0eeb70490b582663a3885007d975b` passed identity restart,
post-Chunky behavior and bounded queues under qualification identity
`d0fa283dd0cb1afe45945945cb7312a5371d828982ebfc310359404ce0282bfe`.
Chunky processed 1,089 requested chunks; the bounded generation halo added
3,025 terrain chunks. Normal zero-player DH added no terrain entries and showed
no unsolicited backfill. Nineteen ten-second observations established a full
180-second quiet interval by 190.21 seconds, with stable zero queues/database
content and accepted one-second CPU/I/O samples. All three proof references
passed the manifest-bound verifier. This proves the bounded zero-player workload;
active client synchronization remains a separate gate.

The controller exited successfully, production and its backup timer restarted,
and live backup verification passed with health `ok`. The original system closure
remained active. Both recovery units and the functional service unloaded, and the
disposable slice stopped with its runtime definition removed. Raw evidence is
retained privately under
`/persist/minecraft-performance-functional-catchup-pilot-acb6cf1`.
These receipts certify only the named frozen identity; they do not certify a later
Git revision, complete DH acceptance, authoritative paired idle, CI or merge.

The next review supersedes adaptive stopping with a fixed eleven-pair mean-power
experiment. The runner records that sampling plan before measurements and the
analyzer refuses early/incomplete batches. Authentic FAIL and INCONCLUSIVE proofs
now retain their outcomes; tampered/stale evidence remains UNPROVEN. The committed
gate-source mapping adds external dependencies to a conservative shared set of all
performance-tool sources, and runtime validation rechecks every gate source.
The deterministic eight-gate aggregator rejects duplicates, missing gates and
mixed identities, preserves outcomes, and produces a canonical readonly bundle.
Historical partial bundles cannot qualify through that path.

The post-Chunky extent now derives requested full-chunk bounds from block center
and radius: 496–528 inclusive for this workload. It rejects pre-existing target
entries. Both root `region/` and the observed Minecraft 26.3
`dimensions/minecraft/overworld/region/` layout have regression coverage.
Offline inspection of the previous pilot found exactly 1,089 full chunks inside
those bounds. Its other 1,936 entries are unfinished dependency chunks. A Java
source helper now reads the pinned game's own accumulated generation radii:
full/light/spawn 0, features/initialize-light 1, terrain 2,
biomes/structure-references 3, structure-starts/empty 11. These radii and their
classpath/source hashes enter the frozen manifest. The region parser independently
checks NBT status and coordinates. Full chunks outside the requested bounds,
unknown stages, or protochunks outside their stage-specific dependency bounds
fail; there is no blanket ±32-chunk exemption. Normal-mode status promotion is
also a generation failure. This is a methodology correction supported by the
pinned game's own dependency graph, not a weaker terrain gate.

Queue observers now use unique invocation directories, acknowledge termination,
and remove only canonical directories with the recorded inode/device/owner and
known regular files. Missing acknowledgement retains exact evidence without
poisoning the next attempt. Client provenance can freeze both disposable profile
inventories/configuration and the 77 library JARs without reading account files.
It recompiles probes to reject a stale binary paired with current source hashes.
The bounded GUI lifecycle checks actual JVM ownership/collector/heap; independent
recovery stops that client before restoring production. Client execution and the
five remaining functional adjudicators are still pending. All affected gates
must be rerun under a new committed manifest before authoritative resources.

The review-fix checkpoint passed 60 Python tests, disposable probe compilation,
Nix formatting, the full flake check (including Statix/deadnix and Minecraft
configuration/backup checks), and the desktop toplevel build. The game dependency
helper runs in a temporary working directory to keep its logging outside the
repository. These are local checks; fresh runtime gates and exact-head PR CI
remain required.

If DH fails these limits, test one exact pinned upstream Minecraft 26.3 build.
Only demonstrated thread/method costs justify one bounded idle-aware backoff
patch attempt. An invasive permanent fork is rejected: omit server-side DH,
document the rejection, and continue independent Krypton, C2ME and collector
qualification. No production DH feature is silently disabled to pass a test.

## Earlier failed attempt

The 2026-10-11 run ended with **FAIL** during isolated Krypton/DH runtime testing.
The benchmark setup copied its DH policy file with mode 0444 and root ownership;
the Minecraft service user could not write it. DH then threw a
`NullPointerException` during configuration loading. This is a benchmark setup
failure, not evidence that the production candidate or upstream mod is unsafe.
The required phase nevertheless did not pass, and no later phase was attempted.

Before that failure, static Minecraft checks, the existing Python suites,
formatter, statix, deadnix, flake check and desktop build passed. Disposable
clients launched automatically, received frame instrumentation, obeyed scripted
spectator/teleport commands and exited cleanly. The transient production candidate
accepted both DH and non-DH clients; the DH client logged receipt of a level-init
message. These partial results do not certify full DH synchronization, real-time
propagation, isolated restore, C2ME or collector acceptance.

The recovery guard restored the original system and started the production
service and timer. Its embedded backup check lacked an executable search path;
an independent `minecraft-backup status --live` then passed. The guard is stopped,
all disposable clients and test servers are stopped, and production again uses
the 6 GiB heap and 8/10 GiB cgroup envelope. No PR was merged.

The machine-readable failure report and evidence digests are retained in
`/persist/minecraft-performance-agent/final-result.json` and
`/persist/minecraft-performance-agent/evidence-manifest.json`. The agent's state
path under `/var/lib/minecraft-performance-agent` points to this persistent
directory. The isolated worktree, fixed baseline snapshot, failed clone and raw
logs remain available for diagnosis.

## Corrected qualification attempt

The benchmark installer now copies template contents, inherits the destination
directory's service ownership and applies mode 0660. Regression tests cover a
read-only source and reject symlink destinations. The recovery guard's executable
search path was corrected and its complete restoration/backup check passed.

The corrected isolated server accepted a clean DH client for three minutes.
Its probe recorded session configuration, level initialization and non-empty
full-data responses. A reversible 21-block landmark change outside the client's
eight-chunk vanilla render radius was followed by 20 partial-update messages;
the client database changed and passed SQLite integrity checking. This accepts
the real-time data path, not subjective visual appearance.

Normal `PRE_EXISTING_ONLY` / `CHUNKS_ONLY` operation created 31 zero-byte region
file shells. Inspection of the pinned DH `RegionFileStorageExternalCache` shows
that its read path checks the parent directory, then constructs a `RegionFile`
without checking whether that individual file already exists. These are explained
read-side artifacts containing no generated chunks. They must be distinguished
from non-empty distant region creation when assessing this gate.

All three server DH databases from the actual production backup passed integrity
checking on copies. An isolated writable restore booted successfully and served
a fresh client cache: 1,371 full-data responses, a 9,486,336-byte healthy client
database and 1,581 `FullData` rows. The 325 exception responses were all
`SectionRequiresSplittingException`; the pinned client's request queue handles
these by completing a split result. No unexpected exception type was recorded.
The restored server also accepted the no-DH client for 45 seconds, completed a
scripted teleport and observed its clean disconnect.

The updated Minecraft config check includes the analysis/setup Python tests and
the Java tick-buffer fixture test, alongside all existing safety tests.

The production idle sample then failed the phase gate: median service CPU was
1.329% of one core across 300 seconds, p95 was 3.878% and maximum was 8.793%.
The required median limit is 1%. All memory-event deltas remained zero. The
original system configuration was restored, the production service and backup
timer are active, and the corrected recovery guard's embedded live backup check
passed. The generated-identity restart was not accepted as a completed gate.
C2ME and collector experiments remain unstarted.

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

The subsequent conservative DH policy (two workers, runtime ratio 0.5) also
failed paused-idle acceptance: across 300 seconds after a 90-second warmup,
median service CPU was 3.259% of one core, p95 4.284%, and maximum 12.776%.
Host CPU median was 2.848%; all cgroup memory-event deltas were zero. The
required limit remains 1%. Thread diagnostics retain activity in DH request
and update queues, but do not establish a complete causal explanation.
Production was restored to the original safe closure; the server and backup
timer are active and live backup verification passed. C2ME and collector
experiments remain unstarted. Shutdown captured the generated DH identity
unchanged; a complete candidate restart identity test remains unproven.
Raw samples and diagnostics are retained under the private evidence root as
`attempt-3-idle`, `attempt-3-thread-cpu.json`, and `attempt-3-thread-dump.txt`.

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
