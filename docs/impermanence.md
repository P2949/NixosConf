# Ephemeral root validation

The `feat/impermanence` branch stabilizes a Btrfs root reset in the systemd
initrd. The parent `desktop` configuration retains persistent root, home and
var. An opt-in `ephemeral-root` specialisation is now prepared for controlled
physical testing; building it does not install or activate it. Hardware
acceptance is still pending. See the [physical runbook](physical-root-validation.md)
and [persistence contract](persistence-contract.md).

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
boot ID. Missing or invalid persistence fails on stderr before any deletion.

## Reproduce validation

Run from the repository in zsh. These commands build tests without changing
host activation, installing boot entries or repartitioning physical storage.

```sh
nix flake check --no-write-lock-file --print-build-logs
nix build '.#impermanence-root-safety' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-recovery' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-test-a' --no-link --no-write-lock-file -L
nix build '.#impermanence-root-test-b' --no-link --no-write-lock-file -L
```

The lightweight `ephemeral-root-config` check forces NixOS evaluation for
three accepted configurations and 39 rejected configurations. VM tests remain explicit packages, outside
ordinary flake checks. The test driver retains type checking and linting.

| Test | Coverage |
| --- | --- |
| Configuration | Default and leading-slash root options accepted; non-systemd initrd, non-Btrfs root, missing device, unsafe names, conflicting names and missing/mismatched/conflicting root selectors rejected |
| Safety | 26 independent failure cases on a real disposable Btrfs disk: unknown child/grandchild, unknown child with empty staging, misleading ` path ` text in a subvolume name, missing root and staging, invalid root paths, missing/invalid persistence, mounted `/sysroot`, malformed staging with root present or absent |
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

## Gate for physical validation

After every final-revision check passes, prepare a separate controlled physical
boot milestone. Before its first boot:

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

The master `plan.md` Phase 4 supersedes the earlier proposed home migration:
selective home and var Impermanence are deferred for the pre-experiment
baseline. Both remain persistent. Compiler tuning, LTO, PGO and BOLT belong
after the final baseline tag. Maintenance and repository cleanup follow the
master plan's dependency gates.
