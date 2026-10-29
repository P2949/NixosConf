# Current status

The **productive desktop** advances on `main`, independently of the immutable
[qualification baseline](baselines/pre-optimization/baseline-final.md) and frozen
[benchmark control](stock-policy.md). Exact-source validation receipts live in local Git metadata under the
[local validation policy](local-validation.md). Historical acceptance records
remain in the [history index](history/README.md).

## Current release and next campaign

Productive NixOS 26.05 is accepted after the stable refresh and Impermanence
compatibility update. Keep this runtime and its package/input pins stable until
a concrete correctness or security issue requires a change.

The NixOS/Home Manager 26.11 migration is externally release-gated: require the
Nixpkgs `26.11` tag, the `nixos-26.11` branch and Home Manager's `release-26.11`
branch. A preliminary release branch alone is insufficient. After release,
qualify the migration with exact-source local validation and two physical
reboot/root-reset cycles, keeping both compatibility state versions at 26.05.

New optimization measurements are paused until migration acceptance, a review
of stable versus unstable productive dependencies, a new frozen 26.11 control
and fresh profiling establish readiness. Preserve the completed 26.05 results
and control identities as historical evidence.

## Storage and recovery

`@root` contains ephemeral root, home and ordinary var. Explicit retained state
is backed by `@persist`; separate mounts retain `@nix`, `@snapshots` and
`@optimization`, plus ESP and swap. Legacy home/var subvolumes are retired.
See the [persistence contract](persistence-contract.md).

Recovery uses Nix/GitHub/reinstall, separately tested secrets recovery and a
small local-only exception archive. The recovery ISO remains verified.
See [backup and recovery](backup-restore.md). The additional final-runtime soak
was disregarded by human intervention and is not a measured PASS.

## Productive policy and optimization

The accepted CPU package baseline is 125 W PL1/PL2, with boot/resume application.
Commander Core retains the accepted cooling policy. Bluetooth is disabled.
Accepted physical display/audio/workload and recovery evidence remains bound
to the baseline closures.

All eight scoped 26.05 optimization experiments are **COMPLETED**; their distinct
performance verdicts and adoption status are in the
[results index](../optimization/results/README.md). Generic and CPU-targeted PGO
established improvements above the predefined 1% practical threshold. No
optimization candidate is installed in the productive desktop.

The 26.05 BOLT decision is an evidence-based **GO for a future isolated experiment**, as recorded
in the [optimization policy](optimization.md#bolt-decision). This decision adds
no BOLT implementation or broader optimization campaign. The declared
measurement scope is complete; further optimization requires new evidence and a
separate proposal. The productive system, ordinary services, timers and retained
application state were recovered after the physical campaigns. Ordinary desktop
changes remain independent of the frozen control and its admission gates.

## Development applications

Prism Launcher is accepted through
[PR #16](https://github.com/P2949/NixosConf/pull/16). Its private launcher root,
accounts, instances/worlds/mods and meaningful state persist. Audited cache/log
children reset under granular Impermanence. See the
[application state audit](ephemeral-state-audit.md).

Android Studio is accepted through
[PR #28](https://github.com/P2949/NixosConf/pull/28). The writable SDK, AVDs,
settings, ADB/debug signing keys, projects and selected Gradle state persist;
audited IDE/Android caches remain disposable. Third-party IDE plugins and
physical USB-device workflows remain unexercised. See the
[Android workflow](development-validation.md#android-studio) and
[state audit](ephemeral-state-audit.md).

General maintainability cleanup is complete under the
[repository policy](repository-policy.md). Generated custom-module docs and the
[interactive desktop bootloader VM](development-validation.md#interactive-desktop-vm)
remain explicit developer tools. The
[interrupted-recovery debug driver](development-validation.md#interactive-interrupted-recovery-debugging)
provides a deliberate Btrfs checkpoint and local VSock SSH inspection. The
[disposable Minecraft staging environment](minecraft-server.md#disposable-staging-before-upgrades)
provides isolated version/mod and world-copy validation.
The [distributed-build VM proof](development-validation.md#distributed-build-routing-proof)
checks remote execution, output transfer and builder feature rejection while
retaining physical-only benchmark admission.
The separate [verity appliance](development-validation.md#standalone-verity-appliance)
boots a UKI with a read-only EROFS store and volatile root. Its QEMU test proves
normal readiness and explicit dm-verity failure after corrupting a private image
copy. It remains independent of desktop deployment and benchmark control.
The [immutable `/etc` VM](development-validation.md#immutable-etc-userborn-and-perlless-vm)
proves read-only configuration replacement, Userborn account updates and
perlless service operation across a switch and switch back. It remains a
disposable experiment; no physical desktop adoption is implied.
The [AArch64 binfmt VM](development-validation.md#aarch64-package-execution-through-binfmt)
checks a cross-built package's ELF identity and transparent execution, rejection
without its guest kernel registration, and recovery after restoring the rule.
This is functional packaging validation only.
The separate [kexec diagnostic image](development-validation.md#future-kexec-diagnostic-sessions)
provides a future headless maintenance environment. Its QEMU test enters the
standalone image with a new kernel boot ID and working diagnostic services.
No physical transition or performance qualification is implied.
The [Facter hardware comparison](development-validation.md#facter-hardware-comparison)
is complete. Its inferred policy did not justify replacing the curated hardware
configuration; raw reports and closure receipts remain private.
VM results do not replace physical acceptance.


Local Sabi-Noema coding agent (`codex-sabi`) is usable in **temporary degraded mode**
on the RX 9070 XT through llama.cpp ROCm: 49,152-token context, 40,000-token compaction
and ubatch 256. Unattended full command access remains enabled, subject to normal Unix
privileges and behavioral restrictions. The backend starts through a loopback socket
on demand and fully unloads with its proxy after 300 s idle; an existing Codex process
wakes it automatically. The GPU stays on Daily. The approximately 10% prompt-speed
loss is intentionally accepted pending a relevant backend/driver fix. Higher context
and larger micro-batches remain outside acceptance on the current stack. See the
[operating guide](local-agentic-coding.md).

Claude Code (VS Code extension) is accepted under granular Impermanence.
`.claude` and `.claude.json` persist privately; login, settings, resumable
transcripts and checkpoints survive normal reboots. `cleanupPeriodDays = 14`
was the mutable user setting at acceptance; NixOS does not own or enforce it. Its debug, session-env,
sessions, shell-snapshots and usage-data children reset each boot, proven by
two physical reboots. See the [state audit](ephemeral-state-audit.md).

## Minecraft server

Minecraft production is deployed on the desktop with automatic startup,
`Restart=always`, a six-hour UTC backup timer and transactional local Btrfs
recovery. Normal policy pins Minecraft 26.3, Fabric 0.19.5, OpenJDK 25, C2ME
executor four and G1. Distant Horizons and the Minecraft maintenance
specialisations are removed. Chunky 1.5.3 and locally extended Chunky Offline
1.1.0 are permanent production features: players online pauses all generation;
empty server applies pending centers and resumes saved tasks. All online players
are sampled every 200 online ticks, with a 75% square deadzone. The farthest candidate is
retained with its owner UUID across disconnects; near-center players cannot erase
it. The owner returning inside clears it. Radii are Overworld 10,000,
Nether 1,250 and End 5,000; Nether/End become enabled lazily on first visits.
Centers and visit state survive restarts. Empty-server tick pausing remains
disabled (`pause-when-empty-seconds=-1`). Six-hour backups remain enabled.
Spark background profiling is disabled.
See [Minecraft operations](minecraft-server.md).

The accepted stack, backup/recovery and maintenance behavior are recorded in
[PR #23](https://github.com/P2949/NixosConf/pull/23),
[PR #24](https://github.com/P2949/NixosConf/pull/24) and
[PR #26](https://github.com/P2949/NixosConf/pull/26). One unexpected-terrain C2ME
observation did not reproduce; causality remains unresolved.

Two simultaneous disposable protocol clients passed login/play, position
acknowledgement, saving while both were connected, clean disconnect and restored
player-data checks. A separate network namespace reached production TCP 25565
over non-loopback veth while management TCP 25585 remained inaccessible. The
unchanged natural 2026-10-25 00:00 UTC backup event completed with a new verified
read-only snapshot and clean health. Stopping the empty server and timer across
the real 06:00 UTC event, then restoring management readiness before the timer,
produced exactly one verified catch-up, clean recovery state and the normal
future schedule. Physical router/laptop behavior and maximum-player capacity are outside
this acceptance gate. Local Btrfs recovery covers
rollback on this device; total device loss is outside the declared backup scope.
