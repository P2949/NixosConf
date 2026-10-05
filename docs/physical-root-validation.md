# Controlled physical root validation

Status: prepared, hardware validation pending. Do not install or select the
reset entry until the preflight gates below are satisfied. All commands here
are operator commands; documenting them does not mean they have been run.

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

## Recovery drill and failure handling

Build the pinned, secret-free ISO with `nix build '.#recovery-iso' --no-link`.
The 2026-10-05 build produced
`/nix/store/f424ql5wbi7h4xl7151696bvx1rr74g7-nixos-minimal-26.05.20261002.774debe-x86_64-linux.iso/iso/nixos-minimal-26.05.20261002.774debe-x86_64-linux.iso`
(1,496,678,400 bytes), SHA-256
`085a7b41e54e4e595f34fcea1ad9d37b48662d7eeae24d0f40781081d86678ca`.
Copy the ISO onto your verified recovery medium (for example a Ventoy data
partition), then boot it once. The ISO is built, but its physical boot and
read-only recovery drill remain pending. Do not write a raw image to a device
selected only by an assumed `/dev/sdX` name.

Boot recovery media and first identify the disk by its MP600 model/serial,
partition layout and Btrfs label; device enumeration can differ on recovery
media. Never run Disko, `mkfs`, repartitioning or recursive deletion for this
drill. Mount top-level read-only using the verified partition, list subvolumes
and read the reset log under `@persist`. Mount each of `@nix`, `@var`, `@home`
and `@persist` read-only at separate mountpoints to verify expected state.
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
