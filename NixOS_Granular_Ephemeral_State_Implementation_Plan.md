# Granular Ephemeral NixOS Implementation Plan

**Repository:** `P2949/NixosConf`  
**Starting branch reviewed:** `feat/pre-optimization-readiness`  
**Starting reviewed commit:** `de058b4b65416249e2a1ac2e722f7514c87d5a36`  
**Primary objective:** make the workstation ephemeral by default across root, home, and system mutable state, while preserving only explicitly declared state that has a demonstrated reason to survive reboot.

## Implementation status — 2026-10-09

This is the active implementation record. The numbered procedure below remains
the acceptance specification; unchecked physical gates must not be inferred
from source changes or VM tests.

- Fully read all 2,393 original lines, including the migration ordering and
  retirement gates. No repository `AGENTS.md` applies.
- Started `feat/granular-impermanence` at the exact reviewed commit above.
  Tracked files were clean; this user-supplied plan was the sole untracked file
  and is preserved and updated as part of this work.
- Initial topology: `/home` used `@home`, `/var` used `@var`, `/persist`
  used `@persist`. Current home is root-local; legacy var remains. The
  optimization mount stays independent; privileged commands are available.
- Metadata-only inventories found 151 GiB of home state, including development
  projects, Unity installs, Firefox profiles, VS Code shared storage and game
  saves outside Steam. These require explicit declarations beyond the examples.
- `@var` has nested `lib/portables`, `lib/machines`, and `tmp` subvolumes.
  Retirement must inspect these individually and must not recursively delete.
- Prepared: snapshots, state classification ledger, migration backing,
  granular declarations, topology guards and multi-boot regression tests.
- Passed: formatting, flake checks, the strengthened combined regression
  (three normal, two recovery, return to normal), desktop and home-only builds,
  blank-disk reconstruction, workstation smoke and five root-reset scenarios.
- Home cutover generation 42 has booted. Its quiesced shutdown copy and first
  physical home sentinel matrix passed; home is root-local and legacy var remains.
  A redundant random-seed bind on legacy var was diagnosed and corrected below.
- Pending: repeated physical home acceptance and the var cutover, post-trial
  application rechecks, physical repeated normal/recovery boots, backing-store pruning, and
  legacy-subvolume/snapshot retirement. The goal is not complete.
- Observed Unreal Zen startup delay corrected on 2026-10-09: the earlier editor
  fixture leaked private PIDs into host shared memory. Stale runtime records were
  removed and fixture IPC isolation corrected. Actual relaunch: Zen ready in
  0.058 seconds, editor startup 12.612 seconds; user confirms normal startup.

Evidence paths and validation results will be added here as work progresses.

### Offline validation receipts

| Check | Result | Receipt |
| --- | --- | --- |
| Combined home/var/identity/cache/recovery/return regression | PASS, 143.49 s | `/tmp/granular-flake-final2.log`; `/nix/store/gn3v0k8hwf5avib1kl1i210l66lcbyfp-vm-test-run-granular-impermanence` |
| Flake checks, formatting, statix, deadnix, actual topology evaluation | PASS | `/tmp/granular-flake-final2.log` |
| Actual Disko blank-disk reconstruction and installed-system reboot/recovery | PASS, 251.07 s | `/tmp/granular-reconstruction-final2.log`; `/nix/store/vl85cgqyj7lbs0ncd0j9jf4xc0qd1syh-vm-test-run-blank-disk-reconstruction` |
| Workstation Home Manager smoke | PASS | `/tmp/granular-build-pass7.log`, `/tmp/granular-offline-final.log` |
| Five root regression scenarios | PASS; latest fixture replay recorded separately | `/tmp/granular-root-suite-final.log`, `/tmp/granular-root-suite-pass2.log` |
| Migration tools | Build/shellcheck PASS; runtime refusal PASS | `/tmp/granular-tools-uid-fixed.log`, private `shutdown-refusal-fixed.log`, `var-refusal-fixed.log` |

The home/var test output aliases share the combined regression intentionally.
These receipts do not assert physical or functional application acceptance.

### Migration and implementation evidence

- Read-only pre-migration snapshots:
  `/.snapshots/pre-granular-impermanence-home-20261008-104128` and
  `/.snapshots/pre-granular-impermanence-var-20261008-104128`.
- Full home safety copy: `/persist/home/p2949`, copied from the immutable home
  snapshot with `cp -a --reflink=always` to retain metadata without duplicating
  151 GiB of physical extents. `rsync -aHAXn --numeric-ids --delete
  --itemize-changes` against that snapshot returned no differences. This verifies
  the snapshot copy, not changes made by still-running applications afterward.
- Selected `/var` backing was copied and verified: NixOS allocation state,
  Bluetooth pairing, Btrfs scrub history, random seed, and NetworkManager's
  identity key. Only paths/metadata and comparison exit statuses were inspected.
- A 600-second `fatrace` session captured Firefox, VS Code, Codex, Thunar and
  WirePlumber writes. Btrfs resolves events through `/mnt/btrfs-top/@home` and
  `@var`, so extraction uses these prefixes. Duplicate watch warnings occurred;
  observed events do not prove every application was exercised.
- After snapshots created at `20261008-110009`; no-data send/receive metadata
  diffs and all inventory/trace receipts are private in
  `/persist/granular-migration` (directory 0700, artifacts 0600).
- User confirms using browser, Codex, VS Code, Steam, Unity, Unreal and Blender;
  Android Studio is planned but not installed. User specifically requests
  auditing disposable children inside application profiles as well.
- `.zen` owner identified from metadata as the Unreal engine's `zen` binary;
  its invocation History/States are disposable runtime records. It is omitted
  from persistence; Firefox profiles are actually under `.config/mozilla`.
- User explicitly selected persistence for the specific expensive Steam shader
  cache (218 MiB) and Unreal shared DDC/Zen caches (831 MiB). Ordinary caches,
  diagnostics, temporary files and undeclared state remain disposable.
- Source now omits active `@home`/`@var` mounts; physical sources are retained.
  Dedicated Home Manager persistence and host system-state declarations added,
  with topology assertions and volatile journal policy.
- Application cache children are declared in `home/p2949/ephemeral-app-state.nix`
  and mounted from root-local `.cache/ephemeral-app-state`. This permits atomic
  profile-file replacement while caches still disappear. Known disposable
  profile files use boot-only tmpfiles rules, disabled in recovery mode.
- Zsh history moved to a persisted state directory, avoiding an atomic rename
  onto a file bind mount; existing history was copied to the new backing path.
- Global Git config similarly moves from `.gitconfig` to the standard XDG
  `.config/git/config` directory; contents copied and compared privately.
  The observed Markdown/VS Code association is now declarative, while
  pavucontrol's geometry/filter/meter preferences are deliberately ephemeral.
  Epic's application-scoped parent is retained with generated/cache exceptions
  so project-record updates can be atomic too.
- First VM run exposed upstream tmpfiles-created `@root/var/lib/portables`
  subvolumes. The reset guard correctly refused deletion. The fix preserves
  upstream tmpfiles rules but changes machines/portables/var-tmp to ordinary
  directories, retaining the strict reset guard.
- Second VM run exposed root-owned `.cache` scaffolding. Activation now creates
  the cache root with the user's ownership before creating nested cache sources.
- Subsequent cache write check exposed a fixture error: root-created sentinel
  files prevented user writes. Home sentinels are now created as the actual
  user, retaining the ownership check rather than bypassing it.
- Reconstruction proved normal reset/home/var persistence and recovery topology,
  then exposed two failures: a physical CPU power-limit service has no RAPL
  device in QEMU, and an unseeded NetworkManager key was atomically replaced.
  The fixture now disables physical RAPL control; production persists the
  NetworkManager directory with boot-only deletion of leases/seen-BSSID/time
  caches. That directory was copied and verified before changing declarations.
- Updated reconstruction, smoke-test integration and shared root harness;
  combined test covers normal/recovery/normal boots and application cache paths.
  The actual desktop, blank-disk reconstruction and workstation smoke builds
  returned exit 0 (`/tmp/granular-build-pass7.log`). Five root scenarios returned
  exit 0 (`/tmp/granular-root-suite-final.log`). The stronger combined test with
  cross-boot Git/Code atomic-save checks subsequently passed; see the receipts above.
- A packaged `granular-final-sync` tool is available as a flake output. Its
  immutable manifest is generated from the evaluated real allow-list; it checks
  the old mount topology, mirrors only declared state, migrates Git/history,
  verifies a clean metadata dry-run, and refuses to run after cutover.
- Live read-only verification found drift since the immutable safety copy,
  as expected while apps are running. Final quiesced synchronization remains
  mandatory; the initial copy must not be treated as current application state.
- Metadata send streams were captured to private files before dumping, avoiding
  a pipe SIGPIPE from the dump receiver. Both operations completed successfully:
  home diff 110,006 lines, var diff 337 lines; extracted traces 28,841 home-write
  events and 327 var-write events. Binary streams contain no file data.
- Added the temporary `desktop-home-cutover` output to follow stages 21–26
  before removing `/var`. It keeps only `@var`, with `neededForBoot` required
  by Impermanence's persisted var paths. The final `desktop` retains neither.
  Evaluation checks both configurations. Reconstruction calls the actual Disko
  module with the desktop policy rather than assuming it is a literal set.
  Copying already evaluated Disko internals initially retained the physical
  device despite the fixture override; importing raw declarations fixes that
  test integration error without changing the physical disk configuration.
- Project metadata audit found Unity project logs/temp and Unreal project
  Intermediate/Logs/ShaderDebugInfo/UnrealBuildTool artifacts under the persisted
  Development parent. These are now declared root-backed exceptions. Assets,
  source, settings, autosaves and editor collections remain retained.
- Unity Libraries total 3.3 GiB. The older project's Assets directory is absent;
  its Library may contain recovery data. User explicitly selected retaining both
  Libraries while resetting project logs and temporary files; both are class R.
- Packaged `granular-physical-check` seeds a private, exact-closure/boot-ID-bound
  matrix including every application cache exception, then verifies only after
  a real reboot. `granular-shutdown-cutover` refuses while desktop-user processes
  remain, seeds the matrix, performs/verifies final synchronization, and only
  then sets a one-shot boot entry. The first shutdown copy subsequently completed
  successfully; its physical boot result is recorded below.
- Final-sync tooling supports the later var-only migration and rejects copying
  root-local home back over active persisted profiles. A failed shutdown copy
  must leave the old boot default selected. No live mount replacement is used.
- Strengthened combined VM passed three normal boots and two recovery boots,
  then its return-to-normal step reached a stale boot entry whose initrd had
  been pruned when installing the fixture's recovery-only profile. The fixture
  now reinstalls the exact normal generation before selecting it, matching
  real `nixos-rebuild boot`; return-to-normal assertions are retained unchanged.
- A local shutdown-refusal check exposed a runtime-allocated UID: the Nix UID
  was null and the first wrapper passed an empty process selector. It incorrectly
  began an allow-list copy while apps were running. The final dry-run detected
  drift and aborted before boot selection; source volumes and snapshots were
  untouched. The wrapper now resolves `id -u` at runtime, and any process-check
  error aborts. Only generated diagnostic sentinels were removed; failed ticket
  and copy log are private under `/persist/granular-migration`. Final quiesced
  synchronization is still mandatory; this attempt is not migration acceptance.
- Added [the physical cutover procedure](docs/granular-cutover.md) and the
  packaged arming tool: boot-only installation of an exact built store closure,
  old-default protection, reviewed stop ordering, no automatic reboot, and
  receipt-based normal/recovery checks. These tools never retire subvolumes.

### Home cutover preparation — historical preboot record, 12:00–12:06

- Boot-only generation 42 installed successfully from the validated closure
  `/nix/store/vldhz13imcq9bz6pq9nkm795v69cbpqj-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Its ESP kernel and initrd copies compare equal to the store artifacts.
- Generation 41 (`c9my1br8xhqn4rzpv2c2fl55csvzp0ny`) remains the live system and
  EFI default. Its boot ID is `5862c6f3-22ec-4c12-b88e-6829be0edc00`. Live `/home`
  and `/var` still use their originals. No legacy subvolume/snapshot was deleted.
- `granular-final-copy.service` is active/exited and armed with the reviewed
  shutdown ordering. It seeds the physical matrix, copies/verifies stopped
  application state, then selects generation 42 for one boot. Copy failure
  preserves the generation-41 default. A forced reset bypasses the copy.
- Arming uses pinned rebuild-ng with `--no-reexec --store-path`: the default
  self-reexec otherwise tries to evaluate a channel configuration even when
  deploying a prebuilt store path. Both unsuccessful attempts retained the old
  default; the successful installation made no live mount changes.
- Tool and candidate GC roots: `/persist/granular-migration/arm-cutover-tool`,
  `physical-check-tool`, `final-sync-tool`, `home-cutover-system`, `final-system`.
  The exact final desktop closure is
  `/nix/store/h2vbh2291h1v7vz1kk2in39hx10rq1hx-nixos-system-desktop-26.05.20261004.0d9e9b8`.
- Private receipts include `home-arm.log`, `boot-artifact-verification.log`,
  `pre-cutover-flake.log`, `combined-regression-final.log`,
  `reconstruction-final.log`, `root-suite-final.log`; the unit and shutdown log
  are in the same directory. Artifacts are 0600, directory 0700.
- Final armed-source `nix flake check` passed after the rebuild/self-reexec
  correction (`armed-flake-final.log`); the combined VM remained cached at its
  passing exact derivation. `git diff --check` passes as well.
- User chose “I'll save my work and reboot myself” for the first physical home
  cutover. No agent-initiated reboot is authorized or scheduled. Await that
  actual orderly reboot; elapsed time is not evidence it occurred. The plan and
  service are ready; do not arm another service
  or select generation 42 manually before final-copy verification.
- After the actual reboot, inspect `final-copy-shutdown.log`,
  `final-sync-verified`, and `physical-boot-pending.json`, then run:
  `sudo /persist/granular-migration/physical-check-tool/bin/granular-physical-check verify`.
  A receipt must pass before clearing the temporary old-default EFI override
  (`sudo bootctl set-default ''`), repeating normal/recovery trials, functional
  app checks, pruning or any retirement. The home-only phase keeps `@var`.

### First physical home boot — 2026-10-08 12:17

- User rebooted independently. New boot ID:
  `3166d07f-d1a9-4d86-830b-91d29d277a3d`; exact running closure is generation 42
  (`vldhz13imcq9bz6pq9nkm795v69cbpqj`). The shutdown log ends with a verified
  quiesced copy and successful one-shot selection; final-sync receipt is dated
  `2026-10-08T12:16:35+01:00`. This supplies actual shutdown-handoff evidence.
- `granular-physical-check verify` passed and saved
  `/persist/granular-migration/physical-boot-passed-457180b3-d53c-4233-a7a3-ee7c404ec151.json`.
  Root/home ephemeral sentinels disappeared; declared state, identity and all
  persistent islands survived. Legacy var intentionally remains mounted.
- An independent check confirmed all 82 cache-exception mounts point into
  root-local `.cache/ephemeral-app-state` and are owned by UID 1000. Steam shader
  cache and Unreal shared DDC/Zen remain on persisted application parents.
- The sole startup failure was Impermanence attempting a file bind over the
  existing random seed on legacy `@var`. The actual random-seed load succeeded.
  The intermediate home-only policy now omits that redundant file declaration;
  the final root-local-var policy continues to persist it. The obsolete failed
  unit was runtime-masked/reset without moving, replacing or reading seed data;
  zero failed services remain. Private failure receipt:
  `home-first-boot-seed-collision.log`. Evaluation now asserts both phase policies.
- User now explicitly requires autonomous work, no requests for human
  intervention, and **no reboot**. This supersedes previous reboot discussions.
  Continue non-disruptive diagnostics, corrections and offline validation.
  Repeated physical normal/recovery cycles and final var cutover cannot be
  certified from this first home boot; keep those gates open and retain originals,
  snapshots and migration backing. Do not schedule or request another reboot.
- Private comparisons against the now-inactive original home confirm identical
  Codex authentication/configuration, ADB identity, GitHub CLI authentication,
  Firefox key database/profile registry, VS Code settings and PulseAudio cookie.
  Firefox places/cookies and both VS Code state databases pass SQLite quick-check.
  Extension, Steam library/userdata and Blender version-directory inventories
  match. These are state-integrity checks, not interactive functional acceptance.
- The user's pre-reboot file transaction changed the Unity projects: the old
  and active trees both now have Assets/Library under `VR-AR-project`, while
  `VR-AR-project-2` is empty except for generated cache mount scaffolding. A
  Library exists in retained Trash. No project was silently restored or deleted;
  these current results supersede the initial inventory without weakening the
  user's policy to retain Libraries. Unreal and Unity project metadata compare
  equal to the quiesced original.
- Corrected home-only closure built and installed as generation 43, boot-only:
  `/nix/store/0g2j5q657pfd373xicqdyanwrlmwjpf0-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Normal and persistent-root ESP kernel/initrd comparisons both pass. After the
  first physical home matrix passed, generation 43 was selected as the future
  default to avoid returning to the now-inactive legacy home by accident.
  Generation 42 remains the running session; no live activation or reboot ran.
  Generation 41 and original subvolumes remain available as deliberate rollback.
  Both first-boot and corrected closures have separate migration GC roots.
- Corrected-source formatting, flake checks and home-only build pass. The final
  desktop still evaluates to the previously validated `h2vbh2291h1v7vz1kk2in39hx10rq1hx`
  closure; combined VM derivation is unchanged and its passing result is cached.
  Private receipts: `home-correction-flake.log`, `home-correction-install.log`.
- Postboot live review passes all 32 checks, including every declared directory
  bind, password-source/private-mode equality, app identity comparisons, SQLite
  integrity, expensive-cache backing, corrected normal/recovery ESP artifacts,
  Home Manager and random-seed health. Receipt: `home-first-boot-live-review.json`.
  Temporary test files proved user atomic replacement under Documents, Code,
  Git and Codex, and writes to Firefox/Code/Steam/Unity cache mounts; all test
  files were removed. Blender 5.2.2 LTS loaded persisted configuration and eight
  addons in background mode and exited successfully (`home-first-boot-blender.log`).
  This does not certify gameplay, browser sign-in, Unity/Unreal interactive work,
  or the pending repeated physical boot/recovery requirements.

### Autonomous application checks and backing audit — 2026-10-08, begun 12:34

- Codex CLI login status, executed as `p2949`, confirms the retained ChatGPT
  login. Auth/config content comparisons already passed; the resumed running
  Codex session also works. Private receipt: `home-first-boot-codex-login.log`.
  VS Code CLI successfully reads the retained extension inventory; its active
  graphical session and private user-state/database checks remain healthy.
- Firefox successfully starts headlessly from a private reflink copy of the
  retained profile, renders `about:blank`, preserves the bookmark count and
  exits successfully. It ran inside an isolated network namespace, without
  modifying the real profile or opening a graphical window. The temporary copy
  was removed. Private receipts: `home-first-boot-firefox-startup.json` and `.log`.
  This proves offline profile startup, not sign-in to remote websites.
- A read-only backing audit found that shared mount propagation also exposes
  live root-backed cache overlays beneath `/persist/home/p2949`. Directly
  deleting these apparent backing paths could affect an active cache. Audit and
  later pruning must use a non-recursive view of `@persist` inside a private mount
  namespace, with its propagation made private before creating the view. The
  inventory view was read-only; live host mounts were unchanged.
- The raw backing inventory identifies 56 undeclared migration-residue paths
  (1,912,860,672 allocated bytes), 82 hidden cache directories (1,885,999,104
  bytes), and 5 boot-managed disposable files (6,221,824 bytes). File exceptions
  can be live and must be left to their boot-only rules. Allocated totals can
  share reflink/snapshot extents and do not predict reclaimed disk space.
- All 49 top-level `/persist` entries have recorded purposes: explicit backing,
  credentials, current migration evidence, earlier validation evidence and
  backup/recovery staging. Historical material retains separate retirement
  gates. Private inventory/script: `backing-pruning-inventory.json`/`.py`;
  immutable evaluated file-policy copy: `disposable-files-policy.json`.
  This is preparation for stages 26/42; **no backing data was pruned** and no
  final hygiene or repeated-physical-acceptance gate is claimed complete.

The repeated physical and remaining functional application gates remain open.
The goal remained incomplete under the no-reboot/no-intervention instruction
at this point. The 2026-10-09 coordination update below supersedes that restriction.

### Isolated retained-project editor checks — 2026-10-08

- Unity 6000.6.4f1 loaded a private reflink copy of `VR-AR-project` and the
  retained profile/license state. The log confirms resolved entitlements,
  successful assembly reload/build, a connected shader compiler and successful
  batch-mode shutdown; exit status 0 in 19.10 seconds. Assets, Packages,
  ProjectSettings and UserSettings in the original project are unchanged.
  Private evidence: `home-first-boot-unity-startup.json`, `-editor.log` and
  `-launcher.log` under `/persist/granular-migration`.
- The first editor attempt used bare `steam-run`, which lacks the `libtinfo.so.6`
  already supplied by the configured Unity Hub. It imported the copied project
  but failed its shader subprocess (exit 134). The successful retry provides
  the same existing ncurses library only inside the test launch; no production
  package, global library environment or project was changed. Failed evidence
  is retained separately with `-first-editor-failure-` names.
- Unreal 5.8.2 loaded the retained `AI_Gavin_Project` compiled module and
  `L_FirstPlayableRoom` default map from a private project/profile copy. Engine
  initialization and map check (zero errors/warnings) passed; `QUIT_EDITOR`
  requested an orderly shutdown, exit 0 in 18.20 seconds. Original Source,
  Config, Content, Binaries and `.uproject` files are unchanged. Private evidence:
  `home-first-boot-unreal-startup.json`, `-editor.log` and `-launcher.log`.
- An earlier positional project argument failed before initialization (exit 139);
  using the engine's supported explicit `-project=` argument loaded the project.
  A second attempt loaded the map but generic `quit` did not close this editor
  and its 180-second fixture deadline expired (exit 124). The installed engine
  source routes `QUIT_EDITOR` to `UUnrealEdEngine::CloseEditor`; the final retry
  uses this command and logs normal editor/engine shutdown. Earlier failures
  remain separate `-first-editor-failure-` and `-generic-quit-timeout-` receipts;
  none are counted as passing tests and no production launch wrapper changed.
- Both editor fixtures use private mount, PID and network namespaces, private
  home/project copies, read-only editor installs and loopback-only networking.
  `HOME` is unchanged. Initial fixture-path failures did not launch an editor;
  temporary copies are removed after each terminal result. The isolated Unity
  check certifies retained-project startup/import and local license handling,
  not interactive editing, Unity VCS remote access, Unreal PIE/gameplay, GPU
  rendering or a complete build workflow.
- Qualification discovered on 2026-10-09: these original fixtures did not isolate
  SysV IPC or the POSIX `/dev/shm` filesystem. Their project-integrity claims
  remain valid, but they leaked Zen runtime state into the host. The correction
  and independent actual-launch acceptance are recorded below. General-named
  Unreal receipts were refreshed by the diagnostic rerun; the 18.20-second
  October-8 result above is historical, not the contents of those latest files.
- Unity command-line behavior is documented in the
  [official Unity editor argument reference](https://docs.unity.com/en-us/engine/6000.5/manual/unity-editor/command-line-arguments/editor).
  Unreal unattended/headless flags are documented in the
  [official Unreal argument reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-command-line-arguments-reference?lang=en-US).

### Migration gate enforcement and stage audit — 2026-10-08

- The var-arming helper now validates physical home receipts before writing
  migration evidence, changing EFI defaults, installing a generation or creating
  its runtime service. Stage 22's initial legacy-home cutover does not count as
  either root-local-home reboot cycle required by stage 23. Future sentinel
  tickets record `seeded_home_fsroot`; old receipts without that evidence cannot
  be used to satisfy the repeated-cycle gate.
- Twelve regression cases cover empty/single histories, duplicate boots,
  unaccepted current boot/closure, intervening recovery, wrong phase, receipt
  order, valid consecutive cycles, same-boot receipts, malformed timestamps,
  legacy-home initial cutover and receipts without source topology.
- Live execution of the packaged var-arming tool refuses on the actual one-boot
  state. EFI entries/selection, running/system profiles, original migration
  evidence, pending-ticket state and runtime-service state remain unchanged.
  Private receipts: `var-home-gate-refusal.json` and `.log`.
- Updated packaged arming/physical tools build and shellcheck successfully;
  the full flake check, including all twelve receipt regression cases, passes.
  Receipts: `home-gate-build.log`, `home-gate-flake.log`, `home-gate-regression.log`.
  Current migration GC-root aliases now reference the guarded tools; previous
  versions are independently retained with `-before-home-gate` names. This
  changes no running/installed system closure, boot choice or live mount.

The following audit covers all numbered stages. “Source complete” certifies only
the implementation/artifact named; it does not certify later physical gates.
Private receipts below are under `/persist/granular-migration`.

| Stage | Current evidence and remaining obligation |
| --- | --- |
| 1 | Objective preserved; final root-local var, repeated physical modes and retirement remain incomplete. |
| 2 | Initial topology recorded; current root-local home/legacy var verified live. |
| 3 | Originals/snapshots retained, boot-only boundary changes, private secrets and verified final copy respected. |
| 4 | Implementation branch exists at the reviewed starting commit; current changes preserved. |
| 5 | `topology-before.txt`, `subvolumes-before.txt`, `usage-before.txt` capture the initial host. |
| 6 | Read-only before/after home/var snapshots exist; UUID/readonly metadata verified. |
| 7 | `docs/ephemeral-state-audit.md` classifies authoritative, rebuildable, generated and mixed state. |
| 8 | Full home metadata inventory and protected copy recorded; no secret contents added to Git. |
| 9 | `.config`/`.local` split; application/project children classified individually. |
| 10 | Trace covers observed browser/Code/Codex/desktop writes; complete representative coverage of every app remains partial. |
| 11 | Before/after snapshots and no-data Btrfs diffs retained privately. |
| 12 | Audited initial home classes implemented, including user-selected expensive caches and Unity Libraries. |
| 13 | Dedicated Home Manager persistence module imported and tested. |
| 14 | Protected home backing prepared; user ownership/private modes verified. |
| 15 | Initial reflink copy and dry-run passed; orderly shutdown performed/verified the final allow-list copy. |
| 16 | Selected credential comparisons/private modes and password-source equality passed. |
| 17 | Home is root-local on generation 42; original `@home` is retained inactive. |
| 18 | Actual desktop/intermediate topology and narrow-parent assertions pass. |
| 19 | Combined automated test covers repeated home reset/persistence and atomic saves. |
| 20 | Home builds, formatting, checks, smoke and reconstruction passed. |
| 21 | Home-only generations 42/43/44 installed; generation-44 normal/recovery ESP artifact pairs independently verified. |
| 22 | First physical home matrix passed on exact generation 42. Generation-44 recovery is live; its corrected first recovery trial now has a strict 100-marker passing receipt. Earlier failed marker trial remains archived/unaccepted. |
| 23 | One of four accepted generation-44 trials complete: first recovery PASS. The second attempt failed strict verification after Firefox cleanup; its ticket is archived and does not count. Repeat the second recovery before normal → normal. The updated proof tool passes eight marker cases; app closure and pre-application verification remain required. |
| 24 | Initial home application gate passed: technical integrity/startup checks plus user confirmation on generation 42 that browser, Steam, Code, Git/GitHub, relevant VCS and Unity/Unreal workflows all work. Fuzzel ordering restored/confirmed; actual Unreal Zen startup delay resolved/confirmed. Recheck after accepted generation-44 trials; Android Studio remains uninstalled. |
| 25 | Source already uses narrow audited parents and cache exceptions; no whole `.config`/`.local` persistence. |
| 26 | Raw backing inventory prepared; pruning waits for repeated physical/application acceptance. |
| 27 | Var metadata/write/diff audit recorded; physical phase advancement waits for home acceptance. |
| 28 | Stable identity/state retained; volatile diagnostics/cache/undeclared-state policy explicit. |
| 29 | Final var declarations implemented; intermediate seed-bind collision corrected without changing native seed state. |
| 30 | Selected var backing copied; another quiesced var-only copy is required immediately before its actual cutover. |
| 31 | Final source omits `@var`; live intermediate still mounts legacy var. |
| 32 | Final/intermediate topology, persistent islands and recovery configuration assertions pass. |
| 33 | Combined automated var test passes, including persistence/disappearance across normal/recovery/return. |
| 34 | Final desktop/offline suite passed; new migration guards receive their own checks. |
| 35 | Pending: var candidate not armed/installed as a cutover; new guard prevents premature advancement. |
| 36 | Pending: no physical root-local-var boot has occurred. |
| 37 | Pending: physical var cache/tmp/undeclared-state reset cycles have not occurred. |
| 38 | Current generation-44 intermediate recovery services are healthy; final-var service acceptance remains pending. |
| 39 | Automated recovery/return passed; repeated physical granular recovery/return remains pending. |
| 40 | Final topology passes reconstruction; full final physical topology audit awaits var cutover. |
| 41 | Exact-system physical sentinel tool implemented; Codex/Firefox telemetry marker placement passes eight regressions without relaxing retention or whole-container reset requirements. First generation-42 home matrix and first corrected generation-44 recovery passed; remaining physical matrices are pending. |
| 42 | Read-only raw backing inventory records 49 top-level purposes and residual paths; final hygiene/pruning remains pending. |
| 43 | Persistence contract reflects final source and actual staged rollout; final-actual acceptance remains pending. |
| 44 | Combined permanent flake regression registered; new home-acceptance guard is also checked. |
| 45 | Pending: preserve legacy subvolumes and inspect nested var children individually after all technical gates. |
| 46 | Pending: specifically identified snapshots remain required safety material; none retired. |
| 47 | Required host/home/module/test/document structure exists; no root-reset guard was weakened. |
| 48 | Checklist keeps unproven physical, application and hygiene items open. |
| 49 | Not achieved: var remains a persistent island and repeated physical/final-retirement proof is missing. |

No VM, static audit, copied-profile startup or elapsed time is substituted for
the remaining physical workstation requirements. No reboot is requested or scheduled.

The same no-reboot dependency has persisted across at least three consecutive
continuations. Available independent source, guard, integrity and isolated
application checks are recorded above; these do not close the required physical
cycles. The goal was blocked at those rollout gates under the then-current
instruction; this historical restriction is superseded below. Keep generation 43
as the future home-only candidate, legacy var/originals/snapshots intact, and do
not arm the var phase or retire backing material while its prerequisites are open.
The editor-review receipt confirms the same boot, root-local home, legacy var and
zero failed system services (`home-first-boot-editor-review.json`).



### Coordinated physical testing resumed — 2026-10-09

- User now permits requesting human intervention and scheduling necessary
  reboots, and is actively using the system. This supersedes the earlier
  no-reboot/no-intervention restriction. Coordinate the interruption and saving
  active work; permission to discuss/schedule a reboot is not confirmation that
  the current session can be closed immediately.
- Fresh preflight confirms the same first-cutover boot ID, live generation 42,
  root-local home and legacy var. Exact corrected generation 43 is the system
  profile and next normal default; no one-shot entry is selected. Both normal
  and persistent-root ESP kernel/initrd pairs match their exact store closures.
  All 82 cache-exception mounts are root-backed; zero failed system services;
  no active final-copy service. No extra home synchronization is required for
  a repeat cycle because selected home parents are already live persistent
  binds. Private receipt: `home-repeat-cycle-1-preflight.json`.
- At this point the retained physical-check tool seeded and independently
  re-read all 100 harmless sentinels for the first repeat normal cycle. This
  unbooted ticket was subsequently superseded by the recovery-first sequence
  below. Its original pending ticket was:
  `/persist/granular-migration/physical-boot-pending.json`; mode `home`, source
  home `seeded_home_fsroot=/@root`, exact target generation 43
  (`0g2j5q657pfd373xicqdyanwrlmwjpf0`). This is preparation, not a passed cycle.
- User chose to save active work and perform the first repeat reboot themselves.
  No agent reboot is scheduled or initiated. Generation 43 is already the normal
  default; the recovery-first instructions below subsequently changed the next
  boot to recovery once. On return, run the retained
  physical-check `verify` and inspect service/application health before seeding
  the second repeat cycle. Retain the pending ticket on any verification failure. Keep
  legacy var/originals/snapshots intact and do not advance the var phase until
  home physical and application prerequisites pass.


### Supplied continuation review adopted in full — 2026-10-09

- Fully read the user's pasted review/instructions (all eleven continuation
  steps, both physical sequences, and the final prohibitions). Its reviewed
  head `c79f246529e646d1025197146b477846040e5e1d` is historical; the fresh starting
  local head is `15883f6` with a clean tree before these documentation updates.
  Continue by crossing existing gates. Do not redesign persistence/reset
  architecture, weaken the home-acceptance guard, prune backing, or retire
  originals/snapshots before their prerequisites.
- User explicitly confirmed **all checked and working** for the requested
  actual Firefox profile/tabs/logins, Steam library/game saves, VS Code
  settings/extensions/workspaces, Git/GitHub and relevant Unity VCS credentials,
  and Unity/Unreal project access. This closes the initial post-home-cutover
  high-value application gate on live generation 42, in addition to earlier
  Codex/Blender and isolated-editor checks. It is not a claim that Android
  Studio is installed or that future generation-43/final-var sessions are
  accepted before they occur. Avoid further synthetic application QA without
  an observed defect; recheck authoritative state after the physical trials.
- No reboot had occurred since the normal ticket was seeded. Archived that
  unbooted ticket as `physical-boot-superseded-<token>.json` (explicitly not a
  passed receipt), validated exact token contents/regular files, and removed
  only its 99 still-present generated files; one original generated file was
  already absent. No application data, cache contents, directories, backing
  copies or subvolumes were deleted. The superseded ticket does not count
  toward any physical gate.
- Reverified exact generation-43 normal and recovery ESP artifacts against
  their store closures and healthy services, then seeded/re-read all 100
  sentinels for mode `home-recovery`. The new pending target is
  `/nix/store/i81b2klc6z76slxn911mwlla3jm6s6pg-nixos-system-desktop-26.05.20261004.0d9e9b8`,
  source home `/@root`, original boot ID
  `3166d07f-d1a9-4d86-830b-91d29d277a3d`.
  Selected `nixos-generation-43-specialisation-persistent-root.conf` **once**;
  normal generation 43 remains the default/main installed profile, preserving
  both entries. Private receipt: `home-recovery-cycle-1-preflight.json`.
  No reboot was initiated or scheduled by the agent.

The revised home sequence is mandatory for this continuation (generation 44
below supersedes the review's generation 43 after the observed Fuzzel correction):

| Order | Next boot / ticket | Acceptance before proceeding |
| --- | --- | --- |
| 1 | Generation 44 persistent-root / `home-recovery` | Verify exact recovery closure, retained root/home/cache sentinels, legacy var, identity/islands and service health. |
| 2 | Same generation 44 persistent-root / `home-recovery` | Seed a new ticket only after order 1 passes; verify repeated retention and unchanged root identity. |
| 3 | Generation 44 normal / `home` | Seed from root-local recovery home; verify recovery-only/root/home/cache state disappears while declared state and legacy var survive. |
| 4 | Generation 44 normal / `home` | Verify the second consecutive root-local-home normal cycle, then independently run home acceptance. |

After those trials and important app state pass, freeze the home phase. Before
arming var, build/validate the exact current-source final desktop **and** its
persistent-root specialisation, granular VM test, blank-disk reconstruction and
workstation evaluation again; record the source/lock identity and exact closure.
Run home acceptance independently first, then use the existing var-only shutdown
copy/verification/sentinel/one-shot machinery without changing its design. Never
manually select the final system after a failed shutdown copy.

Treat the first final-var normal boot as discovery/acceptance: verify the ticket,
root-local var, service health, NetworkManager identity/connectivity, allocation,
random seed, Btrfs service state, optimization storage and login; verify cache,
tmp, ordinary logs and undeclared var state reset. Add only a specifically proven
missing authoritative service path if a defect appears. Then perform final
recovery → recovery → normal, verifying each ticket before seeding the next.
The initial final normal boot plus return-normal supplies two accepted final
normal boots; repeated recovery must retain root/home/var.

Only after final physical/application acceptance, prune allow-listed E/D residue
and hidden disposable backing copies via a private mount namespace and raw
non-recursive `@persist` view. Leave boot-managed file exceptions to their boot
rules; run the complete sentinel matrix once after pruning. Compare/inspect
legacy home/var and each nested var subvolume for unique authoritative data,
explicitly acknowledge loss of those old rollback generations, retire inactive
home then var/descendants individually, verify the five-island topology, then
handle specifically identified migration snapshots with the required final
confirmation. No such cleanup or retirement is authorized by an unpassed gate.

Fresh GitHub API queries find zero workflow runs directly on this branch and no
PR for this branch. The current workflow triggers pushes to main and pull
requests, so local checks cannot be represented as branch CI. Obtain exact-head
CI/PR checks after the final source freeze, before merge readiness. Corrected the
stale lower status claim that current home/var are both persistent. Preserve the
49-stage original acceptance specification and honest unchecked physical gates.


### Observed Fuzzel history exception corrected — 2026-10-09

- User observed the launcher returned to alphabetical ordering after the home
  migration. This is a small specific missed authoritative state path, not an
  application-startup failure. Its usage counts were stored in the otherwise
  disposable `.cache/fuzzel` file. The eight-entry original survives in inactive
  `@home`; three current entries recorded launches after the cutover.
- Read the installed Fuzzel 1.14.1 manual and exact packaged upstream source:
  `main.c` reads/writes application IDs and counts (`id|count`); `config.c` and
  `doc/fuzzel.ini.5.scd` support `main.cache`. The source writes through an open
  file descriptor, so a temporary compatibility symlink safely preserves live
  writes. This is actual user history (`P`), regardless of the default cache
  pathname; the rest of `.cache` remains reset-root storage.
- Recovered the original read-only inside a private mount namespace. Kept both
  original/recent histories privately, merged counts for matching IDs (the recent
  file was reset by cutover, so its counts are additional), and restored all eight
  resulting entries to `/persist/home/p2949/.local/state/fuzzel/history`, UID
  1000, directory 0700/file 0600. Replaced only the current cache file with a
  compatibility symlink to that backing; no Fuzzel process was running and the
  original bytes were rechecked before replacement. User then explicitly
  confirmed **the ordering is restored**. New live launches go to that backing.
- Source now configures `${xdg.stateHome}/fuzzel/history` and persists only
  `.local/state/fuzzel`; the mounted directory permits ordinary/atomic writes.
  Both final/intermediate evaluation checks require the configured path and
  dedicated persistence declaration to agree. No root reset or migration guard
  was altered. Restoring this observed omission is the exception to home freeze
  permitted by the supplied continuation review.
- Cleared the recovery one-shot while fixing the omission, archived its still-
  unbooted ticket as superseded, and removed only its 100 exact generated token
  files. No physical cycle was counted; no application directories, originals,
  snapshots or migration backing were pruned. The preparation interval had no
  pending ticket and was held against reboot until validation/install completed.
  Generation 42 remains live; generation 44 is now installed for future boots.
- Corrected home closure built:
  `/nix/store/m5kmyzchvyax9k2dbaikwx0m9zrn14i0-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  Workstation evaluation passes; the generated Fuzzel INI passes the actual
  binary's `--check-config`. Full flake checks passed, including a fresh combined
  six-boot VM run in 141.57 seconds. Installed boot-only as generation **44**;
  both normal/recovery ESP kernel/initrd pairs match their exact store closures.
  Use generation 44 for **all four** home trials (recovery → recovery → normal → normal), superseding the review's
  generation-43 reference because a specific additional defect was found.
- Generation 44 recovery closure:
  `/nix/store/66s40b8r4ijbm5jmyf0xb9w56g69y2zn-nixos-system-desktop-26.05.20261004.0d9e9b8`.
  The fresh `home-recovery` ticket has all 100 sentinels independently re-read;
  EFI one-shot is independently confirmed as
  `nixos-generation-44-specialisation-persistent-root.conf`. Normal generation
  44 is the default/main system profile. Source root ID 330 and its UUID are
  recorded for the two recovery-retention checks. Next ordinary orderly reboot
  will enter recovery once; **no agent reboot is scheduled or initiated**.
- Current home GC-root aliases reference generation 44. Generation-43 home
  aliases and prior final-sync/arming tools remain independently retained as
  `-before-fuzzel`; current packaged tools use the corrected evaluated policy.
  Generation 42, generation 41, original subvolumes/snapshots remain available.
  Independent indirect GC-root registration was verified for all four prior
  home/tool aliases and `granular-vm-fuzzel`, whose fresh passing result is
  `/nix/store/w9k5kx6v8knsjjhidybv7slsl5m75fnc-vm-test-run-granular-impermanence`.
  On return verify the physical ticket and root ID/UUID, then check the Fuzzel
  state-directory mount, generated cache setting, user history, and services.
  Remove only the temporary live compatibility symlink once the new configured
  state path is verified; seed the second recovery trial only after acceptance.
- Private evidence: `fuzzel-legacy-history`, `fuzzel-post-cutover-history`,
  `fuzzel-history-restoration.json`, `fuzzel-home-build.out`/`.log` and
  `fuzzel-home-flake.log`, `fuzzel-home-install.json`/`.log`, and
  `home-recovery-cycle-1-fuzzel-preflight.json`. Historical raw backing inventories
  remain preserved; future pruning must account for the now-declared history before deleting
  redundant old cache copies. Final-var exact-source builds/physical acceptance,
  raw cleanup, retirement and final exact-head CI remain gated as specified.

---

### Observed Unreal Zen startup delay corrected — 2026-10-09

- Fully read the user's reported launch log (4,632 lines) and subsequent normal
  launch log (2,528 lines). The first contains 3,571 permission warnings for PID
  76 and a failed Zen auto-launch taking 85.422 seconds. Unreal subsequently
  falls back to filesystem DDC and remains usable; this was a startup delay,
  not lost project data or a reason to discard the retained expensive cache.
- Installed Epic source `ZenServerState.h/.cpp` confirms the 64-byte shared-table
  layout and process liveness check. Host `/dev/shm/UnrealEngineZen` entry zero
  held PID 76, desired/effective port 8558 and session ID matching the companion
  `ZenI_0ad925b0ba22bb42f8e8cbea`. Host PID 76 is root kernel thread `cpuhp/10`.
  Its permission denial causes Zen to assume a server exists. The shared-table
  modification timestamp, 2026-10-08T12:25:20.554425Z, matches the earlier private
  editor test. That fixture isolated PIDs but shared host IPC: this was an agent
  test-isolation defect, not an Impermanence cache-retention defect.
- Archived and removed exactly those two unused shared-memory runtime files
  after confirming no actual editor/Zen process, no port-8558 listener and no
  process mapping of either file. No process was signalled; persistent Zen/DDC,
  profiles, projects and migration snapshots were untouched.
- Corrected the private editor harness to use `unshare --ipc` and mount a private
  tmpfs at `/dev/shm` inside its private mount namespace. Both are necessary:
  SysV namespace isolation alone does not isolate POSIX shared-memory files.
  The harness verifies separate namespace/filesystem identities, unchanged host
  Zen shared-memory contents and unchanged authoritative project files. Its
  old version is archived; the retained executable fixture is corrected.
- A root write to the user-owned `/tmp` harness was denied by `protected_regular`;
  the command sequence erroneously continued with the old fixture. That rerun
  exited successfully in 17.14 seconds after initial cleanup, but leaked another
  private Zen record. Its receipts/records are archived under `uncorrected-rerun`;
  the unused records were removed after the same independent inactivity checks.
  The corrected run then passed in 16.20 seconds, Zen initialization 0.040
  seconds, status OK, no permission/time-out warnings, and no host Zen records
  created. Original project authoritative files remained unchanged.
- The user's ordinary relaunch then created a valid host Zen server, PID 139689,
  listening on 8558; this legitimate live state was left intact. Its full new
  attached log confirms Zen ready in **0.058 seconds**, `ZenLocal` status OK,
  editor initialization and **12.612-second editor startup**, orderly shutdown,
  zero error lines and no prior repeated Zen permission/startup failures. Five
  other warnings concern Vulkan bindless options, absent `.nix-profile`, a render
  console variable and a missing RecastNavMesh; none indicates this Zen failure.
  User explicitly confirmed **"Yes, Zen starts normally"**.
- Private evidence under `/persist/granular-migration/zen-ipc-repair-20261009`:
  original runtime bytes and `cleanup.json`, both attached logs,
  `editor-check-before-ipc-fix.py`, `editor-check-with-ipc-fix.py`,
  `uncorrected-rerun/`, corrected `isolated-unreal-*` receipts/logs and
  `verification.json`. The retained general editor fixture also has the fix.
  Production Unreal wrapper and persistence policy are unchanged; generation 44,
  the pending 100-sentinel recovery ticket and recovery one-shot remain prepared.
  This app defect is resolved; repeated physical home/var and retirement gates
  remain open. No reboot was initiated or scheduled.

### Recovery readiness refreshed after application use — 2026-10-09

- Before advising the next reboot, rechecked the unchanged live generation-42
  boot, exact generation-44 recovery ticket/closure, recovery EFI one-shot and
  zero failed system services. Three generated sentinel files were absent in
  Unity project `Temp`, Firefox `firefox-mpris` and Steam HTML cache. These are
  application-managed temporary directories; disappearance before reboot is not
  a physical recovery failure and no boot is counted.
- Restored only those three exact token-named generated proof files as the user
  and independently verified all 100 ticket paths/contents. Ticket, source boot
  identity and EFI selection are unchanged. Private refresh evidence:
  `home-recovery-marker-refresh-20261009.json`. The next step remains the user's
  orderly reboot into generation-44 recovery after saving work, then exact
  physical receipt/root-identity/service/Fuzzel checks before the second trial.
  If further application use removes markers, refresh them again before the
  test; do not mistake application cleanup for boot-reset behavior.

### First generation-44 recovery observed; strict receipt not accepted — 2026-10-09

- User rebooted; boot `9079c962-37b7-4a7f-af7d-33e73c5c1718` runs the exact
  generation-44 recovery closure `66s40b8r4ijbm5jmyf0xb9w56g69y2zn`. Root ID 330
  and UUID `852d109c-c584-b546-b58c-7c04dd96f728` are unchanged, consistent with
  recovery retaining the root. Home is root-local and legacy var remains.
  There are zero failed system services. Fuzzel's dedicated state directory is
  mounted from `/persist`, and its generated configuration selects that history.
- The unmodified physical verifier refused: 99 of 100 markers matched, but the
  plain file under `.codex/shell_snapshots` was absent. This boot has **no passing
  receipt and does not count**. Do not recreate a missing marker after reboot
  and count it as proof of retention.
- Reproduced cleanup with the actual installed Codex binary in a separate
  temporary `CODEX_HOME`, isolated network namespace and no submitted model turn:
  the plain generated marker was deleted on thread initialization; a marker
  inside a dedicated generated directory survived. Private evidence:
  `codex-marker-cleanup-reproduction.json`. This is an instrumentation defect;
  the production cache mount retains the original root-local backing. Correct
  this specific marker placement before another recovery trial; keep strict
  verification and all normal-reset requirements. No production persistence or
  reset guard is weakened. Generation 44 remains the home candidate; var is
  unarmed. Subsequent preparation/validation is recorded below.

### Physical marker correction and repeat recovery prepared — 2026-10-09

- Corrected only the `.codex/shell_snapshots` proof location: it now uses a
  generated directory containing the token file, on the same root-local cache
  bind mount. All other paths and the 100-path scope are unchanged. Recovery
  still requires the exact file/token; normal mode requires both its token file
  and generated container to disappear. Verification does not ignore missing
  proofs or consult a post-boot replacement. Cleanup unlinks only generated
  files and removes the one generated directory only if empty, never recursively.
- Added seven marker regressions covering reproduced regular-file cleanup,
  missing/corrupt recovery tokens, normal removal of both token/container,
  precise cleanup, preserving unexpected extra files, malformed containers and
  existing flat-marker receipts. Packaged regressions and the unchanged twelve
  home-acceptance regressions pass. Full flake checks completed successfully;
  unchanged VM/reconstruction results were reused, not newly claimed as physical
  evidence. Formatting, statix and deadnix also pass. Live refusal checks confirm
  the new packaged verifier rejects same-boot acceptance and preserves its
  ticket, and the independent home guard still refuses incomplete acceptance.
- Archived the unaccepted ticket as `physical-boot-failed-<token>.json`. The
  initial strict attempt found 99 retained markers; subsequent Firefox use
  removed three further markers in Pending Pings, firefox-mpris and saved
  telemetry pings. The archive records both observations. Removed only the 96
  remaining exact generated proof files. No passing receipt was created, no
  application directories were removed, and no physical cycle is counted.
- New retained physical-check tool:
  `/nix/store/d0n49wyi4bzc8jcw40ynknrbz8dixh7w-granular-physical-check`.
  The previous tool remains independently GC-rooted as
  `physical-check-tool-before-codex-marker`; registration for old/current tool
  aliases was verified. Future var tooling must be built from current source,
  as already required after home freeze, so it incorporates this marker fix.
- Verified the new generation-44 Fuzzel state bind/config and eight retained
  history records, and removed only the temporary `.cache/fuzzel` symlink. Actual
  Fuzzel `--check-config` passes; the configured state history remains intact.
- Seeded/re-read all 100 fresh `home-recovery` proofs from current recovery boot
  `9079c962-37b7-4a7f-af7d-33e73c5c1718`, retaining root ID 330 and its UUID as the
  next recovery expectation. Selected generation-44 recovery once; main/default
  remains normal generation 44. Independently verified both ESP kernel/initrd
  pairs against the existing closures and zero failed services. No rebuild or
  production policy change is needed for this standalone test-tool defect.
- The required accepted sequence is still generation-44 **recovery → recovery
  → normal → normal**; the observed unaccepted boot supplies none of these
  receipts. After the next boot verify promptly before exercising applications,
  since ordinary cache cleanup can remove proof files independently of boot.
  If applications remove generated markers before reboot, refresh only the
  current ticket's exact generated files before reboot, never after it.
  Private evidence: `home-first-recovery-unaccepted-review.json`,
  `codex-marker-cleanup-reproduction.json`, `granular-codex-proof-build.out`/`.log`
  and `home-recovery-codex-marker-preflight.json`. No reboot is initiated/scheduled.
  Full-check evidence: `granular-codex-proof-flake.log`; live refusal evidence:
  `codex-marker-guard-refusals.json`. App use must pause for the physical proof
  interval: save/close ordinary applications, verify markers before reboot, and
  return here after reboot before relaunching Firefox/Steam/Unity/Unreal.

### Independent live recovery binding audit — 2026-10-09

- On unchanged recovery boot `9079c962-37b7-4a7f-af7d-33e73c5c1718`, independently
  verified every one of the 82 selected cache mounts resolves to its exact
  `/@root/home/p2949/.cache/ephemeral-app-state/<relative>` backing, with UID
  1000 ownership. Used `findmnt` JSON to preserve spaces in application paths.
  This is runtime topology evidence, not a substitute for a physical receipt.
- Sample normal-only Codex generated-file and VS Code lock cleanup rules are
  absent in recovery. Root still has only its permitted `srv` descendant. Private
  evidence: `home-recovery-runtime-binding-audit.json`.
- Rechecked the pending replacement recovery ticket: all 100 generated markers
  remain intact, selected one-shot is generation-44 recovery, and there are no
  failed services. No reboot has occurred since reseeding. Firefox is still
  running; the user's app-close/readiness question remains unanswered. The next
  dependent action is the final marker check after application shutdown, then
  the user's chosen self-reboot. No applications were stopped by the agent, no
  reboot was initiated, and var remains unarmed.

### Continuation gate remains blocked on user readiness — 2026-10-09

- Revalidated the same required user-readiness/reboot gate across the three
  consecutive goal turns ending here, including the correction/preparation turn
  and subsequent runtime audit. Independent implementation and runtime checks
  are complete for this home candidate; the next authorized dependent action
  cannot proceed while the user is still using Firefox and has not answered the
  app-close/readiness question. Do not infer saved work or reboot permission from
  an automatic goal continuation, and do not stop the user's applications.
- Latest live check: unchanged recovery boot
  `9079c962-37b7-4a7f-af7d-33e73c5c1718`, all 100 replacement proofs intact,
  generation-44 recovery one-shot still selected, Firefox still running. No
  reboot since seeding and no accepted replacement physical receipt exist.
- Updated stale generation references in the 49-stage audit to current
  generation-44 evidence. The goal is blocked on the required readiness/self-
  reboot event, not complete. Resume with the final marker check once the user
  confirms apps are closed, or verify the exact pending ticket immediately if
  the user has already rebooted. Final builds/var cutover, backing pruning,
  retirement and final CI remain behind the unchanged physical home gate.

---

### User readiness confirmed; final pre-reboot check passed — 2026-10-09

- User answered: **"Saved and closed; I'll reboot myself after your check"**.
  Readiness is now confirmed; do not request the same permission again. The
  compositor initially still reported one Firefox window. An attempted legacy
  dispatch was rejected by Hyprland's Lua dispatcher; Firefox subsequently
  exited. Independent process scanning now finds no Firefox/Steam/Unity/Unreal
  or Zen server processes. No process was forcibly terminated.
- Rechecked the same seeded boot before making any proof refresh. Application
  shutdown had removed one generated marker; recreated only that exact missing
  user-owned proof file before reboot and independently verified all 100 token
  files. The ticket bytes/hash are unchanged. This is pre-boot preparation, not
  replacement of evidence after reboot, and no physical receipt is counted.
- Generation-44 recovery one-shot, normal main profile, original root ID 330
  and UUID, zero failed services and all eight Fuzzel history records remain
  verified. The system is ready for the user's self-reboot. No agent reboot was
  initiated or scheduled. Private final evidence:
  `home-recovery-final-ready-after-app-close.json`.
- After reboot verify the pending exact recovery ticket promptly before ordinary
  applications restart, then record acceptance and prepare the second recovery
  trial only if verification succeeds. Var remains unarmed.

---

### First accepted recovery passed; second recovery prepared — 2026-10-09

- User self-rebooted into generation-44 recovery on new boot
  `99c7b457-caa8-4599-9d87-6b74f10ccb20`. The corrected strict verifier passed
  all 100 markers, exact closure, source/target topology, machine identity and
  persistent islands. Receipt:
  `physical-boot-passed-f27d98d2-004e-4b1b-a803-68af4b8c4f20.json`.
  Generated survivors were removed by the verifier after recording acceptance.
  This is **accepted recovery 1 of 2**, not a normal home-reset cycle. The earlier
  failed trial remains unaccepted and is never substituted for this receipt.
- Independently confirmed unchanged root ID 330 and UUID
  `852d109c-c584-b546-b58c-7c04dd96f728`, zero failed services, Fuzzel's exact
  persistent state bind/config, all eight history records and absence of the
  removed compatibility symlink. Actual Fuzzel `--check-config` passes. No
  Firefox/Steam/Unity/Unreal/Zen server processes are running. Private review:
  `home-recovery-accepted-cycle-1-review.json`.
- Only after acceptance, seeded all 100 new `home-recovery` markers from the
  current root-local home for the same exact generation-44 recovery closure.
  Independently re-read every token and selected
  `nixos-generation-44-specialisation-persistent-root.conf` once. Normal/main
  generation 44 remains installed. Private preparation:
  `home-recovery-accepted-cycle-2-preflight.json`.
- Next user self-reboot is **accepted recovery trial 2**. Verify unchanged root
  ID/UUID and the strict pending ticket promptly before opening other apps.
  If it passes, prepare generation-44 normal → normal; only those subsequent
  two consecutive root-local normal receipts satisfy the independent var guard.
  Updated current-status/contract/audit/runbook documentation accordingly.
  No agent reboot is scheduled/initiated, no var cutover is armed, and no
  migration backing, legacy subvolume or snapshot was retired.

---

### Second recovery awaits another application-close check — 2026-10-09

- Revalidated current boot `99c7b457-caa8-4599-9d87-6b74f10ccb20`: the second
  recovery reboot has not occurred, and systemd reports no active shutdown jobs.
  First recovery acceptance is unchanged. The next ticket has 98/100 markers;
  Firefox has reopened and removed the flat proofs under `Pending Pings` and
  `y34aofre.default/saved-telemetry-pings` before reboot. This is pre-boot cache
  cleanup, not another failed physical trial.
- Asked the user to save/close the reopened Firefox so the final generated-marker
  refresh can occur after its cleanup. The earlier saved/closed confirmation
  applied to the previous trial; do not assume newly reopened work is saved or
  terminate the browser. No existing ticket, marker expectation, strict verifier
  or EFI selection was changed, and no reboot was initiated/scheduled. Private
  readiness evidence: `home-recovery-cycle-2-awaiting-firefox-close.json`.
- Next action after closure: refresh only the current ticket's exact missing
  generated proof files while still on its source boot, independently verify all
  100 proofs, then return the prepared self-reboot step to the user. Do not
  advance to normal trials before the second recovery receipt passes.

---

### Second recovery final readiness restored — 2026-10-09

- User confirmed **"Firefox is saved and closed"**. Independent process scanning
  confirms Firefox/Steam/Unity/Unreal/Zen server have all exited. On unchanged
  source boot `99c7b457-caa8-4599-9d87-6b74f10ccb20`, recreated only the two
  missing, exact token-named user proof files before reboot. All 100 proofs now
  match the unchanged ticket. No expectation or verifier rule was altered.
- Generation-44 recovery one-shot is independently confirmed; services have no
  failures. Second recovery self-reboot is ready again. Leave ordinary apps
  closed until the next boot's strict receipt has been verified. Private final
  evidence: `home-recovery-cycle-2-final-ready-after-app-close.json`.
  No agent reboot is initiated/scheduled; the first accepted recovery receipt
  remains the only counted trial, and var is unarmed.

---

### Second recovery waits on the chosen self-reboot — 2026-10-09

- The readiness-confirmation turn and two following goal continuations all end
  at the same remaining external gate: the user has chosen to reboot themselves,
  but source boot `99c7b457-caa8-4599-9d87-6b74f10ccb20` is still live. Latest
  revalidation finds all 100 proofs intact, no active systemd shutdown jobs and
  no failed services. The previous continuation added no new acceptance evidence;
  it was not a verified wait on a live reboot job.
- Required preparation and independent checks are complete. No safe independent
  work remains before the second physical recovery receipt; normal trials and
  final-var advancement depend on it. Mark the goal blocked on this self-reboot
  event, without altering its scope or treating the project as complete. No
  further readiness permission is needed. Resume with strict ticket verification
  when the user returns after reboot; the first accepted recovery remains counted.

---

### Latest continuation review and failed second recovery — 2026-10-09

- Fully read all four identical newly attached continuation reviews, including
  all fourteen steps and the instruction to stop expanding application-cleanup
  modeling. Reviewed/source head is `4d615cb9bc98e4f00a591f74b121ccc6ebfd31de`.
  Retain generation 44 and the sequence recovery → recovery → normal → normal;
  then freeze home, rebuild the exact final var candidate, use the unchanged
  guarded var-only shutdown copy, prove the final chain, prune raw backing,
  individually retire legacy subvolumes/specific snapshots, and obtain final CI.
  No persistence architecture or home-acceptance guard change is required.
- The review's second-trial preparation checkpoint is superseded by actual
  boot `d0f24f81-807b-4e27-810a-b2fcdf1beae4`. It runs the exact generation-44
  recovery closure with root ID 330/UUID unchanged, root-local home, legacy var
  and zero failed services. Strict verification found 98/100 proofs: Firefox
  removed the Pending Pings and saved-telemetry-pings regular files. Later media
  artwork cleanup removed firefox-mpris too, leaving 97. No missing proof was
  recreated after boot. Failed ticket is archived as
  `physical-boot-failed-8566011d-bea0-4ddf-baaa-eedbad683975.json`; only its 97
  exact surviving generated files and empty generated container were removed.
  This attempt is unaccepted. First accepted recovery remains counted.
- The existing source fix nests only the two Firefox telemetry proofs, as for
  Codex. Installed Firefox 157.0's TelemetryStorage module skips directories.
  Recovery still requires the exact token; normal reset must remove its whole
  generated container. Eight marker regressions and all twelve unchanged home
  guard regressions pass. New GC-rooted tool is
  `/nix/store/crqszcdvl5hfqxqzi88wraw9bln27ld6-granular-physical-check`;
  the previous tool is separately retained as
  `physical-check-tool-before-firefox-markers`. No system generation is changed.
- Firefox MPRIS cleanup can remove its entire artwork directory, so nesting
  another marker there does not solve the observation timing. Follow the review:
  close applications before seeding, then verify immediately after reboot before
  starting Firefox/Steam/Unity/Unreal. If necessary, use a text console before
  opening the graphical session. Do not weaken or replace missing postboot proof.
- Current preparation boundary: no pending ticket, no new recovery one-shot,
  no var cutover service. The normal default remains generation 44. Firefox is
  active again; previous saved/closed confirmation applied to the earlier boot.
  Finish the current-source tool checks and recheck application closure before
  seeding the replacement second-recovery ticket. No agent reboot is initiated
  or scheduled; no backing/subvolume/snapshot retirement is performed.
- Private evidence: `firefox-marker-repair-20261009/failed-trial-and-source.json`,
  extracted installed `TelemetryStorage.sys.mjs`, upstream MPRIS source copy,
  and `granular-firefox-proof-build.out`/`.log`. The independent live home guard
  still rejects this unaccepted boot; var stays unarmed.

---

# 1. Objective and finish line

This plan has one objective only:

> **Make as much mutable state on the NixOS workstation ephemeral as is practical, with persistence becoming an explicit allow-list rather than an accidental property of filesystem layout.**

The implementation is complete only when all of the following are true:

1. `/` is reset on every normal boot, as it is already.
2. `/home` is no longer an always-persistent Btrfs subvolume.
3. User home state survives reboot **only** when it is explicitly declared through Impermanence.
4. `/var` is no longer an always-persistent Btrfs subvolume.
5. System state under `/var` survives reboot **only** when it is explicitly declared through Impermanence or lives on a deliberately persistent nested mount.
6. `/nix`, `/persist`, `/.snapshots`, `/boot`, and `/var/lib/nixos-optimization` remain deliberately persistent.
7. `/etc` remains ephemeral except for explicitly persisted paths.
8. `/root`, `/tmp`, `/srv`, ordinary `/usr`-side mutable state, user caches, system caches, temporary state, and undeclared application state are discarded on normal reboot.
9. Home Manager reconstructs declarative user configuration after each root reset.
10. NixOS reconstructs declarative system configuration after each root reset.
11. Important credentials, user-created files, application profiles, machine identity, and required service databases have been explicitly identified and persisted.
12. The system has automated tests proving both sides of the contract:
    - declared state survives;
    - undeclared state disappears.
13. The physical workstation has passed repeated normal boots with the new persistence model.
14. The `persistent-root` specialisation still works as the recovery mode.
15. The former `@home` and `@var` contents have been either deliberately retired or retained only as clearly named temporary migration snapshots; they are no longer active persistence mechanisms.

The intended final model is:

```text
Btrfs filesystem
│
├── @root
│   └── /
│       ├── etc/                 ephemeral except bind-persisted state
│       ├── home/                ephemeral except bind-persisted state
│       ├── root/                ephemeral
│       ├── srv/                 ephemeral
│       ├── tmp/                 ephemeral
│       ├── usr/                 reconstructed/declarative
│       └── var/                 ephemeral except bind-persisted/nested state
│
├── @nix
│   └── /nix                     persistent
│
├── @persist
│   └── /persist                 persistent backing store for explicit state
│
├── @optimization
│   └── /var/lib/nixos-optimization
│                               persistent
│
├── @snapshots
│   └── /.snapshots              persistent
│
└── EFI partition
    └── /boot                    persistent
```

The governing rule is:

```text
If state survives a normal reboot, there must be a deliberate declaration
or a deliberate persistent filesystem explaining why.
```

---

# 2. Current starting point

The existing system already has a strong root-Impermanence design.

Current Disko layout:

```text
@root          -> /
@home          -> /home
@nix           -> /nix
@persist       -> /persist
@var           -> /var
@optimization  -> /var/lib/nixos-optimization
@snapshots     -> /.snapshots
```

The current normal boot resets `@root` through the custom systemd-initrd Btrfs root-reset module.

The current `persistent-root` specialisation disables that reset.

The current explicit root persistence consists of:

```text
/etc/machine-id
/etc/nixos
/etc/NetworkManager/system-connections
```

The remaining reason that large amounts of mutable state survive is not the root filesystem. It is the two persistent islands:

```text
@home -> /home
@var  -> /var
```

Therefore this plan does **not** redesign the existing root reset. It extends its persistence philosophy to the currently persistent home and var domains.

---

# 3. Safety invariants

These rules apply throughout the implementation.

## 3.1 Never delete the old `@home` or `@var` during initial cutover

Removing a mount from the NixOS configuration does not require deleting the physical Btrfs subvolume.

During migration:

```text
@home
@var
```

must remain physically present.

They become inactive rollback sources.

This provides two safety properties:

1. old generations that still expect `@home` and `@var` can continue to find them;
2. data omitted from the first persistence declaration can still be recovered.

Do not delete these subvolumes until the final retirement stage.

---

## 3.2 Persistence migration happens before mount removal

Never first make home or var ephemeral and then discover what should have been copied.

The order is always:

```text
inventory
→ classify
→ prepare /persist
→ copy data
→ verify copy
→ declare persistence
→ build
→ boot
→ verify
```

---

## 3.3 Unknown state defaults to “preserve during migration”

The final policy is ephemeral-by-default.

The migration policy is deliberately more conservative.

For any directory that has not yet been classified:

```text
UNKNOWN -> temporarily preserve
```

After it is understood:

```text
UNKNOWN
  ↓
PERSISTENT
DECLARATIVE
EXPENSIVE-RECONSTRUCTABLE
EPHEMERAL
MIXED
```

Only then is it removed from the persistence allow-list.

This prevents a classification mistake from becoming data loss.

---

## 3.4 Never put secrets into the Git repository

The persistence configuration may contain paths such as:

```text
.ssh
.gnupg
.pki
.local/share/keyrings
```

It must never contain their contents.

Actual secret state lives beneath `/persist`.

---

## 3.5 Activate filesystem-boundary changes with `boot`, not `switch`

Changing `/home` or `/var` while they are in active use is unnecessary risk.

For the first home cutover and first var cutover use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Then reboot.

Do not attempt to replace the currently mounted `/home` or `/var` beneath a live graphical session.

---

# 4. Create an isolated implementation branch

Start from the exact source revision that is intended to receive this feature.

Record the current state:

```bash
cd /etc/nixos

git status --short
git branch --show-current
git rev-parse HEAD
git log -1 --oneline
```

Require a clean worktree before beginning.

Create a dedicated branch:

```bash
git switch -c feat/granular-impermanence
```

The feature branch should contain only changes required for this ephemeral-state project.

---

# 5. Capture the current mount and subvolume topology

Before modifying anything, record exactly what currently provides each path.

Run:

```bash
findmnt -R -o TARGET,SOURCE,FSTYPE,OPTIONS /

echo
for path in \
    / \
    /boot \
    /home \
    /nix \
    /persist \
    /var \
    /var/lib/nixos-optimization \
    /.snapshots
do
    echo "=== $path ==="
    findmnt "$path" || true
done
```

Record Btrfs topology:

```bash
sudo btrfs subvolume list -p /
sudo btrfs subvolume show /
sudo btrfs filesystem usage /
```

Mount the Btrfs top-level temporarily if it is not already accessible:

```bash
sudo mkdir -p /mnt/btrfs-top

sudo mount \
    -o subvolid=5 \
    /dev/disk/by-label/nixos \
    /mnt/btrfs-top
```

Verify:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top
```

The expected active subvolumes include at least:

```text
@root
@home
@nix
@persist
@var
@optimization
@snapshots
```

Do not change them yet.

---

# 6. Create migration snapshots of home and var

Create read-only snapshots before auditing or copying.

Choose an unambiguous migration timestamp:

```bash
stamp="$(date +%Y%m%d-%H%M%S)"
echo "$stamp"
```

Create snapshots:

```bash
sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@home \
    "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-home-$stamp"

sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@var \
    "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-var-$stamp"
```

Verify:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top \
    | grep 'pre-granular-impermanence'
```

These snapshots are migration rollback evidence, not the final persistence mechanism.

---

# 7. Build an explicit state classification ledger

Create a working document dedicated to this implementation:

```text
docs/ephemeral-state-audit.md
```

Its purpose is to classify mutable paths.

Use five classes:

| Class | Meaning | Final policy |
|---|---|---|
| `E` | Ephemeral runtime/cache/scratch state | discard every normal reboot |
| `D` | Declaratively reconstructed by NixOS/Home Manager | discard every normal reboot |
| `R` | Reconstructable, but expensive enough that persistence is intentionally worthwhile | persist if explicitly chosen |
| `P` | Authoritative user/service state | persist |
| `M` | Mixed container holding several classes | split into children |

Every top-level home entry and every important `/var` subtree must eventually receive one of these classifications.

Do not finish this project with important entries still marked unknown.

---

# 8. Inventory the entire home directory

Start with size and type information.

```bash
du -xhd1 "$HOME" | sort -h
```

Inspect hidden and normal entries:

```bash
find "$HOME" \
    -xdev \
    -mindepth 1 \
    -maxdepth 1 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Inspect symbolic links:

```bash
find "$HOME" \
    -xdev \
    -maxdepth 2 \
    -type l \
    -printf '%p -> %l\n' \
    | sort
```

Pay special attention to:

```text
.android
.cache
.codex
.config
.dbus
.dotnet
.epic
.icons
.local
.nix-defexpr
.pki
.plastic4
.steam
.vim
.vscode
.vscode-shared
.zen

.ssh
.gnupg
.nuget
.mozilla
Development
Desktop
Documents
Downloads
Music
Pictures
Public
Templates
Videos
```

The XDG user directories currently declared by Home Manager are:

```text
Desktop
Documents
Downloads
Music
Pictures
Development
Public
Templates
Videos
```

All user-created/authoritative directories must be intentionally classified before home becomes ephemeral.

---

# 9. Expand mixed home containers

The following directories must not be treated as single semantic units:

```text
.config
.local
```

Inventory them separately.

## `.config`

```bash
du -xhd1 "$HOME/.config" 2>/dev/null | sort -h

find "$HOME/.config" \
    -xdev \
    -mindepth 1 \
    -maxdepth 1 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Typical policy:

```text
Home-Manager-owned configuration  -> D
application caches                -> E
application identity/profile DBs  -> P
unknown application state         -> preserve during migration, then classify
```

Any configuration that is already generated by Home Manager should normally **not** be persisted.

The purpose of Home Manager is to reconstruct it.

---

## `.local`

Inspect:

```bash
du -xhd1 "$HOME/.local" 2>/dev/null | sort -h
du -xhd1 "$HOME/.local/share" 2>/dev/null | sort -h
du -xhd1 "$HOME/.local/state" 2>/dev/null | sort -h

find "$HOME/.local" \
    -xdev \
    -mindepth 1 \
    -maxdepth 2 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort
```

Treat major children independently.

Examples that are often persistent:

```text
.local/share/keyrings
.local/share/Steam
.local/share/<browser-or-app profiles>
```

Examples that are often disposable:

```text
application caches
generated thumbnails
temporary indexes that are cheap to regenerate
```

Do not persist the entire `.local` permanently merely because it is convenient.

It may be temporarily preserved during the first migration, but the final state should be granular.

---

# 10. Observe real home writes during representative use

Static inspection is not enough.

Use `fatrace` temporarily:

```bash
nix shell nixpkgs#fatrace
```

Start a write-only trace:

```bash
sudo fatrace \
    --filter=W \
    --timestamp \
    --output=/tmp/fatrace-home-var-writes.log
```

During the trace, perform a representative session using the applications whose state matters.

At minimum exercise the applications corresponding to the directories being considered, for example:

```text
Zen/browser
Firefox if used
Steam
one Steam game
VS Code
Codex
Android Studio/emulator if retained
Plastic/Unity VCS if retained
Unreal
Blender
terminal/shell/Git
```

Stop `fatrace`.

Extract home writes:

```bash
grep '/home/p2949/' \
    /tmp/fatrace-home-var-writes.log \
    > /tmp/fatrace-home-writes.log
```

Extract var writes:

```bash
grep '/var/' \
    /tmp/fatrace-home-var-writes.log \
    > /tmp/fatrace-var-writes.log
```

Use the writing process to answer:

```text
Who owns this state?
What creates it?
Will the application recreate it?
Would recreation lose identity, history, projects, credentials or settings?
Is regeneration cheap or expensive?
```

Update `docs/ephemeral-state-audit.md`.

---

# 11. Use Btrfs snapshots to identify actual changed paths

After the representative session, take second read-only snapshots.

```bash
stamp_after="$(date +%Y%m%d-%H%M%S)"
```

```bash
sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@home \
    "/mnt/btrfs-top/@snapshots/granular-impermanence-home-after-$stamp_after"

sudo btrfs subvolume snapshot -r \
    /mnt/btrfs-top/@var \
    "/mnt/btrfs-top/@snapshots/granular-impermanence-var-after-$stamp_after"
```

Use Btrfs send metadata to inspect changes.

For home:

```bash
sudo btrfs send --no-data \
    -p "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-home-$stamp" \
       "/mnt/btrfs-top/@snapshots/granular-impermanence-home-after-$stamp_after" \
    | sudo btrfs receive --dump \
    > /tmp/home-btrfs-diff.txt
```

For var:

```bash
sudo btrfs send --no-data \
    -p "/mnt/btrfs-top/@snapshots/pre-granular-impermanence-var-$stamp" \
       "/mnt/btrfs-top/@snapshots/granular-impermanence-var-after-$stamp_after" \
    | sudo btrfs receive --dump \
    > /tmp/var-btrfs-diff.txt
```

The two sources answer different questions:

```text
fatrace           -> which process wrote the state
Btrfs snapshot diff -> which paths changed
```

Use both before finalizing the allow-list.

---

# 12. Required initial home classifications

The audit has final authority, but use the following as the starting policy.

| Path | Starting classification | Reason |
|---|---|---|
| `.cache` | `E` | cache |
| `.dbus` | `E` | session/runtime state |
| `.nix-defexpr` | `E`/remove | legacy Nix state unless specifically used |
| `.ssh` | `P` | credentials and trust state |
| `.gnupg` | `P` | key material |
| `.pki` | `P` | certificate/NSS state |
| `.android` | `P` or `R` | ADB keys, AVDs, debug identity and expensive SDK/emulator state |
| `.codex` | `P` | authentication and application state unless audit proves otherwise |
| `.plastic4` | `P` | VCS credentials/configuration |
| `.zen` | `P` | browser profile/history/cookies/extensions |
| `.vscode` | `R`/`P` | extensions and editor state |
| `.vscode-shared` | unknown -> audit | identify exact owner |
| `.epic` | unknown -> audit | identify exact owner |
| `.icons` | `P` or `D` | persist user assets unless Home Manager owns them |
| `.dotnet` | `M` | split tools/state from disposable generated data |
| `.vim` | `M` | persist authoritative config/data; discard temp/swap/cache |
| `.steam` | inspect symlink/role | actual Steam state normally lives elsewhere |
| `.config` | `M` | split per application |
| `.local` | `M` | split `share`, `state`, `bin`, etc. |
| `Development` | `P` | authoritative source/project data |
| `Documents` | `P` | user-created data |
| `Desktop` | `P` if used | user-created data |
| `Downloads` | explicit user decision | may contain irreplaceable downloads |
| `Pictures` | `P` | user-created data |
| `Music` | `P` if locally authoritative | user data |
| `Videos` | `P` if locally authoritative | user data |
| `Public` | `P` if used | user data |
| `Templates` | `P` if used | user data |

For safety, user-created XDG data directories should initially persist.

If the final desired policy intentionally makes a directory such as `Downloads` disposable, that must be an explicit decision in the audit ledger.

---

# 13. Add a dedicated Home Manager persistence module

Create:

```text
home/p2949/persistence.nix
```

Import it from:

```text
home/p2949/default.nix
```

The import list should become conceptually:

```nix
imports = [
  ./cli.nix
  ./desktop
  ./development
  ./persistence.nix
  ./shell.nix
  ./xdg.nix
];
```

Use Home Manager's Impermanence support already provided by the NixOS Impermanence module.

Do **not** manually import Impermanence's Home Manager module.

The structure should be:

```nix
{ ... }:

{
  home.persistence."/persist" = {
    directories = [
      # Authoritative user data.
      "Desktop"
      "Documents"
      "Downloads"
      "Development"
      "Music"
      "Pictures"
      "Public"
      "Templates"
      "Videos"

      # Credentials and security state.
      {
        directory = ".ssh";
        mode = "0700";
      }
      {
        directory = ".gnupg";
        mode = "0700";
      }
      ".pki"

      # Application state selected by the completed audit.
      ".android"
      ".codex"
      ".plastic4"
      ".vscode"
      ".zen"

      # Add only audited children of .config/.local here.
      # Examples:
      # ".config/<stateful-application>"
      # ".local/share/keyrings"
      # ".local/share/Steam"
    ];

    files = [
      # Add audited individual persistent files only when needed.
    ];
  };
}
```

This is the shape, not permission to skip the audit.

Before final implementation, replace broad temporary entries with the actual audited final list.

The final file should contain **no unexplained directory**.

Every persistent entry must correspond to a `P` or deliberately accepted `R` entry in the state ledger.

---

# 14. Prepare the persistent home backing tree

Before changing `/home`, create the backing directory:

```bash
sudo install \
    -d \
    -m 0700 \
    -o p2949 \
    -g users \
    /persist/home/p2949
```

Confirm:

```bash
stat -c '%A %a %U:%G %n' /persist/home/p2949
```

Expected ownership:

```text
p2949:users
```

Do not put this path itself into Home Manager's `persistentStoragePath`; `home.persistence."/persist"` automatically handles the home path.

---

# 15. Copy the current home into the persistence backing tree

The safest first migration is to copy the current home into the persistent backing tree before narrowing it.

Use a root-owned rsync invocation so metadata is retained:

```bash
nix shell nixpkgs#rsync
```

Then:

```bash
sudo rsync \
    -aHAX \
    --numeric-ids \
    --info=progress2 \
    /home/p2949/ \
    /persist/home/p2949/
```

Verify with a dry run:

```bash
sudo rsync \
    -aHAXn \
    --numeric-ids \
    --delete \
    /home/p2949/ \
    /persist/home/p2949/
```

At this stage a clean dry-run should show no unexplained differences.

This full copy is a migration safety measure.

It does **not** mean the complete home is declared persistent.

Only paths listed by Impermanence will appear in the active home after cutover.

The undeclared data under `/persist/home/p2949` can be pruned later after the new policy is proven.

---

# 16. Validate credentials before home cutover

Explicitly confirm that every credential-bearing directory expected to survive exists in the persistent backing tree.

Check metadata only; do not print secret contents.

Example:

```bash
for path in \
    /persist/home/p2949/.ssh \
    /persist/home/p2949/.gnupg \
    /persist/home/p2949/.pki \
    /persist/home/p2949/.codex
do
    if [[ -e "$path" ]]; then
        stat -c '%A %a %U:%G %n' "$path"
    fi
done
```

Also check application-profile directories selected by the audit.

Do not proceed until every required persistent path is represented beneath `/persist/home/p2949`.

---

# 17. Make `/home` part of the ephemeral root

Edit:

```text
hosts/desktop/disko.nix
```

Remove the active `@home -> /home` mount declaration from the desired Disko configuration.

The final desired Disko layout should no longer contain:

```nix
"@home" = {
  mountpoint = "/home";
  mountOptions = btrfsMountOptions;
};
```

Do **not** physically delete the existing `@home` Btrfs subvolume.

The currently existing physical subvolume remains on disk as rollback material.

After this configuration change:

```text
/home
```

is simply a directory inside `@root`.

Therefore the existing normal root reset automatically makes undeclared home state ephemeral.

No second home-reset script is required.

---

# 18. Add evaluation assertions for the intended home model

The configuration should make accidental reintroduction of a separate persistent `/home` obvious.

Add a small assertion in the most appropriate persistence/storage module or host persistence policy:

```nix
assertions = [
  {
    assertion = !(config.fileSystems ? "/home");
    message = "Granular Impermanence requires /home to live inside the ephemeral root.";
  }
];
```

If the implementation architecture makes a direct assertion awkward, provide an equivalent evaluation test.

The important invariant is:

```text
normal desktop configuration must not independently mount /home
```

---

# 19. Add an automated home Impermanence test before physical rollout

Create a dedicated test under the existing storage test hierarchy, for example:

```text
tests/storage/impermanence-home.nix
```

The test must prove at least:

### First boot

Create:

```text
/home/tester/persistent-data/survives
/home/tester/.cache/disappears
/home/tester/undeclared-state/disappears
```

The first path must be declared persistent.

The other two must not be.

Reboot.

### Second boot

Assert:

```text
persistent-data/survives exists
.cache/disappears does not exist
undeclared-state/disappears does not exist
```

Also assert:

```text
/home is not a separate @home-style persistent filesystem
```

Then create another ephemeral sentinel and reboot again.

### Third boot

Repeat the persistence/disappearance assertions.

This makes repeated-reset behavior part of the test, not a one-boot coincidence.

Register the test in the existing `tests/` registry.

---

# 20. Validate the home cutover offline

Run formatting and repository checks:

```bash
cd /etc/nixos

nix fmt
nix flake check
```

Build the desktop:

```bash
nix build \
    '.#nixosConfigurations.desktop.config.system.build.toplevel' \
    --no-link
```

Build/run the new home persistence test.

Also evaluate the mount model:

```bash
nix eval \
    '.#nixosConfigurations.desktop.config.fileSystems' \
    --json \
    | jq
```

Confirm that the desired system no longer declares `/home` as an independent filesystem.

Do not reboot until all evaluation and VM checks pass.

---

# 21. Install the home cutover as a next-boot generation

Use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Do not use `switch` for this first filesystem-boundary change.

Before reboot, record:

```bash
readlink -f /run/current-system
sudo nixos-rebuild list-generations
findmnt /home
```

Also verify the physical rollback source still exists:

```bash
sudo btrfs subvolume list /mnt/btrfs-top \
    | grep '@home'
```

---

# 22. First physical boot with ephemeral home

Reboot normally.

Immediately verify:

```bash
findmnt /
findmnt /home || true
findmnt /persist
```

The required result is:

```text
/       -> @root
/home   -> NOT a separate @home filesystem
/persist -> @persist
```

Check the home directory:

```bash
stat -c '%A %a %U:%G %n' /home/p2949
```

Check declared persistence mounts:

```bash
findmnt -R /home/p2949
```

Verify that known persisted directories exist.

Verify that `.cache` is not a persistence bind mount:

```bash
findmnt -T /home/p2949/.cache || true
```

---

# 23. Prove physical home ephemerality

Create physical sentinels.

Ephemeral:

```bash
mkdir -p ~/.cache/impermanence-test
echo ephemeral > ~/.cache/impermanence-test/cache-sentinel

mkdir -p ~/undeclared-impermanence-test
echo ephemeral > ~/undeclared-impermanence-test/home-sentinel
```

Persistent:

```bash
mkdir -p ~/Documents/impermanence-test
echo persistent > ~/Documents/impermanence-test/document-sentinel
```

If a state directory such as `.codex` is declared persistent, create a harmless test file there too:

```bash
mkdir -p ~/.codex
echo persistent > ~/.codex/impermanence-sentinel
```

Reboot.

Verify:

```bash
test ! -e ~/.cache/impermanence-test/cache-sentinel
test ! -e ~/undeclared-impermanence-test/home-sentinel

test -e ~/Documents/impermanence-test/document-sentinel
test -e ~/.codex/impermanence-sentinel
```

Repeat at least once more.

The physical acceptance condition is:

```text
two consecutive normal reboot cycles:
persistent sentinels survive
ephemeral sentinels disappear
```

---

# 24. Validate actual application state after the home cutover

The persistence model is not complete merely because test files behave correctly.

Open each application whose state was classified `P` or `R`.

For each one verify the state that justified persistence.

Examples:

### Browser / Zen

Verify:

```text
profile exists
expected extensions exist
bookmarks/history if intended persist
authentication cookies/session if intended persist
```

### Codex

Verify:

```text
authentication survives
expected configuration survives
```

### VS Code

Verify:

```text
extensions selected for persistence exist
workspace/user state selected for persistence survives
```

### Android

Verify as applicable:

```text
ADB identity survives
AVDs selected for persistence survive
debug signing identity survives
```

### Steam

Verify:

```text
actual Steam library/profile state is available
no accidental dependence on an undeclared ~/.steam path
```

### Plastic/Unity VCS

Verify:

```text
required identity/auth/config state survives
```

Record any newly discovered required paths in the audit ledger and persistence declaration.

If a new persistent path is discovered:

```text
declare it
copy it from old @home or migration backing tree
rebuild
repeat the reboot test
```

Do not paper over missing state by remounting all of `@home`.

---

# 25. Narrow temporary broad home persistence

If the first transition temporarily persisted broad containers such as:

```text
.config
.local
```

now split them.

For every child:

```text
.config/<child>
.local/bin
.local/share/<child>
.local/state/<child>
```

assign:

```text
E
D
R
P
M
```

The final `home/p2949/persistence.nix` should persist only:

```text
P
and deliberately accepted R
```

Remove `E` and `D`.

Split `M`.

After each narrowing batch:

```bash
nix flake check
sudo nixos-rebuild boot --flake '.#desktop'
reboot
verify applications
```

The home phase is finished only when whole-container persistence exists solely where there is an explicit reason for it.

---

# 26. Prune undeclared migration data from `/persist/home/p2949`

After repeated physical acceptance and application verification, compare:

```text
what exists in /persist/home/p2949
vs
what is actually declared persistent
```

Anything copied there only for migration safety but now classified `E` or `D` should be removed from `/persist`.

Do this only after confirming the original `@home` migration snapshot or source remains available until final retirement.

The goal is not merely hidden junk.

The goal is a persistent backing tree that itself reflects the declared contract.

---

# 27. Begin the `/var` audit

Do not remove the `/var` mount before completing this stage.

Inventory:

```bash
sudo du -xhd1 /var | sort -h
sudo du -xhd2 /var/lib | sort -h
sudo du -xhd2 /var/cache | sort -h
```

Inspect top-level metadata:

```bash
sudo find /var \
    -xdev \
    -mindepth 1 \
    -maxdepth 2 \
    -printf '%y %m %u:%g %s %p\n' \
    | sort \
    > /tmp/var-inventory.txt
```

Review:

```text
/var/cache
/var/lib
/var/log
/var/spool
/var/tmp
```

Also review the previously collected:

```text
/tmp/fatrace-var-writes.log
/tmp/var-btrfs-diff.txt
```

Every mutable service directory that is required across reboot must receive an explicit classification.

---

# 28. Required starting `/var` policy

Use this as the starting policy, then adjust according to the audit.

## Ephemeral by default

```text
/var/cache
/var/tmp
/var/lib/systemd/coredump    unless deliberately retained
generated caches
temporary application indexes
reconstructable transient service state
```

## Explicitly persistent

At minimum evaluate and normally retain:

```text
/var/lib/nixos
/var/lib/systemd/random-seed
```

`/var/lib/nixos` should normally remain persistent because NixOS uses it for persistent system allocation/state that should not be casually regenerated.

`/var/lib/systemd/random-seed` should remain persistent so entropy state is carried safely across boots.

## Already independently persistent

```text
/var/lib/nixos-optimization
```

This remains provided by `@optimization`.

It does not need to be copied into `/persist`.

## Logs

Make an explicit policy choice.

For maximum ephemerality:

```text
journal/logs -> ephemeral
```

If cross-boot forensic logs are intentionally required:

```text
/var/log -> P
```

Do not allow `/var` as a whole to remain persistent merely to retain logs.

## Service databases

Any discovered path such as:

```text
/var/lib/<service>
```

must be classified according to actual use.

If loss changes identity, destroys authoritative data, or breaks intended application behavior:

```text
P
```

If it is regenerated automatically and safely:

```text
E
```

If expensive but reconstructable:

```text
R
```

Unknown is not a final classification.

---

# 29. Extend system Impermanence declarations for `/var`

Edit:

```text
hosts/desktop/persistence.nix
```

Keep the existing explicit root persistence.

Add audited var state.

A likely minimum shape is:

```nix
{ username, ... }:

{
  environment.persistence."/persist" = {
    hideMounts = true;

    files = [
      "/etc/machine-id"

      {
        file = "/var/lib/systemd/random-seed";
        parentDirectory.mode = "0755";
      }
    ];

    directories = [
      {
        directory = "/etc/nixos";
        user = username;
        group = "users";
        mode = "0755";
      }

      {
        directory = "/etc/NetworkManager/system-connections";
        mode = "0700";
      }

      "/var/lib/nixos"

      # Add only audited persistent /var state.
      #
      # "/var/log"
      # "/var/lib/<required-service>"
    ];
  };
}
```

Do not blindly copy this example without comparing it with the completed `/var` audit.

The final declaration is the audit result.

---

# 30. Prepare `/persist/var` data before removing persistent `/var`

Impermanence will create declared backing paths, but migration data must be copied before cutover.

Create a migration backing area if necessary and copy each selected path.

Example for `/var/lib/nixos`:

```bash
sudo mkdir -p /persist/var/lib

sudo rsync \
    -aHAX \
    --numeric-ids \
    /var/lib/nixos/ \
    /persist/var/lib/nixos/
```

Example for logs if logs are intentionally persisted:

```bash
sudo mkdir -p /persist/var

sudo rsync \
    -aHAX \
    --numeric-ids \
    /var/log/ \
    /persist/var/log/
```

For the random seed, preserve metadata without displaying contents:

```bash
sudo install -d -m 0755 /persist/var/lib/systemd

if [[ -e /var/lib/systemd/random-seed ]]; then
    sudo cp \
        --preserve=mode,ownership,timestamps \
        /var/lib/systemd/random-seed \
        /persist/var/lib/systemd/random-seed
fi
```

Check only metadata:

```bash
sudo stat \
    /persist/var/lib/systemd/random-seed \
    2>/dev/null || true
```

Repeat for every `P` and accepted `R` path identified by the audit.

---

# 31. Make `/var` part of the ephemeral root

Edit:

```text
hosts/desktop/disko.nix
```

Remove the active:

```nix
"@var" = {
  mountpoint = "/var";
  mountOptions = btrfsMountOptions;
};
```

Do not physically delete the existing `@var`.

Keep:

```nix
"@optimization" = {
  mountpoint = "/var/lib/nixos-optimization";
  mountOptions = btrfsMountOptions;
};
```

After the change:

```text
/var
```

is an ordinary directory under `@root`.

Therefore it is reset whenever `@root` is reset.

The nested:

```text
/var/lib/nixos-optimization
```

is still mounted separately and persists intentionally.

---

# 32. Add assertions for the final var topology

Enforce:

```text
/var is not an independent persistent filesystem
/var/lib/nixos-optimization is still a deliberate persistent filesystem
```

Add an evaluation assertion/test equivalent to:

```nix
{
  assertion = !(config.fileSystems ? "/var");
  message = "Granular Impermanence requires /var to live inside the ephemeral root.";
}
```

Do not assert that nested `/var/lib/nixos-optimization` is absent; it is intentionally persistent.

---

# 33. Add an automated var Impermanence test

Create a test such as:

```text
tests/storage/impermanence-var.nix
```

The test must prove at minimum:

### Persisted

```text
/var/lib/nixos/<test sentinel>
/var/lib/systemd/random-seed or a test substitute
/var/lib/nixos-optimization/<test sentinel>
```

### Ephemeral

```text
/var/cache/<test sentinel>
/var/tmp/<test sentinel>
/var/lib/<undeclared-test-service>/<test sentinel>
```

Perform multiple boots.

Assert:

```text
persisted state remains
undeclared var state disappears
nested optimization mount remains intact
```

Avoid modifying actual sensitive random-seed semantics in the test; a dedicated fixture path can test file persistence while configuration evaluation separately confirms the real declaration.

---

# 34. Run all offline validation after the var change

Run:

```bash
cd /etc/nixos

nix fmt
nix flake check
```

Build:

```bash
nix build \
    '.#nixosConfigurations.desktop.config.system.build.toplevel' \
    --no-link
```

Run:

```text
root Impermanence tests
home Impermanence tests
var Impermanence tests
existing storage safety tests
reconstruction test affected by the changed Disko layout
```

The blank-disk/reconstruction path must be rerun because the desired disk layout has changed:

```text
@home and @var are no longer part of the intended fresh-install active layout
```

A fresh installation must reconstruct the new topology, not the old one.

---

# 35. Install the var cutover as next boot only

Use:

```bash
sudo nixos-rebuild boot --flake '.#desktop'
```

Before reboot verify:

```bash
findmnt /var
findmnt /var/lib/nixos-optimization

sudo btrfs subvolume list /mnt/btrfs-top \
    | grep '@var'
```

The old physical `@var` must still exist.

Reboot normally.

---

# 36. First physical boot with ephemeral `/var`

Verify:

```bash
findmnt /
findmnt /var || true
findmnt /var/lib/nixos-optimization
findmnt /persist
```

Required result:

```text
/var is not an independent @var mount
/var/lib/nixos-optimization is still @optimization
/persist is still @persist
```

Check persistent paths:

```bash
findmnt -T /var/lib/nixos
findmnt -T /var/lib/systemd/random-seed
```

If `/var/log` was selected for persistence:

```bash
findmnt -T /var/log
```

---

# 37. Prove physical var ephemerality

Create:

```bash
sudo mkdir -p /var/cache/impermanence-test
echo ephemeral \
    | sudo tee /var/cache/impermanence-test/cache-sentinel >/dev/null

sudo mkdir -p /var/tmp/impermanence-test
echo ephemeral \
    | sudo tee /var/tmp/impermanence-test/tmp-sentinel >/dev/null
```

Create a harmless persistent test path only in a deliberately persisted test directory, or use the automated test for `/var/lib/nixos`.

For the independently persistent optimization mount:

```bash
sudo mkdir -p /var/lib/nixos-optimization/impermanence-test
echo persistent \
    | sudo tee /var/lib/nixos-optimization/impermanence-test/sentinel >/dev/null
```

Reboot.

Verify:

```bash
test ! -e /var/cache/impermanence-test/cache-sentinel
test ! -e /var/tmp/impermanence-test/tmp-sentinel

test -e /var/lib/nixos-optimization/impermanence-test/sentinel
```

Verify declared `/var` persistence paths are still present.

Repeat at least once more.

---

# 38. Verify services after ephemeral `/var`

After each physical boot:

```bash
systemctl --failed
systemctl is-system-running
```

Review the current boot for persistence-related errors:

```bash
journalctl -b \
    -p warning..alert \
    --no-pager
```

Search specifically for:

```bash
journalctl -b --no-pager \
    | grep -Ei \
      'permission denied|no such file|failed to start|read-only|persist|mount|var'
```

Any service that fails because previously hidden state was stored under `@var` must be investigated.

Do not solve failures by restoring whole `/var`.

Persist only the exact service state that actually needs to survive.

---

# 39. Validate `persistent-root` recovery semantics

The normal configuration now has:

```text
root + home + ordinary var = ephemeral
```

The existing `persistent-root` specialisation disables root reset.

That means under `persistent-root`:

```text
ordinary root-local home and var state can remain between recovery boots
```

This is acceptable and useful for recovery.

Test it explicitly.

Boot the `persistent-root` specialisation.

Create recovery-only sentinels:

```text
/home/p2949/recovery-root-test
/var/tmp/recovery-root-test
```

Reboot into `persistent-root` again.

They should remain because root was not reset.

Then boot normal mode.

They should disappear because the normal root reset resumes.

Explicitly persisted Impermanence state must survive both modes.

This proves that the specialisation still means:

```text
normal          -> ephemeral root
persistent-root -> retain root for recovery/debugging
```

without reintroducing `@home` or `@var`.

---

# 40. Audit top-level filesystem semantics

After home and var are complete, verify the whole machine.

Use:

```bash
for path in \
    / \
    /boot \
    /dev \
    /etc \
    /home \
    /nix \
    /proc \
    /root \
    /run \
    /srv \
    /sys \
    /tmp \
    /usr \
    /var \
    /persist \
    /var/lib/nixos-optimization \
    /.snapshots
do
    echo
    echo "===== $path ====="
    findmnt -T "$path" || true
done
```

The intended semantics are:

| Path | Final policy |
|---|---|
| `/` | ephemeral normal root |
| `/boot` | persistent |
| `/dev` | runtime virtual filesystem |
| `/etc` | ephemeral except declared persistence |
| `/home` | ephemeral except declared user persistence |
| `/nix` | persistent |
| `/proc` | runtime virtual filesystem |
| `/root` | ephemeral |
| `/run` | runtime tmpfs |
| `/srv` | ephemeral unless explicitly changed later |
| `/sys` | runtime virtual filesystem |
| `/tmp` | ephemeral |
| `/usr` | reconstructed/declarative |
| `/var` | ephemeral except declared state/nested mounts |
| `/persist` | persistent backing store |
| `/var/lib/nixos-optimization` | persistent |
| `/.snapshots` | persistent |

---

# 41. Create a final system-wide reboot sentinel matrix

Before one final normal reboot, create harmless sentinels.

## Must disappear

```text
/root/ephemeral-proof
/tmp/ephemeral-proof
/srv/ephemeral-proof
/home/p2949/.cache/ephemeral-proof
/home/p2949/undeclared-ephemeral-proof
/var/cache/ephemeral-proof
/var/tmp/ephemeral-proof
```

## Must survive

Use safe declared locations:

```text
/persist/ephemeral-project-proof
/home/p2949/Documents/persistent-proof
one declared application-state path
/var/lib/nixos-optimization/persistent-proof
```

Do not modify secret contents merely to test persistence.

Reboot.

Check every sentinel.

The test passes only if **all** expected-disappear paths disappeared and **all** expected-survive paths survived.

---

# 42. Inspect the final persistent backing store

The final `/persist` tree should contain only deliberate state.

Inspect:

```bash
sudo find /persist \
    -xdev \
    -mindepth 1 \
    -maxdepth 4 \
    -printf '%y %m %u:%g %p\n' \
    | sort
```

Compare it with:

```text
hosts/desktop/persistence.nix
home/p2949/persistence.nix
```

Every meaningful subtree beneath `/persist` must have a reason to exist.

Classify unexpected leftovers.

Remove stale migration-only copies after confirming they are not active persistence targets.

The end state must not be:

```text
everything copied into /persist but only some of it mounted
```

It should be:

```text
/persist itself is an intentional state store
```

---

# 43. Update the persistence contract

Update:

```text
docs/persistence-contract.md
```

Replace the old:

```text
/home (@home) -> persistent
/var  (@var)  -> persistent
```

with the final contract.

The document should state:

```text
/                  ephemeral on normal boot
/home              root-local and ephemeral by default
/var               root-local and ephemeral by default
/nix               persistent
/persist           persistent explicit-state backing store
/var/lib/nixos-optimization
                   persistent dedicated subvolume
/.snapshots         persistent
/boot              persistent

home paths          persist only when listed in home/p2949/persistence.nix
system paths        persist only when listed in hosts/desktop/persistence.nix
```

Also document that:

```text
persistent-root disables root reset and therefore temporarily makes
otherwise root-local home/var state persistent for recovery boots.
```

The contract should list path categories, not secret contents.

---

# 44. Make the automated persistence test a permanent regression guard

The finished repository must retain a test that proves the complete contract.

A single combined multi-boot test is preferable once the implementation stabilizes.

It should cover:

```text
root ephemeral state
home ephemeral state
home persistent state
var ephemeral state
var persistent state
nested @optimization persistence
machine-id persistence
persistent-root behavior
normal-mode reset after persistent-root
```

The test should fail if a future change accidentally:

```text
re-adds @home as /home
re-adds @var as /var
removes a required persistence bind
stops resetting root
turns a known-ephemeral path persistent
breaks nested optimization persistence
```

This converts the desired ephemerality into a maintained system invariant.

---

# 45. Retire the legacy `@home` and `@var` persistence mechanism

Do this only after:

```text
all automated tests pass
multiple physical normal boots pass
application state passes
persistent-root passes
the final sentinel matrix passes
/persist is audited
```

First inspect the old subvolumes one final time.

```bash
sudo du -sh \
    /mnt/btrfs-top/@home \
    /mnt/btrfs-top/@var

sudo btrfs subvolume show /mnt/btrfs-top/@home
sudo btrfs subvolume show /mnt/btrfs-top/@var
```

Compare remaining contents with active persistent data.

If no required data exists only in the old subvolumes, mark them safe to retire.

Be aware that deleting them prevents very old NixOS generations whose filesystem declarations require `@home` or `@var` from booting normally.

Therefore the retirement point is also the point at which rollback is intentionally bounded to generations using the new layout.

When that is accepted, delete the old inactive subvolumes:

```bash
sudo btrfs subvolume delete /mnt/btrfs-top/@home
sudo btrfs subvolume delete /mnt/btrfs-top/@var
```

If nested subvolumes are discovered, stop and inspect them rather than using recursive deletion blindly.

Confirm:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top
```

The old always-persistent home/var architecture is now gone.

---

# 46. Remove migration snapshots when they are no longer required

The read-only migration snapshots were created only to make the transition safe.

Once:

```text
old @home/@var have been retired
new persistence contract is accepted
required data exists in /persist
```

the migration snapshots may also be retired deliberately.

Do not let them become an accidental shadow persistence mechanism indefinitely.

List them:

```bash
sudo btrfs subvolume list -p /mnt/btrfs-top \
    | grep 'granular-impermanence'
```

Delete only the specifically identified migration snapshots after final confirmation.

---

# 47. Final source layout

The implementation should leave the relevant source structure approximately:

```text
NixosConf/
├── hosts/
│   └── desktop/
│       ├── default.nix
│       ├── disko.nix
│       ├── ephemeral-root.nix
│       ├── hardware-configuration.nix
│       └── persistence.nix
│
├── home/
│   └── p2949/
│       ├── default.nix
│       ├── persistence.nix
│       ├── cli.nix
│       ├── shell.nix
│       ├── xdg.nix
│       ├── desktop/
│       └── development/
│
├── modules/
│   └── storage/
│       └── ephemeral-btrfs-root/
│           ├── default.nix
│           ├── check.nix
│           └── reset.sh
│
├── tests/
│   └── storage/
│       ├── ...
│       └── granular-impermanence.nix
│
└── docs/
    ├── persistence-contract.md
    └── ephemeral-state-audit.md
```

No additional cleanup architecture is required for this objective.

---

# 48. Final acceptance checklist

The ephemeral-state project is **not complete** until every item below passes.

## Filesystem topology

- [x] `@root` provides `/`.
- [x] no `@home` subvolume is mounted at `/home`.
- [ ] no `@var` subvolume is mounted at `/var`.
- [x] `/nix` remains persistent.
- [x] `/persist` remains persistent.
- [x] `/.snapshots` remains persistent.
- [x] `/boot` remains persistent.
- [x] `/var/lib/nixos-optimization` remains persistent.

## Root

- [x] undeclared `/etc` state disappears on normal reboot.
- [x] `/root` state disappears on normal reboot.
- [x] `/tmp` state disappears on normal reboot.
- [x] `/srv` state disappears on normal reboot.
- [x] `/etc/machine-id` survives.
- [x] `/etc/nixos` survives.
- [ ] NetworkManager connections survive.

## Home

- [x] `/home/p2949` is root-local rather than a separate persistent filesystem.
- [x] `.cache` disappears across normal reboot.
- [x] undeclared home directories disappear.
- [x] declared user data survives.
- [ ] credentials selected for persistence survive.
- [ ] browser profile selected for persistence survives.
- [ ] development/project data survives.
- [ ] stateful development tools selected for persistence survive.
- [x] Home Manager reconstructs declarative configuration.
- [x] `.config` has been audited rather than blindly persisted as a whole.
- [x] `.local` has been audited rather than blindly persisted as a whole.

## Var

- [ ] `/var` is root-local rather than a separate persistent filesystem.
- [ ] `/var/cache` disappears.
- [ ] `/var/tmp` disappears.
- [ ] undeclared service state disappears.
- [ ] `/var/lib/nixos` survives.
- [ ] system random-seed state survives.
- [x] every additional persistent service DB has an explicit justification.
- [ ] `/var/lib/nixos-optimization` survives independently.
- [x] log persistence/ephemerality is an explicit policy rather than a side effect.

## Boot modes

- [ ] normal boot resets root.
- [ ] normal boot therefore resets undeclared home and var state.
- [ ] `persistent-root` disables reset.
- [ ] root-local recovery sentinels survive repeated `persistent-root` boots.
- [ ] returning from `persistent-root` to normal mode discards those undeclared sentinels.
- [ ] explicitly persisted state works in both modes.

## Applications

- [x] Zen/browser required profile state works (actual Firefox confirmed on generation 42).
- [x] Codex required state works.
- [x] VS Code required state works (user confirmed on generation 42).
- [ ] Android state selected for persistence works.
- [x] Steam state selected for persistence works (actual library/game saves confirmed on generation 42).
- [ ] Plastic/Unity VCS state selected for persistence works.
- [ ] any other path classified `P` or `R` has been functionally checked.

## Tests

- [x] `nix fmt` passes.
- [x] `nix flake check` passes.
- [x] desktop system builds.
- [x] home multi-boot test passes.
- [x] var multi-boot test passes.
- [x] combined granular-Impermanence regression test passes.
- [x] changed Disko layout passes reconstruction testing.
- [ ] physical repeated-boot sentinel tests pass.

## Persistent storage hygiene

- [ ] `/persist` has been audited.
- [ ] no unexplained full-home migration copy remains.
- [ ] no unexplained full-var migration copy remains.
- [ ] old active `@home` persistence has been retired.
- [ ] old active `@var` persistence has been retired.
- [ ] obsolete migration snapshots have been deliberately handled.
- [ ] `docs/persistence-contract.md` describes the final actual state.

---

# 49. Definition of done

At the end of this plan, the machine should obey this rule:

```text
NORMAL BOOT

@root is replaced
        │
        ├── /etc       clean
        ├── /root      clean
        ├── /home      clean
        ├── /srv       clean
        ├── /tmp       clean
        └── /var       clean
              │
              └── except /var/lib/nixos-optimization separate mount

NixOS activation
        │
        ├── reconstructs declarative system state
        └── bind-mounts explicitly persisted system state

Home Manager activation
        │
        ├── reconstructs declarative user configuration
        └── bind-mounts explicitly persisted user state

result:
    undeclared mutable state does not survive reboot
```

Persistent state is reduced to deliberate islands:

```text
/boot
/nix
/persist
/.snapshots
/var/lib/nixos-optimization

plus paths explicitly exposed from /persist by Impermanence
```

The project is complete when persistence is no longer determined by:

```text
"this happened to live under /home"
or
"this happened to live under /var"
```

and is instead determined by:

```text
"this state was explicitly audited, classified, and declared persistent."
```

That is the final granular ephemeral model.
