# Optimization experiments

Qualification remains fixed at `nixos-26.05-pre-optimization-baseline`.
The physically booted benchmark control is the separately protected annotated
`nixos-26.05-optimization-stock-v1` tag at
`53b58e38e36d7c6071807e7abedc85fce42c449c`. Its normal output begins
`6rn4ggk32wcqrhcdv2chr55daqxxh026`; persistent-root begins
`yf7jg059hm4qg2yhyls4ciddliwc8ych`. The intentional post-qualification
journal change is documented in [stock policy](stock-policy.md).

The v2 framework is under construction. Its first experiment compares stock
zstd with package-scoped `-march=skylake -mtune=skylake` on the fixed-hash
Silesia corpus. This is a framework validation experiment, not a global system
optimization. The specification owns CPU selection, commands, warmups, duration,
pilot and sampling policy. Only explicitly allowed packages receive CPU flags.

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

## Foundation acceptance and first result

Keep the foundation PR draft until exact-head CI and all local checks pass:
`nix fmt -- --ci`, `git diff --check`, and
`nix flake check --no-write-lock-file --print-build-logs`. Python checks include
compilation, Ruff format/lint and unit tests, including actual pinned-zstd output
syntax. Build stock/candidate zstd, corpus, specification, build provenance and
runner. Independently resolve normal/persistent/recovery outputs and require
exact stock identities, lock hash and nixpkgs revision. The real CPU-stage
output must contain the stock contamination contract's `-nixos-opt-cpu-` marker.
Merge the foundation only after final PR-head CI passes, then require merged
main CI. Framework-only source changes require no activation, reboot, stock
retagging or application/readiness retests.

Create `experiment/zstd-skylake-v1` from merged main for the first result. Build
all inputs before the measurement window. Keep the normal desktop running;
no CPU isolation boot, single-user mode, mitigation changes or GUI shutdown
belongs in this package experiment. Admission requires clean source matching
build provenance, exact current/booted stock, matching lock/normal/persistent
identities, physical virtualization=`none`, expected SMT/online topology and
125 W PL1/PL2, inactive maintenance timers/services and unchanged throttle
counters. Record naturally dynamic temperature, memory, frequency and EPP
observations without arbitrary admission thresholds.

Keep full private evidence under `/var/lib/nixos-optimization/runs/`, on the
existing optimization subvolume, with mode 0700/umask 077. Run IDs combine
experiment, UTC timestamp and source commit, and agree with directory names.
Retain exact `specification.json`, `build-provenance.json`, separate
`execution.json`, before/after runtime, raw output, observations, results and
an artifact hash index. Execution records source commit/tree, original manifest
hashes, exact binary/corpus paths/hashes/size, runner identity and timestamps.
Build targets explicitly connect spec IDs and flake attributes to derivations.

The initial real spec uses three-second minimum evaluations, six independent
pilot pairs and ten to thirty fresh measurement pairs. `targetDeltaHalfWidth`
means an absolute half-width in fractional paired-delta units: 0.01 targets
roughly one percentage point. If pilot demand exceeds the maximum, retain the
limit and report limited precision rather than quietly claiming the target.
Pilot data remain permanently available but excluded from final estimates.

Reject wrong identity/policy/input, maintenance overlap, throttle deltas,
critical temperature, parser errors and command failures. Preserve failed
partial bundles with failed status. Validate all hashes and the final runtime
interval, and reconstruct summaries from the observations before acceptance.
Publish only a small sanitized result with source/tree, artifact/private-bundle
hashes, derivations, corpus hash, pair counts/statistics and
IMPROVEMENT/REGRESSION/INCONCLUSIVE. Commit it after measurement, pointing back
to the clean measured source. Full proc data, machine identifiers, reset receipts
and large profiles remain private. A trustworthy inconclusive result is a
successful framework-validation experiment.

After this first result, expand CPU targeting gradually through several small
packages and selected dependency sets before system targeting. Use real desktop
VM variants (including bootloader variants) for system composition, activation,
services and contamination tests; physical measurements remain authoritative.
Use boot specialisations only when the runtime system is itself experimental.
ThinLTO records compiler/linker, mode/flags, affected derivations and closure.
PGO records training source and profile format as well as the identities above.
Large PGO/BOLT profiles belong in the store or optimization subvolume with
hash/size/producer references in Git. Distributed builders become useful when
build costs justify them; the desktop remains the sole measurement target.
No new general cleanup campaign or stock tag is needed for framework commits.
