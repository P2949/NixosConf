# Development tooling

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

Historical workload results are retained in [baseline evidence](baselines/pre-optimization/evidence/development-validation.md).
The completed qualification state is recorded in the [canonical baseline](baselines/pre-optimization/baseline-final.md).

For Unreal, run project builds from the project directory in the supported
Steam FHS environment, using Epic's bundled compiler and sysroot. Do not
substitute ambient Nix compilers. Engine/project paths and target names belong
to the actual project; generated build products remain disposable.

## Interactive desktop VM

Build the real desktop configuration with its bootloader variant:

```bash
nixos-rebuild build-vm-with-bootloader --flake .#desktop
# Equivalent explicit build:
nix build .#nixosConfigurations.desktop.config.system.build.vmWithBootLoader
vm_launcher=$(readlink -f result/bin/run-desktop-vm)
mkdir -p /tmp/nixos-desktop-vm
cd /tmp/nixos-desktop-vm
"$vm_launcher"
```

The launcher defaults to a private `desktop.qcow2` overlay and EFI-variable file
in the working directory. Reuse them for guest state across restarts; choose a
fresh directory for a clean guest. `/tmp` guest state is disposable across host
reboots. Keep guest images and raw receipts outside Git.

This extends the real desktop modules, Home Manager, services and ordinary
packages. It uses 4 virtual CPUs, 8 GiB RAM, a 32 GiB virtual disk and UEFI
systemd-boot. Physical Commander Core/RAPL services, activation prerequisites,
Disko disk declarations and Btrfs maintenance are disabled. No physical disk or
workstation credential file is consumed. The normal desktop remains unchanged.

The guest uses a persistent ext4 root. `/persist` is an ordinary guest-root
directory, retaining the same system/Home Manager bind-mount declarations.
Btrfs root reset and boot-only disposable-file cleanup are disabled; disposable
application backing directories survive guest restarts. This exercises desktop
composition and persistence mounts, while the targeted Btrfs tests remain the
storage/reset validation tier. The physical @optimization requirement applies
only to Btrfs hosts.

Greetd starts the normal Hyprland session. The VM user `p2949` has the VM-only
password `vm` for a console login; normal sudo policy remains available. For
headless diagnosis, use `QEMU_OPTS='-display none -serial stdio -monitor none'`
with the launcher. Serial and graphical consoles are enabled only in the VM.

Build, UEFI boot, Home Manager activation, guest persistence/reboot, active
Hyprland and a rendered Alacritty window have been verified. System and user
units reported no failures. Human interactive input/audio and application
workloads remain unexercised in the VM; physical acceptance is separate.
The desktop VM is an explicit developer tool and is not built by ordinary CI.
