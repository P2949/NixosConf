# Current status

The **productive desktop** advances on `main`, independently of the immutable
[qualification baseline](baselines/pre-optimization/baseline-final.md) and frozen
[benchmark control](stock-policy.md). Exact source, CI and acceptance receipts
belong to PR/tag history; see the [history index](history/README.md).

## Storage and recovery

`@root` contains ephemeral root, home and ordinary var. Explicit retained state
is backed by `@persist`; separate mounts retain `@nix`, `@snapshots` and
`@optimization`, plus ESP and swap. Legacy home/var subvolumes are retired.
See the [persistence contract](persistence-contract.md).

Recovery uses Nix/GitHub/reinstall, separately tested secrets recovery and a
small local-only exception archive. The recovery ISO remains verified.
See [backup and recovery](backup-restore.md). The additional final-runtime soak
was disregarded by human intervention and is not a measured PASS.

## Productive policy and optimization

The accepted CPU package baseline is 125 W PL1/PL2, with boot/resume application.
Commander Core retains the accepted cooling policy. Bluetooth is disabled.
Accepted physical display/audio/workload and recovery evidence remains bound
to the baseline closures.

The optimization-v2 foundation is available. No optimization candidate is
installed in the productive system. The completed
[`zstd-skylake-v1`](../optimization/results/zstd-skylake-v1/) experiment found
compression inconclusive and decompression regressed at its declared threshold;
the candidate was not adopted. Ordinary desktop changes may proceed while the
frozen control and experiment admission gates remain protected.

## Development applications

Prism Launcher is accepted through
[PR #16](https://github.com/P2949/NixosConf/pull/16). Its private launcher root,
accounts, instances/worlds/mods and meaningful state persist. Audited cache/log
children reset under granular Impermanence. See the
[application state audit](ephemeral-state-audit.md).

Android Studio is accepted through
[PR #28](https://github.com/P2949/NixosConf/pull/28). The writable SDK, AVDs,
settings, ADB/debug signing keys, projects and selected Gradle state persist;
audited IDE/Android caches remain disposable. Third-party IDE plugins and
physical USB-device workflows remain unexercised. See the
[Android workflow](development-validation.md#android-studio) and
[state audit](ephemeral-state-audit.md).

General maintainability cleanup is complete under the
[repository policy](repository-policy.md). Generated custom-module docs and the
[interactive desktop bootloader VM](development-validation.md#interactive-desktop-vm)
remain explicit developer tools. The
[interrupted-recovery debug driver](development-validation.md#interactive-interrupted-recovery-debugging)
provides a deliberate Btrfs checkpoint and local VSock SSH inspection. The
[disposable Minecraft staging environment](minecraft-server.md#disposable-staging-before-upgrades)
provides isolated version/mod and world-copy validation.
The [distributed-build VM proof](development-validation.md#distributed-build-routing-proof)
checks remote execution, output transfer and builder feature rejection while
retaining physical-only benchmark admission.
VM results do not replace physical acceptance.

## Minecraft server

Minecraft production is deployed on the desktop with automatic startup,
`Restart=always`, a six-hour UTC backup timer and transactional local Btrfs
recovery. Normal policy pins Minecraft 26.3, Fabric 0.19.5, OpenJDK 25, C2ME
executor four, Distant Horizons 3.3.4 and G1. Maintenance specialisations provide
Chunky pregeneration and DH LOD backfill. Spark background profiling is disabled.
See [Minecraft operations](minecraft-server.md).

The accepted stack, backup/recovery and maintenance behavior are recorded in
[PR #23](https://github.com/P2949/NixosConf/pull/23),
[PR #24](https://github.com/P2949/NixosConf/pull/24) and
[PR #26](https://github.com/P2949/NixosConf/pull/26). One unexpected-terrain C2ME
observation did not reproduce; causality remains unresolved.

Ordinary calendar-event and genuine missed-event observations remain deferred;
manual/synthetic tests do not establish either. Actual laptop/LAN gameplay and
multi-player resource capacity remain unexercised. Local Btrfs recovery covers
rollback on this device; total device loss is outside the declared backup scope.
