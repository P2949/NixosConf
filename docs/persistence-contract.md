# Desktop persistence contract

Desktop declares reset of `@root` as normal policy, with a `persistent-root`
recovery specialisation that disables reset. Both retain machine identity.
Three physical opt-in reset trials passed; exact final default/recovery boot
acceptance remains pending and is batched with other work.

| State | Policy | Reason |
| --- | --- | --- |
| `/` (`@root`) | Disposable in default; retained in recovery | Reconstructed by NixOS activation |
| `/home` (`@home`) | Persistent | Projects, credentials, application and desktop state |
| `/var` (`@var`) | Persistent | Journal, Bluetooth, service databases and caches |
| `/nix` (`@nix`) | Persistent | Store and generations |
| `/persist` (`@persist`) | Persistent | Explicit root-state backing storage |
| `/var/lib/nixos-optimization` (`@optimization`) | Persistent, experiments inactive | Preserve existing artifacts |
| `/.snapshots` (`@snapshots`) | Retain pending forensic review | Not an independent backup |
| `/etc/nixos` | Bind persisted under `/persist/etc/nixos` | Working repository and tracked master plan |
| NetworkManager connections | Bind persisted under `/persist/etc/NetworkManager/system-connections` | Profiles and secrets |
| `/etc/machine-id` | Persist in both variants; current identity seeded before trials | Stable journal and service identity |
| Password hash | `/persist/secrets/p2949-password-hash` | Declarative authentication without secrets in Git |
| SSH host keys | Persist before enabling sshd | Stable server identity; sshd currently not declared |
| `/tmp`, `/srv` | Reconstructed, root-local data discarded | Audit and back up any needed contents first |
| Other mutable `/etc`, `/root` and root-local files | Root home inspected: Nix channels/cache only; ordinary root state disposable | Must be declared, persisted, backed up or approved disposable |

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

At the initial unprivileged inspection, `/srv` had no directory entries,
`/tmp` contained live scratch state, and `/root` was inaccessible at mode
`0700`. Btrfs descendant topology, credential protection, external backups and
recovery-media boot were then unverified. The privileged evidence below
supersedes that initial inventory. Repeat it after the final productive period;
these observations do not authorize discarding newly created state.

## Privileged and repeated-boot evidence

Preflight verified root-owned 0700 secret directory and 0600 nonempty password
file; current shadow matched its declarative source privately. Top-level
inspection found only allowed tmp/srv descendants and no grandchildren or
staging. Root home contained Nix channels/cache, with no project or credential
files found; root home is disposable policy, with a read-only pretrial snapshot
retained. Three physical reset boots preserved all declared mounts, identity
and account source. A fresh `/etc` metadata inventory after boot three found
only reconstructed account, sudo, marker, resolver and empty imperative-Wi-Fi
files, plus persisted machine identity.

The operator reports an older independent backup of secrets and recovery media
previously used successfully. Backup freshness, encrypted storage and a
representative restore proof remain unverified. Those broader baseline gates
are not inferred from successful root reset. Full application acceptance and
the productive-period state audit remain pending.
