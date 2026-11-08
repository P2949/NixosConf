# Proton compatibility experiments

Steam compatibility tools are managed by `programs.steam.extraCompatPackages`:
CachyOS 11.0-20261015 SLR (generic and v3), GE-Proton 11-12, and
EM 11.0-1-beta1-34-g57d3b63a. Each has a unique internal and visible name.
Select a tool per game in Steam's Compatibility settings. Valve's installed
Proton remains available. Installation does not replace game launch settings,
prefixes, libraries or shader caches.

The desktop's graphics packages use the separate exact `nixpkgs-mesa` input,
Mesa 26.2.6 for both architectures. The system and Home Manager remain on
26.05; other existing inputs and package selections remain unchanged.

```console
proton-lab inventory
proton-lab probe
proton-lab run --fork cachyos --case dxvk --target /path/to/game.exe
proton-lab run --fork cachyos --case dxvk-lowlatency --target /path/to/game.exe
proton-lab run --fork em --case wayland --target /path/to/game.exe
proton-lab report ~/Development/ProtonExperiments/results
```

For standalone probes use `nix build .#proton-fixture64 .#proton-fixture32`.
Their `bin/probe-win64.exe` and `bin/probe-win32.exe` accept `d3d11` (default),
`d3d12` (device creation), `ddraw` (device creation) or `audio` (silent device
open). D3D11 presents 240 colored frames and records CPU-observed Present
durations. These measure this fixture's frame pacing, not game throughput
or input-to-photon latency. The posted character checks the window message
path; it does not validate physical input, IME composition or pointer capture.

Every run uses UMU with the real `steamcompattool` output and a new private
prefix. Results, prefixes, logs and telemetry stay in the existing persistent
`~/Development/ProtonExperiments/results/` directory. `--timeout` bounds the
launch; timeouts are INCONCLUSIVE. A successful launch is distinct from
feature functionality and performance benefit. Reports preserve that distinction.
The launcher removes inherited experiment flags, then applies one named case.
Logs may contain private game/account data; no automatic upload is performed.

`inventory` reads the generated package manifest and `features.json`, including
source versions and exact tool paths. Example Steam options are per-game;
no Wayland, HDR or latency option is enabled globally.

| Area | Cases / interpretation |
| --- | --- |
| Window system | `xwayland`, `wayland`; XWayland is the control |
| HDR | `hdr` uses automatic Wine-Wayland detection; `sdr` disables DXVK HDR on GE/EM. Requires compatible output, protocols and target; do not force HDR on SDR outputs |
| CachyOS audio | `pipewire` default versus `pulse`; observations cannot establish absolute latency |
| CachyOS pacing | `dxvk`/`dxvk-lowlatency`, `vkd3d`/`vkd3d-lowlatency`; isolate APIs and controls |
| CachyOS legacy/injection | `ddraw`, `optiscaler`; need suitable targets |
| FSR4 | `fsr4-cachyos`, `fsr4-ge`, `fsr4-em`; verify actual game/DLL/variant. GE's downloader is opt-in and its requested version may fall back upstream |
| MLFG | `mlfg-em` uses `MLFG_UPGRADE=1`; CachyOS selected-release support remains unverified, so its case cannot run. A frame-generation watermark alone proves nothing |
| GE fullscreen scaling | `fullscreen-fsr`; strength 2, optional per-game `WINE_FULLSCREEN_FSR_CUSTOM_MODE=WIDTHxHEIGHT`; compare with native scaling/Gamescope |
| EM AMD services | `native-ags`; compatible AMD/UE target required |
| Input | EM `input`, `sdl`, `steaminput`; emulation does not implement ISteamInput |
| Wayland diagnostics | EM `ime`, `decorations`, `rawinput`; primary-monitor inventory documents `WAYLANDDRV_PRIMARY_MONITOR` for an actual connected output |
| GE controller | `gamepad-ge`; Sony HIDRAW/XInput fallback requires matching physical hardware and permissions; native Steam Input remains authoritative |
| Media | `media`; codec/launcher behavior requires an applicable target |
| Synchronization | `ntsync`, `ntsync-off`; kernel support must already exist |
| Anti-Lag 2 | Game-dependent; inspect actual driver support and isolate competing latency controls |
| Sarek | Older GPU path; hardware-inapplicable as primary RX 9070 XT path. No async anti-cheat/multiplayer testing |
| ZLUDA/PhysX | Native-only, unavailable in selected SLR tools; no additional ROCm stack |
| NVIDIA | DLSS/NVAPI/CUDA/RTX options are hardware-inapplicable on this AMD workstation |

RDNA4 does not require RDNA3 WMMA or old RDNA2 Vulkan-layer workarounds.
Unavailable games, controllers and compositor protocols are NOT_TESTED or
UNSUPPORTED with reasons, never inferred operational from environment flags.

## EM archive retention and restoration

EM is an upstream Actions snapshot, not a durable release download. Its
archive and checksum originate from [run 36402466585](https://github.com/BananaWorks07/Proton/actions/runs/36402466585),
artifact IDs `10962027195` and `10962101927`, expiring 27 December 2026.
The payload was checked against that workflow's SHA-512 checksum, then pinned
by SHA-256 in `packages/proton/sources.nix`. The source archive and checksum
are retained under `~/Development/ProtonExperiments/sources/` outside Git.
Indirect GC roots in its sibling `gcroots/` protect imported sources.

After store loss, restore the retained archive from that directory or its
normal persistent-home backup, verify the recorded checksum, then import it:

```console
cd ~/Development/ProtonExperiments/sources
sha512sum -c proton-EM-11.0-1-beta1-34-g57d3b63a-x86_64.sha512sum
nix-store --add-fixed sha256 proton-EM-11.0-1-beta1-34-g57d3b63a-x86_64.tar.xz
```

The filename must match `sources.nix`. Recreate the indirect GC root with
`nix-store --realise STORE_PATH --add-root ../gcroots/EM_SOURCE --indirect`.
GC roots do not replace backup of the archive. After artifact expiry, a fresh
workstation needs this retained source; future public downloading is not promised.

## Rollback

Retain the previous bootable system generation when preparing the combined
candidate. Select it in the boot menu if graphics fail. To undo the integration
in source, revert the feature's package registrations and Mesa selection,
validate and build before preparing another generation. Do not delete game
prefixes, reset GPU tuning, change kernel flags or upgrade channels to mask a
failed probe. Private checkpoint records identify the accepted old and candidate
system paths before the single human-initiated reboot.
