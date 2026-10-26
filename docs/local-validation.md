# Local validation

Validation execution is local-only on the NixOS development workstation.
GitHub is source hosting, not validation infrastructure. Hosted CI, GitHub
Actions (including self-hosted runners), and equivalent remote validation
services are prohibited. PRs may support human review or history but never
control validation, merge eligibility, or release qualification.

Install the tracked push hook in each checkout:

```bash
./scripts/setup-local-validation
```

The canonical orchestrator is `scripts/validate`:

- `fast` runs ordinary flake checks, including formatting, lint and policy tests.
  It allows a dirty tree and does not qualify a commit.
- `affected [--base REF] [--head REF]` runs fast checks, sequential path-selected
  integration builds and the desktop build when selected. The default base is
  the merge base with local `main`; head must be the checked-out commit.
- `full` runs fast checks, all storage, optimization, workstation and Minecraft
  integration targets, and the desktop build.
- `all` runs full plus the six automated developer/system-model tests; interactive
  and debugging artifacts remain explicit developer tools.

Affected, full and all require clean committed source, including no untracked
files. The runner disables remote Nix builders and obtains Python from the
locked Nix input. Nix jobs use two cores, with two fast jobs or one integration/build job.
Tests and their derivations remain authoritative in `tests/default.nix` and
`flake.nix`; selection lives in `scripts/validation-targets.py`.

Successful qualification writes machine-readable PASS receipts under
`git rev-parse --git-path local-validation`, alongside stage logs. Receipts bind
repository identity, exact commit and tree, lock hash, mode, selection, stages,
tool/system provenance and timestamps. Failed or interrupted runs cannot qualify
source. These local artifacts are never committed or added to system persistence.

The pre-push hook rejects a feature branch without an exact affected PASS and
rejects `main` without an exact full PASS. Inspect admission without a push:

```bash
./scripts/validate require-receipt full HEAD
```

Develop on a feature branch, commit, then run `./scripts/validate affected`.
Merge locally into `main`, run `./scripts/validate full` against the exact merge
commit, then push `main`. Earlier feature receipts do not qualify a merge commit.
Use `all` for exhaustive qualification when needed. No network service or human
validation step decides PASS; GitHub can be unavailable throughout qualification
and local merge decisions. Building never activates the workstation.
