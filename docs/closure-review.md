# Reviewing workstation closure changes

Build the exact candidate without activating it or replacing the system profile:

```bash
candidate=$(nix build \
  '.#nixosConfigurations.desktop.config.system.build.toplevel' \
  --no-link --no-write-lock-file --print-out-paths)
nix store diff-closures /run/current-system "$candidate"
```

Review package version changes and unexpected kernel, Mesa, LLVM or unstable
dependencies before accepting a candidate. Generated units, initrds, manuals
and specialisation closures can change size without a package version change.
Retain the output and both closure identities with the change record. A closure
comparison proves dependency changes; activation and runtime acceptance require
their own evidence.

Historical comparisons are retained in [baseline evidence](baselines/pre-optimization/evidence/closure-comparisons.md).
