# NixosConf

Declarative NixOS configuration for the primary desktop workstation.

The repository is intentionally organized around a simple rule:

> **Hosts contain facts, modules contain features, profiles compose features, Home Manager contains user policy, packages build software, and optimization contains experiments.**

The current configuration targets NixOS 26.05 and is built around a single `desktop` host.

## Repository structure

```text
.
├── flake.nix
├── flake.lock
├── statix.toml
│
├── hosts/
│   ├── desktop/
│   │   ├── default.nix
│   │   ├── hardware-configuration.nix
│   │   ├── disko.nix
│   │   ├── ephemeral-root.nix
│   │   └── persistence.nix
│
├── images/
│   └── recovery.nix
│
├── profiles/
│   └── workstation.nix
│
├── modules/
│   ├── core/
│   │   └── maintenance.nix
│   ├── desktop/
│   ├── gaming/
│   ├── compatibility/
│   ├── storage/
│   │   ├── btrfs-maintenance/
│   │   │   ├── default.nix
│   │   │   └── guard.sh
│   │   └── ephemeral-btrfs-root/
│   │       ├── default.nix
│   │       └── reset.sh
│   └── hardware/
│       └── commander-core/
│           ├── default.nix
│           └── keeper.py
│
├── packages/
│   └── liquidctl-pr886.nix
│
├── scripts/
│   └── nixos-baseline-info.sh
│
├── docs/
│   └── baselines/pre-optimization/
│
├── home/
│   └── p2949/
│       ├── default.nix
│       ├── cli.nix
│       ├── shell.nix
│       ├── desktop/
│       │   ├── default.nix
│       │   ├── appearance.nix
│       │   ├── hyprland.nix
│       │   ├── hyprland.lua
│       │   ├── waybar.nix
│       │   └── notifications.nix
│       └── development/
│           ├── default.nix
│           ├── blender.nix
│           └── unreal.nix
│
├── tests/
│   ├── default.nix
│   ├── workstation/
│   ├── hardware/commander-core/
│   └── storage/
│
└── optimization/
    └── default.nix
```

## Architecture

### `hosts/`

Host-specific facts and policy belong here.

For the desktop this includes:

- hostname
- bootloader configuration
- CPU microcode
- firmware policy
- disk layout
- Btrfs maintenance
- Commander Core device identity and cooling policy
- `system.stateVersion`

The host composes the workstation profile and hardware-specific modules.

### `profiles/`

Profiles describe machine roles.

`profiles/workstation.nix` composes the reusable workstation features and enables simple workstation policy such as:

- NetworkManager
- Bluetooth
- Polkit
- UDisks/GVfs
- Firefox

### `modules/`

Reusable NixOS functionality lives here.

Current groups include:

- `core` — Nix policy, guarded maintenance, locale, users, and baseline packages
- `desktop` — graphics, PipeWire, Hyprland, and portals
- `gaming` — Steam, GameMode, Gamescope, and MangoHud
- `compatibility` — `nix-ld`
- `hardware/commander-core` — reusable Commander Core cooling support
- `storage` — guarded ephemeral Btrfs root reset support

### `home/`

Home Manager owns user-session policy.

Desktop configuration is separated into:

- applications
- appearance
- Hyprland/session integration
- Waybar
- notifications

Development configuration is separated into:

- general development tools
- Blender
- Unreal Engine support

### `packages/`

Custom package derivations belong here.

`packages/liquidctl-pr886.nix` builds the pinned Liquidctl revision required by the Commander Core implementation.
It accepts an explicit source selected at the flake/module boundary.

Recovery and administration tools remain in `modules/core/packages.nix`.
Interactive tools such as ripgrep, jq, gh and btop belong to Home Manager's
`home/p2949/cli.nix`. Compilers, debuggers, build systems and Python are provided
by `nix develop`, which also contains the repository's Nix lint tools.

### `optimization/`

Reserved for controlled system optimization experiments.

This area is intentionally kept separate from the productive workstation configuration. CPU tuning, compiler tuning, LTO, PGO, and BOLT work should be introduced here only after establishing a stable architectural baseline.

## Stable and unstable nixpkgs

The main system uses the NixOS 26.05 nixpkgs branch.

A single `pkgsUnstable` package set is created at the flake boundary and passed to modules that explicitly require unstable software.

At present, Blender is sourced from unstable for the ROCm-enabled build.

This keeps unstable package usage explicit rather than allowing individual modules to instantiate independent package sets.

## Home Manager

Home Manager is integrated as a NixOS module and uses the same stable package set as the system through:

```nix
useGlobalPkgs = true;
useUserPackages = true;
```

The user identity is defined once at the flake boundary and passed to both NixOS and Home Manager.

## Commander Core cooling

The Corsair Commander Core is managed declaratively.

The implementation consists of:

```text
host cooling policy
        ↓
hardware.commanderCore options
        ↓
Commander Core NixOS module
        ↓
keeper.py
        ↓
pinned Liquidctl PR #886 build
```

The desktop currently uses:

- base fan duty: 60%
- high fan duty: 100%
- pump duty: 100%
- high temperature threshold: 65 °C
- low temperature threshold: 60 °C

The module uses systemd supervision and watchdog support.

## Unreal Engine

Unreal Engine itself is **not packaged by Nix**.

The externally installed engine currently lives at:

```text
~/Development/Unreal/Engines/UE_5.8.2
```

Home Manager provides:

- the required Steam FHS runtime environment
- an `unreal-engine` launcher

The wrapper launches the external Unreal installation inside the compatibility environment.

This distinction is intentional: Nix manages the launcher/runtime integration, not the Unreal Engine installation itself.

## Common commands

Build the desktop configuration without switching:

```bash
nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link
```

Check what activation would change:

```bash
sudo nixos-rebuild dry-activate --flake '.#desktop'
```

Activate the configuration:

```bash
sudo nixos-rebuild switch --flake '.#desktop'
```

Run all repository checks:

```bash
nix flake check --print-build-logs
```

Format the repository:

```bash
nix fmt
```

Verify formatting without modifying files:

```bash
nix fmt -- --ci
```

Enter the repository development environment:

```bash
nix develop
```

The development shell contains:

- `nixfmt`
- `nixfmt-tree`
- `deadnix`
- `statix`

## Lint policy

Statix is configured by `statix.toml`.

Two style-only rules are intentionally disabled:

- `empty_pattern`
- `repeated_keys`

Module-style argument patterns such as `{ ... }:` and separate dotted module option assignments are intentionally accepted.

`hardware-configuration.nix` is generated by `nixos-generate-config`. It is formatted with the rest of the repository but excluded from Deadnix's unused-argument check.

## CI

GitHub Actions runs:

```bash
nix flake check --print-build-logs
```

The flake exposes reproducible checks for:

- Nix formatting
- Statix
- Deadnix
- Desktop and recovery-specialisation evaluation
- Ephemeral-root configuration validation
- Baseline collector syntax and ShellCheck
- Commander Core option validation, Python syntax, Ruff and hardware-free unit tests

CI deliberately does not build the complete workstation closure.

The real workstation profile and Home Manager configuration have an explicit
headless integration VM: `nix build .#workstation-smoke`. Its guest storage,
test-only credentials and disabled physical cooling/reset services isolate it
from the host. This tests boot and service composition; it does not benchmark
the workstation or replace graphics, cooling and application acceptance.

## Impermanence validation

The desktop declares an ephemeral Btrfs root by default, with a
`persistent-root` recovery specialisation. Both variants persist machine
identity; home and `/var` remain persistent. Validation includes original opt-in physical trials and accepted normal/recovery
boots. See [current status](docs/status.md) for accepted artifacts and open gates.

See [ephemeral root validation](docs/impermanence.md) for the reset contract,
test commands, results and remaining physical acceptance gates. Explicit VM
tests cover safety, interrupted-reset recovery, machine-ID persistence and
transition to the persistent-root fallback. Heavy VM
tests are exposed as packages; ordinary flake checks include configuration
validation alongside formatting, Statix and Deadnix.

## Baselines

The known-good productive workstation before the architecture refactor is tagged:

```text
nixos-26.05-productive-baseline
```

That baseline includes the functional workstation configuration before repository restructuring.

The architecture checkpoint is tagged `nixos-26.05-architecture-baseline`.
The final pre-optimization baseline remains pending the acceptance gates in
[plan.md](plan.md).

## Optimization development

Pinned diagnostic tools are available with `nix develop .#validation`.
This shell includes CPU, thermal, storage and graphics inspection tools;
entering it does not run stress tests or change the workstation configuration.
Tools come from the pinned nixpkgs input; `turbostat` is selected from the
desktop's kernel package set.

The [baseline collector](docs/baseline-capture.md) records the current running
system and repository identities, diagnostic results and missing evidence
without activating configuration or running stress tests.

The [backup and restore ledger](docs/backup-restore.md) distinguishes verified
project remotes from the remaining independent home-data backup gate.

The [development validation notes](docs/development-validation.md) cover
project toolchain ownership, scoped clangd compiler queries and the current
physical KVM acceptance gate.

The [selected stable refresh](docs/stable-refresh.md) records its isolated
input update, complete offline validation, closure diff and matching recovery
artifact and the accepted physical boot sequence.

The [maintenance policy](docs/maintenance-policy.md) documents guarded GC/scrub
windows, rollback artifact retention and bounded persistent diagnostics.
Current acceptance and remaining maintenance tasks are recorded in
[current status](docs/status.md).

Optimization work begins only from the final tagged stock baseline described
in [current status](docs/status.md).

The intended progression is:

```text
stock baseline
    ↓
CPU-specific code generation
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

Each stage should remain independently identifiable and benchmarkable.

PGO/BOLT infrastructure should preserve provenance and fail closed when profile or binary identity does not match the expected derivation.

BOLT outputs must be represented as new immutable Nix derivations rather than modifying files in `/nix/store`.

The [stock policy audit](docs/stock-policy.md) records evaluated kernel, CPU,
memory and environment declarations and their remaining acceptance limits.
