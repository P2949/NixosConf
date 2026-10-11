# Current status

The **productive desktop** is current `main`, including accepted Prism Launcher
integration through [PR #16](https://github.com/P2949/NixosConf/pull/16).
It advances independently of the immutable **qualification baseline** in the
[canonical baseline](baselines/pre-optimization/baseline-final.md) and the frozen
**benchmark control** in [stock policy](stock-policy.md).

## Storage and recovery

`@root` contains ephemeral root, home and ordinary var. Explicit retained state
is backed by `@persist`; separate mounts retain `@nix`, `@snapshots` and
`@optimization`, plus ESP and swap. Legacy home/var subvolumes are retired.
See the [persistence contract](persistence-contract.md).

Recovery uses Nix/GitHub/reinstall, separately tested secrets recovery and a
small local-only exception archive. The recovery ISO remains verified.
See [backup and recovery](backup-restore.md). The additional final-runtime soak
was disregarded by human intervention; it is not a measured PASS.

## Productive policy

The accepted CPU package baseline is 125 W PL1/PL2, with boot/resume application.
Commander Core retains the accepted cooling policy. Bluetooth is disabled.
The optimization-v2 framework is merged. The productive desktop has advanced
beyond the frozen benchmark control. No optimization
derivation is installed into the productive system. Accepted display/audio/workload
and recovery evidence remains bound to the baseline closures.

## Development phase

The optimization-v2 experiment foundation is merged. No optimization candidate
has been adopted into the productive desktop.

The first authoritative package experiment,
[`zstd-skylake-v1`](../optimization/results/zstd-skylake-v1/), found
compression inconclusive at the declared practical threshold and a material
decompression regression. The candidate was therefore not adopted.

Prism Launcher implementation is accepted; source integration is tracked by
[PR #16](https://github.com/P2949/NixosConf/pull/16). See the
[permanent state audit](ephemeral-state-audit.md). Its persistence policy retains
the private launcher root with audited disposable cache/log overlays. Normal boot, launcher/Java and real vanilla world
validation pass; refreshed account online features are user-confirmed. Cache/log
exclusions pass normal-reboot persistence/reset and retained-file hash proofs.
Post-reboot Fabric world, retained settings, graphics/input/audio and absence
of full assets/library downloads are user-confirmed. Proof and approved old
cache/log cleanup and final local source checks pass. Exact-head CI and merge
evidence are recorded in PR metadata.
Ordinary desktop changes may proceed while the immutable benchmark
control and experiment admission gates remain protected.

Further optimization investigation is intentionally deferred. General
repository organization is finished under the [repository policy](repository-policy.md).
Generated custom-module documentation and the [interactive desktop bootloader
VM](development-validation.md#interactive-desktop-vm) are explicit developer tools.
The VM retains desktop composition with adapted storage and hardware; it does
not replace accepted physical qualification.

## Minecraft server

The Minecraft server and complete local Btrfs recovery scope are deployed on
the desktop. The normal server and six-hour UTC backup timer are active. See [Minecraft operations](minecraft-server.md).

Real paused/online backups, autosave failure recovery, safe retention and a
user-verified playable local restore passed. The latest helper rejects nested
subvolumes and mountpoints, syncs before publishing success, and reconciles only
one interrupted deletion before fresh capture. Live snapshot integrity is healthy.
Full flake, desktop and bootloader VM qualification passed. Spark background
profiling is disabled; VM disable isolation and the one-server invariant hold.

Normal → pregen → normal switching passed with a bounded 25-chunk Chunky run
and manual backups. A backup during a VM build took about 2.1 seconds, including
0.325 seconds of filesystem sync; the user reported no stalls so far. Isolated
IPv4/IPv6 peers verified game status/ping access and unavailable management/RCON.
The unavailable laptop's actual LAN/gameplay path remains an unexercised,
recommended operational smoke test rather than a branch-merge blocker.

Actual reboot persistence passed: the normal configuration booted, the stamp
remained a real file bind mount with its persistent inode/timestamp unchanged,
and seed/server/timer started successfully. Ordinary calendar-event acceptance
is a user-approved post-merge observation; its live observer was cancelled.
Production scheduling remains active. Genuine missed-event catch-up is also a
post-merge observation. Neither test is claimed as passed. Disposable acceptance snapshots were cleaned up;
raw cleanup/reboot identities remain in local root-only receipts.

Local Btrfs recovery is the complete Minecraft backup scope. Total device loss
is deliberately outside it; off-machine backup/restore is not an integration gate.

The empty-server check observed the 60-second pause and 0.24% of one core before
backup, returning to 0.29% afterward over 30-second service CPU samples. Live
recovery integrity remained healthy. This proves a short return-to-idle sample;
it does not substitute for a representative multi-minute resource baseline.

Trusted failure reason codes and complete live recovery-set inspection are now
implemented and focused-tested. The runbook includes production cutover and
matching-configuration upgrade rollback; a disposable Btrfs cutover rehearsal
passed without replacing production. One-player resource observation averaged
14.3% of one CPU core with RSS around 1.54–1.61 GiB; the additional paused
sample averaged 0.246%. The user reported no noticeable play-session stutter or desktop stalls.
