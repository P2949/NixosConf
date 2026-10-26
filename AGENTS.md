# Repository instructions

NixOS configuration for the main desktop workstation.

## Architecture

- `hosts/` physical facts and policy; `profiles/` role composition.
- `modules/` reusable NixOS features; `home/` user/session policy (Home Manager).
- `packages/` custom derivations; `tests/` protect real invariants.

Read [README.md](README.md) and [docs/repository-policy.md](docs/repository-policy.md)
before architectural changes.

## Completion checks

```console
./scripts/validate fast     # during development
./scripts/validate affected # clean feature commit before pushing
./scripts/validate full     # exact local merge commit before main advances
```

See [local validation](docs/local-validation.md) for receipts, hooks and exhaustive checks.
Hosted CI and remote validation services are prohibited.

## Safety

- Passwordless sudo `ALL NOPASSWD` and Nix trusted-user access are intentional.
  Agents running as the workstation user can therefore potentially act as root;
  generic hardening must preserve these privileges. Operational restrictions
  below still apply unless the task explicitly authorizes the action.
- Recovery relies on declarative state, Git, generations, ephemeral-root reset
  and activation checks. Rollback restores integrity and availability within
  those mechanisms; it cannot undo confidentiality loss.
- Builds do not activate. Do not run `nixos-rebuild switch`, reboot or deploy unless explicitly asked.
- Do not commit or push unless explicitly asked.
- Persistence changes need an entry in `docs/ephemeral-state-audit.md` and matching tests.
- Inspect `git diff` before declaring completion.
