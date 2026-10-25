# Boehm GC CPU-targeted PGO v1

Measured Boehm GC 8.2.12 with matched Clang/LLD 21.1.8, collector policy and
unchanged Nix 2.34.8 consumer. Attribution: PGO with Skylake CPU code generation.
The profile was trained on a distinct pinned repository; training and functional
acceptance remain separate from these physical measurement results. Exact
profile, compiler, merge-tool, source, library and corpus identities are in
[result.json](result.json).

4 independent pilot pairs selected 10 fresh measurement pairs.
Warmups and pilot observations were excluded. Balanced randomized order, CPU
pinning and fresh private HOME/XDG state were retained. Positive effects mean
improvement; the predefined practical threshold was 1%. All descriptive
statistics, sampling decisions and paired bootstrap intervals are preserved in
the result. No samples were appended after observing the outcome.

| Metric | Stock mean | Candidate mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 133.213 s | 128.042 s | +3.882% | +3.716% to +4.050% | IMPROVEMENT |
| CPU time | 131.979 s | 126.842 s | +3.892% | +3.733% to +4.054% | IMPROVEMENT |

This result records the measurement only: **NOT ADOPTED** into the productive
workstation. It establishes no effects for other packages or optimization
combinations.

The exact measured source is `46ea637b071ae23c789a030840f228442f433166`, retained by annotated tag
`archive/boehmgc-compiler-frozen-control-v1`. Both current and booted system
identities matched the frozen control; required maintenance units remained
inactive during measurement and were restored afterward. Independent verification
reconstructed every observation and statistic from sealed private evidence.
Productive-system recovery passed before publication. Raw runtime and process
logs remain private. The private bundle hash identifies a deterministic tar of
exactly the indexed immutable artifacts plus their index, excluding execution
caches.
