# Boehm GC CPU-targeted ThinLTO v1

Measured Boehm GC 8.2.12 with matched Clang/LLD 21.1.8. Both variants use
`-march=skylake -mtune=skylake`; only the candidate adds `-flto=thin`.
Collector configuration, source, linker settings, unchanged Nix 2.34.8 consumer
and pinned offline real-repository evaluation remain matched. Sanitized identities,
flags and statistics are in [result.json](result.json).

Four independent pilot pairs selected ten fresh measurement pairs. Warmups and
pilots were excluded. Both variants used CPU 2, fresh private HOME/XDG state and
balanced randomized ordering. Positive effects mean improvement. The predefined
practical threshold was 1%; intervals are paired bootstrap 95% intervals with
10,000 resamples and the declared deterministic seed.

| Metric | Stock mean | Candidate mean | Mean paired effect | 95% interval | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Wall time | 135.408 s | 135.347 s | +0.044% | -0.122% to +0.225% | INCONCLUSIVE |
| CPU time | 134.332 s | 134.287 s | +0.032% | -0.123% to +0.203% | INCONCLUSIVE |

No practical improvement was demonstrated: **NOT ADOPTED**. No extra samples were
appended after seeing this result. Together with the separate generic ThinLTO
campaign, this measures the two declared within-toolchain LTO comparisons; it does
not support an unpaired cross-campaign interaction estimate or a PGO conclusion.
Dependency/system targeting gates remain closed.

[build-cost.json](build-cost.json) records earlier reproducibility rebuild
observations separately: 20.857 s for the CPU-targeted control and 20.027 s for
CPU-targeted ThinLTO. These include the Nix driver, evaluation, tests and output
verification, with prebuilt dependencies, one build job, two make cores and
single-threaded LLD/ThinLTO links. Ordinary desktop background activity was
uncontrolled; they are **not controlled runtime measurements or a reliable
build-speed comparison**. Their older source is explicit, and exact derivation,
output and flag equality was checked against the measured libraries. Output NAR
sizes are 309,744 and 307,872 bytes, respectively; these are package-output sizes,
not total closure or executable text sizes.

Exact measured source `46ea637b071ae23c789a030840f228442f433166`, actual loaded
libraries, artifact hashes, runtime intervals and reconstructed statistics passed
independent verification on the physically booted frozen control. Private indexed
evidence is sealed outside Git, identified by public hashes, excluding mutable
execution caches. All five maintenance timers were restored. Productive policy
remains unchanged.
