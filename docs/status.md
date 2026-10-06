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

1. Complete sustained validation of the tuned cooling policy. User confirms
   H150i Elite Capellix pump/fans/airflow with mechanical ramp delay. Earlier
   response diagnostic passed real editor/map startup at72C from60% idle duty.
   Source fdf63d3 adopts high50C/delay0,low45C/30s,poll0.5s. Test-active normal
   candidate`pl4iy6fdvgjanswwwvvvja42p17p40zd`, persistent candidate
   `4rkvhfwj2vvj932ck5hp2izvrs65dp2f`, GC-protected. The host now declares
   a125W boot service and resume reapplication; test-activation/readback passed. Kernel/initrd unchanged;
   activation preview restarts only Commander. Boot default still accepted
   generation37/0p67xd; do not call tuned policy durably deployed yet.
   Guarded30-minute12-worker CPU trial stopped at80C after457.98s: verification
   errors0, throttle counters unchanged, but required duration incomplete.
   User adopted125W baseline on2026-10-06. Both runtime package long/short
   limits now125W with verified readback; timewindows unchanged. Guarded
   The15-minute12-worker125W
   trial stopped at thermal80C guard after295.43s, sampled peak83C, bothlimits
   still125W. Zero worker errors do not override incomplete duration/guardstop.
   Runtime125W remains applied by the test-active declarative service;
   boot deployment, physical resume and thermal acceptance pending.
   Investigate measured load power/voltage/clocks and AIO heat transfer;
   retain80C guard and avoid unchanged-load retries. The24GiB RAM attempt stopped at
   the3GiB desktop-headroom guard after496.96s, peak79C; incomplete, not passed.
   The separate22GiB pass also stopped after718.36s at the256MiB swap-growth
   guard, peak79C. Neither completed; substantial RAM gate remains open.
   Desktop/cooling remain active, no failed units or targeted kernel errors.
   Retain all guards and arrange stable headroom for a substantial full pass.
2. Sustained CPU/cooling and substantial RAM stability during a dedicated period.
3. Real Unreal editor/PIE and appropriately broad build; interactive/sustained
   Blender; native/Proton games,
   controller, intended audio/reconnect, normal desktop/Bluetooth and HDR/VRR
   where used. Android tooling, Gradle projects and AVD/emulator validation
   are NOT APPLICABLE by explicit user instruction on2026-10-06: this machine
   will not perform Android work. No Android setup or project input is needed.
   Installed Dark Souls Remastered/app570940 and Proton Experimental provide
   a real Proton candidate. No native game identified in inspected manifests
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
