# Physical granular Impermanence cutover

The [granular plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
records the completed migration and release gates. Generation46 normal runs
with home and ordinary var on reset-root storage. Legacy `@home`, `@var`, their
three nested children and the four exact migration snapshots are retired.
The [persistence contract](persistence-contract.md) describes the finished policy;
the staged commands below are historical and must not be rerun on this system.

## Accepted physical sequence

Home acceptance used generation44 recovery → recovery → normal → normal,
with an unchanged independent guard requiring two consecutive verified normals.
Final-var generation45 normal → recovery → recovery → normal passed after an
actual orderly, quiesced var-only copy. The narrow Unity-preferences correction
then passed its own exact generation46 normal → recovery → recovery → normal,
with user UI acceptance and all nine preference hashes retained.

Scoped private raw-view pruning removed55 audited residue nodes and emptied82
hidden backing caches, retaining active mounts and empty target scaffolds.
The post-pruning normal receipt
`physical-boot-passed-11eafc82-f18c-4ef2-930a-7cc1c8892ae6.json` proves root344,
reset count26, all92 disposable proofs removed, eight persistent proofs and nine
Unity files retained. Earlier failed application-cleanup trials remain archived
and do not count toward acceptance. No marker was recreated after boot.

## Legacy retirement and supported rollback

`legacy-home-retirement-ready.json` classifies85,721 old-only selected paths
into16 semantic cases with no unknown required state. Private database checks
reconcile18 superseded IndexedDB blobs; old Trash discard was explicitly
confirmed. Selected authoritative var data is present in active backing.
`legacy-subvolume-retirement.json` records home256 deletion, individual var
children263/264/266 deletion, then parent261. The independent post-retirement
review verifies active topology, health and both exact generation46 ESP pairs.

The user separately confirmed deletion of the four exact migration snapshots;
`migration-snapshot-retirement.json` records326/327/328/329 removed with every
unrelated subvolume retained. Keep the small receipts, forensic roots and
separately justified earlier readiness backup staging. No extra reboot is needed.
Supported rollback is the accepted, GC-rooted generation46 normal/persistent-root
pair. Older generations requiring `@home` or `@var` are obsolete. Recovery retains
the current root and does not restore data discarded by earlier normal resets.

Final documentation/source freeze and exact-head local/CI integration are
separate release gates. The correct integration path is a granular PR into the
readiness branch, then fresh exact-head CI for its changed PR#7 head.

## Historical staged procedure (completed)

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
45–46 for deliberate retirement. The original staged safety copies were temporary until these gates passed.
Legacy sources and the four specifically confirmed migration snapshots are now
retired; the receipts below record the completed transaction. Snapshot removal requires
the plan's final confirmation; no helper here deletes subvolumes or snapshots.

Cache mounts propagate into the apparent `/persist` paths on this machine.
Before any later pruning, create a private mount namespace, make propagation
private, and use a non-recursive raw view of `@persist`. Confirm that the path to
prune resolves to `@persist`, and that the active application's cache still
resolves to root-local backing. Avoid deleting through the live propagated cache
mount. The read-only preparation inventory is retained as
`/persist/granular-migration/backing-pruning-inventory.json`; it authorizes no
deletions and boot-managed file exceptions must be left to their lifecycle rules.
