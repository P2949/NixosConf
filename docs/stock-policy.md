# Stock workstation policy

## Immutable control

The control is `nixos-26.05-pre-optimization-baseline`, merged at
`1e3bdd13d179f88d6f1f0497d0ee75da88e67165`. Its normal closure begins
`15f6c5dsjl047j7my4c7cpkdhk6ly2xp`; persistent-root begins
`7lkx40kh36s809bz1yr9bmfdddy1n80a`. Stable nixpkgs is
`0d9e9b832d03ac387417e16ce1febf73b2e631e1`.
See the [canonical baseline](baselines/pre-optimization/baseline-final.md)
for full identities and accepted evidence. Preparation history is available
through the [history index](history/README.md).

## CPU

PL1 and PL2 are both 125 W, applied at boot and resume. The stock system
retains intel_pstate default policy; GameMode's accepted temporary request
restores the previous policy on exit. No experimental governor, CPU isolation,
mitigation disabling or RCU offload is declared. Commander Core cooling remains
at its accepted policy.

## Memory and storage

Disk swap remains configured. IRQ balancing and zram are disabled. No
experimental swappiness, dirty-page, THP, NUMA or scheduler tuning is declared.
Retain kernel-selected NVMe scheduling and the declared Btrfs policy.
Maintenance should run outside benchmark intervals. Root, home and ordinary
var are disposable; journald uses volatile storage. Persistent journal size
knobs in the maintenance module require a separate policy review.

## Build environment and graphics

No global experimental CFLAGS, CXXFLAGS, LDFLAGS, NIX_CFLAGS_COMPILE,
NIX_LDFLAGS, allocator preload, LTO, PGO, BOLT or march policy is declared.
NIX_LD and NIX_LD_LIBRARY_PATH are compatibility integration. Application-local
library paths are not evidence of global compiler optimization.
The accepted productive kernel/Mesa/graphics closure remains the control;
package inputs are pinned during closure-preserving cleanup.

## Experiment boundary

`optimization/default.nix` is inert. Future experiments must be explicitly
selected and carry provenance, runtime and result manifests. The productive
stock closure rejects project-owned optimization output namespaces; see the
[stock closure contract](stock-control.md). Runtime-policy changes, package
refreshes and workstation features belong on separate branches.
