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

The repository has retired completed journals and one-time migration tools.
Permanent granular/root/recovery regression tests remain. General cleanup is complete. Narrow framework correctness changes belong in
the draft foundation PR; authoritative results follow on separate experiment
branches after framework integration. Ordinary workstation changes stay separate.
[Historical records](history/README.md) are preserved by the immutable tag.
