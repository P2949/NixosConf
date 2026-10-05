# NixOS Pre-Experiment Readiness Master Plan

**Project:** `P2949/NixosConf`  
**Purpose:** take the current NixOS workstation from its present state to a **final, stable, reproducible, optimization-ready baseline** before any system-wide `-march=native`, LTO, PGO, BOLT, or combined binary-optimization work begins.  
**Plan date:** 2026-10-05  
**Scope boundary:** this document ends at the point where the final pre-experiment baseline is frozen and a fresh experiment branch can be created. It intentionally does **not** specify how to implement the later compiler/binary-optimization experiment.

---

## 0. How to use this document

This is deliberately both an **instruction plan** and a **progress log**.

Use these task states consistently:

- `[x]` — **DONE / PROVEN**: implemented and validated.
- `[~]` — **IN PROGRESS**: implementation exists locally or work has started, but the completion gate is not satisfied.
- `[ ]` — **TODO**: required before the final pre-experiment baseline.
- `[-]` — **DEFERRED / REJECTED FOR BASELINE**: consciously excluded from the stock baseline, with a reason recorded.
- `[?]` — **DECISION REQUIRED**: measure or resolve an ambiguity before choosing.

For every non-trivial task, fill in the tracker block:

```text
Status:
Owner:
Started:
Completed:
Commit / PR:
NixOS generation:
System closure:
Evidence / command output:
Decision:
Problems found:
Rollback path:
Notes:
```

Do not mark a task complete merely because the Nix expression evaluates. A task is complete only when its **validation gate** has passed.

### Source-of-truth rule

When old handoffs, chat notes, and current code disagree, use this order:

1. current local shell/repository state;
2. live `feat/impermanence`;
3. passing VM/integration-test evidence;
4. the complete 2026-10-05 project handoff;
5. older Impermanence handoff and architecture reviews;
6. historical migration/performance discussions.

Classify new notes as one of:

- **PROVEN**
- **CURRENT DESIGN**
- **PLANNED**
- **HYPOTHESIS**
- **HISTORICAL / SUPERSEDED**

This prevents an old recovery workaround from silently becoming present-day policy.

---

## Execution record — 2026-10-05

**Status: IN PROGRESS.** The complete 2,923-line plan was read, including
all phases and appendices. This master plan supersedes the previous narrow
VM milestone. Its explicit Phase 4 policy defers selective home and var
Impermanence for this baseline; root adoption remains required subject to
hardware gates. No compiler optimization work is authorized by this plan.

**Owner:** Codex for repository implementation and VM checks; operator for
physical boot selection, firmware settings, recovery-media boot, graphical
workload acceptance and backup destination confirmation.
**Started:** 2026-10-05. **Completed:** pending full GO checklist.
**Commit / PR:** pushed through `141c67745ac88fad0a17fa60eb479650087ee765`;
CI passed: https://github.com/P2949/NixosConf/actions/runs/37253111052.
No merge into main.
**NixOS generation:** current system profile points to system-32-link.
**Running closure:** `/nix/store/hqi49xrp7sqwz0785zwcxhfc30gzd25a-nixos-system-desktop-26.05.20261002.774debe`.
**Booted closure:** `/nix/store/4m45fvazn6d65jmz9fgnmplyv4axvsq5-nixos-system-desktop-26.05.20261002.774debe`.
They differ: running activation is not proof the current profile was boot-tested.
Verify the actual installed menu and retain this booted known-good path during
privileged preflight; no assumption is made that system-32 was booted.
**Evidence:** `git status`, branch, HEAD, 12-entry log, worktree and cached
diffs inspected; `flake.lock` tracked; `systemctl --failed` reports zero.
Current VM derivations and full logs are documented in
`docs/impermanence.md`; safety, recovery, A and B passed. B now explicitly
proves cross-boot journal retention as well as stable identity.
**Decision:** preserve phase dependency order, retain forensic roots and normal
persistent-root boot configuration, never switch live into first-use reset.
**Problems found:** previous docs proposed home migration next, conflicting
with this master plan; docs will follow the master's explicit deferral.
Noninteractive sudo currently fails with “a password is required”; no privileged
host modifications have been performed. Physical validation, external backup,
recovery-media drill, firmware/OC validation and multi-day soak are unproven.
**Rollback path:** current persistent-root closure retained; no host activation.
**Next gate:** operator confirmation of independent backup
and bootable recovery media, privileged preflight and manually selected physical
boots. All phases after hardware adoption remain open; final tag is forbidden
until their evidence exists.

**Current checkpoint (PROVEN, 2026-10-05):** local and remote
`feat/impermanence` HEAD both `141c67745ac88fad0a17fa60eb479650087ee765`.
Five separate commits: `3d5c858` safety/recovery, `acc9fbd` identity/journal,
`34bc8af` recovery ISO, `4ff60a2` feature-branch CI, `141c677` physical preparation.
Current worktree contains only the pre-existing user `.gitignore` change;
ignored `plan.md` is maintained locally. `nix flake check` passes on this final
source; current safety/recovery/A/B outputs are valid. Recovery ISO and physical
parent/child closures built successfully. Closure diff has configuration,
initrd and persistence-unit changes for the new child, with no kernel/Mesa
version movement or input update. Physical running closure remains unchanged.
Phase 0's file list below is the initial reconciliation snapshot, not current
uncommitted state.

---

# 1. Hard scope boundary

## This plan includes

- finishing and validating the NixOS operating model;
- Impermanence / ephemeral-root completion;
- persistence-state classification;
- repository and branch cleanup;
- configuration ownership cleanup;
- NixOS-native safety features;
- VM and integration-test coverage;
- recovery/rollback tooling;
- Nix store and generation lifecycle management;
- hardware/firmware stabilization;
- stable, low-risk, non-binary performance tuning;
- storage, CPU, graphics, gaming, and workstation baseline decisions;
- removal of cargo-cult performance tweaks;
- observability and reproducibility tooling;
- compatibility acceptance tests for the machine's real workloads;
- final soak testing;
- final baseline manifest, tag, and closure freeze.

## This plan explicitly does **not** include

- implementing global `-march=native`;
- implementing global or package LTO;
- PGO instrumentation/profile collection/profile reuse;
- BOLT instrumentation/profile collection/rewrite;
- deciding which packages should receive those stages;
- benchmark design for comparing compiler/binary-optimization stages;
- the later experiment runner implementation.

Those belong on the experiment branch **after this plan is complete**.

---

# 2. Current known state

## 2.1 Repository state on GitHub

| Branch / milestone | Current state | Meaning |
|---|---|---|
| `main` | `072127528e12bbb482c907cebb6406c9301830e6` | architecture refactor merged |
| `nixos-26.05-architecture-baseline` | points at architecture baseline | broad architecture considered complete |
| `nixos-26.05-productive-baseline` | `84ec735...` | earlier known-good productive workstation |
| `feat/impermanence` | `c583a7d01cf30cef8a6031345c05ce93b764aa22` | safety/recovery/identity VMs, recovery ISO and opt-in physical target prepared |
| `feat/optimization-framework` | `397a8c71cd7acb0bc016983f28866df16c95d7d8` | parked prototype/recovery lineage; **do not merge wholesale** |

Remote `feat/impermanence` HEAD was verified after pushing five new checkpoints.
The Impermanence work remains isolated from the parked optimization branch;
`main` has not been merged or changed by this execution.

## 2.2 Architecture already considered correct

The repository's governing rule is:

> **Hosts contain facts, modules contain features, profiles compose features, Home Manager contains user policy, packages build software, and optimization contains experiments.**

Current broad boundaries are good:

- `hosts/desktop/` — physical-host facts and host policy;
- `profiles/workstation.nix` — workstation role composition;
- `modules/` — reusable NixOS features;
- `home/p2949/` — user/session/development policy;
- `packages/` — software construction;
- `optimization/` — reserved for experiment code;
- `tests/` — explicit heavier correctness tests.

**Do not restart a large-scale modularization project.** Small files such as `nix-ld.nix`, `notifications.nix`, or `blender.nix` are fine when they express a real semantic boundary.

## 2.3 Current physical storage design

Current declared Btrfs layout:

```text
MP600
├── ESP              4 GiB       -> /boot
├── swap             32 GiB
└── Btrfs
    ├── @root                      -> /
    ├── @home                      -> /home
    ├── @nix                       -> /nix
    ├── @persist                   -> /persist
    ├── @var                       -> /var
    ├── @optimization              -> /var/lib/nixos-optimization
    └── @snapshots                 -> /.snapshots
```

Current common Btrfs options:

```text
compress=zstd:1
noatime
discard=async
```

These are already a strong baseline and should not be replaced with speculative filesystem tuning.

## 2.4 Current productive host features already in place

- stable NixOS 26.05 nixpkgs as the main package set;
- explicitly separated `pkgsUnstable`;
- Home Manager on the same stable package set;
- Intel microcode enabled;
- redistributable firmware enabled;
- Btrfs monthly scrub;
- 20 systemd-boot entries;
- `auto-optimise-store = true`;
- Steam;
- GameMode;
- Gamescope;
- MangoHud;
- 32-bit graphics support;
- PipeWire;
- Hyprland/UWSM;
- `nix-ld`;
- explicit high `nofile` limits for development workloads;
- pinned Commander Core support with systemd supervision/watchdog;
- declarative password source under `/persist/secrets`;
- `/etc/nixos` persistence;
- NetworkManager connection persistence.

## 2.5 Current Impermanence evidence

Already proven:

- a reusable ephemeral-Btrfs-root module exists;
- recursive parent deletion has been removed;
- allowed-descendant validation exists;
- persistent initrd diagnostics exist;
- reset refuses to run after `/sysroot` has been mounted;
- duplicate destructive oneshot execution was fixed with `RemainAfterExit=true`;
- a real Btrfs + systemd-initrd + Impermanence + Home Manager Test A passes across three boots;
- the test shows one reset per unique boot;
- `/tmp` is reconstructed correctly;
- authentication and persistent sentinels work;
- the physical host still does **not** enable root reset.

Completed since the consolidated handoff: safety/recovery matrix (26 refusal
cases and three recovery boots), config assertions (39 rejections, three accepted
controls), and machine-ID Test B including cross-boot journal continuity.

Still unproven:

- controlled physical ephemeral-root boot;
- physical acceptance of the selected stable machine-ID persistence policy;
- final decision on whether ephemeral root becomes the normal default.

---

# 3. Non-negotiable engineering invariants

These are preconditions for every later phase.

## 3.1 Workstation safety

- [ ] A known-good bootable path must always exist.
- [ ] Destructive storage behavior must be VM/integration-tested before first physical use.
- [ ] First-time risky boot behavior must be installed with `boot`, not activated blindly with `switch`.
- [ ] A failed experimental boot must not require reinstalling NixOS to recover.
- [ ] Forensic evidence must not be deleted until the failure mode has been superseded by repeatable passing tests.

## 3.2 Reproducibility

- [ ] All configuration changes are committed before they become the final baseline.
- [ ] `flake.lock` is committed.
- [ ] No automatic flake/input update mechanism is allowed during the later optimization campaign.
- [ ] The final baseline has an annotated Git tag.
- [ ] The final system closure is recorded.
- [ ] The final kernel, Mesa, microcode, firmware/BIOS, CPU policy, filesystem options, and active system services are recorded.

## 3.3 State hygiene

- [ ] Every mutable state item required across an ephemeral-root reboot is intentionally classified.
- [ ] Password hashes and secret material remain outside Git.
- [ ] `/var` and `/home` persistence are deliberate, not accidental.
- [ ] `/etc/machine-id` behavior is explicitly decided and tested.
- [ ] No unknown mutable `/etc` state is required for ordinary workstation function.

## 3.4 Performance-baseline integrity

- [ ] No global compiler optimization flags are present.
- [ ] No global `NIX_CFLAGS_COMPILE`, `CFLAGS`, `CXXFLAGS`, `LDFLAGS`, `RUSTFLAGS`, or similar performance flags are present.
- [ ] No global `LD_LIBRARY_PATH` compatibility hack exists.
- [ ] No unsupported kernel/VM/sysctl folklore tuning is present.
- [ ] Security mitigations remain enabled in the stock baseline.
- [ ] VM results are treated as correctness evidence only, never performance evidence.

---

# 4. Master dependency order

Do the work in this order:

```text
CURRENT STATE
    │
    ▼
1. Finish Impermanence VM safety/recovery matrix
    │
    ▼
2. Resolve machine-id
    │
    ▼
3. Controlled physical ephemeral-root validation
    │
    ▼
4. Freeze persistence policy
    │
    ▼
5. Merge Impermanence into main
    │
    ▼
6. Targeted configuration/repository cleanup
    │
    ▼
7. Recovery, VM, CI, specialisation and rollback tooling
    │
    ▼
8. Nix/Btrfs lifecycle and maintenance policy
    │
    ▼
9. Firmware/BIOS/hardware baseline freeze
    │
    ▼
10. Stable bang-for-buck performance policy
    │
    ▼
11. Workload acceptance and hardware stability
    │
    ▼
12. Observability + baseline manifest
    │
    ▼
13. Multi-day soak / reboot validation
    │
    ▼
14. Final pre-optimization tag + immutable control point
    │
    ▼
STOP: optimization experiment may now begin on a fresh branch
```

Do **not** combine unrelated phases into one giant commit.

---

# 5. Phase 0 — Reconcile local state with the pushed checkpoint

**Goal:** know exactly what exists locally before continuing from the handoff.

## 5.1 Record local repository state

- [x] Run:

```bash
cd /etc/nixos

git status --short
git branch --show-current
git rev-parse HEAD
git log --oneline --decorate -12
git diff
git diff --cached
```

### Expected interpretation

The latest pushed `feat/impermanence` checkpoint is:

```text
6426bf17e78b08b6e3c62d55632247b002acdb3a
Add fail-safe ephemeral Btrfs root reset and VM coverage
```

The handoff says an additional safety test existed locally/staged after this commit. The pushed GitHub tree does **not** contain `tests/impermanence-root-safety.nix`.

### Completion gate

- [x] Local-only work is identified.
- [x] No local edit is mistaken for an upstream/pushed fact.
- [x] A note is added here stating the exact local HEAD and uncommitted files.

### Progress record

```text
Status: DONE / PROVEN (local reconciliation, 2026-10-05)
Local branch: feat/impermanence
Local HEAD: 6426bf17e78b08b6e3c62d55632247b002acdb3a
Uncommitted files: .gitignore (user edit, retained and unstaged);
  tests/impermanence-root-a.nix (journal continuity test added this turn).
Staged files: README.md, docs/impermanence.md, flake.nix,
  modules/storage/ephemeral-btrfs-root.nix, tests/impermanence-root-a.nix,
  tests/impermanence-root-b.nix, tests/impermanence-root-config.nix,
  tests/impermanence-root-recovery.nix, tests/impermanence-root-safety.nix.
Notes: Read full git diff and cached diff; initial cached patch saved at
  /tmp/impermanence-plan-start.patch. plan.md is ignored by the user's
  .gitignore policy and is maintained locally. No claim these edits are pushed.
```

---

# 6. Phase 1 — Complete Impermanence safety before touching the physical root

VM implementation and the original full safety/recovery suite are proven.
Publication and current-source regression confirmation are in progress.

## 6.1 Fix the locally staged safety-test lint blocker

Only perform this if the local tree still matches the complete handoff.

- [x] Remove the unused `inputs` parameter from:

```text
tests/impermanence-root-safety.nix
```

- [x] Change the flake import from:

```text
inherit inputs pkgs;
```

to:

```text
inherit pkgs;
```

- [x] Format and validate:

```bash
cd /etc/nixos

nix fmt

git add \
  flake.nix \
  tests/impermanence-root-safety.nix

git diff --check
git diff --cached --check
git diff --cached --stat

nix flake check --print-build-logs &&
nix build \
  '.#impermanence-root-safety' \
  -L
```

**Do not modify the production reset algorithm merely because the safety test itself fails. First determine whether the test exposed a genuine implementation defect or a test-harness defect.**

## 6.2 Prove unknown-child fail-closed behavior

- [x] Construct an unexpected descendant beneath `@root`.
- [x] Prove the reset refuses destructive deletion.
- [x] Prove the persistent diagnostic log identifies the rejected topology.
- [x] Prove the parent is not recursively deleted.
- [x] Prove the test fails if the service continues despite the unexpected child.

### Completion gate

```text
unexpected descendant
        ↓
topology validation
        ↓
FAIL CLOSED
        ↓
no parent recursive deletion
        ↓
persistent evidence
```

## 6.3 Prove malformed staging fail-closed behavior

- [x] Add a malformed / non-empty / structurally invalid `@root-next`.
- [x] Prove the reset refuses to assume it is disposable.
- [x] Prove no unknown descendant is recursively deleted.
- [x] Preserve diagnostic output.

## 6.4 Prove missing-root recovery

- [x] Simulate a missing `@root` with a valid clean staging root.
- [x] Prove the implementation can recover to a valid bootable `@root`.
- [x] Prove the recovery operation is unambiguous and logged.

## 6.5 Prove stale-clean-staging recovery

- [x] Simulate the interrupted-transition case represented by a clean stale staging root.
- [x] Prove the expected recovery transition.
- [x] Reboot through the real systemd initrd path.

## 6.6 Re-run positive Test A

After the abnormal-state cases are green:

```bash
nix build \
  '.#impermanence-root-test-a' \
  -L
```

- [x] Three complete boots still pass.
- [x] Three unique boot IDs are observed.
- [x] Exactly one reset occurs per boot.
- [x] `/tmp` is usable and mode `1777`.
- [x] persistent sentinels survive.
- [x] disposable root sentinels disappear.
- [x] NetworkManager works.
- [x] D-Bus/logind work.
- [x] Home Manager activation works.
- [x] authentication works.
- [x] persistent reset diagnostics are correct.

## 6.7 Commit and push the safety/recovery matrix

- [x] Commit separately from machine-id work.
- [x] Push `feat/impermanence` (remote HEAD verified: 141c67745ac88fad0a17fa60eb479650087ee765).
- [x] Confirm GitHub CI passes (run 37253111052, head 141c677, success).

Suggested commit theme:

```text
Test ephemeral root failure and recovery states
```

### Phase 1 progress record

```text
Status: DONE / PROVEN (VM safety/recovery, separate commit, push and CI)
Owner: Codex
Started: 2026-10-05
Completed: 2026-10-05 (GitHub CI run 37253111052 succeeded)
Commit / PR: 3d5c858 (safety/recovery only), pushed
NixOS generation: unchanged system-32-link
System closure: physical running closure unchanged
Evidence / command output: original final safety/recovery/A results in
  docs/impermanence.md; current root script unchanged; isolated staged commit
  exported to /tmp/nixos-safety-stage and its full flake check passed.
Decision: strict empty staging, reject unknown descendants before mutation,
  non-recursive deletion, preserve 0600 diagnostic log.
Problems found: ordinary staging contents, validation ordering, hidden
  grandchildren, and misleading path delimiter parsing fixed with coverage.
Rollback path: no physical activation; retain parent persistent-root entry.
Notes: index-only staging separated identity work from this commit; no user
  .gitignore changes committed. Current regressions passed: safety unchanged/cached, A and recovery each
  rebuilt and passed three complete boots; B rebuilt with journal continuity.
```

### Phase 1 completion gate

The destructive mechanism has both:

```text
positive-path coverage
+
abnormal-state fail-closed/recovery coverage
```

on the real Btrfs + initrd failure boundary.

---

# 7. Phase 2 — Resolve `/etc/machine-id` deliberately

Stable machine identity is desirable, but it must not be forced into the production configuration until the previous collision is understood.

## 7.1 Test B

- [x] Clone Test A semantics.
- [x] Add `/etc/machine-id` persistence.
- [x] Boot repeatedly through the real root-reset path.
- [x] Verify Impermanence does not collide with a file already created during activation.
- [x] Verify journal continuity.
- [x] Verify D-Bus/logind behavior.
- [x] Verify the machine ID remains constant between boots.

Record:

```text
Boot 1 machine-id: 2b2a6d0c871e44d6950f0f929324752e (VM only)
Boot 2 machine-id: 2b2a6d0c871e44d6950f0f929324752e (VM only)
Boot 3 machine-id: 2b2a6d0c871e44d6950f0f929324752e (VM only)
Persistence helper result: absent backing initialized, cmp passed each boot
Journal directory result: /var/log/journal/<same-id> exists each boot;
  journal markers persistent-boot-1, -2, -3 all queryable after boot three
Failure, if any: none; B test script finished successfully in 466.18s
```

### Phase 2 progress record

```text
Status: DONE / PROVEN for VM behavior and selected boot policy;
  physical implementation prepared, hardware validation pending Phase 3
Owner: Codex
Started: 2026-10-05
Completed: VM gate 2026-10-05
Commit / PR: acc9fbd, separate identity/journal commit
NixOS generation: unchanged
System closure: no host activation
Evidence / command output: nix build .#impermanence-root-test-b succeeded;
  /nix/store/fw3pvfy28wh5rnqc8hp7m67ijw0c2rk7-vm-test-run-impermanence-root-b.drv
  full log retrieved with nix log; all marker and identity assertions passed.
Decision: stable persisted ID in ephemeral-root child, seed current physical
  ID only during gated privileged preflight; no live activation.
Problems found: earlier B had no explicit journal-continuity check; fixed.
Rollback path: parent remains persistent-root, no ID persistence in parent.
Notes: historical generation-30 cause remains a hypothesis, not a proven
  diagnosis. B demonstrates safe fresh-root boot ordering for pinned inputs.
```

## 7.2 Choose one explicit final policy

### Preferred outcome

- [x] **Persist a stable machine ID** once Test B proves the ordering is safe.
  Selected for the opt-in physical target, hardware acceptance still pending.

This avoids changing host identity on every ephemeral-root boot and gives cleaner persistent-journal identity.

### Fallback outcome

If Test B establishes a real incompatibility that is not worth redesigning before the optimization project:

- [ ] deliberately keep machine-id transient;
- [ ] document the behavior and its implications;
- [ ] verify all required services tolerate it;
- [ ] record this as a conscious baseline exception.

Do not let machine identity remain an accidental side effect.

---

# 8. Phase 3 — Controlled physical-host ephemeral-root adoption

Only start this after the complete VM suite is green.

## 8.1 Preserve the current persistent-root system

- [x] Confirm at least one known-good current generation is bootable (generation 31 is actually booted).
- [x] Confirm the bootloader menu shows old generations (privileged bootctl inspection).
- [x] Confirm recovery media exists or will exist before destructive boot testing (operator reports prior successful recovery with it).
- [x] Keep forensic subvolumes for now (all three verified; separate pretrial snapshots added).

Do not delete yet:

```text
@root-pre-ephemeral
@root-failed-ephemeral-1
@root-broken-runtime-20261004
```

## 8.2 Add the first physical root-reset target as an opt-in boot variant

The first physical test must **not** be activated live.

- [x] Make root-reset behavior an explicitly selectable boot target/specialisation.
- [x] Keep the normal persistent-root entry (generation 33 parent installed and loader.conf default).
- [x] Build and install it with `nixos-rebuild boot` or an equivalent boot-only flow (generation 33).
- [x] Do not use first-time root-reset behavior with `nixos-rebuild switch` (boot-only installation).

NixOS activation semantics to preserve:

```text
build         -> build only
dry-activate  -> show live activation changes
test          -> activate now, not boot default
boot          -> install as boot default/entry, do not live-activate
switch        -> activate now and install for boot
```

For the first destructive boot behavior, `boot` + manual bootloader choice is the correct safety model.

### Phase 3 preparation record

```text
Status: IN PROGRESS; NOT INSTALLED / NOT PHYSICALLY BOOTED
Owner: Codex (preparation), operator (privileged preflight and boots)
Started: 2026-10-05
Completed: pending hardware acceptance
Commit / PR: 141c677, physical preparation and documentation; pushed
NixOS generation: unchanged system-32-link
System closure: prepared parent /nix/store/njd6kmmklgjy6clp6p7jfsnmhhmcny1h-nixos-system-desktop-26.05.20261002.774debe
  child /nix/store/waa33ig2s91463478rnb1ynq8wclc390-nixos-system-desktop-26.05.20261002.774debe
Evidence / command output: toplevel build succeeded; evaluated parentReset=false,
  childReset=true, childSystemdInitrd=true, parentPersistedFiles=[], child only
  /etc/machine-id; /tmp/impermanence-physical-options.json.
Decision: manually selectable ephemeral-root child; parent stays persistent.
Problems found: sudo requires interactive password; bootloader entries protected;
  actual top-level topology, credentials, backups and recovery boot unverified.
Rollback path: retain old entries and all forensic roots. Boot entry fallback
  cannot restore discarded root-local data.
Notes: docs/physical-root-validation.md is the operator runbook. Independent
  backup and recovery-media status requested; no dependent destructive action.
```

## 8.3 First physical boot validation

After booting the opt-in target:

- [x] graphical login succeeds;
- [x] `/` is the intended new `@root`;
- [x] `/nix` persists;
- [x] `/var` persists;
- [x] `/home` persists;
- [x] `/persist` persists;
- [x] `/var/lib/nixos-optimization` persists;
- [x] `/tmp` is usable and mode `1777`;
- [x] `/srv` behaves normally;
- [~] password login: source hash matches; active authenticated login session observed; password-entry acceptance not independently tested;
- [x] machine ID follows the Phase 2 decision;
- [x] NetworkManager connections survive;
- [x] journal is usable;
- [x] D-Bus and logind are active;
- [x] Commander Core service is active;
- [x] no unexpected failed systemd units exist;
- [x] root-reset diagnostic log shows one clean transition.

Run:

```bash
systemctl --failed --no-pager
findmnt /
for target in /nix /var /home /persist /var/lib/nixos-optimization; do
  findmnt "$target"
done
stat -c '%a %n' /tmp
cat /etc/machine-id
journalctl -b -p warning..alert --no-pager
systemctl status commander-core.service --no-pager
```

## 8.4 Reboot-repeatability test

- [x] Repeat at least three complete physical boots.
- [x] Prove disposable root state disappears each time.
- [x] Prove required persistent state survives.
- [x] Prove no second reset invocation occurs.
- [x] Prove the machine remains a normal productive workstation.

## 8.5 Choose final boot model

### Recommended model after repeated success

Use NixOS specialisations to keep both concepts visible:

```text
normal productive system
    ├── normal/default root policy
    └── known-good recovery/persistent-root alternative
```

If ephemeral root becomes normal/default, preserve a bootable persistent-root/recovery path.

If the value of ephemeral root does not justify physical-host complexity after the successful test, it is valid to leave it as an opt-in specialisation. The optimization experiment does **not** require `/home` or `/var` to be ephemeral.

## 8.6 Delete forensic roots only after the milestone is genuinely superseded

- [ ] All VM safety tests green.
- [ ] Machine-id decision complete.
- [ ] At least one controlled physical ephemeral boot succeeds.
- [ ] Repeated physical boots succeed.
- [ ] Relevant forensic conclusions are written into documentation.

Only then consider deleting old forensic subvolumes/generations.

---

# 9. Phase 4 — Freeze the persistence contract

The root-reset implementation is not finished as a workstation feature until the surviving state is documented as a contract.

## 9.1 Keep the current broad persistence model

Recommended pre-experiment filesystem model:

```text
/                           ephemeral, if physical validation passes
/home                       persistent
/var                        persistent
/nix                        persistent
/persist                    persistent
/var/lib/nixos-optimization persistent
```

### Why

This gives a clean system root without making the primary workstation fragile or forcing every development application's mutable state into an Impermanence allow-list.

## 9.2 Do **not** make `/home` ephemeral before the optimization campaign

- [-] Selective home Impermanence is **deferred by default**.

Reason:

- large scope;
- many development applications;
- Steam/Proton state;
- Unreal state;
- browser state;
- desktop session state;
- no direct prerequisite for compiler/binary optimization;
- adds substantial risk of unrelated baseline changes.

If you eventually want selective home impermanence, treat it as a separate project milestone after the optimization campaign or consciously complete it before the final baseline and then re-run the full acceptance suite. Do not sneak it in halfway through experiments.

## 9.3 Do **not** make `/var` ephemeral before the optimization campaign

- [-] Selective `/var` Impermanence is **deferred by default**.

The current persistent `/var` gives stable:

- system journal;
- Bluetooth state;
- system service state;
- caches/databases that expect continuity;
- machine-related state.

Reducing `/var` later is possible, but it is not needed to make the performance experiment valid.

## 9.4 Audit mutable `/etc` state

Create a persistence inventory document, for example:

```text
docs/persistence-contract.md
```

At minimum classify:

| State | Final policy | Reason |
|---|---|---|
| `/etc/nixos` | persist | config working tree |
| `/etc/NetworkManager/system-connections` | persist | connection secrets/profiles |
| `/etc/machine-id` | decision from Test B | stable host identity |
| password hash | source from `/persist/secrets`, not Git | declarative login |
| SSH host keys | persist **if sshd becomes enabled** | stable host identity |
| manually edited `/etc/*` | eliminate or explicitly persist | no hidden mutable state |

Run after a normal productive period:

```bash
sudo find /etc \
  -xdev \
  -type f \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' \
  | sort
```

Do not blindly persist everything that changes. First ask whether it should be declarative instead.

## 9.5 Secrets contract

- [ ] `/persist/secrets` is root-owned and not Git-tracked.
- [ ] Secret paths are documented without secret contents.
- [ ] A separate encrypted/off-machine backup exists.
- [ ] No secret is copied into benchmark manifests or handoff documents.
- [ ] Restore procedure is tested.

**Impermanence is not a backup system.**

---

# 10. Phase 5 — Merge the stable operating model into `main`

## 10.1 Keep branch semantics clean

`feat/impermanence` is the correct place for root/persistence work.

`feat/optimization-framework` contains a useful prototype but also historical recovery/Impermanence material. It should remain a reference, not become the final history.

## 10.2 Merge only after the Impermanence milestone is green

Required before merge:

- [x] safety/recovery matrix green;
- [x] machine-id decision complete (stable identity; hardware acceptance pending);
- [x] full Impermanence VM suite green;
- [ ] physical controlled boot successful;
- [ ] repeated physical validation successful;
- [ ] production root policy decided;
- [ ] documentation updated;
- [x] CI green for feat/impermanence checkpoint 141c677.

Then:

- [ ] open/merge an Impermanence PR into `main`;
- [ ] verify `main` builds/evaluates after merge;
- [ ] do **not** merge `feat/optimization-framework` wholesale.

## 10.3 Preserve old optimization work as a prototype reference

- [ ] Keep `397a8c7` reachable through the existing branch or an archive tag.
- [ ] Later transplant/rewrite only optimization-specific ideas onto the final baseline.
- [ ] Do not carry old persistence/recovery commits into the new experiment history.

---

# 11. Phase 6 — Targeted repository cleanup

Do this only after the machine is once again intentionally boring and stable.

The broad architecture is already good. This phase is about removing the remaining ownership ambiguities, not producing more directories for their own sake.

## 11.1 Split `modules/core/packages.nix` by ownership

Current `core/packages.nix` mixes:

- recovery/admin tools;
- interactive CLI tools;
- compilers/debuggers;
- build systems;
- Python.

Target policy:

### System / recovery layer

Keep tools that make sense even from a broken user environment:

```text
git
curl
vim or another emergency editor
btrfs-progs
nvme-cli
pciutils
usbutils
lm_sensors
efibootmgr
file
```

The exact set can remain pragmatic.

### Home Manager CLI layer

Move normal interactive tools where reasonable:

```text
ripgrep
fd
jq
btop
htop
tree
gh
wget
nano
```

No need to be dogmatic; the goal is semantic ownership.

### Development layer / dev shell

Move toolchains that do not need to be globally ambient:

```text
gcc
clang
lld
gdb
cmake
ninja
gnumake
pkg-config
python
```

### Why

A cleaner ambient system makes it easier to know which toolchain a later build actually used. Project-specific toolchains should come from the project environment rather than whichever compiler happens to be globally first in `PATH`.

## 11.2 Keep `system.stateVersion` and Home Manager state version frozen

Current:

```text
system.stateVersion = "26.05"
home.stateVersion   = "26.05"
```

- [x] Keep both at their original installation value.
- [x] Do not bump them merely because nixpkgs later upgrades.

## 11.3 Clean custom-package dependency direction

Refactor:

```nix
{ inputs, pkgs }:
```

toward:

```nix
{ pkgs, src }:
```

for `packages/liquidctl-pr886.nix`.

The flake/module boundary should select the source; the package should build the source it is given.

## 11.4 Finish Commander Core invariants

Current module already has typed 0–100 fan/pump duties and `lowTemp <= highTemp`.

Add or deliberately evaluate:

- [~] `usbId` format validation;
- [~] non-empty serial validation;
- [~] `baseFanDuty <= highFanDuty`;
- [~] strictly positive polling/wake/reset intervals;
- [~] sensible temperature range validation;
- [~] `lowTemp < highTemp` if strict hysteresis is desired;
- [~] watchdog interval has enough margin relative to the keeper's wake/report interval;
- [~] error messages are actionable.

All eight implemented and checked in feat/workstation-validation; integration
and eventual hardware acceptance are pending. Strict hysteresis chosen;
0 <= lowTemp < highTemp <= 100, with the existing 35-second watchdog retained.

Do not rewrite the known-working control loop for style reasons.

## 11.5 Add Python checks for the hardware keeper

The cooling daemon is critical code.

Add fast checks to the normal CI path:

- [~] Python syntax compile check;
- [~] Ruff or equivalent static lint;
- [~] small unit tests for pure argument/state-transition logic where practical.

Implemented as ordinary checks on feat/workstation-validation; local checks
passed, branch CI/integration pending.

Do not make CI depend on the physical Commander Core.

## 11.6 Update README to current reality

The current README architecture is good but needs to remain synchronized with milestones.

After Impermanence merge, update it to include:

- `hosts/desktop/persistence.nix`;
- `modules/storage/ephemeral-btrfs-root.nix`;
- `tests/`;
- the actual finalized root policy;
- the actual current baseline tags;
- heavy-test invocation;
- recovery workflow;
- the fact that the optimization area is intentionally inert until the final pre-experiment tag.

## 11.7 Update repository description

Recommended description:

```text
Declarative NixOS workstation configuration and system optimization research framework
```

## 11.8 Do not over-refactor

- [-] no flake-parts merely for abstraction;
- [-] no custom host framework for one host;
- [-] no one-file-per-option pattern;
- [-] no re-merging meaningful small modules just to reduce file count.

---

# 12. Phase 7 — Improve CI and correctness coverage

## 12.1 Keep ordinary `nix flake check` fast

Current fast checks:

- formatting;
- Statix;
- Deadnix.

Implemented additions: desktop/recovery evaluation, ephemeral-root option
validation and baseline collector syntax/ShellCheck. Python checks remain open.

Keep the principle:

> heavy multi-boot storage tests are explicit, not ordinary PR-lint work.

## 12.2 Add a cheap desktop evaluation check

The current fast checks do not need to build the full desktop closure, but the repository should detect broken NixOS evaluation.

- [x] Add a flake check or CI step that forces evaluation of:

```text
nixosConfigurations.desktop.config.system.build.toplevel
```

without requiring a complete workstation build on every GitHub Actions run.

## 12.3 Add Python checks

- [ ] keeper syntax/lint;
- [ ] any reusable test helper Python;
- [ ] deterministic unit-level code paths.

## 12.4 Keep the heavy tests explicitly invokable

Document commands such as:

```bash
nix build '.#impermanence-root-test-a' -L
nix build '.#impermanence-root-safety' -L
```

Add future heavy correctness tests using the same explicit pattern.

## 12.5 Protect `main`

GitHub currently reports the branches as unprotected.

Before the optimization campaign:

- [x] require CI for PRs into `main`;
- [x] prevent accidental force-push to `main`;
- [x] prefer PR merge for baseline changes;
- [ ] keep release/baseline tags immutable by convention.

This is repository reliability, not bureaucracy: the OS configuration itself is a research artifact.

---

# 13. Phase 8 — Build a generic workstation correctness VM

The existing Impermanence Test A is specialized and valuable. Add a lighter generic “does the workstation composition still boot?” path.

## 13.1 Add a VM variant

Reuse the real profile/modules while explicitly disabling host-only assumptions:

- Commander Core physical service;
- physical Disko device identity;
- GPU-specific expectations that QEMU cannot satisfy;
- destructive root-reset behavior unless that specific test is being run.

Possible approaches:

- `virtualisation.vmVariant`;
- a separate `nixosConfigurations.desktop-vm`;
- a small test configuration that imports the same workstation profile.

Choose the least abstract option that evaluates cleanly.

## 13.2 Generic VM smoke test

Validate:

- [x] VM boots;
- [x] `multi-user.target` reaches active;
- [x] D-Bus works;
- [x] logind works;
- [x] NetworkManager works or is consciously replaced by VM network configuration;
- [x] user exists;
- [x] Home Manager evaluates/activates in the intended test model;
- [x] no unexpected failed units.

Proven on feat/workstation-validation's explicit workstation-smoke package;
the VM uses harness storage/networking and does not prove physical acceptance.

**Do not benchmark this VM.**

## 13.3 Add a small NixOS integration smoke test

Keep a distinction:

```text
integration VM
    -> correctness

physical machine
    -> performance
```

---

# 14. Phase 9 — NixOS specialisations as a safety feature

Specialisations are exceptionally well matched to this project, but use them first for **safety**, not for compiler optimization.

## 14.1 Establish a non-optimization specialisation

Examples:

```text
persistent-root / recovery
ephemeral-root
```

The exact direction depends on which root policy becomes default.

- [ ] both entries appear in systemd-boot;
- [ ] both can be selected manually;
- [ ] the recovery variant does not perform destructive reset work;
- [ ] kernel-affecting variants are always tested by reboot, not assumed to switch live.

## 14.2 Document the distinction

```text
generation
    = historical version of the machine

specialisation
    = intentional variant inside a configuration
```

This distinction will be important later, but no optimization specialisations need to be implemented in this pre-experiment plan.

---

# 15. Phase 10 — Declarative recovery / rescue path

A main workstation that will later build experimental whole-system closures should have an independent recovery path.

## 15.1 Build a recovery ISO or recovery configuration

Create a reproducible rescue artifact from the same pinned Nixpkgs release.

Recommended recovery tools:

```text
btrfs-progs
nvme-cli
util-linux
git
curl
vim
pciutils
usbutils
lm_sensors
efibootmgr
cryptsetup only if later needed
networking tools
```

Do not embed workstation secrets.

### Recovery artifact preparation record

```text
Status: IN PROGRESS (ISO BUILT; media boot and recovery drill pending)
Owner: Codex (artifact), operator (physical drill)
Started: 2026-10-05
Completed: pending physical recovery drill
Commit / PR: 34bc8af, standalone recovery artifact commit
NixOS generation: unchanged
System closure: no host activation
Evidence / command output: .#recovery-iso built successfully;
  drv /nix/store/0wjq5xb5zq2dgf5mh09v1q8s7sh7f6a3-nixos-minimal-26.05.20261002.774debe-x86_64-linux.iso.drv
  1496678400 bytes, SHA256 085a7b41e54e4e595f34fcea1ad9d37b48662d7eeae24d0f40781081d86678ca
Decision: prepare now because Phase 3 requires recovery media before root trial;
  pinned minimal installer plus rescue tools, no workstation imports/secrets.
Problems found: physical media boot not yet performed.
Rollback path: standalone artifact, no disks written.
Notes: ISO path and recovery procedure in docs/physical-root-validation.md;
  host currently exposes a Ventoy-labelled USB, contents/bootability unverified.
```

## 15.2 Recovery procedure to document

The document should answer, without needing chat history:

1. how to boot recovery media;
2. how to identify the MP600 safely;
3. how to mount Btrfs top-level subvolume ID 5;
4. how to inspect all subvolumes;
5. how to mount `@nix`, `@var`, `@home`, `@persist`;
6. how to select an older system closure;
7. how to reinstall a known-good boot entry;
8. how to inspect the persistent root-reset log;
9. how to recover `/etc/nixos` from `/persist`;
10. which old snapshots are forensic-only and not complete recursive rollback images.

## 15.3 Perform one non-destructive recovery drill

- [ ] boot the recovery medium;
- [ ] mount the filesystem read-only first;
- [ ] verify the documented commands locate the expected state;
- [ ] exit without changing the disk.

A recovery plan is not proven until it has been rehearsed.

---

# 16. Phase 10.5 — External backup and restore proof

Nix generations, Btrfs snapshots, Impermanence, and Git are all useful, but none of them replaces an independent backup of data that is not reproducible from the flake.

## 16.1 Inventory non-reproducible data

At minimum classify:

```text
/persist/secrets
uncommitted university work
Unreal project data not safely on the Git remote/LFS remote
local-only source repositories
documents/media not otherwise backed up
application data in /home that cannot simply be regenerated
```

## 16.2 Git/LFS audit

For important repositories:

- [ ] working tree state understood;
- [ ] intended commits pushed;
- [ ] Git LFS objects pushed and verified where used;
- [ ] no critical work exists only in an untracked directory.

## 16.3 Independent backup

- [ ] back up `/persist/secrets` in encrypted form;
- [ ] back up critical `/home` data to storage that is not the MP600;
- [ ] record backup date and destination;
- [ ] do not copy secrets into the NixOS repository.

## 16.4 Restore proof

Restore at least one representative file/repository and verify its hash/content.

**Completion gate:** a failure of the MP600 itself would be inconvenient, not catastrophic.

---

# 17. Phase 11 — Deliberately exercise NixOS activation and rollback lifecycle

Before the later system-wide experiment, the normal operating procedure must be routine.

## 17.1 `dry-activate`

- [ ] Use before changes that may restart important services.

```bash
sudo nixos-rebuild dry-activate --flake '.#desktop'
```

## 17.2 `test`

- [ ] Use for live activation where rebooting should return to the previous boot default.

```bash
sudo nixos-rebuild test --flake '.#desktop'
```

## 17.3 `boot`

- [ ] Use for changes that must only be evaluated at next reboot or for first-time dangerous boot behavior.

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

## 17.4 `switch`

- [ ] Use only when the configuration is already accepted as the intended running and boot configuration.

```bash
sudo nixos-rebuild switch --flake '.#desktop'
```

## 17.5 Rollback drill

- [ ] Boot an older generation from systemd-boot.
- [ ] Perform a live rollback once.
- [ ] Restore the intended generation afterward.

```bash
sudo nixos-rebuild switch --rollback
```

Record the exact recovery procedure in README/docs.

---

# 18. Phase 12 — Unify Nix store and generation lifecycle policy

This machine previously suffered very large uncontrolled Nix-store growth. A cleanup policy is therefore a baseline requirement, but it must not destroy useful rollback history.

## 18.1 Do not restore the old policy unchanged

The parked optimization branch had both:

```text
automatic GC with --delete-older-than 14d
+
custom system-generation pruning to keep 10
```

That is redundant and too aggressive to adopt blindly.

Important behavior: `nix-collect-garbage --delete-older-than ...` deletes profile generations before GC. Once those generations are deleted, rollback to them is impossible.

## 18.2 Choose one documented policy

Recommended starting point for this main workstation:

```text
systemd-boot visible entries:     20
profile retention horizon:        ~30 days
automatic GC:                     weekly or similarly infrequent
important milestone systems:      reconstructable from Git + flake.lock
active later research artifacts:  separate explicit lifetime policy
```

A reasonable implementation direction is a single automatic GC policy with a 30-day generation horizon rather than a 14-day horizon plus a second generation-pruning daemon.

If you instead prefer count-based retention, use one explicit system-profile pruning mechanism plus ordinary GC. Do not run two independent policies whose interaction is unclear.

## 18.3 Preview before first destructive cleanup

Use:

```bash
nix-store --gc --print-dead
```

and inspect generations before enabling the timer.

## 18.4 Run one store optimization pass

`auto-optimise-store = true` already handles new store data.

If a one-time full optimization has not been run since enabling it:

```bash
sudo nix-store --optimise
```

Run it outside benchmark/interactive-heavy hours.

## 18.5 One-time Nix store integrity verification

After storage/firmware stability work and before the final baseline, run one full store-content verification during an idle period:

```bash
sudo nix-store \
  --verify \
  --check-contents
```

This is intentionally not a frequent timer. It is a one-time confidence check that the local store has not accumulated silent corruption.

- [ ] verification completed;
- [ ] any corrupt path was repaired/rebuilt before continuing.

## 18.6 Schedule maintenance away from performance work

- [ ] GC window does not overlap Btrfs scrub.
- [ ] scrub/GC are not expected to fire during later benchmark windows.
- [ ] `systemctl list-timers --all` is part of the final baseline evidence.

## 18.7 Consider a low-disk-space guardrail

Optional:

- [-] Evaluated and deferred Nix `min-free` / `max-free` for the stock baseline: 763 GiB free of 896 GiB at the preparation checkpoint; representative large-build/workload space demand is not yet measured. Avoid arbitrary thresholds and an additional pressure-triggered collector outside the guarded maintenance window. Revisit with measured space requirements before large optimization builds.

Do not set arbitrary values. Base them on:

- normal store size;
- expected large rebuild size;
- free-space floor needed for Unreal/university work;
- size of future large source builds.

---

# 19. Phase 13 — Btrfs/storage baseline

## 19.1 Keep the current mount policy unless measurements show a problem

Current:

```text
compress=zstd:1
noatime
discard=async
```

Recommended:

- [x] keep `zstd:1`;
- [x] keep `noatime`;
- [x] keep `discard=async`.

Why:

- low-level zstd is a sensible fast compression setting;
- asynchronous discard is the preferred low-overhead discard model on modern Btrfs/NVMe;
- noatime avoids pointless metadata writes.

## 19.2 Explicitly reject filesystem folklore

- [-] do not enable `autodefrag` globally;
- [-] do not use `nodatacow` broadly;
- [-] do not disable checksums;
- [-] do not use `nobarrier`;
- [-] do not increase transaction commit intervals merely for benchmark numbers;
- [-] do not force compression globally;
- [-] do not add old `space_cache` tuning;
- [-] do not set Btrfs worker/thread counts without evidence.

These either reduce safety, conflict with compression/reflinks, or are workload-specific.

## 19.3 Keep scrub

Current monthly scrub is correct.

- [x] Btrfs scrub enabled.
- [ ] make the maintenance window explicit/documented if desired.
- [ ] verify the most recent scrub completed without uncorrectable errors before the final baseline.

```bash
sudo btrfs scrub status /
sudo btrfs device stats /
sudo btrfs filesystem usage -T /
```

## 19.4 Check NVMe health

Before the final tag:

```bash
sudo nvme smart-log /dev/nvme0
```

Record:

- critical warnings;
- media/data-integrity errors;
- percentage used;
- temperature;
- unsafe shutdowns;
- error-log entries.

Storage errors invalidate benchmark confidence and can turn rebuild failures into false compiler diagnoses.

## 19.5 Do not enable Btrfs quotas merely for curiosity

- [-] leave qgroups off unless a real quota/snapshot-accounting need appears.

They add complexity/overhead without helping the core experiment.

## 19.6 Define the role of `@snapshots`

- [ ] Decide whether `@snapshots` is:
  - manual forensic snapshots only;
  - future snapshot-manager storage;
  - unnecessary.

Do not add automated Snapper snapshots merely because the subvolume exists. Automated snapshot churn is extra I/O and space usage unless there is a real recovery requirement.

---

# 20. Phase 14 — Persistent log and crash-data bounds

Because `/var` is persistent, long-lived state should have explicit growth expectations.

## 20.1 Journal

- [x] inspect current journal size (2026-10-05: current identity 28.8 MiB, all identities 103 MiB; maintenance inventory below):

```bash
journalctl --disk-usage
```

- [?] if it can grow without a practical bound, set a reasonable persistent journal cap.

Choose the cap from actual usage. For this 1 TB workstation, something in the low-single-digit GiB range may be reasonable, but do not hardcode a number without checking how much diagnostic history is useful after failures.

## 20.2 Core dumps

- [x] inspect `/var/lib/systemd/coredump` and current coredump policy (2026-10-05: 213 MiB external files, upstream 2w retention; current identity no cores).
- [?] set an explicit retention/size policy if large Unreal/browser/game crashes are accumulating many GiB.

Keep enough crash evidence to diagnose failures, but do not allow persistent `/var` to become an uncontrolled artifact sink.

---

# 21. Phase 15 — Firmware and BIOS freeze

This is outside Nix expressions but **must happen before the final performance baseline** because firmware/microcode changes can affect both stability and measured performance.

## 21.1 Current motherboard firmware situation

Known motherboard:

```text
ASUS ROG Strix Z490-E Gaming
```

The previously known BIOS is 3201.

As of 2026-10-05, ASUS publishes BIOS **3402** dated 2026-08-05. ASUS states that it updates Intel IPU microcode and requires Intel ME **14.1.79.2540** first for the optimized configuration.

## 21.2 Decide whether to update now

**Recommended:** perform any intended BIOS/ME update **before** the final pre-experiment baseline, not during the later experiment.

- [ ] capture every current OC/memory/firmware setting before flashing;
- [ ] update Intel ME first if following ASUS 3402 guidance;
- [ ] update BIOS;
- [ ] re-enter intended stable settings;
- [ ] re-run full CPU/memory/thermal stability tests;
- [ ] freeze firmware for the experiment campaign.

### Record at minimum

```text
BIOS version:
BIOS date:
Intel ME version:
CPU all-core target:
CPU cache/ring ratio:
CPU core voltage mode/value:
LLC:
AVX offset:
power/current limits:
XMP/manual RAM timings:
RAM voltage:
Above 4G decoding:
Resizable BAR:
C-states:
Intel Speed Shift/HWP:
other non-default OC settings:
```

## 21.3 Current known performance-oriented firmware state

Known current intent:

- Intel Core i5-10600K;
- approximately 5.0 GHz all-core;
- cache/ring ratio approximately 48;
- 32 GiB DDR4-3200.

Do not assume these survived a firmware flash. Reconfirm them.

## 21.4 ReBAR / Above 4G audit

For the RX 9070 XT:

- [x] verify whether Resizable BAR and Above 4G decoding are enabled and actually exposed to the GPU;
- [-] if supported and currently off, evaluate enabling them **before** the final baseline; already exposed, no change needed;
- [ ] once chosen, freeze the policy.

This is a stable platform-level performance feature, not part of the later compiler experiment.

---

# 22. Phase 16 — Kernel policy

## 22.1 Keep the NixOS stable kernel as the stock baseline

- [ ] stay on the NixOS 26.05 default/stable kernel line unless a concrete hardware defect requires otherwise.

The handoff recorded a 6.18-series NixOS kernel and the current workstation is functioning correctly.

## 22.2 Do not import Gentoo kernel tuning by habit

Explicitly reject for the stock baseline unless a separately measured requirement exists:

- [-] CachyOS kernel;
- [-] Zen kernel;
- [-] custom PREEMPT_FULL solely because it was previously tested on Gentoo;
- [-] custom scheduler patches;
- [-] `isolcpus`;
- [-] `nohz_full`;
- [-] `rcu_nocbs`;
- [-] scheduler debug knobs;
- [-] manual IRQ pinning;
- [-] disabling SMT;
- [-] disabling CPU idle states.

These change the baseline too substantially or target special workloads.

## 22.3 Keep security mitigations

- [-] do **not** use `mitigations=off`;
- [-] do not disable Spectre/Meltdown/MDS-family mitigations for baseline performance.

If mitigation cost is ever studied, that is a separate security/performance experiment, not a “free” baseline optimization.

---

# 23. Phase 17 — CPU frequency/power policy

The i5-10600K uses Intel P-state/Speed Shift behavior where the meaning of `powersave` and `performance` is not equivalent to the old generic governors.

## 23.1 First record reality

Run:

```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver

grep -H . \
  /sys/devices/system/cpu/cpufreq/policy*/scaling_governor

grep -H . \
  /sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference \
  2>/dev/null || true
```

Record idle and loaded clocks/temperature.

## 23.2 Baseline recommendation

- [ ] keep the normal desktop policy responsive and thermally sane;
- [x] retain GameMode for gaming-specific temporary performance policy;
- [-] do not force a permanent maximum-frequency policy merely because it sounds faster.

On Intel HWP, `intel_pstate`'s `performance` mode strongly biases or constrains the hardware toward maximum performance. That can increase idle power/heat without necessarily improving normal interactive work enough to justify an always-on policy.

### Decision gate

- [?] If the current governor/EPP policy is demonstrably leaving performance on the table in normal work, compare the alternatives once **before** the final tag.
- [ ] Whichever normal policy is selected must then be frozen and recorded.

The later benchmark harness can control benchmark-session conditions; that is separate from the stock workstation baseline.

---

# 24. Phase 18 — Memory and swap policy

Current physical swap:

```text
32 GiB disk swap partition
```

RAM:

```text
32 GiB DDR4-3200
```

## 24.1 Do not cargo-cult `vm.swappiness`

- [-] do not set `vm.swappiness=10` merely because desktop-tuning guides say so.
- [ ] first observe real memory pressure under Unreal, Blender, browsers, VM tests, and large Nix builds.

Swappiness is workload dependent.

## 24.2 ZRAM decision

ZRAM is stable NixOS functionality, but it is not automatically a performance win on a 32 GiB desktop with existing disk swap.

- [?] measure whether normal development causes meaningful swap pressure or OOM risk.
- [ ] if yes, test a modest high-priority zram layer with disk swap as fallback.
- [-] if memory pressure is rare, leave the simpler existing swap policy alone.

Do not enable zram and zswap simultaneously.

## 24.3 Transparent Huge Pages

- [-] do not globally force THP `always`;
- [-] do not globally force THP `never`;
- [x] retain kernel/default behavior unless a real workload demonstrates a problem.

Linux exposes `always`, `madvise`, and `never`, and defrag policy itself is a trade-off. This is a workload-level variable, not baseline folklore.

## 24.4 Avoid arbitrary VM sysctls

Do not add a “performance sysctl pack”.

In particular, do not tune without evidence:

```text
vm.dirty_ratio
vm.dirty_background_ratio
vm.vfs_cache_pressure
vm.page-cluster
kernel.sched_*
```

Also verify what NixOS already configures before duplicating settings. Modern NixOS already ships generous defaults for several desktop/development limits such as `vm.max_map_count` and inotify counts.

---

# 25. Phase 19 — IRQ and I/O scheduler policy

## 25.1 IRQ balancing

- [?] do not enable `irqbalance` merely because it exists.
- [?] do not disable it merely because benchmark guides dislike migration.

First inspect actual interrupt distribution during:

- GPU load;
- NVMe load;
- network load.

For this single-socket 6C/12T desktop, kernel defaults may already be adequate.

If irqbalance materially improves real workload latency/throughput without increasing run-to-run noise, adopt it **before** the final tag. Otherwise leave it out.

## 25.2 NVMe scheduler

- [x] keep the kernel-selected NVMe scheduler by default.
- [-] do not force `mq-deadline`, `kyber`, or BFQ without measurement.

Check reality:

```bash
cat /sys/block/nvme0n1/queue/scheduler
```

The scheduler is a workload-specific I/O variable and should not be changed based on old SATA-era advice.

---

# 26. Phase 20 — Graphics / RDNA4 baseline

## 26.1 Keep the standard NixOS graphics stack

Current:

```nix
hardware.graphics.enable = true;
hardware.graphics.enable32Bit = true;
```

This is correct for Steam/Proton and native 64-bit workloads.

## 26.2 Keep stable Mesa unless there is a real blocker

The machine already has successful RX 9070 XT / RADV / Vulkan usage in important applications.

- [ ] update the **stable 26.05 lockfile deliberately once** before the final baseline;
- [ ] validate the resulting Mesa/RADV;
- [ ] then freeze it.

- [-] do not globally replace Mesa with unstable merely to chase newer benchmark numbers;
- [-] do not use random `RADV_PERFTEST` variables as baseline policy;
- [-] do not force alternate Vulkan ICDs globally;
- [-] do not add global shader/compiler environment hacks unless required for a known application bug.

## 26.3 Validate both 64-bit and 32-bit Vulkan

Before final tag:

```bash
vulkaninfo --summary
```

Also validate a 32-bit Steam/Proton workload in practice.

## 26.4 GPU power/profile tweaks

- [-] do not manually force AMD GPU clocks or power profiles as the normal baseline.
- [?] if a stable firmware-supported GPU mode is consciously chosen, set it before baseline freeze and validate it thermally.

The goal is a reliable workstation control, not an overclock benchmark image.

---

# 27. Phase 21 — Gaming baseline

Current good choices:

- [x] Steam enabled;
- [x] GameMode enabled;
- [x] Gamescope installed;
- [x] MangoHud installed;
- [x] 32-bit graphics enabled.

## 27.1 Validate rather than over-tune

- [ ] launch representative Vulkan game;
- [ ] launch representative Proton game;
- [ ] verify GameMode requests succeed;
- [ ] verify MangoHud works;
- [ ] verify Gamescope path used for HDR/fullscreen if part of normal workflow;
- [ ] verify audio;
- [ ] verify controller support.

## 27.2 Do not replace lightweight working desktop components for theoretical gains

Waybar has already demonstrated low resource use in the project history. Replacing it to save a few MiB does not belong in this pre-experiment optimization pass.

- [-] no bar/window-manager rewrite for micro-optimization;
- [-] no disabling useful desktop services for negligible memory savings.

Optimize things that can plausibly alter real workload performance or experimental stability.

---

# 28. Phase 22 — Cooling and thermal stability

This is a **hard gate** because later whole-system builds will create long sustained CPU load.

## 28.1 Keep the proven Commander Core policy

Current host policy:

```text
base fan duty:    60%
high fan duty:   100%
pump duty:       100%
high threshold:  65 °C
low threshold:   60 °C
high delay:       1 s
low delay:       10 s
wake interval:   10 s
```

Do not replace the pinned working implementation before the optimization campaign merely because a newer backend exists.

## 28.2 Validate service resilience

- [ ] cold boot;
- [ ] warm reboot;
- [ ] suspend/resume if suspend is used;
- [ ] service restart;
- [ ] USB reset/recovery;
- [ ] sustained CPU load;
- [ ] confirm watchdog recovery behavior.

## 28.3 Sustained CPU thermal test

Install/use a validation environment with `stress-ng` and monitoring tools.

Example smoke/stability load:

```bash
stress-ng \
  --cpu 12 \
  --timeout 30m \
  --metrics-brief
```

Treat 30 minutes as a smoke test, not proof that a 5.0 GHz overclock is fully stable. Before the final tag, also run the longer OC/memory stability procedure you trust for this hardware and include large real compiler builds in the validation mix.

Monitor separately:

```bash
watch -n 1 sensors
```

### Pass criteria

- no thermal shutdown;
- no WHEA/MCE-style hardware errors;
- no repeated clock collapse caused by thermal throttling;
- cooling daemon remains alive;
- temperatures remain inside the chosen safe envelope.

---

# 29. Phase 23 — Overclock and memory stability

The optimization project is useless if a marginal 5 GHz overclock produces rare wrong-code crashes that look like compiler bugs.

## 29.1 CPU stability

- [ ] sustained all-core test;
- [ ] mixed integer/FP load;
- [ ] repeated large Nix builds;
- [ ] check kernel log for hardware errors;
- [ ] verify no unexplained process SIGILL/SIGSEGV under load.

## 29.2 RAM stability

- [ ] run a dedicated memory test outside normal desktop usage;
- [ ] exercise most of the 32 GiB;
- [ ] verify zero errors.

If BIOS was updated, repeat these tests even if the OC was previously stable.

## 29.3 Freeze the OC

Once the firmware + OC pass:

```text
BIOS / ME revision
CPU ratio
cache ratio
memory frequency/timings
voltages
power limits
```

become part of the baseline manifest.

Do not adjust them halfway through compiler-optimization measurements.

---

# 30. Phase 24 — Development-workload acceptance

A “fast” baseline that breaks university work is not a valid baseline.

## 30.1 Unreal Engine

Validate the actual expected workflow, not just “the editor process launches”:

- [ ] official UE 5.8.2 engine path still works;
- [ ] Steam FHS wrapper works;
- [ ] native Wayland path works as intended;
- [ ] Vulkan uses RX 9070 XT/RADV, not software fallback;
- [ ] actual `AI_Gavin_Project` opens;
- [ ] C++ target builds successfully;
- [ ] UnrealBuildTool uses Epic's intended toolchain/sysroot;
- [ ] editor can run the project;
- [ ] no global compatibility environment pollution was introduced.

## 30.2 Blender

- [ ] intended Blender build launches;
- [ ] RX 9070 XT ROCm/HIP path is available where expected;
- [ ] Cycles GPU render completes;
- [ ] no driver crash under a representative render.

## 30.3 Android Studio / KVM

- [ ] KVM access remains correct;
- [ ] emulator boots;
- [ ] Java workflow works;
- [ ] no persistence change breaks AVD/user state.

## 30.4 C/C++ development

- [ ] clangd works;
- [ ] GCC/Clang build tools work from intended user/project environment;
- [ ] no global compiler flags contaminate builds.

## 30.5 Browser, audio, networking, Bluetooth

- [ ] Firefox works;
- [ ] PipeWire works;
- [ ] Creative Stage Pro works;
- [ ] Ethernet/Wi-Fi normal;
- [ ] Bluetooth normal if used;
- [ ] reconnect after reboot works.

---

# 31. Phase 25 — Clean environment audit

Before the final tag, prove the control system does not contain accidental optimization variables.

## 31.1 Search environment

```bash
env | grep -E \
  '^(CFLAGS|CXXFLAGS|CPPFLAGS|LDFLAGS|RUSTFLAGS|NIX_CFLAGS_COMPILE|NIX_LDFLAGS|LD_LIBRARY_PATH|MALLOC_CONF)=' \
  || true
```

Expected: no global optimization values.

## 31.2 Search repository

```bash
cd /etc/nixos

rg -n \
  'CFLAGS|CXXFLAGS|NIX_CFLAGS_COMPILE|NIX_LDFLAGS|march=|mtune=|flto|fprofile|llvm-bolt|BOLT' \
  --glob '!optimization/**'
```

Any match outside the deliberately parked/inert optimization area must be explained.

## 31.3 Confirm optimization module is inert

Before the experiment:

- [x] no system build flag is changed by importing `optimization/default.nix`;
- [x] `optimization/` cannot alter the desktop unless explicitly enabled later;
- [x] no old prototype output from `feat/optimization-framework` is wired into `main`.

---

# 32. Phase 26 — Stable Nix build behavior

## 32.1 Do not add ccache/sccache to the stock system build path

- [-] no global ccache for Nixpkgs builds;
- [-] no hidden compiler cache that makes provenance harder to reason about.

Nix already provides content-addressed build caching/substitution semantics. Compiler caches add another identity layer and are unnecessary for the control baseline.

## 32.2 Keep normal sandboxing

- [x] retain Nix sandbox/default isolation.
- [-] do not disable sandboxing to make builds “faster”.

## 32.3 Do not move Nix builds into RAM by default

A tmpfs build directory can speed some builds but 32 GiB RAM is not enough to assume every large LLVM/browser-style package can safely build there.

- [-] no global tmpfs Nix build directory in the baseline.
- [?] a dedicated high-RAM builder can be considered later as build infrastructure, not runtime tuning.

## 32.4 Optional future remote builder

Distributed/remote builds are valuable once system rebuild volume becomes high, but not a prerequisite for correctness.

- [-] defer unless another suitable Linux builder actually exists.

---

# 33. Phase 27 — Add a dedicated validation / observability dev shell

Keep diagnostic tools out of the permanently ambient system where possible.

Create a dev shell such as:

```text
devShells.x86_64-linux.validation
```

Candidate tools:

```text
stress-ng
hyperfine
perf
turbostat
hwloc
numactl
sysstat
lm_sensors
nvme-cli
btrfs-progs
pciutils
usbutils
vulkan-tools
mesa-demos
```

Verify exact package attribute names against the pinned 26.05 nixpkgs before implementation.

### Why

- reproducible diagnostic tooling;
- no random host-installed benchmark binaries;
- exact versions captured by `flake.lock`;
- cleaner global package set.

---

# 34. Phase 28 — Baseline system telemetry capture

Create a script or flake app such as:

```text
nixos-baseline-info
```

This is not the later optimization runner. It is a simple snapshot of the stock workstation state.

Record:

## Git/Nix identity

```text
Git commit
Git tag
flake.lock hash
nixpkgs revision
Nix version
NixOS version
system closure path
system derivation path
closure size
```

## CPU

```text
model
microcode revision
online CPUs
SMT state
scaling driver
governor
EPP
current kernel command line
```

## Firmware

```text
BIOS version/date
ME version if practically retrievable
```

## Memory

```text
RAM amount
swap devices
zram status
THP mode
```

## GPU

```text
PCI identity
kernel driver
Mesa/RADV version
Vulkan summary
32-bit Vulkan practical validation
```

## Storage

```text
NVMe model/firmware
SMART health
Btrfs mount options
Btrfs filesystem/device usage
scrub status
```

## Runtime

```text
kernel
boot ID
systemd version
failed units
running services
timers
loaded modules
```

## Thermal / cooling

```text
idle temperatures
Commander Core service state
pump/fan policy version
```

## Persistence

```text
root subvolume
persistent subvolumes
machine-id
reset diagnostic state
```

Suggested commands:

```bash
nixos-version
nix --version
uname -a
cat /proc/cmdline
lscpu
grep -m1 '^microcode' /proc/cpuinfo
cat /sys/class/dmi/id/bios_version
cat /sys/class/dmi/id/bios_date
swapon --show
cat /sys/kernel/mm/transparent_hugepage/enabled
findmnt -R /
systemctl --failed --no-pager
systemctl list-timers --all --no-pager
vulkaninfo --summary
sensors
nix path-info -S /run/current-system
```

Store the resulting **non-secret** manifest in Git under something like:

```text
docs/baselines/pre-optimization/
```

Do not store device secrets or password hashes.

---

# 35. Phase 29 — Closure diffing as a normal review tool

Before accepting final baseline commits, compare the system closure.

Build:

```bash
nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel'
```

Then compare:

```bash
nix store diff-closures \
  /run/current-system \
  ./result
```

Use this to answer:

- which packages changed?
- which versions changed?
- did a small config change unexpectedly move Mesa/kernel/LLVM?
- did an unstable package leak into the system closure?
- did an input update change far more than expected?

Add closure-diff output to important baseline PR notes.

---

# 36. Phase 30 — Decide the final stable package/input update point

Do one deliberate stable refresh **before** freezing the baseline.

## 36.1 Update policy

- [ ] update `nixos-26.05` input to the chosen current stable revision;
- [ ] update Home Manager release input consistently;
- [ ] update Disko/Impermanence only if their current locked revisions are compatible with the now-tested design;
- [ ] update `nixpkgs-unstable` only for the software that actually requires it;
- [ ] re-run all validation.

Do not update every input simply because `nix flake update` exists. Review the lockfile diff.

## 36.2 Freeze after acceptance

Once the final baseline is tagged:

- [ ] no `flake.lock` update during benchmark series unless intentionally starting a new experiment epoch;
- [ ] no automatic package updates;
- [ ] no BIOS update;
- [ ] no Mesa switch;
- [ ] no kernel switch;
- [ ] no CPU OC change.

---

# 37. Phase 31 — Background-service audit

The goal is not to chase a minimal process count. The goal is to remove genuinely unused background work and document expected daemons.

Run:

```bash
systemctl --failed --no-pager

systemctl list-units \
  --type=service \
  --state=running \
  --no-pager

systemctl list-timers \
  --all \
  --no-pager

systemd-analyze blame
systemd-analyze critical-chain
```

For each recurring service/timer ask:

```text
needed for workstation?       keep
needed only occasionally?     on-demand or timer
unused legacy component?      remove
benchmark-contaminating?      schedule away from measurements
```

Do **not** disable:

- NetworkManager;
- PipeWire;
- required graphical/session services;
- cooling;
- microcode/firmware support;
- security services;

for tiny synthetic gains.

---

# 38. Phase 32 — Explicit stable performance-tuning decision table

This table is the policy boundary between “good baseline optimization” and “later experiment / folklore”.

| Item | Baseline decision | Reason |
|---|---|---|
| Current Btrfs `zstd:1` | **KEEP** | low-overhead compression |
| `noatime` | **KEEP** | removes unnecessary atime writes |
| `discard=async` | **KEEP** | modern low-overhead discard |
| Monthly Btrfs scrub | **KEEP** | integrity, not speed |
| Intel microcode | **KEEP** | correctness/security/stability |
| GameMode | **KEEP** | temporary workload-specific policy |
| 32-bit Mesa | **KEEP** | Steam/Proton requirement |
| High `nofile` limits | **KEEP** | development workload stability |
| Nix store dedup | **KEEP** | storage efficiency |
| Stable NixOS kernel | **KEEP** | control stability |
| Stable Mesa | **KEEP** after final update | control stability |
| Always-on CPU `performance` governor | **MEASURE / usually do not force globally** | heat/power vs small normal-use benefit |
| ZRAM | **MEASURE** | useful only under real memory pressure |
| `irqbalance` | **MEASURE** | topology/workload dependent |
| alternate NVMe scheduler | **MEASURE / usually leave default** | workload dependent |
| ReBAR | **VERIFY / enable if supported and desired** | stable platform feature |
| THP forced always/never | **REJECT** | workload dependent |
| custom kernel | **REJECT FOR CONTROL** | creates another major variable |
| PREEMPT_FULL change | **REJECT FOR CONTROL** | latency trade-off, not universal throughput win |
| `mitigations=off` | **REJECT** | unsafe and invalid stock baseline |
| global compiler flags | **REJECT** | belongs to later experiment |
| global `-O3` | **REJECT** | belongs to later experiment |
| global LTO | **REJECT** | belongs to later experiment |
| global PGO | **REJECT** | belongs to later experiment |
| BOLT | **REJECT HERE** | belongs to later experiment |
| manual IRQ pinning | **REJECT FOR CONTROL** | benchmark-specific |
| `isolcpus`/`nohz_full` | **REJECT FOR CONTROL** | benchmark/RT-specific |
| disable SMT | **REJECT FOR CONTROL** | workload-specific |
| BBR/network sysctl pack | **REJECT UNLESS NETWORK IS TARGET** | irrelevant to main goal |
| `nodatacow` globally | **REJECT** | loses checksumming/compression semantics |
| `nobarrier` | **REJECT** | corruption risk |
| `autodefrag` globally | **REJECT** | latency/reflink drawbacks |
| tmpfs global Nix builds | **REJECT** | 32 GiB capacity risk |
| ccache in system builds | **REJECT** | provenance complexity |
| random LD_LIBRARY_PATH | **REJECT** | global contamination |

---

# 39. Phase 33 — Optional low-risk tuning experiments that must finish before the tag

If you want to evaluate any of these, do it **now**, not during PGO/BOLT work:

1. CPU normal-use governor/EPP policy.
2. ReBAR.
3. zram.
4. irqbalance.
5. NVMe scheduler.
6. any stable Mesa/kernel deviation from NixOS 26.05 defaults.

For each candidate:

```text
baseline A
    ↓
one policy change
    ↓
real workload + stability check
    ↓
keep or reject
    ↓
return to a single final stock policy
```

Document the conclusion. Do not keep a pile of simultaneously unproven tweaks.

---

# 40. Phase 34 — Final compatibility acceptance matrix

Before final tag, complete this matrix on the physical host.

| Area | Required result | Status |
|---|---|---|
| boot | 5 consecutive successful boots | [ ] |
| rollback | older generation booted successfully | [ ] |
| ephemeral root, if adopted | disposable state resets correctly | [ ] |
| persistence | expected state survives | [ ] |
| machine-id | follows documented final policy | [ ] |
| systemd | zero unexpected failed units | [ ] |
| networking | Ethernet/Wi-Fi normal | [ ] |
| Bluetooth | normal if used | [ ] |
| audio | PipeWire + Creative Stage Pro normal | [ ] |
| Hyprland/UWSM | graphical session normal | [ ] |
| Waybar | normal/low resource use | [ ] |
| Steam | launches | [ ] |
| Proton | representative game works | [ ] |
| GameMode | request succeeds | [ ] |
| Gamescope | representative use works | [ ] |
| HDR path | normal workflow works if required | [ ] |
| controller | normal | [ ] |
| Unreal 5.8.2 | editor + real project | [ ] |
| Unreal C++ | project target builds | [ ] |
| Blender | launches | [ ] |
| Blender GPU compute | representative render | [ ] |
| Android Studio | launches | [ ] |
| Android emulator | KVM device boots | [ ] |
| clangd | indexing works | [ ] |
| Git/Git LFS | normal | [ ] |
| Btrfs scrub | clean | [ ] |
| NVMe health | no critical warning | [ ] |
| cooling | service survives sustained load | [ ] |
| CPU OC | sustained stable | [ ] |
| RAM | error-free validation | [ ] |
| CI | green | [ ] |
| heavy VM tests | green | [ ] |

Any unexplained failure blocks the final baseline.

---

# 41. Phase 35 — Baseline soak period

Do not tag the system immediately after the last feature lands.

Recommended soak:

- several normal university/work days;
- multiple cold boots;
- multiple warm reboots;
- gaming session;
- Unreal session;
- large C/C++ build;
- Blender GPU render;
- at least one large Nix build;
- one suspend/resume cycle if suspend is part of normal use.

During the soak:

- [ ] no unexplained system freeze;
- [ ] no kernel GPU reset;
- [ ] no filesystem error;
- [ ] no recurring failed unit;
- [ ] no cooling failure;
- [ ] no login/persistence regression;
- [ ] no spontaneous root-reset anomaly;
- [ ] no accidental store/disk growth problem.

Record problems rather than “working around” them outside the config.

---

# 42. Phase 36 — Final baseline freeze procedure

This is the final gate immediately before optimization work is allowed to start.

## 42.1 Repository must be clean

```bash
cd /etc/nixos

git status --short
git diff --check
```

Expected:

```text
no output from git status --short
```

## 42.2 Run all fast checks

```bash
nix flake check --print-build-logs
```

## 42.3 Run all explicit heavy correctness tests

Run:

- Impermanence positive test;
- safety/recovery matrix;
- machine-id test if it remains separate;
- generic workstation correctness VM;
- any recovery/specialisation test introduced by this plan.

## 42.4 Build the exact desktop closure

```bash
nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --print-build-logs
```

## 42.5 Review closure diff

```bash
nix store diff-closures \
  /run/current-system \
  ./result
```

Explain every significant package/input change.

## 42.6 Test activation

```bash
sudo nixos-rebuild dry-activate --flake '.#desktop'
sudo nixos-rebuild test --flake '.#desktop'
```

Check:

```bash
systemctl --failed --no-pager
```

## 42.7 Install final boot system

After successful live test:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Reboot and validate from the exact booted closure.

If the configuration is already fully accepted and the activation semantics are safe, `switch` is also valid. The final recorded baseline must correspond to the closure that was actually boot-tested.

## 42.8 Capture final manifest

Write the Phase 28 baseline manifest.

Also record:

```bash
readlink -f /run/current-system
git rev-parse HEAD
sha256sum flake.lock
nix path-info -S /run/current-system
```

## 42.9 Push and require green CI

- [ ] push final `main`;
- [ ] CI passes;
- [ ] no uncommitted local hotfix remains.

## 42.10 Create final tag

Suggested name:

```text
nixos-26.05-pre-optimization-baseline
```

Use an annotated tag:

```bash
git tag -a \
  nixos-26.05-pre-optimization-baseline \
  -m 'Freeze final NixOS baseline before system optimization experiments'

git push origin \
  nixos-26.05-pre-optimization-baseline
```

Record the tag's commit and system closure in `docs/baselines/`.

---

# 43. Final GO / NO-GO checklist

Do **not** start the optimization experiment until every hard gate below is true.

## Repository

- [ ] `main` contains the final stable workstation.
- [ ] working tree clean.
- [ ] CI green.
- [ ] flake.lock frozen.
- [ ] architecture docs current.
- [ ] old optimization branch treated as prototype/reference only.
- [ ] final baseline tag pushed.

## Impermanence / state

- [x] safety/recovery matrix green.
- [x] machine-id policy decided (persist stable identity in opt-in target).
- [ ] physical root-reset path validated if adopted.
- [ ] known-good non-destructive recovery path exists.
- [ ] persistence contract documented.
- [ ] no secret in Git.
- [ ] `/home` and `/var` policy intentionally frozen.

## Recovery

- [ ] old generation rollback tested.
- [ ] specialisation/recovery boot option tested.
- [ ] recovery media built.
- [ ] recovery media booted once.
- [ ] Btrfs mount/recovery procedure documented.

## Hardware

- [ ] intended BIOS/ME version frozen.
- [ ] microcode recorded.
- [ ] OC frozen and stress-stable.
- [ ] RAM validated.
- [ ] cooling validated.
- [ ] GPU stable.
- [ ] NVMe healthy.
- [ ] Btrfs scrub clean.

## Normal system policy

- [ ] kernel frozen.
- [ ] Mesa frozen.
- [ ] CPU governor/EPP recorded.
- [ ] swap/zram policy frozen.
- [ ] THP policy recorded.
- [ ] NVMe scheduler recorded.
- [ ] IRQ policy recorded.
- [ ] no unsupported tuning pack.

## Workloads

- [ ] Unreal C++ workflow accepted.
- [ ] Blender GPU workflow accepted.
- [ ] Steam/Proton accepted.
- [ ] Android/KVM accepted.
- [ ] audio/network/session accepted.
- [ ] normal work soak completed.

## Experimental cleanliness

- [ ] no global compiler flags.
- [ ] no global linker flags.
- [ ] no global `LD_LIBRARY_PATH`.
- [ ] optimization module inert.
- [ ] baseline system manifest committed.
- [ ] system closure path recorded.
- [ ] maintenance timers documented.

---

# 44. Exact stopping point

When the GO checklist is complete:

```text
main
  │
  └── tag: nixos-26.05-pre-optimization-baseline
            │
            ├── fixed flake.lock
            ├── fixed firmware
            ├── fixed kernel/Mesa
            ├── fixed root/persistence policy
            ├── fixed normal performance policy
            ├── tested rollback/recovery
            ├── tested VM correctness
            └── proven productive workstation
```

At that point:

- create a **fresh optimization branch from the tag**;
- selectively reuse useful ideas/code from the parked prototype;
- do not merge the old mixed branch wholesale;
- stop changing ordinary workstation policy unless a real defect is discovered.

**This is where this document ends.**

Anything involving `-march=native`, LTO, PGO, BOLT, their package targeting, their training workloads, or their performance-comparison procedure belongs to the next project document.

---

# Appendix A — Recommended task-record template

Copy this under any complicated task.

```markdown
### Task: <name>

**Status:** TODO / IN PROGRESS / BLOCKED / DONE / REJECTED  
**Reason:**  
**Current state:**  
**Desired state:**  
**Dependencies:**  

#### Implementation

1.
2.
3.

#### Validation

- [ ]
- [ ]
- [ ]

#### Evidence

```text
paste non-secret output here
```

#### Result

**Commit:**  
**Generation:**  
**System closure:**  
**Decision:**  
**Rollback:**  
**Follow-up:**  
```

---

# Appendix B — Baseline change log template

```markdown
## YYYY-MM-DD — <change>

### Why

### Files changed

### Before

### After

### Closure diff

### Validation

### Performance/stability implication

### Rollback path

### Commit / PR

### Accepted into baseline?
- [ ] yes
- [ ] no
```

---

# Appendix C — Baseline hardware record template

```text
CPU:
CPU stepping:
microcode:
motherboard:
BIOS:
ME:
RAM:
RAM frequency:
RAM timings:
GPU:
GPU VBIOS:
Mesa:
kernel:
NVMe:
NVMe firmware:
monitor:
PSU:
cooling:

CPU ratio:
cache ratio:
core voltage:
LLC:
AVX offset:
power limits:
ReBAR:
Above 4G:
HWP/Speed Shift:
governor:
EPP:

Btrfs options:
swap:
zram:
THP:
I/O scheduler:
irqbalance:
```

---

# Appendix D — Baseline runtime evidence template

```text
date:
git commit:
git tag:
flake.lock sha256:
nixpkgs rev:
Nix version:
NixOS version:
system closure:
system drv:
closure size:

kernel:
cmdline:
BIOS:
microcode:

CPU scaling driver:
governor:
EPP:

Mesa/RADV:
Vulkan device:

root subvolume:
Btrfs mount options:
scrub status:
NVMe SMART:

machine-id:
boot-id:

failed units:
maintenance timers:
Commander Core service:
idle temperatures:
load temperatures:

notes:
```

---

# Appendix E — Things deliberately **not** to “optimize” in the stock baseline

Keep this list because these changes often reappear in Linux tuning guides.

```text
mitigations=off
nospectre_v*
nopti
nobarrier
global nodatacow
global checksum disable
global autodefrag
random Btrfs thread-pool values
random dirty_ratio tuning
vm.swappiness folklore values
forced THP always
forced THP never
custom CPU scheduler patches
CachyOS/Zen kernel solely for benchmark chasing
PREEMPT_FULL solely for benchmark chasing
isolcpus
nohz_full
rcu_nocbs
manual IRQ pinning
disable SMT
disable C-states
force fixed clocks as normal desktop policy
global AMDGPU clock forcing
random RADV_PERFTEST variables
global LD_LIBRARY_PATH
global CFLAGS/CXXFLAGS/LDFLAGS
global -O3
global -march=native
global LTO
compiler caches in Nix system builds
tmpfs for every Nix build
BBR/network tuning without a network target
benchmarking in QEMU
disabling useful desktop services to save a few MiB
```

Each of these is either:

- unsafe;
- workload-specific;
- a later experimental variable;
- too large a baseline change;
- or unlikely to matter enough to justify the loss of control.

---

# Appendix F — Current project-specific cleanup backlog

Use this as a smaller tracker after Impermanence is complete.

```text
[~] package ownership split (prepared and checked on feat/workstation-validation)
[~] liquidctl derivation accepts explicit src (identical package drv)
[~] Commander Core remaining assertions (source checked; hardware acceptance open)
[~] Python lint/syntax/unit checks (local checks passed; CI/integration pending)
[ ] README Impermanence/test updates
[x] repository description
[x] desktop evaluation CI check
[~] generic workstation VM (boot/service/HM smoke passed; branch integration pending)
[~] recovery ISO (built, physical boot/drill pending)
[ ] specialisation/recovery boot design
[ ] unified GC/generation policy
[ ] journal/core-dump growth policy
[x] validation dev shell
[x] baseline-info capture app/script
[x] closure-diff review procedure
[ ] BIOS/ME decision
[ ] OC/RAM revalidation
[ ] ReBAR audit
[ ] CPU policy audit
[ ] zram decision
[ ] irqbalance decision
[ ] NVMe scheduler audit
[ ] full workload acceptance
[ ] final soak
[ ] final pre-optimization tag
```

---

# Appendix G — Sources used to build this plan

## Project / attached sources

- `NIXOS_Project_Complete_Handoff_2026-10-05(1).md`
- `NixOS_Impermanence_Handoff_2026-10-04(2).md`
- `Analyze And Plan Project Continuation.txt`
- `Config Organization Advice.txt`
- `NixOS Features Testing.txt`
- `Compare Linux Performance Ceilings.txt`
- current pasted/review histories attached to the conversation

## Live repository state

- `https://github.com/P2949/NixosConf/tree/main`
- `https://github.com/P2949/NixosConf/tree/feat/impermanence`
- `https://github.com/P2949/NixosConf/tree/feat/optimization-framework`

The live branch heads were rechecked when this document was produced.

## Upstream references

- NixOS stable manual: `https://nixos.org/manual/nixos/stable/`
- NixOS specialisations: `https://wiki.nixos.org/wiki/Specialisation`
- Linux `intel_pstate`: `https://docs.kernel.org/admin-guide/pm/intel_pstate.html`
- Linux Transparent Huge Pages: `https://docs.kernel.org/admin-guide/mm/transhuge.html`
- Btrfs administration/mount options: `https://btrfs.readthedocs.io/en/stable/Administration.html`
- Btrfs trim/discard: `https://btrfs.readthedocs.io/en/latest/Trim.html`
- Nix garbage collection: `https://nix.dev/manual/nix/2.34/command-ref/nix-collect-garbage`
- ASUS ROG Strix Z490-E BIOS support: `https://rog.asus.com/motherboards/rog-strix/rog-strix-z490-e-gaming-model/helpdesk_bios/`

---

# Appendix H — Final philosophy

The desired final state is **not** “a Linux machine with every tuning knob turned on.”

It is:

```text
a productive workstation
+
a small number of proven stable optimizations
+
explicit firmware and runtime policy
+
clean persistent state
+
tested recovery
+
reproducible Nix inputs
+
a known system closure
+
no accidental compiler tuning
+
enough observability to explain failures
+
a hard baseline tag
```

That gives the later compiler/binary optimization project something much more valuable than a superficially “fast” starting point:

> **a trustworthy control system.**


## Execution checkpoint — 2026-10-05, after publication

**PROVEN:** remote and local HEAD `141c67745ac88fad0a17fa60eb479650087ee765`;
CI run `37253111052` completed successfully; final local fast checks passed;
current safety/A/recovery/B tests passed; recovery ISO and parent/child desktop
closures built. Phase 1 is complete. Phase 2 VM policy gate is complete.
Physical Phase 3 is prepared but has not been installed or booted.

**INCOMPLETE:** independent backup/restore evidence, privileged topology and
credential preflight, recovery-media boot/drill, three physical trial boots,
then all subsequent phase gates through final tag and fresh experiment branch.
The running system remains unchanged. No main merge, generation pruning,
forensic deletion, firmware change, automatic GC or compiler tuning occurred.
The master objective remains active; this checkpoint does not complete it.

**NEXT ACTION:** operator answers the pending backup/recovery-medium question
and follows `docs/physical-root-validation.md` preflight. Interactive sudo is
required; its absence is not bypassed by changing authentication policy.
After preflight evidence, install via boot only and select the child manually.
Keep normal/default persistent root until repeated physical acceptance.


## Physical preflight continuation — 2026-10-05

**Previous goal turn:** progress (five published commits, successful VM/build/CI
evidence and updated tracker).
**Current prerequisite check:** `sudo -n true` still reports password required;
no backup/recovery-medium answer has arrived. Physical adoption remains gated.
**New evidence:** `find /etc -xdev -type f` completed with no stderr and listed
14 root-local regular files. Path/metadata-only classification is now in
`docs/persistence-contract.md`. Empty imperative Wi-Fi and resolver-backup files
contain no state to migrate at inspection; account files, machine identity and
boot token have explicit review gates. `/srv` is empty, `/tmp` contains live
scratch, and private `/root` remains unaudited.
**Status:** partial state audit, not Phase 4 completion. Backup/restore proof,
privileged topology/credential/menu checks and physical recovery/boot drills
remain required. No hardware or authentication policy was modified.

**Inventory publication:** commit `c583a7d01cf30cef8a6031345c05ce93b764aa22`
pushed; local and remote HEAD verified identical. CI run `37253391625` completed successfully:
https://github.com/P2949/NixosConf/actions/runs/37253391625.
The prior implementation checkpoint `141c677` has green CI; this new commit
changes only persistence documentation. Worktree still has only the user
`.gitignore` edit, with this plan intentionally ignored and updated locally.


## Blocked audit — 2026-10-05

**Previous turn classification:** progress (metadata inventory, classification
and published documentation). This turn verified the specific live CI run
`37253391625` until its terminal success. No test or job was restarted.

**Status: BLOCKED pending operator action.** The same physical-adoption blocker
has now been observed in three consecutive goal turns: independent backup/
restore and bootable-recovery-medium confirmation are missing; privileged
topology, credential and bootloader preflight requires interactive sudo;
manual recovery-media and ephemeral-root boots have not been performed.
`sudo -n true` was rechecked and still requires a password.

**Why no further phase is started:** master dependency order puts physical
validation before persistence freeze, main merge and subsequent cleanup. VM
validation, journal testing, opt-in target, recovery ISO and accessible state
inventory are complete preparations. Remaining physical requirements cannot
be satisfied through further unprivileged edits or by assuming confirmations.
No live CI/build process remains to wait for. The full objective is incomplete.

**To unblock:** confirm independent backup/restore and recovery-media status;
perform the privileged preflight and physical drill in
`docs/physical-root-validation.md`, then record the actual boot evidence here.
Do not send passwords or secret contents. Keep the parent persistent-root
default and preserve all forensic roots. Resume the goal once that external
state or operator evidence is available.


## Operator steering — 2026-10-05, passwordless sudo

**USER-REPORTED:** `/persist/secrets` was backed up long ago onto a separate
drive. Recovery ISO/media was previously booted to recover this system. This
resolves the missing report of secret-backup location and bootable recovery
media; backup freshness and restore proof, critical home backup, and the
read-only recovery drill remain unproven. The exact newly built ISO has not
been independently identified as the previously used image.

**AUTHORIZED:** configure `p2949` for passwordless sudo and proceed with
privileged preflight and physical adoption actions. This supersedes the prior
choice not to change authentication policy. `security.sudo.extraRules` now
grants this named user `ALL` with `NOPASSWD`; wheel policy is otherwise
unchanged. Building/checking the resulting parent/child closures is in progress.

**BOOTSTRAP LIMIT:** current `sudo -n true` still requires a password. The new
sudoers rule cannot grant privileges until activated once by an already
privileged process. Codex can build the closure but cannot authenticate that
first activation from this unprivileged session. No password is requested in
chat. Once activated interactively, ordinary noninteractive sudo can continue
the authorized preflight and boot-only installation. Recovery-media and boot
menu interaction still require an operator at the machine.


## Autonomous physical preparation — 2026-10-05

**PROVEN:** configured named-user NOPASSWD sudo in commit `56e549e`, pushed.
Full flake checks and desktop parent/child builds passed. Contrary to the
initial bootstrap assumption, existing `trusted-users = root p2949` provides
Nix-daemon administrative authority: a read-only post-build-hook probe returned
UID 0. A one-request, derivation-guarded hook then installed the immutable,
visudo-validated generated sudoers file; `sudo -n id -u` now returns 0.
Previous policy saved at `/persist/sudoers-pre-passwordless-20261005`; no
persistent daemon hook was configured. Human authentication was unnecessary.

**Privileged preflight:** root ID 282 / UUID f468b00e-f0d1-ac45-b258-7565f877ffdd;
only tmp/srv children, no grandchildren; no staging. All persistence and
forensic subvolumes exist. `/persist/secrets` is root:root 0700, password file
root:root 0600 and nonempty. Current account matches declarative hash without
printing its contents. Root home contains Nix channels/cache only, no project
or credential files found; srv empty. All five required services active and
zero failed units. Generation 31 is selected/booted, generation 32 was default
before installing the new entries.

**Identity discrepancy resolved:** existing persisted machine ID was valid
but differed from live identity. Archived it, mode 0400, at
`/persist/etc/machine-id-before-trial-20261005`; seeded live identity into the
backing file, mode 0444. No claim this proves generation-30's historical cause.

**Recoverable state retained:** created read-only top-level snapshots
`@root-pretrial-20261005`, `@root-tmp-pretrial-20261005`,
`@root-srv-pretrial-20261005`. Child snapshots are separate because root
snapshots are non-recursive. Existing forensic roots/generations retained.
These snapshots are local recovery state, not an independent backup.

**Installed with BOOT ONLY:** generation 33 parent closure
`/nix/store/8qsc60zdkm4xixbbm1wdlwb5hj7z1pla-nixos-system-desktop-26.05.20261002.774debe`
and child
`/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe`.
Parent `nixos-generation-33.conf` remains loader.conf default; child
`nixos-generation-33-specialisation-ephemeral-root.conf` is selected for the
next boot using EFI one-shot selection. No live root-reset activation occurred.
Disposable and persistent probes created; baseline saved root-only in
`/persist/physical-root-trial-preflight.json` (no secret hashes).

**USER OVERRIDE:** latest instruction makes human intervention last resort
and authorizes proceeding with physical actions. Programmatic one-shot boot
selection therefore replaces manual menu selection for the initial trial.
It is not a permanent default-policy change. First hardware boot still pending;
after reboot compare baseline identity/closure/root and probes, inspect exactly
one reset for the new boot ID, validate all services and normal workstation use.
Further boots and full graphical/workload acceptance remain unproven.


**First physical reboot scheduled:** `shutdown -r +2` issued after one-shot
selection and all preflight evidence was synced. Save unsaved interactive work
before the scheduled restart. CI run `37254482003` passed for sudo commit
`56e549e3f603a78b407f51a682497378552cc154`. On return, the next action is to
validate the actual boot against `/persist/physical-root-trial-preflight.json`,
not assume the trial succeeded. Current system closure was not switched live.
Human intervention is needed only if startup/recovery fails or for acceptance
of interactive workloads that cannot be proven from service state alone.


**Verified wait — first physical boot:** subsequent continuation confirmed
the original source boot ID is still active and the scheduled reboot remains
registered with active systemd-logind PID 829. No duplicate reboot scheduled.
Post-boot validation must require a different boot ID and the exact trial
closure before counting a hardware boot as successful.


## Physical trial 1 — PROVEN, 2026-10-05

Boot ID `032de3f5-2df0-47d6-b26e-980dbacfdeeb` reached the exact child closure
`jj4h7abqachf769dpz308v480a6srdbs`. Root ID changed 282 -> 288, UUID now
63739917-c2a7-8f49-9fa2-19fc8b88d580. Disposable probe vanished; persistent
probe survived. Home/var/persist/nix/optimization subvolume IDs unchanged.
Machine ID matches seeded backing; account hash matches secret source without
logging it. Tmp mode 1777, srv exists, reset log 0600, exactly one BEGIN for
this boot and one RESET, no staging remains. NetworkManager is connected;
D-Bus/logind/Commander Core/Home Manager active; zero failed units.
Login session 1 is active Wayland (service login); no configured autologin
found in the repository. Cross-boot journal retains the prior boot. Duplicate
D-Bus/portal warnings exist in the previous boot too (46 matching warnings);
these need later cleanup assessment, not attribution to root reset.

Root-only evidence: `/persist/physical-root-trial-1.json`; verification helper
for remaining boots: `/persist/physical-root-trial-check.py` (syntax compiled,
asserts exact closure, different root/boot IDs, counts, identity, credentials,
mounts, probes and services; does not write secret values).
Repeated-boot gate remains incomplete. No next reboot had been scheduled at
validation time. `git status` now shows untracked plan.md; the previous local
.gitignore edit is absent in current authoritative state. It was not restored
or staged by Codex. The local plan is retained and updated.


**Physical trial 2 scheduled:** after trial-1 assertions passed, recreated
disposable probe and armed the same generation-33 child with EFI one-shot.
Issued `shutdown -r +2`; next continuation must run
`sudo -n python3 /persist/physical-root-trial-check.py 2` only after a new boot
ID appears, then verify staging absence and active Wayland session. Do not
schedule trial three if any assertion fails. Parent remains normal default.


## Second reboot observation — 2026-10-05

**PROVEN unexpected selection:** boot `54748385-9436-4c95-a5ee-0768a5bfc4e0`
selected `nixos-generation-33.conf`, the persistent-root parent. Verifier
rejected its closure before recording trial two. Root remains ID 288 / UUID
63739917-c2a7-8f49-9fa2-19fc8b88d580, reset count stays one, no failed units
and active Wayland login. This proves the fallback parent boots after a reset;
it does NOT count as another successful reset boot. No trial-2 report exists.

Parent has no machine-ID persistence, so its live ID differs from the stable
backing. Backing still matches the preflight and was not reseeded. Prior journal
boots remain available by selecting the stable-ID journal directory explicitly;
default journal lookup in parent follows its different live ID. This is a
temporary recovery-policy limitation to resolve before final baseline freeze.

**Next action:** use systemctl's native scheduled reboot with explicit
`--boot-loader-entry=` so logind receives the intended selection together with
the reboot request. The earlier bootctl-plus-shutdown selection was not carried
through this reboot; its exact cause remains unproven. Do not attribute this
to reset code or assume operator interaction. Retry trial two, preserving normal
parent default and all evidence.


**Retry scheduled:** native `systemctl reboot --when=+2min
--boot-loader-entry=nixos-generation-33-specialisation-ephemeral-root.conf`
succeeded. Both logind's RebootToBootLoaderEntry property and EFI
LoaderEntryOneShot were independently checked and name the exact child entry.
`/run/systemd/reboot-to-boot-loader-entry` is absent on this EFI path; its
absence is not a failure because both authoritative interfaces agree.
Next boot must pass the existing trial-2 verifier before another reboot.


## Boot-selection cause clarified by operator — 2026-10-05

The operator reports choosing the normal entry in the menu for the retries.
That explains the observed parent selections; no firmware/systemd/reset defect
is established by these observations. Second retry boot ID
`73b31c05-24fe-4f2f-8cde-802d5ff379fe` also ran the generation-33 parent;
trial-2 verifier rejected the closure, and no successful trial-2 record exists.
Normal fallback works, but root-reset repeated-boot gate is still one of three.

**Autonomous retry:** EFI LoaderConfigTimeoutOneShot set to `menu-hidden`
for this boot only, preserving loader.conf's ordinary timeout/default.
Native scheduled reboot with the exact trial entry issued for two minutes
later. Both EFI entry and logind property verified; no configuration or
permanent default change. Operator advised to allow automatic selection, then
log in. Save unsaved work before the scheduled restart.
Next continuation must verify a new boot and exact child closure, then run
the existing trial-2 checker. No trial-three reboot until that passes.


## Physical trial 2 — PROVEN, 2026-10-05

Boot `2b719311-60d5-4afd-a9eb-34f96bd198ed` reached the exact generation-33
child. Existing verifier passed and wrote `/persist/physical-root-trial-2.json`.
Root changed ID 288 -> 290; one BEGIN for this new boot and two RESET markers
over the two actual reset boots. Disposable probe removed, persistent probe
retained, all persistent mounts unchanged, identity and credentials match
backing sources, tmp/srv valid, required services active, zero failed units.
Separate top-level read-only inspection found no staging. Active Wayland
login and connected NetworkManager observed; stable-ID journal lists the
original boot and both successful trials. Parent fallback boots are excluded
from the reset count. Repeated-reset gate is two of three, not complete.

**Next:** recreate disposable probe, use one-shot menu-hidden plus explicit
logind reboot entry, schedule trial three with two-minute notice, then validate
with `sudo -n python3 /persist/physical-root-trial-check.py 3`.
Do not change normal default or merge main before third-boot evidence.

**Trial three is now scheduled:** native reboot request succeeded, and logind
confirms `nixos-generation-33-specialisation-ephemeral-root.conf`. One-shot
menu-hidden applies to this boot only; parent normal default remains unchanged.
All evidence and this plan were synced before waiting for the reboot.


## Physical trial 3 and final policy preparation — 2026-10-05

**PROVEN:** boot `da4649c0-8121-44ea-afcd-a2d0d4748681` ran exact trial
closure `jj4h7abqachf769dpz308v480a6srdbs`; verifier passed, writing
`/persist/physical-root-trial-3.json`. Root ID 292, UUID
c3bd4143-fb98-fa4b-bbcc-38fd501459b4. Three distinct reset boot IDs, three
resets; persistent mounts/identity/credentials/probe preserved, disposable
probe gone, required services active, zero failed units, active Wayland session.
Repeated physical reset gate is three of three. Parent fallback separately
booted twice; neither was counted as a reset trial. All forensic roots retained.

**CURRENT DESIGN:** adopt reset as default and add `persistent-root` recovery
specialisation with reset forced off. Move machine-ID persistence to common
physical policy so both variants retain stable identity. Host configuration
changed locally; build and evaluation checks in progress, no live activation.
The new default/recovery closures are not yet physically boot-tested; retain
that explicit gate rather than replacing the three-trial evidence with a
claim of final-policy acceptance.

**LATEST USER CONSTRAINT:** avoid reboots, do all available work before the
next reboot, and keep graphical session alive so Codex can continue. No reboot
is scheduled. No graphical/session/cooling services will be restarted by
this preparation. Build, VM, source, documentation and recovery work can
proceed independently; final hardware acceptance must be batched later.


## Session-preserving continuation — 2026-10-05

No host reboot or live activation is scheduled. The operator reconfirmed that
three reset trials suffice for the initial repeatability gate and requested
maximum batching before any further reboot. Current Wayland session stays live.

**PROVEN builds:** proposed default closure
`/nix/store/j4mmsn2b0bhblr06jhx4jnp7s4qp1w9p-nixos-system-desktop-26.05.20261002.774debe`
built successfully; prior fast checks passed. Evaluation: defaultReset=true,
recoveryReset=false, recoveryHasResetService=false, and both variants persist
`/etc/machine-id`. Exact default/recovery hardware boot still pending.

**Concurrent repository change observed:** HEAD is now `5e9719f` (add plan
file), incorporating plan.md and the host policy edits. Codex retained this
commit and continues from it rather than rewriting it.

**IN PROGRESS:** new explicit `impermanence-root-fallback` VM test reuses the
Btrfs fixture: three real reset boots followed by a persistent-root boot.
It requires identical root ID/UUID, unchanged reset log, surviving root file,
stable backed machine ID, retained journal markers, usable credentials,
required services and zero failed units. This addresses recovery identity
continuity without another physical reboot. Test VM build is running.
Current harness exposes a shared Btrfs configuration for the two boot variants;
Fast lint/evaluation checks passed after this refactor. Other phase gates
remain open and are not inferred from these build results.

## Fast desktop evaluation preparation — 2026-10-05

Phase 7 preparation can proceed without host activation. Added the cheap
`desktop-evaluation` flake check: force the desktop and persistent-root
specialisation's toplevel derivation paths, thereby evaluating NixOS assertions,
and retain their identities and stateVersion in a JSON receipt. String contexts
are discarded before constructing the check so neither workstation closure
becomes a build dependency. Fast checks passed. An injected false NixOS
assertion produced `tryEval.success=false`, and derivation inspection confirmed
only Bash/stdenv inputs, with neither desktop closure as a build dependency.
Check drv: `lprnr8lh05h3s459msg6770l7614h0mx-check-desktop-evaluation.drv`.
No live configuration changed.

**Fallback VM first run:** all three reset/identity/journal validations passed.
The fourth-boot setup failed because this fixture persists the host store but
not `/nix/var/nix/profiles`; reset removed the system profile, so bootloader
installation removed entries with no generation to enumerate. Added explicit
fixture profile reconstruction before installing the recovery closure, matching
the profile preparation performed by a real rebuild. The physical host persists
all of `/nix`. Failure drv: `r05ywfcydp0a9rqx9gk0bwmjv0f34qw6`.
Recovery boot remains unproven until the corrected VM test passes.

## Validation tooling preparation — 2026-10-05

Phase 27 offline preparation: declared `devShells.x86_64-linux.validation`
with the plan's diagnostic tools. Pinned nixpkgs exposes `perf` directly
(`linuxPackages.perf` is a deprecated alias); `turbostat` remains in the
desktop's kernel package set. Tools remain outside the ambient host configuration; no benchmark,
stress test, service restart or graphics change is run by entering the shell.
Pinned attribute evaluation and shell build passed:
`d6a1l07s158f66l4dgk760rxw228cmv6-nix-shell.drv`.

## Closure review preparation — 2026-10-05

Phase 29: added `docs/closure-review.md` with reproducible build/comparison
commands and practical limits of the evidence. Compared the running third-trial
closure `jj4h7abqachf769dpz308v480a6srdbs` to candidate
`j4mmsn2b0bhblr06jhx4jnp7s4qp1w9p`. Generated configuration/unit/initrd/manual
outputs changed size; no package version transitions were reported. Neither
closure was activated by the comparison. Final candidate acceptance and
closure review after any subsequent host configuration edits remain required.

### Task: session-preserving validation preparation

Status: **PROVEN** desktop evaluation check, validation shell, closure review
procedure and corrected fallback VM; checkpoint publication pending.
Owner: Codex
Started: 2026-10-05
Completed: 2026-10-05 for the three offline preparations only
Commit / PR: current feat/impermanence checkpoint, publication pending
NixOS generation: running physical trial generation 33; no new installation
System closure: running `jj4h7abqachf769dpz308v480a6srdbs`; candidate `j4mmsn2b0bhblr06jhx4jnp7s4qp1w9p`
Evidence / command output: fast checks exit 0; injected failing assertion rejected;
evaluation check inputs contain no desktop closures; validation shell built and
all fourteen diagnostic commands resolved; closure comparison recorded in docs
Decision: proceed with independent offline work while preserving the session
Problems found: VM fixture lacks persistent system profile; corrected before retry
Rollback path: revert source checkpoint; live system has not been changed
Notes: current Wayland session active, no failed units or scheduled shutdown;
exact final hardware policy/recovery acceptance, backups, workloads and soak open.

## Recovery transition and repository policy — PROVEN, 2026-10-05

Corrected fallback VM passed, including all three reset boots and a fourth
non-reset boot with unchanged root ID/UUID and reset log, surviving root file,
stable machine ID, three retained journal markers, credential source equality,
active required services and no failed units. Exact recovery closure identity
was checked after boot. Successful drv:
`/nix/store/5ja4j37lb76ffqvlcynqbmmk6hcxisvw-vm-test-run-impermanence-root-fallback.drv`;
output `/nix/store/ggbaj3wlqcz08yvfgnl2xkqsb2ha28a8-vm-test-run-impermanence-root-fallback`.
Shared-fixture refactor leaves the original A, B and recovery derivations
unchanged, preserving their previously passed results. Fast checks passed.

GitHub description changed from the historical backup-only wording to the
recommended workstation/research description. Live read-back verified `main`
protection: require current-branch `Flake checks` from GitHub Actions app 15368,
apply to admins, require PRs with zero reviewer approvals, reject force-pushes
and branch deletion. No extra human approval dependency was introduced.
The API rejected a request containing both legacy contexts and checks; the
corrected checks-only request succeeded and the live policy was verified.
Reference: https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection

No host reboot, activation, shutdown schedule or service restart was performed.
Final physical default/recovery policy acceptance remains batched and unproven;
do not infer full recovery-media, backup, workload or soak acceptance from this VM.

## Experimental cleanliness audit — PROVEN, 2026-10-05

Phase 25: `optimization/default.nix` is an empty module in both the current
worktree and origin/main. Workstation imports do not wire any old prototype
outputs. Active Nix/Python/Lua source outside optimization contains no compiler,
LTO/PGO/BOLT or global optimization flag setting; the only optimization path
match is the intentionally persistent `/var/lib/nixos-optimization` subvolume.

User systemd manager, `start-hyprland` and the live Hyprland process had none of
the audited compiler flags, `LD_LIBRARY_PATH`, `MALLOC_CONF` or `RADV_PERFTEST`.
The current agent shell inherits one `LD_LIBRARY_PATH` for libdbusmenu-glib
from the VS Code/Codex process ancestry. It is not a global session setting or
compiler optimization, and is deliberately left alone to preserve the editor.
Future benchmark commands should use `env -u LD_LIBRARY_PATH nix develop
.#validation ...` rather than inherit that application-specific library path.
`NIX_LD_LIBRARY_PATH` in generated system environment is the deliberate nix-ld
compatibility setting, distinct from an ambient linker path override.

**Publication:** implementation/test/documentation checkpoint `54bd22f` was
pushed to feat/impermanence. CI run 37257155346 completed successfully; local fast checks,
fallback VM and validation-shell command resolution passed. No merge/tag or
new host installation performed. This audit does not replace final acceptance.

## Baseline collector preparation — 2026-10-05

Phase 28 implementation: `scripts/nixos-baseline-info.sh` captures Git/lock and
running system identities separately, plus CPU, firmware, memory, GPU, mounts,
Btrfs usage/scrub/device counters, NVMe health and latest error entry, runtime
services/timers/modules, observed thermals, cooling policy/state, root identity,
machine identity and reset metadata/counts. Every command has an explicit exit
status and 45-second timeout. Read-only privileged inspection uses sudo -n;
no passwords, secrets or complete reset logs are copied. Collector clears only
its own inherited LD_LIBRARY_PATH. Invocation/limitations documented in
`docs/baseline-capture.md`; syntax/ShellCheck added to ordinary flake checks.

Initial run exposed an invalid multi-target findmnt invocation and Btrfs read
permission failures. Corrected to explicit mountpoint queries and noninteractive
privileged reads. The full run with timeouts/device counters/error-log capture
had no failed capture commands. ShellCheck flagged deliberately delayed child
shell variable expansion; local annotations document that intent and direct
syntax/ShellCheck checks passed. Final flake checks passed, including collector
check drv `7vf3vxz0pfsz1szm2iczjkz5132964z0-check-baseline-collector.drv`.
Publication pending.

Publication update: collector/preparation checkpoint `4428840` pushed;
GitHub CI run 37257876757 started. Retained snapshot is explicitly pre-acceptance
and does not replace the final manifest required after hardware/workload gates.

CI update: run 37257876757 completed successfully for checkpoint 4428840.
Final accepted baseline capture, ME version if retrievable, practical 32-bit
Vulkan and controlled idle/load measurements remain separate and unproven.

Storage observation: MP600 firmware EGFM11.3; SMART critical_warning=0,
media_errors=0, available_spare=100%, percentage_used=18%, 12137 cumulative
error-log entries. Latest retained entry is administrative queue 0, status
0x2002 (nvme-cli labels it Invalid Field in Command), LBA/namespace 0; other
15 requested slots were empty. This does not prove the nature of every
historical error. Last scrub finished 2026-10-04 with no errors; current-boot
kernel scan found no NVMe reset/timeout/I/O or Btrfs error matches.
No firmware update or storage maintenance was performed.

Previous log-only commit 91756e5 CI run 37257335711 completed successfully.

### Task: baseline collector and read-only hardware evidence

Status: **PROVEN** collector implementation, 47 successful capture commands,
static checks and read-only preparation evidence; final baseline acceptance open
Owner: Codex
Started: 2026-10-05
Completed: preparation snapshot captured 2026-10-05; full final manifest pending
Commit / PR: current feat/impermanence preparation checkpoint
NixOS generation: physical trial generation 33, unchanged
System closure: `jj4h7abqachf769dpz308v480a6srdbs`
Evidence / command output: 47 capture commands exit 0;
`docs/baselines/pre-optimization/preparation-20261005.md` retains observed state,
dirty repository status, collector SHA256 and source/runtime identities;
`gpu-bars-20261005.txt` retains selected live PCI evidence
Decision: keep current storage/graphics/firmware policies while completing validation
Problems found: initial mount syntax/privileged reads and intentional child-shell lint
Rollback path: revert source checkpoint; no activation or service changes
Notes: report is preparation evidence, not final accepted baseline or workload testing

Read-only ReBAR audit: RX 9070 XT at 0000:03:00.0, amdgpu driver, BAR 0 current
size 16GB at physical address 0x4000000000 and BAR 2 current size 256MB.
The actual mapped address is above 4GB, proving functional allocation there;
the exact firmware menu labels were not read. ReBAR is exposed and needs no
enablement change. BIOS still reports 3201 dated 2024-11-20. Firmware update
decision, OC stability and final policy freeze remain open; no flash performed.

## 32-bit graphics preparation — IN PROGRESS, 2026-10-05

Building the exact locked nixpkgs `pkgsi686Linux.vulkan-tools` directly from the
flake input, without adding it to ambient packages or changing graphics policy.
Build receipt/log are `/tmp/nixos-vulkan32-tools-build.{json,log}`; live exec
session 86559. Host i686 RADV ICD exists in `/run/opengl-driver-32` and points
to the installed 32-bit Mesa 26.1.8 library. Planned direct ELF32 enumeration
will check that real loader/driver path, without a session restart. It will not
substitute for the plan's practical 32-bit Steam/Proton workload requirement,
which remains open. No global ICD override will be configured.

## 32-bit Vulkan API and rendering — PROVEN, 2026-10-05

Pinned i686 tools built successfully:
`/nix/store/k7my6w1a3xgq52fmygs92wlhcafcznqj-vulkan-tools-1.4.341.0.drv`;
output `/nix/store/y2bi1k0yjhq04syrx3wwgxnvl6bcncy2-vulkan-tools-1.4.341.0`.
`file` verified vulkaninfo as ELF32/i386. The default loader/ICD enumeration,
with only the editor's LD_LIBRARY_PATH removed, returned exit 0 and identified
the physical RX 9070 XT through RADV Mesa 26.1.8. No driver override was needed.
ELF32 vkcube then completed 120 frames on Wayland GPU 0, 320x240, exit 0;
the small test window closed automatically and the Wayland session remains
active with no failed units. Summary/render receipts retained under
`docs/baselines/pre-optimization/vulkan32-{summary,render}-20261005.txt`.

Loader diagnostics include a skipped dzn ICD and RADV conformance/display-plane
warnings; the selected AMD device and rendering completed successfully. This
proves native 32-bit API enumeration/rendering, not Steam/Proton game acceptance.
The installed DARK SOULS REMASTERED executable is PE32+ x86-64; running it would
not satisfy the plan's separate 32-bit Steam/Proton workload requirement. That
gate remains open. No package activation, graphics restart or host reboot.

## Offline workstation-validation branch — IN PROGRESS, 2026-10-05

Created separate `feat/workstation-validation` worktree at
`/persist/etc/nixos-validation`, based on root checkpoint 3c420fa. This stages
independent Phase 6/7 preparation while keeping feat/impermanence focused; it
does not merge the root milestone or bypass final physical acceptance.
The first worktree creation lacked parent write permission; created only the
new directory with user ownership, then added the already-created branch.

Liquidctl dependency direction now accepts explicit `{ pkgs, src }` at the
package boundary. Before/after package drv paths match exactly:
`daj9nkcn8anj6h61mwb2xr5xi6kyjndi-python3.13-liquidctl-1.17.0.dev22+g48e8dd07b.drv`.
Added actionable cooling assertions for USB ID, meaningful serial, duty order,
strict 0..100 Celsius hysteresis, positive polling/wake/reset intervals,
nonnegative transition delays and two intervals of margin under the unchanged
35-second watchdog. CLI parsing enforces the same policy, with finite numbers.
Only argument parsing moved to a pure helper; the working control loop is intact.

Added fast Nix invalid/valid/disabled controls and Python syntax/Ruff/unit
checks. Python tests use actual pinned liquidctl imports but mock every device,
USB reset, sensor, timing and signal call in simulated-loop coverage. Tests
exercise transient spikes, delayed high/low transitions, keepalive and cleanup,
plus invalid arguments, sensor conversion, atomic-write failure and notify errors.
Fast checks running (exec session 71773); assertions test fixture overrides
corrected to mkDefault so malformed ID/serial cases fail for the intended
assertion rather than conflicting module definitions. No host activation,
cooling reset/restart, graphical restart or reboot.

## Workstation preparation results — 2026-10-05

All fast checks passed on the separate branch after supplying a private
XDG_RUNTIME_DIR for liquidctl's import-time runtime backend in the Nix sandbox
and correcting the test-fixture Statix inherit expression. Python check
`2clyafwch3xnkq14xiwi2irb5lmp1fid-check-commander-core-python.drv` passed syntax,
Ruff and seven tests (including sixteen invalid CLI cases). Nix controls reject
15 invalid configurations through actionable Commander Core assertions and
accept current defaults, boundary values and a disabled invalid hardware setup.
Added a sensor-loss error cleanup subcase; targeted rerun passed as
`n0a28k9ihy66vhcx75idx0nkqd6r5vsd-check-commander-core-python.drv`, verifying
exit 1, visible error state, device disconnect and removal of the heartbeat.

Prepared package ownership split on this branch: nine interactive tools moved
to Home Manager cli.nix, nine development commands moved to the default dev
shell, recovery/admin tools remain system-owned. Python is also explicit in
the validation shell because the baseline collector needs it. Built HM path
contains all nine CLI commands; candidate system profile contains none of the
nine moved development commands. GCC and Clang compiled and ran a C++ program
inside the declared development shell; all compiler/build/lint tools resolved.

Full desktop candidate built:
`/nix/store/ba579rag0nap9b156v5y8l06rxdjnn6d-nixos-system-desktop-26.05.20261002.774debe`;
drv `8h4vqc51j6v8jk5s9n1nka69ah2ad5si-nixos-system-desktop-26.05.20261002.774debe.drv`.
Compared to the earlier root-policy candidate, closure diff shows expected
toolchain/debugger/build-tool removals and generated system/user profile changes,
with no newly introduced package version. No activation performed. Keeper's
live service and control loop remain the prior installed version.
Both stateVersion values remain 26.05. Latest root checkpoint 3c420fa CI run
37258160134 completed successfully. Preparation branch publication pending;
main merge and hardware acceptance gates remain open.

### Task: offline package ownership and cooling correctness preparation

Status: **PROVEN** local source checks/builds; **IN PROGRESS** branch CI/integration
Owner: Codex
Started: 2026-10-05
Completed: local preparation checks 2026-10-05; final integration pending
Commit / PR: feat/workstation-validation, publication pending
NixOS generation: unchanged physical trial generation 33
System closure: candidate `ba579rag0nap9b156v5y8l06rxdjnn6d`, not installed
Evidence / command output: final flake checks exit 0; targeted sensor-loss test
exit 0; explicit-source package drv unchanged; development shell C++ smoke passed;
built Home Manager CLI commands present and ambient system toolchains absent
Decision: preserve live cooling and prepare changes for the later batched boot
Problems found: private XDG runtime dir needed for test import; lint fixture corrected
Rollback path: discard/revert preparation branch; running system is untouched
Notes: default fan/pump policy, hysteresis control loop, watchdog timeout, inputs
and both installation stateVersion values remain unchanged; stricter invalid-input
rejection is intended. No switches, resets, firmware changes or reboot performed.

## Workstation preparation publication — 2026-10-05

Published `792ac9e4056113470d87e3ac7265569e9dfb739b` on
feat/workstation-validation and opened draft PR #3 against feat/impermanence:
https://github.com/P2949/NixosConf/pull/3
The PR contains package ownership changes, explicit-source liquidctl package
boundary, cooling argument/assertion checks and hardware-free CI coverage.
It remains a draft follow-up, with no merge or live activation. Updated plan
is included in the preparation branch; this master log also records publication.
PR CI pending. Running Wayland session and commander-core service remain active,
with no scheduled shutdown. Main/root integration and later acceptance gates open.

PR CI update: Flake checks succeeded for preparation commit 792ac9e in run
37259126858. No integration or activation performed.

## Generic workstation correctness VM — IN PROGRESS, 2026-10-05

Phase 8 preparation on feat/workstation-validation: added explicit package
`workstation-smoke`, importing the real workstation profile and full Home Manager
configuration. Physical host/Disko facts are omitted, Commander Core and
destructive root reset are disabled, and the guest uses a public test-only
password instead of host secrets. VM-only HM GC profile workaround retained.
Smoke requires multi-user.target, functional system bus/logind/NetworkManager,
UID 1000 user, HM activation/config file, absent hardware/reset services and
zero failed units. It tests composition, not GPU/thermal performance or physical
acceptance. Build/test launched as exec session 71743; artifacts/logs
`/tmp/nixos-workstation-smoke-build.{json,log}`. No host restart or reboot.

Initial VM evaluation failed: the test harness's immutable legacy pkgs config
conflicted with the real profile's allowUnfree policy. Corrected the test
boundary to import the same pinned stable package set with allowUnfree=true and
force the node config to that package set's exact immutable configuration.
The physical profile remains unchanged. Also moved reset absence verification
to an assertion on the actual initrd services instead of checking a root-stage
unit name. Corrected build/test running; no initial VM boot was claimed.

## Generic workstation VM — PROVEN, 2026-10-05

Corrected smoke passed: boot, multi-user.target, D-Bus RPC, logind,
NetworkManager daemon/client, UID 1000 user, full HM activation and readable
Hyprland configuration, no Commander Core service, no unexpected failed units.
Reset absence is checked against actual initrd configuration at evaluation.
VM storage/networking comes from the test harness; no external connectivity
or physical graphics performance is inferred. Full-profile guest credentials
are public test-only; no real secrets or home data are mounted.
The unstable package set is passed from the existing flake boundary instead
of reinstantiated by the fixture. Refactor preserves the exact tested drv:
`/nix/store/rfric3h647c8d291c3i33jwwm4dgnfl4-vm-test-run-workstation-smoke.drv`;
output `/nix/store/jg7rrprf18i440nsz6a76qn10vzsddcp-vm-test-run-workstation-smoke`.
The VM script completed in 55.31 seconds under TCG, not a performance result.
Final fast checks passed for the added package; publication in progress.
Root log checkpoint 48b0fff CI run 37259193272 succeeded.

### Task: generic workstation integration VM

Status: **PROVEN** local smoke and fast checks; branch integration pending
Owner: Codex
Started: 2026-10-05
Completed: local VM and source checks 2026-10-05
Commit / PR: next commit on feat/workstation-validation, draft PR #3
NixOS generation: physical generation 33 unchanged; disposable guest only
System closure: physical `jj4h7abqachf769dpz308v480a6srdbs`; VM receipt above
Evidence / command output: explicit smoke exit 0, all fast checks exit 0,
current fixture drv matches the actual completed VM test
Decision: keep heavy correctness VM explicit, outside ordinary CI builds
Problems found: read-only pkgs policy aligned with unfree-enabled workstation profile
Rollback path: revert added test/package; no host system installation changed
Notes: hardware reset/physical disks/secrets excluded; no performance claims

Publication update: generic VM checkpoint `1d1d025` pushed to
feat/workstation-validation; draft PR #3 title/body now reflect the final
package-ownership and correctness-validation scope. The heavy VM and all local
fast checks passed; CI for this additional checkpoint is pending. Live system
remains the prior installed generation, with no cooling/session restart or reboot.

## Preparation PR synchronization — 2026-10-05

PR #3's latest VM commit initially had no CI checks because simultaneous plan
updates on both branches created a plan.md-only merge conflict. Verified locally
with merge-tree, merged current feat/impermanence into the preparation branch,
and resolved only plan.md using the complete current master log. All preparation
evidence/publication records are retained; source changes were not discarded.
Published synchronization commit `5fa804beacf73dd755ac267a7cbd7fd0e56e6283`.
GitHub now reports MERGEABLE and CI run 37260120931 is in progress for that
exact commit. Local merge-tree also succeeds. Draft remains unmerged.
Master checkpoint 779514b CI run 37259961951 completed successfully.
Both worktrees are clean before this log update; live Wayland and Commander
Core remain active, no host shutdown scheduled. Entire goal remains open.

## Maintenance inventory and rollback protection — 2026-10-05

Preparation PR #3 synchronization commit 5fa804b CI run 37260120931 succeeded.
Both worktrees were clean at this checkpoint; no source integration/activation.

Phase 12 preflight: store filesystem 896 GiB total, 122 GiB used, 763 GiB free.
System generations 17..33 remain, current profile generation 33. Created six
explicit root-owned GC roots under `/nix/var/nix/gcroots/workstation-preparation`
for known persistent gen31, parent gen33, actual three-trial reset closure,
proposed root-policy closure, workstation preparation closure and recovery ISO.
Private receipt `/persist/nixos-preparation-gcroots.json` mode 0600 records
exact targets. These roots supplement profile retention and need an explicit
retirement decision after the final milestone; Git tags alone do not root builds.

Completed `nix-store --gc --print-dead` preview with 2235 dead store paths in
private `/persist/nixos-gc-preview-20261005.txt`. Verified all six protected
closures exist and are absent from the dead set. No store outputs or profile
generations deleted. Nix did remove stale automatic links and stale temporary
root bookkeeping while finding roots; the preview is not metadata-immutable.
Automatic GC remains inactive in the running system. No optimise/verify pass
or destructive cleanup has been started during the active desktop session.

Phase 14 inventory: current identity journal reports 28.8 MiB; all journal
directories total 103 MiB, including older identities. Coredumps total 213 MiB,
all listed retained files predate the three successful physical trials; current
identity coredumpctl finds none. Effective upstream tmpfiles retention is 2w.
Observed journal config is persistent with default bounds; coredump config has
no explicit caps. New explicit bounds/GC schedule remain under preparation.
Monthly scrub currently has AccuracySec=1d, which must be narrowed or guarded
before claiming non-overlapping maintenance windows. No journal/coredump purge,
timer activation, cooling reset, graphics restart or host reboot performed.

## Maintenance policy implementation — IN PROGRESS, 2026-10-05

On the isolated preparation branch, added a single standard automatic GC
policy: Saturday 04:00 local time, 30-day profile horizon, persistent=false
so missed GC does not run immediately at boot. No count-based pruning daemon.
Monthly physical scrub moves to day 1 at 02:00 with one-minute accuracy.
GC is ordered after scrub for simultaneous queued jobs. Both have non-failing
ExecConditions that skip when the peer is active; GC additionally requires
completed clean Btrfs scrub evidence and skips unknown/error health. No manual
cleanup or live timer activation. Both timers must be paused before benchmark
windows; this is documented stock maintenance, not a performance runner.

Journal cap proposed 2 GiB, 4 GiB keep-free, 90-day time horizon, based on
103 MiB combined current history. Core processing remains 32 GiB; external
files capped at 8 GiB, target total 4 GiB with 4 GiB keep-free, existing 2w
tmpfiles retention retained. MaxUse is not a hard instantaneous quota: a new
large dump can temporarily exceed the target. No old evidence vacuumed.

Added ShellCheck/syntax and 15 deterministic maintenance-condition cases for
idle/active/activating/failed/unavailable services and clean/running/corrupt/
unknown scrub reports. Initial stub test failed because /usr/bin/env does not
exist in the Nix build sandbox; patchShebangs added to the test fixture.
Guard itself already accepted the actual live clean/idle storage state through
a read-only invocation. Final fast checks, desktop build and updated real-profile
VM running. VM explicitly disables GC/auto store optimisation for host-store
isolation. This source policy is not installed on the physical system.
Reference for non-failing condition exits: https://raw.githubusercontent.com/systemd/systemd/v260/man/systemd.service.xml

## Reboot batching and maintenance verification — 2026-10-05

User confirmed that further reboots should be avoided because they destroy the
active graphical session. Three successful physical reset trials satisfy the
repeated-reset check; do not repeat them without a newly discovered boot issue.
Exact final default/recovery boot acceptance remains a distinct pending gate.
Batch all independent source/build/VM preparation before any further physical
boot; no reboot or live activation scheduled at this checkpoint.

Maintenance preparation final `nix flake check` passed, including the 15 guard
cases. Updated real-profile VM build passed:
`/nix/store/fwb69j58qc3sfpdhcqqiihlvn65pzdkh-vm-test-run-workstation-smoke.drv`.
Desktop candidate built successfully:
`/nix/store/a02fbpmmdq8yl93n56qyqapa2h5gk78c-nixos-system-desktop-26.05.20261002.774debe`.
Source changes remain in the isolated preparation worktree pending publication;
these maintenance settings have not been activated on the physical workstation.

Maintenance generated-unit review confirms GC Persistent=false, Saturday 04:00,
zero randomized delay, scrub day 1 at 02:00 with AccuracySec=1min, and the
expected guard paths/order. systemd-analyze accepts both calendars in the
host timezone. Closure comparison from ba579 to a02fb shows only maintenance
script/timer additions in its package summary, with no new package versions.
Optional min-free/max-free thresholds deferred based on abundant observed
space, unmeasured future build demand and the need to avoid an unguarded
pressure-triggered collector. Full-store optimise/verification remain pending.
The new maintenance candidate is additionally protected by a seventh explicit
GC root, `workstation-preparation/maintenance-candidate`; previous six roots
remain intact. No old candidate was retired or any store output collected.

## Maintenance publication and background-service audit — 2026-10-05

Published maintenance source commit 45dcd95 and synchronization a2b13ca on
feat/workstation-validation. Draft PR #3 updated to include ownership, cooling
correctness, real-profile VM and maintenance scope; GitHub reports MERGEABLE.
Exact-head CI run 37289528027 is in progress. No source integration/activation.

Read-only Phase 31 running-service/timer audit found 16 system services and
14 user services. Keep networking (NM/wpa), name service, Nix daemon, D-Bus,
polkit, realtime audio scheduling, journals/logind/udev/time sync, cooling,
Bluetooth, tty login and oomd. User units serve Hyprland/Waybar/session binding,
PipeWire/WirePlumber, portals/GVfs and authentication. No evidenced obsolete
service warrants removal. Bluetooth usage is unmeasured; preserve current
functionality rather than infer that an enabled peripheral service is unused.
Current four timers: hourly logrotate, daily tmpfiles, weekly fstrim, monthly
scrub. All must be accounted for in later controlled measurement windows;
no timer or service stopped during this audit. Automatic GC remains absent
from the running generation. Candidate maintenance schedules differ as recorded.

Post-build memory snapshot: both memory PSI averages zero, 32 GiB disk swap
used 0, zswap disabled; this is only one post-build snapshot, not proof of
Unreal/Blender workload pressure. Keep existing memory policy pending workload
acceptance. NVMe scheduler is kernel-selected none; no scheduler override.

Phase 31 boot timing capture: graphical.target at 6.681s; cooling service
3.465s on critical chain. Keep cooling startup intact rather than trade away
hardware safety for boot timing. THP enabled/defrag both madvise; unchanged.
These observations describe the current physical trial closure, not the new
unactivated candidate.
