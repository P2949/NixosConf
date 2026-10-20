# Chunky task-retirement correction — 20 October 2026

Status: **PASS for local qualification, isolated forced-race acceptance and deployed production pause/resume acceptance.** Required exact-head GitHub Flake checks passed; PR #56 merged as `278578feabbb7b882b80cedfd97f9f9f879bb47a`. Optional integration and desktop CI jobs were still running at merge, by repository design; local desktop qualification passed.

Implementation: commit `bf2ec87`, [PR #56](https://github.com/P2949/NixosConf/pull/56), based on merged main `68fce4386f3de14a9877090334f0c6bd9e1b5b2c`. This deployed correction supersedes the failed online-pause acceptance in the [runtime inspection](minecraft-chunky-runtime-2026-10-20.md). The historical failure and failed baseline evidence are retained.

## Scope

Only Chunky 1.5.3's `GenerationTask.class` changes. The pinned upstream source must compile to the upstream class's exact `javap -c -p` disassembly before applying the patch. The regression checks every JAR entry and permits exactly this one changed class. No controller function, C2ME setting, target/radius, JVM/resource setting, backup policy or timing policy changes.

Retirement uses a per-world `ConcurrentHashMap.compute`: only the currently registered task may save its checkpoint and remove itself. The save remains inside the atomic operation, so a replacement cannot register between the identity check and the save. An old worker cannot erase a replacement or overwrite its checkpoint.

## Deterministic reproduction

A disposable loopback-only Fabric 26.3 server used the existing production mod set and controller, with a test-only gate immediately before the cancelled Overworld worker's retirement. The gate held old A at center 0 until the controller's real pending-recenter path registered replacement B at 9000,0. Releasing A then forces the otherwise timing-sensitive interleaving. The gate is absent from the production JAR.

Unpatched 1.5.3: **EXPECTED FAIL**. After A retired and a player joined, the replacement processed **747 additional positions** during a six-second online observation after a two-second grace period. Its checkpoint was overwritten by cancelled A at center 0. This reproduces both production symptoms rather than relying on registry queries alone.

The [baseline receipt](chunky-retirement-2026-10-20/baseline-result.json), [console log](chunky-retirement-2026-10-20/baseline-console.log), test-only gate source, driver and fixture hashes are retained in the accompanying evidence directory. The driver records machine-local paths and is an execution receipt, not a new production tool.

## Regression and qualification

- Focused Java regression: **PASS**, using actual Chunky tasks, registry and TaskLoader. Late A preserves B and B's saved target; normal paused B removes itself and remains restartable; later unregistered A cannot overwrite it. Unpatched JAR failed this regression.
- Formatting: **PASS**.
- Patched actual controller path: **PASS**. All three stop messages observed after join; raw online progress changes empty; all three resumed after disconnect; restart retained replacement Overworld center 9000,0. See [receipt](chunky-retirement-2026-10-20/patched-result.json) and [console log](chunky-retirement-2026-10-20/patched-console.log).
- Full flake check: **PASS**, all checks passed on committed source.
- Desktop toplevel build: **PASS** on committed source.
- Pre-deployment snapshot and switch: **PASS**. Snapshot `survival-20261020T220653031803Z`; active closure `/nix/store/hk7j8hmlsymdxnw4v7wskypka5rwd9zd-nixos-system-desktop-26.05.20261004.0d9e9b8`, PID 946304, ready 23:07:34 Dublin. Installed patched JAR SHA-256 `587bed76626952407d9caf9437cd0e88b66830ae2ee826c53a4a31d441654299`.
- Production raw-count pause/resume and backup acceptance: **PASS**. Player joined at 23:08:37 Dublin; Overworld emitted its stop message immediately. Between 23:08:58 and 23:09:18, unsolicited raw progress remained 468,153 and the paused checkpoint remained 468,368, with one join and no disconnect throughout. Read-only progress reported no running tasks. The difference between the last periodic message and the checkpoint reflects work completed before retirement; it did not advance during the observation. After disconnect at 23:09:55, unsolicited progress resumed at 468,420 and reached 468,941 at 23:09:57. The saved target stayed 12009,7895, radius 10000. See [online samples](chunky-retirement-2026-10-20/live-online.json) and [production log](chunky-retirement-2026-10-20/production.log).
- Post-deployment ordinary snapshot: **PASS**, `survival-20261020T221004661582Z`. Backup live verification passed, health OK, no problems, no retention backlog, 14 managed snapshots. Timer remained active. See [status](chunky-retirement-2026-10-20/final-backup-status.json).

Earlier patched fixture attempts are retained under `/tmp/chunky-retirement-patched` and `-patched-rerun`: the first used too short a spontaneous-log observer for resumption; the second let the test player spawn outside the replacement deadzone, legitimately triggering a further recenter. The final fixture queries raw progress on resume and places its spectator at the intended replacement center before disconnecting. These are fixture corrections; production controller code was unchanged.

## Separate world investigation

The [read-only block-entity report](minecraft-block-entity-2026-10-20.md) confirms the chest/brushable-block mismatch existed before PR #54's deployment. It does not establish the original cause or prove a correct live repair. No world repair or regeneration was performed.

Production's Nether target finished at 22:49:33 and its End target at 23:04:30,
before this switch. Their completion messages reported 25,281 and 393,129
positions respectively. Only Overworld is active after restart; the live join
acceptance therefore applied to that remaining task. The isolated forced-race
test above covered three simultaneously active dimensions.

## Final repository and deployment reconciliation

PR #56 merged at 22:10:50 UTC as `278578feabbb7b882b80cedfd97f9f9f879bb47a`.
Its required **Flake checks** succeeded on exact head
`bf2ec87eba1bd84cfecd5d1bdd5edf3eb17892c6`; the optional jobs did not gate merge.
At deployment completion, local `main` and `origin/main` both resolved to the merge commit, and their full
tracked tree matches the tested head. A desktop build from merged main returned
**the exact already-active closure** listed above. No second activation or restart
was necessary; server PID remained 946304. Report artifacts are retained under
`docs/reports/` in a separate evidence commit, outside the focused six-file production PR. Generation is left
running; no completion polling or performance campaign continues.


## Goal completion audit

The preceding implementation turn made verified progress through the merge,
deployment and live acceptance. The final audit read the complete goal objective
and inspected the implementation, receipts, raw logs, current GitHub PR state,
active closure and installed JAR. Its requirements are satisfied as follows:

| Requirement | Authoritative evidence | Result |
| --- | --- | --- |
| 1. Reproduce the original replacement race first on Fabric 26.3 | Baseline gate source, driver, console log and result: old worker released after replacement registration; 747 online positions and overwritten checkpoint | PASS, expected baseline failure |
| 2. Patch only pinned Chunky retirement; preserve controller and resource/backup policy; no timing workaround | Six-file production diff; pinned source/JAR; retirement patch; archive regression permits only GenerationTask.class to change | PASS |
| 3. A retiring behind B must preserve B and its lifecycle | Actual Chunky/TaskLoader Java regression source and passing regression log | PASS |
| 4. Real pending-recenter controller path pauses every active dimension, then resumes | Patched console log and result: all three stop on join, no raw online progress, all three resume on logout | PASS |
| 5. Replacement target survives restart | Patched driver assertions, receipt and post-restart log retain center 9000,0 and resume all three dimensions | PASS |
| 6. Regression, flake check, desktop build, snapshot, switch and short production acceptance | Qualification logs, required exact-head GitHub check, active closure, snapshot receipts, live samples, production log and healthy backup audit | PASS |
| Separate read-only block-entity comparison before the error; no repair or causal attribution | Separate report and decoded evidence compare the exact coordinate with stable live reads and read-only snapshots; mismatch predates PR #54 | PASS |
| Commit or clean the remaining changes before completion | Reports, failed baseline, passing evidence and fixture sources retained in a separate evidence commit; final worktree checked clean | PASS |

Nether and End were already complete during live acceptance; the production
check covered its sole active Overworld task. The isolated test supplied the
required all-three-active coverage. Optional remote integration and desktop CI
jobs were not treated as required gates or claimed successful at merge.
