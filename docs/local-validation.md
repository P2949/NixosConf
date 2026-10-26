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

`scripts/local-ci.py` is the same contract under the plan's vocabulary and owns no checks:
`fast`, `changed [--base REV]` (= `affected`), `full`, `policy` (hosted-CI rejection) and `setup`.
The selector also knows `main`, which selects like `changed` but always builds the desktop closure.

The canonical interface is `scripts/validate`. Its trust chain is:

```text
scripts/validate
→ exact local Git revision
→ apps.x86_64-linux.validation
→ immutable Nix-store validator and Python from that locked flake
→ exact Git source for validation stages
→ strict exact-commit receipt
```

Bootstrap uses `nix run --builders ""` and never executes validator code from
the mutable checkout. The app embeds its source revision and verifies it against
HEAD for validation, or the requested commit for receipt admission. Thus
`require-receipt MODE COMMIT` uses COMMIT's own validator, even when COMMIT is
not HEAD. The small wrapper rejects repository paths needing URI encoding.

Supported modes:

- `fast` runs ordinary flake checks, including formatting, lint and policy tests.
  It allows a dirty tree and does not qualify a commit.
- `affected [--base REF] [--head REF]` runs fast checks, sequential path-selected
  integration builds and the desktop build when selected. The default base is
  the merge base with local `main`; head must be the checked-out commit.
- `full` runs fast checks, all storage, optimization, workstation and Minecraft
  integration targets, and the desktop build.
- `all` runs full plus the six automated developer/system-model tests; interactive
  and debugging artifacts remain explicit developer tools. The stock-contamination
  negative build must fail with the forbidden-dependency diagnostic naming its
  fixture; an unrelated failure or unexpected build success fails qualification.

Affected, full and all require clean committed source, including no untracked
files. Exact modes pass a local Git flake reference pinned to the commit SHA to
every Nix stage; transient checkout edits cannot change the qualified source.
Schema version 2 receipts record that reference and strictly validate field types
and time-zone-aware timestamps. Schema v2 rejects unknown or missing fields,
duplicate JSON keys at every object level, and unexpected stage fields. Receipts
are specific to this checkout location;
older receipt schemas require requalification. Bootstrap and validation stages
disable remote Nix builders; binary substitutes are allowed. The app pins Python
and validator source while retaining the host Nix, Git and NixOS-version tools.
Nix jobs use two cores, with two fast jobs or one integration/build job.
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
Use `all` for exhaustive qualification when needed. No GitHub API, Actions
runner, status check, PR or other remote validation service participates in
qualification. If locked dependencies/substitutes are already present,
qualification can run with GitHub unavailable. A cold Nix store may require
network access to acquire locked inputs or substitutes; dependency acquisition
is not remote validation. No human validation step decides PASS. Building never
activates the workstation.
