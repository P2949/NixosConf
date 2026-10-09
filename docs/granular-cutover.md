# Physical granular Impermanence cutover

The [active plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
records acceptance. Source/VM success does not complete the physical gates.
The first candidate is `desktop-home-cutover`: home is root-local and `@var`
remains mounted. The final `desktop` removes both legacy mounts. Neither old
subvolume is deleted during either cutover.

Current result: generation 42 completed its quiesced copy and first physical
home matrix. Home is root-local and legacy var remains. A redundant seed-file
bind over native legacy var was removed from the intermediate policy; corrected
generation 43 first carried this fix. The additional observed Fuzzel history
omission is now restored/corrected in generation 44, installed boot-only with
both ESP artifact pairs checked.
Generation 44 persistent-root is now live. The user confirmed the important application workflows
work after the home cutover and allows coordinated reboots. Following the supplied
2026-10-09 review, the home sequence is recovery → recovery → normal → normal
on the latest corrected home candidate. A specific Fuzzel usage-history omission
was found/restored and its persistence/configuration corrected. Generation 44
builds and full checks pass, including a fresh combined six-boot VM. The unbooted
generation-43 tickets were archived as superseded, not accepted. A new 100-sentinel
`home-recovery` ticket targets generation 44; its recovery entry is selected once,
with normal generation 44 still the main profile/default. The first recovery
boot retained root ID/UUID and healthy services, but Codex startup deleted the
plain shell-snapshot proof file. That strict attempt is unaccepted and its failed
ticket is archived. The standalone test tool now nests only that cache's marker
inside a generated directory, with seven regression cases and unchanged strict
normal/recovery checks. The corrected first recovery trial now passes all 100
markers, retaining root ID/UUID and healthy services. A fresh 100-marker second
recovery ticket is prepared for the same generation 44; both normal trials follow.
No agent reboot is scheduled or initiated.

## Preparation and final copy

Finish formatting, flake checks, the combined reboot regression, desktop and
home-only builds, reconstruction, workstation smoke and root safety checks.
Record the exact built closures and retain migration tooling with GC roots
under `/persist/granular-migration`. Save application work before rebooting.

The packaged `granular-arm-cutover home SYSTEM` performs a boot-only installation
of the already built `SYSTEM` with `nixos-rebuild boot --no-reexec --store-path`. This avoids
re-evaluating a changing checkout during installation. It pins the current boot
entry as the default, records the rollback closure/entry, and creates/starts
`granular-final-copy.service` in `/run/systemd/system`. The runtime unit and
private copy log are recorded under `/persist/granular-migration` for review.
It does not request a reboot or replace live mounts.

On orderly shutdown the unit stops **after** the desktop user manager, session
scopes, greeter, NetworkManager, Bluetooth, random-seed service and Nix daemon,
and **before** the required mounts. Its immutable stop command:

1. Refuses if any desktop-user process remains.
2. Seeds the exact-closure physical sentinel matrix.
3. Mirrors and verifies only the evaluated allow-list with metadata preserved.
4. Sets the candidate as a one-shot boot selection only after verification.

Failure leaves the old boot default selected and both originals available.
Do not manually select the candidate after a failed copy. Read
`final-copy-shutdown.log`, repair the cause and deliberately clear/reseed any
failed pending sentinel ticket before retrying. A forced reset bypasses this
shutdown copy and boots the old default. Stopping the armed service manually
also invokes its copy command; while the desktop is running, its process guard
refuses the cutover.

## Physical acceptance

After the candidate boots, run the retained `granular-physical-check verify` as
root. It requires a different boot ID, the exact expected system closure,
root-local home, the phase-specific var mount, persistent islands, stable
machine identity and all sentinels. Every declared cache exception is checked.
Success saves a private receipt and removes only the generated surviving
sentinels. Failure retains the pending ticket for diagnosis.

Application cleanup may delete cache proof files independently of a reboot.
Verify promptly after boot before exercising apps, and re-read generated markers
before reboot if applications have been used since seeding. Codex shell-snapshot
startup deletes unknown regular files but skips directories; that one proof uses
a generated directory/token pair. Recovery requires its token, and normal boot
requires both token and directory to disappear. No missing marker may be recreated
after boot to manufacture a passing receipt. Archive failed attempts explicitly;
they do not count toward the physical gate.

Once the first home boot is accepted, clear the temporary EFI default override
with `bootctl set-default ''`; the boot-only installation's `loader.conf` then
selects the home candidate on subsequent normal boots. Exercise the applications
and check settings, authentication, sessions, projects and saves. Android Studio
is not installed; its current ADB state can be checked, and Studio-specific
paths need another audit once the application creates them.

Seed each further trial with `granular-physical-check seed MODE SYSTEM`, then
select the already installed normal/recovery entry for one boot and reboot:

| Mode | Expected next boot |
| --- | --- |
| `home` | Intermediate normal: root/home reset, legacy var retained |
| `home-recovery` | Intermediate persistent-root: root/home/var retained |
| `normal` | Final normal: root/home/var reset |
| `recovery` | Final persistent-root: root/home/var retained |

For recovery, `SYSTEM` is the candidate's exact
`specialisation/persistent-root` closure. Verify each ticket before seeding the
next. Perform repeated normal and repeated recovery boots and a return to normal.
Do not install a recovery-only system profile and later select a stale normal
entry: the bootloader may prune its initrd. Keep the candidate's main generation
installed with both boot entries, or reinstall the exact normal generation.

Use corrected generation 44 for recovery → recovery → normal →
normal, verifying each
`home-recovery`, `home-recovery`, `home`, `home` ticket in that order. Repeated
recovery must retain root/home; return-normal must discard recovery-only state.
This ends with the two consecutive accepted normal receipts required by the
unchanged var guard. Recheck important application state and freeze home policy
unless a specific defect appears.

Before arming var, build/check the exact current-source desktop and its recovery
specialisation, granular VM regression, blank-disk reconstruction and workstation
evaluation again. Record source/lock identity and exact resulting closures;
run the independent home-acceptance guard. Then use
`granular-arm-cutover var FINAL_SYSTEM` for the var cutover. Its final copy is var-only and refuses to overwrite active persisted
home profiles with root-local scaffolding. Repeat the system/application and
normal/recovery/return checks against the final configuration. The final chain
is first accepted normal → recovery → recovery → normal. After gated raw-backing
pruning, run one further complete sentinel matrix before legacy retirement.
Freeze final source and obtain exact-head local and CI/PR checks before merge
readiness; local receipts alone are not CI.

The arming helper enforces stage 23 before any var installation/EFI/service
change: two consecutive verified normal cycles must have been seeded with
root-local home, and the latest receipt must match the current boot and running
closure. The initial legacy-home cutover is not a repeated root-local cycle.
New tickets record the source topology; old receipts without it cannot count.
Recovery interrupts the consecutive normal-cycle history, and duplicated
receipts cannot count as separate boots.

## Retirement

Audit `/persist` and remove undeclared migration copies and hidden underlying
cache data only after application and physical acceptance. Compare originals
one last time, inspect each old var descendant subvolume, then follow stages
45–46 for deliberate retirement. The full copied home and snapshots are still
temporary safety material until those gates pass. Snapshot removal requires
the plan's final confirmation; no helper here deletes subvolumes or snapshots.

Cache mounts propagate into the apparent `/persist` paths on this machine.
Before any later pruning, create a private mount namespace, make propagation
private, and use a non-recursive raw view of `@persist`. Confirm that the path to
prune resolves to `@persist`, and that the active application's cache still
resolves to root-local backing. Avoid deleting through the live propagated cache
mount. The read-only preparation inventory is retained as
`/persist/granular-migration/backing-pruning-inventory.json`; it authorizes no
deletions and boot-managed file exceptions must be left to their lifecycle rules.
