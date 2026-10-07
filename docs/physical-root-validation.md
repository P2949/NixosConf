# Controlled physical root validation

Status: source `c5e036b6e87d9aa77700909b508ccc0c3978d5b2` already
passed physical normal → persistent-root → normal validation on 2026-10-05,
ending at root subvolume297. The original three opt-in trials also passed;
these are separate accepted historical results. The current readiness candidate
is now installed as generation37. Its current normal boot has fresh-root,
reset-log, identity/credentials, service, graphical login, network and persistent
mount evidence. Its complete generation37 physical chain now passes; exact evidence is below.
Keep the graphical session alive during offline preparation.

The supplied guide reports an earlier read-only recovery drill. Its exact ISO,
date and physical inspection receipt still need reconciliation; existing build,
hash and copy receipts alone cannot establish that event. Reconcile before
scheduling another drill. The older artifact-specific procedure below is
historical and does not supersede the current stable ISO or this evidence status.

## Current maintenance preflight, 2026-10-05

Generation37 is already installed by the user's earlier switch: normal
`nixos-generation-37.conf` targets0p67xd3scigqmmn65a0x5skdcsf6025b;
persistent-root entry targetsph12l3y4k9jjmp5vhxwlkc11x4js2gjx.
Kernel and initrd copies on the ESP match both store artifacts byte-for-byte.
Accepted generation35 normal/persistent entries remain available. Both new
candidate closures have independent GC roots; full store verification passed.
No second boot installation is needed unless the candidate changes.

The user enabled VMX and rebooted normal generation37; /dev/kvm and actual
KVM initialization now pass. Firmware photo/runtime evidence is recorded in
[firmware baseline](baselines/pre-optimization/firmware-20261005.md).
CPU-heavy editor acceptance aborted at84C under the80C guard; review cooling
and operating conditions before further heavy tests. Preserve the live session.

The staged generation37 sequence is complete: persistent-root retained
root300 and reset count6, then return-normal created root302/count7, removed
the root-local sentinel and retained the persistent sentinel. The private
preparation, persistent-boot and return-normal receipts are terminal accepted
evidence, detailed below. No remaining generation37 root-chain reboot is
required. The tuned cooling candidate is separately test-active with unchanged
kernel/initrd; see [current status](status.md) for its incomplete load validation.

## Physical validation procedure (generation37 sequence completed)

The normal/persistent-root/return sequence below is a reusable procedure,
not a request to repeat accepted generation37 boots. Any genuinely new
required physical window must be coordinated to preserve user work.

This section supersedes the historical opt-in installation commands below.
Do not repeat the three successful reset trials. Complete remaining offline
checks, independent backup/restore and source integration before this window.
Keep the known-good persistent generation and forensic roots. Record the exact
source revision, lock hash, built default closure and its persistent-root
specialisation; do not infer those paths from an earlier build.

1. Build and protect the accepted default/recovery closures and matching ISO.
   Preview activation changes; use boot-only installation when ready, preserving
   the live session. Inspect systemd-boot entries and verify each points at its
   recorded closure. Do not run live `test` or `switch` for this transition.
2. Reconcile the reported earlier physical drill first. If it does not establish
   the required artifact and inspection, batch the matching Ventoy ISO drill
   below into this maintenance window. For the selected stable refresh, the staged filename is
   `nixos-workstation-recovery-26.05.20261004.0d9e9b8-x86_64-linux.iso`,
   SHA-256 `52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
   Its copy/remount checks passed; exact physical drill acceptance is unverified.
3. Select the accepted normal default entry, which now resets root. Verify the
   exact running closure, fresh root, one reset invocation, identity, credentials,
   persistent state, networking, cooling and graphical login. Record private
   evidence. Do not claim acceptance merely because the boot menu entry exists.
4. During the same maintenance window select its `persistent-root` recovery
   specialisation. Verify the exact specialisation closure, unchanged root
   identity and reset-log completion count, retained root sentinel, machine ID,
   earlier journals, credential sources and services. The recovery variant
   prevents future resets; it does not restore previously discarded files.
5. Return to the accepted normal entry when physical checks pass, then continue
   final workloads/soak. Choose firmware/virtualization changes before final
   acceptance so subsequent policy changes do not invalidate the freeze.

These remain physical acceptance gates and require a planned interruption. No
reboot is scheduled by this runbook; batch the checks and avoid intermediate
reboots for documentation, offline builds or repeated smoke tests.

## Historical opt-in trial procedure

## Before installing

1. Require current safety, recovery, A, B and fast checks to pass. B must retain
   journal markers and a stable machine ID through three boots.
2. Independently back up critical home data and encrypted `/persist/secrets`;
   restore a representative file and verify it. Record destination and date
   privately. Verify bootable recovery media before destructive boot testing.
3. Retain forensic roots `@root-pre-ephemeral`, `@root-failed-ephemeral-1` and
   `@root-broken-runtime-20261004`; do not run GC or prune generations.
4. Inspect the ESP with `sudo bootctl list --no-pager`; record a current
   known-good persistent-root entry and its closure. The running closure is
   not proof an older boot entry works; rehearse rollback independently.
5. Audit root-local data using the [persistence contract](persistence-contract.md).
   Check actual topology from a temporary top-level mount, then unmount it:

```sh
findmnt -no SOURCE,FSTYPE,OPTIONS /
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo mkdir -p /mnt/nixos-preflight
sudo mount -t btrfs -o ro,subvolid=5 \
  /dev/disk/by-id/nvme-Force_MP600_2046822900012855404A-part3 /mnt/nixos-preflight
sudo btrfs subvolume list /mnt/nixos-preflight
sudo btrfs subvolume list -o /mnt/nixos-preflight/@root
sudo btrfs subvolume list -o /mnt/nixos-preflight/@root/tmp
sudo btrfs subvolume list -o /mnt/nixos-preflight/@root/srv
sudo umount /mnt/nixos-preflight
```

Only direct `tmp` and `srv` child subvolumes are allowed, with no grandchildren.
An absent child needs no inspection. Any staging must be completely empty.
Do not delete an unexpected child to make the check pass; classify it first.
Verify password-file metadata privately and use `sudo test -s` without printing
contents. `/persist/secrets` must be root-owned and access restricted.

Seed stable identity without overwriting a conflicting backing identity:

```sh
sudo sh -eu -c '
  test "$(wc -c < /etc/machine-id)" -eq 33
  grep -Eq "^[0-9a-f]{32}$" /etc/machine-id
  install -d -m 0755 /persist/etc
  if test -e /persist/etc/machine-id; then
    cmp /etc/machine-id /persist/etc/machine-id
  else
    install -m 0444 /etc/machine-id /persist/etc/machine-id
  fi
'
```

Do not live-activate machine-ID persistence against the existing file. The
first selected reset boot constructs a fresh root and mounts the backing ID.

## Install and select manually

```sh
nix build '.#nixosConfigurations.desktop.config.system.build.toplevel' --no-link
sudo nixos-rebuild boot --flake '.#desktop'
sudo bootctl list --no-pager
```

Check both the parent persistent-root entry and the `ephemeral-root` entry
exist. Keep the parent as the default; manually select `ephemeral-root` in
systemd-boot for each trial. Do not run `switch` or `test` into the child.
Installing entries is not proof of a successful physical boot.

## Three physical boots

Record the boot ID, closure, machine ID, root subvolume identity and persistent
reset log privately after each boot. Check graphical/password login,
Home Manager, networking, cooling, journal, D-Bus and logind as well as:

```sh
readlink -f /run/current-system
cat /proc/sys/kernel/random/boot_id
findmnt /
for target in /nix /var /home /persist /var/lib/nixos-optimization; do
  findmnt "$target"
done
stat -c '%a %n' /tmp
systemctl --failed --no-pager
systemctl is-active NetworkManager dbus systemd-logind commander-core home-manager-p2949
sudo journalctl -b -p warning..alert --no-pager
sudo cat /persist/ephemeral-root-reset.log
```

After boot one, create an unmistakable disposable `/root-reset-probe` and a
persistent `/persist/root-reset-probe`; check the former disappears and the
latter survives on boots two and three. Check one BEGIN and one RESET for
each distinct boot ID. Validate ordinary work between boots. Keep the parent
default until repeated physical acceptance is recorded in `plan.md`.

## Historical ISO staging and recovery drill procedure

Build the pinned, secret-free ISO with `nix build '.#recovery-iso' --no-link`.
The 2026-10-05 build produced
`/nix/store/f424ql5wbi7h4xl7151696bvx1rr74g7-nixos-minimal-26.05.20261002.774debe-x86_64-linux.iso/iso/nixos-minimal-26.05.20261002.774debe-x86_64-linux.iso`
(1,496,678,400 bytes), SHA-256
`085a7b41e54e4e595f34fcea1ad9d37b48662d7eeae24d0f40781081d86678ca`.
The ISO was added on 2026-10-05 to the existing Ventoy data partition as
`nixos-workstation-recovery-26.05.20261002.774debe-x86_64-linux.iso`, without
replacing any existing images. Copy checksum matched; clean unmount completed
and a subsequent read-only exFAT check reported clean. Post-remount checksum
verification is recorded in `plan.md`. This older filename is retained as staging history. For a new drill use the
current stable ISO identified in the maintenance-window section above. The user's previous
successful recovery with another ISO does not establish this artifact's boot.
Do not write a raw image to a device selected only by an assumed `/dev/sdX` name.

Boot recovery media and first identify the disk by its MP600 model/serial,
partition layout and Btrfs label; device enumeration can differ on recovery
media. Never run Disko, `mkfs`, repartitioning or recursive deletion for this
drill. Mount the verified Btrfs partition with `ro,nologreplay,subvolid=5`, list
subvolumes and read the reset log under `@persist`. Use `ro,nologreplay`
with the corresponding `subvol=@nix`, `subvol=@var`, `subvol=@home` and
`subvol=@persist` options for separate inspection mounts. Btrfs can replay its
tree log even with `ro`; `nologreplay` suppresses that behavior for this drill.
See the [official Btrfs mount-option reference](https://btrfs.readthedocs.io/en/latest/ch-mount-options.html).
First confirm the production partition is not already mounted read-write;
if it is, stop and resolve that mount before the read-only inspection.
Record `findmnt` options for every inspection mount, exact ISO/hash, media,
time, target disk identity and observed topology in the drill receipt.
Keep the receipt on recovery RAM storage during inspection, then export it
to the external backup media rather than writing it to the inspected MP600.
The repository is `@persist/etc/nixos`; profile generations live in
`@nix/var/nix/profiles`. Unmount everything and exit without disk changes.

If the trial fails, select the recorded persistent-root generation. It disables
future resets but cannot restore discarded root-local data. If `@root` is
missing, inspect `@root-next` and the diagnostic log from recovery media;
preserve any unexpected staging and forensic evidence before changing names.
The tested automatic recovery accepts only a genuinely empty staging root.
Do not transplant a forensic snapshot blindly: Btrfs snapshots do not include
nested `tmp`/`srv` subvolumes recursively.

For bootloader repair, mount the verified ESP at `/mnt/boot`, `@root` at `/mnt`,
and all required persistent subvolumes at their normal paths under `/mnt`.
Bind `/mnt/persist/etc/nixos` onto `/mnt/etc/nixos`. Confirm the recorded closure
exists under the mounted Nix store, then use `nixos-enter --root /mnt` from
recovery media and run that closure's `bin/switch-to-configuration boot`.
This writes boot entries without enabling reset live. Validate the exact mounts
and selected closure before this repair; it is not part of the read-only drill.

Recovery-media boot and bootloader repair remain unproven until rehearsed.

## Final generation37 chain accepted — 2026-10-05

Normal0p67xd root300/resetcount6 → persistentph12l3 root300/count6 retained
→ normal0p67xd root302/count7. Persistent-root retained root UUID and both
sentinels. Return-normal changed UUID, removed root-local sentinel, retained
persistent sentinel and matched persisted identity/credentials. Correct mounts,
retained journals, active network/cooling/HomeManager/services, zero failed
units and active Wayland login passed. Private0600 receipts:
final-persistent-boot.json and final-return-normal-boot.json under
/persist/nixos-readiness-20261005. Temporary capture wiring removed.
The earlier pending-leg statements above are superseded by this acceptance.
No additional root-chain rehearsal is required for reassurance. Any firmware
policy change or runtime source change needs its relevant evidence reassessed.
