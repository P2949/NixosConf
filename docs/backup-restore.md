# Backup and recovery

## Recovery model

- NixOS/Home Manager configuration and projects: GitHub.
- Applications, installations and caches: reinstall or rebuild.
- Secrets: separate backup already restored during actual recovery, accepted on user evidence.
- Unique local work: targeted exception archive; do not assume uncommitted work is on GitHub.

Application profiles and game libraries are deliberately excluded under the
user's recovery policy. No generic Steam Cloud guarantee is claimed.

## Recovery ISO

Ventoy retains the supported NixOS recovery ISO, SHA-256
`52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
The exact physical recovery drill passed; see the [canonical baseline](baselines/pre-optimization/baseline-final.md).
Reconstruct using [the reconstruction procedure](reconstruction.md), then restore
credentials following [bootstrap-secrets.md](bootstrap-secrets.md).

## Unique local exceptions

Ventoy folder `NixosConf-backups/minimal-20261010` contains the recovery-source
manifest and three-file Blender/Unity exception archive (260,598 bytes).
Archive SHA-256: `b4fea7ae78e2083198ce3847f8ab00a15567ad43a3a4304ada481d265a8232cf`.
Manifest SHA-256: `ebc0990e3ebe8052983bcd672c484b736e64a71929c49838612022f1b116144b`.
Integrity, extraction of all exceptions, source/restored hashes and independent
copy hashes passed; the USB was synced and unmounted.

Before restoring, inspect the manifest. Extract into a separate directory,
review the results and copy only intended files to their project locations.
The archive uses paths relative to `/`; never extract it directly over the
running system. For new unique work, update only the relevant exception set,
verify integrity and representative restore, then sync and unmount the medium.

## Historical evidence

The baseline tag preserves the superseded large-backup attempts and receipts.
Those archives were deliberately retired; they are not current recovery media.
See [history](history/README.md). No full-home or full-persist archive is required.
