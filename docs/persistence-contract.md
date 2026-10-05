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
