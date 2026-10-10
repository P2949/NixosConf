# Blank-disk reconstruction test

`nix build .#blank-disk-reconstruction --no-link --print-out-paths` is an
explicit heavy test; ordinary flake checks evaluate it but do not execute it.

The installer receives a new 96 GiB sparse virtual disk and the production
Disko layout, changing only the virtual device identity. It creates GPT, 4 GiB
ESP, 32 GiB swap and the Btrfs persistence islands. A test-only password hash
uses the production `/persist/secrets/<username>-password-hash` contract.

The fixture derives from the actual desktop NixOS definition with extendModules;
only virtual hardware/test overrides are added. Production imports, specialArgs
and Home Manager integration are inherited.

The declared workstation and Home Manager closure is copied onto the target
with nixos-install. The installer can obtain declared build artifacts from the
NixOS test store; the installed VM is then launched with only its installed disk
and UEFI firmware. It has no host Nix store, 9p mount or host-supplied kernel or
initrd. This distinguishes artifact provisioning from runtime correctness.

Test variants disable physical cooling, use virtual hardware and prevent
maintenance timers from running. They retain production storage, identity,
credential, activation-guard and workstation composition contracts. Actual GPU,
cooling, firmware and graphical workload acceptance remains physical work.

Required checks: blank signatures before Disko; copied closure and EFI fallback;
normal root reset twice; persistent mounts/identity/probes; persistent-root
one-shot boot with retained root identity/reset count; return to normal with
a further reset; credential persistence and volatile journal reset; all five
production Btrfs subvolumes inspected read-only after shutdown; absence of
`@home`/`@var`; root-local home/var probes discarded and declared home/var plus
nested optimization probes retained; no failed units.
Implementation/evaluation alone does not satisfy this gate: retain a successful
execution receipt before merging storage/topology changes that affect this
contract. The immutable baseline already contains an accepted successful execution.

The evaluated-device import was tested after the first terminal pass and
deferred: Disko's computed script values retained the production device path
despite the installer override. The raw host layout import allows Disko to
evaluate its script in the installer configuration. The installed workstation
still derives from the actual desktop with extendModules.
