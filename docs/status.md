# Current readiness status

This file contains current truth only. [plan.md](../plan.md) preserves the
chronological ledger, supplied guides and superseded observations.

## Source, PR and CI

Active local work is `feat/granular-impermanence`, starting at reviewed
`de058b4b65416249e2a1ac2e722f7514c87d5a36`. The
[granular implementation plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
records actual receipts, application policies and the remaining gates.

Generation 44 persistent-root is running: home is root-local and legacy `@var`
remains. Generation 42's quiesced shutdown copy and first home matrix passed.
Generation 44 fixes the intermediate random-seed bind and the observed Fuzzel
history omission, preserving only `.local/state/fuzzel`. The user confirms the
restored ordering. Both normal/recovery ESP artifact pairs match the exact store
closures; generation 41, original subvolumes and snapshots remain available.

The first accepted generation-44 recovery retained all 100 markers and the same
root ID 330/UUID, with stable identity, correct islands and healthy services:
`physical-boot-passed-f27d98d2-004e-4b1b-a803-68af4b8c4f20.json`.
The second attempt on boot `d0f24f81-807b-4e27-810a-b2fcdf1beae4` failed strict
verification after Firefox deleted telemetry proofs; later artwork cleanup
removed another proof. That attempt is archived and never counted. No missing
postboot proof was recreated. The first accepted recovery remains valid.

The standalone checker now nests proofs only where observed Codex/Firefox
telemetry cleanup skips directories. Eight marker regressions pass; recovery
still requires exact tokens and normal reset must remove entire generated
containers. The unchanged twelve-case home guard still refuses this unaccepted
boot. Full current-source flake checks and formatting pass; unchanged VM results
were reused. This is local validation, not new physical or GitHub CI evidence.

After the user confirmed applications were saved/closed and agreed to verify
before reopening them, the replacement second recovery ticket was seeded and
all 100 markers independently re-read. All 82 cache binds, user ownership,
ESP artifact pairs and zero failed services pass fresh preflight. The new
GC-rooted checker also refuses same-boot verification without altering the
ticket. Generation-44 recovery is selected once; normal generation 44 remains
the main profile/default. No agent reboot is initiated or scheduled.
Private evidence: `home-recovery-cycle-2-firefox-preparation.json` and
`home-recovery-cycle-2-firefox-seeded.json`. Verify before starting Firefox or
other cache-cleaning applications, using a text console if needed. Then complete
normal → normal on generation 44, independently run home acceptance, and freeze
home policy before rebuilding the exact final var candidate.

The user already confirmed browser, Steam, VS Code, Git/GitHub, relevant VCS and
Unity/Unreal project workflows after the home migration. Selected identity and
database integrity checks, Codex login, Blender configuration and isolated
Firefox/Unity/Unreal startup checks also passed. Android Studio remains
uninstalled; audit its actual paths after installation.

The earlier editor fixture leaked Zen runtime state through shared host IPC.
The unused records were archived/removed and the fixture corrected with an IPC
namespace and private `/dev/shm`. The user confirms actual Unreal relaunch is
normal: Zen ready in 0.058 seconds, editor startup 12.612 seconds, no errors.
Production policy and the retained expensive caches were unchanged.

Final var cutover, final physical normal/recovery chain, raw backing pruning and
legacy retirement remain gated. Cache overlays propagate into apparent persist
paths; later pruning requires a private non-recursive raw backing view. No
backing, legacy subvolume or snapshot was retired. Fresh GitHub API queries at
the reviewed head found zero branch workflow runs, zero check runs and no open
PR for this branch. Obtain exact-head CI after final source freeze.

Prior readiness branch: `feat/pre-optimization-readiness`, based on main
`f89205c07e4d3a77900b046a5bf937944488647b`. Obtain the current source with
`git rev-parse HEAD`; documentation does not embed its own future commit hash.
[PR #7](https://github.com/P2949/NixosConf/pull/7) remains open and draft.
GitHub [PR #7 checks](https://github.com/P2949/NixosConf/pull/7/checks) on
its current head are authoritative for CI status. Historical exact runs remain
in plan.md. Record final exact-head CI in the PR body and annotated baseline tag
after it completes; a source document cannot certify its own future CI run.
The canonical baseline binds source, lockfile, artifacts and physical evidence.

## Accepted boot candidates and physical history

Generation38 was physically booted and accepted; its normal candidate was
`bjxxpsm7f42b909v9gpf48p7pinajc3x`, boot`b07efa9b-0e60-425f-ba36-d1eb038327cd` after the recovery return.
Fresh root and private machine-ID equality passed. Generation38 normal`bjxxpsm7f42b909v9gpf48p7pinajc3x`
and persistent-root`8v183hn0p5yv7wf625yj38n6bhsjpxz6` ESP kernel/initrd copies
match their store artifacts. Boot-only installation and the coordinated normal reboot passed.
Version: `26.05.20261004.0d9e9b8`; kernel6.18.55.

| Candidate | Store identity |
|---|---|
| Generation38 normal | `bjxxpsm7f42b909v9gpf48p7pinajc3x` |
| Generation38 persistent-root | `8v183hn0p5yv7wf625yj38n6bhsjpxz6` |

Both closures have independent GC roots; their ESP kernel/initrd copies match
store artifacts. Generation37 remains the accepted physical root-chain baseline.
Physical normal→persistent-root→normal chain is ACCEPTED. First normal:
boot`d7c64889-aac3-4d09-8d14-5add9050cea3`, root300, resetcount6.
Persistent-root: boot`c6316fb4-f649-44b0-a8f6-8c4ae75be117`, same root300/UUID
and both sentinels retained, no reset increment. Accepted return-normal:
boot`36b6a76b-44bb-44c7-894c-ea52a060e538`, fresh root302,
UUID`8ec15d12-a1c8-4e40-8539-d97bde501f76`, resetcount7. Root-local sentinel
removed, persistent sentinel retained. Identity/credentials, persistent mounts,
journals, services, network and active Wayland login pass. Commander active,
zero restarts; temporary capture unit removed. No further reboot scheduled.

## Accepted gates

- Full offline suite: flake checks, five root scenarios, workstation smoke,
  native activation actions and 45 guard fixtures.
- Independent blank-disk reconstruction: actual desktop composition, installed
  UEFI boot, reset/recovery/return and seven subvolumes inspected read-only.
  Evaluated-Disko experiment was rejected after failed device rebinding;
  retain the proven direct production source import.
- Stock contamination negative fixture and live closure membership audit.
- Full Nix store content verification.
- Accessible physical KVM and successful QEMU KVM initialization.
- Physical GameMode governor/helper tests; CPU policies restored afterward.
- Btrfs read-only scrub147.36GiB/54s, no errors; all five counters zero.
  NVMe SMART pass, zero media errors/critical warning. Error-log count grew
  12143→12145; latest entry is admin InvalidFieldInCommand. Historical entries
  are not all classified; watch meaningful growth.
- Independent Ventoy home archive and representative restore, engine supplement,
  and separate secrets actual-recovery evidence reported by the user.

## Accepted representative workloads and remaining scopes

- Selected125W CPU verification passed15minutes/12workers; peak81C,
  no correctness failures or thermal-counter growth. Complete20GiB locked
  memtester pass also passed. Older80C cutoff aborts remain incomplete evidence.
- Actual Blender HIP render passed1920x1080/1024samples in105.21s,
  source unchanged. Interactive editing/workspaces accepted by user.
- Unreal configured map/120-second PIE lifecycle and installed-engine project
  rebuild covering all25 project C++ files passed. Interactive editing accepted by the user after normal work with no issues;
  these checks do not claim a full engine rebuild.
- Stardew Valley native Linux gameplay accepted by user and running ELF verified.
  Dark Souls gameplay/controls/audio accepted; uninterrupted final-source binding
  is now accepted on generation38; natural exit restored all12 CPU policies.
- Stage Pro functional USB playback accepted by user with independently observed
  sink/route. Latest snapshot has HDMI3 default and active Firefox/Stardew streams
  routed to the monitor; this does not revoke the accepted USB test. Preserve
  user routing. User confirms audible USB audio works after reboot and suspend;
  audible persistence accepted. Replug is not a mandatory test without actual use.
- HDR policy built and test-activated:10-bit desktop sRGB, automatic fullscreen
  HDR enabled, VRR true at155Hz. EDID advertises PQ/BT2020/static HDR metadata. Actual waterfall.mkv PQ/BT2020 output negotiated with native Wayland mpv;
  DRM DP-3 changed BT2020_RGB during fullscreen and Default after ordinary exit.
  User confirms correct HDR appearance, monitor HDR indication and normal SDR
  return after exit. Visual acceptance passed; EDID is not measured brightness.
- Exact physical recovery drill PASS: matched recovery closure and ISO hash,
  MP600 mounted `ro,rescue=nologreplay,subvolid=5`, required five subvolumes
  and repository/profiles/home/credential existence checked, clean unmount.
  USB receipt `receipt-20261008T000047Z.txt` copied and compared privately;
  SHA256 `61177a8ed57e0e67a7b1c87ded9bae0870c408832e61242147c33296403f45b6`.
  Return to generation38 normal closure verified, with no failed system units.
  Earlier script failures remain historical, superseded by this terminal PASS.

## Validation evidence and remaining actions

Remaining hard gates: representative multi-day soak; backup freshness;
frozen-source capture/manifest/exact validation/CI; PR ready/merge/tag.
Generation38 boot/resume, root-chain decision and Unreal interaction are closed.
Expected mounts, credential-source equality, persistent journal directory and
all12 powersave/balance_performance CPU policies passed read-only inspection.

1. All individual pre-soak gates are accepted by technical evidence and final
   user confirmation on2026-10-08.
2. Representative multi-day mixed-use soak began2026-10-08 on generation38.
   Use the machine normally; record meaningful workloads and any faults.
   Application uptime alone does not prove completed work. No additional
   synthetic stress or deliberate reboot is required for the soak.
3. Check backup freshness at freeze and protect meaningful new work incrementally.
4. Freeze source, capture the canonical baseline, run exact final checks/heavy
   suite and stock closure audit, verify exact-head CI, ready and merge PR7,
   compare the merged tree, and create the annotated baseline tag.

Android/Gradle/emulators and controller testing are not applicable by user
instruction. Bluetooth remains disabled by request. Unreal's normal editor exit
already completed successfully; no repeat interaction is required. Both125W
boot limits and their restoration after real suspend/resume are accepted.

No reboot is scheduled. Preserve the live session and batch required physical
interruptions when the user is available. No final manifest/tag exists yet.

## Recovery and backup

Retain generation35 fallback, forensic roots, candidate GC roots and receipts.
Accepted fallback closures: normal`czk5a2wn8di3pgv8a6w0b8aj3286g3h3`,
persistent`9ppcqjkfnid501na0wc8jjysynp0kp1p`; its physical chain passed.
The fallback generation keeps legacy home/var mounts. The current generation
has root-local home and legacy var; preserve originals and snapshots until final
granular physical/application acceptance and retirement prerequisites pass.

ISO identity`d55ny1z4d53slhz3ilvyy2mg6d8khrqn`; SHA256
`52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
Ventoy filename`nixos-workstation-recovery-26.05.20261004.0d9e9b8-x86_64-linux.iso`.
[Backup details](backup-restore.md): archive27,844,003,241bytes, SHA256
`9ec746a927b42c48484cb877d1d1916ca54f084f5ecdeffd3babc2f5ed1db212`,
plus47-file supplement. No format/repartition; verified restore and clean unmount.

## Retained firmware baseline

BIOS3201, ME14.1.53.1649/14.1.53.1649/14.0.51.1528. AI Optimized50/49,
Auto voltage, MCE RemoveAllLimits, cachemax48, AVXoffset0, XMP I DDR4-3200,
DRAM1.35V,100MHz BCLK. VMX/VT-d/Above4G enabled; ReBAR Auto and Linux
GPU BAR16GiB. Uncaptured firmware fields remain unknown, not reboot prerequisites.
See [firmware baseline](baselines/pre-optimization/firmware-20261005.md).

## Evidence and deferred work

[Development validation](development-validation.md),
[closure review](closure-review.md), [reconstruction](reconstruction.md),
[activation safety](activation-safety.md) and [plan.md](../plan.md) provide scope
and receipts. Architecture cleanup, module-doc generation and docs moves are
POST-BASELINE. Optimization-v2, VM variants, distributed builders and other
experimental ideas start from the accepted baseline tag; optimization remains inert.

## Continuation ownership

The2026-10-06 unified guide is recorded in full near the top of plan.md, with
source provenance and direct-user overrides. README is now an architectural
entry point; cooling thresholds and detailed inventories belong to source.
Formatting/local links passed; source CI and pending validation remain
separate evidence. Post-tag cleanup and optimization-v2 remain deferred.
