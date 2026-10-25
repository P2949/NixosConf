# Optimization results

Accepted public summaries of completed optimization experiments. Full runtime
evidence remains private outside Git. **COMPLETED** records measurement and
verification; performance interpretation and productive adoption are separate.

| Experiment | Stage | Status | Result |
| --- | --- | --- | --- |
| [zstd-skylake-v1](zstd-skylake-v1/) | zstd CPU codegen (`-march=skylake -mtune=skylake`) | COMPLETED | Compression inconclusive; decompression regression; not adopted |
| [boehmgc-skylake-v1](boehmgc-skylake-v1/) | Boehm GC CPU codegen with GCC | COMPLETED | Evaluation wall/CPU time inconclusive; not adopted |
| [boehmgc-clang-skylake-v1](boehmgc-clang-skylake-v1/) | Boehm GC CPU codegen with matched Clang/LLD | COMPLETED | Evaluation wall/CPU time inconclusive; not adopted |
| [boehmgc-thinlto-v1](boehmgc-thinlto-v1/) | Generic ThinLTO with matched Clang/LLD | COMPLETED | Evaluation wall/CPU time inconclusive; not adopted |
| [boehmgc-cpu-thinlto-v1](boehmgc-cpu-thinlto-v1/) | CPU-targeted ThinLTO with matched Clang/LLD | COMPLETED | Evaluation wall/CPU time inconclusive; not adopted |
| [boehmgc-toolchain-bridge-v1](boehmgc-toolchain-bridge-v1/) | GCC/binutils to Clang/LLD bridge, both generic | COMPLETED | Evaluation wall/CPU time inconclusive; not adopted |
| [boehmgc-pgo-v1](boehmgc-pgo-v1/) | Generic PGO | COMPLETED | Wall time +3.13%, CPU time +3.15% improvement; not adopted |
| [boehmgc-cpu-pgo-v1](boehmgc-cpu-pgo-v1/) | CPU-targeted PGO | COMPLETED | Wall time +3.88%, CPU time +3.89% improvement; not adopted |

No listed result implies adoption into the productive desktop unless stated
explicitly. The qualification baseline, frozen benchmark control and productive
desktop are distinct identities; exact benchmark identities belong to
[stock policy](../../docs/stock-policy.md).

Both PGO comparisons exceeded the predefined 1% practical threshold. The
[evidence-based BOLT decision](../../docs/optimization.md#bolt-decision) permits
only a future isolated experiment; this result publication adds no BOLT implementation.
