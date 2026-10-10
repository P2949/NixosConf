# Minimal backup and recovery policy — current as of 2026-10-10

The user explicitly narrowed the recovery scope: projects are restored from GitHub,
applications are reinstalled, and Unity, Unreal, Blender, Steam, Firefox and other
application/system state do not require local archives. This replaces the earlier
whole-home and additive-delta backup requirements. A larger drive is **not required**.

The separate secrets backup was already restored successfully during an actual
system failure and remains accepted on user-reported evidence. Do not duplicate
secrets onto Ventoy or publish their contents.

Ventoy retains the verified NixOS recovery ISO, checksum, successful physical
inspection receipt/script and a short restore guide. The October 5 home archive,
engine supplement and October 10 failed partial were deliberately removed with
user authorization, along with failed drill receipts and the obsolete script copy.
The 10.33 GB local staged archive was also removed. Other existing OS ISOs were
left intact. Approximately 38 GiB is now free on Ventoy.

No whole-home/application archive is a release gate under this user-selected
scope. The targeted minimal recovery-source audit now identifies three local
authored exceptions: Blender changes/recovery copy and a Unity settings change.
These are protected in a 260,598-byte exceptions-only archive on Ventoy. Zstd
integrity, extraction of all three files, source/restored hash comparisons and
external-copy hashes passed; Ventoy was synced and cleanly unmounted.
Archive SHA-256:
`b4fea7ae78e2083198ce3847f8ab00a15567ad43a3a4304ada481d265a8232cf`.
Private recovery-source manifest SHA-256:
`ebc0990e3ebe8052983bcd672c484b736e64a71929c49838612022f1b116144b`.
Relevant project repositories have no local commits ahead of their upstream;
working-tree exceptions are covered separately. The extra Unity directory
contains only disposable Logs/Temp. Application/game state remains deliberately
excluded under the user's policy; Steam Cloud coverage is not independently
claimed. The separate secrets restore remains accepted on user evidence.

This is a scope decision, not a claim that removed
archives remain available or that local uncommitted files are remotely backed up.
The earlier verified project clone/LFS restore and physical recovery evidence
remain valid. Final runtime soak and baseline release gates remain separate.

## Historical evidence — superseded backup scope

The following describes earlier operations and is retained for chronology only.
Its archive-preservation, whole-home and delta-freshness requirements no longer apply.

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

### October 10 freshness attempt

The full additive delta runner stopped at the required 4 GiB reserve, leaving
an incomplete 8,113,283,072-byte USB archive. It did not replace the accepted
October 5 archive or recovery ISO. Backup freshness remains **pending**.

A content comparison against the retained October 5 source found 519 identical
files (307,689,596 logical bytes), with zero errors. That reduction alone does
not resolve capacity. The complete original selection was staged privately on
the MP600 with zstd level 10, without omitting selected state. The result is
10,331,350,085 bytes, exceeding Ventoy's approximately 8.1 GB usable budget
after retaining the required reserve. It passed zstd integrity and separate
representative project/application extraction and source-hash comparisons.
Its SHA-256 is
`c353f798c5a3a1a9232052cda62b431d8d485a9a657905a9bb979410f649a297`.
Same-disk staging is not an independent backup: external transfer and
verification remain pending. Ventoy was synced and cleanly unmounted; its
failed partial and prior accepted recovery set remain intact. Private receipts
and failure evidence are retained under the October 10 readiness directory.

Before excluding large trees, distinguish downloadable installations and
rebuildable caches from unique project assets, local changes and autosaves.
Inventory paths and repository details remain in root-only receipts rather
than the public configuration repository.

## Backup acceptance criteria

- A destination outside the MP600, with enough capacity for the chosen data.
- Critical data selection that covers local/untracked/ignored work and useful
  application state, with exclusions justified rather than assumed.
- Encrypted secrets backup and restore: completed by user-confirmed recovery.
- Backup date, destination, successful operation and integrity verification.
- Representative restore from that backup into a separate directory, followed
  by content/hash comparison; preserve the original working data.

The Git restore and independent Ventoy home archive/integrity/representative
restore gates have passed. See the terminal evidence below. At final freeze,
check meaningful changes since the snapshot and back up new work as needed.

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

The main home archive integrity and representative external restore have
passed; terminal receipt and clean unmount are recorded below. `/persist/secrets` is outside its scope; the separate
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

Reconstruction was subsequently completed and accepted; see
[reconstruction evidence](reconstruction.md). The backup receipt closes its
home archive/integrity/representative restore/unmount gates, independently
of hardware/workload acceptance and multi-day soak. No backup or
reconstruction process is claimed to be running from this historical record.
