# Current readiness status

This file contains current truth only. [plan.md](../plan.md) preserves the
chronological ledger, supplied guides and superseded observations.

## Source, PR and CI

Branch: `feat/pre-optimization-readiness`, based on main
`f89205c07e4d3a77900b046a5bf937944488647b`. Obtain the current source with
`git rev-parse HEAD`; documentation does not embed its own future commit hash.
[PR #7](https://github.com/P2949/NixosConf/pull/7) remains open and draft.
[CI run 37381090051](https://github.com/P2949/NixosConf/actions/runs/37381090051)
passed Flake checks on exact reviewed head
`1f96e0d3696d7f3f566819ddc5c83ed866b6f838`. Documentation successors need
their own CI result; this does not certify a future head.

## Accepted boot candidates and physical history

Generation37 is installed. Version: `26.05.20261004.0d9e9b8`; kernel6.18.55.

| Candidate | Store identity |
|---|---|
| Normal | `0p67xd3scigqmmn65a0x5skdcsf6025b` |
| Persistent-root | `ph12l3y4k9jjmp5vhxwlkc11x4js2gjx` |

Both closures have independent GC roots; their ESP kernel/initrd copies match
store artifacts. Reinstallation is unnecessary unless runtime source changes.
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

## Partial gates

- Unreal final-candidate incremental build passed using Epic's toolchain.
  Editor/map attempt THERMAL ABORT at84C after6s under the80C guard.
- Actual Blender project HIP render passed on final candidate:1920x1080,
  64samples,12.6673s, source unchanged. Interactive/sustained work remains open.
- General C++20 compile/run and scoped clangd compilation-database check
  passed on the test-active cooling candidate; actual project workflows remain
  open. Synthetic Gamescope/MangoHud stack passed.
  Representative final workflows/games remain open.
- Silent PCM via current HDMI3 PipeWire default passed. StagePro enumerates
  without an active sink; intended audible/reconnect workflow is unaccepted.
- Recovery ISO build/hash/Ventoy copy passed; exact physical-drill provenance
  still requires reconciliation with existing evidence.

## Open hard gates and next actions

1. Validate the selected125W package policy using hardware/correctness evidence.
   Test-active normal`pl4iy6fdvgjanswwwvvvja42p17p40zd`, persistent
   `4rkvhfwj2vvj932ck5hp2izvrs65dp2f` built/GC-protected. Declarative
   power service and generated resume hook/readback passed; boot default
   remains generation37. Physical boot/resume remains pending.
   Earlier80C cutoff stops were incomplete tests, not proven overheating or
   hardware faults. User explicitly superseded the arbitrary80C criterion;
   block/paste history is not a prerequisite. The isolated15-minute125W trial
   passed:900.38s elapsed,12 workers passed/0 failed, peak81C, all24 thermal
   counters remained0, bothlimits125W, no guard stop or targeted new kernel
   faults. This accepts the user-selected15minute CPU scope on the test-active
   candidate, not exhaustive OC stability or physical boot/resume acceptance.
   Measured AIO pump/fans function; post-load coolant snapshots do not
   establish load-time warmup or contact. No firmware/voltage changes.
   Previous24/22GiB attempts remain incomplete. The separate20GiB/one-loop
   memtester pass completed in3036.55s: all16 enabled patterns ok, exit0,
   mlock successful, no guard stop, all24 thermal counters unchanged0,
   peak79C, minimum available8323716KiB and swap growth1084KiB. No matching
   new kernel faults or failedunits; session1Wayland active. Accept substantial
   tested-memory full-pass scope, not all installed RAM or exhaustive stability.
   EDAC controller counters are not exposed on this host.
2. CPU15minute and substantial20GiB RAM validation accepted on test-active
   candidate. Continue representative workloads before soak/freeze.
3. Real Unreal interactive editing and appropriately broad build remain open;
   configured-map/120s PIE/endplay/normal editor exit passed on the test-active
   candidate with project Git-clean and no matching new kernel faults. Interactive/sustained
   Blender interactive editing/viewport (longer1024sample real-project HIP
   render passed105.21s, source unchanged, no matching GPU faults); native/Proton games,
   controller, intended audio/reconnect, normal desktop/Bluetooth and HDR/VRR
   where used. Android tooling, Gradle projects and AVD/emulator validation
   are NOT APPLICABLE by explicit user instruction on2026-10-06: this machine
   will not perform Android work. No Android setup or project input is needed.
   Installed Dark Souls Remastered/app570940 and Proton Experimental provide
   a real Proton candidate. User reports gameplay/controls/audio worked
   perfectly; observed exit restored GameMode inactive and all12 CPU policies
   to powersave/balance_performance, with no targeted kernel faults. Session
   spanned test-activation; uninterrupted final-candidate binding remains open.
   No native game identified in inspected manifests
   or controller observed in current kernel input enumeration; actual play
   and controller acceptance remain open.
4. Reconcile existing recovery-drill receipts before scheduling another drill.
5. Check backup freshness at freeze; incrementally protect meaningful new work.
6. Multi-day representative soak after individual gates; final stock-policy and
   environment audit; canonical manifest; exact-source validation/CI; PR ready,
   protected-main merge and annotated baseline tag.

No reboot is scheduled. Preserve the live session and batch required physical
interruptions when the user is available. No final manifest/tag exists yet.

## Recovery and backup

Retain generation35 fallback, forensic roots, candidate GC roots and receipts.
Accepted fallback closures: normal`czk5a2wn8di3pgv8a6w0b8aj3286g3h3`,
persistent`9ppcqjkfnid501na0wc8jjysynp0kp1p`; its physical chain passed.
Home/var deliberately remain persistent. Do not prune before final acceptance.

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
