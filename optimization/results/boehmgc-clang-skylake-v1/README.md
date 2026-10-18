# Boehm GC Clang Skylake v1

Measured Boehm GC 8.2.12 with matched Clang/LLD 21.1.8 controls and only
`-march=skylake -mtune=skylake` changed. The unchanged Nix 2.34.8 consumer,
pinned real-repository corpus, collector policy and offline command match the
prepared comparison. This is a separate within-Clang experiment, not a direct
comparison with the earlier GCC campaign. Complete sanitized identities and
statistics are in [result.json](result.json).

Four independent pilot pairs selected ten fresh measurement pairs. Warmups and
pilots were excluded. Both variants used CPU 2, fresh private HOME/XDG state and
balanced randomized order. Positive effects mean improvement. The predefined
practical threshold was 1%; intervals are paired bootstrap 95% intervals with
10,000 resamples and the declared deterministic seed.

| Metric | Stock mean | Candidate mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 133.908 s | 135.178 s | -0.948% | -1.132% to -0.772% | INCONCLUSIVE |
| CPU time | 132.849 s | 134.097 s | -0.939% | -1.125% to -0.764% | INCONCLUSIVE |

The candidate was slower, but the intervals cross the practical regression
threshold. No practical improvement was demonstrated: **NOT ADOPTED**. No extra
samples were appended after examining this result. Dependency/system targeting
gates remain closed; these measurements establish no ThinLTO or PGO effect.

Exact measured source `46ea637b071ae23c789a030840f228442f433166`, loaded libraries,
artifact hashes, runtime intervals and reconstructed statistics passed independent
verification on the physically booted frozen control. Private indexed evidence is
retained in a sealed archive outside Git, identified by public hashes. Mutable
execution caches are excluded. All five maintenance timers were restored.
