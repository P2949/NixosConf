# Desktop persistence contract

This is the planned physical-root contract, not evidence of hardware adoption.
The parent desktop configuration keeps persistent root. The opt-in
`ephemeral-root` specialisation resets only `@root` at boot.

| State | Policy | Reason |
| --- | --- | --- |
| `/` (`@root`) | Disposable only in opt-in entry | Reconstructed by NixOS activation |
| `/home` (`@home`) | Persistent | Projects, credentials, application and desktop state |
| `/var` (`@var`) | Persistent | Journal, Bluetooth, service databases and caches |
| `/nix` (`@nix`) | Persistent | Store and generations |
| `/persist` (`@persist`) | Persistent | Explicit root-state backing storage |
| `/var/lib/nixos-optimization` (`@optimization`) | Persistent, experiments inactive | Preserve existing artifacts |
| `/.snapshots` (`@snapshots`) | Retain pending forensic review | Not an independent backup |
| `/etc/nixos` | Bind persisted under `/persist/etc/nixos` | Working repository, including ignored local plan |
| NetworkManager connections | Bind persisted under `/persist/etc/NetworkManager/system-connections` | Profiles and secrets |
| `/etc/machine-id` | Persist in opt-in entry; seed current identity before boot | Stable journal and service identity |
| Password hash | `/persist/secrets/p2949-password-hash` | Declarative authentication without secrets in Git |
| SSH host keys | Persist before enabling sshd | Stable server identity; sshd currently not declared |
| `/tmp`, `/srv` | Reconstructed, root-local data discarded | Audit and back up any needed contents first |
| Other mutable `/etc`, `/root` and root-local files | Unclassified until physical preflight | Must be declared, persisted, backed up or approved disposable |

Selective home and var Impermanence are deferred by `plan.md` Phase 4.
No directory contents or secret values belong in this document. Independent
encrypted backup and a restore test remain operator gates. The declarations
alone do not prove credentials are present, correctly protected or backed up.

Before first boot, inspect mutable `/etc` files with the Phase 4 inventory
command and classify each unexpected regular file. Nix store symlinks are
declarative; a regular file is not automatically safe to discard. Inspect
root-local work outside the separate mounts, especially `/root`, `/srv`,
`/opt` and `/tmp`. Do not copy secrets into the repository while auditing.

Recovery and physical acceptance: [physical-root-validation.md](physical-root-validation.md).

## Initial root-local inventory, 2026-10-05

`find /etc -xdev -type f` completed without permission errors and found 14
regular files. The separately mounted repository and NetworkManager backing
directory are excluded by `-xdev`. This inventories paths and metadata, not
secret contents, and is not a complete audit of root-local data.

| Files | Classification and remaining gate |
| --- | --- |
| `NIXOS`, `.clean`, `.updated` | NixOS/systemd markers, reconstructed |
| `resolv.conf` | Resolver runtime state, reconstructed by networking |
| `resolv.conf.bak` | Empty at inspection; disposable runtime backup |
| `wpa_supplicant/imperative.conf` | Empty at inspection; pinned module creates it on service start; do not start storing undeclared profiles here |
| `machine-id` | Seed and persist current identity before the first trial |
| `group`, `passwd`, `shadow`, `subuid`, `subgid` | Account activation outputs; verify all intended accounts/credentials are declarative before discarding imperative changes |
| `sudoers` | Declarative activation output; verify no manual-only changes |
| `kernel/entry-token` | Boot installation state; review during privileged bootloader preflight |

`/srv` had no directory entries at inspection. `/tmp` contains live scratch
state and must be audited before reboot. `/root` is mode `0700` and remains
unaudited: the operator must preserve any required data there. Actual Btrfs
descendant topology, credential protection, external backups and recovery-media
boot remain unverified. Repeat the inventory after the final productive period;
these observations do not authorize discarding newly created state.
