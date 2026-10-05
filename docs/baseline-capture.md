# Capturing workstation state

From the repository root:

```bash
nix develop .#validation --command bash scripts/nixos-baseline-info.sh > snapshot.md
```

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
not prove 32-bit Vulkan works. ME firmware identification, practical 32-bit
graphics testing, sustained thermals and workload acceptance remain separate
gates. This is a preparation snapshot until the final candidate is booted and
accepted; the final baseline manifest must be captured again then.
