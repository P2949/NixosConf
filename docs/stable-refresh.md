# Stable refresh acceptance

## Accepted result — 2026-10-05

Source: `c5e036b6e87d9aa77700909b508ccc0c3978d5b2`.
Normal: `/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8`.
Persistent-root: `/nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8`.
Kernel: `6.18.55`. Matching recovery ISO/hash are recorded below.

Physical normal → persistent-root → normal acceptance passed: root 295 reset,
retained by recovery without another reset, then replaced by 297. Persistent
probe and machine identity survived; root-local probe disappeared on final
normal reset. See [current status](status.md) for remaining final-baseline gates.

The bv3 output and timings below are the historical pre-log-hardening offline
candidate, superseded by the exact c5e batch in plan.md. They are preserved
as comparison evidence, not the current accepted desktop identity.

## Historical preparation record

The selected NixOS 26.05 revision is
`0d9e9b832d03ac387417e16ce1febf73b2e631e1` (2026-10-04).
It replaces `774debe7a0d1b496e35677ad955a1011c6ff74f3` in an isolated
`feat/stable-refresh-validation` worktree based on the workstation preparation
branch. Only the stable Nixpkgs lock node changed. Home Manager release-26.05
was checked against upstream and is already current at
`db7d5e2332710f5abb088f6b5de927d7f9511b35`; it continues to follow stable Nixpkgs.
Disko, Impermanence, unstable packages and liquidctl retain their tested pins.
Both stateVersion values remain 26.05.

## Built desktop and closure review

Candidate:
`/nix/store/bv3qgrvavss8r34shphqch0cdp4yk14j-nixos-system-desktop-26.05.20261004.0d9e9b8`.
Compared with the prepared GameMode candidate, version changes are kernel/initrd
6.18.54 to 6.18.55, Lua 5.5.0 to 5.5.1, WebKitGTK 2.54.0 to 2.54.1 and
wpa_supplicant 2.11 to 2.12, plus system/source metadata. Mesa has no version
change in the closure summary. The [full comparison](baselines/pre-optimization/stable-refresh-20261005-closure.txt)
is retained for review.

The upstream [stable comparison](https://github.com/NixOS/nixpkgs/compare/774debe7a0d1b496e35677ad955a1011c6ff74f3...0d9e9b832d03ac387417e16ce1febf73b2e631e1)
contains the relevant kernel, Lua, WebKitGTK and wireless updates. This is a
chosen stable refresh, not an unstable graphics/toolchain replacement.

## Recovery artifact

The matching pinned, secret-free ISO is
`/nix/store/d55ny1z4d53slhz3ilvyy2mg6d8khrqn-nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso/iso/nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso`.
Size: 1496678400 bytes. SHA-256:
`52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
Its new Ventoy filename is
`nixos-workstation-recovery-26.05.20261004.0d9e9b8-x86_64-linux.iso`.
Media copy/flush verification passed, including SHA-256 after a read-only
remount and an exFAT read-only check reporting clean. Prior recovery images remain.
The supplied continuation guide reports a completed read-only filesystem drill;
exact media-boot receipt details still need reconciliation in the recovery runbook.

The desktop and ISO are protected by additional explicit GC roots
`stable-refresh-candidate` and `stable-refresh-recovery-iso`. The existing eight
roots remain; the private receipt now records ten. Retire none before the
final milestone review.

## Acceptance

Fast flake checks, desktop/ISO builds and all six heavy VMs passed:

| Test | Duration | Result |
|---|---:|---|
| Root A, three resets | 318.18 s | passed |
| Safety matrix | 147.38 s | passed |
| Interrupted recovery | 323.84 s | passed |
| Root B, stable identity | 322.56 s | passed |
| Persistent-root fallback | 429.01 s | passed |
| Real workstation profile, including polkit allow/deny | 69.25 s | passed |

The complete build receipts are retained privately under `/persist`.
Offline validation is complete for this candidate.
No profile installation, service restart, live activation or reboot occurred.
This historical candidate was superseded by the accepted result above.
Independent backup, final firmware, workload and soak gates remain open.
