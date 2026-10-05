# Independent backup and restore gates

The final baseline requires an independent backup of non-reproducible home
state and a representative restore. Persistent subvolumes, same-disk snapshots,
GC roots and Git tags do not protect against MP600 failure.

The user confirms that `/persist/secrets` was backed up separately and restored
during recovery from an actual system failure. That gate is complete on
user-reported evidence. Keep secrets out of this repository. This does not
establish a current home backup.

## Verified project remote

AI_Gavin_Project is clean at commit
`376e151fca709b084e182da4c76ccb21a228f86d`, verified on remote main.
A fetch into empty LFS storage retrieved all 415 tracked objects, with exact
sizes and SHA-256 matches. A fresh remote clone restored the project descriptor
with its hash matching the local tracked file. Private receipts reside under
`/persist`; repository documentation contains no project content or credentials.

This proves this project's tracked remote data. It does not cover ignored
files, other repositories, editor state, documents or secrets. In particular,
Unreal's `Saved` directory can contain autosaves and must not be dismissed as
reproducible solely because Git ignores it.

## Inventory and destination

The 2026-10-05 allocated-size scan found about 118 GB in Development, of which
117.5 GB is the engine tree, 1.8 GB in `.config` and 14 GB in `.local/share`.
Unreal projects occupy about 545 MB, mostly intermediate build data. These are
`du` accounting figures, not deduplicated backup-size estimates.

A subsequent full top-level home scan covered 31 entries with no failed
directory scans. Non-Development directories allocate about 18.4 GB in total.
The private inventory records symlinks without following them; this is size
and topology evidence, not proof that application state is reproducible or
that every local repository has been audited. Root-only receipt:
`/persist/nixos-home-full-inventory-20261005.json`.

Only the MP600 and Ventoy recovery USB are currently connected. The earlier USB inventory showed
43.2 GB free before adding the pinned recovery ISO. The user subsequently chose
an additive compressed backup folder on Ventoy, with audited exclusions and a
4 GiB free-space reserve enforced by the runner.
Do not erase or repurpose the recovery medium to make room.

Before excluding large trees, distinguish downloadable installations and
rebuildable caches from unique project assets, local changes and autosaves.
Inventory paths and repository details remain in root-only receipts rather
than the public configuration repository.

## Completion evidence still required

- A destination outside the MP600, with enough capacity for the chosen data.
- Critical data selection that covers local/untracked/ignored work and useful
  application state, with exclusions justified rather than assumed.
- Encrypted secrets backup and restore: completed by user-confirmed recovery.
- Backup date, destination, successful operation and integrity verification.
- Representative restore from that backup into a separate directory, followed
  by content/hash comparison; preserve the original working data.

A representative Git restore has passed. The broader home backup/restore gate
remains open until the actual independent backup is available and verified.

## Source-work scan scope

A follow-up metadata scan of visible home/project trees found one clean Git
repository and 476 files matching source/document/project extensions. Two
Blender files outside the discovered repository total 313,363 bytes; include
them in critical-data selection. The scan had no traversal or Git-status
errors. Paths and status details remain root-private in
/persist/nixos-home-work-audit-20261005.json.

Engine installations, generated build trees and application/cache directories
were excluded from this source-work scan to avoid treating installed software
as user work. These are scan exclusions, not approved backup exclusions. File
extensions do not cover all unique data; application state, ignored work and
autosaves still need backup coverage. No files were deleted or transferred to
an independent destination by this audit.


## Current Ventoy backup operation — 2026-10-05

The user explicitly selected a dedicated folder on existing Ventoy, overriding
the older destination recommendation above. No existing boot files were erased
and no partition was formatted. A fresh read-only home snapshot supplies a
consistent filesystem view, without claiming quiesced application databases.

The main compressed archive includes home, projects, engine source and assets.
Capacity exclusions are the engine installation ZIP and engine binary/generated
intermediate/cache directories. A read-only audit found all26,000 compared
binaries equal in size/CRC to the retained ZIP;47 extra/different files were
backed up separately and all47 restored/hash-verified. This compares with the
local distribution, not a vendor authenticity signature.

The main home archive integrity and representative external restore are still
pending. `/persist/secrets` is outside its scope; the separate
[bootstrap restore](bootstrap-secrets.md) is already user-confirmed. Preserve snapshots and
receipts; only a terminal verified receipt closes the corresponding gate.

## Independent Ventoy home backup accepted — 2026-10-05

- [x] Main archive: 27,844,003,241 bytes.
- [x] Zstd integrity passed; SHA-256
  `9ec746a927b42c48484cb877d1d1916ca54f084f5ecdeffd3babc2f5ed1db212`.
- [x] Two Blender files and one actual Unreal project descriptor restored to
  a separate root-private directory; all three source/restored hashes match.
- [x] Earlier47-file engine supplement remains separately verified.
- [x] Backup runner session50539 exited0, terminal receipt completed
  2026-10-05T17:58:06Z. Ventoy cleanly unmounted17:58:09Z; findmnt confirms absent.

USB folder: NixosConf-backups/2026-10-05; media UUID1BF6-1635. No formatting,
partition change or existing ISO deletion. About12GiB free before unmount,
above enforced4GiB reserve. Source is read-only home-ventoy-20261005 snapshot;
application quiescence was not claimed. Engine ZIP and audited binaries/cache
exclusions remain documented, with unique binary additions supplemented.
Secrets backup is separate and user-confirmed from actual recovery.
Private receipts, restored samples, scripts and logs are retained under
/persist/nixos-ventoy-backup-20261005. This is point-in-time backup evidence;
new work after snapshot creation requires a later backup before final freeze.

Queued reconstruction session11114 started only after verified receipt and
clean unmount, source736b0fb. Nix PID1186208 is actively building. This closes
home archive/integrity/representative restore/unmount gates; it does not close
reconstruction, physical hardware/workload acceptance or multi-day soak.
