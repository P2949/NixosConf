# Boehm GC PGO preparation

This experiment uses the GC library identified in the real Nix evaluation
workload. It preserves the matched Clang/LLD generic and Skylake controls from
the ThinLTO experiment, with ThinLTO disabled. Instrumentation adds
`-fprofile-instr-generate -fprofile-update=atomic`; collector source and policy
remain unchanged.

The instrumented libraries are explicit developer outputs:

```console
nix build .#boehmgc-pgo-instrumented --no-link
nix build .#boehmgc-pgo-cpu-instrumented --no-link
```

Upstream tests use a separate temporary profile directory. Their profiles must
never enter workload training. The training wrappers require an explicit
`LLVM_PROFILE_FILE` destination and keep the existing Nix consumer unchanged.
Use a private directory and `%p-%m.profraw` to distinguish process and binary
identities. See the [Clang instrumentation documentation](https://clang.llvm.org/docs/UsersManual.html#profiling-with-instrumentation).

Instrumentation build success alone establishes neither representative training
nor a performance result. An accepted profile needs a source-bound training
receipt, raw profile hashes, the exact LLVM merge tool and command, and the merged
profile hash. The optimized derivation must depend on immutable profile bytes;
its receipt must identify the independent benchmark separately from training.
Generic and Skylake instrumentation require separate compatible profiles.

These outputs do not activate the desktop or authorize physical measurements.

## Profile artifacts and consumption

`boehmgc-pgo-training` runs an 8 GiB VM with two vCPUs. It evaluates the actual
desktop toplevel from repository revision
`4a122b6f2898269d9c8d85a15d655f4bcb80b195`, offline with fresh user state for
each variant. This training input is distinct from the existing benchmark
corpus at `658c02f637f488bf02cd6907b51718b52e133f54`. VM execution supplies
training counts, never authoritative performance timings.

Build both merges together to share one training run:

```console
nix build .#boehmgc-pgo-profile .#boehmgc-pgo-cpu-profile --no-link --print-out-paths --max-jobs 1 --cores 2
```

Each profile artifact retains raw files, the training receipt, the exact merge
command/tool version, merged bytes and SHA-256, and a function-count summary.
Merging rejects a changed raw file set or hash and requires a nonzero count for
`GC_mark_some`, part of the identified hot marking code. Keep the original
training output for loader logs and evaluation results.

Training counts and process IDs can vary between rebuilds. Promote the selected
merged artifact with `nix store add-path --name boehmgc-pgo-profile PATH`, then
record its content-addressed store path and `nix hash path` result. Root or
archive the selected artifact before garbage collection; rebuilding the training
recipe is not a promise to regenerate identical profile bytes.

`optimized.nix` deliberately requires explicit `variant`, `profilePath` and
`profileNarHash` parameters, alongside the pinned `pkgs`. It verifies the whole
artifact NAR hash, merged-file hash, instrumented derivation, compiler/linker,
consumer and CPU variant before consuming the profile. Different profile bytes
produce a different optimized derivation. Compiler warnings for stale or missing
instrumentation profiles are errors; optimized libraries must not retain the
profile-writing runtime. Record the resulting optimized derivation and output
alongside the independent benchmark descriptor in an execution receipt.

The default flake has no dependency on a machine-local promoted profile. BOLT
and performance conclusions remain gated on a reliable independent benchmark.
