# Current status

Pre-optimization readiness is complete. Immutable tag:
`nixos-26.05-pre-optimization-baseline`, verified merged main
`1e3bdd13d179f88d6f1f0497d0ee75da88e67165`.
See the [canonical baseline](baselines/pre-optimization/baseline-final.md).

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
Optimization-v2 framework development is active. The productive NixOS closure
remains the protected `nixos-26.05-optimization-stock-v1` control. No optimization
derivation is installed into the productive system. Accepted display/audio/workload
and recovery evidence remains bound to the baseline closures.

## Development phase

The optimization-v2 experiment foundation is merged. The productive system
remains the protected `nixos-26.05-optimization-stock-v1` control and no
optimization candidate has been adopted into it.

The first authoritative package experiment,
[`zstd-skylake-v1`](../optimization/results/zstd-skylake-v1/), found
compression inconclusive at the declared practical threshold and a material
decompression regression. The candidate was therefore not adopted.

Prism Launcher implementation is accepted; source integration is tracked by
[PR #16](https://github.com/P2949/NixosConf/pull/16). See the
[live plan](prism-launcher-plan.md). Its Phase 1 candidate retains the complete
private launcher root. Normal boot, launcher/Java and real vanilla world
validation pass; refreshed account online features are user-confirmed. Cache/log
exclusions pass normal-reboot persistence/reset and retained-file hash proofs.
Post-reboot Fabric world, retained settings, graphics/input/audio and absence
of full assets/library downloads are user-confirmed. Proof and approved old
cache/log cleanup and final local source checks pass. Exact-head CI and merge
evidence are recorded in PR metadata.
Ordinary desktop changes may proceed while the immutable benchmark
control and experiment admission gates remain protected.

Further optimization investigation is intentionally deferred. General
workstation/readiness cleanup remains complete.
