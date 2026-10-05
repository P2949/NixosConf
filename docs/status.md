# Stock workstation readiness status

This is the current status entry point. `plan.md` retains the full execution
ledger and Phase A–Y continuation directive until final baseline completion.

## Accepted operating system

- Source: `c5e036b6e87d9aa77700909b508ccc0c3978d5b2`.
- Normal closure: `/nix/store/czk5a2wn8di3pgv8a6w0b8aj3286g3h3-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Persistent-root closure: `/nix/store/9ppcqjkfnid501na0wc8jjysynp0kp1p-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Kernel: `6.18.55`; stable Nixpkgs: `0d9e9b832d03ac387417e16ce1febf73b2e631e1`.
- Recovery ISO: `d55ny1z4d53slhz3ilvyy2mg6d8khrqn`; SHA-256
  `52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
- Physical normal → persistent-root → normal passed on 2026-10-05;
  final normal root subvolume 297. Home and var intentionally remain persistent.

## Implementation line

`feat/pre-optimization-readiness`, based on integrated main `f89205c`.
Current HEAD is obtained with `git rev-parse HEAD`; exact validation revisions
are recorded in plan.md rather than maintaining a self-referencing HEAD literal.

The incomplete username refactor is repaired in `2334858`: full flake checks
pass; workstation-smoke and desktop reproduce their prior exact outputs.
`2976771` removes the merged feature branch from push CI; PR CI is the
feature-branch validation path. Main retains required Flake checks protection.

## Open gates

Storage/test/image organization, explicit Nix/Bash data interface, Commander
Core policy ownership, native build/activation guards and stock closure
exclusions are implemented on the draft readiness PR. Fast checks pass;
activation has 45 fixture cases, native action VM acceptance and a read-only
live positive check. The stock negative build rejects the intended test fixture.
Candidate normal/persistent closures are GC-protected and remain uninstalled.

All five reset VM scenarios passed. The user confirmed the separate secrets
backup was restored during a real system recovery, completing that gate on
user-reported evidence. Retain BIOS 3201/current ME; no firmware update is planned.

Still open: executed blank-disk reconstruction, VMX enablement,
sustained CPU/RAM/cooling/storage health, final
exact-candidate workloads and multi-day soak. See the latest plan.md execution
records for exact source/artifact identities and private receipt locations.

The user chose a dedicated folder on existing Ventoy for the home backup,
overriding the guide's older recommendation against that target. It is additive
and does not reformat/erase Ventoy. An engine exclusion audit and supplemental
47-file restore passed; the main archive is verified with representative restore
and clean unmount (see the accepted receipt below).
The newer guide reports earlier refactor checks and a read-only recovery drill;
retain that provenance and reconcile exact physical-media receipts.

No final pre-optimization tag exists yet. Compiler optimization remains outside
this project. Any final physical checks are batched to minimize interruptions.

## Latest exact candidate identity

After deriving reconstruction from the real desktop and moving/asserting
workstation activation safety, the validated pre-fuzzel/Alacritty normal/persistent builds reproduce
`l994fn5hpd2g2rijyffprl4368587m5w` and
`cxc50rmb8i6akb62fcvzz3xkszzqf895` respectively (both stock26.05.20261004.0d9e9b8).
Existing closure review and GC roots apply to those artifacts. These remain uninstalled.
User desktop commits c3476c1/6893511 need new candidate validation; the prior
closure equality is not evidence for those changes.
Activation composition tests and full flake checks passed. The main Ventoy
archive passed integrity, SHA-256 and three representative restored-file hash
comparisons, with terminal receipt and clean unmount. Reconstruction source736b0fb
completed independent installed-disk boot/reset/recovery checks but exited1 at
final offline inspection: standalone Btrfs nologreplay was rejected. The narrow
rescue=nologreplay correction is running in retry session89323, source9731b6d
plus the existing local desktop comment edit; terminal acceptance remains open.
The newest unified guide in plan.md supersedes older next-step ordering: no
further broad refactor; close evidence before physical maintenance and freeze.

Latest backup result: [backup receipt summary](backup-restore.md#independent-ventoy-home-backup-accepted--2026-10-05).
Earlier open-backup statements above are superseded by this accepted result.
