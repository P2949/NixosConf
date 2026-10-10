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

Each experiment must preserve independently versioned specification, build,
runtime and results artifacts linked by hashes. Build evidence includes clean
source commit/tree, lock/input identities, compiler/linker and package
outputs/derivations, stage parameters and corpus identity. Runtime evidence
requires the designated physical target, exact current/booted/control equality,
kernel/microcode/SMT, CPU/EPP/power and memory policy, maintenance state,
temperature and thermal throttle counters. The human-readable workstation
collector remains a separate diagnostic tool.

The runner must preserve raw output, execution order and timestamps, use
balanced randomized paired order and CPU pinning, capture runtime before/after,
and reject overlapping maintenance or changed policy/identity. Do not interrupt
active maintenance. Restore stopped timers after the measurement window. Pilot
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
