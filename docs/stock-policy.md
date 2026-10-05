# Stock workstation policy

The evaluated stable-refresh candidate at source commit
`909700b33d7b524a8f517f3d804ab6e294244359` uses the standard NixOS kernel
6.18.55. Kernel parameters contain root/fstab, log level and the configured
LSM list; no mitigation disable, isolated CPUs, tickless CPU isolation or RCU
offload parameters are declared. Firmware and hardware acceptance remain open.

No permanent CPU governor is declared. The current physical generation uses
intel_pstate powersave with balance_performance EPP; retain that default while
collecting representative loaded evidence. GameMode's temporary governor
request is separate and still needs physical acceptance after activation.

IRQ balancing and zram are disabled. The existing disk swap partition remains
configured without an explicit priority. No swappiness, dirty-page, THP or
scheduler tuning pack is declared. Evaluated VM/inotify limits are upstream
NixOS values, not performance experiments. Keep kernel-selected NVMe scheduling
until measurements establish a reason to change it. Representative pressure
and interrupt-distribution comparisons are still required.

The evaluated system and Home Manager environment variable names contain no
CFLAGS, CXXFLAGS, LDFLAGS, NIX_CFLAGS_COMPILE, NIX_LDFLAGS, LD_LIBRARY_PATH,
RADV_PERFTEST or MALLOC_CONF. The optimization module is empty. NIX_LD and
NIX_LD_LIBRARY_PATH are deliberate nix-ld compatibility integration. The editor
process's inherited libdbusmenu path is not a declared system/HM override;
validation children clear their own inherited LD_LIBRARY_PATH where needed.

Private evaluated receipt: /persist/nixos-stock-policy-audit-20261005.json.
Only environment names are recorded, not values. This verifies candidate
declarations; it does not prove final running policy, thermals, absence of
per-application settings or workload performance. Freeze follows acceptance.

## Loaded preparation interval, 2026-10-05

A 55-second sample during the existing Proton game and USB home backup had
about 25 GiB available RAM, 4.5 GiB occupied disk swap, 4,904 pages swapped in,
zero pages swapped out and zero OOM events. Memory PSI some/full avg10 ended
at0.01%; GPU interrupt42945 was on CPU7. These concurrent activities and the
preceding VM tests make this preparation evidence rather than a controlled
idle/load comparison. Do not infer balanced interrupts from aggregate timer
counts or disable disk swap because available RAM is high. No policy was
changed. Representative final-candidate compiler/Unreal workloads still need
pressure and interrupt deltas before the stock policy is frozen.

Private receipt:
`/persist/nixos-readiness-20261005/pressure-game-backup-interval.json`.
