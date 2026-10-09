# Current readiness status

This file contains current truth only. [plan.md](../plan.md) preserves the
chronological ledger, supplied guides and superseded observations.

## Source, PR and CI

Active local work is `feat/granular-impermanence`, starting at reviewed
`de058b4b65416249e2a1ac2e722f7514c87d5a36`. The
[granular implementation plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
records actual receipts, application policies and the remaining gates.

Generation 46 normal is running: home and ordinary var are root-local.
Its quiesced var-only shutdown copy, first final physical matrix and discovery
checks pass; the user confirms representative application state works. Both
policies are frozen. Generation 42's shutdown copy and first home matrix passed.
Generation 44 fixes the intermediate random-seed bind and the observed Fuzzel
history omission, preserving only `.local/state/fuzzel`. The user confirms the
restored ordering. Both normal/recovery ESP artifact pairs match the exact store
closures; generation 41, original subvolumes and snapshots remain available.

Both accepted generation-44 recovery trials retained all 100 markers and the
same root ID 330/UUID, with stable identity, correct islands and healthy services:
`physical-boot-passed-f27d98d2-004e-4b1b-a803-68af4b8c4f20.json` and
`physical-boot-passed-56ff8f4f-9ba4-4c25-b6c5-0c45ae130634.json`.
The second accepted boot is `50c48157-a1fd-4542-a418-628b594f8106`; the user ran
the strict verifier immediately before applications. Independent receipt,
root identity, topology, Fuzzel state and service checks pass. Earlier failed
Codex/Firefox cleanup attempts remain archived and unaccepted.

The standalone checker nests proofs only where observed Codex/Firefox telemetry
cleanup skips directories. Eight marker regressions and the unchanged twelve
home-guard cases pass. Full flake checks and formatting pass; unchanged VM
results were reused. This is local validation, not GitHub CI evidence.

Both normal home trials also pass all 100 requirements:
`physical-boot-passed-74b64b81-8435-4cb6-82d8-e4f49aab5e96.json` and
`physical-boot-passed-c0483ba7-38e8-46b1-a5cf-5ba61b7f9b0e.json`.
The last home-only boot was `de9406f5-9eac-4e3a-9051-68797c98b8e4`. Home reset replaced
roots 330 → 332 → 334; latest UUID is `f7efa8c4-1329-af44-916a-2f8060f3a3ca`.
Each normal removed all 89 disposable proofs/three containers and retained the
11 persistent proofs before precise cleanup. Identity, islands, Fuzzel and
service checks pass. The unchanged independent home guard now passes two
consecutive verified normal cycles. No physical ticket remains pending.

The user reconfirmed all important application state after these generation-44
trials. Home acceptance is complete and its policy is frozen at recorded hashes.
Immutable source `/nix/store/0bqznjpxlyivhzr3d6dy4851qdx2h4ch-source` reproduces the
accepted home candidate and builds final desktop/recovery. Full flake checks,
evaluation, marker/home-guard checks and formatting pass. Fresh actual runs pass:
granular six-boot VM 185.78 seconds, all five root scenarios, blank-disk
reconstruction 287.38 seconds, and workstation smoke. Durable source/lock/closure
and runtime receipts are in `final-var-candidate-build.json` and the associated
`granular-final-var-*` logs; this is local evidence, not final exact-head CI.

After independently rerunning home acceptance, the existing var arming helper
installed the final candidate boot-only as generation 45. Normal closure:
`xbw73avz8hvpqq6p5qh6srnimxd8ism3`; recovery:
`6fl58xj2f8yqccmaxa4k89508nahigyc`. Both ESP pairs and generation-44 rollback
artifacts match their store closures. The user's orderly reboot completed the
var-only copy at `2026-10-09T21:05:09+01:00`; its immutable-policy comparison
passed before selecting generation 45. Source boot was
`de9406f5-9eac-4e3a-9051-68797c98b8e4`.

First final normal boot `971b1496-f119-46ac-a248-d23202cdab92` is accepted by
`physical-boot-passed-f0309ac2-5ee1-49c5-96a6-ae7610598589.json`: all 100 proofs,
92 disposable proofs/three containers gone and eight persistent proofs retained
before cleanup. Root 334 became 336, UUID `1d408d1a-0e0a-af4e-ada5-8095ba3b5d1d`;
reset count 21 became 22. Home/var are on @root; persistent islands, selected
service-state binds and protected random seed are correct. System running,
zero failed services, full connectivity, successful Home Manager/seed services,
Fuzzel history and configured audio route pass discovery checks. The user
reconfirmed representative apps work. Both policies are frozen in
`final-policy-freeze-20261009.json`; independent review is
`final-normal-accepted-cycle-1-review.json`. The missing pending ticket after
successful verification is expected cleanup.

Cleared the temporary generation-44 EFI fallback override after acceptance;
generation 45 normal is now default and both final entries remain installed.
Next is final recovery → recovery → normal, then gated raw-persist pruning,
post-pruning normal proof, legacy/snapshot retirement and final source/CI.
The user has saved/closed the named apps for the first recovery trial and will
verify from a text console before reopening them. No agent reboot is initiated
or scheduled; the full goal remains incomplete.

First final recovery passes all 100 proofs on boot
`6d1eb85e-cd9e-4857-a553-48bbf6384776`; receipt
`physical-boot-passed-8fd21368-c8c4-40ee-b40c-34b2fa71b345.json`. Root 336/UUID
and reset count 22 are retained; identity, topology, services and connectivity
pass independent review. Second recovery also passes all 100 proofs on boot
`20d82f78-9bb0-4106-839e-849bcb2f4ae8`, receipt
`physical-boot-passed-a41581f2-d86b-43a6-a7bb-1b6673b3f608.json`, with the same
root identity/reset count and healthy services/network. Return-normal is now
prepared with all 100 tokens present and normal generation 45 selected once.
Return-normal is accepted by
`physical-boot-passed-b07b3cd2-79b2-40c6-80b7-719e61c7a8e7.json` on boot
`3f599e92-e86e-40a9-831f-199acc327961`: new root 338/UUID
`9ece7cc1-ebd0-dd45-ae0b-ff25cf896f74`, reset count 23, 92 disposable proofs
gone and eight persistent proofs retained. Full topology/services/network pass.
The generation-45 final physical chain is complete.

The refreshed private raw-persist audit identified undeclared Unity editor
preferences/layouts. The user explicitly requests their preservation; the source
now declares `.config/unity3d/Preferences`. Old backing and the current root-local
version are protected independently. This narrow authorized policy amendment
requires a new exact candidate and physical acceptance before pruning or retirement.
Generation 45 remains running; no reboot or deletion has been initiated.

The corrected preference candidate is built from immutable source
`ca08qvh8cry5msxny61hfizgaiw54y02`; normal/recovery are
`15f6c5dsjl047j7my4c7cpkdhk6ly2xp`/`7lkx40kh36s809bz1yr9bmfdddy1n80a`.
Its evaluated manifest persists only the requested preference directory. Full
flake checks PASS; fresh granular VM 163.31 s, workstation smoke 14.26 s and
reconstruction 259.52 s pass; five unchanged root outputs reuse their accepted
fresh identities. Corrected generation 46 is installed boot-only, both ESP pairs
match, and main profile is normal 46. Generation 45 remains live/fallback default.
Firefox is now confirmed exited. Both Unity preference versions were compared;
the newer current working state is authoritative and all nine files/metadata
were mirrored to backing with a clean dry-run. The old raw version and earlier
current version are separately protected. Receipt:
`unity-preferences-data-reconciliation-20261009.json`.
All 100 normal proof tokens, nine preference hashes and both ESP pairs pass
preboot checks; generation 46 normal is selected once with 45 as fallback.
Corrected normal receipt `physical-boot-passed-cb942ba2-6d02-4541-9a24-e6c34da85f45.json`
passes all 100 proofs on boot `02df7ca1-88b9-4b02-aa53-d010cd84c0ef`: new root
340/UUID `11d42ced-4134-4c44-a97b-486904976a8e`, reset count 24. Preferences
is @persist-backed and all nine prepared hashes match; user confirms its UI
looks right. Services/network/identity/islands pass. Normal 46 is now default.
First corrected recovery is prepared with all 100 tokens and post-UI preference
hashes; recovery is selected once. Ready record:
`unity-preferences-recovery-cycle-1-ready.json`. Expect root 340/reset count 24
retained. Corrected recovery/return, pruning and retirement remain gated.

First corrected recovery passes all 100 proofs on boot
`7a7c767e-f23a-497b-9fba-546a2f6f86ba`, receipt
`physical-boot-passed-2348e96a-9c34-4ce8-8cd1-3b807c32b4d0.json`. Root 340/UUID,
reset count 24, Unity bind and all nine hashes retain correctly; services/network
pass. Second corrected recovery is prepared and selected once; ready record
`unity-preferences-recovery-cycle-2-ready.json`. Await self-reboot/verification
before apps, then return-normal. Pruning and retirement remain gated.

Second corrected recovery is accepted by
`physical-boot-passed-1873d5c4-88e9-4444-9fed-9589d62b26cb.json`, boot
`90a06fd5-8f0e-4e35-8497-26be2a38e332`: all 100 proofs, root 340/UUID/reset
count 24 and nine Unity hashes retained again; services/network pass.
Corrected return-normal passes receipt
`physical-boot-passed-3919c82a-ef26-4b58-be41-9633439795bb.json` on boot
`1107c458-f65a-4bbc-82f1-cf85eaf11a4e`. Root 342/reset count 25 replaces
root 340; all 92 disposable proofs disappear, eight persistent proofs and all
nine Unity preference hashes survive. Services/network/topology pass.
The corrected normal → recovery → recovery → normal chain is accepted and
policy refrozen in `corrected-policy-freeze-20261009.json`. The refreshed raw
inventory identifies 55 undeclared residues and 82 hidden cache directories;
pruning, post-pruning normal proof and retirement remain pending.

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
