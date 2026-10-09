# Desktop persistence contract

On a normal boot, NixOS replaces `@root` and reconstructs declarative system
and user configuration. Ordinary home and var state are root-local and
**ephemeral by default**. State survives only through an explicit persistence
declaration or a deliberately persistent filesystem.

`persistent-root` disables root replacement for recovery. Root-local home/var
and application-cache overlays then remain across recovery boots; the next
normal boot discards that undeclared state. Explicitly persisted state works
in both modes. Recovery retains the current root; it is not restoration of
previously discarded data.

| State | Policy | Reason |
| --- | --- | --- |
| `/` (`@root`) | Reset on normal boot; retained in recovery | Reconstructed by activation |
| `/home` | Root-local, ephemeral by default | Only explicit user state persists |
| `/var` | Root-local, ephemeral by default | Only explicit service state/nested mounts persist |
| `/nix` (`@nix`) | Persistent | Store, profiles and generations |
| `/persist` (`@persist`) | Persistent | Explicit backing, secrets and justified recovery evidence |
| `/var/lib/nixos-optimization` (`@optimization`) | Separate persistent mount | Existing artifacts; experiments inactive |
| `/.snapshots` (`@snapshots`) | Persistent snapshot store | Deliberate retention; not an independent backup |
| `/boot` | Persistent ESP | Verified normal/recovery boot artifacts |
| `/etc/nixos` | Persisted containing directory | Repository and running ledger |
| `/etc/NetworkManager/system-connections` | Persisted containing directory | Connection profiles and secrets |
| `/etc/machine-id` | Persisted in both modes | Stable machine/service identity |
| `/var/lib/nixos` | Persisted directory | UID/GID/subuid allocation |
| `/var/lib/systemd/random-seed` | Persisted file | Protected entropy state |
| `/var/lib/NetworkManager` | Persisted directory with boot-only runtime cleanup | Stable key/internal configuration; leases, timestamps and seen-bssids discarded normally |
| `/var/lib/bluetooth` | Persisted directory, declared mode 0700 | Pairing identity/trust |
| `/var/lib/btrfs` | Persisted directory | Scrub history/progress |
| Logs/journal/coredumps, `/var/cache`, `/var/tmp`, undeclared service state | Ephemeral | Journal storage explicitly volatile |
| `/persist/secrets/p2949-password-hash` | Private persistent source | Declarative account authentication; no secrets in Git |
| SSH host keys | Declare persistence before enabling sshd | Stable server identity; sshd currently undeclared |
| `/etc` outside declarations, `/root`, `/srv`, `/tmp`, ordinary `/usr` mutable state | Ephemeral/reconstructed | Required new state needs an explicit audit/declaration |
| `/run`, `/dev`, `/proc`, `/sys` | Runtime/virtual | Recreated each boot |

Home state persists only through
[`home/p2949/persistence.nix`](../home/p2949/persistence.nix); system state through
[`hosts/desktop/persistence.nix`](../hosts/desktop/persistence.nix).
The [state audit](ephemeral-state-audit.md) lists path categories, reasons and
mixed-container exceptions. Never persist `.config`, `.local` or `.cache` as
whole containers, or assume that an application directory contains only caches.
Credentials, profile databases and atomic-save companions remain together in
writable containing directories.

Known disposable directory children of retained profiles bind to reset-root
storage through [`ephemeral-app-state.nix`](../home/p2949/ephemeral-app-state.nix).
This preserves atomic settings/database replacement in the parent. Known
disposable files use native boot-only tmpfiles rules through
[`ephemeral-app-files.nix`](../home/p2949/ephemeral-app-files.nix); those rules
are absent in recovery and do not run during live reactivation.

Fuzzel launch counts use persisted `.local/state/fuzzel/history`. Unity layouts,
search filters and overlays use persisted `.config/unity3d/Preferences`.
The user deliberately retains Steam shaders, Unreal DDC/Zen and current Unity
project Libraries; other audited project logs/temp/cache state resets. New
applications, profiles and projects require a fresh audit for their actual paths.
Android Studio is uninstalled; its future SDK/AVD policy is deferred. Existing
ADB identity is retained. Empty future credential/Plastic directories are
intentional reservations, not evidence of tested remote workflows.

Tmpfiles creates ordinary directories for `/var/lib/machines`,
`/var/lib/portables` and `/var/tmp`. Unknown nested Btrfs subvolumes correctly
stop the unchanged root-reset descendant guard. No blanket recursive deletion
or weakened guard is part of this contract.

## Acceptance and storage hygiene

The corrected generation 46 normal → recovery → recovery → normal chain and
post-pruning normal pass all 100 physical requirements; user application and
Unity preference checks are accepted. `/persist` has no undeclared home residue
or hidden cache data after scoped raw-view pruning. Empty cache mountpoint
scaffolds and explicitly justified evidence/backup subtrees remain.
Legacy `@home`/`@var` and their dedicated migration snapshots are retired.
Supported rollback is generation 46 normal/persistent-root; older generations
requiring legacy mounts are obsolete. Unrelated forensic/readiness backups
remain under their separate retention purposes.

The [granular plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
retains chronology and private-receipt names. Automated validation permanently
covers root/home/var reset and persistence, identity, optimization, repeated
recovery and return-normal. `nix flake check` runs the combined regression;
`nix build .#impermanence-home .#impermanence-var --no-link` aliases that same
test. Blank-disk reconstruction rejects `@home`/`@var` creation. Final exact-head
local/CI release validation is distinct from accepted physical migration.

No private directory contents or secret values belong in this contract.
Separate secrets recovery and the prior independent home archive/restore are
accepted evidence; backup freshness remains its own readiness gate. Snapshots
and successful boot tests do not replace an independent current backup.
