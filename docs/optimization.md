# Optimization experiments

The immutable qualification baseline and frozen benchmark control are distinct
from the current productive desktop. Exact benchmark identities and policy belong
to [stock policy](stock-policy.md); qualification evidence belongs to the
[canonical baseline](baselines/pre-optimization/baseline-final.md).
The v2 framework is established on the frozen benchmark control.

Ordinary desktop application additions may change the productive closure without
retagging the immutable benchmark control. Ordinary `nix flake check` validates
the optimization framework, stage/schema invariants and optimization-dependency
exclusions; it does not require productive inputs or the recovery ISO to equal
an older frozen control. Before an experiment, run
`nix build .#optimization-control-identity --no-link` explicitly: it rejects
evaluated normal/recovery closures that differ from the frozen control. The
runner independently rejects evaluated/current/booted control mismatches.
An advanced productive source is expected to fail this explicit admission gate.
The immutable control tag retains its source and lock identities independently
of productive maintenance.
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

## Completed scope and future research

All eight scoped experiments are **COMPLETED** in the
[results index](../optimization/results/README.md): zstd CPU codegen, Boehm GC
GCC and Clang/LLD CPU codegen, generic and CPU-targeted ThinLTO, the
bridge from GCC/binutils to Clang/LLD, generic PGO and CPU-targeted PGO.
Inconclusive performance is a completed measurement outcome. None of these
candidates is adopted into the productive desktop.

PGO profiles are first-class artifacts recording the instrumented derivation,
training workload/input hashes, compiler, profile hashes, optimized derivation
and distinct benchmark evidence. Independent training, functional VM acceptance
and physical performance measurements retain separate identities.

Readiness is closed. No additional soak, application qualification, recovery
campaign or whole-home backup is required. Preserve the tested secret recovery
and tiny local-only exception archive. Optional storage forensics, manual GC,
extra abstractions and cosmetic refactors do not block experiments.

## BOLT decision

**BOLT = GO for a future isolated experiment.** Both the
[generic PGO](../optimization/results/boehmgc-pgo-v1/) and
[CPU-targeted PGO](../optimization/results/boehmgc-cpu-pgo-v1/) comparisons
established improvements at the predefined 1% practical threshold; their 95%
paired bootstrap intervals lie entirely above 1% for wall and CPU time.
This is a decision only. A future BOLT implementation needs its own bounded
experiment and admission evidence; no BOLT candidate is implemented or adopted
by these result publications.

Carry forward the proven identity requirements without Gentoo's Portage
machinery: exact input derivation and binary, full binary hash, build ID and
`.text` identity where applicable, exact `llvm-bolt` derivation/version/options,
exact profile evidence, and an immutable output derivation. Never mutate the
Nix store in place. Fail closed on identity mismatch. The retired global
PGO/BOLT approach remains retired.

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

Further package, dependency, system, kernel or Mesa research requires new
evidence and a separately scoped proposal. Completed measurements do not
establish benefits for other workloads or optimization combinations. VM variants
remain appropriate for functional validation; authoritative performance
measurements run on the designated physical workstation.

## Nix evaluation GC candidate

The [GC evaluation experiment](../optimization/experiments/boehmgc-nix-evaluation/README.md)
targets the Boehm GC hot path identified in a complete profile of actual
repository evaluation. Its isolated stock/candidate commands use the same Nix
executable and differ only in GC CPU-target flags. The pinned offline corpus,
build manifests, physical admission, raw evidence and reconstruction verifier
are implemented. The GCC CPU-codegen comparison is **COMPLETED**, with
inconclusive wall/CPU effects and no productive adoption; see the
[accepted result](../optimization/results/boehmgc-skylake-v1/).

Keep frozen benchmark source, retained by its annotated archive tag, separate
from productive `main`; never rebase frozen experiment history.
The Nix-checks workflow supports manual invocation for that pushed source ref;
verify its exact head and successful conclusion before using the source for
measurement. Build `.#optimization-control-identity` explicitly as the frozen
source admission gate. Code integration does not retag the control or adopt the
candidate. General cleanup and readiness qualification remain closed.

## GC compiler and profile experiments

The [ThinLTO matrix](../optimization/experiments/boehmgc-thinlto/README.md)
provides matched Clang/LLD controls with generic and Skylake code generation,
with and without ThinLTO. The Clang CPU-codegen, both ThinLTO and toolchain
bridge comparisons are **COMPLETED**, with inconclusive wall/CPU effects and no
productive adoption; see the [results index](../optimization/results/README.md).
The separate GCC-to-Clang bridge changes both compiler and linker; it cannot
isolate an LTO effect.

The [PGO workflow](../optimization/experiments/boehmgc-pgo/README.md) builds
instrumented libraries, trains them against a distinct pinned real repository,
retains raw and merged profiles, and consumes selected content-addressed profile
artifacts in optimized derivations. Training and functional VM results remain
separate from the completed physical
[generic PGO](../optimization/results/boehmgc-pgo-v1/) and
[CPU-targeted PGO](../optimization/results/boehmgc-cpu-pgo-v1/) measurements.
Both passed the declared practical threshold and remain unadopted.

[Compiler comparison admission](../optimization/experiments/boehmgc-compiler-measurements/README.md)
binds each pair to its source, toolchains, build audits, collector policy and
actual consumer/command/library identities. Parameterized PGO targets record the
committed Nix expression and source hash. These paths retain the physical and
frozen-control gates and bounded paired sampling. All declared compiler and PGO
comparisons now have independently verified physical results. Raw evidence stays
private; public results retain identities, hashes and reconstructed statistics.
The [BOLT decision](#bolt-decision) is limited to a future isolated experiment;
dependency/system targeting and further combinations require their own evidence.
