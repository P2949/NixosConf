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

## Root-policy preparation, 2026-10-05

Compared the running third-trial closure
`/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe`
with the built default/recovery candidate
`/nix/store/j4mmsn2b0bhblr06jhx4jnp7s4qp1w9p-nixos-system-desktop-26.05.20261002.774debe`.

The comparison reported size changes in generated `dbus`, `etc`, `initrd-linux`,
configuration reference/manual, `nixos-system-desktop`, `system` and `user`
outputs. It reported no package version transitions. The candidate includes
the additional persistent-root recovery closure. No activation or host reboot
was performed by this review.
