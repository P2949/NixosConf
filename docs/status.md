# Current readiness status

The finished granular persistence policy runs as generation **46 normal**.
[The granular plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
and [plan.md](../plan.md) retain chronology and superseded observations.
This page describes the current contract and separates accepted storage work
from the remaining repository-release and stock-readiness gates.

## Running system and topology

Last accepted boot: `5278eaa9-875c-48d0-8c2c-a5b021b251f2`, root **344**, UUID
`9dda6d9e-c291-4047-adad-12a998122e7b`, reset count **26**. Root identity changes
on each normal boot. The observed system has no failed services and full
NetworkManager connectivity.

| Path | Current policy |
| --- | --- |
| `/`, `/etc`, `/root`, `/srv`, `/tmp`, ordinary `/usr` state | Reset-root storage; configuration reconstructed |
| `/home`, ordinary `/var` | Root-local; only explicit state survives normal boot |
| `/nix`, `/persist`, `/.snapshots`, `/boot` | Deliberately persistent |
| `/var/lib/nixos-optimization` | Separate persistent `@optimization`; experiments inactive |
| `/run`, `/dev`, `/proc`, `/sys` | Runtime or virtual filesystems |

Legacy `@home` and `@var`, including their three nested children, are deleted.
The four granular-migration snapshots are also deleted after explicit final
confirmation. Unrelated forensic roots and earlier readiness backup staging
remain under documented recovery purposes. `/persist` contains declared backing,
empty cache mountpoint scaffolds and explicitly justified evidence/backup state;
its raw re-audit found no undeclared home residue or hidden cache data.

## Accepted persistence and physical evidence

The [contract](persistence-contract.md) and [state audit](ephemeral-state-audit.md)
define retained user/system state and exact generated-state exceptions.
`.config`, `.local`, `.cache`, `/home` and `/var` are not whole-container
persistence mechanisms. Fuzzel history and Unity editor preferences persist.
User-selected Steam shaders, Unreal DDC/Zen and current Unity project Libraries
remain persistent; other audited caches, logs and temporary files reset.

Home's recovery → recovery → normal → normal sequence, final generation-45
normal → recovery → recovery → normal, corrected generation-46 equivalent,
and one post-pruning normal boot all pass. Each final physical trial verifies
**100** requirements: **92** disposable and **eight** persistent proofs.
Both corrected recovery trials retain root340/reset count24; normal return
replaces it with342/count25; post-pruning normal replaces342 with344/count26.
All nine prepared Unity preference hashes survive, and the user confirms the UI.

Private evidence under `/persist/granular-migration` includes:

- `post-pruning-normal-review.json`: accepted physical receipt, root/identity,
  topology, services/network and Unity hashes.
- `scoped-backing-prune-20261009.json`: 55 audited residue nodes removed and
  82 hidden backing caches emptied while active cache identities remain intact.
- `legacy-home-retirement-ready.json`: 608,511 old selected paths examined;
  85,721 old-only paths classified into16 cases, no unknown required state.
- `legacy-database-generation-review.json`:18 obsolete IndexedDB blobs are
  unreferenced; current references and private-copy integrity checks pass.
- `legacy-subvolume-retirement.json`: home256 and individually inspected
  var children263/264/266, then parent261, deleted deliberately.
- `migration-snapshot-retirement.json`: only snapshots326/327/328/329 deleted
  after explicit confirmation; unrelated subvolumes unchanged.
- `post-legacy-retirement-topology-review.json`: active topology, both exact
  generation46 ESP pairs and retained recovery ISO identity verified.

Important browser, Codex, VS Code, Git/GitHub, Steam saves/library and
Unity/Unreal workflows are user-confirmed. Fuzzel ordering and actual Unreal
Zen startup are corrected and accepted. Blender configuration/render/editing
also has retained evidence. Android Studio is uninstalled: its future SDK/AVD
state needs an actual installation audit. Existing ADB keys remain retained.
Plastic's empty directory is reserved for future use; no current remote Plastic
workflow is claimed. Credential/data categories and unexercisable cases are
explicitly separated in the plan checklist.

## Source validation and release

The accepted implementation comes from immutable source
`ca08qvh8cry5msxny61hfizgaiw54y02`. Its checks and normal/recovery builds pass;
fresh granular six-boot, reconstruction and workstation VMs pass, with five
unchanged root-scenario identities retained. These are local/physical evidence.
The final documentation checkpoint must receive its own exact-head complete
local suite and GitHub CI; historical runs do not certify a later commit.

Integration is layered: granular changes enter `feat/pre-optimization-readiness`
through a separate PR, then [PR #7](https://github.com/P2949/NixosConf/pull/7)
feeds `main`. PR #7 belongs to the readiness branch; its earlier CI is not
CI for `feat/granular-impermanence`. Updating PR #7's head requires new exact-head
CI. Frozen source, lockfile, closures, topology and private evidence identities
belong in the final manifest; CI/integration/tag identities belong in PR/tag
metadata after they exist. A source document cannot certify its own future CI.

## Supported recovery and backup

Supported rollback is the accepted generation46 pair:
normal `15f6c5dsjl047j7my4c7cpkdhk6ly2xp`, persistent-root
`7lkx40kh36s809bz1yr9bmfdddy1n80a`. Both are independently GC-rooted and have
verified ESP kernel/initrd copies. Old generations requiring `@home` or `@var`
are intentionally obsolete. `persistent-root` retains the current reset root;
it does not restore data already discarded by a previous normal boot.

The GC-rooted recovery ISO is `d55ny1z4d53slhz3ilvyy2mg6d8khrqn`, rechecked SHA256
`52e3496c74f135641c8f39132b058c4e0971063ead8a143ec406b359647d8061`.
The prior external recovery drill and independent Ventoy archive/restore are
accepted; their small receipts remain. External media is not currently mounted.
[Backup details](backup-restore.md) records the27,844,003,241-byte archive,
SHA256 `9ec746a927b42c48484cb877d1d1916ca54f084f5ecdeffd3babc2f5ed1db212`
and47-file engine supplement. Prior backup acceptance does not prove freshness
of work created since then.

## Separate pre-optimization readiness

Stock individual boot/resume, CPU/memory, Blender HIP, Unreal project/PIE,
native/Proton gameplay, USB audio, HDR/SDR and external recovery gates have
accepted evidence in [development validation](development-validation.md),
[physical root validation](physical-root-validation.md), [reconstruction](reconstruction.md)
and the readiness ledger. Their accepted human-observation gates need not be
repeated without a relevant defect or configuration change.

Representative multi-day mixed-use soak began2026-10-08. Its completion,
backup freshness, stock baseline capture and final readiness merge/tag remain
separate gates; storage acceptance does not silently close them. Compiler/LTO/
PGO/BOLT optimization, Prism and ordinary feature additions remain deferred.
No extra reboot or synthetic stress is requested for retirement or final docs.
Keep the active graphical session intact.
