# GPU policy

The desktop boots into **Daily**: 238 W, −150 mV, factory core and VRAM clocks,
automatic performance states, native PMFW fan curve and zero RPM. The curve is
30°C/20%, 40°C/30%, 45°C/50%, 50°C/70%, 55°C/100%. The native curve uses the
firmware's hotspot sensor; the serialized software temperature key is retained
from the validated configuration.

`Stock` and the underlying `Default` preserve the exact original 340 W / 0 mV
configuration. Stock is an exact recovery/reference policy. Historical sustained
heavy-load thermal acceptance failed for Stock; Daily is the normal workstation
policy, including workloads launched without GameMode.

## Configuration ownership

[The desktop source](../hosts/desktop/lact-policy.yaml) is the canonical LACT
version-7 configuration. Its Stock and Daily definitions come directly from the
validated configuration. LACT automatic switching remains disabled.

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
are unchanged. Games that use GameMode share Daily; no separate Gaming profile is
created.

At GameMode start, the helper saves the current profile and selects Daily only if
needed. At end, it restores the previous profile only while Daily is still active.
A later manual profile selection is preserved. Starting from Daily causes no
profile write. Starting from Stock gives Stock → Daily → Stock.

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

The flake includes five fake-LACT helper cases, real desktop configuration
assertions, and the existing workstation VM extended for hook installation,
runtime locking, writable seeding and daemon-restart ordering. The VM does not
prove physical AMD clocks, power, temperature or fan behavior.

Final implementation acceptance requires one declarative boot/readback and one
10–15 minute DSR/GameMode Stock → Daily → Stock integration run, then returning to
Daily. Prior electrical, fan, boot and accepted suspend evidence remains closed;
ordinary use is a nonblocking soak.

Ordinary updates need a build, boot and exact Daily readback. Material changes to
the kernel/amdgpu stack, LACT schema, electrical policy or fan curve need a compact
regression: exact Daily, GameMode Stock → Daily → Stock, one representative
approximately 10-minute GPU load, and return to zero RPM. Reopen broader tuning
only when evidence justifies it. Preserve recovery generation 62 and the separate
evidence branch until post-merge acceptance succeeds.
