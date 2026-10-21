# GPU workload-profile implementation and acceptance

**FAIL / NOT ADOPTED.** The post-switch kernel gate found two recoverable Unreal
graphics-ring timeouts under Daily Manual + POWER_SAVING. Generation 68 and the
original Automatic policy/hooks are restored. PR #59 remains a draft; passing
software checks and perceived responsiveness do not override the hardware gate.

Baseline: `35ed27115bad7c59e30f5847cc2bd2e548164802` (PR #58).
This change preserves the qualified 238 W / −150 mV, factory clocks, native fan
curve and zero RPM. It does not reopen electrical, fan or thermal qualification.

## Runtime preflight

LACT 0.10.1 on Navi 48 retained `POWER_SAVING` when the original Automatic
configuration was restored. Explicit `Manual + BOOTUP_DEFAULT → Automatic`
restored `auto + BOOTUP_DEFAULT`. The same reset passed after `3D_FULL_SCREEN`.
Stock and root Default therefore require a reset in LACT's application path;
changing only the GameMode helper would miss GUI/CLI selections and reloads.

The package patch was built independently before production policy edits. Its
enabled upstream tests passed. A temporary daemon override verified both manual
modes → Stock, both → Default, and both → original Automatic config reload.
Readbacks confirmed profile, DPM level, firmware mode, power cap, voltage offset,
fan curve and zero RPM. The original daemon/config was restored afterward.
See [reset readbacks](gpu-workload-profiles-2026-10-21/reset-smoke.json).
The first test script edited the file inside LACT's 1000 ms self-edit exclusion;
that attempt did not exercise the patch. Respecting that interval resolved it.

The historical Unreal benchmark had been removed during cleanup. The user
explicitly instructed that it must not be rebuilt and checked their existing
Unreal session instead. They reported normal responsiveness/no new stutter with
POWER_SAVING, and normal responsiveness/boost with no regression for
3D_FULL_SCREEN. Both five-minute captures retained the 238 W cap and dynamic
clocks. The Unreal log recorded `QUIT_EDITOR` and a normal shutdown; no kernel
GPU fault/reset/timeout was identified during preflight.

Those normal-use captures were not matched workloads. In particular, Unreal was
closed during the initial Automatic comparison; that capture is not evidence of
relative efficiency. The retained candidate captures are
[POWER_SAVING](gpu-workload-profiles-2026-10-21/power-saving-user-unreal.json) and
[3D_FULL_SCREEN](gpu-workload-profiles-2026-10-21/3d-user-unreal.json).

## Descriptive desktop-idle comparison

The user then agreed to leave the desktop unchanged for two five-minute
captures, Automatic first and POWER_SAVING second, each after 20 seconds settling.
No builds or browsing ran during measurement. The original daemon was used;
Automatic was explicitly reset to `BOOTUP_DEFAULT` before/after the pair.

| Mean/readback | Automatic | POWER_SAVING |
| --- | ---: | ---: |
| Reported power | 24.13 W | 21.86 W |
| Core clock | 1070.72 MHz | 1348.86 MHz |
| VRAM clock | 448.00 MHz | 359.28 MHz |
| GPU busy | 7.74% | 6.56% |
| Peak edge/hotspot/memory | 40/43/45°C | 38/40/42°C |
| Power cap | 238 W throughout | 238 W throughout |
| Fan RPM | 0, one 137-RPM reading | 0 throughout |

POWER_SAVING showed 2.27 W (9.4%) lower mean reported power and lower average VRAM
clocks in this observation. It did not lower average core clocks. Background
activity varied, so this is a descriptive result supporting the narrow policy
choice, not proof of a universal or loaded-workload saving. Combined with the
user's responsiveness/boost checks, these observations supported trying Daily
mode 2 and Gaming mode 1. The subsequent kernel fault gate rejected adoption.

See [summary](gpu-workload-profiles-2026-10-21/idle-summary.json),
[Automatic samples](gpu-workload-profiles-2026-10-21/automatic-idle.json) and
[POWER_SAVING samples](gpu-workload-profiles-2026-10-21/power-saving-idle.json).

## Implementation ledger

- PASS: runtime persistence/reset gate before Nix edits; original policy restored.
- PASS: candidate user-workload checks and descriptive benefit observation.
- IMPLEMENTED: Stock/root mapping unchanged; Daily Manual/mode 2, Gaming identical
  except mode 1; Daily boot default, automatic LACT switching disabled.
- IMPLEMENTED: existing ownership-aware helper targets Gaming; Daily, Stock,
  Gaming, Default, external-choice, stale-owner and failure tests updated.
- IMPLEMENTED: exact policy freeze, equality-except-mode invariant, patched LACT
  package, desktop evaluation and CI routing; no extra watcher, state masks,
  clock limits, electrical/fan changes or Unreal benchmark replacement.
- PASS: focused Nix GPU policy, seven helper cases and desktop evaluation;
  CI-selection tests and formatting passed. The initial full flake check stopped
  because a pre-existing optimization training test requires `repository.rev`,
  unavailable in a dirty checkout; rerun from the clean implementation commit.
- PASS: full `nix flake check --no-write-lock-file --print-build-logs`,
  `nixos-rebuild build --flake .#desktop --no-write-lock-file`, and
  `nix build .#workstation-smoke --no-link --no-write-lock-file --print-build-logs`
  from clean implementation commit `a0f33c0c28712119958127b1479414ee7b34ce0e`.
- PASS: candidate generation activated; writable mode-0600 runtime YAML is
  semantically identical to source. Clock/voltage table, native fan curve and zero
  RPM match the original qualified readback; installed helper matches source.
- PASS: real `gamemoderun sleep 10` gave Daily mode 2 → Gaming mode 1 → Daily
  mode 2, and Stock auto/mode 0 → Gaming mode 1 → Stock auto/mode 0. The saved
  previous profile and receipt cleanup were checked. GameMode was restarted only
  while inactive so it loaded the new hooks. See the
  [physical readbacks](gpu-workload-profiles-2026-10-21/gamemode-smoke.json) and
  [smoke script](gpu-workload-profiles-2026-10-21/gamemode-smoke.py).
- PASS (responsiveness only): the user opened/used their normal Unreal project after activation and
  reported normal responsiveness with no new problems. No replacement benchmark
  or real-game qualification campaign was used. A 180-sample LACT capture reached
  2421 MHz, with peak edge/hotspot/memory 40/50/44°C and no throttle flags. See
  [post-switch telemetry](gpu-workload-profiles-2026-10-21/unreal-post-switch-telemetry.json).
- PASS (configuration only, before fault review): [candidate readback](gpu-workload-profiles-2026-10-21/final-readback.json)
  confirms exact source/runtime semantics and unchanged qualified hardware values.
  [Local checks](gpu-workload-profiles-2026-10-21/local-checks.json) retain command
  outcomes and the kernel fault check.
- FAIL: the final kernel review found `gfx_0.0.0` timeouts at 01:33:40 and
  01:33:50, attributed to `UnrealEditor` / `RHISubmission`. Each recovered through
  a ring reset. Daily Manual/mode 2 was still active when the failure was checked.
  See the [kernel evidence](gpu-workload-profiles-2026-10-21/post-switch-kernel.log).
  The heuristic is not proven to be the root cause, but the no-GPU-fault gate
  failed. Empty thermal-throttle flags do not negate graphics-ring timeouts.
- NOT ADOPTED: no electrical, voltage, fan, clock-limit or DPM-state compensation
  was attempted. The manual pair must not be merged on this evidence.
- PASS: original runtime config applied through the patched daemon first, which
  explicitly reset mode 0, followed by `nixos-rebuild switch --rollback` to
  generation 68. Both running system and boot profile point to the original
  closure. The runtime config is byte-identical to baseline `35ed271`; clock,
  voltage, fan and zero-RPM readbacks match the qualified baseline. Original
  GameMode hooks were reloaded while inactive. See
  [rollback readback](gpu-workload-profiles-2026-10-21/rollback-readback.json).
- PASS: after reopening the project under original Automatic, the user again
  reported normal responsiveness/no new problems. The kernel showed no new GPU
  fault/reset/timeout from the restored daemon's start through the short control
  window. See [Automatic control](gpu-workload-profiles-2026-10-21/automatic-control.json).
  This does not prove root cause, but provides no reason to change the qualified
  electrical/fan settings.
- INCOMPLETE: the requested production pair is not adopted. PR #59 stays draft
  with failure evidence; production remains original Automatic. Any alternate
  architecture needs an explicit user decision rather than silently substituting
  a different Daily mode or weakening the failed gate.
