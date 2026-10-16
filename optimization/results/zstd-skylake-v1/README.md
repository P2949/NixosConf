# Zstd Skylake v1

Measured the isolated CPU-target package on the physically booted stock control.
The complete sanitized statistics and evidence hashes are in [result.json](result.json).

Six independent pilot pairs selected the declared minimum of ten fresh measurement
pairs. Both variants used the same pinned CPU, fixed Silesia corpus and three-second
minimum evaluations, with balanced randomized pair order. Pilot data were excluded
from the estimate. The practical threshold was 1%; intervals are paired bootstrap
95% intervals with the declared deterministic seed.

| Metric | Mean paired effect | 95% interval | Interpretation |
| --- | ---: | ---: | --- |
| Compression | +0.691% | +0.169% to +1.164% | INCONCLUSIVE |
| Decompression | -2.671% | -2.972% to -2.334% | REGRESSION |

This experiment validates the framework; it does not justify adopting the CPU-target
candidate. The productive configuration remains unchanged. These conclusions apply
to this package, workload and run, without establishing effects for other packages
or system-wide targeting. Full private evidence remains on the optimization
subvolume; the public bundle hash identifies its sealed archive. Independent audit
confirmed artifact identities, raw observations, ordering, summary reconstruction
and runtime intervals. Maintenance timers were restored after measurement.
