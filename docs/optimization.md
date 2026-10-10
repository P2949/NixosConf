# Optimization experiments

The immutable qualification baseline and frozen benchmark control are distinct
from the current productive desktop. Exact benchmark identities and policy belong
to [stock policy](stock-policy.md); qualification evidence belongs to the
[canonical baseline](baselines/pre-optimization/baseline-final.md).
The v2 framework is established on the frozen benchmark control.

Ordinary desktop application additions may change the productive closure without
retagging the immutable benchmark control. `nix flake check` retains the pinned
control-input and optimization-dependency checks. Before an experiment, run
`nix build .#optimization-control-identity --no-link` explicitly: it rejects
evaluated normal/recovery closures that differ from the frozen control. The
runner independently rejects evaluated/current/booted control mismatches.
Prism candidates are ordinary workstation changes and are not benchmark controls.

The first completed reference experiment is
[zstd-skylake-v1](../optimization/results/zstd-skylake-v1/). It tested
package-scoped `-march=skylake -mtune=skylake` on zstd using the fixed Silesia
corpus. Compression was inconclusive at the declared practical threshold and
decompression regressed, so the candidate was not adopted.

Each experiment must preserve byte-identical Nix-generated specification and
build-provenance artifacts, a separate execution receipt, and independently versioned
runtime and results artifacts linked by hashes. Build evidence includes clean
source commit/tree, lock/input identities, compiler/linker and package
outputs/derivations, stage parameters and corpus identity. Runtime evidence
requires the designated physical target, exact current/booted/control equality,
kernel/microcode/SMT, CPU/EPP/power and memory policy, maintenance state,
temperature and thermal throttle counters. The human-readable workstation
collector remains a separate diagnostic tool.

The runner must preserve raw output, execution order and timestamps, use
balanced randomized paired order and CPU pinning, capture runtime before/after,
and reject overlapping maintenance or changed policy/identity. The runner observes and refuses active services or timers; it does not manage
workstation state by default. Prepare maintenance explicitly outside the runner,
without interrupting active jobs, and restore timers afterward. Pilot
observations determine bounded sample counts and remain outside final estimates.
Report variance, standard deviation, paired effects, confidence intervals and an
explicit effect threshold; a higher candidate mean alone proves no improvement.
Missing evidence or uncertain effects remain inconclusive. Builds may run on
valid distributed builders; measurements run only on the physical target.

## Progression

Develop schema/provenance first, then package CPU targeting, selected dependency
sets and a controlled system specialization. Follow with ThinLTO, PGO
infrastructure, package PGO and wider PGO; then BOLT and combinations. Treat
kernel/Mesa as separate experiments. Do not begin with all stages combined.

PGO profiles are first-class artifacts recording the instrumented derivation,
training workload/input hashes, compiler, profile hashes, optimized derivation
and distinct benchmark evidence. BOLT produces a new immutable derivation;
never modify a binary in the Nix store. Record input derivation/binary hash,
profile identity, BOLT derivation/version/arguments, and output hash/derivation.

Readiness is closed. No additional soak, application qualification, recovery
campaign or whole-home backup is required. Preserve the tested secret recovery
and tiny local-only exception archive. Optional storage forensics, manual GC,
extra abstractions and cosmetic refactors do not block experiments.

## Reference experiment procedure

The `zstd-skylake-v1` experiment successfully exercised the framework end to
end. Its accepted public result is recorded in
[`optimization/results/zstd-skylake-v1`](../optimization/results/zstd-skylake-v1/).

For future isolated package experiments, preserve the same workflow:

1. Create the experiment from a clean source revision compatible with the frozen
   benchmark control, and boot that control for measurements. Ordinary `main`
   revisions may have a different desktop closure.
2. Build the control, candidate, corpus, specification, build provenance and
   runner before entering the measurement window.
   Build `.#optimization-control-identity` as the explicit admission gate.
3. Require exact source and lock identity, current/booted stock equality,
   physical-host identity, expected CPU topology and 125 W PL1/PL2, inactive
   maintenance, and unchanged thermal-throttle counters.
4. Keep full private evidence under `/var/lib/nixos-optimization/runs/` with
   exact specification and build-provenance artifacts, execution metadata,
   runtime snapshots, raw observations, results and an artifact hash index.
5. Use independent pilot observations only to choose the bounded fresh
   measurement count. Do not include pilot data in the final estimator.
6. Use balanced randomized paired order on the declared CPU and retain exact
   binary, corpus and command identities for every observation.
7. Reject invalid runs rather than correcting them after the fact. Preserve
   failed partial evidence with failed status.
8. Validate artifact hashes, runtime intervals and reconstructed statistics
   before accepting a result.
9. Publish only a sanitized result containing the identities, hashes,
   derivations, pair counts, statistics and
   `IMPROVEMENT`/`REGRESSION`/`INCONCLUSIVE` interpretation.
10. Commit the public result only after measurement so that it points back to
    the clean measured source revision.

The first completed experiment used three-second minimum evaluations, six
independent pilot pairs and ten fresh measurement pairs. Its zstd CPU-target
candidate produced inconclusive compression performance at the declared
practical threshold and a material decompression regression, so it was not
adopted.

Future research may expand CPU targeting through additional packages and
dependency sets before any system-level variant, followed separately by
ThinLTO, PGO and BOLT when work resumes. VM variants are appropriate for
functional system validation; authoritative performance measurements remain
on the designated physical workstation.

No further optimization investigation, general cleanup campaign, stock retag,
activation, reboot or readiness retest is currently required.
