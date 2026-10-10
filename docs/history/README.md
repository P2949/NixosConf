# Historical implementation records

Pre-optimization readiness completed 2026-10-10 through [PR #7](https://github.com/P2949/NixosConf/pull/7).
The immutable `nixos-26.05-pre-optimization-baseline` tag preserves the complete
readiness journal, granular migration plan, cutover procedure and tooling.
The concise result remains [baseline-final.md](../baselines/pre-optimization/baseline-final.md).

Granular migration completed through [PR #8](https://github.com/P2949/NixosConf/pull/8):
frozen source `96678c3a974755ca285c734999c70acfc0bfd254`, integration
`c981a6ffd9b484c53adf0a374f6915c772d12a83`.

Retrieve exact historical records without duplicating them in the live tree:

```bash
git show nixos-26.05-pre-optimization-baseline:plan.md
git show nixos-26.05-pre-optimization-baseline:NixOS_Granular_Ephemeral_State_Implementation_Plan.md
git show nixos-26.05-pre-optimization-baseline:docs/granular-cutover.md
```

Current operational guidance is in the persistence, recovery and safety documents.

Prism Launcher completed through [PR #16](https://github.com/P2949/NixosConf/pull/16):
final feature head `36e3d777d5c88c35ad94a7d3fb6a181b587bc393`, merged into main
at `70f2e2b596772d3ae620bfb5e48ee69a738584ba`.
The implementation journal remains accessible through Git:

```bash
git show 36e3d777d5c88c35ad94a7d3fb6a181b587bc393:docs/prism-launcher-plan.md
```

Permanent application classification is in the [state audit](../ephemeral-state-audit.md).
