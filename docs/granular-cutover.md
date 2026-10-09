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
Generation 44 home acceptance is complete. Both accepted recovery trials passed
all 100 markers with unchanged root ID/UUID, stable identity and healthy services.
The user ran the second verifier immediately after reboot, before apps. Earlier
cleanup-related failed attempts remain archived and unaccepted. The required
home sequence recovery → recovery → normal → normal is fully accepted. Generation 44 remains the canonical candidate.

The standalone checker nests only the observed Codex and Firefox telemetry
proofs inside generated directories. Eight marker regressions and all twelve
unchanged home-acceptance cases pass, as do full flake checks. Retention still
requires exact tokens; normal reset must remove entire generated containers.
Firefox artwork cleanup can remove its whole cache directory, so verify before
launching applications. No additional cleanup-model architecture is introduced.

Both normal home trials now pass all 100 requirements. Root 330 was replaced by
332 then 334; each normal removed 89 disposable proofs/three containers and
retained 11 persistent proofs before cleanup. The required recovery → recovery
→ normal → normal sequence is accepted, the independent home guard passes, and
the user reconfirmed important application state works after these trials.
Home policy is frozen at its recorded fingerprint; change only for a defect.

Exact immutable-source final desktop/recovery and the complete required suite
now pass, including fresh six-boot granular, five root, blank-disk reconstruction
and workstation tests. Source/lock and exact closures are recorded in
`final-var-candidate-build.json`; local checks do not certify final-head CI.

The existing var helper installed final generation 45 boot-only and its reviewed
shutdown copy completed on the user's orderly reboot. A clean var-only policy
comparison preceded one-shot selection. First final normal boot
`971b1496-f119-46ac-a248-d23202cdab92` passes all 100 proofs: 92 disposable proofs
gone, eight persistent proofs retained. Root 336 is new; both home and var are
on @root. Discovery and the user's representative application recheck pass;
both policies are frozen. Receipt:
`physical-boot-passed-f0309ac2-5ee1-49c5-96a6-ae7610598589.json`.
The temporary fallback override was cleared after acceptance; generation 45
normal is default. Both final ESP pairs and generation-44 rollback artifacts
match. Next is final recovery → recovery → normal, then gated raw-backing
pruning and one further normal sentinel boot before retirement. Verify each
ticket before opening apps; its disappearance after success is expected.
No agent reboot or retirement is initiated.

The first final recovery is accepted by
`physical-boot-passed-8fd21368-c8c4-40ee-b40c-34b2fa71b345.json`: all 100 proofs,
root 336/UUID and reset count 22 retained. The second recovery is accepted by
`physical-boot-passed-a41581f2-d86b-43a6-a7bb-1b6673b3f608.json` with those same
100 proofs/root/reset invariants. Return-normal is prepared against exact normal
generation 45; all 100 tokens pass preboot checks and its entry is selected once.
Return-normal is accepted by
`physical-boot-passed-b07b3cd2-79b2-40c6-80b7-719e61c7a8e7.json`: new root 338,
reset count 23, 92 disposable proofs gone and eight persistent proofs retained.
The refreshed raw-persist audit found previously unclassified Unity editor
preferences. The user requested their preservation, authorizing a narrow home
declaration amendment. Protect both versions and validate/physically accept the
exact corrected candidate before pruning and retirement. No old receipt proves
a future corrected closure.

The corrected Unity-preferences candidate is validated and installed boot-only
as generation 46: normal `15f6c5dsjl047j7my4c7cpkdhk6ly2xp`, recovery
`7lkx40kh36s809bz1yr9bmfdddy1n80a`; both ESP pairs match. Generation 45 remains
running/fallback. Firefox has exited; the two preference versions were compared
and the newer current working state reconciled to backing, preserving separate
archives of both versions. All 100 proofs and nine authoritative preference
hashes pass preboot checks; normal 46 is selected once. After the user's reboot,
verify before apps, independently confirm the new bind/hashes, and check Unity's
UI state before corrected recovery/recovery/normal. No var copy is repeated.

Corrected normal 46 is accepted by
`physical-boot-passed-cb942ba2-6d02-4541-9a24-e6c34da85f45.json`: all 100 proofs,
new root 340/reset count 24 and active @persist Preferences bind with all nine
authoritative hashes. User confirms Unity preferences look right; normal 46 is
now default. First corrected recovery is prepared and selected once. Verify
before apps after the user's reboot; root 340/reset count 24 and all preference
data must survive. Ready record: `unity-preferences-recovery-cycle-1-ready.json`.

First corrected recovery passes all 100 proofs, retained root 340/reset count 24
and all nine Unity hashes; receipt
`physical-boot-passed-2348e96a-9c34-4ce8-8cd1-3b807c32b4d0.json`.
Second corrected recovery is prepared and selected once. Ready record:
`unity-preferences-recovery-cycle-2-ready.json`; verify before apps after the
user's self-reboot. Return-normal and retirement gates remain pending.

Second corrected recovery passes the same root/count, all 100 proofs and nine
Unity hashes; receipt `physical-boot-passed-1873d5c4-88e9-4444-9fed-9589d62b26cb.json`.
Corrected return-normal passes receipt
`physical-boot-passed-3919c82a-ef26-4b58-be41-9633439795bb.json`: new root 342,
reset count 25, 92 disposable proofs gone, eight persistent proofs and nine Unity
hashes retained. The corrected normal → recovery → recovery → normal chain is
accepted; `corrected-policy-freeze-20261009.json` refreezes the accepted policy.
Fresh raw inventory and scoped pruning are complete. Private non-recursive
`@persist` pruning removed 55 audited E/D nodes and emptied 82 hidden backing
caches, retaining empty mountpoint scaffolds, active cache identities, every
declared path and all nine Unity hashes. Originals and snapshots remain intact.
Receipt: `scoped-backing-prune-20261009.json`. Read-only re-audit finds zero
undeclared residue or hidden cache data. Post-prune physical proof and retirement
gates remain. User confirms apps closed and process inspection agrees. The
post-pruning normal trial is now seeded and selected once: all 100 tokens,
generation-46 ESP artifact hashes and the Unity bind/nine hashes pass preboot
checks. `post-pruning-normal-ready.json` records expected reset count 26 and new
root. The post-pruning physical receipt
`physical-boot-passed-11eafc82-f18c-4ef2-930a-7cc1c8892ae6.json` passes on
root 344/reset count 26, retaining all nine Unity hashes. Final read-only legacy
comparison now precedes retirement; all original subvolumes and snapshots remain.

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
and Firefox telemetry cleanup delete unknown regular files but skip directories;
those specific proofs use generated directory/token pairs. Recovery requires
their tokens, and normal boot requires both tokens and directories to disappear.
Firefox MPRIS artwork cleanup removes its whole directory, so applications must
remain closed until verification. No missing marker may be recreated
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
