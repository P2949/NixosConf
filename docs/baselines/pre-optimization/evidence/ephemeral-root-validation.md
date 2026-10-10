# Ephemeral root validation

Desktop replaces `@root` on every normal boot; `persistent-root` disables that
reset for recovery. Both modes retain machine identity and explicitly declared
state. Home and ordinary var are root-local, with audited profile/cache splitting.
The corrected generation 46 normal → recovery → recovery → normal sequence and
post-pruning normal all pass100 requirements, including nine Unity preference
hashes. Latest accepted root 344/reset count 26 is in
`post-pruning-normal-review.json`.

Scoped backing pruning, semantic legacy reconciliation, individual home/var
retirement and explicitly confirmed migration-snapshot retirement are complete.
Both accepted generation 46 closures/ESP pairs and the recovery ISO are retained.
Older generations requiring legacy mounts are obsolete. No additional physical
boot chain is required solely for inactive-data retirement or documentation.

The [current status](../../../status.md), [contract](../../../persistence-contract.md),
[state audit](../../../ephemeral-state-audit.md) and
[granular ledger](https://github.com/P2949/NixosConf/blob/nixos-26.05-pre-optimization-baseline/NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
separate current results from the historical root-module evidence below.
Readiness is complete at the immutable baseline tag; the additional soak was
waived by the user. The root-reset guard remains unchanged.

## Results and historical findings

The original safety test passed after removing the Statix-rejected parentheses
and correcting its timestamp-sensitive log assertion. Its initial failure was
a test assertion error: root and the unknown child had survived correctly.

Review then identified two independent gaps: ordinary staging contents were
not checked, and stale staging was deleted before the root descendant audit.
The stricter checks and safety matrix address both. The grandchild test also
demonstrated that the root-level Btrfs list did not expose a nested subvolume
below an allowed child. Non-recursive deletion stopped data loss, but staging
had already been created. The module now separately audits every allowed
child before any mutation. Parsing removes only the first output delimiter,
preserving any ` path ` text inside a subvolume name for rejection rather than
mistaking its suffix for an allowed child. Configuration validation also
prevents selecting persistence as the disposable root.

Validation on 2026-10-05 uses the unchanged flake lock. Safety, recovery, A and B
passed against the final reset script, with the following derivations:

| Result | Derivation |
| --- | --- |
| Safety: 26 refusals, identity/content preservation | `/nix/store/whhp5wgx2d191cwj1w39h9jh26f6jzi0-vm-test-run-impermanence-root-safety.drv` |
| Recovery: one recovery plus two resets over three unique boots | `/nix/store/qjm4qz6irvpzr3ysbb2hksv4jswj8mi8-vm-test-run-impermanence-root-recovery.drv` |
| A: three resets over three unique boots | `/nix/store/f8xyhs66fjw3mrlk98k7ia802xs6nvph-vm-test-run-impermanence-root-a.drv` |
| B: three resets, stable initialized machine-ID and journal markers retained | `/nix/store/fw3pvfy28wh5rnqc8hp7m67ijw0c2rk7-vm-test-run-impermanence-root-b.drv` |

Read the build evidence with `nix log` and the exact derivation path. The VM
runs use QEMU's TCG fallback because `/dev/kvm` is unavailable in this execution
environment. They validate correctness, not performance.

Formatting, Statix, Deadnix and configuration validation also passed. The
configuration check rejected all 39 invalid settings and accepted all three
positive controls, including a disabled module on an ordinary persistent root.

Machine-ID testing establishes behavior for this pinned VM configuration; it
does not establish the cause of the historical generation-30 physical
activation failure.

## Original physical trial procedure

The three completed opt-in trials used the following procedure. The later stable-refresh default/recovery policy was also physically accepted;
do not repeat these reboots merely to rerun the initial trial.

- Inventory current root-local data and preserve anything needed explicitly.
- Inspect actual Btrfs topology and verify persistent credentials without
  printing their contents.
- Retain forensic roots and known-good generations. Btrfs snapshots do not
  recursively include nested subvolumes; the historical forensic snapshots
  are not complete replacement roots.
- Build an optional ephemeral-root specialisation while retaining the normal
  persistent-root entry. Install through `nixos-rebuild boot`, with no live
  switch into machine-ID persistence or first-time root-reset behavior.
- Document and verify a recovery procedure before manually selecting the
  experimental entry. A normal boot entry is a configuration fallback, not
  restoration of data discarded by a previous reset.
- Repeat physical boots and validate authentication, networking, Home Manager,
  Hyprland, cooling, persistent state, machine identity and reset logs.

The earlier root-only Phase4 deferred selective home/var persistence. The
subsequent explicit granular goal superseded that storage deferral: home and
var are now root-local with a physically accepted explicit allow-list. Compiler
tuning, LTO, PGO and BOLT remain after the final baseline tag; unrelated readiness
soak/backup/release gates are not waived by storage acceptance.

## Physical evidence and recovery transition

| Trial | Boot ID | Fresh root ID | Result |
| --- | --- | --- | --- |
| 1 | `032de3f5-2df0-47d6-b26e-980dbacfdeeb` | 288 | Passed |
| 2 | `2b719311-60d5-4afd-a9eb-34f96bd198ed` | 290 | Passed |
| 3 | `da4649c0-8121-44ea-afcd-a2d0d4748681` | 292 | Passed |

Each boot reached the exact trial closure, removed the disposable sentinel,
preserved required mounts and state, retained the seeded identity, matched
credentials without logging them, and had healthy networking, cooling,
Home Manager, D-Bus/logind and an active Wayland session. No failed units
were found. Each distinct trial boot has one reset-service invocation.
Private receipts are `/persist/physical-root-trial-{1,2,3}.json`.

Two intervening parent boots were selected manually by the operator; neither
counts as a reset trial. They demonstrated the original persistent-root
fallback but exposed its temporary identity change. The final declared policy
persists identity in both variants. The new fallback VM checks three reset
boots followed by a non-reset boot retaining root, identity, journals and
credentials. The fallback test passed on 2026-10-05:
`/nix/store/5ja4j37lb76ffqvlcynqbmmk6hcxisvw-vm-test-run-impermanence-root-fallback.drv`.
The fourth boot verified the exact recovery closure, unchanged root ID/UUID and
reset log, retained root file, stable machine ID, all three previous journal
markers, credential source equality, required services and zero failed units.
The fixture recreates its system profile before installing the recovery entry
because only its host store is shared, whereas the physical host persists all
of `/nix`. Interactive workload acceptance, exact final physical policy boots
and the final soak remain separate gates.

Read-only pretrial snapshots of root, tmp and srv remain intact, along with
all three historical forensic roots. An older conflicting persisted machine
ID was archived privately before seeding the active identity. This does not
prove the historical generation-30 failure cause.

## Diagnostic path hardening follow-up

The expanded safety VM passed all 33 refusal cases and an additional successful
nested-log reset control on 2026-10-05. New cases cover log symlinks (including
broken ones), hard links, directories/FIFOs and symlink/non-directory parents.
Refusals compare file modes as well as identities, entries and contents; unsafe
log metadata remains intact. The positive control creates a safe log directory,
resets root, retains persistent data and writes a regular 0600 completion log.
All fast checks pass with 43 rejected and four accepted configurations.
Earlier result tables describe the preceding 26-case revision; their closures
do not prove this follow-up code. At that historical checkpoint, refreshed-input boot tests and candidate builds
were still required before deployment. Subsequent immutable-source builds,
physical generation 46 acceptance and retirement are recorded in the granular plan.
