# Boehm GC toolchain bridge v1

Measured generic Boehm GC 8.2.12 built with GCC/binutils versus Clang/LLD.
This comparison changes **both compiler and linker**. It does not isolate a
compiler-only effect, and it is not evidence for ThinLTO. Neither variant uses
CPU-target or PGO flags. Collector configuration, package source, unchanged Nix
2.34.8 consumer and pinned real-repository offline evaluation are retained.
Actual toolchains, flags, hashes and statistics are in [result.json](result.json).

Four independent pilot pairs selected ten fresh measurement pairs. Warmups and
pilots were excluded. Both variants used CPU 2, fresh private HOME/XDG state and
balanced randomized order. Positive effects mean improvement. The predefined
practical threshold was 1%; intervals are paired bootstrap 95% intervals with
10,000 resamples and the declared deterministic seed.

| Metric | GCC/binutils mean | Clang/LLD mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 133.751 s | 134.391 s | -0.480% | -0.687% to -0.278% | INCONCLUSIVE |
| CPU time | 132.675 s | 133.324 s | -0.490% | -0.698% to -0.286% | INCONCLUSIVE |

Clang/LLD was slightly slower, below the declared practical regression threshold.
No practical improvement was demonstrated: **NOT ADOPTED**. No extra samples were
appended after seeing the result. This is a direct paired bridge comparison;
absolute means from separate earlier campaigns must not be substituted for it.
Dependency/system targeting gates remain closed.

Exact measured source `46ea637b071ae23c789a030840f228442f433166`, actual loaded
libraries, artifact hashes, runtime intervals and reconstructed statistics passed
independent verification on the physically booted frozen control. Private indexed
evidence is sealed outside Git, identified by public hashes, excluding mutable
execution caches. All five maintenance timers were restored. Productive policy
remains unchanged.
