# Repository change policy

Every file on `main` must remain useful after the feature that created it is
finished. Implementation chronology belongs in Git, tags and PRs. General
repository organization is finished after the post-Prism maintainability work;
normal development follows the rules below.

## Ownership and scope

Keep the existing explicit architecture: hosts own physical policy, profiles
compose roles, modules provide reusable NixOS features, and Home Manager owns
user/session policy. Packages, images, tests, scripts, docs and optimization
retain their current responsibilities. A new top-level directory requires a
new responsibility.

Preserve the overall flake architecture, desktop host composition, workstation
profile, core/desktop modules, desktop/development split, Disko layout, root-reset
and recovery architecture, test registry and top-level layout. Do not introduce
flake-parts, flake-utils, a host/user framework, automatic discovery, individual
application persistence modules or tiny option-only modules without a concrete
new need.

One conceptual feature belongs to one branch/PR. Separate runtime changes from
cleanup claimed to preserve behavior or closures. Compare desktop outputs before
and after such cleanup; investigate unexpected differences before acceptance.
Tests protect real invariants and regressions. VM/physical acceptance is required
only when it resolves uncertainty that automated checks cannot cover.

## Documentation and artifacts

Plans live in Issue/PR descriptions. Before merge, move permanent operating
policy into normal documentation and remove implementation journals, temporary
scripts and evidence. Retain tooling only when it has recurring operational value.
Git, tags and PRs preserve history; `docs/history` is an index, not an archive dump.
Do not commit generated files that Nix can produce. Raw evidence stays outside
Git except canonical baseline evidence; remove credentials and machine-private
identifiers before publishing any receipt.

One authoritative location owns each current fact:

| Fact | Owner |
| --- | --- |
| Qualification identities/evidence | `docs/baselines/pre-optimization/baseline-final.md` |
| Benchmark control identities/policy | `docs/stock-policy.md` |
| Optimization closure exclusions | `docs/stock-control.md` |
| Productive desktop state | `docs/status.md` |
| Experiment procedure | `docs/optimization.md` |

README provides navigation. Other documents link to the fact owner rather than
copying exact hashes or detailed policy. The productive desktop, qualification
baseline and benchmark control are distinct identities.

## Feature completion gate

Before merge:

- Decide ownership and implement the bounded feature.
- Run necessary checks; classify application persistence where applicable.
- Record VM or physical acceptance when needed; never label an unexercised
  workflow as tested.
- Update permanent documentation and current status.
- Remove temporary plans, scripts and raw evidence from the live tree.
- Run `nix fmt -- --ci`, `nix flake check --no-write-lock-file --print-build-logs`
  and the desktop build; inspect changed closures and verify PR CI.

Then merge and delete the feature branch. PR metadata owns exact source/CI and
acceptance receipts. Do not make source documents certify their own future CI.

## Adopt capabilities when needed

Experimental ideas stay in GitHub Issues until adopted. Generated custom-module
docs and the real-config bootloader VM are explicit developer tools; generated
docs are not committed and the desktop VM is not an ordinary CI build.

Add an nspawn test tier when service orchestration needs it without boot/storage
modeling. Consider Facter only after a useful hardware comparison. Repart/dm-verity
belong to separate exploratory images; immutable `/etc`, Userborn and perlless
belong to VM experiments. Add kexec diagnostic systems or cross-architecture
emulation only for an actual use case. Additional recovery or Impermanence
machinery requires a concrete failure it solves. Existing capability alone does
not justify a permanent repository feature.
