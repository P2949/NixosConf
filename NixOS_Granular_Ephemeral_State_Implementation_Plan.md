# Granular Ephemeral NixOS Implementation Plan

**Repository:** `P2949/NixosConf`  
**Starting branch reviewed:** `feat/pre-optimization-readiness`  
**Starting reviewed commit:** `de058b4b65416249e2a1ac2e722f7514c87d5a36`  
**Primary objective:** make the workstation ephemeral by default across root, home, and system mutable state, while preserving only explicitly declared state that has a demonstrated reason to survive reboot.

## Implementation status — 2026-10-08

This is the active implementation record. The numbered procedure below remains
the acceptance specification; unchecked physical gates must not be inferred
from source changes or VM tests.

- Fully read all 2,393 original lines, including the migration ordering and
  retirement gates. No repository `AGENTS.md` applies.
- Started `feat/granular-impermanence` at the exact reviewed commit above.
  Tracked files were clean; this user-supplied plan was the sole untracked file
  and is preserved and updated as part of this work.
- Live topology confirmed: `/home` is `@home`, `/var` is `@var`, `/persist`
  is `@persist`; the optimization mount remains independent. Passwordless
  privileged commands are available.
- Metadata-only inventories found 151 GiB of home state, including development
  projects, Unity installs, Firefox profiles, VS Code shared storage and game
  saves outside Steam. These require explicit declarations beyond the examples.
- `@var` has nested `lib/portables`, `lib/machines`, and `tmp` subvolumes.
  Retirement must inspect these individually and must not recursively delete.
- In progress: snapshots, state classification ledger, migration backing,
  granular declarations, topology guards and multi-boot regression tests.
- Pending: all offline validation, next-boot cutovers, representative application
  checks, physical repeated normal/recovery boots, backing-store pruning, and
  legacy-subvolume/snapshot retirement. The goal is not complete.

Evidence paths and validation results will be added here as work progresses.

---

# 1. Objective and finish line

This plan has one objective only:

> **Make as much mutable state on the NixOS workstation ephemeral as is practical, with persistence becoming an explicit allow-list rather than an accidental property of filesystem layout.**

The implementation is complete only when all of the following are true:

1. `/` is reset on every normal boot, as it is already.
2. `/home` is no longer an always-persistent Btrfs subvolume.
3. User home state survives reboot **only** when it is explicitly declared through Impermanence.
4. `/var` is no longer an always-persistent Btrfs subvolume.
5. System state under `/var` survives reboot **only** when it is explicitly declared through Impermanence or lives on a deliberately persistent nested mount.
6. `/nix`, `/persist`, `/.snapshots`, `/boot`, and `/var/lib/nixos-optimization` remain deliberately persistent.
7. `/etc` remains ephemeral except for explicitly persisted paths.
8. `/root`, `/tmp`, `/srv`, ordinary `/usr`-side mutable state, user caches, system caches, temporary state, and undeclared application state are discarded on normal reboot.
9. Home Manager reconstructs declarative user configuration after each root reset.
10. NixOS reconstructs declarative system configuration after each root reset.
11. Important credentials, user-created files, application profiles, machine identity, and required service databases have been explicitly identified and persisted.
12. The system has automated tests proving both sides of the contract:
    - declared state survives;
    - undeclared state disappears.
13. The physical workstation has passed repeated normal boots with the new persistence model.
14. The `persistent-root` specialisation still works as the recovery mode.
15. The former `@home` and `@var` contents have been either deliberately retired or retained only as clearly named temporary migration snapshots; they are no longer active persistence mechanisms.

The intended final model is:

```text
Btrfs filesystem
│
├── @root
│   └── /
│       ├── etc/                 ephemeral except bind-persisted state
│       ├── home/                ephemeral except bind-persisted state
│       ├── root/                ephemeral
│       ├── srv/                 ephemeral
│       ├── tmp/                 ephemeral
│       ├── usr/                 reconstructed/declarative
│       └── var/                 ephemeral except bind-persisted/nested state
│
├── @nix
│   └── /nix                     persistent
│
├── @persist
│   └── /persist                 persistent backing store for explicit state
│
├── @optimization
│   └── /var/lib/nixos-optimization
│                               persistent
│
├── @snapshots
│   └── /.snapshots              persistent
│
└── EFI partition
    └── /boot                    persistent
```

The governing rule is:

```text
If state survives a normal reboot, there must be a deliberate declaration
or a deliberate persistent filesystem explaining why.
```

---

# 2. Current starting point

The existing system already has a strong root-Impermanence design.

Current Disko layout:

```text
@root          -> /
@home          -> /home
@nix           -> /nix
@persist       -> /persist
@var           -> /var
@optimization  -> /var/lib/nixos-optimization
@snapshots     -> /.snapshots
```

The current normal boot resets `@root` through the custom systemd-initrd Btrfs root-reset module.

The current `persistent-root` specialisation disables that reset.

The current explicit root persistence consists of:

```text
/etc/machine-id
/etc/nixos
/etc/NetworkManager/system-connections
```

The remaining reason that large amounts of mutable state survive is not the root filesystem. It is the two persistent islands:

```text
@home -> /home
@var  -> /var
```

Therefore this plan does **not** redesign the existing root reset. It extends its persistence philosophy to the currently persistent home and var domains.

---

# 3. Safety invariants

These rules apply throughout the implementation.

## 3.1 Never delete the old `@home` or `@var` during initial cutover

Removing a mount from the NixOS configuration does not require deleting the physical Btrfs subvolume.

During migration:

```text
@home
@var
```

must remain physically present.

They become inactive rollback sources.

This provides two safety properties:

1. old generations that still expect `@home` and `@var` can continue to find them;
2. data omitted from the first persistence declaration can still be recovered.

Do not delete these subvolumes until the final retirement stage.

---

## 3.2 Persistence migration happens before mount removal

Never first make home or var ephemeral and then discover what should have been copied.

The order is always:

```text
inventory
→ classify
→ prepare /persist
→ copy data
→ verify copy
→ declare persistence
→ build
→ boot
→ verify
```

---

## 3.3 Unknown state defaults to “preserve during migration”

The final policy is ephemeral-by-default.

The migration policy is deliberately more conservative.

For any directory that has not yet been classified:

```text
UNKNOWN -> temporarily preserve
```

After it is understood:

```text
UNKNOWN
  ↓
PERSISTENT
DECLARATIVE
EXPENSIVE-RECONSTRUCTABLE
EPHEMERAL
MIXED
```

Only then is it removed from the persistence allow-list.

This prevents a classification mistake from becoming data loss.

---

## 3.4 Never put secrets into the Git repository

The persistence configuration may contain paths such as:

```text
.ssh
.gnupg
.pki
.local/share/keyrings
```

It must never contain their contents.

Actual secret state lives beneath `/persist`.

---

## 3.5 Activate filesystem-boundary changes with `boot`, not `switch`

Changing `/home` or `/var` while they are in active use is unnecessary risk.

For the first home cutover and first var cutover use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Then reboot.

Do not attempt to replace the currently mounted `/home` or `/var` beneath a live graphical session.

---

# 4. Create an isolated implementation branch

Start from the exact source revision that is intended to receive this feature.

Record the current state:

```bash
cd /etc/nixos

git status --short
git branch --show-current
git rev-parse HEAD
git log -1 --oneline
```

Require a clean worktree before beginning.

Create a dedicated branch:

```bash
git switch -c feat/granular-impermanence
```

The feature branch should contain only changes required for this ephemeral-state project.

---

# 5. Capture the current mount and subvolume topology

Before modifying anything, record exactly what currently provides each path.

Run:

```bash
findmnt -R -o TARGET,SOURCE,FSTYPE,OPTIONS /

echo
for path in \
    / \
    /boot \
    /home \
    /nix \
    /persist \
    /var \
    /var/lib/nixos-optimization \
    /.snapshots
do
    echo "=== $path ==="
    findmnt "$path" || true
done
```

Record Btrfs topology:

```bash
sudo btrfs subvolume list -p /
sudo btrfs subvolume show /
sudo btrfs filesystem usage /
```

Mount the Btrfs top-level temporarily if it is not already accessible:

```bash
sudo mkdir -p /mnt/btrfs-top

sudo mount \
    -o subvolid=5 \
    /dev/disk/by-label/nixos \
    /mnt/btrfs-top
```

Verify:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top
```

The expected active subvolumes include at least:

```text
@root
@home
@nix
@persist
@var
@optimization
@snapshots
```

Do not change them yet.

---

# 6. Create migration snapshots of home and var

Create read-only snapshots before auditing or copying.

Choose an unambiguous migration timestamp:

```bash
stamp="$(date +%Y%m%d-%H%M%S)"
echo "$stamp"
```

Create snapshots:

```bash
sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@home \
    "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-home-$stamp"

sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@var \
    "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-var-$stamp"
```

Verify:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top \
    | grep 'pre-granular-impermanence'
```

These snapshots are migration rollback evidence, not the final persistence mechanism.

---

# 7. Build an explicit state classification ledger

Create a working document dedicated to this implementation:

```text
docs/ephemeral-state-audit.md
```

Its purpose is to classify mutable paths.

Use five classes:

| Class | Meaning | Final policy |
|---|---|---|
| `E` | Ephemeral runtime/cache/scratch state | discard every normal reboot |
| `D` | Declaratively reconstructed by NixOS/Home Manager | discard every normal reboot |
| `R` | Reconstructable, but expensive enough that persistence is intentionally worthwhile | persist if explicitly chosen |
| `P` | Authoritative user/service state | persist |
| `M` | Mixed container holding several classes | split into children |

Every top-level home entry and every important `/var` subtree must eventually receive one of these classifications.

Do not finish this project with important entries still marked unknown.

---

# 8. Inventory the entire home directory

Start with size and type information.

```bash
du -xhd1 "$HOME" | sort -h
```

Inspect hidden and normal entries:

```bash
find "$HOME" \
    -xdev \
    -mindepth 1 \
    -maxdepth 1 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Inspect symbolic links:

```bash
find "$HOME" \
    -xdev \
    -maxdepth 2 \
    -type l \
    -printf '%p -> %l\n' \
    | sort
```

Pay special attention to:

```text
.android
.cache
.codex
.config
.dbus
.dotnet
.epic
.icons
.local
.nix-defexpr
.pki
.plastic4
.steam
.vim
.vscode
.vscode-shared
.zen

.ssh
.gnupg
.nuget
.mozilla
Development
Desktop
Documents
Downloads
Music
Pictures
Public
Templates
Videos
```

The XDG user directories currently declared by Home Manager are:

```text
Desktop
Documents
Downloads
Music
Pictures
Development
Public
Templates
Videos
```

All user-created/authoritative directories must be intentionally classified before home becomes ephemeral.

---

# 9. Expand mixed home containers

The following directories must not be treated as single semantic units:

```text
.config
.local
```

Inventory them separately.

## `.config`

```bash
du -xhd1 "$HOME/.config" 2>/dev/null | sort -h

find "$HOME/.config" \
    -xdev \
    -mindepth 1 \
    -maxdepth 1 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Typical policy:

```text
Home-Manager-owned configuration  -> D
application caches                -> E
application identity/profile DBs  -> P
unknown application state         -> preserve during migration, then classify
```

Any configuration that is already generated by Home Manager should normally **not** be persisted.

The purpose of Home Manager is to reconstruct it.

---

## `.local`

Inspect:

```bash
du -xhd1 "$HOME/.local" 2>/dev/null | sort -h
du -xhd1 "$HOME/.local/share" 2>/dev/null | sort -h
du -xhd1 "$HOME/.local/state" 2>/dev/null | sort -h

find "$HOME/.local" \
    -xdev \
    -mindepth 1 \
    -maxdepth 2 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Treat major children independently.

Examples that are often persistent:

```text
.local/share/keyrings
.local/share/Steam
.local/share/<browser-or-app profiles>
```

Examples that are often disposable:

```text
application caches
generated thumbnails
temporary indexes that are cheap to regenerate
```

Do not persist the entire `.local` permanently merely because it is convenient.

It may be temporarily preserved during the first migration, but the final state should be granular.

---

# 10. Observe real home writes during representative use

Static inspection is not enough.

Use `fatrace` temporarily:

```bash
nix shell nixpkgs#fatrace
```

Start a write-only trace:

```bash
sudo fatrace \
    --filter=W \
    --timestamp \
    --output=/tmp/fatrace-home-var-writes.log
```

During the trace, perform a representative session using the applications whose state matters.

At minimum exercise the applications corresponding to the directories being considered, for example:

```text
Zen/browser
Firefox if used
Steam
one Steam game
VS Code
Codex
Android Studio/emulator if retained
Plastic/Unity VCS if retained
Unreal
Blender
terminal/shell/Git
```

Stop `fatrace`.

Extract home writes:

```bash
grep '/home/p2949/' \
    /tmp/fatrace-home-var-writes.log \
    > /tmp/fatrace-home-writes.log
```

Extract var writes:

```bash
grep '/var/' \
    /tmp/fatrace-home-var-writes.log \
    > /tmp/fatrace-var-writes.log
```

Use the writing process to answer:

```text
Who owns this state?
What creates it?
Will the application recreate it?
Would recreation lose identity, history, projects, credentials or settings?
Is regeneration cheap or expensive?
```

Update `docs/ephemeral-state-audit.md`.

---

# 11. Use Btrfs snapshots to identify actual changed paths

After the representative session, take second read-only snapshots.

```bash
stamp_after="$(date +%Y%m%d-%H%M%S)"
```

```bash
sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@home \
    "/mnt/btrfs-top/@snapshots/granular-impermanence-home-after-$stamp_after"

sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@var \
    "/mnt/btrfs-top/@snapshots/granular-impermanence-var-after-$stamp_after"
```

Use Btrfs send metadata to inspect changes.

For home:

```bash
sudo btrfs send --no-data \
    -p "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-home-$stamp" \
       "/mnt/btrfs-top/@snapshots/granular-impermanence-home-after-$stamp_after" \
    | sudo btrfs receive --dump \
    > /tmp/home-btrfs-diff.txt
```

For var:

```bash
sudo btrfs send --no-data \
    -p "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-var-$stamp" \
       "/mnt/btrfs-top/@snapshots/granular-impermanence-var-after-$stamp_after" \
    | sudo btrfs receive --dump \
    > /tmp/var-btrfs-diff.txt
```

The two sources answer different questions:

```text
fatrace           -> which process wrote the state
Btrfs snapshot diff -> which paths changed
```

Use both before finalizing the allow-list.

---

# 12. Required initial home classifications

The audit has final authority, but use the following as the starting policy.

| Path | Starting classification | Reason |
|---|---|---|
| `.cache` | `E` | cache |
| `.dbus` | `E` | session/runtime state |
| `.nix-defexpr` | `E`/remove | legacy Nix state unless specifically used |
| `.ssh` | `P` | credentials and trust state |
| `.gnupg` | `P` | key material |
| `.pki` | `P` | certificate/NSS state |
| `.android` | `P` or `R` | ADB keys, AVDs, debug identity and expensive SDK/emulator state |
| `.codex` | `P` | authentication and application state unless audit proves otherwise |
| `.plastic4` | `P` | VCS credentials/configuration |
| `.zen` | `P` | browser profile/history/cookies/extensions |
| `.vscode` | `R`/`P` | extensions and editor state |
| `.vscode-shared` | unknown -> audit | identify exact owner |
| `.epic` | unknown -> audit | identify exact owner |
| `.icons` | `P` or `D` | persist user assets unless Home Manager owns them |
| `.dotnet` | `M` | split tools/state from disposable generated data |
| `.vim` | `M` | persist authoritative config/data; discard temp/swap/cache |
| `.steam` | inspect symlink/role | actual Steam state normally lives elsewhere |
| `.config` | `M` | split per application |
| `.local` | `M` | split `share`, `state`, `bin`, etc. |
| `Development` | `P` | authoritative source/project data |
| `Documents` | `P` | user-created data |
| `Desktop` | `P` if used | user-created data |
| `Downloads` | explicit user decision | may contain irreplaceable downloads |
| `Pictures` | `P` | user-created data |
| `Music` | `P` if locally authoritative | user data |
| `Videos` | `P` if locally authoritative | user data |
| `Public` | `P` if used | user data |
| `Templates` | `P` if used | user data |

For safety, user-created XDG data directories should initially persist.

If the final desired policy intentionally makes a directory such as `Downloads` disposable, that must be an explicit decision in the audit ledger.

---

# 13. Add a dedicated Home Manager persistence module

Create:

```text
home/p2949/persistence.nix
```

Import it from:

```text
home/p2949/default.nix
```

The import list should become conceptually:

```nix
imports = [
  ./cli.nix
  ./desktop
  ./development
  ./persistence.nix
  ./shell.nix
  ./xdg.nix
];
```

Use Home Manager's Impermanence support already provided by the NixOS Impermanence module.

Do **not** manually import Impermanence's Home Manager module.

The structure should be:

```nix
{ ... }:

{
  home.persistence."/persist" = {
    directories = [
      # Authoritative user data.
      "Desktop"
      "Documents"
      "Downloads"
      "Development"
      "Music"
      "Pictures"
      "Public"
      "Templates"
      "Videos"

      # Credentials and security state.
      {
        directory = ".ssh";
        mode = "0700";
      }
      {
        directory = ".gnupg";
        mode = "0700";
      }
      ".pki"

      # Application state selected by the completed audit.
      ".android"
      ".codex"
      ".plastic4"
      ".vscode"
      ".zen"

      # Add only audited children of .config/.local here.
      # Examples:
      # ".config/<stateful-application>"
      # ".local/share/keyrings"
      # ".local/share/Steam"
    ];

    files = [
      # Add audited individual persistent files only when needed.
    ];
  };
}
```

This is the shape, not permission to skip the audit.

Before final implementation, replace broad temporary entries with the actual audited final list.

The final file should contain **no unexplained directory**.

Every persistent entry must correspond to a `P` or deliberately accepted `R` entry in the state ledger.

---

# 14. Prepare the persistent home backing tree

Before changing `/home`, create the backing directory:

```bash
sudo install \
    -d \
    -m 0700 \
    -o p2949 \
    -g users \
    /persist/home/p2949
```

Confirm:

```bash
stat -c '%A %a %U:%G %n' /persist/home/p2949
```

Expected ownership:

```text
p2949:users
```

Do not put this path itself into Home Manager's `persistentStoragePath`; `home.persistence."/persist"` automatically handles the home path.

---

# 15. Copy the current home into the persistence backing tree

The safest first migration is to copy the current home into the persistent backing tree before narrowing it.

Use a root-owned rsync invocation so metadata is retained:

```bash
nix shell nixpkgs#rsync
```

Then:

```bash
sudo rsync \
    -aHAX \
    --numeric-ids \
    --info=progress2 \
    /home/p2949/ \
    /persist/home/p2949/
```

Verify with a dry run:

```bash
sudo rsync \
    -aHAXn \
    --numeric-ids \
    --delete \
    /home/p2949/ \
    /persist/home/p2949/
```

At this stage a clean dry-run should show no unexplained differences.

This full copy is a migration safety measure.

It does **not** mean the complete home is declared persistent.

Only paths listed by Impermanence will appear in the active home after cutover.

The undeclared data under `/persist/home/p2949` can be pruned later after the new policy is proven.

---

# 16. Validate credentials before home cutover

Explicitly confirm that every credential-bearing directory expected to survive exists in the persistent backing tree.

Check metadata only; do not print secret contents.

Example:

```bash
for path in \
    /persist/home/p2949/.ssh \
    /persist/home/p2949/.gnupg \
    /persist/home/p2949/.pki \
    /persist/home/p2949/.codex
do
    if [[ -e "$path" ]]; then
        stat -c '%A %a %U:%G %n' "$path"
    fi
done
```

Also check application-profile directories selected by the audit.

Do not proceed until every required persistent path is represented beneath `/persist/home/p2949`.

---

# 17. Make `/home` part of the ephemeral root

Edit:

```text
hosts/desktop/disko.nix
```

Remove the active `@home -> /home` mount declaration from the desired Disko configuration.

The final desired Disko layout should no longer contain:

```nix
"@home" = {
  mountpoint = "/home";
  mountOptions = btrfsMountOptions;
};
```

Do **not** physically delete the existing `@home` Btrfs subvolume.

The currently existing physical subvolume remains on disk as rollback material.

After this configuration change:

```text
/home
```

is simply a directory inside `@root`.

Therefore the existing normal root reset automatically makes undeclared home state ephemeral.

No second home-reset script is required.

---

# 18. Add evaluation assertions for the intended home model

The configuration should make accidental reintroduction of a separate persistent `/home` obvious.

Add a small assertion in the most appropriate persistence/storage module or host persistence policy:

```nix
assertions = [
  {
    assertion = !(config.fileSystems ? "/home");
    message = "Granular Impermanence requires /home to live inside the ephemeral root.";
  }
];
```

If the implementation architecture makes a direct assertion awkward, provide an equivalent evaluation test.

The important invariant is:

```text
normal desktop configuration must not independently mount /home
```

---

# 19. Add an automated home Impermanence test before physical rollout

Create a dedicated test under the existing storage test hierarchy, for example:

```text
tests/storage/impermanence-home.nix
```

The test must prove at least:

### First boot

Create:

```text
/home/tester/persistent-data/survives
/home/tester/.cache/disappears
/home/tester/undeclared-state/disappears
```

The first path must be declared persistent.

The other two must not be.

Reboot.

### Second boot

Assert:

```text
persistent-data/survives exists
.cache/disappears does not exist
undeclared-state/disappears does not exist
```

Also assert:

```text
/home is not a separate @home-style persistent filesystem
```

Then create another ephemeral sentinel and reboot again.

### Third boot

Repeat the persistence/disappearance assertions.

This makes repeated-reset behavior part of the test, not a one-boot coincidence.

Register the test in the existing `tests/` registry.

---

# 20. Validate the home cutover offline

Run formatting and repository checks:

```bash
cd /etc/nixos

nix fmt
nix flake check
```

Build the desktop:

```bash
nix build \
    '.#nixosConfigurations.desktop.config.system.build.toplevel' \
    --no-link
```

Build/run the new home persistence test.

Also evaluate the mount model:

```bash
nix eval \
    '.#nixosConfigurations.desktop.config.fileSystems' \
    --json \
    | jq
```

Confirm that the desired system no longer declares `/home` as an independent filesystem.

Do not reboot until all evaluation and VM checks pass.

---

# 21. Install the home cutover as a next-boot generation

Use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Do not use `switch` for this first filesystem-boundary change.

Before reboot, record:

```bash
readlink -f /run/current-system
sudo nixos-rebuild list-generations
findmnt /home
```

Also verify the physical rollback source still exists:

```bash
sudo btrfs subvolume list /mnt/btrfs-top \
    | grep '@home'
```

---

# 22. First physical boot with ephemeral home

Reboot normally.

Immediately verify:

```bash
findmnt /
findmnt /home || true
findmnt /persist
```

The required result is:

```text
/       -> @root
/home   -> NOT a separate @home filesystem
/persist -> @persist
```

Check the home directory:

```bash
stat -c '%A %a %U:%G %n' /home/p2949
```

Check declared persistence mounts:

```bash
findmnt -R /home/p2949
```

Verify that known persisted directories exist.

Verify that `.cache` is not a persistence bind mount:

```bash
findmnt -T /home/p2949/.cache || true
```

---

# 23. Prove physical home ephemerality

Create physical sentinels.

Ephemeral:

```bash
mkdir -p ~/.cache/impermanence-test
echo ephemeral > ~/.cache/impermanence-test/cache-sentinel

mkdir -p ~/undeclared-impermanence-test
echo ephemeral > ~/undeclared-impermanence-test/home-sentinel
```

Persistent:

```bash
mkdir -p ~/Documents/impermanence-test
echo persistent > ~/Documents/impermanence-test/document-sentinel
```

If a state directory such as `.codex` is declared persistent, create a harmless test file there too:

```bash
mkdir -p ~/.codex
echo persistent > ~/.codex/impermanence-sentinel
```

Reboot.

Verify:

```bash
test ! -e ~/.cache/impermanence-test/cache-sentinel
test ! -e ~/undeclared-impermanence-test/home-sentinel

test -e ~/Documents/impermanence-test/document-sentinel
test -e ~/.codex/impermanence-sentinel
```

Repeat at least once more.

The physical acceptance condition is:

```text
two consecutive normal reboot cycles:
persistent sentinels survive
ephemeral sentinels disappear
```

---

# 24. Validate actual application state after the home cutover

The persistence model is not complete merely because test files behave correctly.

Open each application whose state was classified `P` or `R`.

For each one verify the state that justified persistence.

Examples:

### Browser / Zen

Verify:

```text
profile exists
expected extensions exist
bookmarks/history if intended persist
authentication cookies/session if intended persist
```

### Codex

Verify:

```text
authentication survives
expected configuration survives
```

### VS Code

Verify:

```text
extensions selected for persistence exist
workspace/user state selected for persistence survives
```

### Android

Verify as applicable:

```text
ADB identity survives
AVDs selected for persistence survive
debug signing identity survives
```

### Steam

Verify:

```text
actual Steam library/profile state is available
no accidental dependence on an undeclared ~/.steam path
```

### Plastic/Unity VCS

Verify:

```text
required identity/auth/config state survives
```

Record any newly discovered required paths in the audit ledger and persistence declaration.

If a new persistent path is discovered:

```text
declare it
copy it from old @home or migration backing tree
rebuild
repeat the reboot test
```

Do not paper over missing state by remounting all of `@home`.

---

# 25. Narrow temporary broad home persistence

If the first transition temporarily persisted broad containers such as:

```text
.config
.local
```

now split them.

For every child:

```text
.config/<child>
.local/bin
.local/share/<child>
.local/state/<child>
```

assign:

```text
E
D
R
P
M
```

The final `home/p2949/persistence.nix` should persist only:

```text
P
and deliberately accepted R
```

Remove `E` and `D`.

Split `M`.

After each narrowing batch:

```bash
nix flake check
sudo nixos-rebuild boot --flake '.#desktop'
reboot
verify applications
```

The home phase is finished only when whole-container persistence exists solely where there is an explicit reason for it.

---

# 26. Prune undeclared migration data from `/persist/home/p2949`

After repeated physical acceptance and application verification, compare:

```text
what exists in /persist/home/p2949
vs
what is actually declared persistent
```

Anything copied there only for migration safety but now classified `E` or `D` should be removed from `/persist`.

Do this only after confirming the original `@home` migration snapshot or source remains available until final retirement.

The goal is not merely hidden junk.

The goal is a persistent backing tree that itself reflects the declared contract.

---

# 27. Begin the `/var` audit

Do not remove the `/var` mount before completing this stage.

Inventory:

```bash
sudo du -xhd1 /var | sort -h
sudo du -xhd2 /var/lib | sort -h
sudo du -xhd2 /var/cache | sort -h
```

Inspect top-level metadata:

```bash
sudo find /var \
    -xdev \
    -mindepth 1 \
    -maxdepth 2 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort \
    > /tmp/var-inventory.txt
```

Review:

```text
/var/cache
/var/lib
/var/log
/var/spool
/var/tmp
```

Also review the previously collected:

```text
/tmp/fatrace-var-writes.log
/tmp/var-btrfs-diff.txt
```

Every mutable service directory that is required across reboot must receive an explicit classification.

---

# 28. Required starting `/var` policy

Use this as the starting policy, then adjust according to the audit.

## Ephemeral by default

```text
/var/cache
/var/tmp
/var/lib/systemd/coredump    unless deliberately retained
generated caches
temporary application indexes
reconstructable transient service state
```

## Explicitly persistent

At minimum evaluate and normally retain:

```text
/var/lib/nixos
/var/lib/systemd/random-seed
```

`/var/lib/nixos` should normally remain persistent because NixOS uses it for persistent system allocation/state that should not be casually regenerated.

`/var/lib/systemd/random-seed` should remain persistent so entropy state is carried safely across boots.

## Already independently persistent

```text
/var/lib/nixos-optimization
```

This remains provided by `@optimization`.

It does not need to be copied into `/persist`.

## Logs

Make an explicit policy choice.

For maximum ephemerality:

```text
journal/logs -> ephemeral
```

If cross-boot forensic logs are intentionally required:

```text
/var/log -> P
```

Do not allow `/var` as a whole to remain persistent merely to retain logs.

## Service databases

Any discovered path such as:

```text
/var/lib/<service>
```

must be classified according to actual use.

If loss changes identity, destroys authoritative data, or breaks intended application behavior:

```text
P
```

If it is regenerated automatically and safely:

```text
E
```

If expensive but reconstructable:

```text
R
```

Unknown is not a final classification.

---

# 29. Extend system Impermanence declarations for `/var`

Edit:

```text
hosts/desktop/persistence.nix
```

Keep the existing explicit root persistence.

Add audited var state.

A likely minimum shape is:

```nix
{ username, ... }:

{
  environment.persistence."/persist" = {
    hideMounts = true;

    files = [
      "/etc/machine-id"

      {
        file = "/var/lib/systemd/random-seed";
        parentDirectory.mode = "0755";
      }
    ];

    directories = [
      {
        directory = "/etc/nixos";
        user = username;
        group = "users";
        mode = "0755";
      }

      {
        directory = "/etc/NetworkManager/system-connections";
        mode = "0700";
      }

      "/var/lib/nixos"

      # Add only audited persistent /var state.
      #
      # "/var/log"
      # "/var/lib/<required-service>"
    ];
  };
}
```

Do not blindly copy this example without comparing it with the completed `/var` audit.

The final declaration is the audit result.

---

# 30. Prepare `/persist/var` data before removing persistent `/var`

Impermanence will create declared backing paths, but migration data must be copied before cutover.

Create a migration backing area if necessary and copy each selected path.

Example for `/var/lib/nixos`:

```bash
sudo mkdir -p /persist/var/lib

sudo rsync \
    -aHAX \
    --numeric-ids \
    /var/lib/nixos/ \
    /persist/var/lib/nixos/
```

Example for logs if logs are intentionally persisted:

```bash
sudo mkdir -p /persist/var

sudo rsync \
    -aHAX \
    --numeric-ids \
    /var/log/ \
    /persist/var/log/
```

For the random seed, preserve metadata without displaying contents:

```bash
sudo install -d -m 0755 /persist/var/lib/systemd

if [[ -e /var/lib/systemd/random-seed ]]; then
    sudo cp \
        --preserve=mode,ownership,timestamps \
        /var/lib/systemd/random-seed \
        /persist/var/lib/systemd/random-seed
fi
```

Check only metadata:

```bash
sudo stat \
    /persist/var/lib/systemd/random-seed \
    2>/dev/null || true
```

Repeat for every `P` and accepted `R` path identified by the audit.

---

# 31. Make `/var` part of the ephemeral root

Edit:

```text
hosts/desktop/disko.nix
```

Remove the active:

```nix
"@var" = {
  mountpoint = "/var";
  mountOptions = btrfsMountOptions;
};
```

Do not physically delete the existing `@var`.

Keep:

```nix
"@optimization" = {
  mountpoint = "/var/lib/nixos-optimization";
  mountOptions = btrfsMountOptions;
};
```

After the change:

```text
/var
```

is an ordinary directory under `@root`.

Therefore it is reset whenever `@root` is reset.

The nested:

```text
/var/lib/nixos-optimization
```

is still mounted separately and persists intentionally.

---

# 32. Add assertions for the final var topology

Enforce:

```text
/var is not an independent persistent filesystem
/var/lib/nixos-optimization is still a deliberate persistent filesystem
```

Add an evaluation assertion/test equivalent to:

```nix
{
  assertion = !(config.fileSystems ? "/var");
  message = "Granular Impermanence requires /var to live inside the ephemeral root.";
}
```

Do not assert that nested `/var/lib/nixos-optimization` is absent; it is intentionally persistent.

---

# 33. Add an automated var Impermanence test

Create a test such as:

```text
tests/storage/impermanence-var.nix
```

The test must prove at minimum:

### Persisted

```text
/var/lib/nixos/<test sentinel>
/var/lib/systemd/random-seed or a test substitute
/var/lib/nixos-optimization/<test sentinel>
```

### Ephemeral

```text
/var/cache/<test sentinel>
/var/tmp/<test sentinel>
/var/lib/<undeclared-test-service>/<test sentinel>
```

Perform multiple boots.

Assert:

```text
persisted state remains
undeclared var state disappears
nested optimization mount remains intact
```

Avoid modifying actual sensitive random-seed semantics in the test; a dedicated fixture path can test file persistence while configuration evaluation separately confirms the real declaration.

---

# 34. Run all offline validation after the var change

Run:

```bash
cd /etc/nixos

nix fmt
nix flake check
```

Build:

```bash
nix build \
    '.#nixosConfigurations.desktop.config.system.build.toplevel' \
    --no-link
```

Run:

```text
root Impermanence tests
home Impermanence tests
var Impermanence tests
existing storage safety tests
reconstruction test affected by the changed Disko layout
```

The blank-disk/reconstruction path must be rerun because the desired disk layout has changed:

```text
@home and @var are no longer part of the intended fresh-install active layout
```

A fresh installation must reconstruct the new topology, not the old one.

---

# 35. Install the var cutover as next boot only

Use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Before reboot verify:

```bash
findmnt /var
findmnt /var/lib/nixos-optimization

sudo btrfs subvolume list /mnt/btrfs-top \
    | grep '@var'
```

The old physical `@var` must still exist.

Reboot normally.

---

# 36. First physical boot with ephemeral `/var`

Verify:

```bash
findmnt /
findmnt /var || true
findmnt /var/lib/nixos-optimization
findmnt /persist
```

Required result:

```text
/var is not an independent @var mount
/var/lib/nixos-optimization is still @optimization
/persist is still @persist
```

Check persistent paths:

```bash
findmnt -T /var/lib/nixos
findmnt -T /var/lib/systemd/random-seed
```

If `/var/log` was selected for persistence:

```bash
findmnt -T /var/log
```

---

# 37. Prove physical var ephemerality

Create:

```bash
sudo mkdir -p /var/cache/impermanence-test
echo ephemeral \
    | sudo tee /var/cache/impermanence-test/cache-sentinel >/dev/null

sudo mkdir -p /var/tmp/impermanence-test
echo ephemeral \
    | sudo tee /var/tmp/impermanence-test/tmp-sentinel >/dev/null
```

Create a harmless persistent test path only in a deliberately persisted test directory, or use the automated test for `/var/lib/nixos`.

For the independently persistent optimization mount:

```bash
sudo mkdir -p /var/lib/nixos-optimization/impermanence-test
echo persistent \
    | sudo tee /var/lib/nixos-optimization/impermanence-test/sentinel >/dev/null
```

Reboot.

Verify:

```bash
test ! -e /var/cache/impermanence-test/cache-sentinel
test ! -e /var/tmp/impermanence-test/tmp-sentinel

test -e /var/lib/nixos-optimization/impermanence-test/sentinel
```

Verify declared `/var` persistence paths are still present.

Repeat at least once more.

---

# 38. Verify services after ephemeral `/var`

After each physical boot:

```bash
systemctl --failed
systemctl is-system-running
```

Review the current boot for persistence-related errors:

```bash
journalctl -b \
    -p warning..alert \
    --no-pager
```

Search specifically for:

```bash
journalctl -b --no-pager \
    | grep -Ei \
      'permission denied|no such file|failed to start|read-only|persist|mount|var'
```

Any service that fails because previously hidden state was stored under `@var` must be investigated.

Do not solve failures by restoring whole `/var`.

Persist only the exact service state that actually needs to survive.

---

# 39. Validate `persistent-root` recovery semantics

The normal configuration now has:

```text
root + home + ordinary var = ephemeral
```

The existing `persistent-root` specialisation disables root reset.

That means under `persistent-root`:

```text
ordinary root-local home and var state can remain between recovery boots
```

This is acceptable and useful for recovery.

Test it explicitly.

Boot the `persistent-root` specialisation.

Create recovery-only sentinels:

```text
/home/p2949/recovery-root-test
/var/tmp/recovery-root-test
```

Reboot into `persistent-root` again.

They should remain because root was not reset.

Then boot normal mode.

They should disappear because the normal root reset resumes.

Explicitly persisted Impermanence state must survive both modes.

This proves that the specialisation still means:

```text
normal          -> ephemeral root
persistent-root -> retain root for recovery/debugging
```

without reintroducing `@home` or `@var`.

---

# 40. Audit top-level filesystem semantics

After home and var are complete, verify the whole machine.

Use:

```bash
for path in \
    / \
    /boot \
    /dev \
    /etc \
    /home \
    /nix \
    /proc \
    /root \
    /run \
    /srv \
    /sys \
    /tmp \
    /usr \
    /var \
    /persist \
    /var/lib/nixos-optimization \
    /.snapshots
do
    echo
    echo "===== $path ====="
    findmnt -T "$path" || true
done
```

The intended semantics are:

| Path | Final policy |
|---|---|
| `/` | ephemeral normal root |
| `/boot` | persistent |
| `/dev` | runtime virtual filesystem |
| `/etc` | ephemeral except declared persistence |
| `/home` | ephemeral except declared user persistence |
| `/nix` | persistent |
| `/proc` | runtime virtual filesystem |
| `/root` | ephemeral |
| `/run` | runtime tmpfs |
| `/srv` | ephemeral unless explicitly changed later |
| `/sys` | runtime virtual filesystem |
| `/tmp` | ephemeral |
| `/usr` | reconstructed/declarative |
| `/var` | ephemeral except declared state/nested mounts |
| `/persist` | persistent backing store |
| `/var/lib/nixos-optimization` | persistent |
| `/.snapshots` | persistent |

---

# 41. Create a final system-wide reboot sentinel matrix

Before one final normal reboot, create harmless sentinels.

## Must disappear

```text
/root/ephemeral-proof
/tmp/ephemeral-proof
/srv/ephemeral-proof
/home/p2949/.cache/ephemeral-proof
/home/p2949/undeclared-ephemeral-proof
/var/cache/ephemeral-proof
/var/tmp/ephemeral-proof
```

## Must survive

Use safe declared locations:

```text
/persist/ephemeral-project-proof
/home/p2949/Documents/persistent-proof
one declared application-state path
/var/lib/nixos-optimization/persistent-proof
```

Do not modify secret contents merely to test persistence.

Reboot.

Check every sentinel.

The test passes only if **all** expected-disappear paths disappeared and **all** expected-survive paths survived.

---

# 42. Inspect the final persistent backing store

The final `/persist` tree should contain only deliberate state.

Inspect:

```bash
sudo find /persist \
    -xdev \
    -mindepth 1 \
    -maxdepth 4 \
    -printf '%y %m %u:%g %p\n' \
    | sort
```

Compare it with:

```text
hosts/desktop/persistence.nix
home/p2949/persistence.nix
```

Every meaningful subtree beneath `/persist` must have a reason to exist.

Classify unexpected leftovers.

Remove stale migration-only copies after confirming they are not active persistence targets.

The end state must not be:

```text
everything copied into /persist but only some of it mounted
```

It should be:

```text
/persist itself is an intentional state store
```

---

# 43. Update the persistence contract

Update:

```text
docs/persistence-contract.md
```

Replace the old:

```text
/home (@home) -> persistent
/var  (@var)  -> persistent
```

with the final contract.

The document should state:

```text
/                  ephemeral on normal boot
/home              root-local and ephemeral by default
/var               root-local and ephemeral by default
/nix               persistent
/persist           persistent explicit-state backing store
/var/lib/nixos-optimization
                   persistent dedicated subvolume
/.snapshots         persistent
/boot              persistent

home paths          persist only when listed in home/p2949/persistence.nix
system paths        persist only when listed in hosts/desktop/persistence.nix
```

Also document that:

```text
persistent-root disables root reset and therefore temporarily makes
otherwise root-local home/var state persistent for recovery boots.
```

The contract should list path categories, not secret contents.

---

# 44. Make the automated persistence test a permanent regression guard

The finished repository must retain a test that proves the complete contract.

A single combined multi-boot test is preferable once the implementation stabilizes.

It should cover:

```text
root ephemeral state
home ephemeral state
home persistent state
var ephemeral state
var persistent state
nested @optimization persistence
machine-id persistence
persistent-root behavior
normal-mode reset after persistent-root
```

The test should fail if a future change accidentally:

```text
re-adds @home as /home
re-adds @var as /var
removes a required persistence bind
stops resetting root
turns a known-ephemeral path persistent
breaks nested optimization persistence
```

This converts the desired ephemerality into a maintained system invariant.

---

# 45. Retire the legacy `@home` and `@var` persistence mechanism

Do this only after:

```text
all automated tests pass
multiple physical normal boots pass
application state passes
persistent-root passes
the final sentinel matrix passes
/persist is audited
```

First inspect the old subvolumes one final time.

```bash
sudo du -sh \
    /mnt/btrfs-top/@home \
    /mnt/btrfs-top/@var

sudo btrfs subvolume show /mnt/btrfs-top/@home
sudo btrfs subvolume show /mnt/btrfs-top/@var
```

Compare remaining contents with active persistent data.

If no required data exists only in the old subvolumes, mark them safe to retire.

Be aware that deleting them prevents very old NixOS generations whose filesystem declarations require `@home` or `@var` from booting normally.

Therefore the retirement point is also the point at which rollback is intentionally bounded to generations using the new layout.

When that is accepted, delete the old inactive subvolumes:

```bash
sudo btrfs subvolume delete /mnt/btrfs-top/@home
sudo btrfs subvolume delete /mnt/btrfs-top/@var
```

If nested subvolumes are discovered, stop and inspect them rather than using recursive deletion blindly.

Confirm:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top
```

The old always-persistent home/var architecture is now gone.

---

# 46. Remove migration snapshots when they are no longer required

The read-only migration snapshots were created only to make the transition safe.

Once:

```text
old @home/@var have been retired
new persistence contract is accepted
required data exists in /persist
```

the migration snapshots may also be retired deliberately.

Do not let them become an accidental shadow persistence mechanism indefinitely.

List them:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top \
    | grep 'granular-impermanence'
```

Delete only the specifically identified migration snapshots after final confirmation.

---

# 47. Final source layout

The implementation should leave the relevant source structure approximately:

```text
NixosConf/
├── hosts/
│   └── desktop/
│       ├── default.nix
│       ├── disko.nix
│       ├── ephemeral-root.nix
│       ├── hardware-configuration.nix
│       └── persistence.nix
│
├── home/
│   └── p2949/
│       ├── default.nix
│       ├── persistence.nix
│       ├── cli.nix
│       ├── shell.nix
│       ├── xdg.nix
│       ├── desktop/
│       └── development/
│
├── modules/
│   └── storage/
│       └── ephemeral-btrfs-root/
│           ├── default.nix
│           ├── check.nix
│           └── reset.sh
│
├── tests/
│   └── storage/
│       ├── ...
│       └── granular-impermanence.nix
│
└── docs/
    ├── persistence-contract.md
    └── ephemeral-state-audit.md
```

No additional cleanup architecture is required for this objective.

---

# 48. Final acceptance checklist

The ephemeral-state project is **not complete** until every item below passes.

## Filesystem topology

- [ ] `@root` provides `/`.
- [ ] no `@home` subvolume is mounted at `/home`.
- [ ] no `@var` subvolume is mounted at `/var`.
- [ ] `/nix` remains persistent.
- [ ] `/persist` remains persistent.
- [ ] `/.snapshots` remains persistent.
- [ ] `/boot` remains persistent.
- [ ] `/var/lib/nixos-optimization` remains persistent.

## Root

- [ ] undeclared `/etc` state disappears on normal reboot.
- [ ] `/root` state disappears on normal reboot.
- [ ] `/tmp` state disappears on normal reboot.
- [ ] `/srv` state disappears on normal reboot.
- [ ] `/etc/machine-id` survives.
- [ ] `/etc/nixos` survives.
- [ ] NetworkManager connections survive.

## Home

- [ ] `/home/p2949` is root-local rather than a separate persistent filesystem.
- [ ] `.cache` disappears across normal reboot.
- [ ] undeclared home directories disappear.
- [ ] declared user data survives.
- [ ] credentials selected for persistence survive.
- [ ] browser profile selected for persistence survives.
- [ ] development/project data survives.
- [ ] stateful development tools selected for persistence survive.
- [ ] Home Manager reconstructs declarative configuration.
- [ ] `.config` has been audited rather than blindly persisted as a whole.
- [ ] `.local` has been audited rather than blindly persisted as a whole.

## Var

- [ ] `/var` is root-local rather than a separate persistent filesystem.
- [ ] `/var/cache` disappears.
- [ ] `/var/tmp` disappears.
- [ ] undeclared service state disappears.
- [ ] `/var/lib/nixos` survives.
- [ ] system random-seed state survives.
- [ ] every additional persistent service DB has an explicit justification.
- [ ] `/var/lib/nixos-optimization` survives independently.
- [ ] log persistence/ephemerality is an explicit policy rather than a side effect.

## Boot modes

- [ ] normal boot resets root.
- [ ] normal boot therefore resets undeclared home and var state.
- [ ] `persistent-root` disables reset.
- [ ] root-local recovery sentinels survive repeated `persistent-root` boots.
- [ ] returning from `persistent-root` to normal mode discards those undeclared sentinels.
- [ ] explicitly persisted state works in both modes.

## Applications

- [ ] Zen/browser required profile state works.
- [ ] Codex required state works.
- [ ] VS Code required state works.
- [ ] Android state selected for persistence works.
- [ ] Steam state selected for persistence works.
- [ ] Plastic/Unity VCS state selected for persistence works.
- [ ] any other path classified `P` or `R` has been functionally checked.

## Tests

- [ ] `nix fmt` passes.
- [ ] `nix flake check` passes.
- [ ] desktop system builds.
- [ ] home multi-boot test passes.
- [ ] var multi-boot test passes.
- [ ] combined granular-Impermanence regression test passes.
- [ ] changed Disko layout passes reconstruction testing.
- [ ] physical repeated-boot sentinel tests pass.

## Persistent storage hygiene

- [ ] `/persist` has been audited.
- [ ] no unexplained full-home migration copy remains.
- [ ] no unexplained full-var migration copy remains.
- [ ] old active `@home` persistence has been retired.
- [ ] old active `@var` persistence has been retired.
- [ ] obsolete migration snapshots have been deliberately handled.
- [ ] `docs/persistence-contract.md` describes the final actual state.

---

# 49. Definition of done

At the end of this plan, the machine should obey this rule:

```text
NORMAL BOOT

@root is replaced
        │
        ├── /etc       clean
        ├── /root      clean
        ├── /home      clean
        ├── /srv       clean
        ├── /tmp       clean
        └── /var       clean
              │
              └── except /var/lib/nixos-optimization separate mount

NixOS activation
        │
        ├── reconstructs declarative system state
        └── bind-mounts explicitly persisted system state

Home Manager activation
        │
        ├── reconstructs declarative user configuration
        └── bind-mounts explicitly persisted user state

result:
    undeclared mutable state does not survive reboot
```

Persistent state is reduced to deliberate islands:

```text
/boot
/nix
/persist
/.snapshots
/var/lib/nixos-optimization

plus paths explicitly exposed from /persist by Impermanence
```

The project is complete when persistence is no longer determined by:

```text
"this happened to live under /home"
or
"this happened to live under /var"
```

and is instead determined by:

```text
"this state was explicitly audited, classified, and declared persistent."
```

That is the final granular ephemeral model.
