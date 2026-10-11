# Ephemeral root architecture

Normal boots replace `@root`; `persistent-root` disables reset for recovery.
Home and ordinary var are root-local, with explicit state islands backed by
`@persist`. See the [persistence contract](persistence-contract.md) and
[canonical baseline](baselines/pre-optimization/baseline-final.md).

The [Minecraft server](minecraft-server.md) adds authoritative backup metadata
directly under `/persist/minecraft-backup` and persists only the timer file
`/var/lib/systemd/timers/stamp-minecraft-backup.timer`, backed under `/persist`.
The timer depends on that file's Impermanence service so calendar catch-up can
survive ordinary `/var` reset. Other systemd timer stamps are not added by this
module. The world uses the separately declared and physically deployed
`@minecraft` mount, whose persistence across a controlled reboot passed. Autosave recovery markers and the lock
are volatile under `/run/minecraft-backup` and survive a service failure within
the current boot.

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
nix build '.#interrupted-recovery' --no-link --no-write-lock-file -L
nix build '.#reset-control' --no-link --no-write-lock-file -L
nix build '.#persistent-identity' --no-link --no-write-lock-file -L
nix build '.#persistent-fallback' --no-link --no-write-lock-file -L
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

Historical trials and results are preserved in [baseline evidence](baselines/pre-optimization/evidence/ephemeral-root-validation.md).
