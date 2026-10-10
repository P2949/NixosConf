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

The [current status](status.md), [contract](persistence-contract.md),
[state audit](ephemeral-state-audit.md) and
[granular ledger](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
separate current results from the historical root-module evidence below.
Final exact-head validation/CI and the separate stock-readiness soak/backup gates
remain distinct from accepted migration. The root-reset guard is unchanged.

## Reset contract

`boot.ephemeralBtrfsRoot` is an opt-in reusable module. The defaults select
`@root`, stage through `@root-next`, and log into `@persist`.

The three names must be distinct direct top-level names matching
`[A-Za-z0-9_@][A-Za-z0-9_.@-]*`. The root filesystem must use Btrfs, have a
concrete device, and select the configured root with exactly one matching
`subvol=` option (`@root` and `/@root` forms are accepted). A conflicting
`subvolid=` option is rejected. A systemd initrd is required.

Before deletion the service validates persistence, root, staging and every
root descendant. Only explicitly allowed direct children (`tmp` and `srv`
by default) are disposable. Unknown grandchildren also stop reset. Staging
must have no descendants and no ordinary entries, including dotfiles, empty
directories and broken symlinks. Symlinks cannot stand in for subvolumes.

If root is absent and staging is empty, staging is renamed to root and the
service records `RECOVERY complete`. If both are present and valid, stale
empty staging is deleted only after the root audit passes. A new empty staging
subvolume is created and synced, validated children and root are deleted
non-recursively, and staging becomes root. The service records `RESET complete`.

The `/sysroot` mount guard and `RemainAfterExit=true` prevent resetting a
mounted root during the proven initrd lifecycle. Normal activation constructs
runtime directories; the reset service does not recreate `/tmp` or `/srv`.
Diagnostics go to `@persist/ephemeral-root-reset.log` with mode `0600` and a
boot ID. Relative log path components must be safe names; existing parents
cannot be symlinks or non-directories. The leaf must be a regular file with
only one hard link, or absent. Unsafe diagnostic paths fail on stderr before
log creation, chmod or root reset. Missing or invalid persistence fails on stderr before any deletion.

## Reproduce validation

Run from the repository in zsh. These commands build tests without changing
host activation, installing boot entries or repartitioning physical storage.

```sh
nix flake check --no-write-lock-file --print-build-logs
nix build '.#impermanence-root-safety' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-recovery' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-test-a' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-test-b' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-fallback' --no-link --no-write-lock-file -L
```

The lightweight `ephemeral-root-config` check forces NixOS evaluation for
four accepted configurations and 43 rejected configurations. VM tests remain explicit packages, outside
ordinary flake checks. The test driver retains type checking and linting.

| Test | Coverage |
| --- | --- |
| Configuration | Default and leading-slash root options accepted; non-systemd initrd, non-Btrfs root, missing device, unsafe names, conflicting names and missing/mismatched/conflicting root selectors rejected |
| Safety | 33 independent failure cases on a real disposable Btrfs disk: unknown child/grandchild, unknown child with empty staging, misleading ` path ` text in a subvolume name, missing root and staging, invalid root paths, missing/invalid persistence, mounted `/sysroot`, malformed staging with root present or absent, aliased/nonregular diagnostics and unsafe log parents |
| Recovery | Real UEFI/systemd-initrd boot with missing root and empty staging, then a boot with existing root and stale empty staging, then a normal reset boot |
| A | Three real root-reset boots without machine-ID persistence |
| B | Same three-boot harness with machine-ID persistence; missing backing file initialized on first boot and stable non-empty identity reused thereafter |

Safety compares all subvolume IDs/UUIDs, directory entries, symlink targets
and regular-file SHA-256 digests before and after each refusal, excluding only
the intentional diagnostic log. It verifies the expected diagnostic and
absence of successful reset/recovery markers, and checks cleanup of the
service's temporary mount.

Successful boot tests verify the selected system closure, Btrfs root mount,
persistent sentinels under `/persist`, `/etc/nixos`, `/home` and `/var`, the
persisted declarative credential, `/tmp` mode and usability, Home Manager,
NetworkManager, D-Bus and logind. Three distinct boot IDs must each have
exactly one reset-service invocation. Recovery additionally checks Btrfs
identities and the absence of leftover staging. B checks `/etc/machine-id`
against its persistent backing file and compares its value across all boots.
B also writes a journal marker per boot and requires all earlier markers to
remain queryable, using persistent journal storage under the same identity.

The `home.activationGenerateGcRoot = false` workaround applies only to this
VM harness's shared host store. It is not workstation policy.

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
