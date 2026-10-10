# Execution ledger — 2026-10-10

This is the supplied implementation plan, retained below as the sequencing
reference. Historical assumptions below are superseded by this live ledger.
Pasted citation placeholders are not usable source references.

- [x] Read the complete supplied goal and implementation plan.
- [x] Start gate: granular integration is an ancestor of clean main
  `9a84d77dd2ae141575355b32e6b32333e70859bd`. Private completion and integration
  receipts under `/persist/granular-migration` accept Unity preferences,
  pruning, post-pruning physical proof and exact legacy retirement.
  The migration copy service is absent/inactive; no migration is pending.
- [x] Live system running, no failed units; home resolves to `/@root`.
- [x] Baseline `nix flake check` and desktop toplevel build passed.
  Baseline closure: `/nix/store/6rn4ggk32wcqrhcdv2chr55daqxxh026-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- [x] No existing `/home/p2949/.local/share/PrismLauncher` state found.
- [x] Created isolated `feat/prism-launcher` from the revision above.
- [x] Added stock wrapped Home Manager Prism and complete private `0700`
  persistent root; preliminary mixed-container audit updated.
- [x] Pinned package evaluates to 11.1.1. Inspected pinned Nixpkgs wrapper:
  Java 25/21/17/8, Qt Wayland, driver/runtime libraries and GameMode support.
- [x] Candidate formatting, checks, closure build and evaluated mount review.
  Formatting/diff review and evaluated package/private bind mount passed.
  Initial candidate flake check failed at `optimization-control-identity`:
  the newer framework asserts that every desktop change has the exact frozen
  stock closure. Prism necessarily changes it. The user explicitly chose
  "Allow ordinary desktop changes; preserve frozen benchmark control".
  Exact closure admission now lives in the explicit
  `.#optimization-control-identity` build target; ordinary checks retain input
  identity and the existing forbidden optimization dependency guard. The frozen
  `stock.nix`, tags and benchmark runtime rejection remain unchanged.
  Negative validation correctly rejects the Prism candidate with the specific
  frozen-control diagnostic; positive frozen-tag validation passed.
  Full candidate `nix flake check` passed, including granular storage regression.
  Candidate desktop build passed:
  `/nix/store/2mmvgbyd32qahwhy3y01l66s7vqwn3yk-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Closure contains wrapped Prism and Java 25/21/17/8; generated systemd mount
  binds `/persist/home/p2949/.local/share/PrismLauncher` to the live root.
- [x] Boot-only installation passed: generation 48 points to the candidate
  closure above. Generation 47 remains available; running system stays on
  `6rn4ggk32wcqrhcdv2chr55daqxxh026`. Private validation/install logs are in
  `/home/p2949/Documents/.prism-integration` (persistent, mode 0700).
- [x] User-controlled normal reboot and private mount verification.
  Boot ID `87d07fff-fe78-45a5-b61b-df2f04db0ef2`: running/profile closures
  match generation 48. System running with no failed units; Prism resolves to
  wrapped Nix store 11.1.1. Root mount FSROOT is
  `/@persist/home/p2949/.local/share/PrismLauncher`, owned `p2949:users`, mode 700.
  Native Wayland Quick Setup observed (`xwayland=false`). User confirms setup,
  UI and Java detection work. Process environment independently exposes the
  four Nix Java paths; each executable's version check passed (25, 21, 17, 8).
  User subsequently completed normal Quit; independent process check confirms
  Prism exited. Quiesced pre-account tree/size inventories are saved privately
  as `prism-tree-before-account.txt` and `prism-sizes-before-account.txt`.
  `accounts.json` exists, which alone does not establish authentication. No
  account contents were read. The rejected automatic compositor close attempt
  did not mutate state; the user closed Prism normally.
- [ ] Launcher/Java/UI acceptance; Microsoft authentication; vanilla game,
  GPU/audio/input and test-world acceptance; structural first-run audit.
  Launcher/UI/Java gates pass as above. Microsoft/vanilla-world acceptance is
  now requested from the user with Prism reopened. Host `amdgpu` binds Navi48;
  PipeWire, PipeWire Pulse and WirePlumber are active; GameMode is available
  and inactive outside a requested GameMode session. These host checks do not
  establish actual game rendering/audio. Post-boot documentation check passed.
  User's first instance launch failed to enter a world. Supplied log identifies
  Minecraft 26.3 with Fabric Loader 0.19.5, Java25 and a player-name placeholder
  `No Minecraft profile` (20 characters). Login hello packet rejects it at
  the 16-character limit; Realms also reports missing profile claims.
  This proves a profile-resolution failure, not valid account acceptance.
  Log shows native Wayland game window, RX9070XT through Zink/RADV and OpenAL
  initialization, but world/input/audible-output acceptance remains pending.
  Resolve Java profile in the user's Microsoft/Minecraft account and refresh
  Prism authentication through its UI; do not edit credentials or trim the
  placeholder. Repeat with a true vanilla instance (no Fabric) for baseline.
- [ ] Phase 1 state survival proof and acceptance commit.
- [ ] Evidence-backed cache/log exclusions, checks and boot-only installation.
- [ ] Normal reboot: parent sentinel survives, cache/log sentinels disappear;
  account/instance/world/assets/libraries and game functionality survive.
- [ ] Remove proof state, final review/checks, acceptance commit and integration.

Runtime acceptance is pending. Do not add cache/log exclusions before the
observed workload gate. `meta` and `java` require separate later evidence.
Microsoft authentication and physical visual/audio observations require the
user; automated builds cannot satisfy those gates. Reboots remain user-controlled.
No credentials or runtime game data belong in this ledger or Git.

## Next user-controlled gate

Generation 48 normal boot, private mount, launcher and Java acceptance have
passed. The pre-account structural tree is captured. Complete Microsoft
authentication and vanilla instance/world checks, then close game and launcher
normally so the agent can audit the real post-workload state. Preserve all state
and keep the whole launcher root persistent until that evidence is accepted.
The existing package checkpoint commits record implementation only, not
completed physical/runtime acceptance.

---

I’d treat this as a small, self-contained workstation feature with its own acceptance proof, rather than just adding one package line. The plan below deliberately preserves your current “ephemeral by default, persistent by declaration” model and keeps the first Prism install separate from the later cache classification.

# Prism Launcher on NixOS — Detailed Implementation Plan

## 1. Objective

Integrate **Prism Launcher** into the current NixOS workstation in a way that is:

- fully declarative where appropriate;
- compatible with the existing Home Manager architecture;
- compatible with Hyprland/Wayland;
- compatible with the RX 9070 XT and existing Mesa/RADV stack;
- compatible with the existing GameMode infrastructure;
- able to automatically use appropriate Java runtimes;
- safe under the workstation's granular Impermanence design;
- persistent for Minecraft accounts, instances, worlds, mods and expensive game data;
- ephemeral for genuinely disposable Prism cache/log data;
- independently testable and reversible;
- documented in the existing ephemeral-state audit.

The end state should conceptually be:

```text
NixOS
│
├── system gaming infrastructure
│   ├── GameMode
│   ├── Gamescope
│   ├── MangoHud
│   ├── Mesa/RADV
│   └── PipeWire
│
└── Home Manager
    └── Prism Launcher
        │
        ├── Nix-provided Java runtimes
        ├── Microsoft account
        ├── Minecraft instances
        ├── worlds
        ├── mods
        ├── assets/libraries
        │
        └── ~/.local/share/PrismLauncher
            │
            ├── persistent application data
            │
            └── selected ephemeral cache/log children
```

Prism's normal Linux application root is `~/.local/share/PrismLauncher`. Upstream documents `assets`, `cache`, `icons`, `instances`, `java`, `libraries`, `logs`, `meta`, skins, themes and similar content underneath that root. :chatgpt-content-reference{index="0"}

---

# 2. Current repository assumptions

This plan is written specifically for the current `P2949/NixosConf` architecture.

Ordinary user desktop applications currently live under:

```text
home/p2949/desktop/
```

and `home/p2949/desktop/default.nix` presently installs applications such as Thunar, `pavucontrol`, and VS Code through `home.packages`. 

System-level gaming infrastructure lives separately in:

```text
modules/gaming/default.nix
```

where Steam, GameMode, Gamescope and MangoHud are configured. 

That distinction should remain:

```text
modules/gaming/
    system gaming infrastructure

home/p2949/desktop/
    user-facing Prism Launcher package
```

Do not add Prism to `environment.systemPackages`.

Do not make a new system-level Prism module.

Do not introduce Flatpak merely for Prism.

Do not use `prismlauncher-unwrapped`.

Do not globally install Java just for Minecraft.

Do not create a Prism-specific flake input.

The standard Nixpkgs `prismlauncher` wrapper already provides the relevant Linux runtime environment and supplies Java 25, 21, 17 and 8 through `PRISMLAUNCHER_JAVA_PATHS`. 

The current pinned NixOS 26.05 package is Prism Launcher **11.1.1**. 

---

# 3. Important prerequisite: finish the active Impermanence work first

## 3.1 Do not implement Prism on the currently moving candidate

The granular Impermanence architecture itself is now physically proven end-to-end: `/home` and ordinary `/var` are root-local, and the complete normal → recovery → recovery → normal physical sequence has passed. :chatgpt-content-reference{index="5"}

However, the current branch still has the narrow Unity Preferences persistence amendment in its final validation/acceptance path, followed by `/persist` pruning, old `@home`/`@var` retirement and final source/CI work. :chatgpt-content-reference{index="6"}

Therefore:

```text
DO NOT
    add Prism now
    change the persistence manifest now
    change ephemeral-app-state.nix now
```

Doing so would modify the persistence policy while its final evidence is still being established.

## 3.2 Prism implementation start gate

Start this plan only once the granular Impermanence work has reached a stable accepted point.

Minimum prerequisite:

```text
[ ] Unity Preferences correction accepted
[ ] final persistence policy frozen
[ ] /persist pruning complete
[ ] post-pruning physical proof passes
[ ] old @home/@var retirement completed if still planned
[ ] exact source is clean
[ ] no destructive migration operation is pending
```

Ideally also:

```text
[ ] granular branch merged into its intended parent
[ ] exact-head CI green
```

## 3.3 Why this matters

Prism itself introduces a new persistent application tree:

```text
.local/share/PrismLauncher
```

That changes the evaluated persistence manifest.

It therefore should be the **first ordinary application addition after the Impermanence project**, not another variable inside that project.

---

# 4. Create an isolated implementation branch

After the Impermanence work is frozen:

```bash
cd /etc/nixos

git status --short
git branch --show-current
git rev-parse HEAD
```

Require:

```text
clean working tree
accepted source revision
no migration operation pending
```

Then create a dedicated branch:

```bash
git switch -c feat/prism-launcher
```

Record the starting point:

```bash
git rev-parse HEAD
git status --short
```

Optional but useful:

```bash
git tag --points-at HEAD
```

The purpose of the branch is to make this progression obvious:

```text
accepted workstation
        ↓
package + persistence
        ↓
first runtime validation
        ↓
state audit
        ↓
granular cache exclusions
        ↓
reboot proof
        ↓
accepted Prism integration
```

---

# 5. Capture the pre-change baseline

Before editing anything:

```bash
cd /etc/nixos

nix flake check

nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link
```

Both should pass.

Also capture:

```bash
git status --short
```

which should be empty.

This tells us that any subsequent failure was introduced by the Prism work rather than inherited from the baseline.

---

# 6. Check for existing Prism data before adding the persistence mount

This step matters because adding an Impermanence bind mount over existing state can hide the existing directory beneath the mount.

Run:

```bash
PRISM_ROOT="$HOME/.local/share/PrismLauncher"

if [[ -e "$PRISM_ROOT" ]]; then
    echo "Existing Prism state found:"
    du -sh "$PRISM_ROOT"
    find "$PRISM_ROOT" -maxdepth 2 -printf '%y %p\n' | sort
else
    echo "No existing Prism state"
fi
```

Do **not** print the contents of files such as:

```text
accounts.json
```

Prism loads its account list from `accounts.json`, so treat the application directory as potentially containing authentication material. 

### Expected case

For a fresh installation:

```text
No existing Prism state
```

Proceed normally.

### If existing state is found

Stop the normal procedure before activating the new persistence mount.

First make a private backup somewhere already persistent.

For example:

```bash
BACKUP="$HOME/Documents/.prism-pre-persistence-backup"

install -d -m 0700 "$BACKUP"

rsync -a \
  "$HOME/.local/share/PrismLauncher/" \
  "$BACKUP/"
```

Verify structurally:

```bash
rsync -ani \
  "$HOME/.local/share/PrismLauncher/" \
  "$BACKUP/"
```

Expected output:

```text
nothing
```

Do not delete this backup until Prism has survived reboot testing.

---

# 7. Phase 1 — install Prism Launcher declaratively

Edit:

```text
home/p2949/desktop/default.nix
```

Current architecture already places desktop applications here. 

Add:

```nix
    # Gaming
    prismlauncher
```

The relevant part should become approximately:

```nix
  home.packages = with pkgs; [
    # File manager
    thunar

    # Wayland utilities
    wl-clipboard
    grim
    slurp

    # Desktop utilities
    brightnessctl
    pavucontrol

    # Gaming
    prismlauncher

    # Work
    vscode
  ];
```

Do **not** add:

```nix
jdk21
jdk17
jdk8
```

Do **not** add:

```nix
programs.java.enable = true;
```

Do **not** create a manual `JAVA_HOME`.

Do **not** override Prism yet.

The Nixpkgs wrapper already exposes:

```text
jdk25
jdk21
jdk17
jdk8
```

to Prism. 

---

# 8. Phase 1 — declare the Prism application root persistent

Edit:

```text
home/p2949/persistence.nix
```

Your current configuration persists selected user state through:

```nix
home.persistence."/persist"
```

rather than preserving all of `/home`. 

Add Prism to the `directories` list.

I recommend:

```nix
      # Minecraft launcher state, authentication, instances/worlds and
      # deliberately retained expensive game data.
      {
        directory = ".local/share/PrismLauncher";
        mode = "0700";
      }
```

Use `0700` because this tree can contain account/authentication state.

At this stage, persist the **entire Prism root**.

Do not try to split caches yet.

The initial state should be:

```text
.local/share/PrismLauncher     persistent as one unit
```

not:

```text
accounts.json                  separate mount
instances                      separate mount
assets                         separate mount
...
```

This is both safer and more compatible with applications that atomically replace state files.

---

# 9. Phase 1 — document the initial policy

Edit:

```text
docs/ephemeral-state-audit.md
```

Your persistence configuration explicitly states that persisted entries are classified in this audit. 

Add Prism as a mixed application container.

For example:

```text
| .local/share/PrismLauncher | M |
Prism Launcher profile containing authoritative account/instance/world state
and deliberately retained expensive Minecraft data. Initial implementation
persists the complete application root; disposable children will be classified
after observing a real first-run workload. |
```

Use your existing classifications:

```text
P = authoritative state
R = deliberately retained expensive rebuild/download data
D = declaratively reconstructed
E = disposable runtime/cache data
M = mixed container
```

Your current audit already uses this model. 

At this stage do **not** claim that:

```text
cache
logs
meta
java
```

are actually ephemeral yet.

They are only candidates.

---

# 10. Format and inspect the first change

Run:

```bash
cd /etc/nixos

nixfmt \
  home/p2949/desktop/default.nix \
  home/p2949/persistence.nix
```

Then:

```bash
git diff --check
git diff
```

Expected files:

```text
home/p2949/desktop/default.nix
home/p2949/persistence.nix
docs/ephemeral-state-audit.md
```

Nothing else should have changed.

Then:

```bash
git status --short
```

---

# 11. Run offline validation before activation

Run:

```bash
nix flake check
```

Then:

```bash
nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link
```

Also verify Prism evaluates:

```bash
nix eval --raw \
  '.#nixosConfigurations.desktop.pkgs.prismlauncher.version'
```

Expected result on the current pinned package set:

```text
11.1.1
```

The exact version is not itself an acceptance criterion; the important point is that the package evaluates from the pinned `flake.lock`.

---

# 12. Inspect the evaluated Home Manager package set

Before booting, confirm Prism is actually present in the evaluated user environment.

A simple build of the final system is sufficient for correctness, but you can also search the closure:

```bash
SYSTEM="$(
  nix build \
    '.#nixosConfigurations.desktop.config.system.build.toplevel' \
    --no-link \
    --print-out-paths
)"

nix-store -qR "$SYSTEM" | grep -i prism
```

You should see Prism Launcher in the resulting closure.

---

# 13. Prefer a boot-only activation for the new persistence mount

Because this change introduces a new persistent bind mount inside an ephemeral home, I would **not make the first acceptance depend on live mount mutation**.

Use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

not initially:

```bash
sudo nixos-rebuild switch
```

Verify installation succeeded.

Then inspect generations:

```bash
sudo nixos-rebuild list-generations
```

Keep the previous accepted generation available.

---

# 14. Reboot into the Prism candidate

Perform one ordinary normal boot.

Do not select `persistent-root`.

After login:

```bash
git -C /etc/nixos rev-parse HEAD
```

and verify the expected source.

Then verify the system:

```bash
systemctl is-system-running
systemctl --failed
```

Expected:

```text
running
0 failed units
```

---

# 15. Verify Prism is installed

Run:

```bash
command -v prismlauncher
```

Then:

```bash
prismlauncher --version
```

The executable should resolve through the Nix profile/store rather than `/usr/bin`, `/opt`, an AppImage or Flatpak.

Also check:

```bash
which prismlauncher
readlink -f "$(which prismlauncher)"
```

---

# 16. Verify the persistent application root

Before launching Prism:

```bash
PRISM_ROOT="$HOME/.local/share/PrismLauncher"

findmnt -T "$PRISM_ROOT"
```

Also:

```bash
stat -c '%a %U:%G %n' "$PRISM_ROOT"
```

Desired result:

```text
owned by p2949
private user directory
persistence-backed
```

The mode should correspond to the requested private policy.

Do not proceed if the path unexpectedly resolves only to disposable `@root` storage.

---

# 17. First Prism launch — launcher only

Start:

```bash
prismlauncher
```

Do not immediately install a large modded setup.

First verify the launcher itself.

Check:

```text
[ ] window appears normally under Hyprland
[ ] Wayland/Qt rendering is correct
[ ] fonts render correctly
[ ] file dialogs work
[ ] no obvious missing-library errors
[ ] audio-related settings/UI do not error
```

The Nixpkgs wrapper includes Qt Wayland support plus the Linux runtime libraries needed by Minecraft/Prism. 

---

# 18. Verify Java detection

In Prism:

```text
Settings
→ Java
```

Use its Java auto-detection.

Verify that Prism sees Nix-provided JDKs rather than requiring a downloaded Java runtime.

Expected available generations should include versions corresponding to:

```text
Java 25
Java 21
Java 17
Java 8
```

Do not manually configure:

```text
/usr/bin/java
```

because that is not how this NixOS setup should work.

Do not enable Prism-managed Java downloads unless an actual compatibility problem later requires them.

Use the Minecraft-version-appropriate runtime Prism recommends.

---

# 19. Inspect the first-run Prism filesystem before authentication

Close Prism.

Run:

```bash
find "$PRISM_ROOT" \
  -maxdepth 2 \
  -printf '%y %p\n' \
  | sort \
  > /tmp/prism-tree-before-account.txt
```

Also:

```bash
du -h -d 2 "$PRISM_ROOT" | sort -h
```

Do not print file contents.

This establishes what Prism creates before account and game installation.

---

# 20. Add the Microsoft/Minecraft account

Launch Prism again.

Use Prism's normal Microsoft authentication flow.

Do not manually manipulate `accounts.json`.

After successful login:

```text
[ ] account visible
[ ] account status valid
[ ] skin/profile resolves
```

Close Prism cleanly.

Then verify only structural existence:

```bash
test -f "$PRISM_ROOT/accounts.json" &&
  echo "accounts.json exists"
```

Do not:

```bash
cat accounts.json
```

Do not put the file into:

```text
Git
plan.md
docs/
terminal transcripts
screenshots
```

It is application authentication state.

---

# 21. Create a minimal validation instance

Before installing your eventual performance-oriented Minecraft setup, create a simple baseline instance.

Prefer:

```text
current Minecraft release
vanilla
no shaders
no content mods
```

The purpose is not benchmarking.

The purpose is proving:

```text
Prism
→ Java
→ Minecraft
→ LWJGL
→ Mesa/RADV
→ RX 9070 XT
→ PipeWire
```

Create the instance and let Prism download everything.

---

# 22. Launch vanilla Minecraft once

Launch the instance.

Verify:

```text
[ ] Java starts
[ ] Minecraft reaches menu
[ ] graphics render correctly
[ ] RX 9070 XT is used
[ ] mouse/keyboard work
[ ] audio works
[ ] game can create/load a world
[ ] game exits normally
```

Create a disposable test world if desired.

This is important because launching the Prism GUI proves much less than launching Minecraft itself.

---

# 23. Verify the instance data actually exists

After closing Minecraft and Prism:

```bash
find "$PRISM_ROOT/instances" \
  -maxdepth 3 \
  -printf '%y %p\n' \
  | head -200
```

You should now have actual instance data.

The upstream Prism directory model identifies `instances` as user instance storage and `assets`/`libraries` as Minecraft runtime data. :chatgpt-content-reference{index="14"}

---

# 24. Capture the post-workload application tree

Run:

```bash
find "$PRISM_ROOT" \
  -maxdepth 2 \
  -printf '%y %p\n' \
  | sort \
  > /tmp/prism-tree-after-game.txt
```

Compare:

```bash
diff -u \
  /tmp/prism-tree-before-account.txt \
  /tmp/prism-tree-after-game.txt
```

Also inspect sizes:

```bash
du -h -d 2 "$PRISM_ROOT" | sort -h
```

This is the evidence used to classify Prism state.

---

# 25. Initial state classification

Use the following as the **starting hypothesis**, then confirm it against the observed installation.

## Persistent `P` candidates

```text
accounts.json
prismlauncher.cfg
instances/
icons/
iconthemes/
themes/
catpacks/
```

These either contain authoritative user state or explicit customization.

## Retained `R` candidates

```text
assets/
libraries/
```

They are reconstructible but potentially large and expensive to redownload.

For this workstation, I recommend retaining them.

There is very little practical value in redownloading Minecraft assets/libraries every normal reboot merely to make the persistence model theoretically purer.

## Ephemeral `E` candidates

```text
cache/
logs/
```

These are explicitly identified upstream as cached downloads and logs. :chatgpt-content-reference{index="15"}

These are the strongest candidates to move back onto reset-root storage.

## Audit-first candidates

```text
meta/
java/
translations/
skins/
```

Do not classify these purely from their names.

Observe whether they exist and what the launcher does with them.

`meta` is upstream-described cached metadata, so it will probably ultimately be class `E`. `java` contains launcher-managed Java installations, but with the Nix wrapper you may not need Prism-managed Java at all. :chatgpt-content-reference{index="16"}

Treat those as hypotheses until your actual instance confirms them.

---

# 26. Update the audit from observed state

Edit:

```text
docs/ephemeral-state-audit.md
```

Replace the preliminary Prism entry with something more precise.

For example:

```text
| .local/share/PrismLauncher | M |
Microsoft/Minecraft account state, launcher settings, instances/worlds/mods and
user customization are persistent. Minecraft assets/libraries are deliberately
retained as expensive reconstructible state. Observed download caches and logs
are disposable and are overlaid onto reset-root storage. Other children remain
persistent until separately classified from real workload evidence. |
```

Do not claim `meta` or `java` are ephemeral unless the audit actually supports that.

---

# 27. Phase 2 — carve out proven disposable children

Now modify:

```text
home/p2949/ephemeral-app-state.nix
```

Your existing file already uses:

```nix
{
  parent = "...";
  children = [
    ...
  ];
}
```

for exactly this model: a persisted application container with selected children redirected to reset-root storage. 

Add:

```nix
  {
    parent = ".local/share/PrismLauncher";
    children = [
      "cache"
      "logs"
    ];
  }
```

Stop there initially.

Do **not** immediately add:

```nix
"meta"
"java"
```

unless the first-run audit justifies them.

That gives:

```text
PrismLauncher/
│
├── accounts.json       P
├── configuration       P
├── instances/          P
├── worlds              P
├── mods                P
├── assets/             R
├── libraries/          R
│
├── cache/              E → @root
└── logs/               E → @root
```

---

# 28. Format and validate Phase 2

Run:

```bash
cd /etc/nixos

nixfmt \
  home/p2949/ephemeral-app-state.nix

git diff --check
git diff
```

Then:

```bash
nix flake check
```

Then:

```bash
nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link
```

All must succeed.

---

# 29. Create explicit reboot sentinels

Before activating the cache split, create controlled proof files.

Define:

```bash
PRISM_ROOT="$HOME/.local/share/PrismLauncher"
```

Create a persistent proof:

```bash
touch "$PRISM_ROOT/.prism-persistence-proof"
```

Create disposable proofs:

```bash
mkdir -p \
  "$PRISM_ROOT/cache" \
  "$PRISM_ROOT/logs"

touch \
  "$PRISM_ROOT/cache/.prism-cache-ephemeral-proof" \
  "$PRISM_ROOT/logs/.prism-logs-ephemeral-proof"
```

Verify:

```bash
test -e "$PRISM_ROOT/.prism-persistence-proof"
test -e "$PRISM_ROOT/cache/.prism-cache-ephemeral-proof"
test -e "$PRISM_ROOT/logs/.prism-logs-ephemeral-proof"
```

All should currently exist.

---

# 30. Install the cache-split candidate boot-only

Again use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Keep the previous generation available.

Then reboot normally.

---

# 31. Verify the Impermanence contract after reboot

Immediately after login, before launching Prism:

```bash
PRISM_ROOT="$HOME/.local/share/PrismLauncher"
```

Persistent proof:

```bash
test -e "$PRISM_ROOT/.prism-persistence-proof" &&
  echo "PASS: Prism persistent root survived"
```

Disposable cache proof:

```bash
if [[ ! -e "$PRISM_ROOT/cache/.prism-cache-ephemeral-proof" ]]; then
    echo "PASS: Prism cache was reset"
else
    echo "FAIL: Prism cache survived"
fi
```

Disposable log proof:

```bash
if [[ ! -e "$PRISM_ROOT/logs/.prism-logs-ephemeral-proof" ]]; then
    echo "PASS: Prism logs were reset"
else
    echo "FAIL: Prism logs survived"
fi
```

The required result is:

```text
persistent parent marker       survives
cache marker                   disappears
logs marker                    disappears
```

---

# 32. Verify mount topology

Run:

```bash
findmnt -T "$PRISM_ROOT"
findmnt -T "$PRISM_ROOT/cache"
findmnt -T "$PRISM_ROOT/logs"
```

The important semantic result should be:

```text
Prism root
    persistent backing

cache
    root-local/reset storage

logs
    root-local/reset storage
```

This directly proves that the mixed-container implementation works.

---

# 33. Verify real Prism state after reboot

Now launch:

```bash
prismlauncher
```

Verify:

```text
[ ] Microsoft account remains present
[ ] authentication still works
[ ] instance remains present
[ ] instance settings remain present
[ ] Minecraft files remain available
[ ] test world remains present
```

Then start Minecraft again.

Verify:

```text
[ ] no full assets redownload
[ ] no full libraries redownload
[ ] correct Java selected
[ ] Minecraft launches
[ ] world opens
[ ] audio works
[ ] graphics work
```

Prism should simply regenerate its cache/log directories as required.

---

# 34. Validate the intended performance-mod workflow

Only after the basic vanilla setup is accepted should you start building the actual performance-oriented instance.

This keeps launcher validation independent from mod compatibility.

The progression should be:

```text
Prism package
        ✓

vanilla Minecraft
        ✓

persistent launcher state
        ✓

ephemeral cache split
        ✓

then:
performance instance
```

Your later performance instance can contain things such as:

```text
Sodium-family optimizations
Lithium
FerriteCore
ImmediatelyFast
C2ME where appropriate
Voxy
Distant Horizons
other non-content performance mods
```

but those are **not part of the NixOS Prism installation acceptance gate**.

---

# 35. Consider GameMode only after vanilla works

The Nixpkgs Prism wrapper already includes GameMode runtime support, and your NixOS configuration has `programs.gamemode.enable = true`.  

Once the normal instance works, you can test Minecraft with GameMode.

Verify separately rather than making GameMode necessary for basic operation.

During game launch:

```bash
gamemoded -s
```

or:

```bash
gamemoded -t
```

as appropriate for the installed version.

The desired distinction is:

```text
Minecraft works normally
+
GameMode can enhance a session

not:

Minecraft only works because of GameMode
```

---

# 36. MangoHud is optional validation, not a Prism dependency

MangoHud is already installed by the system gaming module. 

Use it later if useful for confirming:

```text
GPU
FPS
frame timing
CPU
VRAM
```

but do not change the Prism package just to integrate MangoHud during initial setup.

---

# 37. Do not use Gamescope by default initially

Gamescope is also already installed. 

For vanilla Minecraft launcher validation:

```text
Hyprland
→ Minecraft
```

is simpler than:

```text
Hyprland
→ Gamescope
→ Minecraft
```

Once Prism/Minecraft works directly, Gamescope can be tested separately if it provides a specific benefit.

---

# 38. Revisit `meta` after real use

After several launches:

```bash
du -sh "$PRISM_ROOT/meta"
find "$PRISM_ROOT/meta" -maxdepth 2 -type f | head -100
```

Do not print sensitive contents.

If observation confirms that it contains only cached component metadata and Prism cleanly rebuilds it, change:

```nix
children = [
  "cache"
  "logs"
];
```

to:

```nix
children = [
  "cache"
  "logs"
  "meta"
];
```

Then repeat:

```text
format
→ flake check
→ build
→ sentinel
→ boot
→ verify
```

Do not bundle this into the first cache split without evidence.

---

# 39. Revisit `java` separately

If:

```text
~/.local/share/PrismLauncher/java
```

does not exist or stays empty because the Nix wrapper supplies Java, no action is required.

If Prism creates launcher-managed Java installations, decide whether you actually want them.

Preferred policy for this NixOS machine:

```text
Nix-provided JDKs
    preferred

Prism-managed Java
    only when specifically required
```

If the directory contains only replaceable launcher-managed JDKs, it can later become class `R` or `E` depending on whether avoiding downloads matters.

Do not make that decision before observing actual behavior.

---

# 40. Clean up proof state

After acceptance:

```bash
rm -f \
  "$PRISM_ROOT/.prism-persistence-proof" \
  "$PRISM_ROOT/cache/.prism-cache-ephemeral-proof" \
  "$PRISM_ROOT/logs/.prism-logs-ephemeral-proof"
```

The latter two may already be absent.

If a pre-persistence backup was created and the live installation has survived reboot successfully, compare one final time and then remove the temporary backup.

Do not leave authentication copies scattered around the filesystem.

---

# 41. Review final source diff

At the expected final state, the source changes should normally be limited to:

```text
home/p2949/desktop/default.nix
home/p2949/persistence.nix
home/p2949/ephemeral-app-state.nix
docs/ephemeral-state-audit.md
```

Possibly documentation/status files if your project workflow requires them.

There should be no:

```text
Prism configuration in Git
Microsoft credentials in Git
Minecraft worlds in Git
Java binaries in Git
downloaded mods in Git
assets/libraries in Git
```

Those belong in persistent runtime state, not Nix source.

---

# 42. Final validation suite

Run:

```bash
cd /etc/nixos

git diff --check
nix flake check

nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link
```

If your current branch's normal validation registry remains applicable, also run the relevant workstation checks.

Then:

```bash
git status --short
```

Inspect every changed file deliberately.

---

# 43. Commit structure

I recommend two commits rather than one.

## Commit 1 — package + durable application state

Files:

```text
home/p2949/desktop/default.nix
home/p2949/persistence.nix
docs/ephemeral-state-audit.md
```

Suggested commit:

```bash
git add \
  home/p2949/desktop/default.nix \
  home/p2949/persistence.nix \
  docs/ephemeral-state-audit.md

git commit -m "Add Prism Launcher with persistent Minecraft state"
```

This commit should correspond to the state where:

```text
Prism launches
Java works
Minecraft launches
account survives
instances survive
whole Prism root is persistent
```

## Commit 2 — granular disposable state

Files:

```text
home/p2949/ephemeral-app-state.nix
docs/ephemeral-state-audit.md
```

Suggested commit:

```bash
git add \
  home/p2949/ephemeral-app-state.nix \
  docs/ephemeral-state-audit.md

git commit -m "Reset disposable Prism Launcher state"
```

This commit should correspond to the proven:

```text
persistent parent
+
ephemeral cache
+
ephemeral logs
```

behavior.

If `meta` is later proven disposable, make that a separate evidence-backed change rather than rewriting history.

---

# 44. Final acceptance criteria

The integration is complete only when all of these are true.

## Declarative package

```text
[ ] Prism installed through Home Manager
[ ] stock wrapped Nixpkgs prismlauncher used
[ ] no Flatpak/AppImage installation
[ ] no separate Java system configuration required
```

## Runtime

```text
[ ] Prism starts
[ ] Wayland UI works
[ ] Java detection works
[ ] Microsoft login works
[ ] vanilla Minecraft starts
[ ] RX 9070 XT rendering works
[ ] PipeWire audio works
```

## Persistence

```text
[ ] ~/.local/share/PrismLauncher is persistence-backed
[ ] account survives normal reboot
[ ] launcher configuration survives
[ ] instances survive
[ ] worlds survive
[ ] mods survive
[ ] assets/libraries survive
```

## Ephemeral policy

```text
[ ] cache proof disappears after normal reboot
[ ] logs proof disappears after normal reboot
[ ] persistent parent proof survives
[ ] Prism recreates disposable directories normally
```

## Repository

```text
[ ] ephemeral-state audit updated
[ ] no credentials committed
[ ] no runtime Minecraft data committed
[ ] nix flake check passes
[ ] final desktop build succeeds
[ ] exact source diff reviewed
```

---

# 45. Rollback procedure

If Prism itself fails but the system is otherwise healthy, simply remove the package declaration or debug Prism. There is no reason to modify the system gaming infrastructure.

If the new persistence mount causes trouble:

1. Boot the previous known-good NixOS generation.
2. Do not delete the Prism data.
3. Remove or correct the `.local/share/PrismLauncher` persistence declaration.
4. Rebuild.
5. Recover the data from the temporary private backup if necessary.

If the cache split causes trouble:

1. Boot the previous generation.
2. Remove the Prism entry from `ephemeral-app-state.nix`.
3. Leave the entire Prism root persistent.
4. Rebuild.
5. Investigate the child independently.

This means the safe fallback is always:

```text
whole Prism root persistent
```

That may preserve a little more cache than necessary, but it cannot destroy the actual Minecraft state merely for the sake of cache cleanliness.

---

# 46. Security rules

Treat:

```text
~/.local/share/PrismLauncher/accounts.json
```

as private authentication state.

Never:

```text
cat it into chat
commit it
paste it into plan.md
include it in CI artifacts
include it in debugging logs
copy it into a world-readable location
```

The persistence root should remain user-private.

When auditing Prism:

```text
inspect names
inspect paths
inspect sizes
inspect timestamps
inspect hashes when useful
```

but not authentication contents.

---

# 47. Desired finished architecture

The final result should look approximately like:

```text
NixOS source
│
├── modules/gaming/default.nix
│   ├── Steam
│   ├── GameMode
│   ├── Gamescope
│   └── MangoHud
│
├── home/p2949/desktop/default.nix
│   └── prismlauncher
│
├── home/p2949/persistence.nix
│   └── .local/share/PrismLauncher
│       └── mode 0700
│
├── home/p2949/ephemeral-app-state.nix
│   └── PrismLauncher
│       ├── cache
│       └── logs
│
└── docs/ephemeral-state-audit.md
    └── explicit Prism M/P/R/E classification
```

Runtime:

```text
/home/p2949
    ephemeral
        │
        └── .local/share/PrismLauncher
                bind/persistence-backed
                │
                ├── accounts/settings          persistent P
                ├── instances/worlds/mods      persistent P
                ├── icons/themes               persistent P
                ├── assets/libraries           retained R
                │
                ├── cache                      ephemeral E
                └── logs                       ephemeral E
```

Potential later refinement:

```text
meta
    → classify after evidence

java
    → likely unnecessary with Nix-provided JDKs
    → classify after evidence
```

---

# 48. Recommended exact execution order

```text
FINISH CURRENT GRANULAR-IMPERMANENCE PROJECT
        ↓
freeze accepted persistence policy
        ↓
create feat/prism-launcher
        ↓
capture clean pre-change baseline
        ↓
check for existing Prism state
        ↓
add pkgs.prismlauncher to Home Manager
        ↓
persist complete .local/share/PrismLauncher
        ↓
classify Prism as mixed in state audit
        ↓
nixfmt
        ↓
nix flake check
        ↓
build desktop closure
        ↓
install candidate boot-only
        ↓
normal reboot
        ↓
verify persistence mount
        ↓
launch Prism
        ↓
verify Nix-provided Java runtimes
        ↓
authenticate Microsoft account
        ↓
create vanilla instance
        ↓
launch Minecraft
        ↓
create/load test world
        ↓
close cleanly
        ↓
audit real Prism filesystem
        ↓
classify observed state
        ↓
add cache + logs to ephemeral-app-state.nix
        ↓
update audit
        ↓
nix flake check
        ↓
build candidate
        ↓
create persistent/cache/log sentinels
        ↓
install boot-only
        ↓
normal reboot
        ↓
persistent sentinel survives
cache sentinel disappears
logs sentinel disappears
        ↓
verify Microsoft account survives
        ↓
verify instance/world survives
        ↓
launch Minecraft again
        ↓
remove proof files
        ↓
commit package/persistence work
        ↓
commit cache-policy work
        ↓
final exact-source validation
        ↓
merge
```

---

# 49. Definition of done

Prism Launcher is considered properly integrated when you can reboot the machine into a freshly reset normal root and immediately do:

```bash
prismlauncher
```

then find:

```text
your Microsoft account still authenticated
your launcher configuration intact
your Minecraft instances intact
your worlds intact
your mods intact
your expensive assets/libraries intact
Java supplied by Nix
Mesa/RADV using the RX 9070 XT
PipeWire audio working
GameMode available
```

while:

```text
old Prism download cache
old Prism logs
```

have disappeared with the previous root and are cleanly regenerated as necessary.

That is the Prism installation that best fits the design of this workstation: **software declarative, valuable state explicit, expensive data deliberately retained, and disposable state automatically destroyed.**

The key sequencing choice is worth keeping: **first prove Prism with its whole application root persistent, then split cache/log state only after observing the real filesystem it creates.** That matches the evidence-first approach your Impermanence work already uses, rather than making assumptions about application state.
