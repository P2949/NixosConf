# Development validation

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

On the current physical boot, the user belongs to `kvm`, but `/dev/kvm` is
absent and the kernel reports `VMX (outside TXT) disabled by BIOS`.
Enable firmware virtualization during the batched firmware maintenance window
before claiming accelerated Android emulator acceptance. A passing software
VM test is not evidence that physical KVM works.

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
