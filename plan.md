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

### Historical source-of-truth rule

The newer current continuation directive below supersedes this original order.

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

## Current continuation directive — unified readiness guide

**Imported:** 2026-10-05. **Source:** user-supplied attachment
`5df71026-9a8b-4bc3-9b91-5ebc0b6b0c4f/Pasted text.txt` (3,104 logical lines).
**Scope of this update:** organize and incorporate the entire guide into this
plan. Its commands, suggested commits and implementation steps are planned work;
importing them does not mean they were executed or authorize unrelated actions
as part of this documentation-only request.

The complete guide follows, with its section structure nested into this plan.
All source text, examples, paths, hashes, checklists, caveats and final commentary
are retained; heading depth and trailing whitespace are normalized. `:chatgpt-content-reference{...}` markers belong to the supplied
review and are preserved for provenance; their referenced attachments are not
embedded here and these markers are not independently verified citations.

**Precedence and evidence reconciliation:** this newer guide supersedes older
continuation orders and branch references below. Current local worktree/index
still takes precedence over a guide snapshot. The older authoritative-state
section remains a dated local observation, rather than the latest execution
order. In particular:

- The guide supplies previously missing validation for `96c6a3d` and `c15a175`,
  including unchanged accepted desktop closure, byte-identical reset script and
  successful checks/VMs. Retain these as **GUIDE-REPORTED EVIDENCE**, not tests
  newly rerun during this import. The broken local username attempt is separate
  from the validity of those committed refactors.
- The guide reports the recovery filesystem drill as completed read-only;
  preserve its checked status below as **GUIDE-REPORTED EVIDENCE**. Earlier
  missing-receipt observations remain historical. The supplied guide does not
  add an exact drill date/receipt path or resolve every ISO-boot identity detail;
  attach exact-source evidence when reconciling recovery documentation.
- Independent home backup, current encrypted secrets backup and representative
  independent restore remain open. Do not infer them from physical acceptance.
- Facter comparison/adoption is explicitly optional in this newer guide and
  cannot block readiness unless it exposes a real configuration problem.
- No repeat of the historical three-trial program is required for unrelated
  cleanup. Batch necessary final exact-source physical acceptance; preserve the
  user's preference to minimize reboots and graphical-session interruptions.

**Navigation — complete imported guide:**

- [NixOS Pre-Optimization Readiness — Unified Continuation Guide](#nixos-pre-optimization-readiness--unified-continuation-guide)
- [1. Governing conclusion](#1-governing-conclusion)
- [2. Source-of-truth rules from this point forward](#2-source-of-truth-rules-from-this-point-forward)
- [3. Current Git state](#3-current-git-state)
- [4. Proven stable baseline evidence](#4-proven-stable-baseline-evidence)
- [5. Impermanence/root-reset evidence already proven](#5-impermanenceroot-reset-evidence-already-proven)
- [6. Readiness commits completed after physical acceptance](#6-readiness-commits-completed-after-physical-acceptance)
- [7. Other validation infrastructure already completed](#7-other-validation-infrastructure-already-completed)
- [8. Development/workload evidence already collected](#8-developmentworkload-evidence-already-collected)
- [9. Backup/recovery evidence](#9-backuprecovery-evidence)
- [10. Firmware/hardware state](#10-firmwarehardware-state)
- [11. Maintenance/storage evidence](#11-maintenancestorage-evidence)
- [12. Documentation truth drift](#12-documentation-truth-drift)
- [13. CI state](#13-ci-state)
- [14. Unified implementation sequence](#14-unified-implementation-sequence)
- [PHASE A — Restore a valid development head](#phase-a--restore-a-valid-development-head)
- [PHASE B — Establish working CI before more readiness commits](#phase-b--establish-working-ci-before-more-readiness-commits)
- [PHASE C — Fix current-state documentation immediately](#phase-c--fix-current-state-documentation-immediately)
- [PHASE D — Finish storage packaging](#phase-d--finish-storage-packaging)
- [PHASE E — Correct Btrfs maintenance policy ownership](#phase-e--correct-btrfs-maintenance-policy-ownership)
- [PHASE F — Replace the reset-script text-template boundary](#phase-f--replace-the-reset-script-text-template-boundary)
- [PHASE G — Turn `tests/` into a subsystem](#phase-g--turn-tests-into-a-subsystem)
- [PHASE H — Move recovery configuration into `images/`](#phase-h--move-recovery-configuration-into-images)
- [PHASE I — Remove Commander Core policy duplication](#phase-i--remove-commander-core-policy-duplication)
- [PHASE J — Add NixOS-native safety gates](#phase-j--add-nixos-native-safety-gates)
- [PHASE K — Add narrow `system.preSwitchChecks`](#phase-k--add-narrow-systempreswitchchecks)
- [PHASE L — Define stock closure contamination contracts](#phase-l--define-stock-closure-contamination-contracts)
- [PHASE M — Build the blank-disk reconstruction VM](#phase-m--build-the-blank-disk-reconstruction-vm)
- [PHASE N — Complete the independent backup/restore gate](#phase-n--complete-the-independent-backuprestore-gate)
- [PHASE O — Optional isolated NixOS Facter experiment](#phase-o--optional-isolated-nixos-facter-experiment)
- [PHASE P — Physical firmware maintenance window](#phase-p--physical-firmware-maintenance-window)
- [PHASE Q — Hardware and storage stability](#phase-q--hardware-and-storage-stability)
- [PHASE R — Freeze ordinary stock performance policy](#phase-r--freeze-ordinary-stock-performance-policy)
- [PHASE S — Final candidate workload acceptance](#phase-s--final-candidate-workload-acceptance)
- [PHASE T — Clean experimental-control audit](#phase-t--clean-experimental-control-audit)
- [PHASE U — Multi-day stock-system soak](#phase-u--multi-day-stock-system-soak)
- [PHASE V — Final baseline freeze](#phase-v--final-baseline-freeze)
- [PHASE W — Retire temporary preparation state deliberately](#phase-w--retire-temporary-preparation-state-deliberately)
- [PHASE X — Archive `plan.md`](#phase-x--archive-planmd)
- [PHASE Y — Start optimization as a new project](#phase-y--start-optimization-as-a-new-project)
- [15. Features explicitly deferred from the stock baseline](#15-features-explicitly-deferred-from-the-stock-baseline)
- [16. Target repository structure at baseline](#16-target-repository-structure-at-baseline)
- [17. Validation rule for every remaining source change](#17-validation-rule-for-every-remaining-source-change)
- [18. New effective critical path](#18-new-effective-critical-path)
- [19. Hard GO checklist](#19-hard-go-checklist)
- [20. Immediate next action](#20-immediate-next-action)

---

I reviewed all four attached files, the current `feat/pre-optimization-readiness` branch, the live `plan.md`, current source layout, validation/docs, recent commits, and the local terminal evidence. The key result is that the project has crossed from “finish Impermanence/stable-refresh” into **final pre-optimization readiness engineering**. The original plan remains useful for its end-state gates, but its execution order and several status statements are now stale.

The guide below is the consolidated version I would use from here.

### NixOS Pre-Optimization Readiness — Unified Continuation Guide

**Repository:** `P2949/NixosConf`
**Active branch:** `feat/pre-optimization-readiness`
**Authoritative committed head:** `c15a1756fe97ac89d7872326df70b0c758a0bfe0`
**Base:** `main` at `f89205c07e4d3a77900b046a5bf937944488647b`
**Date:** 2026-10-05
**Purpose:** continue and finish `plan.md` from the actual current state, freeze a trustworthy stock NixOS baseline, and only then begin the separate system-optimization project.

---

### 1. Governing conclusion

The workstation architecture itself is now sufficiently organized.

Do **not** restart a broad restructuring of:

- `modules/core`;
- `modules/desktop`;
- `modules/gaming`;
- `profiles/workstation.nix`;
- Home Manager;
- Disko;
- the basic host/profile/module division.

The remaining structural work is concentrated in:

1. the currently incomplete local username cleanup;
2. CI policy;
3. storage feature packaging and the Nix/Bash interface;
4. the test subsystem and flake validation registry;
5. documentation ownership/current-state truth;
6. recovery-image categorization;
7. a few remaining duplicated sources of truth;
8. NixOS-native build/activation safeguards;
9. reconstruction/backup proof;
10. firmware/hardware stability;
11. final workload acceptance;
12. soak and baseline freeze.

This matches the architectural review: host/profile/module boundaries, core, desktop, Home Manager and Disko are already considered good; remaining architecture work belongs primarily to CI, storage, tests, docs and duplicated policy. :chatgpt-content-reference{index="0"}

---

### 2. Source-of-truth rules from this point forward

`plan.md` still contains an early source-of-truth rule referring to `feat/impermanence` as the live implementation line. That is now historical.

Use this order now:

```text
1. Current local worktree/index
2. Current remote feat/pre-optimization-readiness
3. Passing validation from the exact source revision under consideration
4. Physically accepted stable-refresh evidence
5. Current main
6. Historical feat/impermanence evidence
7. Historical architecture/workstation/stable-refresh branches
8. feat/optimization-framework only as a prototype/reference
```

Every future claim should be marked mentally or explicitly as:

```text
PROVEN
CURRENT DESIGN
PLANNED
HYPOTHESIS
HISTORICAL / SUPERSEDED
```

Do not rewrite historical logs to make them appear current. Add newer evidence that supersedes them.

---

### 3. Current Git state

#### 3.1 Remote committed state

Remote readiness HEAD is:

```text
c15a1756fe97ac89d7872326df70b0c758a0bfe0
Extract ephemeral root reset script
```

The readiness branch is exactly three commits ahead of `main` and zero behind:

```text
main
f89205c

  ↓ +3

7295363  Record completed stable-refresh physical acceptance
96c6a3d  Move Btrfs maintenance coordination into storage
c15a175  Extract ephemeral root reset script
```

GitHub's comparison confirms the branch is three commits ahead of `main`, with the readiness work limited to `plan.md`, maintenance ownership, reset extraction, README and corresponding tests.

`main` itself is protected and requires the `Flake checks` status.

#### 3.2 Current local state is ahead of that remote only as an incomplete experiment

The attached terminal evidence shows that after `c15a175`:

1. the existing `workstation-smoke` baseline was successfully captured as:

```text
/nix/store/1anhzd1q0pby5zy8qzyr6lf9spr5a0sb-vm-test-run-workstation-smoke
```

:chatgpt-content-reference{index="3"}

2. the attempted transformation of `tests/workstation-smoke.nix` aborted because it expected a standalone:

```python
machine.wait_for_unit("home-manager-p2949.service")
```

but the actual source contains the service in a Python list. The transformation therefore wrote **nothing** to that test file. :chatgpt-content-reference{index="4"}

3. `flake.nix` **was** changed and staged to pass `username` to `workstation-smoke`. :chatgpt-content-reference{index="5"}

4. because the test file was still unchanged, the local build now fails with:

```text
function 'anonymous lambda' called with unexpected argument 'username'
```

:chatgpt-content-reference{index="6"}

5. `nix flake check` fails for the same reason. :chatgpt-content-reference{index="7"}

6. importantly, the actual desktop derivation still reproduced the exact accepted closure despite this flake-output-only failure:

```text
/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8
```

:chatgpt-content-reference{index="8"}

##### Immediate interpretation

The remote branch is good.

The local worktree is **not currently a valid checkpoint**.

Do not begin another unrelated refactor until this partial username change is either:

- completed correctly and committed; or
- completely restored to `c15a175`.

The preferred path is to **finish it**, because removing this duplicate is still the correct design.

---

### 4. Proven stable baseline evidence

This evidence must remain the anchor for all source-only refactors.

#### 4.1 Accepted stable-refresh source

Frozen accepted source:

```text
c5e036b6e87d9aa77700909b508ccc0c3978d5b2
```

Stable Nixpkgs:

```text
0d9e9b832d03ac387417e16ce1febf73b2e631e1
```

The accepted stable refresh moved from the older `774debe...` pin to `0d9e9b8...`; Home Manager remained on release-26.05 and Disko, Impermanence, unstable and Liquidctl pins stayed fixed.

#### 4.2 Accepted normal system

```text
/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8
```

Kernel:

```text
6.18.55
```

#### 4.3 Accepted persistent-root specialisation

```text
/nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8
```

#### 4.4 Matching recovery ISO

```text
/nix/store/d55ny1z4d53slhz3ilvyy2mg6d8khrqn-nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso/iso/nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso
```

Size:

```text
1496678400 bytes
```

SHA-256:

```text
52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061
```



#### 4.5 Physical acceptance

The final accepted physical sequence was:

```text
normal
  ↓
persistent-root
  ↓
normal
```

The repository's final plan evidence records:

```text
first normal:
    reset root → subvolume 295

persistent-root:
    root remains 295
    no reset-log increment
    root-local probe survives
    persistent probe survives

second normal:
    root 295 replaced by 297
    root-local probe disappears
    persistent probe survives

machine-id:
    stable

services:
    expected services active
    zero failed units
```

The plan explicitly concludes:

```text
physical acceptance gate PASSED
stable-refresh integration gate PASSED
pre-optimization readiness engineering may now begin
```



The more detailed physical records also established separate boot IDs for the two normal boots and the persistent-root boot, while machine identity remained stable. The read-only recovery drill could identify the MP600, mount Btrfs top-level subvolume ID 5 and see the expected root/persistence/forensic subvolumes without modifying the filesystem.

##### Consequence

The old rule:

> do not refactor before stable-refresh physical acceptance

is now superseded.

Refactoring is allowed.

But any **runtime semantic change** must eventually be accepted again before the final baseline tag.

---

### 5. Impermanence/root-reset evidence already proven

Do not rerun this entire historical program after every unrelated source cleanup.

The current root feature already has strong validation.

#### Physical initial viability

Three physical reset trials passed:

| Trial | Boot ID | Fresh root |
|---|---|---:|
| 1 | `032de3f5-2df0-47d6-b26e-980dbacfdeeb` | 288 |
| 2 | `2b719311-60d5-4afd-a9eb-34f96bd198ed` | 290 |
| 3 | `da4649c0-8121-44ea-afcd-a2d0d4748681` | 292 |

They preserved required mounts/state, credentials and machine identity, removed disposable state, kept networking/cooling/Home Manager/D-Bus/logind healthy, and had no failed units.

#### Safety behaviour

The safety suite evolved from 26 refusal cases to **33 refusal cases**, covering:

- unknown children;
- unknown grandchildren;
- malformed/stale staging;
- missing root/staging;
- invalid root paths;
- mounted `/sysroot`;
- missing/invalid persistence;
- log symlinks;
- broken symlinks;
- hard links;
- FIFO/directory log leaves;
- symlink/non-directory log parents;
- names containing misleading ` path ` fragments;
- mutation preservation after refusal.

The config suite expanded to **43 rejected configurations and four accepted controls**.

#### Recovery behaviour

The VM suite proves:

- missing root + valid staging recovery;
- subsequent reset behaviour;
- stable identity;
- persistent journal continuity;
- three reset boots followed by a `persistent-root` boot;
- unchanged root ID/UUID during persistent-root fallback;
- no extra reset-log increment;
- retained credentials/services.



#### Final policy

The accepted model is:

```text
normal/default:
    ephemeral @root reset

persistent-root specialisation:
    reset disabled

/home:
    persistent

/var:
    persistent

/nix:
    persistent

/persist:
    persistent

/var/lib/nixos-optimization:
    persistent

/etc/machine-id:
    persisted in both variants
```

Selective `/home` and `/var` Impermanence remain explicitly deferred.

---

### 6. Readiness commits completed after physical acceptance

#### 6.1 `7295363` — physical acceptance evidence

This records the final accepted closures, recovery artifact and physical sequence into `plan.md`.

No runtime change.

#### 6.2 `96c6a3d` — Btrfs maintenance ownership

Commit:

```text
Move Btrfs maintenance coordination into storage
```

The guard was moved byte-for-byte from:

```text
modules/core/maintenance-guard.sh
```

to:

```text
modules/storage/maintenance-guard.sh
```

The Btrfs scrub + GC coordination was moved into a storage module, while generic:

- GC retention;
- journald retention;
- coredump retention

remained in `modules/core/maintenance.nix`.

Validation performed before commit included:

- guard remained byte-identical;
- behavioral guard test passed;
- evaluated Btrfs scrub policy matched;
- scrub timer remained `AccuracySec=1min`;
- GC ordering remained after `btrfs-scrub--.service`;
- GC/scrub ExecConditions remained equivalent;
- full `nix flake check` passed;
- rebuilt desktop reproduced **exactly** the physically accepted `czk5a2...` closure.

Therefore this was a true structural refactor with no system derivation change.

#### 6.3 `c15a175` — reset-script extraction

The approximately 263-line Bash body was extracted from the Nix module into:

```text
modules/storage/ephemeral-root-reset.sh
```

The service now consumes a rendered script from the separate source. GitHub confirms this exact extraction.

Validation proved:

```text
before rendered script:
    263 lines
    5712 bytes
    SHA256 6c1320260732390e2dba967450d70fdb3a47c19bd298c69312a48fbf224a0a71

after extraction:
    263 lines
    5712 bytes
    same SHA256

cmp:
    identical
```

The desktop again reproduced the exact physically accepted `czk5a2...` closure.

Then:

```text
ephemeral-root-config        PASS
nix flake check              PASS
impermanence-root-safety     PASS
impermanence-root-recovery   PASS
impermanence-root-test-a     PASS
impermanence-root-test-b     PASS
impermanence-root-fallback   PASS
```

The final invariant check confirmed:

- exactly one renderer;
- service consumes the rendered external script;
- old inline script gone;
- seven template tokens map 1:1;
- six generated assignments correct;
- template parses as Bash;
- exactly three intended files staged.

The commit was then pushed successfully. :chatgpt-content-reference{index="17"}

---

### 7. Other validation infrastructure already completed

The repository already includes:

- Flakes;
- Home Manager as a NixOS module;
- Disko;
- Impermanence;
- specialisations;
- systemd-initrd customization;
- typed custom modules;
- negative evaluation tests;
- multi-boot NixOS VM tests;
- recovery ISO;
- stable + unstable package sets;
- diagnostic dev shell;
- custom Commander Core hardware management;
- baseline collector;
- closure-review procedure.

:chatgpt-content-reference{index="18"}

`flake.nix` currently exposes lightweight checks for:

```text
maintenance-guard
commander-core-config
commander-core-python
baseline-collector
desktop-evaluation
ephemeral-root-config
formatting
statix
deadnix
```

and explicit heavier package tests for:

```text
workstation-smoke
impermanence-root-test-a
impermanence-root-safety
impermanence-root-recovery
impermanence-root-test-b
impermanence-root-fallback
recovery-iso
```

The root flake is now the validation registry, which is why `tests/default.nix` is the next logical structural improvement.

---

### 8. Development/workload evidence already collected

These results are useful preparation evidence but **do not replace final-candidate acceptance**.

#### C/C++

The pinned development shell:

- compiled and ran C++20;
- clangd AST/index passed with zero errors when using an exact `--query-driver` matching the trusted Nix compiler wrapper.



#### Unreal Engine

Proven preparation evidence includes:

- actual `AI_Gavin_ProjectEditor` incremental target build;
- Epic Clang 20.1.8;
- Rocky Linux 8 sysroot;
- bundled libc++;
- Steam FHS environment;
- native Wayland SDL3;
- compositor reported `xwayland=false`;
- Vulkan selected RX 9070 XT / RADV GFX1201;
- actual configured startup map loaded;
- 28 actors observed;
- map held approximately ten seconds;
- corrected native shutdown lifecycle exited cleanly under default Mimalloc.

An earlier synchronous automation shutdown produced an ICU/Slate allocator crash, but that was traced to the test harness violating Unreal's deferred shutdown lifecycle. The corrected post-tick/deferred-close probe passed, so no allocator workaround was adopted.

Still open:

- interactive play;
- broad/full rebuild;
- longer session;
- final-candidate acceptance.

#### Blender

Preparation evidence:

- Blender 5.2.2 LTS;
- RX 9070 XT HIP detected;
- factory smoke rendered successfully;
- actual local 33-object Cycles scene loaded;
- actual camera rendered at 1920×1080;
- 64 samples;
- GPU-only HIP;
- CPU disabled;
- approximately 11.83 seconds;
- source remained unchanged;
- no new targeted GPU reset/fault/timeout kernel messages.



Still open:

- sustained render;
- interactive acceptance;
- final-candidate acceptance.

#### GameMode

Preparation evidence:

- registration/reaper behavior works;
- physical governor helper currently lacked authorization because user was not in `gamemode`;
- candidate policy adds conditional group membership;
- real-profile VM proves intended user allowed;
- unrelated `nobody` user denied;
- split-lock mitigation remains enabled.



Final physical governor test remains required.

#### Gamescope/MangoHud

Preparation evidence:

- Gamescope 3.16.23;
- 600-frame Vulkan cube tests;
- native Wayland child passed;
- XCB/XWayland child passed;
- MangoHud 0.8.3 initialized;
- XCB run mapped overlay + shim.

Still open:

- representative game;
- HDR;
- controller;
- final-candidate acceptance.



#### Creative Stage Pro

Proven:

- USB/ALSA device exists;
- direct ALSA transport works;
- current PipeWire default transport works.

Not proven:

- Stage Pro PipeWire profile is currently Off;
- intended Stage Pro sink/routing;
- audible playback through that route;
- reconnect behavior.



#### CPU thermal test

The planned 30-minute sustained test **did not pass**.

The conservative wrapper stopped after roughly five seconds when sampled CPU temperature reached 80 °C.

Positive observations:

- no throttle-counter increase;
- no matching kernel hardware/thermal error;
- Commander Core remained alive;
- fan policy commanded 100%;
- machine cooled back down.

But this remains:

```text
SUSTAINED CPU / OC STABILITY = OPEN
```

Do not increase the temperature boundary merely to manufacture a pass.

#### Android/KVM

User belongs to `kvm`, but:

```text
/dev/kvm absent
VMX outside TXT disabled by BIOS
```

Physical accelerated Android emulator acceptance is blocked on firmware virtualization.

---

### 9. Backup/recovery evidence

#### Verified remote project recovery

`AI_Gavin_Project`:

```text
commit:
376e151fca709b084e182da4c76ccb21a228f86d
```

Proven:

- remote main matches;
- fresh empty LFS store downloaded all **415** tracked LFS objects;
- sizes/hashes matched;
- fresh remote clone restored representative project data correctly.



#### Home inventory

Evidence exists for:

- full top-level home scan;
- approximately 118 GB allocated under Development;
- large Unreal engine install dominates that;
- `.config` ~1.8 GB;
- `.local/share` ~14 GB;
- source/project scan;
- loose Blender files identified.

But an independent broad home backup has **not** been proven.

#### Secrets

Current user authentication deliberately depends on:

```nix
hashedPasswordFile =
  "/persist/secrets/${username}-password-hash";
```

and `/persist/secrets` is therefore part of the reconstruction contract but not Git.

The final baseline still needs either:

```text
external encrypted bootstrap backup
```

or a deliberately adopted encrypted declarative solution.

A secrets framework is **not required** for this baseline if the external model is documented and restore-tested.

---

### 10. Firmware/hardware state

Current known motherboard firmware:

```text
ASUS ROG STRIX Z490-E GAMING
BIOS 3201
embedded date 2024-11-20
```

Observed ME:

```text
14.1.53.1649
14.1.53.1649
14.0.51.1528
```

ASUS currently lists:

```text
BIOS 3402
2026-08-05
```

with ME prerequisite:

```text
14.1.79.2540
```

and an ME update tool published 2026-09-01.

Recorded hashes:

```text
BIOS:
9928bf5a987ff0a44f2efa7bd131186d68a7d1eaeb5198f43ad8333897bc5cf9

ME:
75c5efe983cfb0c4c9e75830b3e1d1287e0e6adcf93d97194acbaaac15746bfe
```

No update decision or flash has been completed.

Virtualization is currently disabled in firmware.

---

### 11. Maintenance/storage evidence

Current intended maintenance policy:

```text
Nix GC:
    Saturday 04:00
    --delete-older-than 30d
    no catch-up at boot

Btrfs scrub:
    day 1, 02:00
    AccuracySec=1min

coordination:
    GC and scrub may not overlap
    GC requires most recent scrub to be finished and clean

journal:
    2 GiB active persistent limit
    4 GiB keep-free
    90-day horizon

coredump:
    32 GiB processing ceiling
    8 GiB external file ceiling
    4 GiB total-use target
    4 GiB keep-free
```



The documentation still claims this policy is awaiting physical installation, but that sentence predates the later accepted stable-refresh closure. The later physical acceptance and exact-closure-preserving `96c6a3d` refactor supersede that status wording.

Still required before final tag:

- current Btrfs scrub status;
- Btrfs device stats;
- NVMe SMART;
- one idle-period store integrity verification;
- optional one-time store optimization if desired;
- deliberate retirement of preparation GC roots only after final milestone.

---

### 12. Documentation truth drift

This is now a genuine project bug.

Current `README.md` still says:

- `feat/impermanence` declares the current root policy;
- final default/recovery hardware acceptance remains pending;
- stable-refresh physical acceptance remains pending.



`docs/stable-refresh.md` still:

- describes the older `bv3...` desktop candidate;
- says physical acceptance remains open.



`docs/impermanence.md` still says exact final physical default/recovery acceptance remains pending.

`docs/maintenance-policy.md` says source policy is pending physical acceptance.

But `plan.md` now records the accepted `czk5...`/`9ppc...` normal → persistent-root → normal sequence as passed.

This must be corrected before more evidence accumulates.

---

### 13. CI state

Current workflow:

```yaml
push:
  branches:
    - main
    - feat/impermanence

pull_request:
```



`feat/impermanence` is merged.

There is currently **no open PR** for `feat/pre-optimization-readiness`.

There is consequently no GitHub workflow/status attached to `c15a175`.

`main`, however, is already protected and requires `Flake checks`.

The appropriate workflow is therefore:

```text
feature branch
   ↓
draft PR
   ↓
PR CI on every update
   ↓
protected main
```

rather than hard-coding each temporary feature branch into `check.yml`.

---

### 14. Unified implementation sequence

The following supersedes older “next action” sections while retaining the original plan's hard final gates.

---

### PHASE A — Restore a valid development head

#### A1. Finish the current username parameterization

Do this **before anything else**.

Current desired source of truth:

```nix
flake.nix:

username = "p2949";
```

The real desktop and Home Manager already consume that value.

`tests/workstation-smoke.nix` must accept the same `username` as an argument rather than redefining:

```nix
let
  username = "p2949";
```

Current test literals that should become derived from `username` include:

```text
home-manager-p2949
id -u p2949
runuser -u p2949
```

The repository path:

```text
../home/p2949
```

should remain literal for now because it is a source-tree path, not runtime identity policy.

##### Required implementation

Change the test function interface to:

```nix
{
  inputs,
  pkgs,
  pkgsUnstable,
  username,
}:
```

Remove its local username definition.

Derive the Home Manager service:

```nix
homeManagerService = "home-manager-${username}";
```

or directly interpolate the same value in the test script.

Parameterize the runtime command strings.

##### Completion gate

Must pass:

```text
tests/workstation-smoke.nix accepts username
flake passes username
no runtime hard-coded p2949 remains
only source path ../home/p2949 remains
```

Then:

```bash
nix build .#workstation-smoke --no-link --print-out-paths
```

Compare against baseline:

```text
/nix/store/1anhzd1q0pby5zy8qzyr6lf9spr5a0sb-vm-test-run-workstation-smoke
```

If identical:

```text
excellent mechanical-equivalence evidence
```

If different:

```text
inspect why;
do not assume failure merely from changed path
```

Then:

```bash
nix flake check --print-build-logs
```

and desktop build must remain:

```text
czk5a2wn8di3pgv8a6w0b8aj3286g3h3
```

Commit separately.

Suggested commit:

```text
Parameterize workstation smoke username
```

No activation.

---

### PHASE B — Establish working CI before more readiness commits

#### B1. Open a draft readiness PR

After Phase A is clean and pushed:

```text
feat/pre-optimization-readiness
        →
main
```

Keep it draft until the full readiness project is complete.

The existing `pull_request:` trigger already gives the branch a CI path.

#### B2. Fix stale push branch policy

Change:

```yaml
push:
  branches:
    - main
    - feat/impermanence
```

to:

```yaml
push:
  branches:
    - main

pull_request:
```

Do not add `feat/pre-optimization-readiness` specifically.

The PR becomes the branch-independent CI mechanism.

##### Gate

- PR workflow runs.
- `Flake checks` passes.
- subsequent pushes update PR CI.
- main remains protected.

Suggested commit:

```text
Use pull requests for feature-branch CI
```

---

### PHASE C — Fix current-state documentation immediately

Do a **status correction**, not a giant historical rewrite.

#### C1. Establish one current status source

Add:

```text
docs/status.md
```

or:

```text
ROADMAP.md
```

I prefer `docs/status.md` while `plan.md` remains active.

It should contain:

```text
current branch
current HEAD
accepted normal closure
accepted persistent-root closure
accepted kernel
accepted recovery ISO/hash
last physically accepted source
current readiness tasks
open hard gates
```

#### C2. Make README timeless

README should describe:

- what the repo is;
- architecture;
- build/check commands;
- where status/evidence live.

Remove fast-changing statements such as:

```text
feat/impermanence currently...
physical acceptance pending...
```

#### C3. Correct stable-refresh evidence

`docs/stable-refresh.md` should preserve the old offline `bv3...` record as historical if useful, but add the actual final accepted result:

```text
source:
c5e036b...

normal:
czk5...

persistent:
9ppc...

kernel:
6.18.55

ISO:
d55...
SHA256:
52e349...

physical:
normal → persistent-root → normal
PASS
```

#### C4. Correct Impermanence status

Preserve the three original opt-in trial records.

Add that the later exact final normal/persistent/normal stable-refresh acceptance has also passed.

#### C5. Correct maintenance-policy status

Remove the claim that its source policy has never been physically accepted.

##### Do not yet archive `plan.md`

It remains the forensic execution ledger until final readiness completion.

---

### PHASE D — Finish storage packaging

Current layout:

```text
modules/storage/
├── btrfs-maintenance.nix
├── maintenance-guard.sh
├── ephemeral-btrfs-root.nix
└── ephemeral-root-reset.sh
```

There are now two obvious implementation pairs.

Target:

```text
modules/storage/
├── btrfs-maintenance/
│   ├── default.nix
│   └── guard.sh
│
└── ephemeral-btrfs-root/
    ├── default.nix
    └── reset.sh
```

This mirrors the successful Commander Core pattern. :chatgpt-content-reference{index="40"}

Do **not** create a `modules/storage/default.nix` which silently imports everything.

The desktop should explicitly choose storage features.

#### D1. Mechanical directory moves first

Commit only path changes and reference updates.

Required gate:

```text
nix fmt
git diff --check
nix flake check
desktop exact closure == czk5...
```

For this commit the exact closure should remain identical.

Suggested commit:

```text
Group storage modules with their helpers
```

---

### PHASE E — Correct Btrfs maintenance policy ownership

The new storage module correctly owns coordination, but it currently also owns:

```nix
services.btrfs.autoScrub = {
  enable = true;
  interval = "*-*-01 02:00:00";
  fileSystems = [ "/" ];
};
```



That is partly physical-host policy.

The better split is:

```text
hosts/desktop/default.nix:
    enable scrub
    scrub filesystem
    schedule

modules/storage/btrfs-maintenance:
    GC/scrub exclusion
    ordering
    guard
    timer coordination mechanism
```

Moving a few policy lines back to the host is not architectural regression.

#### E1. Add assumptions/assertions

The coordination module should fail evaluation if its required counterpart services are not configured.

For example, it should not silently expect:

```text
nix-gc.service
btrfs-scrub--.service
```

to exist through unrelated imports.

##### Gate

The evaluated system must remain exactly equivalent:

```text
scrub enabled
interval unchanged
filesystem /
AccuracySec unchanged
GC ordering unchanged
GC guard unchanged
scrub guard unchanged
desktop closure ideally exact czk5...
```

Suggested commit:

```text
Separate Btrfs maintenance mechanism from host schedule
```

---

### PHASE F — Replace the reset-script text-template boundary

Current reset module performs seven textual substitutions:

```text
@NIX_TOP@
@NIX_ROOT_DEVICE@
@NIX_ROOT_NAME@
@NIX_NEXT_NAME@
@NIX_PERSIST_NAME@
@NIX_LOG_RELATIVE@
@NIX_ALLOWED_DESCENDANT_CHECK@
```

and the final one injects generated Bash code.

This worked and was proven byte-equivalent to the old inline implementation, but it is not the best long-term boundary.

#### F1. Make `reset.sh` ordinary Bash

Nix should provide **data**.

Bash should own **procedural logic**.

Conceptual Nix prefix:

```nix
script = ''
  top=${lib.escapeShellArg topLevelMount}
  root_device=${lib.escapeShellArg rootDevice}
  root_name=${lib.escapeShellArg cfg.rootSubvolume}
  next_name=${lib.escapeShellArg cfg.stagingSubvolume}
  persist_name=${lib.escapeShellArg cfg.persistenceSubvolume}
  log_relative=${lib.escapeShellArg cfg.logFile}

  allowed_descendants=(
    ...
  )

  ${builtins.readFile ./reset.sh}
'';
```

Bash then owns:

```bash
is_allowed_descendant() {
    local candidate=$1
    local allowed

    for allowed in "${allowed_descendants[@]}"; do
        [[ "$candidate" == "$allowed" ]] && return 0
    done

    return 1
}
```

This removes the home-grown template/code-injection mechanism described in the architectural review. :chatgpt-content-reference{index="43"}

#### F2. Independently lint the shell implementation

Add a fast source check:

```bash
bash -n reset.sh
shellcheck -s bash reset.sh
```

Optionally adopt `shfmt --check` later, but don't add a formatter purely for novelty.

#### F3. Validation gate is stronger because generated initrd content changes

Run:

```text
ephemeral-root-config
maintenance checks
full nix flake check
impermanence-root-safety
impermanence-root-recovery
impermanence-root-test-a / renamed equivalent
impermanence-root-test-b / renamed equivalent
impermanence-root-fallback
desktop build
persistent-root build
closure diff
```

This is no longer merely a path move, so do not demand the exact same store path.

Demand the same **observable reset contract**.

Do not immediately reboot the workstation. Batch its final physical acceptance with the later final-candidate hardware window.

Suggested commit:

```text
Use explicit data interface for ephemeral root reset
```

---

### PHASE G — Turn `tests/` into a subsystem

Current `tests/` is flat and now contains several independent domains.

Target:

```text
tests/
├── default.nix
│
├── workstation/
│   ├── evaluation.nix
│   └── smoke.nix
│
├── hardware/
│   └── commander-core/
│       ├── config.nix
│       ├── python.nix
│       └── test_keeper.py
│
└── storage/
    ├── btrfs-maintenance/
    │   └── guard.nix
    │
    └── ephemeral-root/
        ├── harness.nix
        ├── config.nix
        ├── safety.nix
        ├── reset-control.nix
        ├── persistent-identity.nix
        ├── interrupted-recovery.nix
        └── persistent-fallback.nix
```

The current `impermanence-root-a.nix` is effectively a configurable factory, not meaningfully “Test A” anymore. :chatgpt-content-reference{index="44"}

#### G1. Rename scenarios semantically

Prefer:

```text
reset-control
persistent-identity
interrupted-recovery
persistent-fallback
```

over:

```text
A
B
```

You may retain temporary flake aliases for the old names if scripts/docs depend on them.

#### G2. Add `tests/default.nix`

It should return:

```nix
{
  checks = { ... };
  packages = { ... };
}
```

Inputs should be explicit:

```text
inputs
pkgs
pkgsUnstable
username
desktopConfig where genuinely needed
```

#### G3. Thin `flake.nix`

Keep visible:

```text
inputs
system
username
stable + unstable package sets
formatter
dev shells
NixOS configurations
major top-level artifacts
```

Move detailed validation registration out.

Do **not** adopt `flake-parts`.

#### G4. Validation

Because this should be source organization:

```text
all existing check names remain available
all heavy package tests remain available
workstation-smoke equivalent
flake check passes
desktop closure unchanged unless another semantic change is intentionally included
```

Do this as one focused subsystem refactor, not mixed with runtime policy.

---

### PHASE H — Move recovery configuration into `images/`

Current:

```text
hosts/
├── desktop/
└── recovery/
```

But recovery is not a physical host.

Target:

```text
images/
└── recovery.nix
```

Keep:

```nix
nixosConfigurations.recovery
```

if useful for evaluation.

The recovery configuration itself is already well isolated: it imports the minimal installer and deliberately excludes workstation disks, persistence, passwords, cooling and reset behavior.

##### Gate

The resulting ISO should ideally retain the same derivation/output if the content is unchanged.

At minimum:

```text
same packages
same NixOS pin
same stateVersion
no workstation secrets/imports
ISO builds
```

Suggested commit:

```text
Move recovery image out of hosts
```

---

### PHASE I — Remove Commander Core policy duplication

The Nix module already passes every physical/cooling parameter explicitly.

But `keeper.py` independently defaults:

```text
base fan duty
high fan duty
pump duty
high/low temperatures
delays
intervals
USB VID:PID
physical serial
```

including the actual physical serial number.

That means host policy exists twice.

#### I1. Make the Python daemon mechanism-only

For Nix-managed operation, arguments should be required.

Example:

```python
parser.add_argument("--base-fan-duty", type=int, required=True)
parser.add_argument("--usb-id", required=True)
parser.add_argument("--usb-serial", required=True)
```

Keep validation inside Python too; duplicate **validation** is useful defensive programming.

Remove duplicate **policy defaults**.

#### I2. Centralize watchdog duration

Current module uses:

```text
assert interval margin < 35
WatchdogSec = "35s"
```

from two literals.

Define once:

```nix
watchdogSeconds = 35;
```

derive both.

#### I3. Add formatter check

Existing Python validation already includes syntax, Ruff and hardware-free tests.

Add:

```bash
ruff format --check
```

#### I4. Do not generalize `coretemp`

There is one real consumer.

Leave it concrete.

##### Gate

```text
commander-core-config PASS
commander-core-python PASS
hardware-free tests PASS
workstation-smoke PASS
desktop builds
```

The service must later receive final physical cooling acceptance because the keeper source itself changes the system closure.

---

### PHASE J — Add NixOS-native safety gates

This is one of the most valuable remaining readiness tasks.

The repository already has:

```text
source/repository checks
heavy VM correctness tests
physical validation
```

Add two intermediate layers.

#### J1. `system.checks`

Use these for cheap checks that should be dependencies of building the NixOS system itself.

Good candidates:

```text
reset.sh bash syntax
reset.sh ShellCheck
maintenance guard syntax/ShellCheck
critical custom-module pure/unit checks
possibly Commander Core pure Python checks
```

Do **not** include:

```text
formatting
Statix
Deadnix
multi-reboot VMs
full workstation VM
```

Conceptual architecture:

```text
nix flake check
    repository/source health

system.checks
    critical configuration cannot build unless invariant checks pass

system.preSwitchChecks
    built system cannot activate unless current physical machine state is safe
```

The value of this layering is explicitly identified in the NixOS-feature review. :chatgpt-content-reference{index="48"}

---

### PHASE K — Add narrow `system.preSwitchChecks`

Only check conditions where activation itself could make the machine unusable.

Good candidates:

```text
/persist is mounted correctly
password hash source exists and is readable by root
/boot exists and has a measured minimum free-space reserve
physical Btrfs root device/topology matches expectations
no unsafe @root-next transitional state exists
```

Do **not** gate activation on:

```text
Commander Core USB currently attached
monitor present
Creative Stage Pro present
internet connectivity
Bluetooth peripheral connected
Steam available
user graphical session
```

Those are runtime/peripheral conditions, not activation invariants.

##### Test requirements

For every pre-switch check, create:

```text
positive test
negative test
clear failure message
```

Test `switch`, `boot` and other action semantics where relevant.

Never introduce a gate you cannot recover from using the persistent-root/recovery paths.

---

### PHASE L — Define stock closure contamination contracts

Before optimization begins, add a convention and enforcement mechanism for experimental outputs.

Use deliberately recognizable output naming, for example:

```text
nixos-opt-cpu-
nixos-opt-lto-
nixos-opt-pgo-
nixos-opt-bolt-
```

Then use:

```nix
system.forbiddenDependenciesRegexes
```

on the stock/control system.

The goal is:

```text
stock system
    must contain no optimization outputs

CPU-codegen stage
    may contain CPU outputs
    must not contain PGO/BOLT

PGO stage
    may contain PGO
    must not silently contain BOLT

etc.
```

This transforms closure purity into an experimental invariant rather than a documentation promise. It is one of the strongest NixOS-specific mechanisms identified for this project. :chatgpt-content-reference{index="49"}

##### Important

Do not use vague patterns such as:

```text
experimental
```

which may match unrelated packages.

Use a project-owned naming namespace.

Add a negative test proving a deliberately injected forbidden derivation makes the system build fail.

---

### PHASE M — Build the blank-disk reconstruction VM

This is a hard pre-optimization reproducibility gate.

The intended test is:

```text
empty virtual disk
    ↓
boot recovery/installer environment
    ↓
Disko
    ↓
GPT
ESP
swap
Btrfs
subvolumes
    ↓
inject test-only bootstrap secret
    ↓
install pinned workstation configuration
    ↓
install systemd-boot
    ↓
power off
    ↓
boot from installed virtual disk
    ↓
normal ephemeral-root reset occurs
    ↓
persistent state survives
    ↓
workstation services reach expected state
    ↓
reboot persistent-root variant
    ↓
root retained / no reset
```

This should prove:

```text
repository
+
required external bootstrap state contract
=
reconstructable workstation
```

The feature review ranks this as one of the highest-value remaining gates. :chatgpt-content-reference{index="50"}

#### M1. Never use the real password secret

Supply a test-only secret through the **same path contract**:

```text
/persist/secrets/<username>-password-hash
```

#### M2. Prove both variants

After the default boot:

- root reset;
- persistent mounts;
- machine ID;
- credential;
- services.

After persistent-root boot:

- root identity unchanged;
- reset count unchanged;
- persistent root-local sentinel survives.

#### M3. Treat this as a heavy explicit package/test

Do not put it into ordinary PR `nix flake check`.

---

### PHASE N — Complete the independent backup/restore gate

This must happen before firmware flashing and before final baseline freeze.

Current remote/LFS project restore proof is good but insufficient.

Required:

1. independent storage outside the MP600;
2. selected critical home data;
3. loose Blender projects;
4. Unreal ignored/autosave state judged deliberately;
5. local repositories/untracked work;
6. `/persist/secrets` encrypted backup;
7. backup date and destination;
8. integrity verification;
9. representative restore to a **separate** directory;
10. hash/content comparison.

The existing Ventoy recovery USB is not the broad backup target.

Do not destroy or repurpose it.

#### Secret model decision

Choose one:

##### Model A — external bootstrap secret

```text
repo
+
external encrypted secret backup
```

Document restoration.

##### Model B — encrypted declarative secret

sops-nix/agenix style.

This is optional for the pre-optimization baseline.

Model A is sufficient if actually tested.

---

### PHASE O — Optional isolated NixOS Facter experiment

Do this only after the source organization is stable.

Generate a Facter report and compare with the existing explicit hardware configuration.

Goal:

```text
current generated/explicit hardware config
            vs
Facter-derived hardware config
```

Use comparison tooling.

Do **not** adopt Facter merely because it is newer.

Adopt it only if it:

- preserves required configuration;
- makes hardware provenance clearer;
- does not hide important host-specific details.

Otherwise keep `hardware-configuration.nix`.

This is optional and cannot block the baseline unless it exposes a real configuration problem.

---

### PHASE P — Physical firmware maintenance window

Batch reboot-dependent work.

#### P1. Capture current firmware/OC settings first

Record:

```text
BIOS
ME
CPU ratio
cache ratio
core voltage
LLC
AVX offset
power limits
memory frequency
memory timings
ReBAR
Above 4G
VT-x/VMX
Speed Shift/HWP
```

Photographs/screenshots are acceptable for firmware settings.

#### P2. Decide BIOS/ME update

Either:

```text
A. retain 3201 deliberately
```

or:

```text
B. update ME 14.1.79.2540
   then BIOS 3402
```

Do not update simply because a newer version exists.

If updating, verify package hashes against the already recorded values.

#### P3. Enable virtualization

Physical Android/KVM gate requires:

```text
VMX enabled
/dev/kvm exists
user kvm membership works
```

#### P4. Freeze firmware

Once selected:

```text
no firmware changes during optimization campaign
```

Any later firmware/microcode change creates a new performance baseline.

---

### PHASE Q — Hardware and storage stability

Run after the final firmware decision.

#### Q1. NVMe

Record:

```bash
nvme smart-log
```

Require:

```text
no critical warning
no unexplained media/data errors
reasonable percentage used
temperatures acceptable
error log understood
```

#### Q2. Btrfs

Require:

```text
scrub finished
Error summary: no errors found
device stats zero/understood
filesystem usage recorded
```

#### Q3. Nix store

During idle period:

```bash
sudo nix-store --verify --check-contents
```

Repair/rebuild any corrupt paths.

Optional one-time:

```bash
sudo nix-store --optimise
```

Do not run this during performance measurements.

#### Q4. Cooling

Test:

```text
cold boot
warm reboot
service restart
USB reset/recovery
sustained CPU load
watchdog behavior
```

#### Q5. CPU OC

The existing five-second 80 °C stop is **not** an OC pass.

Resolve:

```text
voltage
power
cooling
or clock
```

rather than weakening the safety boundary.

Then run:

- sustained all-core;
- mixed FP/integer;
- large Nix/compiler builds;
- hardware error inspection.

#### Q6. RAM

Run a dedicated broad memory validation.

Require zero errors.

Any BIOS update requires CPU/RAM revalidation.

---

### PHASE R — Freeze ordinary stock performance policy

Do not add speculative tuning.

#### Keep/reconfirm

```text
security mitigations enabled
SMT enabled
normal C-states
normal scheduler
sandboxed Nix
Btrfs zstd:1
noatime
discard=async
kernel-selected NVMe scheduler
THP default/madvise policy
```

#### Measure/decide

##### CPU frequency policy

Current observed baseline:

```text
intel_pstate
powersave
balance_performance EPP
```

Compare only if evidence suggests a problem.

##### ZRAM

Current:

```text
32 GiB RAM
32 GiB disk swap
zram off
```

Existing post-build snapshot showed zero swap pressure.

Do not add zram without workload evidence.

##### irqbalance

Measure real interrupt distribution.

Do not enable or disable based on folklore.

##### THP

Current recorded state:

```text
madvise
```

Leave it unless a real workload demonstrates a defect.

##### GPU

Keep stock stable RADV/Mesa.

No:

```text
global RADV_PERFTEST
global power-profile forcing
global clocks
```

---

### PHASE S — Final candidate workload acceptance

Run these on the **exact final candidate that is intended to become the baseline**.

Earlier preparation results remain evidence, but are not substitutes.

#### S1. Desktop/session

- graphical login;
- Hyprland/UWSM;
- portals;
- Firefox;
- persistence across reboot;
- zero failed units.

#### S2. C/C++

- development shell;
- GCC;
- Clang;
- clangd;
- representative build;
- no global flags contamination.

#### S3. Unreal

Require:

```text
official 5.8.2 path
actual project
broad/full C++ build
native Wayland
RADV RX 9070 XT
configured startup map
interactive editor
PIE/play
clean ordinary shutdown
longer working session
```

Do not add `-ansimalloc` unless a genuine ordinary workload defect later requires it.

#### S4. Blender

Require:

```text
actual project
HIP RX 9070 XT
interactive use
longer representative render
no GPU reset/fault
```

#### S5. Android Studio

After VMX enablement:

```text
/dev/kvm
Java project
AVD boot
normal emulator interaction
persistent AVD state
```

#### S6. Gaming

Require representative:

```text
native Vulkan game
Proton game
GameMode helper actually changes requested policy
MangoHud
Gamescope
controller
audio
HDR if part of normal workflow
```

Confirm GameMode returns CPU policy after exit and retains split-lock mitigation.

#### S7. Audio

Specifically complete the currently missing Stage Pro gate:

```text
PipeWire profile enabled intentionally
Stage Pro sink selected
audible playback
reconnect after reboot/replug
normal default-route policy
```

#### S8. Networking/Bluetooth

- expected Ethernet/Wi-Fi;
- NetworkManager profiles;
- Bluetooth if used;
- reconnect after reboot.

---

### PHASE T — Clean experimental-control audit

Immediately before soak/freeze:

#### Environment

No global:

```text
CFLAGS
CXXFLAGS
CPPFLAGS
LDFLAGS
RUSTFLAGS
NIX_CFLAGS_COMPILE
NIX_LDFLAGS
LD_LIBRARY_PATH
MALLOC_CONF
```

unless explicitly justified for the stock system.

#### Repository

Search outside `optimization/` for:

```text
-march=
-mtune=
-flto
-fprofile
llvm-bolt
BOLT
PGO
```

Any hit must be explained.

#### Optimization module

Must remain inert.

The old optimization branch:

```text
397a8c71cd7acb0bc016983f28866df16c95d7d8
```

remains a reference only.

Never merge it wholesale.

---

### PHASE U — Multi-day stock-system soak

After the final candidate is installed and all one-time maintenance/hardware work is complete:

Use the workstation normally for several days.

Include:

```text
multiple cold boots
multiple warm reboots
Unreal work
Blender render
gaming
large C/C++ build
large Nix build
Android emulator
normal browser/audio/network
suspend/resume if used
```

Require:

```text
no unexplained freeze
no GPU reset
no filesystem errors
no recurring failed unit
no cooling failure
no persistence/login issue
no root-reset anomaly
no uncontrolled disk/store growth
```

Do not silently work around failures.

Record and fix them declaratively, then restart the relevant portion of acceptance.

---

### PHASE V — Final baseline freeze

Only after the soak passes.

#### V1. Repository clean

```text
main candidate source committed
no unstaged files
no staged leftovers
no untracked configuration hotfixes
```

#### V2. Fast checks

```bash
nix flake check --print-build-logs
```

#### V3. Heavy checks

Run all explicit storage/workstation/reconstruction tests.

By then the descriptive names should replace A/B terminology.

At minimum:

```text
ephemeral config/safety
reset control
persistent identity
interrupted recovery
persistent fallback
workstation smoke
blank-disk reconstruction
```

#### V4. Build exact normal and persistent closures

Record both.

#### V5. Closure review

Compare with last accepted baseline and explain every material change.

#### V6. Activation preview

```bash
nixos-rebuild dry-activate
```

Then use the appropriate `test`/`boot` flow.

Because initrd/root-reset/safety checks will have changed during this readiness work, perform one final physical acceptance sequence on the exact final source.

Recommended:

```text
normal
→
persistent-root
→
normal
```

This does not need the historical three-trial repetition unless the reset semantics materially changed in a way not covered by the VM matrix.

#### V7. Final runtime manifest

Record:

```text
Git commit
flake.lock hash
Nixpkgs revision
NixOS version
Nix version
normal closure
persistent closure
kernel
Mesa
microcode
BIOS
ME
CPU ratio/cache/voltage/power
RAM config
GPU
NVMe + firmware
Btrfs mount options
scrub status
CPU governor/EPP
THP
swap/zram
scheduler
irqbalance
maintenance timers
Commander Core policy
machine-id
failed units
```

#### V8. Documentation

Before merge:

```text
README timeless/current
docs/status.md says all hard gates
validation evidence tied to exact commit/closure
recovery instructions current
backup contract current
firmware/hardware manifest current
```

#### V9. Merge readiness PR

Move the tested readiness HEAD into protected `main`.

Require green `Flake checks`.

Build/confirm the merged commit if merge mechanics changed tree identity.

#### V10. Tag

Create:

```text
nixos-26.05-pre-optimization-baseline
```

as an annotated tag.

Record tag + closures under:

```text
docs/baselines/
```

---

### PHASE W — Retire temporary preparation state deliberately

Only after the baseline tag exists and recovery is proven.

Review:

- temporary GC roots;
- old stable-refresh candidate roots;
- old recovery ISO roots;
- forensic Btrfs roots;
- pretrial snapshots;
- obsolete generations.

Do not bulk-delete merely because the project is “finished.”

For every retained artifact decide:

```text
required rollback
forensic evidence
historical curiosity
safe to remove
```

Run a fresh GC preview before destructive cleanup.

---

### PHASE X — Archive `plan.md`

Only now should the giant execution ledger leave the repository root.

Move it to something like:

```text
docs/history/pre-optimization-readiness-2026-10-05.md
```

The exact filename date can reflect the actual completion date instead.

Keep a short root/current document:

```text
ROADMAP.md
```

or:

```text
docs/status.md
```

The final root should answer:

```text
What is this repo?
How do I build/check it?
What is the accepted stock baseline?
What is currently being researched?
```

not require reading thousands of lines of migration history.

---

### PHASE Y — Start optimization as a new project

From:

```text
tag:
nixos-26.05-pre-optimization-baseline
```

create:

```text
feat/optimization-framework-v2
```

Do not continue the readiness branch for optimization work.

The historical branch:

```text
feat/optimization-framework
397a8c7...
```

is donor/reference code only.

The new project can then introduce staged experimental identities:

```text
stock
  ↓
CPU-specific codegen
  ↓
conservative compiler tuning
  ↓
LTO
  ↓
PGO
  ↓
BOLT
  ↓
validated combinations
```

The contamination rules created before the baseline then become part of the experimental framework.

---

### 15. Features explicitly deferred from the stock baseline

These are interesting but should not block readiness.

#### `system.replaceDependencies`

Very useful later as an **experimental research path** to compare dependency grafting with conventional downstream rebuild propagation.

Do not make it the default PGO/BOLT architecture. :chatgpt-content-reference{index="52"}

#### Distributed builds

Useful once large LTO/PGO rebuilds dominate build time.

Not a pre-baseline requirement. :chatgpt-content-reference{index="53"}

#### `system.includeBuildDependencies`

Interesting recovery/reproducibility experiment.

Far too large for normal workstation policy.

Defer. :chatgpt-content-reference{index="54"}

#### Generated module documentation

`nixosOptionsDoc` would be useful later for:

```text
boot.ephemeralBtrfsRoot.*
hardware.commanderCore.*
```

but it is documentation polish rather than a baseline hard gate. :chatgpt-content-reference{index="55"}

#### Selective home/var Impermanence

Explicitly deferred.

#### flake-parts / flake-utils / host framework / giant lib

Do not add.

#### Additional performance knobs

Do not introduce:

```text
mitigations=off
isolcpus
nohz_full
rcu_nocbs
forced THP
random VM sysctls
global LD_LIBRARY_PATH
global compiler flags
Cachy/Zen kernel merely for benchmark gains
fixed clocks as ordinary desktop policy
global AMDGPU/RADV hacks
```

Those belong either nowhere or in explicit later experiments.

---

### 16. Target repository structure at baseline

A sensible final form is:

```text
NixosConf/
├── flake.nix
├── flake.lock
├── README.md
├── ROADMAP.md / docs/status.md
│
├── hosts/
│   └── desktop/
│       ├── default.nix
│       ├── hardware-configuration.nix
│       ├── disko.nix
│       ├── persistence.nix
│       └── ephemeral-root.nix
│
├── images/
│   └── recovery.nix
│
├── profiles/
│   └── workstation.nix
│
├── modules/
│   ├── core/
│   ├── desktop/
│   ├── gaming/
│   ├── compatibility/
│   ├── hardware/
│   │   └── commander-core/
│   │       ├── default.nix
│   │       └── keeper.py
│   └── storage/
│       ├── btrfs-maintenance/
│       │   ├── default.nix
│       │   └── guard.sh
│       └── ephemeral-btrfs-root/
│           ├── default.nix
│           └── reset.sh
│
├── home/
│   └── p2949/
│
├── packages/
│   └── liquidctl-pr886.nix
│
├── tests/
│   ├── default.nix
│   ├── workstation/
│   ├── hardware/
│   │   └── commander-core/
│   └── storage/
│       ├── btrfs-maintenance/
│       └── ephemeral-root/
│
├── scripts/
│   └── nixos-baseline-info.sh
│
├── docs/
│   ├── status.md
│   ├── design/
│   ├── runbooks/
│   ├── validation/
│   ├── baselines/
│   └── history/
│
└── optimization/
    └── default.nix
```

Going materially further than this for a one-host repository is likely to reduce maintainability.

---

### 17. Validation rule for every remaining source change

Use the smallest gate appropriate to the risk.

#### Pure path/organization refactor

Examples:

```text
move module directory
move test file
move recovery image file
tests/default.nix registry
```

Require:

```text
nix fmt
git diff --check
nix flake check
relevant unit/check
desktop closure comparison
```

Exact closure identity is highly desirable.

#### Workstation/profile policy refactor

Examples:

```text
username plumbing
Commander Core argument ownership
```

Require:

```text
flake check
workstation-smoke
desktop build
relevant module/unit tests
closure diff
```

No physical activation simply for organization.

#### Root/initrd/destructive-storage semantics

Examples:

```text
reset shell logic
preSwitch topology checks
root module assertions
```

Require:

```text
config negative/positive matrix
safety VM
recovery VM
reset-control VM
identity VM
persistent-fallback VM
desktop + persistent builds
closure review
```

Batch physical acceptance for the final candidate.

#### Firmware/runtime policy

Require actual physical testing.

VMs cannot prove:

```text
OC stability
thermals
KVM firmware
GPU stability
audio routing
real gameplay
USB cooling hardware
```

---

### 18. New effective critical path

From the actual current state:

```text
LOCAL BROKEN USERNAME ATTEMPT
        │
        ▼
finish workstation-smoke parameterization
        │
        ▼
open draft PR + repair CI policy
        │
        ▼
correct current-status documentation
        │
        ▼
finish storage packaging
        │
        ├── host vs mechanism split
        └── explicit Nix → Bash data interface
        │
        ▼
tests/default.nix + semantic test layout
        │
        ▼
recovery → images/
        │
        ▼
Commander Core source-of-truth cleanup
        │
        ▼
system.checks
        │
        ▼
system.preSwitchChecks
        │
        ▼
stock forbidden-dependency contracts
        │
        ▼
blank-disk reconstruction VM
        │
        ▼
independent backup + restore proof
        │
        ▼
firmware/VMX decision
        │
        ▼
OC / RAM / cooling / NVMe / Btrfs / store validation
        │
        ▼
freeze normal CPU/memory/I/O policy
        │
        ▼
final exact-candidate workload acceptance
        │
        ▼
multi-day soak
        │
        ▼
full final validation + normal/persistent/normal physical acceptance
        │
        ▼
merge to protected main
        │
        ▼
nixos-26.05-pre-optimization-baseline
        │
        ▼
archive plan.md
        │
        ▼
fresh optimization-framework-v2
```

---

### 19. Hard GO checklist

Optimization remains forbidden until all of these are true.

#### Repository

- [ ] current local username work repaired/committed
- [ ] readiness PR open and CI green
- [ ] source tree final
- [ ] tests organized
- [ ] docs have one current source of truth
- [ ] main receives final readiness merge
- [ ] `flake.lock` frozen
- [ ] final annotated tag exists

#### Storage / Impermanence

- [x] root reset safety matrix proven
- [x] interrupted recovery proven
- [x] machine-ID persistence proven
- [x] persistent-root fallback proven
- [x] physical ephemeral-root repeatability proven
- [x] stable-refresh normal/persistent/normal acceptance proven
- [ ] post-refactor final reset VM suite green
- [ ] final exact-source physical normal/persistent/normal acceptance green
- [ ] blank-disk reconstruction passes

#### Recovery / backup

- [x] recovery ISO reproducibly built
- [x] matching artifact hash known
- [x] recovery filesystem drill performed read-only
- [x] important project remote/LFS restore proven
- [ ] independent home-data backup current
- [ ] encrypted secret backup current
- [ ] representative independent restore proven
- [ ] recovery documentation corrected/current

#### Hardware

- [ ] BIOS/ME decision frozen
- [ ] VMX enabled and KVM physically accepted
- [ ] OC sustained stable
- [ ] RAM error-free
- [ ] Commander Core sustained-load behavior accepted
- [ ] NVMe SMART accepted
- [ ] Btrfs scrub/device health accepted
- [ ] Nix store verified

#### Stock policy

- [ ] CPU governor/EPP frozen
- [ ] zram decision frozen
- [ ] IRQ policy frozen
- [ ] THP documented/frozen
- [ ] NVMe scheduler recorded
- [ ] maintenance timers recorded
- [ ] no accidental performance flags/hacks

#### Workloads

- [ ] C/C++ final candidate accepted
- [ ] Unreal full workflow accepted
- [ ] Blender sustained final candidate accepted
- [ ] Android/KVM accepted
- [ ] Steam/Proton accepted
- [ ] Gamescope/MangoHud/GameMode accepted
- [ ] controller accepted
- [ ] HDR accepted if part of normal workflow
- [ ] Creative Stage Pro PipeWire route/reconnect accepted
- [ ] network/Bluetooth/session accepted

#### Stability

- [ ] multi-day normal-use soak complete
- [ ] no recurring failed units
- [ ] no GPU resets
- [ ] no filesystem errors
- [ ] no thermal/cooling faults
- [ ] no root/persistence regressions

#### Experimental integrity

- [ ] stock closure contamination policy exists
- [ ] optimization module remains inert
- [ ] no global compiler/linker tuning
- [ ] final manifest committed
- [ ] normal + persistent closure paths recorded

Only then:

```text
GO FOR OPTIMIZATION
```

---

### 20. Immediate next action

Do **not** start the test-registry or storage-directory work from the current local state.

First fix the half-completed username change.

The exact starting condition is:

```text
remote:
    c15a175
    valid

local:
    flake.nix staged with username argument
    workstation-smoke still old
    workstation-smoke build fails
    nix flake check fails
    desktop closure remains accepted
```

Finish that one atomic change and return to:

```text
clean worktree
flake check PASS
workstation-smoke PASS
desktop == accepted closure
```

Then push it, open the draft readiness PR, and use that PR as the live implementation surface for everything above.

That is the correct continuation point for `plan.md`.

The most important change in this unified version is that it separates three things that had become mixed together: **historical proof**, **current source cleanup**, and **future hard gates**. The Impermanence/stable-refresh work is no longer the blocker; the current critical path starts with repairing the half-finished username refactor, establishing working PR CI, then completing one final source-organization/safety pass before the physical hardware/workload phase.

I would use this guide as a new “current continuation directive” near the top of `plan.md`, while leaving the existing historical execution ledger intact until the final baseline is tagged.

---

## Current authoritative state — reconciled 2026-10-05

This section supersedes conflicting present-tense statements below. Historical
records remain intact. The final pre-optimization baseline is **IN PROGRESS**.

### Live workstation — verified during this update

- [x] Running closure, booted closure and system profile all resolve to
  `/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Profile: `system-35-link`; kernel: `6.18.55`.
- [x] Boot ID: `1299a2b6-c50b-4e83-8437-aa7e705914d6`.
  Root subvolume **297**, UUID `f10d446f-0ed8-4a4d-bfc0-cb1c0932fa56`,
  created 2026-10-05 13:49:16 Europe/Dublin. Persistent reset log records
  `RESET complete` for that creation at 12:49:16 UTC.
- [x] Normal root is ephemeral; matching persistent-root recovery closure:
  `/nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Home/var remain persistent; selective home/var Impermanence is **DEFERRED**.
- [x] Zero failed systemd units. NetworkManager, D-Bus, systemd-logind,
  commander-core and home-manager-p2949 active. Session 1 active, Wayland.
  `sudo -n true` succeeds. No secret contents were printed or changed.
- MP600 persistent mounts, ESP and swap remain present; Ventoy USB is attached
  and unmounted. No independent backup disk is currently attached.
- No reboot, activation, graphical/cooling restart, GC, scrub or firmware change
  was performed for this documentation update.

### Physical acceptance and actual integration history

- [x] Commit `7295363` records physical acceptance of
  `c5e036b6e87d9aa77700909b508ccc0c3978d5b2`:
  **normal → persistent-root → normal**, root 295 → retained 295 → fresh 297.
  Recovery produced no reset-log increment; root-local probe survived recovery
  and disappeared on normal reset; persistent probe survived both. Machine ID
  stable, expected services active, zero failed units. Current root/closure
  corroborate the final normal boot. This update did not repeat those trials.
  The three earlier opt-in physical reset trials remain historical evidence.
- [x] Live GitHub main: `f89205c07e4d3a77900b046a5bf937944488647b`.
  PRs [#3](https://github.com/P2949/NixosConf/pull/3),
  [#4](https://github.com/P2949/NixosConf/pull/4), then
  [#6](https://github.com/P2949/NixosConf/pull/6) merged on 2026-10-05.
  This differs from the guide's proposed single stable-refresh-to-main PR.
  Record actual history; do not repeat or undo integration to mimic the proposal.
- [~] Physical acceptance is recorded as passed, but no newer independent
  home-backup/restore or matching-ISO physical read-only drill receipt was found.
  Earlier receipts mark them pending. Desktop acceptance alone does not prove
  these prerequisite checks. Reconcile missing evidence explicitly.
- Earlier claims of root 292, October 2 live closure, uninstalled candidate,
  no main integration and an active prerequisite hold are now historical.

### Readiness branch and changes requiring validation

- Branch: `feat/pre-optimization-readiness`; HEAD:
  `c15a1756fe97ac89d7872326df70b0c758a0bfe0`, descended from integrated main.
  Commits above main: `7295363`, `96c6a3d`, `c15a175`.
- [x] `96c6a3d` moved Btrfs scrub and GC/scrub coordination into
  `modules/storage/btrfs-maintenance.nix`; guard moved to
  `modules/storage/maintenance-guard.sh`. Desktop import, test and README updated.
  Generic GC/journal/coredump policy stays in core. Actual layout uses files,
  rather than the guide's proposed directory structure.
- [x] `c15a175` extracted `modules/storage/ephemeral-root-reset.sh`;
  Nix substitutes escaped configuration placeholders with `builtins.replaceStrings`.
  Implementation is committed; the running closure predates these refactors.
- [~] Existing staged `flake.nix` change passes `username` into workstation-smoke.
  The test still defines local `username = "p2949"` instead of accepting that
  argument. This change is incomplete/unvalidated and has been preserved.
- [ ] Live Actions query returned no readiness-branch runs. Frozen-candidate
  passes do not validate later refactors or the staged change. Required checks,
  closure comparison and subsequent physical acceptance remain outstanding.
- Other worktrees now point to stable-refresh `67b0c41` and workstation
  `ad89962`; do not call them frozen c5e checkouts. Accepted c5e and archived
  receipts remain the original acceptance reference.
- Lock SHA-256 unchanged:
  `7efb19569e8a022768cd570498ff8b93cb98b108358149b668a658e2d9f406a2`.
  No compiler optimization or final baseline tag is claimed.

### Preserved evidence and remaining gates

- [x] Exact c5e batch finished exit 0: fast 76.21s, safety 160.54s,
  recovery 382.18s, A 310.53s, B 365.86s, fallback 482.58s,
  workstation-smoke 10.04s, desktop/ISO 25.44s. Workstation-smoke reused a
  successful derivation; no fresh VM execution. No batch remains running.
  Private receipts/logs/guide/preflight:
  `/persist/nixos-logguard-refresh-20261005/`. bv3→czk closure delta was only
  system/initrd; no other package/kernel movement. This excludes later refactors.
- Matching recovery ISO: `d55ny1z4d53slhz3ilvyy2mg6d8khrqn`,
  1,496,678,400 bytes; SHA-256
  `52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
  Prior Ventoy copy/remount hash and clean filesystem checks passed;
  exact physical ISO drill remains unproven in available receipts.
- Retain eleven preparation GC roots, known-good generations, forensic roots
  and home staging until the relevant retention milestone.
  `/persist/nixos-preparation-gcroots.json` records protected identities.
- [ ] Independent home backup/external restore. Read-only snapshot
  `/persist/backup-staging/home-20261005` and its two-file restore are same-disk.
  User reports older separate secrets backup; fresh secrets restore is unproven.
  Git/LFS restore covers tracked project data only, not ignored work, autosaves,
  loose Blender files or application state. Existing inventories remain relevant.
- [ ] Finish module/test/flake/recovery ownership cleanup; critical
  `system.checks`, guarded `system.preSwitchChecks` with negative tests, ESP
  reserve evidence, blank-disk reconstruction VM, explicit secret contract and
  Facter comparison. Facter adoption remains optional if unjustified.
- [ ] Firmware decision/settings and VMX enablement remain unresolved in earlier
  evidence. CPU sustained stability unproven: intended 30-minute test stopped
  after about 5 seconds at 80°C. Cooling response is not capacity proof;
  do not raise the cutoff merely to pass.
- [ ] Final-candidate real workloads/hardware: sustained Blender/Unreal,
  gaming/controller/HDR where required, Creative Stage audio,
  Android/virtualization and multi-day soak. Existing Vulkan/Gamescope, HIP,
  Unreal compile/map smoke results retain their limited scope.
- [ ] Complete validation and readiness→main integration, compare actual-main
  closure, then annotate `nixos-26.05-pre-optimization-baseline`.
  Only afterward create `feat/optimization-framework-v2` and stop at the boundary.
- Continue offline work without unnecessary reboots; batch justified physical
  checks into a planned window and preserve the graphical session.

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

- [x] Dry activation preview exercised against built workstation candidate a02fb on 2026-10-05 before any real activation; running closure/profile, cooling PID/invocation, boot ID and graphical session unchanged. Continue using previews before service-affecting changes.

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
- [~] GameMode registration/reaper pass; current governor helper denied. Group/mitigation fix prepared with VM allow/deny proof; physical feature retest after activation pending.
- [~] MangoHud library/shim mapped in successful physical Gamescope Vulkan smoke; representative-game/final-candidate acceptance pending;
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

- [~] official UE 5.8.2 path loaded actual project on current trial; final-candidate acceptance pending;
- [~] Steam FHS build/editor wrapper passed actual-project tests on current trial; final-candidate acceptance pending;
- [~] native Wayland startup/configured-map rendering passed on current physical trial closure (SDL3 wayland, compositor xwayland=false); final candidate/soak acceptance pending;
- [~] actual editor Vulkan selects RX 9070 XT/RADV GFX1201, Mesa 26.1.8; final candidate acceptance pending;
- [~] actual `AI_Gavin_Project` module and configured startup map loaded, 28 actors, ten-second editor tick/render hold; interactive play/final candidate acceptance pending;
- [~] actual editor target incremental link passed; full compilation/final-candidate acceptance pending;
- [~] UBT reported Epic Clang 20.1.8/Rocky8 sysroot/libc++; final-candidate acceptance pending;
- [ ] editor can run the project;
- [ ] no global compatibility environment pollution was introduced.

## 30.2 Blender

- [~] Blender 5.2.2 LTS loaded both actual local scenes; final-candidate acceptance pending;
- [~] actual-scene render selected RX 9070 XT HIP alone; final-candidate acceptance pending;
- [~] actual 33-object Cycles camera render completed 1920x1080/64 samples; sustained/final acceptance pending;
- [~] no crash/new targeted GPU kernel faults in actual local-scene render; sustained/final acceptance pending.

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

- [~] selected stable 0d9e9b8 prepared and fully checked on feat/stable-refresh-validation (draft PR #4); integration/physical acceptance pending;
- [~] release-26.05 checked current at db7d5e2 and follows selected stable pin; compatible full-profile VM passed, integration/physical acceptance pending;
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
- [~] Actual local scene HIP camera render passed; interactive/sustained/final-candidate acceptance pending.
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
[~] unified GC/generation policy (prepared/tested; physical installation pending)
[~] journal/core-dump growth policy (prepared/tested; physical installation pending)
[x] validation dev shell
[x] baseline-info capture app/script
[x] closure-diff review procedure
[ ] BIOS/ME decision
[ ] OC/RAM revalidation
[x] ReBAR audit (16 GiB GPU BAR above 4 GiB; firmware policy freeze pending)
[~] CPU policy declarations audited; loaded comparison/final running acceptance pending
[ ] zram decision
[ ] irqbalance decision
[x] NVMe scheduler audit (kernel-selected none; preserved)
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

## Development preflight and current CI — 2026-10-05

Exact preparation PR head c2b43ca CI run 37289661236 completed successfully.
Local clangd in the current HM profile completed C++20 AST/index checks with
zero errors. Candidate development shell Clang compiled/ran the vector smoke;
clangd requires --query-driver for that exact trusted compiler wrapper to
discover Nix C++ include paths. Initial test incorrectly passed -std to clangd
CLI, corrected to a compilation database. Without query-driver, the database
probe then reported missing vector; exact-wrapper query resolved all errors.
Final smoke log /tmp/nixos-clangd-devshell.log. No global clangd allowlist or
project settings modified. Candidate HM still owns pinned clang-tools.
This verifies the development setup, not final post-activation acceptance.

Android/KVM preflight: user belongs to kvm, but /dev/kvm is absent and current
boot kernel says "VMX (outside TXT) disabled by BIOS". CPU exposes no vmx
flag. Firmware virtualization enablement is required before accelerated
emulator acceptance; defer it to the already batched firmware/reboot window.
No module load or firmware change attempted to disguise this hardware gate.

Actual AI_Gavin_Project Git worktree is clean on main, HEAD 376e151fca709b084e182da4c76ccb21a228f86d.
Fresh git ls-remote confirms remote main at the same commit. All 415 local
LFS objects exist, match declared sizes and SHA256 IDs (2247127 bytes total).
Read-only custom hashes used instead of git lfs fsck, which can move bad
objects. This proves local object integrity and pushed Git commit, not remote
LFS availability or independent backup/restore. Those gates remain pending.
Engine executable and project file exist; editor/project launch, actual C++
target build and renderer acceptance remain unperformed. No project contents
or remote credentials published; no project files changed.

## Remote restore proof and backup inventory — 2026-10-05

Preparation head d3467fa CI run 37290085329 succeeded. Previous turn made
verified progress: development tests, source documentation and master ledger
were committed/pushed. This turn continues independent recovery/backup work.

Fetched Unreal HEAD LFS objects into a newly empty isolated storage directory,
so existing local objects could not satisfy the operation. All 415 remote
objects retrieved; exact sizes and SHA256 matched, zero missing/corrupt.
Fresh no-checkout clone restored AI_Gavin_Project.uproject at remote HEAD
376e151fca709b084e182da4c76ccb21a228f86d; SHA256
eb5d13da3a8d07c82ca4f1d2722c1189fc1832248c7254d6054dc692e31dc92b
matches the clean local file. Private receipts in /persist record remote LFS
and representative Git restore proof. These prove this project's tracked
remote data, not an independent encrypted backup of all critical home data.

Read-only Development Git discovery (excluding engine/dependency/build cache
trees) found one project repo, clean, no untracked files and valid upstream.
No claim that every repository elsewhere in home has been audited. Home
category allocated-byte inventory: Development 118032478208, .config
1778237440, .local/share 14045966336. Engine tree 117487734784; Unreal
projects 544743424. Values are du accounting, not deduplicated backup-size
predictions. Project ignored data includes Binaries (5 files/3941728 bytes),
DerivedDataCache (5/1627828), Intermediate (128/525015000), Saved
(30/5672980). Preserve Saved/autosaves until content importance established;
a clean Git status does not prove ignored data is reproducible. Private
inventories saved root-only under /persist; no project contents published.

Only external block disk present is 57.7 GiB Ventoy USB; read-only mount found
existing multi-OS ISO files and 43239342080 bytes free. No separate backup
drive connected. Asked for an independent backup destination while continuing
other work; the user's earlier separate secrets-backup report is retained,
not relabelled as a fresh home backup. No home backup or encryption/restore
gate claimed complete.

Read-only storage refresh: all five Btrfs device error counters zero; last
scrub (2026-10-04 03:20:45) finished with no errors. No new scrub started.
Pinned recovery ISO is being added under a new filename on Ventoy without
replacing existing images; copy complete in size, explicit flush and hash
verification still running. This is not physical boot/drill acceptance.
The private GC-root receipt was refreshed atomically to include the seventh
maintenance-candidate root; exact symlink target verified before recording.
USB kernel log notes a pre-existing exFAT improperly-unmounted warning on
both the initial read-only audit and later writable mount. Copy flush is still
active, with device writes progressing; no repair or interruption attempted.
Do not claim recovery-media readiness until hash/clean unmount completes.

Recovery USB copy completed: added
nixos-workstation-recovery-26.05.20261002.774debe-x86_64-linux.iso
(1496678400 bytes) without replacing existing images. Explicit flush completed,
copy SHA256 matched 085a7b41e54e4e595f34fcea1ad9d37b48662d7eeae24d0f40781081d86678ca;
clean unmount succeeded. Pinned exfatprogs 1.3.2 read-only fsck -n subsequently
reports clean (6 directories/8 files); no filesystem repair performed. A fresh
read-only remount checksum is running before final media-copy acceptance.
Current NM reports connected/full; PipeWire/Pulse/WirePlumber active, Bluetooth
Powered=yes. These establish daemon/connectivity state, not audible sound,
peripheral reconnection or full workload acceptance. No current boot kernel
amdgpu timeout/reset/fault/MCE/hardware-error matches in the targeted search.
Post-remount ISO SHA256 matches the pinned artifact exactly. Read-only audit
mount cleanly unmounted; the new media file is ready for its pending physical
boot/drill. No host reboot, live activation, service restart, home-data copy,
secret read or old ISO replacement occurred. Recovery and backup documentation
updated on the isolated preparation branch. Independent backup destination
question remains pending; continue unrelated offline work while awaiting it.

## Activation preview and Blender preflight — 2026-10-05

Reviewed generated candidate dry-activation snippets: persistence/filesystem
activation excluded; user update code checks NIXOS_ACTION=dry-activate.
Existing /root0700 and /home0755 match the generated directory setup.
Ran a02fb/bin/switch-to-configuration dry-activate successfully, equivalent
to previewing that already built exact closure without rebuilding source.
Would stop/start commander-core, reload D-Bus, restart scrub timer, HM,
polkit and journald. No real switch/test/boot performed. Before/after capture
proves unchanged boot ID, runtime closure, system profile, cooling MainPID
and InvocationID, active Wayland session. Private preview/runtime receipts
saved under /persist. This confirms why live activation is still deferred.

Current Blender 5.2.2 LTS background factory-startup HIP probe completed
exit0, enumerating physical RX9070XT HIP and CPU. CUDA CUEW initialization
warning observed; selected test backend is HIP, not CUDA. No custom user
preferences/project opened or altered. A bounded factory-scene GPU render
smoke is running with only the physical HIP GPU selected, CPU device disabled,
512x512/32 samples and two host preparation threads; output only under /tmp.
This is preparation smoke, not sustained or user-project render acceptance.

Blender HIP smoke completed exit0: RX9070XT selected alone, CPU disabled,
512x512/32 samples rendered to PNG (210552 bytes) in 2.30 seconds; private
receipt /persist/nixos-blender-hip-smoke-20261005.json. Targeted current kernel
log has no new GPU timeout/reset/fault or MCE/hardware-error match. Wayland
remains active, Commander Core remains active, zero failed system units.
After tests CPU package30C/GPU junction39C. Representative project render,
longer thermal/stability and final candidate acceptance remain open.
Exact preparation head a17023b CI run 37290998797 succeeded.

Actual AI_Gavin_ProjectEditor Linux Development incremental target build
passed using the existing Steam FHS environment, Epic bundled DotNet, Clang
20.1.8 from v26_clang-20.1.8-rockylinux8/x86_64-unknown-linux-gnu and bundled
libc++. MaxParallelActions=2 and nice10 used to preserve interactivity.
One project shared-library link action executed, result Succeeded in2.06s;
this is not a full recompile or large-compiler-load stability proof. Tracked
project worktree remains clean. First invocation from /etc/nixos failed
because the FHS view lacks that cwd; retried from actual project directory
with the identical build command. No source edits or engine/toolchain flags
changed. Private full build log /persist/nixos-unreal-cpp-build-20261005.log.
Graphical editor/project launch, play and Vulkan rendering remain pending.

## Native Unreal graphical validation — IN PROGRESS, 2026-10-05

Preparation PR exact head caafd7a CI run 37291668888 succeeded. Previous
turn completed build/render evidence and activation preview; no reboot or
configuration activation. Native test launched existing unreal-engine wrapper
from the project home directory, temporary SDL_VIDEO_DRIVER/SDL_VIDEODRIVER
wayland selection, explicit Vulkan, unattended startup; no global overrides.
SDL3 log confirms wayland, compositor client confirms xwayland=false/mapped,
Vulkan log confirms radv/Mesa26.1.8. Actual project game name and linked
AI_Gavin_Project module loaded. No GPU/software-fallback substitution.

Initial ExecCmds=QUIT did not close the editor; installed source defines
QUIT_EDITOR instead. Requested close via current Hyprland Lua dispatcher
hl.dsp.window.close({window="pid:30808"}); old string dispatcher syntax
rejected without action. Process exited0. All other observed window addresses
retained; test windows gone, current session/cooling remain active. Startup
modified generated editor/cache state, not tracked project files (Git clean).
No project assets saved by test.

A more precise Python map probe verifies intended project root, loads its
configured EditorStartupMap and checks editor world/actors before calling
SystemLibrary.quit_editor. Initial script in host /tmp was inaccessible to
Steam FHS private tmp; engine correctly logged missing script, no receipt,
so no map pass inferred from its process exit0. Relocated script/report to
user-private ~/.cache/nixos-validation and reran. Map proof pending result.
This is actual startup/map validation, not interactive gameplay/soak.

Map probe returned success with 28 actors from configured startup map; engine
version 5.8.2-56702186+++UE5+Release-5.8. Physical Vulkan device explicitly
RX9070XT RADV GFX1201. HOWEVER orderly quit then crashed: SDL teardown
destroying tracked windows, free(): invalid size, Signal6 handler followed by
SIGSEGV; process exit139, core PID31445 present485.1M. Do not mark clean
editor lifecycle accepted. Initial compositor-close smoke bypassed normal
teardown (RequestExit force=true), so its exit0 does not contradict this
reproducible-fault candidate. Current session/cooling healthy, zero failed
system units, no targeted GPU/MCE kernel fault. Tracked project remains clean.

Captured existing core privately under ~/.cache/nixos-validation mode0600
inside0700 parent, rather than launch another GUI merely for a stack trace.
Offline GDB in the same Steam FHS view is reading it; only function backtraces
requested, no locals/env/core contents published. Workload failure investigation
continues before final baseline acceptance; no global workaround introduced.
Offline core backtrace locates glibc malloc abort at ubidi_close_64 in bundled
Unreal Core ICU, through FICUTextBiDi/FTextLayout/Slate widget destructors;
no external libicu shared object matched. A scoped -ansimalloc trial changed
only that test process's default Mimalloc to ANSI: same map/28 actors, exit0.
Vulkan shutdown suballocation warnings remain; do not treat this as full
workload acceptance or install an allocator workaround on a single trial.

Harness audit then found a critical confound: SystemLibrary.quit_editor calls
QUIT_EDITOR synchronously, but installed EditorPythonExecuter source explicitly
requires a full tick after the script before its deferred quit. The probe's
immediate quit did not follow that lifecycle. Corrected probe uses keep-script-
alive plus a post-tick callback, holds the loaded map for 10 seconds, then
clears keep-alive so the native executor defers orderly close. Retesting the
unchanged default Mimalloc first; no launcher/code policy change made. Original
crash evidence remains valid, but applicability to ordinary user shutdown is
unproven until this corrected lifecycle test completes. No engine source edit.

Corrected lifecycle test completed exit0 with DEFAULT Mimalloc: intended
project/root and configured startup world matched,28 actors, held10.0029s
over1195 post-tick callbacks. Python reflected class is EditorPythonScripting
(as declared by installed ScriptName metadata); first keep-alive attempt used
wrong class name, so hold was not claimed despite clean framework-deferred
exit0. Final test used correct class and native executor deferred close.
Original synchronous in-script quit was a confound; corrected default close
passes. Do not adopt -ansimalloc or libdecor/driver/global memory overrides
based on the flawed probe. No source config/engine/allocator policy changed.

Held-render test still logs Vulkan shutdown suballocation warnings (not an
abort, process exits0); retained privately for later workload/soak review.
No observed kernel GPU/MCE/hardware fault. Intentional earlier diagnostic
core retained privately and classified as test-harness lifecycle failure;
not silently vacuumed or presented as an ordinary user shutdown regression.
Current startup/map smoke is valid, but gameplay and final baseline/soak
remain unproven. Receipts/logs stored root-only under /persist.

## GameMode and audio runtime gates — IN PROGRESS, 2026-10-05

Exact preparation head3f61a1c CI run37293252039 succeeded. GameMode1.8.2
selftest on current generation: registration, dual-client, reaper and
supervisor pass; governor performance switch failed with pkexec Not authorized.
Live user lacks gamemode group; upstream packaged polkit rules require it
for governor/GPU/CPU/procsys helpers. No inference that requests alone prove
governor policy works. All12 CPU policy governor/EPP values equal captured
pre-test values afterwards; GameMode inactive, split_lock_mitigate remains1.
Screensaver service unknown also logged; no screen-lock service disabled.

Prepared fix in isolated gaming module: conditional p2949 gamemode membership
when enabled, and general.disable_splitlock=0 to preserve stock mitigation
even in gaming sessions. No live group/policy/service modifications. Added
real-profile VM behavioral polkit authorization proof for user and deny
control for nobody. First VM fixture incorrectly awaited inactive DBus-
activated polkit before first request; moved wait after actual pkcheck trigger.
No host helper or governor change used by VM. Fast flake checks passed;
updated VM and full desktop candidate builds running.

Audio inspection: Creative Stage Pro USB041e:32b4 present, ALSA card0,
PipeWire sees device but current profile Off and only active sink is RX9070XT
HDMI3 stereo (volume0.65). No claim that Creative is active or audible.
One-second 48kHz stereo zero-valued WAV playback passed direct ALSA Pro
plughw and current PipeWire default separately; no audible tone, sink/profile/
volume/route change. Pro PCM returned closed afterwards. This verifies driver
and default transport, not Creative-through-PipeWire hearing/reconnect.
Current route preserved; dedicated Creative audio acceptance remains open.
Updated real-profile VM passed:
/nix/store/bpxcynh3pg4xamy6dsp0q197hn0513qh-vm-test-run-workstation-smoke.drv.
Intended user actual polkit helper action succeeds; nobody returns1, proving
privilege is not granted to unrelated user. Standard full-profile boot/HM/
networking/zero-failed/hardware-exclusion tests still pass. Desktop candidate
/nix/store/cpwrqq3c7kjxgknf5slk5h2sbs7gv4kq-nixos-system-desktop-26.05.20261002.774debe
built; generated INI contains [general] disable_splitlock=0, user membership
includes gamemode. Closure diff from a02fb has no package-version changes.
Eighth explicit GC root gamemode-candidate protects new closure; previous
seven retained, private exact-target receipt atomically refreshed. Final fast
checks running after the corrected fixture; physical feature retest remains
pending actual candidate activation. No live group/CPU/mitigation edit.

Final fast flake check completed successfully after fixture correction.
GameMode source/docs committed on isolated preparation branch; desktop build
and behavioral VM complete. Root safety A/B/recovery/fallback derivations
remain unchanged by this gaming-policy fix. No source integration into running
generation, no reboot scheduled, live graphical session/cooling remain active.

## Deliberate stable-input refresh preparation — IN PROGRESS, 2026-10-05

Previous goal turn made concrete progress: GameMode authorization source fix,
behavioral VM allow/deny proof, full build and audio transport evidence published.
Phase30 upstream inspection now finds stable26.05 HEAD
0d9e9b832d03ac387417e16ce1febf73b2e631e1 (2026-10-04T19:50:49Z), compared
with current774debe7a0d1b496e35677ad955a1011c6ff74f3. Home Manager release26.05
HEAD remains db7d5e2332710f5abb088f6b5de927d7f9511b35 (same current pin).
GitHub compare reports171 commits/254 changed files, including kernel6.18.55
and wpa_supplicant2.12 updates. Actual closure impact still must be reviewed.
Primary upstream comparison:
https://github.com/NixOS/nixpkgs/compare/774debe7a0d1b496e35677ad955a1011c6ff74f3...0d9e9b832d03ac387417e16ce1febf73b2e631e1

Created isolated /persist/etc/nixos-stable-refresh worktree on
feat/stable-refresh-validation from preparation head862735e. Current root
and preparation branch pins remain unchanged. Selected only nixpkgs and
consistent HM release refresh; retain proven Disko/Impermanence/unstable/
liquidctl pins. Lock diff/evaluation in progress before any merge/activation.
Need full fast/heavy tests, desktop/recovery builds, closure review and later
physical acceptance before declaring this chosen refresh accepted/frozen.
No reboot or service restart; existing candidates/ISO GC roots retained.
Lock update complete: exactly nixpkgs locked revision/date/narHash changed;
original nixos-26.05 ref and every other input node identical. Fast checks
passed. New desktop candidate built and registered valid in store:
/nix/store/bv3qgrvavss8r34shphqch0cdp4yk14j-nixos-system-desktop-26.05.20261004.0d9e9b8.
Closure diff from cpwr: kernel/initrd6.18.54->6.18.55, Lua5.5.0->5.5.1,
WebKitGTK2.54.0->2.54.1, wpa_supplicant2.11->2.12, system revision/source
metadata changes; no Mesa-version change reported. Exact diff saved in /tmp.
Candidate protected by ninth GC root stable-refresh-candidate; prior eight
retained and private receipt refreshed. Real-profile VM (including polkit
allow/deny controls) passed69.25s; safety matrix passed147.38s. Remaining
A/B/recovery/fallback tests still running, recovery ISO compression active.
Latest memory PSI averages zero; graphical session/cooling remain active.
New stable recovery ISO built successfully:
/nix/store/d55ny1z4d53slhz3ilvyy2mg6d8khrqn-nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso/iso/nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso
1496678400 bytes, SHA25652e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061.
Protected by tenth GC root stable-refresh-recovery-iso; original ISO/candidates
retained, root-only receipt updated. Additional Ventoy copy flushed, checksum
matched and cleanly unmounted under new filename
nixos-workstation-recovery-26.05.20261004.0d9e9b8-x86_64-linux.iso.
No old images overwritten. Read-only exFAT/checksum remount verification now
running; physical boot/drill still pending. A and B three-boot tests passed
318.18s and322.56s under refreshed kernel; recovery/fallback still running.
Refreshed recovery VM passed323.84s; only fallback VM remains active.
Read-only post-remount ISO SHA256 matches52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061;
exfatprogs -n reports clean (6 directories/9 files), clean unmount completed.
Media-copy acceptance complete; physical boot/read-only drill still pending.
Retired only our duplicated expanded GDB scratch core copy after diagnosis;
original systemd core and private backtrace receipts retained. No user project,
secret, store output, profile generation or forensic root removed.
Fallback VM passed429.01s; full six-test build batch completed exit0.
Complete refreshed outputs recorded root-only in
/persist/nixos-stable-refresh-heavy-build-20261005.json and desktop/ISO JSON.
All six explicit heavy VMs and all fast checks pass for chosen0d9e9b8;
desktop/recovery builds and closure review complete. New recovery USB checksum
and clean exFAT check passed; disk unmounted. Selected stable/HM alignment and
all unchanged pins documented in isolated refresh branch, with closure-diff
artifact committed. Current source root/preparation input pins remain unchanged
pending review/integration; no final freeze or physical acceptance claimed.

## Stable refresh publication — 2026-10-05

Published separate draft PR #4:
https://github.com/P2949/NixosConf/pull/4
base feat/workstation-validation, head feat/stable-refresh-validation.
Source refresh commit033a02a plus master-plan synchronization committed/pushed.
Only the stable input node and review/evidence documentation differ from its
preparation base; all six heavy tests, fast checks and artifact/media proofs
are complete. Keep draft unmerged until remaining baseline integration and
physical gates are satisfied. No final baseline/optimization tag or branch.

## Reboot budget and graphics smoke verification — 2026-10-05

The three successful physical reset trials are sufficient; do not repeat them.
User requests avoiding further reboots because each destroys the graphical
session. Continue offline preparation and bounded runtime checks; batch any
remaining final-candidate/recovery-media physical acceptance into a planned
window. No reboot, live activation or graphical/cooling restart performed.

Gamescope 3.16.23 nested Wayland and XCB/XWayland Vulkan cube runs each
completed 600 frames on RX 9070 XT RADV and exited zero. MangoHud 0.8.3
initialized; the XCB child maps positively contain libMangoHud.so and its shim.
Small temporary windows closed normally. Logs retain nonfatal keyboard/cursor
and teardown warnings; outer refresh was 155 Hz and HDR was disabled. These
are smoke checks, not gameplay, HDR, controller or sustained-load acceptance.
Cooling remains active, Wayland session active, no failed system units or
matching new kernel GPU reset/fault/timeout messages in the test interval.
Stable refresh draft PR #4 exact-head CI run37297618440 succeeded.
Remaining physical, independent-backup and representative-workload gates
remain open; the full baseline goal is not declared complete.

## Pressure and IRQ evidence collection — 2026-10-05

Preparation collector now records memory/CPU/I/O PSI, VM counters, interrupt
distribution, effective IRQ affinity, IRQ-balancer state, NVMe scheduler and
zswap/THP defrag. Bash syntax and pinned ShellCheck 0.11.0 pass. Full updated
collector run completed with 56 captures, all exit zero; private receipt
/tmp/nixos-preparation-expanded-20261005.md. Validation shell does not include
ShellCheck, so lint used the independently resolved pinned stable package.
Observed memory PSI averages zero, irqbalance absent/inactive, NVMe scheduler
none, zswap disabled and THP defrag madvise. This is a snapshot, not workload
delta evidence; no IRQ/memory policy decision or loaded acceptance claimed.
No kernel tuning, service restart, live activation or reboot performed.

## Broader home inventory and architecture reconciliation — 2026-10-05

Read-only full top-level home accounting completed: 31 entries, no failed
directory scans, 18,361,851,904 allocated bytes across directories outside
Development. Symlinks recorded without traversal; file contents not collected.
Private root-owned 0600 receipt:
/persist/nixos-home-full-inventory-20261005.json. This extends earlier partial
size inventory but does not classify all application data, prove remote
coverage, or substitute for independent backup and representative restore.
Destination question remains pending; recovery USB is not repurposed.

Preparation README architecture/tree reconciled with guarded maintenance,
storage module and workstation/maintenance/Commander tests. Backup ledger
updated with inventory scope and limitations. Documentation diff whitespace
check passed. No home data removed, backup destination assumed, live
activation, reboot or service restart performed.

## Evaluated stock policy audit — 2026-10-05

Stable-refresh source909700b evaluated kernel6.18.55, no permanent governor,
irqbalance=false, zram=false and existing disk swap with implicit priority.
No mitigation-disable/CPU-isolation parameters or arbitrary memory tuning.
System/HM environment names exclude global compiler/linker flags,
LD_LIBRARY_PATH, RADV_PERFTEST and MALLOC_CONF. Optimization module remains
empty; nix-ld compatibility variables are intentional. Names only recorded,
not environment values. Root-only receipt:
/persist/nixos-stock-policy-audit-20261005.json.
Initial attempt serialized whole swap submodule and encountered unset optional
label; corrected query selected defined device/priority fields and succeeded.
This is an evaluation-query issue, not a failed configuration build.
Preparation docs/stock-policy.md records declared policy and remaining scope.
Loaded CPU/IRQ/memory evidence, firmware policy and final running acceptance
remain pending. No activation, tuning, reboot or graphical restart performed.

## Final-policy runbook separation — 2026-10-05

Physical runbook now separates completed historical opt-in trials from the
remaining final-default/persistent-root acceptance window. The final section
requires exact source/lock/closure receipts, boot-only installation, matching
new ISO read-only drill, exact default boot validation, non-reset recovery
identity/root/log/state proof and return to accepted normal policy. It explicitly
rejects repeating the three trials or live activation during this transition.
Stable-refresh media filename/SHA matched the previously verified artifact.
This prepares the interruption; none of these pending physical actions ran.
Documentation whitespace check passed; source and final acceptance remain
distinct. Latest refresh CI run37299169138 was observed in progress at its
then-head a799647; previous-head54ee0ef run37298793271 succeeded.
No host boot entries, default, runtime services or firmware changed.

## Physical Intel ME identification — 2026-10-05

Read-only ME sysfs query returned all three component blocks:
0:14.1.53.1649, 0:14.1.53.1649, 0:14.0.51.1528. Kernel ABI documents up
to three component versions; no unsupported component-role decoding assumed.
ASUS support reverified BIOS3402 dated2026-08-05 requiring ME14.1.79.2540
first, and MEUpdateTool14.1.79.2540v5 dated2026-09-01. Current readings do
not establish that prerequisite. Source links and published package SHA256
recorded in preparation docs/firmware-preparation.md; no firmware flashed.
Collector now captures all readable ME firmware blocks and fails explicitly
if the interface is unavailable. Bash syntax/ShellCheck pass; full run has
57 captures, all exit zero, private /tmp/nixos-preparation-me-20261005.md.
Firmware/OC settings capture, upgrade decision and hardware stability gates
remain pending. No reboot, live activation or graphical/cooling restart.

## Sustained CPU gate attempted; conservative stop — 2026-10-05

Planned30m stress-ng12CPU/all-method/verify at nice19 with5s monitoring.
Preflight cooling/session active, low load, CPU about30C. Supervisor stopped
all workers after5.06s when CPU max sampled80C reached conservative boundary
matching coretemp high value; no threshold increase or cooling-policy change.
Stressor short run reported12passed/0failed; supervisor marks thermal test
aborted, not accepted. Throttle counters unchanged; targeted new kernel
hardware/thermal errors absent; CPU returned28–30C, cooling active/high100%
fan and pump100%, Wayland session still active. No host reboot/activation.
Root-private receipt/log under/persist/nixos-cpu-thermal-20261005. Receipt UTC
is explicitly completion time with elapsed duration, not mislabeled start.
30minute thermal and longer OC/RAM stability gates remain open. Review
firmware/OC/power/cooling state before retry; do not repeat short tests or
relax the boundary merely to obtain a green result.

## Cooling response timing and CI supersession — 2026-10-05

Journal correlation places approximate stress interval10:55:13.778–18.838UTC;
keeper commanded fans100% at10:55:16.405 (CPU79C) before supervisor stop,
then60% at10:55:30.408 (CPU28C). PID912/invocation unchanged and session
active. This establishes logged control response, not measured RPM/capacity
or sustained acceptance. Private cooling journal added to thermal receipts.

Preparation workflow adds workflow/ref concurrency with cancel-in-progress
per official GitHub documentation, retaining Flake checks name/triggers and
required-check semantics. This prevents future superseded same-ref checks
from consuming parallel CI; separate branches/PR refs stay independent.
Whitespace review passed; new exact-head CI acceptance remains pending.
No host load repeated, cooling change, reboot or activation.

## Local source-work discovery — 2026-10-05

Read-only visible-home/project metadata scan found1Git repo, clean, no Git
status failures;476matching source/document/project files totalling2,699,360
bytes.2Blender files outside discovered repos total313,363bytes and require
critical backup coverage. No traversal errors. Private path/status receipt
/persist/nixos-home-work-audit-20261005.json mode0600/root-owned.
Engine/generated/application/cache scan exclusions are not approved backup
exclusions; extensions do not prove all unique home data audited. Ignored
project/autosave/application data remain required. Current disks still only
MP600 and Ventoy; independent destination pending, no deletion/repurposing.
Backup ledger updated. No host tuning/load, reboot or live activation.

## Actual Blender scene GPU validation — 2026-10-05

Both discovered local .blend files loaded with source SHA256 unchanged,
33object Cycles scenes/cameras, no missing file-backed images/linked libraries
detected. Newer actualscene rendered1920x1080/100%,64samples in11.83s on
RX9070XT HIP alone, CPUdevice disabled, PNG produced, exit0 under180s limit.
Samples/output/device choices in-memory only; neither project nor preferences
saved. Sourcehash unchanged. Existing CUEW warning retained; HIP successful.
No new targeted kernel GPU reset/fault/timeout messages; cooling and Wayland
session active. Root-private inspection/render receipts:
/persist/nixos-blender-project-validation-20261005. Image remains private tmp.
This verifies actualscene load/render beyond factorysmoke, not all dependency
classes, interactiveworkflow, sustainedrender or finalcandidateacceptance.
No reboot, activation, service restart or physicalclockpolicy change.

## Workload ledger reconciliation and Android prerequisite gap — 2026-10-05

Phase24 checkbox ledger now marks measured Unreal wrapper/toolchain/target and
Blender scene/HIP/render evidence partial rather than leaving those tests
unrecorded. Full compilation, interactive/sustained work and finalcandidate
acceptance remain open. No broader acceptance inferred from smoke tests.

Android/Java preflight: no java/javac on current PATH; no Android declaration
in current preparation Nix source; standard .android/.gradle/Android/
AndroidStudioProjects/Google/JetBrains state paths absent; inspected home
contains no Java source outside excluded engine/cache paths. Therefore an
actual Android/Java workflow cannot yet be validated. This is distinct from
BIOS-disabled VMX/missing /dev/kvm. No SDK licenses accepted, arbitrary JDK
selected or absent application/project workflow assumed. Required tooling
and intended project remain to establish; Android gate not bypassed.
CI latest stable-refresh head59f26b run37300432384 observed pending; previous
bb5699c run37300122243 inprogress; f16aeea run37299922367 cancelled;
a109542 run37299736219 succeeded. No fresh load/reboot/activation performed.

## Reset diagnostic alias hardening in progress — 2026-10-05

Code review found reset log initialization could follow symlink/hardlink aliases
and chmod/append unrelated persistent data before refusal. Source now validates
relative log components, checks each parent against symlinks/non-directories,
and refuses leaf symlink/nonregular/hard-linked files before touch/chmod.
Nested log paths remain supported with a positive configuration control.
Safety matrix adds five leaf-alias/type cases and two parent-alias/type cases;
file modes now included in preservation comparisons and log metadata retained
on refusal. New totals intended33runtime refusals/43invalid config cases,
with4positive controls. No physical source activated.
Bash source formatting completed. Fast check session10340 and disposable
Btrfs safety VM session66710 authoritatively still running; logs under
/tmp/nixos-log-safety-{fast,vm}-20261005.log. Results not yet claimed.
These are additional safety changes; prior closure/VM results do not establish
acceptance of this new script. No reboot, cooling/graphical restart or live
activation. Propagation/build review follows passing checks.

Fast checks completed exit0. First safety VM stopped at nested-parent fixture:
test replacement assumed quoted safe assignment, but escapeShellArg emitted
an unquoted safe filename, so fixture still used default leaf. Leaf alias/type
cases passed before this harness error. Corrected fixture derives both
assignment spellings using the same escapeShellArg helper; rerun required.
Production nested-parent behavior not accepted based on failed fixture.

Corrected VM session72429 confirms all7new unsafe-log cases passed, including
nested parent symlink/file, while remaining matrix still running. Added
explicit nested-log runtime positive control for safe directory creation and
successful reset; not part of the currently running derivation, so another
final safety build is required before full acceptance. Formatting passed.
Existing stable-refresh exact-head d13d010 CI37300638766 completed success;
this predates uncommitted log hardening and is not evidence for new code.

Corrected33-refusal safety VM completed exit0. Final safety rebuild now includes
new nested-log successful-reset positive control, with final fast recheck
because the fixture changed. Logs /tmp/nixos-log-safety-final-20261005.log
and /tmp/nixos-log-safety-final-fast-20261005.log. Both builds started;
positive-control outcome not yet claimed. Previous33case proof remains valid
for unchanged production script; later fixture extends coverage.

Final fast check session56404 completed exit0. Final safety session91247
completed exit0:33refusals plus safe nested-log successful-reset control.
Actual physical log metadata root:root/0600/regular/one link satisfies guards;
read only, no physical reset attempted. New source is ready for publication
and propagation; selected refreshed-input boot/closure validation remains
required because script changed. Full baseline still not accepted.

Log hardening committed/pushed a74d195 and propagated into preparation and
stable-refresh branches. Refreshed-input validation batch started sequentially
(fast,33case+positive safety,recovery,A,B,fallback,workstation,desktop+ISO),
one build job/two builder cores. Private logs/JSON under
/tmp/nixos-logguard-refresh-20261005; receipts update after each terminal
step. Batch handle recorded by tool; no stage restarted from timeout.
Prior refreshed candidate/ISO and GC roots retained until new outputs reviewed.
No host live activation/reboot or graphical/cooling restart.

## Read-only home backup staging — 2026-10-05

Home subvolume descendant audit returned zero nested subvolumes. Created
additive read-only snapshot /persist/backup-staging/home-20261005 under
root-owned0700parent; ro=true verified and snapshot parent UUID matches
live/home UUID. Root-private0600receipt:
/persist/nixos-home-backup-staging-20261005.json. No existing snapshot
replaced/deleted. Same-MP600 staging only, not independent backup; application
databases were not quiesced, so no application-consistency guarantee. Refresh
staging/coverage for subsequent edits before actual external backup. Retire
only after explicit backup/restore and snapshot lifecycle review.

Refreshed batch session82197 still running: fastchecks passed76.21s, expanded
safety started. Stable-refresh source c5e036b remains unchanged during batch;
later documentation synchronization waits for receipts to avoid changing
source identity mid-validation. Cooling and Wayland active. No reboot/live
activation, home policy change, data deletion or independent-backup claim.

## Refreshed safety and home staging restore evidence — 2026-10-05

Batch82197 expanded stable-input safety passed160.54s; recovery now running.
Same immutable source c5e036b remains selected. No batch restart.
Copied both loose Blender files from read-only home snapshot to separate
private/tmpdirectory; snapshot/restored SHA256 matched for both and current
live file hashes still matched. Original work untouched. Root-private receipt
/persist/nixos-home-staging-restore-20261005.json. This is a staging copy/hash
proof on the same physical disk, explicitly not independent backup/restore
or Phase16 acceptance. External destination and application-data coverage
remain pending. No render repeated, no host activation/reboot.

Restore probe initially omitted the username component: snapshot source is
/home, not/home/p2949. First path lookup failed before any copy; corrected
paths preserve the full relative path from/home. Both copies/hash comparisons
then completed successfully with original files unchanged. No failed probe
was accepted as restore evidence. Coverage remains same-disk staging only.

## Immutable batch checkpoint — 2026-10-05

Exact stable-refresh c5e036b CI37301908893 completed success. Sequential
batch82197 still running recovery VM; completed fast/safety receipts preserved
root-private under/persist/nixos-logguard-refresh-20261005 with clean source
revision, lock/module SHA256 checkpoint. Only terminal successful stages copied;
checkpoint explicitly partial, not full-batch/candidate acceptance. Running
stable-refresh worktree remains clean/unchanged. Documentation synchronization
still deferred until batch terminal. No process restarted because of wait
timeout, no host activation/reboot or cooling/graphical restart.

Refreshed recovery VM completed exit0 in382.18s, including its three virtual
boots. Logs/output JSON and updated completed-step checkpoint copied to
root-private/persist ledger. Batch82197 advanced to testA; same source retained.
Runner preserved privately for reproducibility. These timings describe TCG
correctness tests, not physical performance. No physical reboot or activation.

TestA batch82197 authoritatively still running through VM boot checks; same
handle polled without restarting. Host cooling and Wayland remain active.
Completed results unchanged (fast/safety/recovery pass); no A acceptance yet.
This interval is a verified wait, not a claim of new implementation completion.

Refreshed A three-reset-boot VM passed exit0 in310.53s. Completed A logs/JSON
and timestamped partial checkpoint preserved root-private/persist. Source
revision still matches c5e036b. Batch82197 advanced to B (identity/journal
persistence), pending. Host cooling and Wayland remain active; no physical
reboot or live activation. Remaining B/fallback/workstation/artifact stages
not yet accepted.

B session82197 verified live and entering boot sequence; repeated bounded
waits returned same running handle. No terminal B result yet; completed
fast/safety/recovery/A remain passed. Cooling and Wayland checked active.
No restart, physical reboot or activation; immutable source retained.


## Unified continuation guide adopted — 2026-10-05

Read all 2,507 lines of the user-supplied Downloads guide:
`/home/p2949/Downloads/NIXOS_plan_md_Unified_Continuation_Guide_2026-10-05.md`.
Its dependency order now controls continuation. Exact stable-refresh source
c5e036b6e87d9aa77700909b508ccc0c3978d5b2 remains clean and frozen in
/persist/etc/nixos-stable-refresh. Do not merge this documentation into it,
refactor, change inputs, or start later readiness engineering before physical
acceptance. After acceptance use one stable-refresh-to-main PR, then create
feat/pre-optimization-readiness for the guide's remaining ordered work.
Final baseline tag waits for all required engineering, hardware, workload and
soak gates. Selective home/var Impermanence is explicitly deferred; no compiler
optimization work belongs in this baseline.

Live fetch verified main0721275, impermanencef674601, workstationd49c519,
stable-refreshc5e036b, historical optimization397a8c7. Impermanence advanced
beyond the guide snapshot through documentation-only evidence updates; preserve
these without merging into the frozen acceptance source.

Guide artifact claims predate completion of the diagnostic-log-hardening
refresh batch: do not infer that the older bv3 closure is the exact c5e output.
Continue existing session82197, not a new batch. Fast/safety/recovery/A/B now
pass; B completed365.86s. Fallback currently running; workstation and desktop/
ISO outputs remain pending. Confirm exact output identities after completion.
Actual GC roots live under /nix/var/nix/gcroots/workstation-preparation.

Independent external backup destination and representative external restore
remain open; same-disk staging is not independent backup. Physical matching ISO
read-only drill and exact normal/persistent-root acceptance remain open.
Three historical physical reset trials are sufficient viability evidence.
No physical reboot, live activation, graphical or cooling restart performed.
Decision: PROCEED with existing offline batch; HOLD source changes/integration
and physical installation until their prerequisite gates are satisfied.


## Frozen-candidate validation checkpoint — 2026-10-05

Existing session82197 polled live; fallback VM continues, not restarted.
B completed receipt/logs and updated partial checkpoint copied root-owned0600
to /persist/nixos-logguard-refresh-20261005. The complete user-supplied guide
also preserved privately there as continuation-guide-20261005.md.
Frozen stable-refresh worktree remains clean. Live Wayland session1 Active=yes
and commander-core active. Only MP600 and Ventoy USB attached; independent
backup/restore destination remains unavailable. No physical reboot, activation,
source change to the candidate, or declaration of full-batch acceptance.


## Exact frozen-source output identity — 2026-10-05

Read-only evaluation of clean stable-refresh c5e036b returned desktop drv
/nix/store/717rjl57vdmzbvi1xsh7y2l2rq778l6s-nixos-system-desktop-26.05.20261004.0d9e9b8.drv
with declared output
/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8.
This differs from the older bv3 desktop identity in the handoff; declared
output is not build acceptance. Existing batch will build/review it.
Recovery drv6w0ihzdsp3i6f6i08m7siz9sccxamh3f still declares d55ny1z4d53slhz3ilvyy2mg6d8khrqn,
so ISO identity remains unchanged at evaluation. No redundant ISO copy needed
if build and existing media evidence confirm the same exact artifact.
Concurrent eval emitted ignored SQLite busy warnings but completed exit0.
Derivation JSON probe initially assumed older top-level schema and failed;
corrected for the current derivations envelope and obtained both outputs.
No source change or physical activation. Fallback remains live session82197.


## Refreshed persistent-root fallback passed — 2026-10-05

Sequential batch82197 fallback completed exit0 in482.58s. Terminal VM evidence
confirms persistent-root retained root sentinel/identity, machine ID, journals
and credentials, with no failed units. Logs/output JSON and updated partial
checkpoint preserved root-owned0600 under/persist/nixos-logguard-refresh-20261005.
All five root VM scenarios now pass on frozen c5e036b; workstation-smoke has
started on the same batch. Desktop/ISO build and closure review still pending.
No physical boot/acceptance inferred from this VM. Candidate source unchanged;
no host activation or graphical/cooling restart.


## Exact c5e offline acceptance complete — 2026-10-05

Session82197 terminal exit0: workstation-smoke passed10.04s with existing
successful derivation reused (not a newly executed VM), desktop+ISO25.44s.
All eight batch stages passed. Complete logs/JSON/checkpoint preserved privately
under/persist/nixos-logguard-refresh-20261005. Frozen source clean c5e036b.
Built desktop: /nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8.
Matching persistent-root: /nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8.
Recovery ISO remains d55ny1z4d53slhz3ilvyy2mg6d8khrqn; staged artifact unchanged.
Exact closure-set comparison against bv3 removes only old system+initrd and
adds new system+initrd; no package/kernel movement. Version diff empty.
Private logguard-closure-diff.json records full set delta. New root-owned GCroot
stable-refresh-logguard-candidate added under workstation-preparation and
/persist/nixos-preparation-gcroots.json updated; all ten earlier roots retained.

Offline c5e acceptance now complete, but physical acceptance is NOT complete.
Independent backup+external restore, exact ISO boot/read-only drill, then boot-only
installation and normal/persistent-root/normal maintenance window remain next.
Do not merge stable-refresh or start readiness refactoring before those gates.
Live cooling and graphical session remain active. No physical reboot or activation.


## Physical preflight prepared without activation — 2026-10-05

Root-private0600 physical-preflight.json created in the preserved logguard
validation directory. Captures exact candidate and persistent-root closures,
live closure/boot ID, private machine-ID hash, root subvolume, all persistent
mounts, current ESP entries, three reset completions and session/service health.
No failed units; commander-core active; graphical session1 active. Exact c5e
candidate is NOT installed in current boot entries. Receipt explicitly records
backup/restore and recovery-media physical drill pending, and must be refreshed
before installation. Boot-only installation remains gated by those prerequisites.
No host switch/test/boot installation, physical reboot or source change.


## Prerequisite hold audit 1 — 2026-10-05

After completing offline acceptance and preflight preparation, rechecked actual
storage: only MP600 and Ventoy USB attached; no mounted NFS/CIFS/SSHFS destination.
Independent backup destination remains unresolved. Exact candidate clean c5e;
cooling and graphical session active. Guide forbids later source engineering
or integration before physical acceptance, whose backup and ISO-drill gates
remain unmet. No validation process remains running, and no redundant batch
started. Current turn is a prerequisite hold, not new implementation completion.
Next external input: connect/identify independent backup destination; then execute
backup and representative restore before the planned physical maintenance window.
Goal remains active; first consecutive impasse audit, not marked blocked.


Physical acceptance completed — 2026-10-05

Accepted source:
c5e036b6e87d9aa77700909b508ccc0c3978d5b2

Normal closure:
czk5a2wn8di3pgv8a6w0b8aj3286g3h3
nixos-system-desktop-26.05.20261004.0d9e9b8

Persistent-root closure:
9ppcqjkfnid501na0wc8jjysynp0kp1p
nixos-system-desktop-26.05.20261004.0d9e9b8

Kernel:
6.18.55

Recovery ISO:
d55ny1z4d53slhz3ilvyy2mg6d8khrqn
SHA-256:
52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061

Physical sequence:
normal -> persistent-root -> normal

Results:
- first normal boot reset root to subvolume 295
- persistent-root retained subvolume 295
- persistent-root produced no reset-log increment
- root-local and persistent probes both survived persistent-root
- second normal boot replaced root 295 with 297
- root-local probe disappeared
- persistent probe survived
- machine-id remained stable
- all expected core services active
- zero failed systemd units

Decision:
physical acceptance gate PASSED.
stable-refresh integration gate PASSED.
pre-optimization readiness engineering may now begin.


## Readiness execution — username and CI repaired, 2026-10-05

Latest attachment 36a1ce44 is byte-identical to the already integrated guide
(SHA-256 85e1f947e5c9a77d0d1d311478be4989021caafbfe56b263a034d29a355cff20).
Guide import committed as 40a9a1b. Username repair committed/pushed as 2334858;
full flake check exit 0, workstation-smoke output exactly 1anhzd1q0pby5zy8qzyr6lf9spr5a0sb,
desktop exactly accepted czk5a2wn8di3pgv8a6w0b8aj3286g3h3. Successful VM output
was reused, not re-executed. Logs: /tmp/readiness-username-{fast,smoke,desktop}.log.
2976771 switches feature CI to PRs with main-only push, retaining concurrency.
Current-status documentation corrected without rewriting historical evidence.
Backup destination requested; code preparation continues independently. No
physical reboot, live activation or graphical/cooling restart performed.

## Readiness execution — storage packaging and data interface, 2026-10-05

PR #7 is draft and Flake checks passed at 4c81db7 (run37334007796).
05d7119 groups both storage features with helpers; source scripts byte-identical.
Initial guard basename changed the system closure; builtins.path preserves the
accepted maintenance-guard.sh store identity. Final fast checks pass and desktop
exactly czk5a2wn8di3pgv8a6w0b8aj3286g3h3. da2f1c7 moves scrub host schedule back
to desktop and adds counterpart assertions; fast checks pass and exact desktop
closure remains unchanged. Logs /tmp/readiness-storage-*-final.log and
/tmp/readiness-maintenance-{fast,desktop}.log.

Reset data interface replaces textual/code substitutions with escaped scalar
assignments and allowed_descendants array; Bash owns exact descendant matching.
Source ShellCheck passes. Fast session78939 and sequential heavy session43910
are pending, not acceptance. Heavy uses max-jobs1/cores2; original unbounded
invocation cancelled before completion and restarted with bounded concurrency.
CPU briefly sampled81C while the user's game and evaluation were active;
background Nix clients lowered to nice19, later sampled69C, cooling active.
No user game/session or cooling process was stopped.

User explicitly selected existing Ventoy USB for backup. Verified UUID1BF6-1635,
40,245,919,744 bytes initially free. Additive home snapshot home-ventoy-20261005
created. Backup under NixosConf-backups/2026-10-05 includes all home plus engine
source/assets; excludes installed engine ZIP and engine Binaries/Intermediate/
DerivedDataCache directories (1481 excluded paths recorded privately). Included
logical size50,244,561,937 bytes/348166 files, compressed with one zstd thread.
4GiB free-space reserve enforced; archive integrity/hash and representative
restore still pending in session50539. No secrets outside home included; user's
existing separately held secret backup is not a newly tested encrypted restore.
Private inventory/exclusions/runner receipts: /persist/nixos-ventoy-backup-20261005.
Ventoy boot files/partitioning left intact; no format, delete or physical reboot.

## Readiness execution — test subsystem, 2026-10-05

Reset-interface fast checks completed exit0; root VM matrix remains running.
Built reset-interface desktop grii8zp9miayx0747i1lvr6r91jzmyr6. Version-level
closure diff vs accepted czk is empty; generated initrd/system identities change
because the data interface changes rendered script. No physical acceptance claim.

Tests now have explicit tests/default.nix registry, workstation/hardware/storage
subdirectories, shared ephemeral-root harness and semantic scenario filenames.
Semantic output names added; all historical checks/package aliases preserved.
Root flake delegates detailed validation and remains the input/configuration
entry point. Full fast checks exit0 including hardware-free Python7tests.
Workstation-smoke reproduces1anhzd1q0pby5zy8qzyr6lf9spr5a0sb; built desktop
remains grii8zp9miayx0747i1lvr6r91jzmyr6 for this source-only reorganization.
Logs /tmp/readiness-test-registry-{fast,desktop-smoke,format}.log.

## Readiness execution — native safeguards and backup scheduling, 2026-10-05

Recovery image move aebae83 reproduces exact d55 ISO. Commander cleanup1613e19
requires all policy arguments, passes watchdog seconds from one Nix constant,
retains validation and adds Ruff format checking. Eight hardware-free tests,
config check and unchanged workstation-smoke pass. Initial hysteresis fixture
still relied on removed defaults; corrected to explicit test-only policy.
01e019b adds shell syntax/ShellCheck checks as system.checks dependencies and
reuses them in flake checks. Full current fast checks passed.

Named activation guards now inspect /persist mount, root-owned0600/nonempty/
non-aliased password source, ESP mount/free reserve and Btrfs topology. They
never delete/reset subvolumes. ESP reserve256MiB based on largest installed
initrd45,631,321bytes and3,948,449,792bytes free. Hardware-free fixture suite
45cases passes. Generated preSwitchChecksScript executed directly read-only on
this host with dry-activate arguments and exit0; no native host activation.
Native action VM pending; its first failure was harness default disabling
system.switch.enable, corrected explicitly, and stderr now captured for refusals.
Built candidate normal l994fn5hpd2g2rijyffprl4368587m5w and persistent
cxc50rmb8i6akb62fcvzz3xkszzqf895; these are NOT physically accepted.

Stock control rejects four project-owned namespaces with native forbidden
closure checks. Negative build now fails specifically for included
8ii33j1vxfgl9z2gs954jbiwppsrhhlf-nixos-opt-pgo-fixture. Initial grouped regex
exposed upstream unquoted shell interpolation; switched to four plain patterns.
An empty probe dropped out of buildEnv closure; corrected to a retained bin file.
Positive candidate normal/persistent builds succeed. No optimization introduced.

USB writeback made host sgdisk's global sync wait (confirmed kernel stack), not
an initrd/VM test failure. Compressor PID521504 temporarily SIGSTOP'd to drain
about3GiB dirty pages; partial backup retained, not verified. Supervisor session12930
resumes it automatically when root-matrix Nix PID527727 exits. Root matrix
session43910 continues; backup session50539 remains unfinished. Do not forget
resume/terminal verification or claim external restore before receipt exists.
User graphical session, game and Commander Core remain running. No host reboot.

## Readiness execution — activation accepted in VM, reconstruction prepared, 2026-10-05

Native activation action VM now passes, output
/nix/store/zwbjrn73wajchh8360m4lb7d5iz1lf62-vm-test-run-activation-safety-actions.
It exercises test/boot/switch/dry-activate refusal and success using native
switch-to-configuration; bootloader writer is intentionally test-only. No
physical host action was invoked. Earlier harness-disabled switch binary and
uncaptured stderr were corrected; rejected runs are not acceptance evidence.

Blank-disk reconstruction is registered as an explicit heavy package. It
reuses actual desktop Disko/workstation/Home Manager contracts with virtual
disk/cooling/test-agent overrides, creates a96GiB sparse target, seeds a
fixture-only secret at the production path and installs pinned closure/UEFI.
Installed QEMU boots disk/UEFI only, with no host store/kernel/initrd. It tests
two normal resets and persistent-root retention. Evaluation and full flake
checks pass, but actual execution is still required. Do not mark this gate done.
An initial duplicate Nix attribute in installer Disko setup was fixed before
successful evaluation. docs/reconstruction.md describes precise scope.

External bootstrap-secret Model A documented in docs/bootstrap-secrets.md;
new encrypted framework is unnecessary for this baseline. User was asked for
existing encrypted backup location/key method for a restore check, without
requesting secrets/passwords in chat. Fresh encrypted restore remains open.
User's explicit Ventoy backup choice supersedes the guide's older no-USB-target
recommendation; no-format/no-erasure preservation remains mandatory.

Btrfs coordination counterpart evaluation test added: one valid control and
three disabled/missing counterpart refusals; execution pending at this record.

## Readiness execution — exclusion audit and final preparation checks, 2026-10-05

Latest full preparation flake check exits0, including new maintenance-config
control/refusals. Reconstruction now also checks credential equality, persistent
journal, return to normal after recovery and read-only installer inspection of
all expected subvolumes. Its VM execution remains queued behind backup completion
(session75533); implementation/evaluation is not reconstruction acceptance.

Engine exclusion audit compared26000 binary files to retained distribution ZIP
by size/CRC; all matched, with no read errors.47 additional/different binary-area
files (1,508,851bytes total) were independently archived on Ventoy and all47
restored/hash-compared successfully. Supplement569761bytes; root-private
engine-exclusion-audit.json and supplement-receipt.json under backup receipt dir.
CRC comparison establishes equality to local ZIP, not vendor authenticity.
Generated intermediate/cache directories and installation ZIP remain excluded.
Main home archive/representative restore still pending; supplement alone is not
full home acceptance. Snapshot was taken without application quiescence.

Two candidate GC roots added (readiness-guards-candidate and
readiness-guards-persistent); all13 roots verified, no earlier root retired.
Completed preparation logs preserved root-owned0600 under
/persist/nixos-readiness-20261005. Root-matrix log/receipt must be preserved only
with terminal status; currently final safety VM running. Backup resumes when
that Nix process exits. No physical activation/reboot or final-baseline claim.

## Readiness execution — user confirmations, 2026-10-05

This record supersedes earlier open secrets-restore and firmware-choice gates.

- [x] Separate `/persist/secrets` backup and restore: the user confirms this
  was already performed during recovery from an actual system failure. Evidence
  is user-reported successful recovery, not a fresh agent-run restore. Private
  location/hash/key method were not collected. Do not repeat this completed gate.
- [x] Firmware decision: retain BIOS 3201/current ME. No update is planned.
  VMX enablement and stability validation remain open. No reboot is triggered.
- [x] Five reset scenarios passed; session43910 exited0: safety
  `22h49w4jvsvywvcj5bcybl0600ksr5qq`, interrupted recovery
  `mbm4m0f5l1hffdifgg0ldwzb1f2bd28p`, reset control
  `00viicfiafzw6ys40yqq1zlix2zmb38w`, persistent identity
  `b0hr6yij7b07sap4jrflfbr7jvj6hh01`, fallback
  `4wgixv6kb41hbxppkkigk4fz8n77vlrw`. Terminal log preserved under
  `/persist/nixos-readiness-20261005`.
- [~] Ventoy compressor resumed after reset tests. Main archive and restore
  remain pending until the verification receipt exists.
- [~] Reconstruction remains queued behind verified backup. Installer root
  uses unique virtio-root identity to avoid the target's duplicate nixos label.

No live activation, reboot or graphical-session interruption occurred.

Reconstruction preflight corrected Disko invocation to its executable store
path: pinned makeScriptWriter exposes a direct executable symlink, so appending
/bin/disko was invalid. Runtime acceptance remains pending.

Corrected reconstruction evaluates successfully to
`8fqjrlw2v2q61579lr1y2lqlkgrry0lr-vm-test-run-blank-disk-reconstruction.drv`.
Evaluation is not runtime acceptance.

## Readiness execution — retained-firmware storage observation, 2026-10-05

Read-only NVMe/Btrfs receipts were captured under root-private
`/persist/nixos-readiness-20261005`. Critical warning0, media errors0,
spare100%, wear18%, temperature315K (about42°C), warning/critical temperature
time0. Cumulative error-log entries12143 versus earlier12137; retained newest
entry is admin queue0, status0x2002, parameter offset40, LBA/namespace0.
This does not explain every historical error; storage acceptance remains open.
Unsafe shutdown count2214 is recorded, not dismissed. Btrfs device counters
all0; last scrub finished2026-10-04 with no errors. No new scrub or Nix store
content verification ran while backup/game were active. No current-boot kernel
matches for the captured NVMe/Btrfs error patterns. Backup runner and exclusion
audit scripts preserved root-private alongside receipts for reproducibility.

Firmware and backup runbooks now explicitly reflect the user's retained
BIOS3201/currentME choice and completed real secrets recovery; older conflicting
recommendations in the historical ledger are superseded, not silently erased.

## Readiness execution — loaded pressure interval, 2026-10-05

Read-only55-second sample while user's existing Proton game and USB backup
continued: MemAvailable26,371,032→26,488,752KiB; occupied disk swap about4.5GiB;
pswpin+4904 pages, pswpout0, major faults+2159, OOM kills0. Memory PSI some/full
avg10 ended0.01%, avg60 0.04/0.03%; GPU IRQ159 delivered42945 interrupts onCPU7.
This is preparation after VM tests, not controlled idle or exact final-candidate
acceptance. Timer/function-call distribution is not proof device IRQs are
balanced. Retain current zram/irqbalance settings pending representative final
workload evidence; no tuning occurred. Full private before/after receipt and
collector script preserved under `/persist/nixos-readiness-20261005`.

Optional isolated Facter adoption is consciously deferred for this baseline:
existing explicit hardware configuration remains reviewed and tested; no
identified hardware-provenance defect requires changing that framework. This
optional experiment does not replace required physical hardware validation.

PR CI37343573400 was cancelled by the newer push's configured concurrency;
replacement37343814838 validates b4a1584 and is still running at this record.
This is not a check failure or acceptance of an unfinished run.

## Readiness execution — reconstruction driver preflight, 2026-10-05

Custom installed-disk guest now starts with allow_reboot=True: pinned test
machine driver otherwise adds -no-reboot, which would terminate QEMU at the
first reboot and invalidate the normal/recovery/normal sequence. Final
read-only layout inspection now covers all seven production subvolumes,
including @snapshots. Disko's direct executable uses its noninteractive legacy
destroy implementation and is restricted to the blank virtual target; no
physical disk command is executed. Corrected test evaluates successfully to
`1l6h8zxp25wmifd2bacl006p4lcwb491-vm-test-run-blank-disk-reconstruction.drv`.
Runtime acceptance remains queued, not proven. Documentation reflects full
credential/journal/return-normal/layout checks. No physical reboot occurred.

## Readiness execution — candidate closure review, 2026-10-05

Accepted normal closure `czk5a2wn8di3pgv8a6w0b8aj3286g3h3` was compared with
uninstalled candidate `l994fn5hpd2g2rijyffprl4368587m5w`; both are
`nixos-system-desktop-26.05.20261004.0d9e9b8`. Current source dc668d0 still
evaluates to that exact candidate. Persistent counterpart is
`cxc50rmb8i6akb62fcvzz3xkszzqf895`.

Closure sizes: 16,985,654,488 → 16,985,659,544 bytes (+5,056). No package-version
transitions are reported. Membership: 2,207 → 2,208 paths, with12 added/11
removed. All changes are generated etc/system units, Commander keeper source
and wrapper/unit, initrd, normal/persistent system outputs, pre-switch checks
and the new workstation activation checker. Kernel store path is identical
(`na8n3qdqf1fs7lwads81ra9nlh1hqc9w-linux-6.18.55`).

Material explanations: explicit Bash reset data interface changes initrd;
required Commander policy arguments and derived watchdog change keeper/unit;
named read-only activation prerequisites change pre-switch checker and switch
references. Top-level activate/prepare-root/boot metadata references follow the
new system identities. No compiler optimization or dependency refresh occurred.
The forbidden stock namespaces and build checks are build-time protections.

Private closure membership and recursive system-output differences are retained
under `/persist/nixos-readiness-20261005`. This is preparation review, not
physical acceptance or the final freeze comparison. Both old and candidate
closures remain GC-protected; no installation or profile replacement occurred.

## Readiness execution — published preparation CI accepted, 2026-10-05

GitHub run37344821840 completed successfully for exact source
`4e9e6a312cd786a18a8be326928a9a956ae2b43b`. Flake checks include current
reconstruction evaluation/preflight and source formatting checks; the heavy
reconstruction package is not executed by CI. Earlier superseded runs cancelled
by workflow concurrency are not failures or substitutes for this terminal result.

Live backup processes521492/521503/521504 remain active; archive is about20GB
and increasing, with no logged pipeline error. Queued reconstruction supervisor
730405 remains live and requires the verified backup receipt before starting.
No backup completion, restore acceptance, physical activation or reboot is
claimed from this checkpoint. Worktree was clean before this ledger update.

## Continuation reviews adopted — 2026-10-05

User request: read, record both attached reviews, then follow their applicable
instructions. The reviews describe snapshot75a649c; current live state takes
precedence over stale status claims. Full source texts are retained below.
Immediate tasks: exact-desktop reconstruction via extendModules; workstation
activation-safety namespace/location plus deliberate prerequisite assertions;
fixed Ubuntu/action SHA pins; README docs tree correction; execute reconstruction
after verified Ventoy backup. No generic host framework or broad refactor.
Facter comparison is isolated/non-blocking, superseding the earlier conscious
deferral as an experiment to revisit after reconstruction. Generated option
docs are low-priority optional work. Distributed builds, optimization matrices,
dependency grafting, signed cache, offline full build closure and remote
deployment are future experiments, not baseline requirements. Preserve inert
optimization and persistent home/var. Defer docs moves, plan archival and
compatibility/store-basename/VSCode cleanups until after the baseline tag.

### Attached source: Architecture and maintainability review

Source: `/home/p2949/.codex/attachments/142886c5-3b74-483a-8b84-721ae344eaf6/Pasted text.txt`
SHA-256: `d261b8b667a2b5d00f11acbefe800caada6973db53ed4f2607564a43a8a9e05d`

> I took another fresh pass over the **current** `feat/pre-optimization-readiness`, rather than using the previous `c15a175` review as the answer.
>
> The branch has moved substantially. It is now at **`75a649ca15fe876f4e6a62c9d933338454dd1546`**, with the latest commit recording successful preparation CI and a backup checkpoint.  PR #7 is open as a draft against `main`, with **23 commits and 54 changed files**.   I also checked the current PR-head workflow run: the Nix checks are succeeding.
>
> The biggest change in my assessment is this:
>
> > **Most of the architectural cleanup I previously recommended is now finished. I would stop looking for broad ways to make the repository “more modular.” There are only a few real structural improvements left; beyond them, further abstraction will make this one-host config harder to understand rather than easier.**
>
> ## Current state
>
> | Area | Fresh assessment |
> |---|---|
> | `flake.nix` | **Good now.** Thin enough; validation is delegated. |
> | `tests/` | **Good.** Proper subsystem and semantic organization. |
> | Storage modules | **Good.** Feature directories and implementation co-location are in place. |
> | Ephemeral-root Nix/Bash boundary | **Good.** Nix now supplies data; Bash owns logic. |
> | Btrfs maintenance ownership | **Good.** Host owns schedule; module owns mechanism. |
> | CI branch policy | **Fixed.** Main push + PR is the right model. |
> | Recovery ISO | **Fixed.** Correctly lives under `images/`. |
> | Username source of truth | **Fixed.** Smoke test consumes the flake username. |
> | Commander Core | **Fixed.** Python policy defaults removed; watchdog centralized. |
> | Current-status docs | **Much better.** `docs/status.md` exists. |
> | Stock contamination control | **Good.** Explicit project namespace + negative test. |
> | Activation safety | **Implementation good; ownership/naming could improve.** |
> | Blank-disk reconstruction | **Very good test, but duplicates production assembly. This is now the biggest maintainability issue.** |
> | Documentation tree | **Starting to get crowded.** Final cleanup should happen after baseline freeze. |
> | `plan.md` | **Huge but still operationally useful. Archive after readiness.** |
>
> The root flake is a particularly good improvement. It now essentially defines inputs, package sets, development shells, the validation registry and the two NixOS configurations; the old wall of test registrations is gone.  `tests/default.nix` has become the single validation registry, while the actual tests are organized by workstation/hardware/storage concern.  I would **not split that registry further yet**.
>
> ### The highest-value remaining refactor: stop reconstructing the desktop configuration twice
>
> This is the strongest fresh recommendation.
>
> Your production desktop is constructed in `flake.nix` with Disko, Home Manager, Impermanence, the desktop host, shared `specialArgs`, and the Home Manager user integration.
>
> But `tests/storage/ephemeral-root/reconstruction.nix` independently rebuilds nearly the same composition:
>
> ```nix
> installed = inputs.nixpkgs.lib.nixosSystem {
>   specialArgs = { ... };
>
>   modules = [
>     inputs.disko.nixosModules.disko
>     inputs.home-manager.nixosModules.home-manager
>     inputs.impermanence.nixosModules.impermanence
>
>     ../../../hosts/desktop
>
>     # recreated Home Manager integration,
>     # stateVersion, fixture overrides, ...
>   ];
> };
> ```
>
>
>
> That creates a subtle but important drift risk:
>
> ```text
> real desktop composition
>         │
>         ├── changes later
>         │
>         ▼
> reconstruction fixture may silently remain on old composition
> ```
>
> And this particular test is supposed to prove something stronger than almost every other test:
>
> > the actual workstation definition can reconstruct the machine from a blank disk.
>
> So it should consume the **actual desktop system definition**, not reconstruct a close approximation of it.
>
> I would first try using the existing NixOS configuration's `extendModules` support. Conceptually:
>
> ```nix
> desktopSystem = inputs.self.nixosConfigurations.desktop;
>
> installed = desktopSystem.extendModules {
>   modules = [
>     ({ lib, modulesPath, ... }: {
>       imports = [
>         (modulesPath + "/testing/test-instrumentation.nix")
>         (modulesPath + "/profiles/qemu-guest.nix")
>       ];
>
>       disko.devices.disk.main.device = lib.mkForce diskDevice;
>
>       hardware.commanderCore.enable = lib.mkForce false;
>
>       # Other fixture-only overrides...
>     })
>   ];
> };
> ```
>
> Then `tests/default.nix` can receive `desktopSystem` rather than merely `desktopConfig`.
>
> If `extendModules` produces an undesirable recursion/evaluation issue in this flake, the fallback I'd use is a **desktop-specific constructor**, for example:
>
> ```text
> hosts/desktop/system.nix
> ```
>
> used by both the flake and reconstruction test.
>
> I still would **not** build a generic `mkHost`, `mkSystem`, host framework, or giant `lib/`. Two consumers now genuinely need the exact same desktop assembly, so factoring *that specific assembly* has become justified.
>
> The workstation smoke test should remain different. Its purpose is deliberately to test the reusable workstation profile/Home Manager without physical Disko, Commander Core or destructive root-reset behavior.
>
> ## `activation-safety` is now in the wrong architectural category
>
> The implementation itself looks good. You have four named pre-switch checks, and the shell implementation is read-only and defensive.
>
> But this:
>
> ```text
> modules/storage/activation-safety/
> ```
>
> is no longer an accurate description.
>
> The module validates:
>
> ```text
> /persist mount
> password credential backing file
> ESP free space
> Btrfs/root topology
> ```
>
> Only about half of that is storage.
>
> Likewise:
>
> ```nix
> boot.workstationActivationSafety
> ```
>
> isn't really a boot option. It controls `system.preSwitchChecks`.
>
> I'd use something like:
>
> ```text
> modules/
> └── workstation/
>     └── activation-safety/
>         ├── default.nix
>         └── check.sh
>
> tests/
> └── workstation/
>     └── activation-safety/
>         ├── guard.nix
>         ├── actions.nix
>         └── test_guard.py
> ```
>
> with an option namespace such as:
>
> ```nix
> workstation.activationSafety = {
>   enable = true;
>   espReserveBytes = 256 * 1024 * 1024;
> };
> ```
>
> This isn't urgent for correctness, but it would make the taxonomy more truthful.
>
> While touching it, I'd also make its configuration prerequisites explicit. The module currently assumes the selected user has a `hashedPasswordFile`, `/boot` exists, and the ephemeral-Btrfs-root configuration exists.  Those assumptions are true for your desktop, but reusable modules are easier to maintain when an invalid composition generates a deliberate assertion like:
>
> ```text
> workstation.activationSafety requires:
> - ephemeral Btrfs root enabled
> - concrete /boot filesystem
> - configured hashedPasswordFile
> ```
>
> rather than eventually producing an obscure missing-attribute evaluation failure.
>
> ## CI is structurally correct now; make it reproducible
>
> The stale feature-branch trigger from my previous review is gone. The workflow now correctly runs on pushes to `main` and on pull requests.  That's the model I would keep.
>
> There is one remaining improvement I'd make for a repository that is going to be used for controlled optimization experiments: reduce mutable CI infrastructure.
>
> Currently:
>
> ```yaml
> runs-on: ubuntu-latest
>
> uses: actions/checkout@v7
> uses: cachix/install-nix-action@v31
> ```
>
>
>
> I would use a fixed runner generation such as `ubuntu-24.04` and pin the two actions to full commit SHAs, with comments indicating the corresponding release. A Dependabot config can update those pins later if you want automation.
>
> Nix makes your *build inputs* reproducible; pinning the GitHub Actions layer makes the machinery that launches those builds less mutable too.
>
> I wouldn't make CI substantially more complicated than that. In particular, I still wouldn't put the multi-reboot VM suite or blank-disk reconstruction into every PR run.
>
> ## The new storage architecture is essentially finished
>
> The previous home-grown token templating has been removed. `ephemeral-btrfs-root/default.nix` now injects escaped values and an array, then reads ordinary Bash.  `reset.sh` itself owns the descendant-membership logic and destructive procedure.
>
> That's the right boundary:
>
> ```text
> Nix
>   typed configuration
>   escaping
>   systemd wiring
>        ↓
> Bash
>   procedural reset implementation
> ```
>
> I would leave this architecture alone.
>
> The same applies to Btrfs maintenance. Its module now asserts that automatic GC and the `/` scrub exist, while owning only coordination/ordering and the guard.  The desktop owns the actual monthly scrub policy.
>
> That's exactly the host-policy/module-mechanism division I'd recommend.
>
> There is one deliberate bit of transitional baggage:
>
> ```nix
> guardSource = builtins.path {
>   path = ./guard.sh;
>   name = "maintenance-guard.sh";
> };
> ```
>
> with the comment that this preserves the accepted store identity.
>
> I would **not change that before the baseline freeze**. After the baseline project is complete, you can decide whether preserving that historical store basename is still worth the oddity.
>
> ## Your experimental-control layer is in good shape
>
> `stock-control.nix` is deliberately tiny:
>
> ```nix
> system.forbiddenDependenciesRegexes = [
>   "-nixos-opt-cpu-"
>   "-nixos-opt-lto-"
>   "-nixos-opt-pgo-"
>   "-nixos-opt-bolt-"
> ];
> ```
>
>
>
> And you've done the important part I cared about: there is an explicit negative system containing a named PGO fixture.  The documentation also correctly notes that a failure for an unrelated reason doesn't prove the contract and that `system.extraDependencies` is outside this check.
>
> I would leave `modules/core/stock-control.nix` where it is for now. Creating a `research/`, `experiments/`, or `controls/` hierarchy for one eleven-line module would be architecture theatre. Once the actual optimization framework contains several related control modules, *then* it may warrant its own namespace.
>
> And `optimization/default.nix` is still inert. Keep it that way until the stock baseline tag exists.
>
> ## Documentation has improved, but is now the next organizational pressure point
>
> `docs/status.md` fixes the most serious problem from the last review. It clearly separates the accepted physical system from the current implementation line and current open gates.
>
> That's good.
>
> But the actual `docs/` directory now contains a substantial set of documents—activation safety, backup/restore, baseline capture, bootstrap secrets, closure review, development validation, firmware preparation, Impermanence, maintenance, persistence, physical validation, reconstruction, stable refresh, status, stock control and more.
>
> Meanwhile the README's repository tree still effectively presents:
>
> ```text
> docs/
> └── baselines/pre-optimization/
> ```
>
> which no longer describes the docs architecture very well.
>
> I would make the **README correction now**, but defer actually moving all those documents until the readiness project is finished. Cross-linking a dozen live documents while `plan.md` is actively recording evidence creates churn for little current benefit.
>
> After the baseline freeze, I'd move toward:
>
> ```text
> docs/
> ├── status.md
> ├── design/
> ├── runbooks/
> ├── validation/
> ├── baselines/
> └── history/
> ```
>
> At the same time, archive `plan.md`. It is now roughly **283 KB** at the repository root.  It has served its purpose well as a forensic execution ledger, but once the tag exists, it should become historical evidence rather than the main project-navigation document.
>
> ## A couple of deliberately small cleanups remain
>
> VS Code is still under `home/p2949/desktop/default.nix` as “Work”, while the development module owns clang tooling and Nix formatting.   Moving VS Code to development would be semantically cleaner, but it is very low priority.
>
> The old flake package aliases such as:
>
> ```nix
> impermanence-root-test-a = reset-control;
> impermanence-root-test-b = persistent-identity;
> ```
>
> are also still present.  I think keeping them while `plan.md` and historical commands still refer to A/B is sensible. Once the plan is archived and the semantic names are the documented interface, remove the aliases and the `rec` package set can probably become an ordinary attrset.
>
> Your system package ownership has also reached a sensible state: system/recovery utilities remain system-wide, while interactive CLI tools have moved to Home Manager.   I would stop moving packages around unless actual usage exposes a bad owner.
>
> ## What I would implement from here
>
> 1. **Make blank-disk reconstruction derive from the exact real `desktop` NixOS configuration**, preferably with `extendModules`; this is the one architectural issue I consider genuinely important now. Then execute that reconstruction test, because `docs/status.md` still correctly lists it as an open gate.
> 2. **Rehome and rename `activation-safety`** to a workstation/system-safety concern and add explicit module assertions for its prerequisites. Keep the current shell implementation together rather than splitting its four roles into four tiny scripts.
> 3. **Make CI infrastructure slightly more deterministic**: fixed Ubuntu runner plus commit-pinned GitHub Actions. Keep the current simple main/PR trigger model.
> 4. **Correct the README's repository/docs representation now**, but postpone the large `docs/` directory reorganization and `plan.md` archival until the pre-optimization baseline is actually complete.
> 5. **After the final baseline tag**, remove transitional compatibility baggage: A/B flake aliases, any store-name-preservation hacks you no longer value, archive the execution ledger, and do tiny semantic cleanups such as moving VS Code. Then stop refactoring and create the fresh optimization branch.
>
> The target architecture is therefore no longer dramatically different from what you already have. The repository has reached the point where **stability of the architecture is itself a maintainability feature**. Your host/profile/core/desktop/Home Manager split, storage modules, test registry, recovery image, CI model, custom hardware module, and experimental contamination controls are all at a level where I would actively resist adding flake-parts, flake-utils, a generic host framework, overlays for their own sake, or another layer of module aggregation.
>
> At this point, the more important remaining work is the readiness work already recorded in `docs/status.md`: blank-disk reconstruction execution, the current backup/restore work, hardware/VMX and sustained stability gates, exact-candidate workload acceptance, and the soak.  Those will improve the quality of the eventual optimization baseline much more than another round of broad Nix refactoring.

### Attached source: NixOS feature and readiness review

Source: `/home/p2949/.codex/attachments/ec8e48c1-3c13-4d5c-a3ce-f07ed96fe37d/Pasted text.txt`
SHA-256: `daac048824eaab83bc6bbc0985723670b9d3c52582b34f932049ac3b5c9af7cb`

> I took another fresh look at the live branches. The answer has changed substantially again.
>
> `feat/pre-optimization-readiness` is now at `75a649ca15fe876f4e6a62c9d933338454dd1546`, and PR #7 is an open draft with 23 commits and 54 changed files. The old `feat/optimization-framework` is still untouched at `397a8c7`, so I would continue treating it as historical prototype code rather than the base for new work.
>
> The biggest conclusion is: **you have now implemented nearly all of the high-value NixOS-native features I previously suggested.** The genuinely interesting “what should I try next?” list is getting much shorter.
>
> ## What you have already implemented
>
> These are no longer recommendations:
>
> | Feature | Current state |
> |---|---|
> | Flakes | extensively used |
> | Home Manager as NixOS module | used |
> | Disko | used |
> | Impermanence | extensively tested |
> | Ephemeral Btrfs root | custom implementation + VM/physical testing |
> | Specialisations | `persistent-root` |
> | NixOS integration tests | extensive |
> | Multi-boot tests | extensive |
> | Recovery ISO | declarative and moved to `images/` |
> | Custom typed NixOS modules | extensive |
> | `system.checks` | **implemented** |
> | `system.preSwitchChecks` | **implemented** |
> | `system.forbiddenDependenciesRegexes` | **implemented** |
> | Negative closure-contamination test | **implemented** |
> | Blank-disk reconstruction test | **implemented, execution still pending** |
> | Test registry outside `flake.nix` | **implemented** |
> | CI via feature PR | **implemented** |
>
> Your `flake.nix` has become pleasantly small again: validation is delegated to `tests/default.nix`, while the flake mostly contains actual top-level outputs.  The test registry now separates cheap checks from explicit heavier artifacts such as reconstruction, activation testing and multi-boot Impermanence scenarios.
>
> You also genuinely implemented `system.checks`, rather than merely having equivalent flake checks. Both the ephemeral-root module and Btrfs-maintenance module make their source checks dependencies of the NixOS system build.
>
> And your activation guard is now a proper NixOS mechanism:
>
> ```text
> system.preSwitchChecks
> ├── persistence
> ├── credentials
> ├── esp
> └── topology
> ```
>
>
>
> The stock-control idea is implemented too:
>
> ```nix
> system.forbiddenDependenciesRegexes = [
>   "-nixos-opt-cpu-"
>   "-nixos-opt-lto-"
>   "-nixos-opt-pgo-"
>   "-nixos-opt-bolt-"
> ];
> ```
>
> with a deliberately contaminated NixOS system that should fail construction.
>
> That's a particularly strong foundation for the optimization project.
>
> ---
>
> # Before adding anything else: actually run the reconstruction test
>
> This is now my **#1 recommendation**, but it's no longer an implementation task.
>
> Your blank-disk test is much better than the conceptual version I previously suggested. It actually:
>
> ```text
> empty qcow2 disk
>     ↓
> real Disko layout
>     ↓
> test-only bootstrap secret
>     ↓
> nixos-install
>     ↓
> systemd-boot/UEFI
>     ↓
> installer shuts down
>     ↓
> new QEMU instance boots from installed disk
>     ↓
> NO host Nix store mount
> NO supplied host kernel
> NO supplied host initrd
>     ↓
> normal ephemeral-root boot
>     ↓
> reboot
>     ↓
> root reset verified
>     ↓
> persistent-root specialisation
>     ↓
> root retained
>     ↓
> normal boot again
>     ↓
> root resets
>     ↓
> offline read-only filesystem inspection
> ```
>
>
>
> That's excellent.
>
> But your current status still says **executed blank-disk reconstruction remains open**.  PR #7 says the same thing.
>
> So I would not spend time inventing another major NixOS reliability feature before running:
>
> ```bash
> nix build .#blank-disk-reconstruction --print-build-logs
> ```
>
> That test is now one of the strongest pieces of NixOS-specific infrastructure in the repository. Proving it actually passes is worth far more than adding another module.
>
> ---
>
> # 1. NixOS Facter
>
> This remains the clearest **major NixOS 26.05 feature you genuinely haven't explored yet**.
>
> Facter generates a hardware report and allows NixOS to derive configuration for:
>
> - architecture;
> - firmware;
> - CPU microcode;
> - initrd modules;
> - graphics;
> - networking;
> - Bluetooth;
> - virtualization;
> - some other detected hardware.
>
>
>
> What makes it particularly suited to your repository is its built-in comparison tooling:
>
> ```text
> hardware.facter.debug.nvd
> hardware.facter.debug.nix-diff
> ```
>
>
>
> I would not immediately adopt it. Do this as an isolated experiment:
>
> ```text
> current hardware-configuration.nix
>           │
>           │ compare
>           ▼
>       facter.json
>           │
>           ▼
> Facter-derived NixOS configuration
> ```
>
> Generate the report:
>
> ```bash
> sudo nix-shell -p nixos-facter \
>   --run 'nixos-facter -o facter.json'
> ```
>
> and evaluate a temporary configuration containing:
>
> ```nix
> hardware.facter.reportPath = ./facter.json;
> ```
>
> Then compare closures.
>
> Your existing `hardware-configuration.nix` is tiny enough that manual configuration may still win. That's fine—the interesting part is being able to determine that empirically.
>
> **Priority: 5/5 as the next genuinely new NixOS feature.**
>
> ---
>
> # 2. Distributed Nix builds
>
> This is probably the next feature that can graduate from “interesting” to **actually useful** once the optimization work begins.
>
> NixOS has first-class declarative support through `nix.buildMachines`; Nixpkgs's NixOS module generates the remote builder configuration from it.
>
> Eventually:
>
> ```text
> workstation
>     │
>     │ derivation
>     ▼
> build machine
>     │
>     ├── LLVM rebuild
>     ├── ThinLTO build
>     ├── instrumented PGO build
>     ├── optimized application
>     └── NixOS integration test
>     │
>     ▼
> store output returned
>     │
>     ▼
> workstation performs physical benchmark
> ```
>
> That distinction is especially valuable for you:
>
> > **build location should not determine benchmark location.**
>
> Keep performance measurement on the actual i5-10600K system, while expensive compilation can happen elsewhere.
>
> ### Test this the NixOS way first
>
> Don't even start with a physical second computer.
>
> Make a two-node NixOS test:
>
> ```text
> ┌────────────┐       SSH/Nix       ┌────────────┐
> │ client VM  │ ──────────────────→ │ builder VM │
> └────────────┘                      └────────────┘
>        │
>        └── prove the derivation was really built remotely
> ```
>
> You already have enough experience with `runNixOSTest` that this would be a very natural next experiment.
>
> Then later use builder features such as:
>
> ```text
> big-parallel
> kvm
> nixos-test
> ```
>
> and eventually custom capabilities for hardware-sensitive work.
>
> **Priority: 4.5/5.**
>
> ---
>
> # 3. `system.replaceDependencies`
>
> Now that your stock contamination contract exists, this becomes even more interesting.
>
> NixOS can replace an old dependency with another derivation throughout a system without doing the normal full downstream rebuild:
>
> ```nix
> system.replaceDependencies.replacements = [
>   {
>     oldDependency = pkgs.foo;
>     newDependency = optimizedFoo;
>   }
> ];
> ```
>
> This is deliberately constrained: the replacements should have the same name length and very similar layouts, and the initrd is excluded by default because replacement there is fragile.
>
> I would use this **only as an optimization research experiment**, not as your main architecture.
>
> For example:
>
> ```text
> EXPERIMENT A
>
> stock zstd
>     ↓
> normal override
>     ↓
> downstream rebuild propagation
>
>
> EXPERIMENT B
>
> stock workstation closure
>     ↓
> replaceDependencies
>     ↓
> optimized zstd graft
> ```
>
> Now you can ask:
>
> > Does this performance change come from the optimized library itself, or from the larger rebuild graph changing too?
>
> And because you now have:
>
> ```text
> system.forbiddenDependenciesRegexes
> closure review
> stock negative tests
> specialisations
> ```
>
> you have much better protection against contaminating the control system than when I first suggested this.
>
> I'd eventually create something like:
>
> ```text
> specialisation.zstd-graft
> ```
>
> and never allow it into the stock system.
>
> **Priority: 5/5 during optimization, 1/5 before the baseline.**
>
> ---
>
> # 4. Use specialisations much more aggressively for experiment matrices
>
> You technically already tested specialisations, so this isn't a *new* feature.
>
> But you've barely touched their interesting performance-testing potential.
>
> Today:
>
> ```text
> normal
> persistent-root
> ```
>
> Later I'd aim for:
>
> ```text
> NixOS generation
> │
> ├── stock
> │
> ├── cpu-codegen
> │
> ├── thinlto
> │
> ├── pgo
> │
> ├── bolt
> │
> ├── pgo-bolt
> │
> └── kernel-experiment
> ```
>
> with the important property:
>
> ```text
> same flake.lock
> same source revision
> same userspace policy
> same machine
> same persisted data
>
> only intended experiment differs
> ```
>
> Then your stock contamination module can become stage-sensitive:
>
> ```text
> stock:
>     forbid CPU/LTO/PGO/BOLT
>
> cpu-codegen:
>     permit CPU
>     forbid LTO/PGO/BOLT
>
> PGO:
>     permit selected PGO outputs
>     forbid BOLT
> ```
>
> Your current stock-control implementation is already the seed of exactly this architecture.
>
> This is probably how I would express **whole-system experimental variants** once the new optimization framework starts.
>
> ---
>
> # 5. NixOS test containers / native NixOS containers
>
> You're now using QEMU heavily.
>
> That's correct for:
>
> ```text
> UEFI
> bootloader
> kernel
> initrd
> Btrfs
> ephemeral root
> specialisations
> blank-disk installation
> ```
>
> But NixOS's test framework can also use containers. Nixpkgs explicitly distinguishes:
>
> ```text
> nodes.<name>      → QEMU machine
> containers.<name> → systemd-nspawn machine
> ```
>
>
>
> That gives you a much faster testing tier for things that don't require their own kernel.
>
> Potential candidates from your repository:
>
> ```text
> Commander Core pure systemd integration
> activation helper logic
> service dependency tests
> user/service policy
> network client/server experiments
> future optimization metadata services
> ```
>
> Not:
>
> ```text
> ephemeral root
> Disko
> systemd-boot
> initrd
> kernel experiments
> ```
>
> I'd think of it as:
>
> ```text
> unit/pure tests
>      ↓
> nspawn NixOS tests
>      ↓
> QEMU NixOS tests
>      ↓
> physical host
> ```
>
> You don't necessarily *need* it, but it's one of the remaining uniquely NixOS testing capabilities you haven't really exploited.
>
> **Priority: 3.5/5.**
>
> ---
>
> # 6. Generate your own NixOS option manual
>
> Your custom configuration has stopped being “some Nix files.”
>
> You now have real APIs such as:
>
> ```text
> boot.ephemeralBtrfsRoot.*
> boot.workstationActivationSafety.*
> hardware.commanderCore.*
> ```
>
> For example, activation-safety exposes an actual typed module interface rather than hardcoded scripting.
>
> This is now a good candidate for `nixosOptionsDoc`.
>
> Expose something like:
>
> ```bash
> nix build .#module-docs
> ```
>
> and generate reference documentation directly from the module declarations:
>
> ```text
> boot.ephemeralBtrfsRoot.enable
> boot.ephemeralBtrfsRoot.rootSubvolume
> boot.ephemeralBtrfsRoot.stagingSubvolume
> boot.ephemeralBtrfsRoot.persistenceSubvolume
> boot.ephemeralBtrfsRoot.allowedDescendants
> boot.ephemeralBtrfsRoot.logFile
>
> boot.workstationActivationSafety.enable
> boot.workstationActivationSafety.espReserveBytes
>
> hardware.commanderCore....
> ```
>
> The nice property is:
>
> ```text
> code changes
>     ↓
> module option definitions change
>     ↓
> documentation changes automatically
> ```
>
> instead of maintaining another hand-written truth source.
>
> It's not operationally important, but it's extremely NixOS-native.
>
> **Priority: 3/5.**
>
> ---
>
> # 7. Try a fully self-contained offline recovery build
>
> This is where `system.includeBuildDependencies` becomes interesting.
>
> Normally a NixOS closure contains what is required to **run** the machine.
>
> NixOS can also construct one containing what is required to **rebuild** it:
>
> ```nix
> system.includeBuildDependencies = true;
> ```
>
> That drags in sources, intermediate build dependencies, compilers and even compiler bootstrap dependencies. It is intentionally enormous, so I would never put this on the workstation normally.
>
> But as an experiment:
>
> ```text
> normal recovery ISO
>         vs
> offline-rebuild recovery ISO
> ```
>
> Then disconnect networking and ask:
>
> > Can this environment rebuild the complete target system without downloading anything?
>
> That's a very strong demonstration of Nix's reproducibility model.
>
> You could eventually create:
>
> ```text
> recovery-iso
> recovery-iso-full-build-closure
> ```
>
> and compare sizes.
>
> I would probably delete the latter after the experiment because it will be huge.
>
> **Priority: 2.5/5, mostly educational.**
>
> ---
>
> # 8. Build a real signed binary cache
>
> This one moves slightly outside pure NixOS into Nix itself, but becomes very relevant to PGO/LTO/BOLT.
>
> Once an optimized package costs 30 minutes or several hours to produce, you don't want:
>
> ```text
> successful expensive derivation
>        ↓
> GC
>        ↓
> rebuild it from scratch
> ```
>
> A proper binary cache gives you:
>
> ```text
> builder
>    ↓
> optimized store output
>    ↓
> signed binary cache
>    ↓
> workstation / CI / recovery machine
> ```
>
> The interesting part isn't merely caching—it is **cryptographic trust**.
>
> Then your experiment can record:
>
> ```text
> source commit
> derivation
> profile identity
> binary hash
> cache signature
> benchmark result
> ```
>
> This would pair extremely well with your existing fail-closed provenance philosophy.
>
> I'd do this once optimization builds actually become expensive rather than now.
>
> **Priority: 4/5 later.**
>
> ---
>
> # 9. Remote deployment with `nixos-rebuild --target-host`
>
> If you eventually put NixOS on another test machine/builder, don't manage it manually.
>
> NixOS can separate:
>
> ```text
> machine evaluating/building configuration
>               │
>               ▼
>         target machine
> ```
>
> so you can build/deploy remotely.
>
> Combined with remote builders:
>
> ```text
> control machine
>       │
>       ├── build host
>       │
>       └── target host
> ```
>
> becomes possible.
>
> For your eventual optimization lab, that could become:
>
> ```text
> main workstation
>     = benchmark target
>
> secondary machine
>     = build server
>
> laptop
>     = orchestration/control
> ```
>
> without copying `/etc` trees around.
>
> Not useful enough yet for your one-host baseline, but worth trying when a second NixOS machine becomes part of the project.
>
> ---
>
> # What I would *not* add now
>
> A fresh look actually makes me more conservative here.
>
> I would **not** currently add:
>
> - more Impermanence, especially ephemeral `/home`;
> - flake-parts;
> - flake-utils;
> - a generic host framework;
> - another custom abstraction layer;
> - NixOS containers just for the sake of containerization;
> - automatic NixOS upgrades;
> - secrets tooling merely because it exists;
> - unusual kernels;
> - more performance knobs before the stock baseline;
> - another major recovery mechanism.
>
> Your status document shows that the remaining blockers are now mostly **execution and physical validation**, not missing architecture: reconstruction execution, backup completion, VMX, hardware stability, workload acceptance and soak testing.
>
> ## My updated ranking
>
> If I separate “do now” from “interesting later,” I get:
>
> | Rank | Feature / experiment | Timing |
> |---|---|---|
> | **1** | **Execute your existing blank-disk reconstruction** | now |
> | **2** | **NixOS Facter comparison** | now, isolated/non-blocking |
> | **3** | **Distributed-build two-node NixOS test** | after baseline / early optimization |
> | **4** | **Specialisation-based optimization matrix** | optimization v2 |
> | **5** | **`system.replaceDependencies` experiment** | optimization v2 |
> | **6** | **NixOS nspawn/container tests** | whenever a suitable service test appears |
> | **7** | **Generated option documentation** | low-risk anytime |
> | **8** | **Signed binary cache** | when optimization builds become expensive |
> | **9** | **Offline closure with `includeBuildDependencies`** | curiosity/recovery experiment |
> | **10** | **Remote deployment** | once you have another NixOS machine |
>
> The important change is that I would **stop looking for additional reliability features right now**. You already built them. The more valuable next step is to prove the reconstruction test, finish the remaining physical readiness gates, tag the stock baseline, and then start a fresh optimization branch.
>
> At that point, the genuinely exciting NixOS experiments become **distributed builds + specialisations + `replaceDependencies` + your closure-contamination contracts**. Together, those can make NixOS not merely the OS hosting the PGO/BOLT project, but the actual experimental framework controlling it.


## Attached-review implementation checkpoint — 2026-10-05

Both attached reviews are preserved above in full with source hashes; quote
prefixes and trailing whitespace normalization are presentation changes only.
Reconstruction now consumes actual desktopSystem.extendModules rather than
reassembling Disko/HM/Impermanence/user policy. Evaluation reproduces exact
1l6h8zxp25wmifd2bacl006p4lcwb491 derivation before subsequent safety changes.
An initial attempt to obtain installer inputs from _module.args failed because
specialArgs are not stored there; explicit inputs parameter retained solely
for installer Disko import. No generic constructor was added.

Activation safety moved to modules/workstation and tests/workstation, namespace
workstation.activationSafety. Shell mechanism is unchanged. Assertions now
require declared ephemeral-root contract/concrete Btrfs root, concrete vfat ESP,
and selected user hashedPasswordFile. They allow persistent-root's deliberate
reset disablement. Full checks are running; negative composition coverage and
updated candidate build/runtime validation remain required.

CI uses ubuntu-24.04 and GitHub-API-resolved action commit pins: checkout v7
3d3c42e5aac5ba805825da76410c181273ba90b1; install-nix-action v31
13d8dd58da0234aa297dedd986986ccb8e7f3e24 (annotated tag dereferenced).
Main-push/PR triggers and cheap/heavy split remain unchanged. README now lists
current docs and workstation safety ownership. No docs-directory reshuffle,
plan archival, optimization activation, physical reboot or live switch occurred.

Backup archive writing finished at27,844,003,241bytes; runner521492 is still
live, waiting for writeback before integrity/restore. No verified backup receipt
exists yet and reconstruction supervisor remains queued. Do not claim completion.

First attached-review fast run passed evaluation/formatting but failed Statix's
assignment-versus-inherit rule for desktopSystem.config; changed to
inherit (desktopSystem) config. Full retry session12766 is running, log
/tmp/readiness-attached-review-fast-final.log. Initial failure is not acceptance.

## Readiness execution — activation prerequisites validated, 2026-10-05

Full attached-review refactor fast retry exited0 (session12766). New explicit
activation-safety-config check then passed normal/recovery controls, presence
of four named checks and five targeted prerequisite refusals; output
/nix/store/igfjz1lvkl6lv8y45mabiazxjpy5nfw2-check-workstation-activation-config.
It verifies assertion messages, not unrelated evaluation failure. Initial test
fixtures forced an upstream lazy diagnostic prematurely, assumed exactly four
checks despite built-in switchInhibitors, and used an empty device string
rejected by the upstream type. Fixed assertion short-circuit order, required
check membership and null device fixture respectively. These failed fixture
runs are not acceptance. Runtime guard tests remain distinct from composition.

Backup runner521492 is still draining USB writeback; dirty pages decreasing.
Main archive/restore receipt remains pending. No live service restart/reboot.

Full flake check including activation composition tests completed successfully
for source9ec351d, session44699 exit0. Terminal log retained root-private as
/persist/nixos-readiness-20261005/activation-composition-full.log. Exact desktop
output comparison is being evaluated before any activation; namespace ownership
alone is not claimed to preserve the closure without this check. USB writeback
continues to drain; archive verification receipt remains absent.

## Readiness execution — source identity and backup integrity phase, 2026-10-05

Current desktop evaluation after the safety ownership/assertion refactor still
returns exact l994fn5hpd2g2rijyffprl4368587m5w normal candidate. This verifies
closure identity rather than assuming the namespace move is operationally inert.
GitHub CI37349870726 passed for77527f8; local full checks for9ec351d also passed.
Physical acceptance remains separate.

Archive writeback finished: backup runner521492 has launched zstd integrity
verification (observed child1138116). Dirty pages drained to about3MiB with no
writeback pending. Tar reported only an ignored transient IPC socket; no saved
socket payload is required for reconstruction. Main archive27,844,003,241bytes;
SHA/representative restore and final receipt remain pending, so reconstruction
supervisor730405 still waits. No physical activation or reboot occurred.

## Unified current continuation adopted — 2026-10-05

User explicitly requested reading, recording and following this guide. It
supersedes older next-step ordering; historical records remain intact. The
reviewed77527f8 snapshot is superseded by current clean local/remote source
2ef85856f5b1438518c779b5ae757abb9d487083; main remainsf89205c. Normal candidate
identity was already verified unchanged after the safety refactor. Archive
writeback and zstd integrity have now passed; hashing/representative restore,
terminal receipt and clean unmount remain open. Reconstruction is queued.

Current execution order: exact normal/persistent build and closure receipt;
finish existing backup and clean unmount; execute reconstruction without
weakening its independence; complete offline suite and recovery-evidence/PR
reconciliation; only then batched VMX/boot installation and final physical
normal→persistent→normal acceptance; sustained hardware/storage, stock policy,
real workloads, multi-day soak, freeze/merge/tag; post-baseline historical cleanup
and fresh optimization branch. No further broad architecture work. Optional
Facter/option documentation and future experiments must not delay readiness.

The full45-section source follows. Quote prefixes and trailing whitespace
normalization change presentation only. Imported checkboxes remain source
snapshot claims, not newly verified acceptance; newer execution receipts govern.

Source: `/home/p2949/.codex/attachments/f92f3a86-b0f1-459d-a2c3-b96845975ff1/Pasted text.txt`

SHA-256: `140ad04f87747588c44ef612ea02c9185d20a27873b0b018195383c7ce756e7f`

> I re-ran the review against the **live GitHub branch**, the two new attached reviews, the earlier unified guide, the current source tree, `docs/status.md`, the current reconstruction and activation-safety implementations, PR #7, and the newest `plan.md` evidence.
>
> The most important correction to the previous guide is that the branch has moved well past `c15a175` and even past the attachments’ `75a649c`. The authoritative head at the end of this review is **`77527f8f712611ca244a2946c97c4f5c94d63ba4`**, 26 commits ahead of `main`, and PR #7 remains a mergeable draft. Its current GitHub Actions run #98 completed successfully.
>
> That changes the continuation substantially: **almost all of the architectural/readiness engineering from the previous guide is now complete**. The remaining critical path is primarily backup completion, actual reconstruction execution, physical/hardware acceptance, final workloads, soak, and baseline freeze. This agrees with both of the freshly attached reviews, which concluded that the project had reached the point where further broad abstraction would do more harm than good. Pasted text (2) Pasted text
>
> # NixOS Pre-Optimization Readiness — Unified Current Continuation Guide
>
> **Repository:** `P2949/NixosConf`
> **Active implementation branch:** `feat/pre-optimization-readiness`
> **Authoritative reviewed head:** `77527f8f712611ca244a2946c97c4f5c94d63ba4`
> **Base:** `main` at `f89205c07e4d3a77900b046a5bf937944488647b`
> **Pull request:** #7 — `Complete stock workstation pre-optimization readiness`
> **PR state:** open, draft, mergeable
> **Distance from main:** 26 commits ahead, 0 behind
> **Latest reviewed PR CI:** run #98, `Nix checks`, PASS
> **Date:** 2026-10-05
>
> ---
>
> # 1. Purpose of this document
>
> This is the current execution directive for completing `plan.md`.
>
> It supersedes older **next-step ordering**, including the earlier continuation guide written when the readiness branch was only at `c15a175`, while preserving the evidence recorded by those earlier stages.
>
> Do not delete or rewrite the historical sections of `plan.md`. They remain useful forensic evidence.
>
> This guide separates the project into:
>
> ```text
> PROVEN / COMPLETE
>     work which should not be repeated merely for reassurance
>
> IMPLEMENTED, EXECUTION GATE OPEN
>     code exists and is tested structurally, but a required heavy/physical
>     execution has not yet completed
>
> IN PROGRESS
>     a real operation is already running or has produced only partial evidence
>
> REQUIRED BEFORE BASELINE TAG
>     hard readiness gates
>
> DEFERRED UNTIL OPTIMIZATION
>     interesting work which must not expand the stock-baseline project
> ```
>
> The objective is no longer to discover more NixOS architecture.
>
> The objective is:
>
> ```text
> finish outstanding evidence
>         ↓
> prove full reconstruction
>         ↓
> freeze firmware/hardware state
>         ↓
> physically accept exact final candidate
>         ↓
> accept real workloads
>         ↓
> multi-day soak
>         ↓
> merge/tag stock baseline
>         ↓
> begin optimization-framework-v2
> ```
>
> ---
>
> # 2. Governing decision: stop broad refactoring
>
> The repository architecture has reached a sufficiently mature state.
>
> Do **not** restart broad restructuring of:
>
> - `flake.nix`;
> - `hosts/`;
> - `profiles/`;
> - `modules/core`;
> - `modules/desktop`;
> - `modules/gaming`;
> - Home Manager;
> - Disko;
> - storage modules;
> - the test registry;
> - the recovery image;
> - Commander Core;
> - the general host/profile/module split.
>
> The two newest architectural reviews independently reached this conclusion. By the `75a649c` snapshot, the flake, tests, storage modules, Nix/Bash reset boundary, Btrfs ownership, CI model, recovery-image location, username source of truth, Commander Core policy and stock contamination controls were already considered good. :chatgpt-content-reference{index="4"}
>
> Since then, even the two largest remaining architectural recommendations have been implemented:
>
> 1. blank-disk reconstruction now derives from the **actual desktop NixOS system** using `extendModules`;
> 2. activation safety now lives under `modules/workstation/activation-safety`, uses `workstation.activationSafety`, and explicitly asserts its composition prerequisites.
>
> The architecture is now itself part of the baseline. Stability of that architecture is valuable.
>
> ---
>
> # 3. Source-of-truth hierarchy
>
> From this point forward, use:
>
> ```text
> 1. Current local worktree, if clean and intentionally ahead
> 2. Current remote feat/pre-optimization-readiness
> 3. Successful validation tied to the exact source revision
> 4. docs/status.md
> 5. Exact physically accepted stable-refresh evidence
> 6. plan.md historical execution ledger
> 7. current main
> 8. old feature branches
> 9. feat/optimization-framework only as historical prototype code
> ```
>
> Never assume that a claim from an older section of `plan.md` is still current merely because it remains in the file.
>
> Prefer newer explicit statements such as:
>
> ```text
> supersedes...
> accepted result...
> current status...
> final result...
> ```
>
> while retaining the original record.
>
> ---
>
> # 4. Current Git/CI state
>
> ## Current readiness head
>
> ```text
> 77527f8f712611ca244a2946c97c4f5c94d63ba4
> Record full validation of workstation safety refactor
> ```
>
> Its parent is:
>
> ```text
> 9ec351df03139b097f43125282d552cdd099d7db
> Test activation safety composition and recovery prerequisites
> ```
>
> which follows:
>
> ```text
> 329bce51e19c0ca3b857ab0c44ea0caaf494e47b
> Adopt fresh reviews and derive reconstruction from real desktop
> ```
>
> and then:
>
> ```text
> 75a649ca15fe876f4e6a62c9d933338454dd1546
> Record successful preparation CI and live backup checkpoint
> ```
>
> The latest commit records that the full flake check including activation composition passed for source `9ec351d`; the remaining exact desktop-output comparison was being evaluated, while the USB backup writeback was still draining.
>
> ## Pull request
>
> PR #7:
>
> ```text
> Complete stock workstation pre-optimization readiness
> ```
>
> is still intentionally draft.
>
> Do not mark it ready or merge it merely because CI is green.
>
> Its role is to carry the **complete final readiness project**, including its evidence, until the stock-baseline hard gates pass.
>
> ## CI
>
> Current workflow policy is now correct:
>
> ```yaml
> push:
>   branches:
>     - main
>
> pull_request:
> ```
>
> with:
>
> ```text
> ubuntu-24.04
> actions/checkout pinned to full SHA
> cachix/install-nix-action pinned to full SHA
> ```
>
>
>
> Latest reviewed run:
>
> ```text
> run:       98
> head:      77527f8f...
> workflow:  Nix checks
> event:     pull_request
> result:    success
> ```
>
>
>
> `main` remains protected and requires `Flake checks`.
>
> ---
>
> # 5. Physically accepted reference baseline
>
> Everything still being prepared must be compared against this accepted system.
>
> ## Accepted source
>
> ```text
> c5e036b6e87d9aa77700909b508ccc0c3978d5b2
> ```
>
> ## Stable Nixpkgs
>
> ```text
> 0d9e9b832d03ac387417e16ce1febf73b2e631e1
> ```
>
> ## Normal closure
>
> ```text
> /nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8
> ```
>
> ## Persistent-root closure
>
> ```text
> /nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8
> ```
>
> ## Kernel
>
> ```text
> 6.18.55
> ```
>
> ## Recovery ISO
>
> ```text
> /nix/store/d55ny1z4d53slhz3ilvyy2mg6d8khrqn-nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso/iso/nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso
> ```
>
> Size:
>
> ```text
> 1496678400
> ```
>
> SHA-256:
>
> ```text
> 52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061
> ```
>
> The repository now correctly documents this as the accepted result rather than the older `bv3...` offline candidate.
>
> ---
>
> # 6. Physical root/reset evidence already complete
>
> Do not repeat this whole investigation unless later code actually invalidates the result.
>
> ## Original physical reset trials
>
> Three controlled physical reset boots passed:
>
> ```text
> trial 1 → root 288
> trial 2 → root 290
> trial 3 → root 292
> ```
>
> They established basic physical viability of the reset mechanism.
>
> ## Final stable-refresh policy acceptance
>
> The final accepted sequence was:
>
> ```text
> normal
>   ↓
> persistent-root
>   ↓
> normal
> ```
>
> Result:
>
> ```text
> first normal:
>     @root replaced
>     new root subvolume 295
>
> persistent-root:
>     root 295 retained
>     no additional reset-log completion
>     root-local probe survived
>     persistent probe survived
>
> final normal:
>     root 295 replaced by root 297
>     root-local probe disappeared
>     persistent probe survived
>
> machine-id:
>     stable across all variants
>
> services:
>     required core services active
>     zero failed units
> ```
>
> The current stable-refresh document records this acceptance directly.
>
> ### Interpretation
>
> The ephemeral-root architecture is no longer experimental in the sense of “has it ever worked physically?”
>
> That question is answered.
>
> The remaining physical root test is:
>
> > does the **final readiness candidate**, after the code changes made on this branch, retain the same accepted behavior?
>
> That is one final exact-candidate acceptance gate, not a restart of the entire Impermanence project.
>
> ---
>
> # 7. Ephemeral-root safety evidence already complete
>
> The reset feature has extensive automated coverage.
>
> Evidence accumulated across the project includes:
>
> - valid normal configuration;
> - valid leading-slash root selector;
> - persistent-root reset disablement;
> - invalid filesystem/device selectors;
> - unsafe subvolume names;
> - conflicting names;
> - unknown descendants;
> - nested descendants;
> - stale/malformed staging;
> - missing root/staging cases;
> - invalid persistence;
> - mounted `/sysroot`;
> - diagnostic-path symlinks;
> - broken symlinks;
> - hard links;
> - FIFOs/directories;
> - unsafe log parents;
> - misleading ` path ` substrings;
> - preservation of filesystem identity/content when reset is refused;
> - interrupted reset recovery;
> - machine-ID persistence;
> - journal persistence;
> - transition to persistent-root;
> - return to normal reset behavior.
>
> The historical safety suite reached 33 destructive-refusal cases and the configuration matrix reached 43 rejected configurations plus accepted controls before later source reorganization.
>
> The current implementation now has a cleaner Nix/Bash boundary:
>
> ```text
> Nix:
>     typed configuration
>     escaping
>     allowed-descendant data
>     systemd wiring
>
> Bash:
>     procedural reset implementation
>     descendant matching
>     validation
>     destructive reset/recovery
> ```
>
> The Nix module now injects only escaped values and an array before reading ordinary `reset.sh`; the old token/code templating is gone.
>
> The module also attaches its shell validation through real `system.checks`.
>
> Leave this architecture alone unless a test exposes a real defect.
>
> ---
>
> # 8. Btrfs maintenance work is complete
>
> Current division is now correct:
>
> ```text
> hosts/desktop:
>     whether scrub runs
>     filesystem /
>     schedule
>
> modules/storage/btrfs-maintenance:
>     GC/scrub ordering
>     overlap prevention
>     clean-scrub requirement
>     guard implementation
>     source check
>     composition assertions
> ```
>
> The module explicitly requires:
>
> ```text
> automatic Nix GC
> Btrfs autoScrub enabled
> / included in scrub filesystems
> ```
>
> and exposes its source validation through `system.checks`.
>
> Current policy remains:
>
> ```text
> Btrfs scrub:
>     first day of month
>     02:00
>     AccuracySec 1 min
>
> Nix GC:
>     Saturday 04:00
>     delete older than 30 days
>
> coordination:
>     no GC/scrub overlap
>     GC requires last scrub = finished + clean
> ```
>
> The same physically accepted maintenance policy remains documented, with one-time store verification/optimization still open as separate work.
>
> ### Transitional item
>
> The module deliberately uses:
>
> ```nix
> guardSource = builtins.path {
>   path = ./guard.sh;
>   name = "maintenance-guard.sh";
> };
> ```
>
> to preserve the previously accepted store identity.
>
> Do not clean this up before the stock baseline tag.
>
> It is harmless historical compatibility baggage.
>
> ---
>
> # 9. Repository organization work is complete
>
> The current structure now has:
>
> ```text
> hosts/
>     desktop/
>
> images/
>     recovery.nix
>
> profiles/
>     workstation.nix
>
> modules/
>     core/
>     desktop/
>     gaming/
>     compatibility/
>     storage/
>         btrfs-maintenance/
>         ephemeral-btrfs-root/
>     workstation/
>         activation-safety/
>     hardware/
>         commander-core/
>
> tests/
>     default.nix
>     workstation/
>     hardware/commander-core/
>     storage/
>
> optimization/
>     default.nix
> ```
>
> The current README now actually reflects that structure.
>
> Do not introduce:
>
> ```text
> flake-parts
> flake-utils
> generic mkHost
> generic mkSystem
> giant lib/
> automatic module registries
> one-file-per-option abstractions
> ```
>
> for this one-host repository.
>
> ---
>
> # 10. Test subsystem work is complete
>
> `flake.nix` is now appropriately thin.
>
> It contains:
>
> - inputs;
> - stable/unstable package sets;
> - username source of truth;
> - development shells;
> - validation registry import;
> - desktop NixOS system;
> - recovery NixOS system;
> - major top-level outputs.
>
> Validation details live in:
>
> ```text
> tests/default.nix
> ```
>
>
>
> The registry separates:
>
> ## Cheap checks
>
> Examples:
>
> ```text
> activation-safety-config
> activation-safety
> btrfs-maintenance-config
> btrfs-maintenance-shell
> ephemeral-root-shell
> maintenance-guard
> commander-core-config
> commander-core-python
> baseline-collector
> desktop-evaluation
> ephemeral-root-config
> formatting
> statix
> deadnix
> ```
>
> ## Explicit heavier packages/tests
>
> ```text
> blank-disk-reconstruction
> activation-safety-actions
> stock-contamination-negative
> workstation-smoke
> reset-control
> impermanence-root-safety
> interrupted-recovery
> persistent-identity
> persistent-fallback
> ```
>
> Compatibility aliases for historical names remain:
>
> ```text
> impermanence-root-test-a
> impermanence-root-test-b
> impermanence-root-recovery
> impermanence-root-fallback
> ```
>
>
>
> Keep the aliases until `plan.md` is archived.
>
> They make historical commands reproducible.
>
> ---
>
> # 11. Username source of truth is fixed
>
> The earlier half-completed username refactor described in the old guide has been repaired.
>
> The source of truth remains:
>
> ```nix
> username = "p2949";
> ```
>
> at the flake boundary.
>
> The workstation smoke test now receives it as an argument rather than independently declaring the runtime username.
>
> That previous blocker is closed.
>
> Do not reopen it.
>
> ---
>
> # 12. Recovery-image categorization is fixed
>
> Recovery is now:
>
> ```text
> images/recovery.nix
> ```
>
> rather than pretending to be a physical host under:
>
> ```text
> hosts/recovery/
> ```
>
> The flake still exposes:
>
> ```text
> nixosConfigurations.recovery
> packages.recovery-iso
> ```
>
> The contents remain intentionally secret-free and independent from the workstation's:
>
> - physical disk layout;
> - persistence imports;
> - password data;
> - Commander Core;
> - destructive reset behavior.
>
> No more restructuring is needed here.
>
> ---
>
> # 13. Commander Core source-of-truth cleanup is complete
>
> Host policy lives in Nix.
>
> Current host values include:
>
> ```text
> USB ID            1b1c:0c1c
> serial            declared in host
> base fan          60%
> high fan          100%
> pump              100%
> high temp         65 C
> low temp          60 C
> high delay        1 s
> low delay         10 s
> temp interval     1 s
> wake interval     10 s
> reset delay       3 s
> ```
>
> The Python keeper no longer owns independent policy defaults for these settings.
>
> The module now centralizes:
>
> ```text
> watchdogSeconds = 35
> ```
>
> and derives both:
>
> ```text
> watchdog margin assertion
> systemd WatchdogSec
> keeper --watchdog-seconds
> ```
>
> from that value.
>
> Existing checks cover:
>
> - Nix option constraints;
> - Python syntax;
> - Ruff;
> - argument validation;
> - hardware-free behavioral code.
>
> Do not generalize the CPU sensor system merely for style.
>
> ---
>
> # 14. Native `system.checks` are complete
>
> This was previously a recommendation.
>
> It is now implemented.
>
> Examples:
>
> ```text
> ephemeral-btrfs-root:
>     reset source check becomes system build dependency
>
> btrfs-maintenance:
>     guard source check becomes system build dependency
> ```
>
>
>
> The distinction is now:
>
> ```text
> nix flake check
>     repository/source health
>
> system.checks
>     critical implementation health required by NixOS build
>
> system.preSwitchChecks
>     physical current-machine prerequisites required for activation
>
> heavy QEMU tests
>     behavioral/system correctness
>
> physical validation
>     real hardware correctness
> ```
>
> Do not move all heavy tests into `system.checks`.
>
> ---
>
> # 15. Activation safety is complete architecturally
>
> This was the largest remaining concern in the second attached review.
>
> It has now been fixed.
>
> Current ownership:
>
> ```text
> modules/workstation/activation-safety/
>     default.nix
>     check.sh
>
> tests/workstation/activation-safety/
>     config.nix
>     guard.nix
>     actions.nix
>     test_guard.py
> ```
>
> Current option namespace:
>
> ```nix
> workstation.activationSafety
> ```
>
> rather than the misleading old:
>
> ```text
> boot.workstationActivationSafety
> ```
>
> The module declares four `system.preSwitchChecks`:
>
> ```text
> persistence
> credentials
> esp
> topology
> ```
>
>
>
> They are deliberately read-only.
>
> They do **not** require:
>
> - monitor;
> - audio;
> - internet;
> - Bluetooth device;
> - Commander Core USB presence;
> - graphical session.
>
> The ESP reserve is:
>
> ```text
> 256 MiB
> ```
>
> and was chosen with much larger observed free space than the installed initrd requirement.
>
> ## Composition assertions
>
> The module now deliberately refuses invalid composition when:
>
> ```text
> ephemeral-root contract absent
> / not concrete Btrfs
> /boot not concrete vfat
> selected user lacks hashedPasswordFile
> ```
>
> Recovery is explicitly allowed to retain the contract while disabling the destructive reset.
>
> ## Tests
>
> The dedicated composition test proves:
>
> ```text
> normal composition accepted
> persistent-root/recovery composition accepted
> all four named preSwitch checks present
> missing ephemeral-root contract refused
> non-Btrfs root refused
> missing ESP device refused
> non-vfat ESP refused
> missing hashedPasswordFile refused
> ```
>
>
>
> The full flake check containing these tests passed locally for source `9ec351d`, and the descendant head `77527f8f` has now passed PR CI.
>
> There is no remaining architectural activation-safety task.
>
> ---
>
> # 16. Stock/control contamination protection is complete
>
> The stock system now rejects project-owned optimization output namespaces:
>
> ```text
> nixos-opt-cpu-*
> nixos-opt-lto-*
> nixos-opt-pgo-*
> nixos-opt-bolt-*
> ```
>
> using:
>
> ```nix
> system.forbiddenDependenciesRegexes
> ```
>
> A deliberately contaminated system using:
>
> ```text
> nixos-opt-pgo-fixture
> ```
>
> provides the negative test.
>
> The normal desktop is the positive control.
>
> The documentation correctly notes the limitation that `system.extraDependencies` is exempt and that output-name contracts cannot detect arbitrary unnamed package modifications.
>
> This is sufficient for the stock baseline.
>
> Do not create a new `research/controls/` hierarchy for this one small module.
>
> ---
>
> # 17. Blank-disk reconstruction implementation is now architecturally correct
>
> This is a major update over the attached review.
>
> The old concern was:
>
> ```text
> production desktop assembled once
> reconstruction independently reassembled similar modules
> → possible drift
> ```
>
> That concern is now resolved.
>
> The current test accepts:
>
> ```nix
> desktopSystem
> ```
>
> and constructs the installed target with:
>
> ```nix
> installed = desktopSystem.extendModules {
>     ...
> };
> ```
>
>
>
> Therefore it inherits the real production:
>
> ```text
> Disko
> Home Manager
> Impermanence
> host configuration
> specialArgs
> username
> unstable package set
> Home Manager user integration
> stock controls
> activation safety
> storage modules
> ```
>
> while adding only test/virtual-hardware overrides.
>
> This was exactly the highest-value structural recommendation from the freshest architecture review, and it is now implemented. :chatgpt-content-reference{index="30"}
>
> ## What the test actually proves when executed
>
> It creates a new 96 GiB virtual disk and then exercises:
>
> ```text
> blank disk
>     ↓
> verify no existing signatures
>     ↓
> real production Disko layout
>     ↓
> GPT
>     ├── 4 GiB ESP
>     ├── 32 GiB swap
>     └── Btrfs
>          ├── @root
>          ├── @home
>          ├── @var
>          ├── @nix
>          ├── @persist
>          ├── @optimization
>          └── @snapshots
>     ↓
> install test-only password hash using production path contract
>     ↓
> install persistent machine-id fixture
>     ↓
> nixos-install exact extended desktop
>     ↓
> verify fallback EFI loader
>     ↓
> shutdown installer
>     ↓
> start new QEMU instance from installed disk only
> ```
>
> Critically the installed machine receives:
>
> ```text
> NO host /nix/store mount
> NO 9p host mount
> NO QEMU-supplied host kernel
> NO QEMU-supplied host initrd
> ```
>
> Then it proves:
>
> ```text
> first normal boot
>     exact installed closure
>     machine ID
>     credentials
>     persistent mounts
>     Home Manager
>     root/persistent probes
>
> reboot normal
>     root-local probe disappears
>     persistent probe survives
>     journal survives
>     reset count increments
>
> persistent-root one-shot boot
>     root-local recovery probe survives
>     root ID unchanged
>     reset count unchanged
>     machine ID unchanged
>     zero failed units
>
> return normal
>     root-local recovery probe disappears
>     persistent probe survives
>     reset count increments
>
> shutdown
>
> offline inspection
>     mount Btrfs top-level read-only
>     verify all seven production subvolumes
>     verify persistent machine ID
> ```
>
>
>
> The repository documentation explicitly says that merely implementing/evaluating this test does **not** close the gate; a successful execution receipt is required.
>
> That is now the single most important unexecuted software/reconstruction gate.
>
> ---
>
> # 18. Stable-refresh/recovery evidence
>
> The pinned recovery ISO has already passed:
>
> ```text
> build
> copy to Ventoy
> explicit flush
> SHA-256 verification
> read-only remount verification
> exFAT read-only check
> ```
>
> The accepted stable-refresh documentation also records the physical root-policy sequence.
>
> There is, however, one documentation/evidence reconciliation item remaining:
>
> ```text
> the continuation evidence reports a completed read-only recovery filesystem drill,
> while docs/stable-refresh.md still asks that exact physical-media receipt details
> be reconciled in the recovery runbook
> ```
>
>
>
> Do **not** automatically repeat the recovery drill.
>
> First reconcile the existing private/public evidence.
>
> Repeat it only if the existing receipt cannot establish what was actually booted/mounted.
>
> ---
>
> # 19. Backup evidence
>
> This gate has advanced significantly.
>
> ## Secrets/bootstrap credential
>
> The separate `/persist/secrets` backup is now considered **complete on user-reported evidence** because it was actually restored during recovery from a real system failure.
>
> No additional secrets framework is required for this baseline.
>
> Do not add sops-nix/agenix merely for architectural neatness.
>
> The production contract remains:
>
> ```text
> /persist/secrets/<username>-password-hash
> ```
>
> The reconstruction test uses the same path with a disposable fixture hash.
>
>
>
> ## Git/LFS project recovery
>
> `AI_Gavin_Project` remote recovery was already proven:
>
> ```text
> commit:
> 376e151fca709b084e182da4c76ccb21a228f86d
>
> 415 LFS objects
> fresh empty LFS object store
> exact sizes/hashes matched
> fresh clone restored project descriptor
> ```
>
>
>
> ## Home inventory
>
> Evidence already includes:
>
> ```text
> full top-level home scan
> 31 entries scanned
> Development ~118 GB allocated
> engine tree ~117.5 GB
> .config ~1.8 GB
> .local/share ~14 GB
> other non-Development data ~18.4 GB
> source/project extension audit
> loose Blender files identified
> ```
>
> ## Current Ventoy archive
>
> The user deliberately selected a dedicated folder on the existing Ventoy USB.
>
> That decision supersedes the older recommendation not to use it for the home archive.
>
> The operation is additive:
>
> ```text
> no formatting
> no existing Ventoy images erased
> 4 GiB free-space reserve enforced
> fresh read-only home snapshot used as source
> ```
>
> The exclusion audit established:
>
> ```text
> 26,000 compared engine binaries:
>     size/CRC equal to retained engine ZIP
>
> 47 extra/different files:
>     backed up separately
>     all 47 restored and hash-verified
> ```
>
> The main compressed archive includes home/projects/engine source/assets with only explicitly audited capacity exclusions.
>
> Latest `plan.md` evidence says archive writing completed at:
>
> ```text
> 27,844,003,241 bytes
> ```
>
> but USB writeback was still draining and no terminal verified archive/restore receipt existed yet.
>
> Therefore:
>
> ```text
> MAIN HOME BACKUP = IN PROGRESS / NOT ACCEPTED YET
> ```
>
> Do not count file creation alone as the backup gate.
>
> ---
>
> # 20. Development/workload evidence already collected
>
> These results are valuable, but remain **preparation evidence**, not final-candidate acceptance.
>
> ## C/C++
>
> Passed:
>
> ```text
> pinned dev shell
> C++20 compilation/execution
> clangd AST/index
> exact trusted query-driver
> zero clangd errors
> ```
>
>
>
> ## Unreal Engine
>
> Passed preparation evidence:
>
> ```text
> real AI_Gavin_Project
> incremental editor target build
> Epic Clang 20.1.8
> Rocky Linux 8 sysroot
> bundled libc++
> Steam FHS
> native Wayland SDL3
> compositor xwayland=false
> Vulkan RADV RX 9070 XT / GFX1201
> configured startup map
> 28 actors
> 10-second map hold
> correct deferred editor close
> default Mimalloc
> exit 0
> ```
>
> An earlier synchronous `SystemLibrary.quit_editor()` test crashed through ICU/Slate cleanup, but investigation demonstrated that the automation violated Unreal's intended deferred shutdown lifecycle. The corrected lifecycle passed, and no `-ansimalloc` workaround was adopted.
>
> Still required:
>
> ```text
> broad/full rebuild
> interactive editor use
> PIE/play
> longer working session
> exact final candidate
> ```
>
> ## Blender
>
> Passed preparation evidence:
>
> ```text
> Blender 5.2.2
> RX 9070 XT HIP
> factory GPU render
> actual local project loaded
> 33-object Cycles scene
> 1920x1080
> 64 samples
> GPU-only
> 11.83 s
> source unchanged
> no targeted GPU reset/fault
> ```
>
>
>
> Still required:
>
> ```text
> interactive use
> sustained representative render
> exact final candidate
> ```
>
> ## Gamescope / MangoHud
>
> Passed:
>
> ```text
> Gamescope 3.16.23
> 600-frame Vulkan cube
> native Wayland client
> XCB/XWayland client
> MangoHud 0.8.3 initialized
> overlay/shim mapped
> ```
>
> Still required:
>
> ```text
> real native game
> real Proton game
> HDR
> controller
> final candidate
> ```
>
> ## GameMode
>
> VM authorization evidence exists and intended user policy is fixed.
>
> Still required physically:
>
> ```text
> actual governor helper succeeds
> requested policy changes
> policy restored after game exits
> split-lock mitigation remains enabled
> ```
>
> ## Creative Stage Pro
>
> Proven:
>
> ```text
> USB enumeration
> ALSA device
> direct ALSA silent transport
> current PipeWire default transport
> ```
>
> Not yet proven:
>
> ```text
> Stage Pro PipeWire profile
> Stage Pro as intended sink
> audible playback
> replug/reboot reconnect
> ```
>
> ## Android/KVM
>
> Current physical blocker:
>
> ```text
> user is in kvm group
> /dev/kvm absent
> VMX disabled in BIOS
> ```
>
>
>
> ## CPU sustained test
>
> The requested 30-minute test has **not passed**.
>
> Existing attempt:
>
> ```text
> 12 stress-ng workers
> nice 19
> 5-second sensor monitoring
> automatic 80 C stop
> ```
>
> stopped at approximately five seconds when CPU package temperature reached 80 C.
>
> Positive observations:
>
> ```text
> no throttle-counter increase
> no matching MCE/hardware/thermal error
> Commander Core active
> fan command changed to 100%
> temperature returned to ~30 C
> ```
>
> but this remains:
>
> ```text
> CPU/OC SUSTAINED STABILITY = OPEN
> ```
>
>
>
> Do not raise the thermal cutoff merely to manufacture a pass.
>
> ---
>
> # 21. Firmware decision
>
> The firmware-update question itself is now settled.
>
> Current retained baseline:
>
> ```text
> ASUS ROG STRIX Z490-E
> BIOS 3201
> current ME 14.1.53.1649 / 14.0.51.1528 components
> ```
>
> The user explicitly chose to retain the current BIOS/ME.
>
> No flash is planned.
>
> The newer BIOS/ME packages remain historical reference only.
>
> The only required firmware action remaining is:
>
> ```text
> enable VMX / Intel virtualization
> ```
>
> during the batched maintenance window.
>
> This should be treated as a baseline-setting change and recorded.
>
> ---
>
> # 22. Maintenance/storage evidence
>
> Current maintenance policy is already part of the physically accepted system.
>
> Journal:
>
> ```text
> SystemMaxUse      2 GiB
> SystemKeepFree    4 GiB
> MaxRetentionSec   90 days
> ```
>
> Coredump:
>
> ```text
> ProcessSizeMax    32 GiB
> ExternalSizeMax   8 GiB
> MaxUse            4 GiB
> KeepFree          4 GiB
> ```
>
> GC:
>
> ```text
> Saturday 04:00
> delete older than 30d
> ```
>
> Scrub:
>
> ```text
> monthly day 1 at 02:00
> ```
>
>
>
> Before controlled performance measurements later:
>
> ```bash
> sudo systemctl stop nix-gc.timer btrfs-scrub--.timer fstrim.timer
> systemctl list-jobs
> systemctl list-timers --all
> ```
>
> Restart them after the measurement window.
>
> Do not interrupt active GC/scrub merely to benchmark.
>
> ---
>
> # 23. Current readiness candidate closure evidence
>
> The previously reviewed readiness candidate was:
>
> ```text
> normal:
> l994fn5hpd2g2rijyffprl4368587m5w
>
> persistent:
> cxc50rmb8i6akb62fcvzz3xkszzqf895
> ```
>
> versus physically accepted:
>
> ```text
> czk5a2wn8di3pgv8a6w0b8aj3286g3h3
> ```
>
> That earlier comparison reported:
>
> ```text
> closure size:
> 16,985,654,488
> →
> 16,985,659,544
> (+5,056 bytes)
>
> membership:
> 2207
> →
> 2208
>
> package version transitions:
> none
>
> kernel store path:
> unchanged
> ```
>
> Material changes were explained by:
>
> ```text
> explicit reset data interface
> Commander Core keeper/wrapper source
> activation pre-switch guards
> initrd/system metadata
> generated units
> ```
>
> No compiler optimization or dependency refresh occurred.
>
> However, the later activation-safety namespace/composition work can affect generated system identity.
>
> Therefore **do not treat `l994...` as automatically the final `77527...` candidate closure**.
>
> The latest ledger explicitly says exact output comparison after the workstation-safety refactor was being evaluated.
>
> Closing that evidence gap is the first immediate task.
>
> ---
>
> # 24. Previous Phase A–L status crosswalk
>
> The previous unified guide can now be collapsed as follows.
>
> | Previous phase | Current result |
> |---|---|
> | A — username parameterization | **COMPLETE** |
> | B — PR/CI policy | **COMPLETE** |
> | C — current-status documentation | **COMPLETE** |
> | D — storage feature directories | **COMPLETE** |
> | E — Btrfs host/mechanism ownership | **COMPLETE** |
> | F — Nix/Bash reset data boundary | **COMPLETE** |
> | G — test subsystem + registry | **COMPLETE** |
> | H — recovery under `images/` | **COMPLETE** |
> | I — Commander policy duplication | **COMPLETE** |
> | J — `system.checks` | **COMPLETE** |
> | K — `system.preSwitchChecks` | **COMPLETE** |
> | L — stock closure contamination contract | **COMPLETE** |
> | M — reconstruction implementation | **COMPLETE** |
> | M — reconstruction execution | **OPEN** |
> | N — bootstrap secret restore | **COMPLETE, user-reported actual recovery** |
> | N — broad home backup/restore | **IN PROGRESS** |
> | O — Facter experiment | **OPTIONAL / NOT STARTED** |
> | P — BIOS/ME choice | **COMPLETE: retain existing** |
> | P — VMX enable | **OPEN** |
> | Q onward — hardware/workloads/soak | **OPEN** |
>
> That is the central update to the project.
>
> Do not continue executing old Phase A–L instructions.
>
> ---
>
> # 25. Current critical path
>
> The effective critical path is now:
>
> ```text
> 77527f8f source + CI PASS
>         │
>         ▼
> [1] close current closure-identity evidence
>         │
>         ▼
> [2] finish Ventoy archive flush / integrity / restore
>         │
>         ▼
> [3] execute blank-disk reconstruction
>         │
>         ▼
> [4] final offline readiness sweep
>         │
>         ▼
> [5] batched physical maintenance window
>         ├── enable VMX
>         └── install exact readiness candidate for next boot
>         │
>         ▼
> [6] physical normal → persistent-root → normal acceptance
>         │
>         ▼
> [7] sustained hardware/storage validation
>         │
>         ▼
> [8] exact-candidate application/workload acceptance
>         │
>         ▼
> [9] multi-day real-use soak
>         │
>         ▼
> [10] final closure/evidence freeze
>         │
>         ▼
> [11] merge PR #7
>         │
>         ▼
> nixos-26.05-pre-optimization-baseline
>         │
>         ▼
> post-baseline historical cleanup
>         │
>         ▼
> feat/optimization-framework-v2
> ```
>
> Everything else is secondary.
>
> ---
>
> # 26. PHASE 1 — Close current in-flight evidence
>
> Do this before creating more code.
>
> ## 26.1 Freeze source identity
>
> Record:
>
> ```bash
> git status --short
> git rev-parse HEAD
> git rev-parse origin/feat/pre-optimization-readiness
> git rev-parse origin/main
> ```
>
> Expected reviewed state:
>
> ```text
> HEAD:
> 77527f8f712611ca244a2946c97c4f5c94d63ba4
>
> main:
> f89205c07e4d3a77900b046a5bf937944488647b
> ```
>
> If the branch has moved, use the new exact head and explicitly note that this guide's `77527...` snapshot was superseded.
>
> ## 26.2 Build current exact normal closure
>
> ```bash
> normal="$(
>   nix build \
>     '.#nixosConfigurations.desktop.config.system.build.toplevel' \
>     --no-link \
>     --print-out-paths
> )"
>
> printf '%s\n' "$normal"
> ```
>
> ## 26.3 Build current persistent-root closure
>
> ```bash
> persistent="$(
>   nix build \
>     '.#nixosConfigurations.desktop.config.specialisation.persistent-root.configuration.system.build.toplevel' \
>     --no-link \
>     --print-out-paths
> )"
>
> printf '%s\n' "$persistent"
> ```
>
> ## 26.4 Compare against accepted baseline
>
> ```bash
> nix store diff-closures \
>   /nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8 \
>   "$normal"
> ```
>
> Also compare the new candidate against the last readiness candidate if its old paths remain present.
>
> Required conclusion:
>
> ```text
> all changes explained
> no unplanned package version transition
> no unexpected kernel transition
> no unexpected Mesa transition
> no accidental optimization dependency
> no input refresh
> ```
>
> If current normal/persistent outputs changed after the activation-safety refactor:
>
> - record their exact paths;
> - update private receipts;
> - protect them with explicit temporary GC roots if necessary;
> - update `docs/closure-review.md`;
> - update `docs/status.md`.
>
> Do not activate yet.
>
> ---
>
> # 27. PHASE 2 — Finish the home backup gate
>
> Do not start a second archive.
>
> Continue the existing operation/evidence chain.
>
> Current state:
>
> ```text
> main compressed archive written:
> 27,844,003,241 bytes
>
> USB writeback:
> was still draining in latest ledger
>
> archive integrity receipt:
> not yet terminal
>
> representative restore:
> not yet complete
> ```
>
> ## Required completion evidence
>
> The gate closes only when all of the following are true:
>
> ```text
> [ ] dirty/writeback has drained
> [ ] archive is readable from the USB filesystem
> [ ] compressed stream/archive integrity passes
> [ ] final archive size recorded
> [ ] archive checksum recorded
> [ ] selected restore is made to a separate destination
> [ ] restored files compared against source snapshot
> [ ] representative contents/hash comparison passes
> [ ] supplemental 47-file backup remains verified
> [ ] free-space reserve remains acceptable
> [ ] filesystem is cleanly flushed/unmounted
> [ ] terminal receipt exists
> ```
>
> Do not substitute:
>
> ```text
> file exists
> ```
>
> for:
>
> ```text
> backup verified
> ```
>
> ## Preserve important distinctions
>
> ### Secrets
>
> Already complete separately through actual past recovery.
>
> Do not repeat solely to satisfy the home archive.
>
> ### Git remote
>
> Already proven.
>
> ### Main home archive
>
> Still needs its own integrity + restore gate.
>
> ### Recovery media
>
> The same physical USB now serves more than one purpose.
>
> Do not erase existing ISO content during archive cleanup.
>
> ---
>
> # 28. PHASE 3 — Execute blank-disk reconstruction
>
> Once the backup receipt is safely complete, run the already-implemented test.
>
> Primary command:
>
> ```bash
> nix build \
>   .#blank-disk-reconstruction \
>   --no-link \
>   --print-build-logs
> ```
>
> The attached feature review correctly identified this as the highest-value next NixOS action: the infrastructure already exists, so proving it passes is now more useful than inventing another reliability module. :chatgpt-content-reference{index="47"}
>
> ## Acceptance
>
> Require terminal success for the entire scenario.
>
> Do not accept merely:
>
> ```text
> derivation evaluates
> installer starts
> Disko runs
> first boot works
> ```
>
> The entire chain must pass:
>
> ```text
> blank disk
> Disko
> nixos-install
> UEFI boot
> normal boot
> normal reboot/reset
> persistent-root boot
> return to normal
> offline Btrfs inspection
> zero failed-unit requirement
> ```
>
> ## If reconstruction fails
>
> Classify the failure first:
>
> ```text
> test harness defect
> production config defect
> bootloader issue
> Disko issue
> activation guard issue
> credential contract issue
> root reset issue
> QEMU fixture issue
> resource/time issue
> ```
>
> Then make the narrowest correct fix.
>
> Never weaken:
>
> ```text
> no host store
> no host kernel
> no host initrd
> real desktop composition
> real Disko layout
> credential path contract
> root-reset semantics
> ```
>
> merely to make the test green.
>
> After a code fix:
>
> ```text
> nix flake check --print-build-logs
> relevant focused test
> blank-disk reconstruction again
> ```
>
> Record final derivation/output/log receipt in `plan.md` and `docs/status.md`.
>
> ---
>
> # 29. PHASE 4 — Final offline readiness sweep
>
> Once backup + reconstruction pass, perform one complete pre-physical sweep.
>
> ## Fast suite
>
> ```bash
> nix flake check --print-build-logs
> ```
>
> ## Explicit heavy tests
>
> Run at minimum:
>
> ```bash
> nix build .#workstation-smoke --no-link -L
> nix build .#reset-control --no-link -L
> nix build .#impermanence-root-safety --no-link -L
> nix build .#interrupted-recovery --no-link -L
> nix build .#persistent-identity --no-link -L
> nix build .#persistent-fallback --no-link -L
> nix build .#activation-safety-actions --no-link -L
> nix build .#blank-disk-reconstruction --no-link -L
> ```
>
> Run the stock contamination negative test deliberately and confirm it fails **for the expected forbidden-dependency reason**.
>
> Do not interpret an unrelated build failure as success.
>
> ## Recovery artifact
>
> Build:
>
> ```bash
> nix build .#recovery-iso --no-link
> ```
>
> If the resulting ISO is still exactly:
>
> ```text
> d55ny1z4d53slhz3ilvyy2mg6d8khrqn
> ```
>
> the existing verified Ventoy copy remains the exact artifact.
>
> If it changes, do not silently call the older ISO the matching recovery image.
>
> ## PR description cleanup
>
> PR #7's description has lagged slightly behind the current ledger.
>
> Before final physical work, update it to reflect:
>
> ```text
> bootstrap secret restore = complete
> reconstruction derives exact desktop via extendModules
> activation-safety relocation/assertions = complete
> current head CI = green
> main home archive = current actual status
> blank reconstruction = actual result
> ```
>
> Keep the PR draft.
>
> ---
>
> # 30. PHASE 5 — Optional isolated Facter experiment
>
> This is the only major NixOS 26.05 feature from the attached review that is still genuinely new and potentially useful before optimization. :chatgpt-content-reference{index="48"}
>
> It is **not a hard gate**.
>
> Only do it if it does not delay reconstruction/physical readiness.
>
> Generate:
>
> ```bash
> sudo nix-shell -p nixos-facter \
>   --run 'nixos-facter -o facter.json'
> ```
>
> Compare:
>
> ```text
> existing hardware-configuration.nix
>             vs
> Facter report
>             vs
> Facter-derived evaluation
> ```
>
> Use:
>
> ```text
> hardware.facter.debug.nvd
> hardware.facter.debug.nix-diff
> ```
>
> where useful.
>
> Decision rule:
>
> ```text
> if Facter materially improves hardware provenance without obscuring
> important explicit configuration:
>     consider adoption
>
> otherwise:
>     record comparison
>     keep existing hardware-configuration.nix
> ```
>
> Do not make Facter adoption a new prerequisite simply because the experiment exists.
>
> ---
>
> # 31. PHASE 6 — Batched physical maintenance window
>
> Prerequisites:
>
> ```text
> backup PASS
> reconstruction PASS
> offline test suite PASS
> current candidate closures recorded
> recovery path known
> ```
>
> ## 31.1 Capture retained firmware state
>
> Before firmware-setting changes, record:
>
> ```text
> BIOS 3201
> ME versions
> CPU ratio
> cache ratio
> core voltage
> LLC
> AVX offset
> power limits
> RAM frequency/timings
> ReBAR
> Above 4G decoding
> VMX state
> Speed Shift/HWP
> ```
>
> No BIOS/ME flash is planned.
>
> ## 31.2 Enable VMX
>
> Change only the required virtualization setting unless another deliberately recorded hardware correction is needed.
>
> After boot:
>
> ```bash
> grep -m1 -o 'vmx' /proc/cpuinfo
> test -c /dev/kvm
> ls -l /dev/kvm
> groups
> ```
>
> Required:
>
> ```text
> vmx CPU capability visible
> /dev/kvm exists
> expected kvm group ownership
> p2949 has access
> ```
>
> ## 31.3 Install exact readiness candidate for boot
>
> Given that the candidate changes:
>
> ```text
> initrd
> root-reset source
> Commander Core service source/wrapper
> preSwitch activation checks
> system metadata
> ```
>
> prefer a **boot installation**, not a casual live switch.
>
> Use the exact source already validated.
>
> For example:
>
> ```bash
> sudo nixos-rebuild boot --flake '.#desktop'
> ```
>
> The activation prerequisites should run as designed.
>
> Do not bypass a failed preSwitch check.
>
> A refusal is evidence that the host prerequisite must be corrected.
>
> ---
>
> # 32. PHASE 7 — Exact final physical root/candidate acceptance
>
> Perform the same high-value pattern already proven:
>
> ```text
> normal candidate
>     ↓
> persistent-root candidate
>     ↓
> normal candidate
> ```
>
> ## First normal
>
> Verify:
>
> ```text
> exact candidate closure
> kernel 6.18.55 unless intentionally changed
> fresh @root
> reset count +1
> machine ID stable
> /persist stable
> /home stable
> /var stable
> /nix stable
> /var/lib/nixos-optimization stable
> credentials correct
> Home Manager active
> NetworkManager active
> D-Bus/logind active
> Commander Core active
> Wayland session works
> zero failed units
> ```
>
> Create:
>
> ```text
> root-local probe
> persistent probe
> ```
>
> ## Persistent-root
>
> Verify:
>
> ```text
> persistent-root closure exact
> root ID/UUID unchanged
> reset count unchanged
> root-local probe survives
> persistent probe survives
> machine ID unchanged
> credentials unchanged
> services healthy
> ```
>
> ## Final normal
>
> Verify:
>
> ```text
> normal closure exact
> fresh root ID/UUID
> reset count +1 exactly
> root-local probe gone
> persistent probe survives
> machine ID unchanged
> services healthy
> zero failed units
> ```
>
> This is the final physical validation of the readiness code.
>
> There is no need for another arbitrary three-reset sequence unless the actual reset semantics have changed after the existing VM suite.
>
> ---
>
> # 33. PHASE 8 — Hardware/storage stability
>
> Run on the final physically accepted candidate and retained firmware state.
>
> ## 33.1 NVMe
>
> Capture SMART:
>
> ```bash
> sudo nvme smart-log /dev/nvme0
> ```
>
> and relevant error information.
>
> Require:
>
> ```text
> critical warning = understood/clear
> media/data errors = none or explicitly understood
> temperature normal
> spare healthy
> percentage used reasonable
> error-log anomalies understood
> ```
>
> ## 33.2 Btrfs
>
> Check:
>
> ```bash
> sudo btrfs scrub status /
> sudo btrfs device stats /
> sudo btrfs filesystem usage /
> ```
>
> Require:
>
> ```text
> scrub finished
> no errors found
> device errors zero or explicitly explained
> filesystem usage healthy
> ```
>
> Do not launch a redundant scrub while another is active.
>
> ## 33.3 Nix store
>
> During an idle period:
>
> ```bash
> sudo nix-store --verify --check-contents
> ```
>
> Any corruption must be repaired/rebuilt before the baseline freeze.
>
> Optional one-time:
>
> ```bash
> sudo nix-store --optimise
> ```
>
> but do not run store optimization during benchmark measurements.
>
> ## 33.4 RAM
>
> Run a real memory-stability test suitable for the installed 32 GiB configuration.
>
> Require:
>
> ```text
> zero memory errors
> ```
>
> If CPU/RAM firmware settings change, repeat the relevant stability tests.
>
> ## 33.5 CPU/OC/cooling
>
> The previous 5-second test is not sufficient.
>
> Target the originally intended sustained interval rather than lowering the standard.
>
> Maintain the conservative thermal safety stop.
>
> If the current 5.0 GHz configuration reaches the stop too quickly:
>
> ```text
> reduce voltage if overvolted
> adjust power limits
> improve cooling/contact
> or reduce clock
> ```
>
> Do not simply raise the temperature limit to call the overclock stable.
>
> Monitor:
>
> ```text
> CPU package temperature
> frequency
> throttle indicators
> MCE/hardware errors
> Commander Core service
> fan policy transitions
> watchdog/restarts
> ```
>
> A valid result requires a genuinely sustained stable run.
>
> ---
>
> # 34. PHASE 9 — Freeze stock CPU/memory/I/O policy
>
> Once hardware is stable, document and stop changing ordinary machine policy.
>
> Current intended stock posture remains conservative:
>
> ```text
> security mitigations enabled
> SMT enabled
> ordinary C-states
> intel_pstate
> powersave governor
> balance_performance EPP
> THP madvise
> 32 GiB disk swap
> zram off
> kernel-selected NVMe scheduler
> no global compiler flags
> no global RADV hacks
> no global LD_LIBRARY_PATH
> no fixed performance clocks as normal desktop policy
> ```
>
> Do not introduce new performance tweaks during this phase.
>
> Measure first if you genuinely suspect:
>
> ```text
> zram
> irqbalance
> THP
> scheduler
> governor/EPP
> ```
>
> needs changing.
>
> Any policy change this late requires repeating relevant workload comparisons.
>
> ---
>
> # 35. PHASE 10 — Final exact-candidate workload acceptance
>
> Earlier preparation results establish that the workflows can work.
>
> Now prove them on the actual baseline candidate.
>
> ## Desktop/session
>
> Require:
>
> ```text
> normal graphical login
> Hyprland/UWSM
> portals
> Firefox
> Waybar/notifications
> persistence
> reboot
> zero failed units
> ```
>
> ## C/C++
>
> Require:
>
> ```text
> nix develop
> GCC build
> Clang build
> clangd indexing
> representative project build
> no ambient optimization flags
> ```
>
> ## Unreal Engine
>
> Run actual `AI_Gavin_Project`.
>
> Require:
>
> ```text
> Epic intended toolchain
> broad/full C++ build
> native Wayland
> RX 9070 XT RADV
> actual startup map
> interactive editing
> PIE/play
> normal ordinary shutdown
> longer representative session
> tracked project remains clean
> no GPU reset
> ```
>
> Retain the corrected deferred shutdown lifecycle for automation.
>
> Do not introduce `-ansimalloc` based on the invalid old synchronous-quit test.
>
> ## Blender
>
> Require:
>
> ```text
> actual project
> HIP RX 9070 XT
> interactive use
> representative sustained render
> source file unchanged
> no GPU timeout/reset/fault
> ```
>
> ## Android Studio
>
> Now that VMX is enabled:
>
> ```text
> /dev/kvm functional
> Java project
> AVD starts with hardware acceleration
> normal emulator interaction
> AVD persists across restart
> ```
>
> ## Gaming
>
> Use at least:
>
> ```text
> one native Vulkan title
> one Proton title
> ```
>
> Exercise:
>
> ```text
> GameMode
> Gamescope
> MangoHud
> controller
> audio
> VRR/HDR where part of real workflow
> ```
>
> Verify GameMode:
>
> ```text
> authorized helper actually succeeds
> performance policy applied during session
> policy restored on exit
> split-lock mitigation remains enabled
> ```
>
> ## Creative Stage Pro
>
> Close the outstanding audio gate:
>
> ```text
> appropriate PipeWire profile enabled
> Stage Pro sink exists
> Stage Pro selected intentionally
> audible playback
> replug recovery
> reboot recovery
> default route behaves as intended
> ```
>
> ## Networking/Bluetooth
>
> Verify normal persisted:
>
> ```text
> NetworkManager connection profiles
> Ethernet/Wi-Fi
> Bluetooth where used
> post-reboot reconnection
> ```
>
> ---
>
> # 36. PHASE 11 — Experimental-control audit
>
> Before the soak, ensure this is still a genuinely stock baseline.
>
> ## Environment
>
> Check for accidental global:
>
> ```text
> CFLAGS
> CXXFLAGS
> CPPFLAGS
> LDFLAGS
> RUSTFLAGS
> NIX_CFLAGS_COMPILE
> NIX_LDFLAGS
> LD_LIBRARY_PATH
> MALLOC_CONF
> RADV_PERFTEST
> ```
>
> Every non-empty global value needs an explanation.
>
> ## Source
>
> Search outside `optimization/` for:
>
> ```text
> -march=
> -mtune=
> -flto
> -fprofile
> llvm-bolt
> PGO
> BOLT
> nixos-opt-
> ```
>
> Expected `nixos-opt-*` occurrences should be limited to the contamination-control infrastructure/tests.
>
> ## Optimization module
>
> Must remain inert.
>
> The old branch:
>
> ```text
> feat/optimization-framework
> 397a8c71cd7acb0bc016983f28866df16c95d7d8
> ```
>
> remains donor/prototype code only.
>
> Do not merge it.
>
> ---
>
> # 37. PHASE 12 — Multi-day stock-system soak
>
> Once:
>
> ```text
> candidate physically accepted
> hardware stable
> workloads individually accepted
> ```
>
> use the machine normally.
>
> The soak should include representative combinations rather than isolated smokes:
>
> ```text
> multiple cold boots
> multiple warm reboots
> Unreal development
> Blender rendering
> large C/C++ build
> large Nix build
> Android emulator
> gaming
> controller
> audio
> browser/network
> normal desktop work
> suspend/resume if actually used
> ```
>
> Track:
>
> ```text
> failed systemd units
> kernel GPU faults/resets
> MCE/hardware errors
> filesystem errors
> root-reset anomalies
> persistence failures
> cooling service failures/restarts
> unexpected OOM/swap behavior
> disk/store growth
> application crashes
> ```
>
> A failure should be:
>
> ```text
> recorded
> classified
> fixed declaratively where appropriate
> retested
> ```
>
> not silently worked around.
>
> ---
>
> # 38. PHASE 13 — Final baseline freeze
>
> Only after soak acceptance.
>
> ## Repository
>
> Require:
>
> ```text
> clean worktree
> all intended source committed
> flake.lock frozen
> optimization inert
> PR #7 reflects true current status
> ```
>
> ## Fast checks
>
> ```bash
> nix flake check --print-build-logs
> ```
>
> ## Heavy checks
>
> Re-run the exact final-source set:
>
> ```text
> workstation-smoke
> reset-control
> safety
> interrupted-recovery
> persistent-identity
> persistent-fallback
> activation-safety-actions
> stock-contamination-negative expected refusal
> blank-disk-reconstruction
> recovery ISO
> ```
>
> Do not rely solely on an old derivation if later source changes affect the tested subsystem.
>
> ## Build exact closures
>
> Record:
>
> ```text
> normal closure
> persistent-root closure
> recovery ISO
> ```
>
> ## Closure review
>
> Compare against:
>
> ```text
> accepted c5e stable-refresh
> last readiness candidate
> final candidate
> ```
>
> Explain every material difference.
>
> Require:
>
> ```text
> no unexplained package change
> no accidental optimization dependency
> no unexpected input change
> ```
>
> ## Runtime manifest
>
> Record at minimum:
>
> ```text
> Git commit
> flake.lock SHA-256
> Nixpkgs revision
> unstable revision
> Home Manager revision
> Disko revision
> Impermanence revision
> Nix version
> NixOS version
> normal closure
> persistent closure
> recovery ISO + SHA-256
> kernel
> Mesa
> microcode
> BIOS
> ME
> CPU ratios
> cache ratio
> voltage/power settings
> RAM frequency/timings
> GPU
> NVMe model/firmware
> Btrfs mount options
> scrub result
> CPU governor
> EPP
> THP
> swap
> zram
> NVMe scheduler
> irqbalance state
> maintenance timers
> Commander Core policy
> machine ID
> failed-unit state
> ```
>
> ---
>
> # 39. PHASE 14 — Merge and tag
>
> PR #7 should remain draft until all hard gates are green.
>
> Then:
>
> ```text
> mark ready
> ensure required Flake checks green
> review final diff
> merge to protected main
> ```
>
> Verify merged `main` still corresponds to the tested tree.
>
> Then create annotated tag:
>
> ```text
> nixos-26.05-pre-optimization-baseline
> ```
>
> Record the tag and exact closure identities under:
>
> ```text
> docs/baselines/pre-optimization/
> ```
>
> This tag becomes the immutable control point for the optimization campaign.
>
> ---
>
> # 40. PHASE 15 — Post-baseline cleanup
>
> Only after the tag exists.
>
> Review temporary:
>
> ```text
> preparation GC roots
> old stable-refresh candidate roots
> old readiness candidate roots
> old recovery ISO roots
> forensic root snapshots
> obsolete generations
> ```
>
> Do not delete them as one batch.
>
> Classify each as:
>
> ```text
> rollback needed
> forensic evidence
> historical only
> safe to remove
> ```
>
> Run a fresh GC preview before collection.
>
> ## Historical compatibility cleanup
>
> Only now consider removing:
>
> ```text
> impermanence-root-test-a alias
> impermanence-root-test-b alias
> other old A/B aliases
> maintenance guard basename-preservation hack
> ```
>
> if they no longer provide useful historical reproducibility.
>
> ## Documentation
>
> After baseline completion, reorganize:
>
> ```text
> docs/
> ├── status.md
> ├── design/
> ├── runbooks/
> ├── validation/
> ├── baselines/
> └── history/
> ```
>
> Do not do the large docs move beforehand.
>
> Archive `plan.md` under history once it stops being the live execution ledger.
>
> The fresh architecture review correctly identifies the current docs tree and `plan.md` as the next organizational pressure point, but recommends deferring that churn until readiness is finished. :chatgpt-content-reference{index="49"}
>
> ---
>
> # 41. PHASE 16 — Start optimization cleanly
>
> Create a new branch from the accepted baseline:
>
> ```text
> feat/optimization-framework-v2
> ```
>
> Do not continue optimization work on:
>
> ```text
> feat/pre-optimization-readiness
> ```
>
> and do not revive the old optimization branch as the active implementation.
>
> The experiment sequence remains:
>
> ```text
> stock
>   ↓
> CPU-specific code generation
>   ↓
> conservative compiler tuning
>   ↓
> LTO
>   ↓
> PGO
>   ↓
> BOLT
>   ↓
> validated combinations
> ```
>
> The stock contamination contract is already the seed for stage-sensitive controls.
>
> Later:
>
> ```text
> stock:
>     forbid CPU/LTO/PGO/BOLT
>
> cpu-codegen:
>     permit CPU
>     forbid LTO/PGO/BOLT
>
> LTO:
>     permit CPU/LTO as designed
>     forbid PGO/BOLT
>
> PGO:
>     permit intended PGO
>     forbid BOLT
>
> BOLT:
>     permit intended stage
> ```
>
> ---
>
> # 42. Explicitly deferred ideas
>
> These are **not** readiness blockers.
>
> ## Distributed builds
>
> Excellent once LLVM/LTO/PGO builds become expensive.
>
> Eventually:
>
> ```text
> workstation = benchmark target
> remote machine = build target
> ```
>
> The attached NixOS-feature review ranks this highly for the optimization phase, not for the current baseline. :chatgpt-content-reference{index="50"}
>
> ## `system.replaceDependencies`
>
> Useful experimental comparison:
>
> ```text
> normal downstream rebuild
> vs
> dependency graft
> ```
>
> Do not use as the primary PGO/BOLT architecture.
>
> ## Optimization specialisation matrix
>
> Later:
>
> ```text
> stock
> cpu-codegen
> thinlto
> pgo
> bolt
> pgo-bolt
> kernel-experiment
> ```
>
> This is a strong eventual use of the existing specialisation model.
>
> ## NixOS nspawn tests
>
> Use only where a service test genuinely benefits from a faster no-kernel tier.
>
> Do not migrate Btrfs/initrd/bootloader tests away from QEMU.
>
> ## Generated option docs
>
> `nixosOptionsDoc` could eventually document:
>
> ```text
> boot.ephemeralBtrfsRoot.*
> workstation.activationSafety.*
> hardware.commanderCore.*
> ```
>
> Useful polish, not a stock-baseline gate.
>
> ## Signed binary cache
>
> Highly valuable once optimized builds cost tens of minutes/hours.
>
> Defer until there are expensive outputs worth preserving/distributing.
>
> ## `system.includeBuildDependencies`
>
> Interesting offline-reproducibility experiment.
>
> Do not enable on the normal workstation.
>
> ## Remote deployment
>
> Useful once another NixOS machine becomes part of the lab.
>
> Not needed now.
>
> ---
>
> # 43. Things explicitly not to add
>
> Do not add before baseline freeze:
>
> ```text
> ephemeral /home
> ephemeral /var
> flake-parts
> flake-utils
> generic host framework
> automatic system upgrades
> a secrets framework solely for novelty
> Cachy/Zen/custom kernel solely for performance
> mitigations=off
> isolcpus
> nohz_full
> rcu_nocbs
> global -march/-mtune
> global LTO
> global PGO flags
> global LD_LIBRARY_PATH
> global RADV performance hacks
> fixed clocks as ordinary workstation policy
> another recovery architecture
> another generic module abstraction layer
> ```
>
> The current open gates are evidence/physical gates, not architecture gaps.
>
> ---
>
> # 44. Hard GO checklist
>
> Optimization work must not begin until this is green.
>
> ## Repository / CI
>
> - [x] username source of truth fixed
> - [x] storage feature organization complete
> - [x] reset Nix/Bash boundary complete
> - [x] Btrfs host/mechanism split complete
> - [x] test registry complete
> - [x] recovery moved to `images/`
> - [x] Commander policy duplication removed
> - [x] `system.checks` implemented
> - [x] `system.preSwitchChecks` implemented
> - [x] stock forbidden dependencies implemented
> - [x] reconstruction derives from exact real desktop
> - [x] activation safety rehomed/renamed
> - [x] activation composition assertions tested
> - [x] CI runner/action pins fixed
> - [x] PR #7 current head CI green
> - [ ] exact latest candidate closure identities recorded
> - [ ] final readiness source merged to main
> - [ ] annotated baseline tag exists
>
> ## Root / reconstruction
>
> - [x] physical initial root trials
> - [x] root safety matrix
> - [x] interrupted reset recovery
> - [x] machine-ID persistence
> - [x] persistent-root VM fallback
> - [x] physically accepted normal → persistent → normal stable-refresh
> - [x] blank-disk test implemented
> - [x] blank-disk test uses actual desktop system
> - [ ] blank-disk test executed successfully
> - [ ] final readiness source physical normal → persistent → normal accepted
>
> ## Recovery / backup
>
> - [x] pinned recovery ISO built
> - [x] ISO copied and hash verified
> - [x] exFAT read-only check
> - [x] project remote/LFS restore
> - [x] separate bootstrap-secret restore proven by actual user recovery
> - [x] home inventory
> - [x] engine exclusion audit
> - [x] supplemental 47-file restore/hash verification
> - [ ] main archive integrity verification
> - [ ] representative main archive restore
> - [ ] terminal backup receipt
> - [ ] exact recovery-drill public/private evidence reconciled
>
> ## Firmware
>
> - [x] firmware versions documented
> - [x] BIOS/ME update decision made
> - [x] retain BIOS 3201/current ME
> - [ ] VMX enabled
> - [ ] `/dev/kvm` physically accepted
> - [ ] final firmware/OC settings frozen
>
> ## Storage / hardware
>
> - [ ] NVMe SMART accepted
> - [ ] Btrfs current scrub/device stats accepted
> - [ ] Nix store content verification
> - [ ] RAM stability accepted
> - [ ] sustained CPU/OC stability accepted
> - [ ] sustained Commander Core/cooling behavior accepted
>
> ## Workloads
>
> - [x] C++20 preparation smoke
> - [x] clangd preparation
> - [x] Unreal incremental build preparation
> - [x] Unreal native Wayland/map lifecycle preparation
> - [x] Blender actual-project HIP preparation render
> - [x] Gamescope/MangoHud synthetic preparation
> - [x] Stage Pro ALSA transport
> - [ ] final C/C++ candidate
> - [ ] Unreal full workflow
> - [ ] Blender sustained workflow
> - [ ] Android/KVM
> - [ ] native game
> - [ ] Proton game
> - [ ] physical GameMode governor helper
> - [ ] controller
> - [ ] HDR if baseline workflow uses it
> - [ ] Stage Pro PipeWire audible/reconnect
> - [ ] network/Bluetooth final acceptance
>
> ## Stock policy
>
> - [ ] CPU governor/EPP frozen
> - [ ] THP frozen
> - [ ] zram decision frozen
> - [ ] IRQ policy frozen
> - [ ] scheduler recorded
> - [ ] no unintended global optimization environment
> - [ ] stock closure audit clean
>
> ## Stability
>
> - [ ] multi-day soak complete
> - [ ] no recurring failed units
> - [ ] no GPU reset
> - [ ] no unexplained hardware error
> - [ ] no filesystem error
> - [ ] no cooling failure
> - [ ] no root-reset/persistence failure
> - [ ] no unresolved serious workload regression
>
> Only then:
>
> ```text
> GO FOR OPTIMIZATION
> ```
>
> ---
>
> # 45. Immediate next action
>
> The correct next action is **not another source refactor**.
>
> At the current reviewed head, do these in order:
>
> ```text
> 1. Finish and record the exact post-activation-safety candidate closure comparison.
>
> 2. Let the existing Ventoy backup operation reach a terminal state:
>       flush
>       integrity
>       representative restore
>       receipt
>       clean unmount
>
> 3. Execute:
>       nix build .#blank-disk-reconstruction --no-link --print-build-logs
>
> 4. If reconstruction passes:
>       run final offline heavy readiness suite.
>
> 5. Then schedule the single physical maintenance window:
>       enable VMX
>       install exact candidate for boot
>       normal → persistent-root → normal
>       KVM verification
>
> 6. Continue directly into:
>       hardware stability
>       final workloads
>       soak
>       freeze/merge/tag.
> ```
>
> Unless one of those steps exposes a real defect, **do not expand the architecture any further before the stock baseline is frozen.**
>
> This version deliberately removes all of the old “next architectural refactor” work that the branch has already completed. The current source itself confirms that reconstruction now consumes the real desktop, activation-safety has the right ownership and assertions, the flake/test architecture is settled, and CI is reproducible and green.
>
> The main project-management shift is therefore: **stop implementing readiness mechanisms and start closing readiness evidence.** The live status document says the same thing: the remaining blockers are reconstruction execution, the main home archive/restore, VMX, sustained hardware stability, final exact-candidate workloads, and the soak.

## Current continuation Phase1 accepted — 2026-10-05

Current normal and persistent builds both exited0 (session23324) and reproduce:
normal /nix/store/l994fn5hpd2g2rijyffprl4368587m5w-nixos-system-desktop-26.05.20261004.0d9e9b8
persistent /nix/store/cxc50rmb8i6akb62fcvzz3xkszzqf895-nixos-system-desktop-26.05.20261004.0d9e9b8.
Source2ef8585 plus guide-only ledger import; no runtime configuration difference.
Existing membership/size/kernel comparison remains exact because outputs are
identical, not merely similarly named. Existing candidate GC roots remain the
correct targets; no replacement/removal necessary. Physical acceptance remains
open. Terminal build log preserved root-private. This closes the imported
guide's latest-candidate identity gap without repeating accepted physical boots.

Backup zstd integrity passed; runner is hashing the same existing archive.
Representative restore/final receipt/clean unmount still open. No second archive,
firmware change, live switch or reboot. Next required step remains completion of
backup followed by queued independent reconstruction.

## Backup/reconstruction sequencing corrected — 2026-10-05

Newest guide requires clean USB unmount before reconstruction. Replaced only
our waiting supervisor730405 (explicitly cancelled before build) with session11114:
wait for existing runner521492; require verified receipt; cleanly unmount
/mnt/nixos-backup-ventoy; write private clean-unmount timestamp; only then build
blank-disk reconstruction with bounded jobs/cores and full build logs. A missing
receipt or failed unmount holds execution. No backup process was restarted or
interrupted. Hashing remains live/progressing; no representative restore claim.

## Independent Ventoy home backup accepted — 2026-10-05

- [x] Main archive: 27,844,003,241 bytes.
- [x] Zstd integrity passed; SHA-256
  `9ec746a927b42c48484cb877d1d1916ca54f084f5ecdeffd3babc2f5ed1db212`.
- [x] Two Blender files and one actual Unreal project descriptor restored to
  a separate root-private directory; all three source/restored hashes match.
- [x] Earlier47-file engine supplement remains separately verified.
- [x] Backup runner session50539 exited0, terminal receipt completed
  2026-10-05T17:58:06Z. Ventoy cleanly unmounted17:58:09Z; findmnt confirms absent.

USB folder: NixosConf-backups/2026-10-05; media UUID1BF6-1635. No formatting,
partition change or existing ISO deletion. About12GiB free before unmount,
above enforced4GiB reserve. Source is read-only home-ventoy-20261005 snapshot;
application quiescence was not claimed. Engine ZIP and audited binaries/cache
exclusions remain documented, with unique binary additions supplemented.
Secrets backup is separate and user-confirmed from actual recovery.
Private receipts, restored samples, scripts and logs are retained under
/persist/nixos-ventoy-backup-20261005. This is point-in-time backup evidence;
new work after snapshot creation requires a later backup before final freeze.

Queued reconstruction session11114 started only after verified receipt and
clean unmount, source736b0fb. Nix PID1186208 is actively building. This closes
home archive/integrity/representative restore/unmount gates; it does not close
reconstruction, physical hardware/workload acceptance or multi-day soak.
