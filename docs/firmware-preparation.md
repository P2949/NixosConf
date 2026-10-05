# Firmware preparation

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

No packages have been flashed or upgrade decision finalized. Capture all
OC/RAM/power/virtualization settings before any flash; use the board-specific
vendor procedure and verify ME/BIOS afterwards. Firmware virtualization is
currently disabled, preventing physical KVM acceptance. Resolve firmware and
settings in the batched maintenance window before final stock acceptance and
freeze; then repeat required hardware/workload stability tests.
