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
