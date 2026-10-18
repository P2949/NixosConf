# Boehm GC ThinLTO v1

Measured generic Boehm GC 8.2.12 with matched Clang/LLD 21.1.8 and only
`-flto=thin` added. Both variants retain the same linker settings, collector
configuration, source, unchanged Nix 2.34.8 consumer and pinned real-repository
offline evaluation. Neither variant uses CPU-target flags. Sanitized identities,
flags and statistics are in [result.json](result.json).

Four independent pilot pairs selected ten fresh measurement pairs. Warmups and
pilots were excluded. CPU 2, fresh private HOME/XDG state and balanced randomized
order were used throughout. Positive effects mean improvement. The predefined
practical threshold was 1%; intervals are paired bootstrap 95% intervals with
10,000 resamples and the declared deterministic seed.

| Metric | Stock mean | Candidate mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 134.304 s | 134.401 s | -0.073% | -0.364% to +0.268% | INCONCLUSIVE |
| CPU time | 133.239 s | 133.323 s | -0.065% | -0.354% to +0.270% | INCONCLUSIVE |

No practical runtime improvement was demonstrated: **NOT ADOPTED**. No additional
samples were appended after seeing the result. This establishes no effect for
CPU-targeted ThinLTO, PGO or other packages; dependency/system gates remain closed.

[build-cost.json](build-cost.json) separately records earlier reproducibility
rebuild observations: 19.939 s for stock and 20.612 s for ThinLTO, including the Nix
driver, evaluation, upstream tests and output verification. Dependencies were
prebuilt, with one build job, two make cores and single-threaded LLD/ThinLTO links.
Those observations used ordinary desktop background activity and are **not
controlled runtime measurements or a reliable build-speed comparison**. Their
source revision differs from the benchmark source; exact derivation/output and
flag equality was checked before linking the observations here. Library output
NAR sizes are 299,128 bytes for stock and 297,920 bytes for ThinLTO; these are
package-output sizes, not total closure or executable text sizes.

Exact measured source `46ea637b071ae23c789a030840f228442f433166`, actual libraries,
artifact hashes, runtime intervals and reconstructed statistics passed independent
verification on the physically booted frozen control. Private indexed evidence is
sealed outside Git, identified by public hashes, excluding mutable execution
caches. All five maintenance timers were restored. Productive policy is unchanged.
