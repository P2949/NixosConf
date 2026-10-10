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
contracts also cannot detect unnamed modifications to otherwise ordinary
packages; retain environment/source and full closure audits with each control record.
The completed baseline audits are preserved by the [history index](history/README.md).
