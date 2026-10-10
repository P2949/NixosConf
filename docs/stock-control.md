# Stock closure boundary

The stock desktop rejects dependencies in the project-owned output namespace
`nixos-opt-cpu-*`, `nixos-opt-lto-*`, `nixos-opt-pgo-*`, `nixos-opt-bolt-*` via
`system.forbiddenDependenciesRegexes`. Future experiment modules must name
outputs consistently and deliberately define their stage-specific allowed sets.
This does not implement any compiler optimization.

`nix build .#stock-contamination-negative --no-link` deliberately builds a
minimal system containing a `nixos-opt-pgo-fixture` dependency. It must fail with
the forbidden-dependency diagnostic. This is an explicit negative build, not an
ordinary flake check. A failure for some unrelated reason does not prove the
contract. The normal desktop build supplies the positive control.

Upstream exempts `system.extraDependencies` from this closure check. Do not use
that option to retain optimization artifacts in stock/control systems. Naming
contracts cannot detect unnamed modifications to otherwise ordinary packages.
Retain source revision, lock/input identity, environment, runtime and full
system/toolchain closure identities in each experiment's provenance manifest.
Record stage/profile parameters, workload identity and benchmark results, then
compare against the immutable stock baseline. Historical qualification audits
remain available through the [history index](history/README.md).
