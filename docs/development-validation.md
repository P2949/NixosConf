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

## Android Studio

Home Manager's `development/android.nix` owns `android-studio` from the existing
pinned unstable input and `android-tools` from stable Nixpkgs. The newer stable
Studio channel supports the real project's AGP 9.3 toolchain; stable Nixpkgs'
Panda 4 supports only AGP through 9.2. Studio runs in the Nixpkgs FHS environment
and manages a writable SDK at `~/Android/Sdk` through **Tools → SDK Manager**.
Nix pins the IDE and shell
ADB; projects pin Gradle through their wrapper and select their Android Gradle
Plugin/dependencies. Studio's bundled JDK runs the IDE; use the project's
compatible Gradle JDK in Studio and a project dev shell for command-line builds.
The host has KVM membership for direct emulator acceleration.

The Android feature sets `ANDROID_USER_HOME=~/.android` and
`ANDROID_AVD_HOME=~/.android/avd` in the user session and Studio launcher.
Current SDK libraries otherwise follow `XDG_CONFIG_HOME` into `.config/.android`,
while the emulator's default search still uses `.android`. Explicit paths keep
SDK tools, Studio and the emulator on the retained identity/AVD tree. The SDK
itself remains writable and selected through SDK Manager.

Create Java projects using a Views-based template with **Language: Java**, under
`~/Development/Android/<project>`. The Compose templates use Kotlin. Choose SDK
components required by the actual course/project. The Nix SDK licence setting
allows Nix-built SDK packages; a Studio-managed SDK still uses SDK Manager's
own licence prompts. No SDK installation path is forced globally.

The [persistence contract](persistence-contract.md) owns retained paths.
Google settings/plugins use stable parents so IDE version changes retain state;
this does not authorize persisting other Google applications without an audit.
Gradle's mixed user directory is initially retained, including expensive
downloads. Audit its real children after normal use before introducing cleanup.
Keep Android Studio caches under ephemeral `~/.cache/Google`.

For deployment and physical acceptance:

1. Close Studio, Gradle daemons and emulators. Before the first normal reboot,
   copy any existing root-local SDK, Google settings/user data and `.gradle`
   into their declared `/persist/home/p2949/` backing paths, retaining metadata
   and verifying equality. Do not overwrite differing backing state blindly.
   If SDK tools have already used `.config/.android`, migrate its signing key,
   AVDs and other authoritative state into `.android` with collision/identity
   checks and updated AVD paths. Preserve the existing debug signing key.
2. Build/check the desktop and stage with
   `sudo nixos-rebuild boot --flake '.#desktop'`; use a controlled reboot for
   the new persistence mounts. Verify each new bind mount via
   `/proc/self/mountinfo`, including its persistent Btrfs root and ownership.
   A requested live installation must first quiesce affected applications,
   verify the backing copy and inspect a native activation preview. Verify
   the live mounts and retained data after switching; reboot acceptance remains
   separate. Live installation permits the project check before that reboot.
3. Launch `android-studio`, select `~/Android/Sdk`, create/open the real Java
   project and complete Gradle sync/build. Create an AVD in Device Manager and
   run/debug the app with KVM acceleration. The SDK emulator binary belongs
   inside Studio's FHS environment; a bare host invocation may fail to link.
4. Exit cleanly and capture retained-file hashes/metadata outside Git. Reboot
   normally again; reopen the project, verify SDK/AVD/settings retention and
   build/run again without reinstalling the SDK or system image. Confirm IDE
   cache reset separately from retained state.
5. Audit actual `.android`, SDK, Google and Gradle subtrees. Record unexercised
   workflows explicitly and keep credentials/private receipts outside Git.

Upstream references: [Nixpkgs Android support](https://github.com/NixOS/nixpkgs/blob/nixos-26.05/doc/languages-frameworks/android.section.md)
and [Android Studio configuration directories](https://developer.android.com/studio/troubleshoot#directories).
Check the [Studio/AGP compatibility table](https://developer.android.com/studio/releases#android_gradle_plugin_and_android_studio_compatibility)
when selecting an IDE for a project; do not downgrade a project's pinned
toolchain to make an older IDE pass acceptance.

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

## Interactive interrupted-recovery debugging

`interrupted-recovery-debug` is a deliberately invoked developer artifact for
inspecting the interrupted Btrfs root-replacement case over AF_VSOCK SSH. The
ordinary `interrupted-recovery` test remains unattended; its derivation does not
include the backdoor or the pause. The debug artifact is not a flake check and
is not installed in the productive desktop.

Build and run its interactive driver from a disposable working directory:

```sh
task_debug_driver="$(nix build .#interrupted-recovery-debug \
  --no-write-lock-file --no-link --print-out-paths)"
task_debug_work="$(mktemp -d)"
cd "$task_debug_work"
QEMU_OPTS='-display none' "$task_debug_driver/bin/nixos-test-driver"
```

At the Python prompt, enter `test_script()`. The test boots its VM, creates the
staged `@root-next` subvolume and pauses before creating the other data
subvolumes. At this checkpoint `@root` is absent, which exposes the interrupted
replacement state before recovery changes it. Copy the printed
`ssh -o User=root vsock-mux/.../machine_host.socket` command into another local
terminal. The desktop's systemd SSH proxy handles this per-run local socket;
no production SSH credential is involved. The backdoor provides unauthenticated
root access inside this disposable test VM only.

Useful commands inside the guest include:

```sh
journalctl -b --no-pager
systemctl --failed
systemctl status sshd.service
findmnt /mnt/impermanence-root
lsblk
btrfs subvolume list /mnt/impermanence-root
btrfs subvolume show /mnt/impermanence-root/@root-next
test ! -e /mnt/impermanence-root/@root
cat /proc/cmdline
bootctl status --no-pager
```

The top-level Btrfs filesystem is already mounted at `/mnt/impermanence-root`.
This allows direct inspection of the staged subvolume identity and missing
active root alongside the live journal, systemd and bootloader state. Return to
the driver terminal and press Enter to resume the existing recovery test.
After it completes, `exit()` or Ctrl-D leaves the Python prompt and cleans up the
VM. Socket paths are specific to the current run; use the command the driver
prints rather than a saved socket name.

## Distributed build routing proof

Run the disposable two-node experiment with:

```sh
nix build .#distributed-builds --no-write-lock-file --no-link --print-build-logs
```

The coordinator disables local builds and substitutes. It generates its SSH key
inside the guest and trusts the builder's freshly generated host key. Neither
private keys nor workstation builder credentials enter the Nix store. The
builder executes a sandboxed derivation whose output records the builder's
hostname; the test requires the output to be initially absent from both stores
and then valid with identical contents on both nodes. A second build requires
an advertised test feature. A build requiring the unadvertised `kvm` feature
must fail promptly without producing an output.

The hostname marker is a deliberately declared sandbox input used only to prove
execution location. This fixture does not establish reproducible benchmark
inputs or configure a productive remote builder. It also invokes the existing
optimization runtime admission function with the guest's observed identity and
requires rejection because the guest is virtualized. Distributed compilation
can produce candidates; authoritative measurements still require the designated
physical target and the complete optimization provenance gates.

## Standalone verity appliance

Build the separate image and run its explicit QEMU integrity test:

```bash
nix build .#benchmark-appliance --no-write-lock-file
nix build .#benchmark-appliance-test --no-write-lock-file --print-build-logs
```

The image output contains `benchmark-appliance_1.raw` and partition metadata in
`repart-output.json`. Its GPT disk contains an ESP with a UKI, an EROFS `/usr`
containing the Nix store, and a dm-verity hash partition. The root filesystem is
volatile tmpfs. Update by replacing the whole image; this appliance does not
provide an in-place NixOS switch or a writable package store.

SSH, DHCP networking, perf, turbostat, hwloc, numactl and the existing evaluation
benchmark runner are included. No login credential is shipped. To permit SSH,
add the operator's public key through the standard
`users.users.root.openssh.authorizedKeys.keys` option in the appliance
configuration and rebuild. Private keys stay outside the image. Serial output
reports the mount, verity, network and tool checks before emitting
`BENCHMARK_APPLIANCE_READY`.

The test boots the standalone image through UEFI with a disposable overlay;
it does not inject a guest agent or test credentials. It then changes one byte
in a private copy of the protected data partition and requires an explicit
verity corruption report and kernel panic. The original Nix-store image remains
unchanged. This tests integrity against the UKI's embedded root hash; the UKI is
unsigned, so this does not establish authenticated Secure Boot.

The image is independent of desktop deployment and the frozen benchmark
control. Its VM is for functional validation. The included benchmark runner
retains its physical control admission checks; booting this image does not
qualify it as an authoritative performance environment.

## Immutable `/etc`, Userborn and perlless VM

```bash
nix build .#immutable-etc-userborn --no-write-lock-file --print-build-logs
```

This explicit developer test imports Nixpkgs' perlless profile in a disposable
VM, enables read-only `/etc`, and lets Userborn maintain account files under
`/var/lib/nixos`. A service runs as a declarative UID and writes only to its
systemd-managed state directory. The test switches to a second configuration
with changed `/etc` content and an additional account, then switches back.
At each stage it checks the service's output and ownership, stable identity,
read-only `/etc`, and absence of Perl in the guest store. The profile also
rejects Perl dependencies when building the system closure.

Immutable `/etc` needs declarations for files that traditional services create
there. The guest declares a synthetic machine ID before PID 1 and D-Bus start;
it never copies the physical workstation's identity. Networkd and resolved keep
network/resolver runtime state under `/run`. Userborn's account files remain
outside `/etc`, with declarative symlinks into the immutable tree. These choices
belong to this experiment and do not alter desktop policy or persistence.

The guest uses its own store image rather than mounting the host store, so its
Perl absence check describes the guest closure. Build/runtime evidence from this
VM establishes functional behavior only; it does not establish a desktop
performance or maintenance benefit, and does not authorize physical adoption.
