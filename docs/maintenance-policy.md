# Workstation maintenance policy

The workstation declares one weekly Nix collector, Saturday at 04:00
local time, with `--delete-older-than 30d`. This removes old profile generations
before collecting unreachable outputs. It is not combined with count-based
pruning. The boot menu exposes at most 20 generations independently of the
30-day profile horizon. Missed GC runs do not catch up at boot.

Monthly scrub runs on day 1 at 02:00 with one-minute timer accuracy. GC is
ordered after scrub when both jobs are queued, and each skips if the peer is
active. GC also requires a finished clean scrub report. Missing status, unknown
health and reported corruption skip GC. A skipped scrub must be rerun during
an idle window; it is not evidence that scrubbing completed. Manual maintenance
must follow the same no-overlap rule. Systemd's ExecCondition exit 1 skips a
unit without marking it failed, as specified by the [v260 service contract](https://raw.githubusercontent.com/systemd/systemd/v260/man/systemd.service.xml).

Before performance work, stop the maintenance timers and ensure no job remains:

```bash
sudo systemctl stop nix-gc.timer btrfs-scrub--.timer fstrim.timer
systemctl list-jobs
systemctl list-timers --all
```

Restart them after the controlled measurement window. Do not interrupt an
active scrub or collection merely to start a benchmark.

## Recovery artifacts and GC-root review

Git tags do not keep Nix store paths alive. Dedicated roots under
`/nix/var/nix/gcroots/stock-baseline` retain the accepted normal,
persistent-root and recovery ISO artifacts. The 2026-10-10 inventory and
read-only dead-output preview are retained privately in
`/persist/post-baseline-cleanup-20261010`.

The supported ISO and final baseline closures are KEEP. Preparation roots for
older generations, superseded candidates/ISOs and temporary VM builds were
retirement candidates. Fourteen exact superseded preparation symlinks were
retired after accepted-artifact protection was verified. Their targets are
recorded in `retired-preparation-roots.json` for restoration. The accepted ISO
root was retained. The post-retirement preview found 619 unreachable paths. No store outputs or profile generations were
deleted. Repeat the preview before any later collection; the count is historical.
Forensic Btrfs roots and the minimal recovery exception archive are separate
from GC-root cleanup and remain retained.

## Runtime diagnostics

Journal storage is deliberately volatile under `/run/log/journal`. Runtime
size and keep-free limits use systemd defaults; no explicit RuntimeMaxUse or
RuntimeKeepFree tuning is introduced. The existing `MaxRetentionSec=90day`
remains an upper time bound within a boot, subject to runtime size limits;
it does not promise retention across reboots. Removed SystemMaxUse/SystemKeepFree
settings applied to persistent journal storage and did not cap this volatile
journal. Historical disk journals remain separate retained evidence.

This is a separate maintenance-policy change from the closure-identical cleanup.
Its system output differs from the immutable baseline because generated
journald configuration changes. It is an intentional working-stock change, not a replacement qualification
baseline. Installation is a separate host action.

Existing external core files total 213 MiB. Core processing retains a 32 GiB
limit, external files have an 8 GiB limit, with a 4 GiB total-use target and
4 GiB keep-free. Upstream two-week tmpfiles retention is retained. The total-use
target is not an instantaneous quota: a single new large dump can exceed it.
Larger processes can still provide journal metadata/backtraces subject to the
processing limit, while oversized external files are omitted. Reproduce under
a controlled debugger when a full larger core is necessary. Core contents are
private process memory and must not be committed to Git.

The baseline maintenance configuration is preserved by the immutable tag. One-time store
optimisation and content verification remain separate idle-period tasks.

Pressure-triggered `min-free` / `max-free` GC is deferred: 763 GiB free of
896 GiB was observed, while future large-build/workload demand is unmeasured.
Arbitrary thresholds would introduce collection outside the guarded window.
Revisit with measured space requirements before large optimization builds.
