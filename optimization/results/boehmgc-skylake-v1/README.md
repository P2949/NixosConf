# Boehm GC Skylake v1

Measured GCC-built Boehm GC 8.2.12 with only `-march=skylake -mtune=skylake`
changed, using the unchanged Nix 2.34.8 consumer and pinned real-repository
evaluation workload. The physically booted frozen control, source revision
`468c24c1ef944122a5b394ce3e33c9841eb62501`, immutable artifacts, actual loaded
libraries and runtime intervals passed independent evidence verification.
Complete sanitized identities, hashes and statistics are in [result.json](result.json).

Four independent pilot pairs selected ten fresh measurement pairs. Warmups and
pilots were excluded from estimates. Both variants ran on CPU 2 with fresh private
HOME/XDG state, offline inputs and balanced randomized pair order. Positive effects
mean improvement; negative effects mean increased time. The predefined practical
threshold was 1%; intervals are paired bootstrap 95% intervals with 10,000 resamples.

| Metric | Stock mean | Candidate mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 133.361 s | 134.115 s | -0.566% | -0.729% to -0.396% | INCONCLUSIVE |
| CPU time | 132.279 s | 133.035 s | -0.572% | -0.743% to -0.393% | INCONCLUSIVE |

The candidate was slightly slower, but the effect did not reach the declared
practical regression threshold. It demonstrated no practical improvement and is
**NOT ADOPTED**. This result applies to this package, compiler, workload and run;
it does not establish effects for Clang, ThinLTO, PGO or other packages. Dependency
and system targeting gates remain closed.

Full private evidence is retained on the optimization subvolume. The public bundle
and artifact-index hashes identify its sealed archive, which excludes mutable
execution caches. Maintenance timers were restored after the campaign. Productive
configuration and frozen benchmark-control identities remain unchanged.
