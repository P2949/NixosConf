# Physical activation prerequisites

The desktop supplies named `system.preSwitchChecks` for persistence, credentials,
ESP capacity and Btrfs topology. These inspect current host state before the
native switch-to-configuration action. They do not require any optional USB,
audio, display, network or graphical-session device.

The ESP reserve is 256 MiB. At implementation, the largest installed initrd was
45,631,321 bytes and available ESP space was 3,948,449,792 bytes. The reserve
allows two additional kernel/initrd pairs plus overhead; remeasure if artifacts
grow substantially. This guards available space, not bootloader write atomicity.

Topology inspection mounts subvolume ID 5 read-only temporarily. It refuses
wrong root/persist mounts, unknown root descendants, nested disposable children
and nonempty or invalid staging. It never deletes or renames subvolumes.
Password checks inspect metadata only; no contents enter logs or the repository.

A failure requires correcting the named prerequisite. Retain the physically
accepted generation and recovery ISO: the ISO excludes this host module and can
inspect/repair mounts independently. Do not bypass a refusal to force a normal
activation. The checks are not proof that subsequent firmware or boot succeeds.

Positive/negative fixtures and native action tests must pass before installing
this candidate. No live activation is implied by introducing these guards.

Ownership: `modules/workstation/activation-safety`, configured through
`workstation.activationSafety`. Tests live under
`tests/workstation/activation-safety`. Composition assertions require the
ephemeral-root contract and Btrfs root, concrete vfat ESP and selected user
password-hash path. Recovery deliberately disables reset while retaining guards.
