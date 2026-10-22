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
nix fmt -- --ci
nix flake check --no-write-lock-file --print-build-logs
nix build .#nixosConfigurations.desktop.config.system.build.toplevel
```

## Safety

- Builds do not activate. Do not run `nixos-rebuild switch`, reboot or deploy unless explicitly asked.
- Do not commit or push unless explicitly asked.
- Persistence changes need an entry in `docs/ephemeral-state-audit.md` and matching tests.
- Inspect `git diff` before declaring completion.
