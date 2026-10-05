# Workstation maintenance policy

The preparation branch declares one weekly Nix collector, Saturday at 04:00
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

## Recovery artifacts and first cleanup

Ten explicit GC roots under `/nix/var/nix/gcroots/workstation-preparation`
protect known persistent generation 31, parent/reset generation 33, prepared
root-policy and workstation closures, the newer maintenance/GameMode/stable-refresh candidates, and both pinned
recovery ISOs. Their
private receipt is `/persist/nixos-preparation-gcroots.json`. Git tags do not
keep built store paths alive. These temporary roots require a deliberate
retirement review after the final baseline/recovery milestone.

The first preview is `/persist/nixos-gc-preview-20261005.txt`: 2235 dead paths,
with the original six protected targets excluded; the later candidate roots
were added after that preview. No store outputs or profile generations
were deleted. Nix did remove obsolete automatic/temp-root bookkeeping during
root discovery. Repeat the preview before the first real cleanup if the store
or generation set has changed. No cleanup or timer activation was performed
when preparing this policy.

## Persistent diagnostics

Observed combined journal usage is 103 MiB. The declaration limits the active
persistent journal to 2 GiB, reserves 4 GiB free space and applies a 90-day time
horizon. Size limits can shorten that horizon. Older machine-ID directories
remain separate historical evidence; do not infer their removal from the new
active journal cap.

Existing external core files total 213 MiB. Core processing retains a 32 GiB
limit, external files have an 8 GiB limit, with a 4 GiB total-use target and
4 GiB keep-free. Upstream two-week tmpfiles retention is retained. The total-use
target is not an instantaneous quota: a single new large dump can exceed it.
Larger processes can still provide journal metadata/backtraces subject to the
processing limit, while oversized external files are omitted. Reproduce under
a controlled debugger when a full larger core is necessary. Core contents are
private process memory and must not be committed to Git.

The source policy is pending installation/physical acceptance. One-time store
optimisation and content verification remain separate idle-period tasks.

Pressure-triggered `min-free` / `max-free` GC is deferred: 763 GiB free of
896 GiB was observed, while future large-build/workload demand is unmeasured.
Arbitrary thresholds would introduce collection outside the guarded window.
Revisit with measured space requirements before large optimization builds.
