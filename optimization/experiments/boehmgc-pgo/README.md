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
