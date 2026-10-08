# Physical granular Impermanence cutover

The [active plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
records acceptance. Source/VM success does not complete the physical gates.
The first candidate is `desktop-home-cutover`: home is root-local and `@var`
remains mounted. The final `desktop` removes both legacy mounts. Neither old
subvolume is deleted during either cutover.

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

After home acceptance, use `granular-arm-cutover var FINAL_SYSTEM` for the var
cutover. Its final copy is var-only and refuses to overwrite active persisted
home profiles with root-local scaffolding. Repeat the system/application and
normal/recovery/return checks against the final configuration.

## Retirement

Audit `/persist` and remove undeclared migration copies and hidden underlying
cache data only after application and physical acceptance. Compare originals
one last time, inspect each old var descendant subvolume, then follow stages
45–46 for deliberate retirement. The full copied home and snapshots are still
temporary safety material until those gates pass. Snapshot removal requires
the plan's final confirmation; no helper here deletes subvolumes or snapshots.
