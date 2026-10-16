# GC ThinLTO build and functional preparation

This package-only matrix extends the identified Nix evaluation workload. It
retains GC 8.2.12, large-config mode, initial mark stack 1048576 and the existing
configure/make policy, including default amalgamated compilation. It does not
change the productive desktop, frozen control or prepared CPU experiment.

| Variant | Compiler/linker | CPU flags | LTO |
| --- | --- | --- | --- |
| `gcc-stock` | Existing stock GCC toolchain | Existing baseline | None |
| `gcc-cpu` | Existing stock GCC toolchain | Skylake | None |
| `clang-stock` | Matched Clang/LLD | Existing baseline | None |
| `clang-cpu` | Matched Clang/LLD | Skylake | None |
| `clang-thinlto` | Matched Clang/LLD | Existing baseline | Thin |
| `clang-cpu-thinlto` | Matched Clang/LLD | Skylake | Thin |

Changing GCC to Clang also changes the linker. The Clang controls make the LTO
comparisons independent of that toolchain bridge. Compare `clang-stock` against
`clang-thinlto`, and `clang-cpu` against `clang-cpu-thinlto`; a GCC-to-Clang
comparison cannot attribute an effect to LTO alone.

From a clean committed checkout:

```bash
nix build .#boehmgc-lto-matrix --no-write-lock-file
nix build .#boehmgc-lto-functional --no-write-lock-file --no-link --print-build-logs
nix build '.#boehmgc-lto-clang-thinlto^audit' --no-write-lock-file
```

The matrix records source revision/NAR, source and package derivations, exact
compile/link/configure/make flags, collector policy, the unchanged consumer and
explicit comparator pairs. It requires a committed source identity. Compiler
and linker version output, object format/hash, bitcode summary and saved
ThinLink indexes live in a separate `audit` output. Runtime libraries do not
refer back to that evidence or acquire a compiler dependency through it. Both
Clang controls use the same diagnostic linker flag to save intermediate files.
All package variants retain the upstream test suite.

The VM runs the exact Nix consumer against all six libraries, with a fresh home
and cache for each. It evaluates a known policy attribute from the existing
pinned real repository offline and verifies the actually initialized GC library
through loader output. It is a functional compatibility test, not a shortened
replacement for the full evaluation benchmark.

Build-cost observations and output-size receipts belong to source-bound
executions outside Git; wall clocks do not enter immutable library outputs.
Physical paired runtime measurements remain a separate gate using frozen
control admission and the complete benchmark corpus. The functional matrix has
a distinct kind and `FUNCTIONAL_ONLY_NOT_PERFORMANCE` acceptance marker; it is
not a performance build manifest or an adoption verdict. Dependency/system
variants and later combinations still require their preceding evidence.
