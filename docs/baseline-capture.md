# Capturing workstation state

From the repository root:

```bash
nix develop .#validation --command bash scripts/nixos-baseline-info.sh > snapshot.md
```

The collector is a broad human-readable snapshot of observed workstation state
for diagnosis, before/after comparisons and manual audits. It does not establish
qualification or benchmark validity. Historical qualification is recorded in the
[immutable baseline](baselines/pre-optimization/baseline-final.md). Optimization
experiments require a separate authoritative machine-readable runtime/provenance
manifest; this report remains a broader diagnostic snapshot.

The collector reads runtime state and records each command's exit status.
Commands time out after 45 seconds, followed by a five-second termination
grace period. Privileged storage inspection uses `sudo -n`, so unavailable
privileges become missing evidence without an interactive password prompt.
It clears the editor's inherited `LD_LIBRARY_PATH` in its own process.

The report records Git/lock and running closure identities separately: an
edited repository may describe a candidate that has not been booted. It
includes CPU, firmware, memory, graphics, storage, services, timers, cooling
and persistence observations. It does not read secrets or copy the private
reset log, only its metadata and completion counts.

Review failed commands before relying on the report. An observed temperature
is not proof of idle/load thermal acceptance. The 64-bit Vulkan summary does
not prove 32-bit Vulkan works. ME component versions are read from the kernel
sysfs interface. These observations do not replace physical acceptance evidence.

The collector also records pressure-stall counters, VM counters, per-CPU
interrupt totals and effective IRQ affinity, IRQ-balancer service state, NVMe
schedulers, zswap and THP defrag. Capture before and after representative
loads to compare deltas; a single snapshot does not prove balanced interrupts
or sufficient memory headroom. These reads change no tuning or service state.
