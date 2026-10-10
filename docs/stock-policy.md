# Stock workstation policy

## Identities

The **qualification baseline** is immutable historical qualification; its exact
identities and evidence belong to the
[canonical baseline](baselines/pre-optimization/baseline-final.md).

The **benchmark control** is the separately protected annotated
`nixos-26.05-optimization-stock-v1` tag at
`53b58e38e36d7c6071807e7abedc85fce42c449c`, tree
`a13d519df93daf568b0187ac817ccb3e8ab39f04`.

- Normal: `/nix/store/6rn4ggk32wcqrhcdv2chr55daqxxh026-nixos-system-desktop-26.05.20261004.0d9e9b8`
- Persistent-root: `/nix/store/yf7jg059hm4qg2yhyls4ciddliwc8ych-nixos-system-desktop-26.05.20261004.0d9e9b8`
- nixpkgs: `0d9e9b832d03ac387417e16ce1febf73b2e631e1`
- flake.lock SHA-256: `7efb19569e8a022768cd570498ff8b93cb98b108358149b668a658e2d9f406a2`

The **productive desktop** is current `main` / the installed workstation. Ordinary
workstation features may advance it without retagging either historical identity.
Its current state belongs to [status](status.md). Experiment admission requires
reconstructing and booting the designated benchmark control; see the
[experiment procedure](optimization.md).

## CPU

PL1 and PL2 are both 125 W, applied at boot and resume. The benchmark control
retains intel_pstate default policy; GameMode's accepted temporary request
restores the previous policy on exit. No experimental governor, CPU isolation,
mitigation disabling or RCU offload is declared. Commander Core cooling remains
at its accepted policy.

## Memory and storage

Disk swap remains configured. IRQ balancing and zram are disabled. No
experimental swappiness, dirty-page, THP, NUMA or scheduler tuning is declared.
Retain kernel-selected NVMe scheduling and the declared Btrfs policy.
Maintenance should run outside benchmark intervals. Root, home and ordinary
var are disposable; journald uses volatile storage. Runtime journal sizing uses systemd defaults. The ineffective persistent size
knobs were removed in the separate volatile-journal policy change. The existing
90-day upper time bound remains within a boot; reboot discards the journal.

## Build environment and graphics

No global experimental CFLAGS, CXXFLAGS, LDFLAGS, NIX_CFLAGS_COMPILE,
NIX_LDFLAGS, allocator preload, LTO, PGO, BOLT or march policy is declared.
NIX_LD and NIX_LD_LIBRARY_PATH are compatibility integration. Application-local
library paths are not evidence of global compiler optimization.
Benchmark kernel/Mesa/graphics and package inputs remain frozen in the control.

## Experiment boundary

The optimization namespace exports isolated experiment packages, provenance and
runners. The benchmark control remains frozen. Experiments
must be explicitly selected and carry specification, build, runtime and result
artifacts. Productive desktop and benchmark-control closures reject project-owned
optimization output namespaces; see the
[stock closure contract](stock-control.md). Runtime-policy changes, package
refreshes and workstation features belong on separate branches.

## Post-qualification journal correction

The benchmark control differs from qualification only by the deliberate volatile
journal correction: ineffective persistent sizing settings were removed. No
compiler, cooling, CPU-power, package-input or persistence change was included.
Experiments record their actual control source, inputs and closure identities;
qualification and benchmark control are distinct historical environments.
