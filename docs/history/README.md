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

Minecraft local backup/recovery and accepted performance stack completed through
[PR #23](https://github.com/P2949/NixosConf/pull/23) and
[PR #24](https://github.com/P2949/NixosConf/pull/24). The immutable
`minecraft-server-qualified-2026-10-12` tag preserves the qualified source;
[PR #26](https://github.com/P2949/NixosConf/pull/26) records maintenance-mode
hardening. Current procedures remain in the [Minecraft runbook](../minecraft-server.md).

Android Studio integration completed through
[PR #28](https://github.com/P2949/NixosConf/pull/28). Exact reboot, SDK/AVD,
build/emulator and debugger acceptance belongs to its PR metadata. Current
operations are in the [development guide](../development-validation.md#android-studio)
and [state audit](../ephemeral-state-audit.md).

## Frozen optimization sources

Annotated archive tags retain the exact scientific source independently of
productive `main` and mutable experiment branches:

| Annotated tag | Frozen revision | Purpose |
| --- | --- | --- |
| `archive/boehmgc-cpu-target-v1` | `468c24c1ef944122a5b394ce3e33c9841eb62501` | Original GCC CPU-target experiment source |
| `archive/boehmgc-compiler-frozen-control-v1` | `46ea637b071ae23c789a030840f228442f433166` | Matched compiler, ThinLTO, bridge and physical PGO source |

The compiler source superseded the CPU-target source and remained unchanged
through both PGO campaigns. Frozen history was not rebased onto productive
application changes. Mutable experiment branches are removed after result
publication; annotated tags and [result provenance](../../optimization/results/README.md)
retain their scientific identities. Productive-system recovery preceded the PGO
result publications. Qualification baseline, benchmark control and productive
desktop identities remain distinct.
