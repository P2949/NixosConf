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
