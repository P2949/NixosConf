# Boehm GC CPU targeting for Nix evaluation

The candidate changes only `-march=skylake -mtune=skylake` on Nix's Boehm GC
8.2.12 dependency. The stock package retains Nix's large configuration and
1,048,576-entry initial mark stack. It does not change the workstation, Nix
version, collector policy, or the existing zstd experiment.

Candidate selection comes from the real repository evaluation workload:

```sh
nix flake check --no-build --no-write-lock-file --no-eval-cache
```

A complete discovery profile of clean source
`658c02f637f488bf02cd6907b51718b52e133f54` captured 9,085 CPU-cycle samples with no
reported losses. GC accounted for 44.90% of sampled cycles and `libnixexpr` for
36.17%; GC marking functions were the largest individual entries. The profiled
command took 114.31 seconds and peaked at 17,864,860 KiB RSS. These observations
include profiling overhead and ordinary productive desktop activity. They
establish relevance, not candidate performance or a frozen-control result.

Build the isolated libraries with:

```sh
nix build .#boehmgc-stock .#boehmgc-cpu-target --no-link --print-out-paths
nix build .#nix-evaluation-corpus --no-link --print-out-paths
nix build .#nix-evaluation-stock .#nix-evaluation-candidate --no-link --print-out-paths
```

The corpus pins that repository revision by NAR hash and retains all ten source
trees (the repository plus every locked input) as store references. Its JSON
records the lock-file hash and each input's revision, NAR hash and store path.
Evaluation of the pinned store source passed offline with a fresh private cache.

Both command packages expose `bin/nix-evaluation` and execute the same pinned
Nix 2.34.8 binary, which resolves to the executable observed during profiling.
They set `LD_LIBRARY_PATH` to only their respective GC library directory and
clear `LD_PRELOAD` and `LD_AUDIT`. Loader diagnostics confirmed both selections;
live candidate evaluation mappings confirmed the exact Nix executable and only
the candidate GC. No existing Nix store binary is modified.

`nix-evaluation-spec` declares wall time and CPU time, four independent pilot
pairs, ten to twenty fresh measurement pairs, a one-percent practical threshold
and balanced randomized ordering. The workload runs on declared CPU 2. The
`@source@` argument is replaced only by the verified corpus source path.

`nix-evaluation-build-provenance` records source/control/compiler identities,
the identical Nix consumer, both GC derivations/sources and build flags, and the
corpus identity. Provisional artifacts from a dirty source tree are ineligible
for measurement. The existing zstd artifact serialization is unchanged.

`optimization-nix-evaluation-runner` exposes
`nixos-optimization-nix-evaluation run SPEC BUILD OUTPUT REPOSITORY` and
`nixos-optimization-nix-evaluation verify OUTPUT`. Build the specification,
provenance and runner from the same clean source revision. The output directory
must be new, outside Git, and named
`boehmgc-nix-evaluation-cpu-target-<UTC-time>-<source-short-revision>`.

The runner requires the exact evaluated, current and booted physical benchmark
control with inactive maintenance. It does not activate a system, stop services,
or adjust CPU policy. Every observation uses fresh private HOME/XDG state,
offline evaluation and verified live Nix/GC process mappings. Raw stdout/stderr,
timing receipts, runtime snapshots, ordering, independent pilot decisions and
fresh measurement results remain in the private evidence directory. Failed runs
retain a failed artifact index. Mutable execution caches are excluded from the
evidence hash index.

The verifier checks artifact/input hashes, reconstructs elapsed and CPU time,
requires the declared process bindings and ordering, checks every runtime
interval against the campaign's initial state, and reconstructs pilot sizing
and measurement-only statistics. Use the recorded runner version and retain the
realized input store paths for verification.

The experiment still requires an independent pilot and randomized paired
measurements on the unchanged physical benchmark control. A successful
functional evaluation is not an improvement verdict or authorization to adopt
the candidate.
