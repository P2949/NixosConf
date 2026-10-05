# Development validation

> Current update, 2026-10-05 after the user reboot: VMX enabled in photos,
> /dev/kvm accessible, QEMU KVM initialization PASS (guest paused).
> Earlier VMX-disabled observations below are historical. Actual Android
> emulator acceptance remains open. See [firmware observation](baselines/pre-optimization/firmware-20261005.md)
> for the captured AI Optimized50/49, MCE/XMP policy and remaining unknowns.


Enter the pinned development shell with `nix develop .#default`. GCC, Clang,
debugger and build tools belong to this environment; clangd remains owned by
Home Manager. Open project tooling from the intended environment and generate
a compilation database for the actual build.

For a trusted Nix compiler wrapper, clangd needs a scoped query permission to
discover its C++ standard-library include paths. For example, inside the shell:

```bash
clangd --query-driver="$(command -v clang++)" \
  --compile-commands-dir=/path/to/build
```

Use the exact compiler recorded in the project's compilation database. Avoid a
wildcard permitting arbitrary project executables. Compiler options such as
`-std=c++20` belong in the compilation database, not clangd's command line.
Unreal must continue to use Epic's project toolchain/sysroot; this general
shell smoke does not replace its build acceptance.

The preparation C++20 smoke compiled and ran a standard-library program;
clangd built its AST/index with zero errors using the exact wrapper query.
Final validation of the activated system and actual projects remains pending.

## Android virtualization gate

The post-firmware normal boot exposes accessible `/dev/kvm`; QEMU KVM
initialization passed on the physical host. Actual accelerated Android emulator
boot/project acceptance remains open. No SDK/AVD was found in the inspected
`~/Android`, `~/.android` or `~/Development` locations; this is scoped discovery,
not proof that no SDK exists elsewhere.

## Physical workstation preparation evidence

On 2026-10-05, Blender 5.2.2 LTS detected the RX 9070 XT as a HIP device.
A background factory-scene Cycles render selected only that GPU, disabled CPU
rendering and produced a 512x512 PNG at 32 samples in about 2.3 seconds. The
process exited cleanly with no new targeted kernel GPU fault/reset messages.
This is a basic render smoke; representative project and sustained-load
acceptance remain required. Factory startup left user preferences untouched.

The actual Unreal editor target also passed an incremental build through the
existing Steam FHS wrapper. UBT reported Epic's bundled Clang 20.1.8,
Rocky Linux 8 toolchain/sysroot and bundled libc++; one shared-library link
action executed. A full recompilation and editor/project play acceptance
remain separate requirements.

Run the project build from its home directory, which is visible inside the
Steam FHS environment. `/etc/nixos` is not a usable FHS working directory:

```bash
cd "$HOME/Development/Unreal/Projects/AI_Gavin_Project"
steam-run "$HOME/Development/Unreal/Engines/UE_5.8.2/Engine/Build/BatchFiles/Linux/Build.sh" \
  AI_Gavin_ProjectEditor Linux Development \
  -Project="$PWD/AI_Gavin_Project.uproject" \
  -MaxParallelActions=2 -WaitMutex -NoHotReload
```

Do not substitute ambient Nix compilers for Epic's intended project toolchain.
Private test receipts and build logs are retained under `/persist`; generated
render output remains under `/tmp`. These results describe the currently
running trial generation, pending final acceptance of the staged candidate.

### Unreal Wayland project/map lifecycle

The existing wrapper subsequently launched the actual project with temporary
SDL Wayland selection and Vulkan. SDL3 reported `wayland`; the compositor
reported a mapped native client (`xwayland=false`). Vulkan selected the
RX 9070 XT/RADV GFX1201 with Mesa 26.1.8. The configured startup map loaded
with 28 actors and remained active for ten seconds of editor ticks before
orderly exit with code 0 using the unchanged default Mimalloc allocator.
Interactive gameplay and the final candidate/soak remain pending.

Automation scripts must respect the editor's shutdown lifecycle. An immediate
`SystemLibrary.quit_editor()` from the map-loading script caused an ICU/Slate
cleanup crash. The corrected probe used
`EditorPythonScripting.set_keep_python_script_alive(True)`, a post-tick hold,
and then cleared keep-alive so the native script executor deferred closing.
It completed successfully with the default allocator. A diagnostic
`-ansimalloc` trial also exited, but no allocator workaround was adopted.
The intentionally failing probe/core is retained privately as harness evidence.

Steam FHS uses a private `/tmp`; scripts and receipts that must cross that
boundary belong in a private directory under home. The project itself remained
Git-clean. Shutdown Vulkan suballocation warnings remain recorded for later
workload review; the smoke result is not a claim of warning-free operation.

### GameMode authorization and stock mitigations

The earlier generation failed governor authorization because the user lacked
`gamemode` membership. On the final candidate after the firmware reboot, the
user has that membership and `gamemoded -t` passes all tests, including actual
CPU governor switching. All twelve policies return to powersave and
balance_performance; split_lock_mitigate remains1 and GameMode is inactive
afterwards. The receipt is `/persist/nixos-readiness-20261005/post-vmx-gamemode.json`
(mode0600). This closes the physical GameMode helper/governor gate; representative
gameplay remains separate. The real-profile VM also checks an unrelated-user
authorization deny control.

The candidate declares `general.disable_splitlock=0`. GameMode may temporarily
request the performance governor for games; it should preserve split-lock
mitigation. No permanent performance governor, GPU clock tuning or global
compiler settings are introduced. The test left all physical CPU governor/EPP
values unchanged and GameMode inactive afterwards.

### Audio routing evidence

Creative Stage Pro is detected by USB and ALSA. Its current PipeWire device
profile is Off; the active/default output is HDMI 3. A one-second silent PCM
passed direct ALSA playback on the Stage Pro, and separately passed the current
PipeWire default. No profile, sink, volume or default route was changed.

This establishes hardware/default transport availability, not audible Stage
Pro playback through PipeWire or reconnect acceptance. Preserve the current
route until the intended output is established; do not infer a configuration
bug merely from an inactive peripheral profile.

### Gamescope and MangoHud smoke

Nested Gamescope 3.16.23 completed 600-frame Vulkan cube runs with both
native Wayland and XCB/XWayland clients on the physical RX 9070 XT. Both
exited zero; MangoHud 0.8.3 initialized, and the XCB child mapped both the
overlay library and shim. Temporary small windows closed without restarting
the compositor. Keyboard/cursor and shutdown warnings remain in private logs.
The outer display selected 155 Hz; HDR was disabled. This does not establish
representative gameplay, HDR, controller or final-candidate acceptance.

### Sustained CPU test remains open

A planned 30-minute stress-ng CPU/all-method verification run on 2026-10-05
used 12 workers at nice 19, with five-second sensor checks and an automatic
stop at the conservative 80 C high-temperature boundary exposed by coretemp.
It stopped after about five seconds when sampled temperature reached 80 C.
No throttle-counter increases or matching new kernel hardware/thermal errors
were observed; cooling remained active and temperature returned to about 30 C.
The stressor's short-run verification reported no failures, but the wrapper
correctly recorded an aborted thermal test. This does not pass the requested
30-minute gate or prove OC stability. Review firmware/OC/power/cooling state
before repeating a sustained test; no temperature boundary or cooling policy
was changed to force a pass. Private receipts are retained under
/persist/nixos-cpu-thermal-20261005. The graphical session remained active.

Journal timing confirms the keeper commanded 100% fan duty at 10:55:16.405
UTC, within the approximate 10:55:13.778–10:55:18.838 stress interval, then
returned to 60% at 10:55:30.408 after cooling to 28 C. This proves the control
response was logged before the conservative stop; it does not measure actual
fan RPM or establish cooling capacity for sustained load. PID 912 and the
service invocation remained unchanged.

### Actual Blender project load and GPU render

Both discovered local Blender files loaded in background mode with unchanged
SHA-256 hashes. Each contains a 33-object Cycles scene and camera; inspection
detected no missing file-backed images or linked libraries. This does not
prove every procedural/driver/external dependency is available.

The newer file rendered its actual camera at original 1920x1080 resolution
and 100% scale, with 64 samples chosen in memory. RX 9070 XT HIP was the
only enabled device; CPU rendering was disabled. Rendering took 11.83 seconds,
produced a PNG and exited zero within a 180-second process limit. No project
or user preferences were saved. The source hash remained unchanged; no new
targeted kernel GPU fault/reset/timeout messages were found. The existing
CUEW initialization warning remains recorded, while the selected HIP path
worked. Cooling and graphical session remained active.

Root-private receipts: /persist/nixos-blender-project-validation-20261005.
Rendered output is private temporary data, not a public repository artifact.
This extends the factory smoke to an actual local scene; longer rendering,
interactive workflow and acceptance on the final candidate remain pending.
