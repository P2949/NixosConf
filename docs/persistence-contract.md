# Desktop persistence contract

Desktop's granular source policy resets `@root`, including ordinary home and
var, on every normal boot. `persistent-root` disables that reset: undeclared
root-local home/var state and application-cache overlays remain across recovery
boots, then disappear when normal mode resumes. Explicit state works in both.

Migration status: generation 45 normal is running with both home and var on
@root. The first final normal matrix, service discovery and representative
application recheck pass; both policies are frozen. Generation 42's copy and first
physical home matrix passed; both accepted generation-44 recovery trials now
pass all 100 markers, retaining the same root identity. Offline validation
passed. The redundant seed-file bind over legacy var
is omitted from the corrected intermediate policy; final root-local var retains
that file explicitly. Generation 44 also preserves the restored Fuzzel history
in `.local/state/fuzzel` and is installed boot-only with both ESP artifact pairs
verified. Earlier Firefox/Codex cleanup failures remain archived and unaccepted.
The updated standalone proof tool passes eight regressions. The user's immediate
postboot verification supplied the second accepted recovery receipt; independent
root identity, topology, Fuzzel state and service checks pass. The first normal
home trial also passed all 100 requirements and replaced root 330 with root 332.
The second normal also passed, replacing root 332 with root 334. Independent
home acceptance passes and the user reconfirmed all important application state
works after the trials. Home policy is frozen. Exact-source final desktop/recovery
and the required suite pass, including fresh VM runs. Final generation 45 is
installed boot-only and its guarded var-only shutdown copy verified successfully
before selecting 45 once. Receipt `physical-boot-passed-f0309ac2-5ee1-49c5-96a6-ae7610598589.json`
accepts all 100 proofs on new root 336; final normal is now default after clearing
the fallback override. Final recovery → recovery → normal and the post-pruning
normal proof remain required. No agent reboot is scheduled. Read-only snapshots
and migration backing remain available; no legacy state or temporary copies are
retired before their remaining gates. The
[granular plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md) records
actual results and open gates; historic root-only evidence below does not prove
the new home/var contract.

| State | Policy | Reason |
| --- | --- | --- |
| `/` (`@root`) | Disposable in default; retained in recovery | Reconstructed by NixOS activation |
| `/home` | Root-local, ephemeral by default | Only declared user state survives normal boot |
| `/var` | Root-local, ephemeral by default | Only declared service state or intentional nested mounts survive |
| `/nix` (`@nix`) | Persistent | Store and generations |
| `/persist` (`@persist`) | Persistent | Explicit system/home backing storage, secrets and deliberate recovery evidence |
| `/var/lib/nixos-optimization` (`@optimization`) | Persistent, experiments inactive | Preserve existing artifacts |
| `/.snapshots` (`@snapshots`) | Retain pending forensic review | Not an independent backup |
| `/etc/nixos` | Bind persisted under `/persist/etc/nixos` | Working repository and tracked master plan |
| NetworkManager connections | Bind persisted under `/persist/etc/NetworkManager/system-connections` | Profiles and secrets |
| `/etc/machine-id` | Persist in both variants; current identity seeded before trials | Stable journal and service identity |
| `/var/lib/nixos` | Bind persisted | Stable UID/GID/subuid allocation |
| `/var/lib/systemd/random-seed` | File persisted in final policy; native legacy var retains it during home-only migration | Protected entropy state without a duplicate bind over an existing file |
| `/var/lib/NetworkManager` | Directory persisted; known runtime files reset | Stable key/internal settings; leases and timestamps discarded |
| `/var/lib/bluetooth` | Bind persisted, mode 0700 | Pairing credentials/trust |
| `/var/lib/btrfs` | Bind persisted | Scrub history/progress |
| Logs/journal/coredumps, `/var/cache`, `/var/tmp`, undeclared service DBs | Ephemeral | Volatile journal is explicit policy; no whole-var persistence |
| Password hash | `/persist/secrets/p2949-password-hash` | Declarative authentication without secrets in Git |
| SSH host keys | Persist before enabling sshd | Stable server identity; sshd currently not declared |
| `/tmp`, `/srv` | Reconstructed, root-local data discarded | Audit and back up any needed contents first |
| Other mutable `/etc`, `/root` and root-local files | Root home inspected: Nix channels/cache only; ordinary root state disposable | Must be declared, persisted, backed up or approved disposable |

Home paths persist only when listed in
[`home/p2949/persistence.nix`](../home/p2949/persistence.nix); system paths only
when listed in [`hosts/desktop/persistence.nix`](../hosts/desktop/persistence.nix).
The exact `P`/`R` reasons and application exceptions are in the
[state audit](ephemeral-state-audit.md). `.config`, `.local`, and `.cache` are
never persisted as whole containers. Known cache children inside retained
profiles are bound from root-local storage using
[`ephemeral-app-state.nix`](../home/p2949/ephemeral-app-state.nix), allowing normal
atomic profile updates. Fuzzel launch counts are user history: its configured
`.local/state/fuzzel/history` lives in the explicitly persisted directory
`.local/state/fuzzel`; its default `.cache/fuzzel` history was restored from the
inactive original. The corrected home candidate still needs physical acceptance.
Known disposable profile files use boot-only tmpfiles
removal, disabled in recovery. The user explicitly retains Steam shaders and
Unreal DDC/Zen caches and both Unity project Libraries because rebuilding them
is costly; Unity project logs and temporary files reset.

Upstream tmpfiles rules create ordinary directories for `/var/lib/machines`,
`/var/lib/portables` and `/var/tmp`; creating nested Btrfs subvolumes here would
correctly trip the unchanged root-reset descendant guard.

Regression: `nix flake check` executes the combined granular multi-boot VM;
`nix build .#impermanence-home .#impermanence-var --no-link` aliases that same
test. Blank-disk reconstruction separately uses the production Disko/desktop
closure and rejects `@home`/`@var` creation. VM evidence does not replace
physical application or repeated-boot acceptance.

No directory contents or secret values belong in this document. The separate encrypted secrets
backup/restore gate is completed on user-confirmed real recovery; independent
home backup verification remains open. The declarations
alone do not prove credentials are present, correctly protected or backed up.

Before first boot, inspect mutable `/etc` files with the Phase 4 inventory
command and classify each unexpected regular file. Nix store symlinks are
declarative; a regular file is not automatically safe to discard. Inspect
root-local work outside the separate mounts, especially `/root`, `/srv`,
`/opt` and `/tmp`. Do not copy secrets into the repository while auditing.

Historic root-only recovery acceptance: [physical-root-validation.md](physical-root-validation.md).
Current home/var rollout follows the granular plan, using `nixos-rebuild boot`,
with final application-quiesced copying before reboot. Never replace the live
home/var mounts with `switch`. Never delete old subvolumes or migration snapshots
before repeated physical normal/recovery/normal and application acceptance.

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

The operator confirms a separate secrets backup was restored successfully
during recovery from an actual system failure. This completes that gate on
user-reported evidence. Independent home backup is underway on Ventoy and
requires its own terminal integrity/restore receipt. Those home gates are not
inferred from successful root reset. Full application acceptance and
the productive-period state audit remain pending.
