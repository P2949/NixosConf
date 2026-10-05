# Firmware preparation

> Current update, 2026-10-05 after the user reboot: VMX enabled in photos,
> /dev/kvm accessible, QEMU KVM initialization PASS (guest paused).
> Earlier VMX-disabled observations below are historical. Actual Android
> emulator acceptance remains open. See [firmware observation](baselines/pre-optimization/firmware-20261005.md)
> for the captured AI Optimized50/49, MCE/XMP policy and remaining unknowns.


Observed motherboard: ASUS ROG STRIX Z490-E GAMING, revision 1.xx.
BIOS reports 3201 with embedded date 2024-11-20. The vendor publication date
can differ from this embedded date; do not treat them as interchangeable.

On 2026-10-05, read-only `/sys/class/mei/mei0/fw_ver` returned:

```text
0:14.1.53.1649
0:14.1.53.1649
0:14.0.51.1528
```

The [kernel ABI](https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-mei)
allows up to three component-version blocks. Preserve them all; do not assume
that repeated blocks are a parsing error or infer unspecified component roles.

[ASUS support](https://www.asus.com/supportonly/rog%20strix%20z490-e%20gaming/helpdesk_bios/)
lists BIOS 3402 dated 2026-08-05, with security/microcode updates and a
requirement to update ME to 14.1.79.2540 before the BIOS. The current readings
do not establish that prerequisite. ASUS lists MEUpdateTool
14.1.79.2540v5 dated 2026-09-01. Published package SHA-256 values:

- BIOS: `9928bf5a987ff0a44f2efa7bd131186d68a7d1eaeb5198f43ad8333897bc5cf9`
- ME tool: `75c5efe983cfb0c4c9e75830b3e1d1287e0e6adcf93d97194acbaaac15746bfe`

On 2026-10-05 the user selected retaining BIOS 3201/current ME. No firmware
update is planned; the newer packages above remain historical reference only.
Capture OC/RAM/power/virtualization settings for the retained baseline.
Firmware virtualization is currently disabled, preventing physical KVM
acceptance. Enable VMX in a batched maintenance window before final stock
acceptance and freeze, then complete hardware/workload stability validation.
No firmware packages have been flashed.

## Retained-baseline settings capture

Before changing VMX, record these firmware values for the retained BIOS/ME:

- CPU multiplier, cache multiplier, core voltage mode/value, LLC and AVX offset.
- PL1, PL2 and Tau.
- RAM frequency, primary timings, voltage and XMP/manual policy.
- VMX, Speed Shift/HWP and C-states policy.
- ReBAR and Above 4G decoding.

Runtime frequency or a benchmark cannot establish every firmware setting.
Values unavailable through a reliable read-only interface remain unknown until
the batched firmware window; do not invent them from the intended OC settings.
Record before/after values and whether any setting other than VMX changed.
Changes to CPU/RAM policy require stability validation of that final policy.
No flash, automatic defaults reset, voltage change or tuning is part of this
retained-firmware preparation. Enable VMX during the single coordinated window
after offline acceptance, then verify /dev/kvm on the subsequent normal boot.
