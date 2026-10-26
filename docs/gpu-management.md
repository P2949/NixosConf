# GPU policy

Daily and Gaming are the accepted production profiles. The previously observed
Unreal timeout was resolved by the user and is no longer an adoption blocker.
The workload policy was accepted through [PR #59](https://github.com/P2949/NixosConf/pull/59).

The desktop boots into **Daily**: 238 W, −150 mV, factory core and VRAM clocks,
Manual performance level with the `POWER_SAVING` firmware workload heuristic,
native PMFW fan curve and zero RPM. Gaming uses the same electrical, clock and
fan configuration with `3D_FULL_SCREEN` instead. Both retain dynamic clocks and
all factory DPM states; neither adds clock limits or enabled-state restrictions.
The curve is
30°C/20%, 40°C/30%, 45°C/50%, 50°C/70%, 55°C/100%. The native curve uses the
firmware's hotspot sensor; the serialized software temperature key is retained
from the validated configuration.

`Stock` and the underlying `Default` preserve the exact original 340 W / 0 mV
configuration. Stock is an exact recovery/reference policy. Historical sustained
heavy-load thermal acceptance failed for Stock; Daily is the normal workstation
policy, including workloads launched without GameMode.

## Configuration ownership

[The desktop source](../hosts/desktop/lact-policy.yaml) is the canonical LACT
version-7 configuration. Stock and the root Default mapping preserve the original
factory reference. Daily and Gaming preserve the qualified 238 W / −150 mV / fan
policy and differ only in `power_profile_mode_index` (2 and 1). LACT automatic
switching remains disabled; no profile rules or hooks are installed.

On this Navi 48 stack, returning from Manual to Automatic leaves the selected
firmware workload mode active. The [LACT package patch](../packages/lact/lact-auto-reset.patch)
restores `Manual + BOOTUP_DEFAULT` before applying Automatic when no firmware
mode is configured. This covers GUI/CLI selection, Default, daemon start/reload
and GameMode restoration without another switching owner. Stock's YAML stays
unchanged. A missing firmware-mode interface remains supported; other read/reset
errors fail the operation. Keep this patch until an upstream fix preserves the
same restoration behavior, and verify it when updating LACT.

`gpu-lact-config-seed.service` atomically installs this source as a regular,
root-writable `/etc/lact/config.yaml` before `lactd` starts. `/etc/lact` is not
persisted. Runtime edits last for the current boot; the next boot returns to Daily
and the declarative definitions. Change the source in Git for lasting changes.

The seed remains active after completion, so restarting `lactd` does not reseed or
reset the selected profile. Source changes trigger both the seed and daemon to
restart in order during activation. Leave `services.lact.settings` empty: that
option would install an immutable symlink, conflicting with writable runtime
profile selection.

## GameMode

Native GameMode custom start/end hooks call `gamemode-gpu-profile`. Steam launchers
are unchanged. Games that use GameMode select Gaming.

At GameMode start, the helper saves the current profile and selects Gaming only if
needed. At end, it restores the previous profile only while Gaming is still active.
A later manual profile selection is preserved. Starting from Gaming causes no
profile write. Normal use gives Daily → Gaming → Daily; starting from Stock gives
Stock → Gaming → Stock, including restoration of `BOOTUP_DEFAULT + Automatic`.

State and the `flock` lock live in the user's mode-0700
`$XDG_RUNTIME_DIR/gamemode-gpu-profile` directory. Failed operations return a
nonzero status and log to stderr; failed selections retain the state receipt.
Duplicate callbacks are idempotent. Boot and GameMode-daemon identity prevent
restoration from stale ownership. No additional daemon or root helper is used.

Inspect `lact cli profile get`, `lact cli profile auto-switch get`,
`systemctl status lactd gpu-lact-config-seed`, and the GameMode user-service
journal when diagnosing switching. Preserve a retained helper receipt when
investigating a failure; do not overwrite a manual profile choice to hide it.

## Validation and maintenance

The exact Stock/Daily/Gaming policy semantics and Daily/Gaming equality except
for the workload heuristic are regression-tested by `gpu-policy` on every
`nix flake check`. Full mapping equality rejects additional clock/state overrides.

The flake includes fake-LACT helper cases, real desktop configuration
assertions, and the existing workstation VM extended for hook installation,
runtime locking, writable seeding and daemon-restart ordering. The VM does not
prove physical AMD clocks, power, temperature or fan behavior.

Prior electrical, fan, boot, daemon-restart and accepted suspend evidence remains
closed. The Daily/Gaming workload-heuristic policy is accepted; do not rebuild
the removed historical benchmark or reopen electrical/fan qualification.

For ordinary NixOS/configuration updates, run `nix flake check` and
`nixos-rebuild build`, switch/reboot as normally appropriate, and confirm Daily
is active. No GPU workload is required for unrelated configuration changes or
package refreshes without material GPU-stack changes.

Material changes to kernel/amdgpu, Mesa/RADV, LACT or its schema, GameMode, the
profile helper, policy YAML, electrical settings or fan curve require a compact
regression after the same automated checks and normal activation:

1. Verify exact Daily: 238 W, −150 mV, factory clocks, accepted PMFW curve,
   zero RPM enabled, Manual + `POWER_SAVING` and LACT auto-switch disabled.
2. Verify Daily → GameMode → Gaming → client exit → Daily, modes 2 → 1 → 2;
   also verify Stock restoration ends at Automatic + `BOOTUP_DEFAULT`.
3. Run one representative approximately 10-minute GPU workload. Require no
   thermal flags, hotspot and memory at most 95°C, and no GPU reset/fault.
4. Return to Daily and verify zero-RPM recovery, then stop.

Reopen only tests relevant to an actual regression: fan tests for changed fan
behavior, electrical/stability tests for instability, helper/profile tests for
GameMode restoration, or lifecycle/readback for boot recovery. Do not routinely
repeat the historical transition/static/motion/light-use matrix.

`main` owns production implementation. The experimental evidence may be archived
in one verified offline Git bundle and removed from GitHub and the active
checkout. Do not merge it into main or append routine health logs. Future
experiments use fresh branches. Generation 62 is optional retained
historical recovery, not an outstanding acceptance gate. No special retirement
test is needed; retain it until newer known-good generations make it unnecessary.

Keep the existing automated coverage. Additional automatic LACT rules,
supervisors, periodic health loggers and thermal rollback daemons are not needed.
