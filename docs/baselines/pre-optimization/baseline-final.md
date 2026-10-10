# Immutable stock workstation baseline

Captured 2026-10-10. Runtime freeze **F**:
`9df40f6a06229a4c5263f957787fe802ff5ce198`, tree
`df1527cd14c6509515ba398bb8dba0c46673e534`.
The later documentation release **E** is bound by PR #7 metadata and the
annotated baseline tag; this document does not certify its own future CI.

## Reproducible identities

- flake.lock SHA-256: `7efb19569e8a022768cd570498ff8b93cb98b108358149b668a658e2d9f406a2`.
- nixpkgs revision: `0d9e9b832d03ac387417e16ce1febf73b2e631e1`.
- Normal closure: `/nix/store/15f6c5dsjl047j7my4c7cpkdhk6ly2xp-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Persistent-root closure: `/nix/store/7lkx40kh36s809bz1yr9bmfdddy1n80a-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Recovery output: `/nix/store/d55ny1z4d53slhz3ilvyy2mg6d8khrqn-nixos-minimal-26.05.20261004.0d9e9b8-x86_64-linux.iso`.
- ISO SHA-256: `52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
- Nix 2.34.8; NixOS 26.05.20261004.0d9e9b8; kernel 6.18.55.

Both system outputs equal the physically accepted generation-46 pair. The
normal output equals the running system and closure comparison is empty. The
recovery ISO equals the physically tested artifact; no repeated boot is needed.

## Productive policy and storage

Intel Core i5-10600K, six cores/twelve threads; BIOS 3201/current ME retained.
Firmware/microcode evidence is retained in the firmware baseline and private
collector. CPU PL1/PL2 are 125 W, reapplied after boot/resume. Commander Core
uses the accepted coolant-responsive pump/fan service; no new cooling policy
was introduced. Display policy retains 155 Hz, 10-bit and VRR, with accepted
HDR engagement and SDR return. Stage Pro USB audio is accepted after boot and
resume. Bluetooth is disabled by user request.

`@root` contains ephemeral `/`, `/home` and ordinary `/var`. Explicit NixOS and
Home Manager declarations bind retained state through `@persist`; disposable
cache overlays remain reconstructible. Persistent mounts are `@nix` at `/nix`,
`@persist` at `/persist`, `@snapshots` at `/.snapshots`, `@optimization` at
`/var/lib/nixos-optimization`, and the ESP at `/boot`. Legacy `@home`/`@var` and
selected migration snapshots were deliberately retired. Root reset and the
persistent-root specialization preserve the accepted granular contract.

Granular source `96678c3a974755ca285c734999c70acfc0bfd254` passed exact CI
`38002362044` and was merged through PR #8 at
`c981a6ffd9b484c53adf0a374f6915c772d12a83`, with identical trees. Corrected
physical chains and post-pruning normal boot remain accepted.

## Accepted physical and workload evidence

CPU verification at 125 W (user-selected 15 minutes), complete 20 GiB memory
verification, KVM, Btrfs scrub, NVMe health and store verification passed.
Blender HIP and interactive work, Unreal rebuild/PIE/interactive work, native
Stardew and Proton/Dark Souls with GameMode restoration are accepted. HDR/SDR
and audible Stage Pro observations were user-confirmed. Root chains,
suspend/resume and reconstruction evidence remain bound to unchanged outputs.
See development-validation.md, physical-root-validation.md and reconstruction.md.

Exact physical recovery receipt `receipt-20261008T000047Z.txt`, SHA-256
`61177a8ed57e0e67a7b1c87ded9bae0870c408832e61242147c33296403f45b6`, proves ISO
identity, read-only topology inspection and clean return. Bootloader repair is
not claimed or required as an additional drill.

The additional final-runtime three-day soak is **DISREGARDED BY HUMAN
INTERVENTION** on 2026-10-10. It is not a measured soak PASS. The user reports
that the operational system works well; earlier normal-use stability and
accepted runtime/health observations remain evidence.

## Minimal recovery coverage

Nix/GitHub restore configuration and projects; applications are reinstalled.
Application profiles, installations, caches and game libraries are deliberately
excluded under the user's policy. No unverified Steam Cloud guarantee is made.
Separate secrets backup/restoration is accepted from user-reported actual
system recovery. Targeted project audit found no unpushed commits after remote
fetches; three Blender/Unity local changes are protected independently.

Exception archive: 260,598 bytes, SHA-256
`b4fea7ae78e2083198ce3847f8ab00a15567ad43a3a4304ada481d265a8232cf`.
Recovery-source manifest SHA-256:
`ebc0990e3ebe8052983bcd672c484b736e64a71929c49838612022f1b116144b`.
External copy, zstd integrity, extraction/hash comparison for all three files,
manifest copy/hash, sync and clean USB unmount passed. Oversized archives were
retired by explicit user instruction; historical receipts remain. This proves
the audited exception set, not arbitrary future local work or whole-home backup.

## Exact frozen validation

Private collector captured 57 sections, all command exits zero. Raw machine
identifiers remain private. The corrected topology collector uses containing
filesystem resolution; accepted ELF32 Vulkan rendering is recorded separately.
Formatting, diff-check and flake checks passed on F. Positive heavy outputs
resolved successfully: blank-disk reconstruction, activation actions,
workstation smoke, reset control, root safety, interrupted recovery, persistent
identity and persistent fallback. Identical successful cached outputs were
reused where applicable. The contamination-negative fixture failed specifically
on its forbidden `nixos-opt-pgo-fixture`, as required.

Stock control is clean: optimization/default.nix is inert; the productive
closure has no CPU/LTO/PGO/BOLT experiment namespaces, no global experimental
compiler/linker flags or allocator preload. Package-local Unity runtime library
routing and the ordinary inherited libdbusmenu path are not system-wide
optimization policy. No productive runtime change occurred after F.

Exact release-head CI, tested/main tree equality and the annotated
`nixos-26.05-pre-optimization-baseline` tag are bound in PR #7/tag metadata.
Readiness ends at that tag; optimization and ordinary features remain separate.
