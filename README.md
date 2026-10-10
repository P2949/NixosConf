# NixosConf

Declarative NixOS configuration for one desktop workstation. The productive
system is the stock control for later, separately identified optimization
experiments.

## Where to start

- [Current system](docs/status.md).
- [Immutable stock baseline](docs/baselines/pre-optimization/baseline-final.md).
- Persistence: [contract](docs/persistence-contract.md), [architecture](docs/impermanence.md), [state audit](docs/ephemeral-state-audit.md).
- Recovery: [backup and restore](docs/backup-restore.md), [secrets bootstrap](docs/bootstrap-secrets.md).
- Experiments: [stock control](docs/stock-control.md), [stock policy](docs/stock-policy.md).
- [Historical implementation records](docs/history/README.md).
- [Desktop policy](hosts/desktop/default.nix) and [flake outputs](flake.nix).

## Organization

| Directory | Responsibility |
| --- | --- |
| `hosts/` | Physical host facts and policy |
| `profiles/` | Machine roles and composition |
| `modules/` | Reusable NixOS features |
| `home/` | User and session policy |
| `packages/` | Custom derivations |
| `images/` | Standalone recovery images |
| `tests/` | Configuration and integration validation |
| `docs/` | Design, procedures and evidence |
| `optimization/` | Experiments after the accepted stock baseline |

Hosts select features, profiles compose roles, and Home Manager owns user
policy. The flake remains explicit for this workstation.

## Build and check

```bash
nix build .#nixosConfigurations.desktop.config.system.build.toplevel
nix fmt -- --ci
nix flake check --print-build-logs
nix develop .#default
```

Building does not activate the configuration. Review
[activation safety](docs/activation-safety.md) and
[closure review](docs/closure-review.md) before deployment.
The combined granular persistence VM is a permanent flake check. Other heavy
VM outputs and physical acceptance are separate from ordinary checks;
see [reconstruction](docs/reconstruction.md) and
[development validation](docs/development-validation.md).

## Persistence and recovery

Normal boots reset the disposable Btrfs root. The `persistent-root`
specialisation disables reset; home and persistent system state have their
own explicit allow-list. Source home/var are root-local; persistence classification
rationale and application/cache exceptions are recorded in the
[state audit](docs/ephemeral-state-audit.md). See [root design](docs/impermanence.md),
[persistence contract](docs/persistence-contract.md),
[physical validation](docs/physical-root-validation.md) and
[backup/restore](docs/backup-restore.md).

## Baseline and experiments

The [baseline collector](docs/baseline-capture.md) records evidence without
activating the system or starting stress tests. The
[stock control](docs/stock-control.md) and [stock policy](docs/stock-policy.md)
keep experiments out of the productive control.

Optimization starts from the accepted immutable stock tag, on a separate
branch. Each experiment must retain source, toolchain, profile, derivation
and workload identity. BOLT outputs are new immutable derivations; existing
Nix-store outputs are never modified. Readiness and experiment status belong
in [current status](docs/status.md), rather than this overview.
