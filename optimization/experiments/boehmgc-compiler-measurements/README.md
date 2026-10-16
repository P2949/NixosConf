# GC compiler comparisons

These package-only comparisons share the unchanged Nix consumer, collector
source/configuration and independent real-repository corpus. Each pair isolates
one declared change. `toolchain-bridge` changes compiler and linker together;
its results cannot be attributed to ThinLTO.

| Comparison | Control | Candidate |
| --- | --- | --- |
| `clang-cpu` | Clang generic | Clang Skylake |
| `thinlto` | Clang generic | Clang generic ThinLTO |
| `cpu-thinlto` | Clang Skylake | Clang Skylake ThinLTO |
| `toolchain-bridge` | GCC/binutils generic | Clang/LLD generic |
| `pgo` | Clang generic | Clang generic PGO |
| `cpu-pgo` | Clang Skylake | Clang Skylake PGO |

The ordinary flake exposes stock/candidate commands and specification/build
artifacts for the first four pairs. For example:

```console
nix build .#boehmgc-thinlto-measurement-stock .#boehmgc-thinlto-measurement-candidate .#boehmgc-thinlto-measurement-spec .#boehmgc-thinlto-measurement-build --no-link --print-out-paths
```

Use the existing `optimization-nix-evaluation-runner` with the resulting spec and
build manifest. Its normal physical-machine, frozen-control, CPU policy,
maintenance, temperature, source, workload and paired-sampling checks remain
mandatory. A productive configuration that differs from the frozen control is
rejected. Build success or VM functionality does not authorize a benchmark or
relax these checks; physical measurements require the scheduled measurement
window. Keep the original CPU experiment source and immutable manifests intact.

`measurement.nix` accepts explicit selected profile identities for PGO and the
stock/candidate attribute names in the calling build expression. The normal
flake has no local profile dependency. Follow the [PGO artifact workflow](../boehmgc-pgo/README.md)
to retain selected content-addressed profiles before constructing those pairs.
The runner verifies profile bytes and rejects reuse of the training repository
revision as the independent benchmark.

For a parameterized PGO build, set `expressionTargets = true` and use
`targetAttributes = { stock = "commands.stock"; candidate = "commands.candidate"; }`
when importing `measurement.nix`. These identify the actual attributes returned
by that Nix expression. The build manifest records the committed entrypoint and
its SHA-256, rather than claiming local-profile commands are normal flake
outputs. Admission checks the source file in the clean checkout and retains it
as `source-expression.nix` in the evidence directory. Verification checks the
retained hash and target attributes along with the normal artifact index.

`build.nix` also emits preparation metadata. Its
`PREPARATION_ONLY_NOT_PERFORMANCE` classification remains mandatory, including
when embedded in a measurement build manifest. It records facts rather than a
performance verdict. The runner binds those facts to the spec, source,
toolchains, libraries, consumer and command derivations; actual build audits
must show native objects or ThinLTO bitcode, summaries and ThinLink indexes as
appropriate. Unrelated flags, missing audits, changed collector policy and
substituted commands are rejected.

The independent workload and predefined one-percent practical threshold use
the existing bounded paired sampling and uncertainty reporting. Performance
acceptance requires completed raw measurements and verification, separately
for each declared pair. Dependency targeting, system variants, BOLT and further
combinations retain their prerequisite gates.
