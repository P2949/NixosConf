# Minecraft Chunky runtime inspection — 20 October 2026

**Verdict: PARTIAL PASS, with a confirmed failure of the online-pause policy.**
Current empty-server generation, target application and backup health are working.
The production log also proves that an Overworld task continued for over 18
minutes while players were online. The system cannot currently be described as
fully correct.

## Scope and provenance

- Live observations: **22:37:41–22:39:06 Europe/Dublin (UTC+1)**.
- Reviewed log: current server process, starting at 20:47:19; captured through
  22:39:06. PID **421584**, active throughout inspection.
- Checkout: clean `main` at `68fce4386f3de14a9877090334f0c6bd9e1b5b2c` (PR #55).
- Active closure: `/nix/store/6ir758m1m5j3rbqd17i020v63dzh0bsi-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Installed Chunky is **1.5.3**, with its pinned SHA-512 verified. All **15** live
  controller mcfunctions match the merged checkout byte-for-byte. Artifact hashes,
  sanitized log analysis and numeric observations are in the accompanying
  [evidence JSON](minecraft-chunky-runtime-2026-10-20.evidence.json).
- Observation used MSMP player/status queries, console `data get`, scoreboard
  reads and `chunky progress`, log/file inspection and cgroup counters. It did
  not pause/cancel/start tasks, reload the pack, restart the server, teleport
  players, alter settings or take a new backup. No performance campaign was run.

## Findings

| Area | Result | Evidence |
| --- | --- | --- |
| Installed implementation | PASS | Pinned Chunky and all 15 merged controller functions verified live. |
| Empty-server transition | PASS for observed transition | Last player left at 22:29:47; all three dimensions progressed at 22:29:48. |
| Current generation | PASS | No players connected; all three task counts increased during the live window. |
| Target application | PASS for observed state | Overworld and Nether have new activity-centered targets; End retained its prior center. All pending flags are clear. |
| Pause all work while players are online | **FAIL** | Overworld progressed from 20:48:49 to 21:07:15 with one, then two players connected. |
| Multiplayer candidate ownership | INCONCLUSIVE from this inspection | Applied candidates have no owner field by design; no intermediate per-player samples or owner transitions are retained in this log. |
| Task checkpoint freshness | INFORMATIONAL | Saved task files describe old/stopped jobs; live progress and controller state describe the current jobs. |
| Resource ceiling | PASS for observed window, soft-limit reclaim active | No hard-limit/OOM events; usage near MemoryHigh, predominantly file cache. |
| Backup health | PASS | Live audit healthy, no problems, 14 retained snapshots, timer active. |
| World/block-entity errors | INVESTIGATE | One logged chest/brushable-block mismatch during asynchronous saving; cause and persistence are unproven. |

### Current targets and progress

All dimensions are enabled with `hasTask=1` and `pending=0`. Last activity equals
its applied center. Owner fields are absent, as expected after
[replacement consumes a candidate](../../hosts/desktop/minecraft/chunky-offline/replace.mcfunction).
`#online=0` agrees with MSMP's empty player list. `#ticks=180` was unchanged
between observations, consistent with tracking advancing only while online.

| Dimension | Center X,Z | Radius / deadzone | Processed at 22:37:47 | Processed at 22:39:06 | Increase | Final completion |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Overworld | 12009, 7895 | 10000 / 7500 | 89,370 | 115,553 | 26,183 | 7.38% |
| Nether | 1488, 975 | 1250 / 938 | 14,162 | 14,416 | 254 | 57.02% |
| End | 1000, 0 | 5000 / 3750 | 206,443 | 209,920 | 3,477 | 53.40% |

The last instantaneous reported rates were 210.7 / 4.7 / 163.2 cps respectively.
These are Chunky's own samples, not controlled benchmark results. Its ETAs were
1:54:38 / 0:38:11 / 0:18:42 and varied substantially; they are not completion
promises. Processed positions can include skipped, already-generated chunks.

The earlier Overworld target completed at 21:07:15. Current low Overworld
completion refers to a **new target**, not loss of the old world's generated
chunks. On the final logout, Overworld and Nether began new tasks while End
continued from approximately 137,400 processed positions. That is consistent
with replacing affected dimensions and preserving unaffected work.

### Confirmed online-pause failure

The log contains this sequence (line numbers refer to the captured log snapshot):

```text
313  20:48:49  First player joins.
314  20:48:49  End task stops.
315  20:48:49  Overworld continues: 220,656 processed (14.10%).
316  20:48:50  Overworld continues: 221,976 processed (14.18%).
350  20:49:21  Second player joins; first player is still online.
1469 21:07:15  Overworld continues: 1,564,988 processed.
1470 21:07:15  Overworld finishes: 1,565,001 processed (100%).
1475 21:11:03  First subsequent player departure.
```

There are **1,085 progress messages while at least one logged-in player is
present**, reconstructed from successful join/leave events. They are all
Overworld updates. This is sustained processing, not a few callbacks draining
after pause: the count advances by at least 1,344,345 positions before finishing.
It does not prove that every position required new terrain generation.

End stopping at the first join shows that the controller's online transition
ran. Overworld continuing shows that the intended all-task pause did not hold.
Earlier smoke acceptance is insufficient to dismiss this production failure.

### Lifecycle investigation: likely race, not a proven root cause

The controller currently performs cancel/confirm/start/confirm within one
[replacement function](../../hosts/desktop/minecraft/chunky-offline/replace.mcfunction),
then issues a global continue in its
[empty-server handler](../../hosts/desktop/minecraft/chunky-offline/offline.mcfunction).

Inspection of the **pinned 1.5.3 bytecode** shows that stopping a task sets flags
and returns; cleanup later saves the task and removes its world-name entry.
Cancellation removes the old entry, while a new start can register a replacement
before the old cleanup finishes. This creates a plausible race in which old
cleanup removes the replacement's registration. A running task absent from that
registry could escape the global pause. Upstream's
[GenerationTask implementation](https://github.com/pop4959/Chunky/blob/master/common/src/main/java/org/popcraft/chunky/GenerationTask.java)
and [PauseCommand](https://github.com/pop4959/Chunky/blob/master/common/src/main/java/org/popcraft/chunky/command/PauseCommand.java)
show this lifecycle structure; matching behavior was checked in the installed
version rather than assuming current upstream equals the pin.

A plain duplicate continuation is **not established**: the pinned
[ContinueCommand](https://github.com/pop4959/Chunky/blob/master/common/src/main/java/org/popcraft/chunky/command/ContinueCommand.java)
checks whether the world is already registered before starting it. The
cancellation/cleanup interleaving needs an isolated reproduction before assigning
root cause or selecting a fix. No fix or runtime workaround was applied here.

### Resource observations

The service retains `minecraft.slice`, Nice 5, C2ME parallelism 4, MemoryHigh
10 GiB and MemoryMax 12 GiB. Empty-server pausing remains -1. Chunky has
`continueOnRestart=true` and `forceLoadExistingChunks=false`.

- Cgroup current memory: 10,735,894,528 bytes (~10.00 GiB); lifetime peak:
  10,738,343,936 bytes, just above the **soft** threshold.
- A nearby breakdown showed ~7.35 GiB file cache and ~2.50 GiB anonymous memory.
  Cgroup usage is not Java heap usage; these numbers do not establish a heap leak.
- `memory.events.high` increased from **3,533 to 3,617** during inspection.
  This indicates soft-limit reclaim activity, not OOMs or hard-limit failures.
- `max=0`, `oom=0`, `oom_kill=0`; cgroup swap usage was zero.
- Memory pressure some/full avg10, avg60 and avg300 were 0.00 at the final sample.
  This short observation does not establish long-term resource capacity or
  smooth gameplay, and does not justify changing the memory envelope by itself.

### Saved files, backups and the separate world error

The saved Overworld task file still records the old -267,93 target and
`cancelled=true`; Nether records its old 0,0 target and `cancelled=true`. End's
saved count is 137,400. The active controller and live task counts differ because
these files are checkpoints updated when tasks stop/finish, not a live inventory.
No restart was performed to test checkpoint recovery during this inspection.

`minecraft-backup status --live` reports **health=ok**, **no problems**, live
verification **passed**, and **14** registered recovery points. The latest
snapshot is `survival-20261020T194652213923Z` (20:46:52 Dublin). The enabled timer
reports its next activation as **21 October, 01:00 Dublin / 00:00 UTC**. This is a
health/schedule check, not new proof of a future calendar activation or a restore.

At 20:50:57 the log reports one ERROR: a `minecraft:brushable_block` block entity
was associated with a chest at **-9224,43,-5323**, raising IllegalStateException.
The stack reaches C2ME asynchronous chunk saving. That identifies the execution
path, not the cause: this inspection does not establish whether the mismatch
predates the controller, persisted to disk, or caused data loss. Do not label it
world corruption, or attribute it to a particular mod, without further evidence.

## Recommended follow-up

1. Treat the online-pause failure as the highest-priority functional correction.
   Reproduce startup with an existing pending recenter and delayed old-task
   cleanup in a disposable world; verify every dimension stops on join after
   replacement. A task-registry-only progress check may miss an unregistered task,
   so also check continuing log counts.
2. Ensure replacement is sequenced after old-task cleanup, then validate
   pause/resume across replacement and restart. Keep this bounded; there is no
   evidence here requiring a scheduler or performance campaign.
3. Investigate the isolated block-entity mismatch separately using the location
   and saved evidence, with the existing backups retained.
4. To establish the ownership fix under real multiplayer use, observe candidate
   UUID/position before and after the remote player's departure and genuine
   return. Final applied centers alone cannot prove which player supplied them.

The server and generation were left running unchanged. Only this report and its
sanitized evidence file were added to the repository worktree; no source,
configuration, backup policy or task-control state was changed by the inspection.
Read-only queries added their normal console/management log entries. The raw log
snapshot is retained locally at `/tmp/chunky-runtime-log-snapshot.txt` (mode 0600);
it is not committed because it contains player connection addresses.
