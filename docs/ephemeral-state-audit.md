# Ephemeral state audit

Inventory date: 2026-10-08. Source branch: `feat/granular-impermanence`.
This ledger records paths, classifications and policy, never credential contents.
Generation 45 persistent-root is running with home and var on the retained root.
Both final recovery trials pass all 100 proofs with the same root/reset count;
return-normal is prepared but not yet accepted.
Its verified var-only shutdown copy, first final physical matrix, discovery and
user application recheck pass; both policies are frozen. Generation 42's first
home matrix passed, including all 82 cache exceptions. Both accepted generation-44 recovery trials passed
all 100 markers with unchanged root identity and healthy services. Earlier
cleanup-related failed attempts remain archived and unaccepted. The updated
proof tool passes eight regressions. Both normal trials pass all 100 requirements,
with roots 330 → 332 → 334. The independent home guard and user application
recheck pass; home policy is frozen. Exact-source final-var validation passes,
including fresh VM runs. Final generation 45's first normal receipt is
`physical-boot-passed-f0309ac2-5ee1-49c5-96a6-ae7610598589.json`: 92 disposable
proofs gone, eight persistent proofs retained, new root 336 and reset count 22.
Recovery → recovery → normal, raw-backing pruning, post-pruning normal proof,
legacy retirement and final source/CI remain gated.
Fuzzel history is restored
and verified in its persistent state directory; no agent reboot is scheduled.
The active work record is [the granular plan](../NixOS_Granular_Ephemeral_State_Implementation_Plan.md).

Classes: `P` authoritative state, `R` deliberately retained expensive rebuilds,
`D` declarative reconstruction, `E` disposable runtime/cache data, `M` mixed
containers whose children are classified separately. A `P` application profile
does not make its known cache children persistent.

## Evidence and migration

Privileged metadata inventories and mount/subvolume/usage receipts are stored
under `/persist/granular-migration`, protected by 0700/0600 modes. Before snapshots
were made at `20261008-104128`; after snapshots at `20261008-110009`. A full
metadata-preserving reflink home copy from the immutable before snapshot passed
an itemized rsync dry run with no differences. It is a temporary safety copy;
applications subsequently changed state; the orderly shutdown performed and
verified a fresh allow-list copy before selecting generation 42. `/var` selected
data was separately copied and compared and must be resynchronized for its later
cutover. Originals and snapshots remain intact.

The 600-second write trace identifies Firefox, VS Code, Codex, Thunar and
WirePlumber. Events resolve through top-level Btrfs paths, not only `/home` and
`/var` aliases. Duplicate filesystem-watch warnings and process-exit races mean
the trace is observational evidence, not complete coverage. No-data Btrfs diffs
capture changed paths independently. Unity, Unreal, Blender and Steam functional
sessions were not established by that trace; the user subsequently confirmed
important real application workflows on 2026-10-09. Recheck state after the next
physical trials. The user uses all these apps; Android Studio is planned, with
ADB keys already present.

## Home top-level entries

| Paths | Class | Decision |
| --- | --- | --- |
| Desktop, Documents, Downloads, Development, Music, Pictures, Public, Templates, Videos | P | Retain all user data, including Downloads; 114 GiB Development contains source/project data |
| Unity user templates, Unreal Projects | P | Project/template defaults may receive new authoritative data even though currently empty |
| Unity | R | 18 GiB imperatively installed editor versions; deliberately retain |
| .ssh, .gnupg | P | Future credentials; absent at inventory, create protected empty directories declaratively |
| .pki | P | NSS/certificate state, protected directory |
| .android | M | ADB/debug identity and future AVDs retained; cache and adb.5037 runtime state discarded |
| .codex | M | Authentication, config, goals, queue, threads, memories, sessions, attachments, plugins, skills retained; cache/temp/IPC/locks/shell snapshots and model-cache/diagnostic log DB reset |
| .plastic4 | P | Unity VCS credentials/settings; currently empty |
| .zen | E | Invocation metadata identifies the Unreal engine's `Engine/Binaries/Linux/zen`; History/States are server invocation/runtime bookkeeping, not the browser profile or retained Zen data cache |
| .vscode | P/R | Editor argv and extension inventory/builds; CLI installation/state retained; VS Code generated caches are separately discarded |
| .vscode-shared | M | sharedStorage/state.vscdb and SQLite companions retained; no other observed child |
| .dotnet | M | corefx/cryptography retained; future tools require a separate audit; generated CLI state is disposable |
| .epic | E | Only UnrealBuildAccelerator CAS/temp/session cache was observed |
| .steam | M | Runtime pipe/PID/token and generated launcher symlinks/registry/exported settings; actual profile and library under .local/share/Steam retained; verify launcher reconstruction physically |
| .steampid, .steampath | E | Generated aliases into Steam runtime |
| .cache, .dbus | E after history migration | Runtime/cache state; Fuzzel launch history was the discovered exception and is moved into explicitly persisted state/fuzzel |
| .nix-defexpr, .nix-profile, .local/state/nix | D/E | Legacy channel/profile aliases; profiles directory empty, current packages are declared by NixOS/Home Manager |
| .icons, .gtkrc-2.0, .zshenv | D | Observed Home Manager store symlinks |
| .vim, .viminfo | E | Only netrw/recent editing history observed; no user configuration or plugins |
| Library, UnrealEngine | E | Only Unreal build logs and trace-server logs/store observed; no project/assets |
| .gitconfig | P, migrated | Contents move to .config/git/config under a persisted directory; Git uses its standard XDG path and can atomically save global settings |
| .zshrc | P | Existing manual legacy configuration retained; Home Manager owns separate .config/zsh files |
| .bash_history, .histfile, .zsh_history | P | Explicit choice to retain historical commands |
| .pulse-cookie | P | Audio authentication identity |
| .config, .local | M | Never persisted as whole containers; children below |

Zsh's active history moves from `.config/zsh/.zsh_history` to
`.local/state/zsh/history`. Its containing directory is persisted, allowing
atomic saves. The existing history was copied before changing the declaration.
Existing Git configuration was likewise copied to `.config/git/config` and
compared without printing contents. The final-sync tool repeats both migrations
after applications stop, using the new path when it already exists.

## .config children

The project trees beneath `Development` are mixed too. Unity's observed project
`Logs` and `Temp` directories and Unreal's `AI_Gavin_Project/Intermediate`,
`Saved/Logs`, `Saved/ShaderDebugInfo` and `Saved/UnrealBuildTool` reset. Source,
Assets, Packages, ProjectSettings/UserSettings, Unreal Content/Config, autosaves,
collections and installed engine binaries remain retained. The user explicitly
selected retaining both Unity Libraries (class R): the older `VR-AR-project` has
no Assets directory, so deletion might also lose recovery material.
The actual Unity and Unreal project exception paths are in the same application
exception list as profile caches; new projects require an audit and declaration.

After the user's pre-reboot file transaction, the inactive original and active
persisted trees both contain Assets/Library under `VR-AR-project`;
`VR-AR-project-2` is empty except for cache mount scaffolding, and a Library is in
retained Trash. This supersedes the earlier absence-of-Assets observation.
Libraries remain class R; the migration follows the user's actual file changes
and does not restore old project layouts without a reason.

Official references: [Unity project directories](https://docs.unity.com/en-us/engine/6000.5/manual/get-started/project-configuration/default-directories)
and [Unreal directory structure](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-directory-structure?lang=en-US).

| Paths | Class | Decision |
| --- | --- | --- |
| alacritty, environment.d, fontconfig, fuzzel, gtk-3.0, gtk-4.0, hypr, starship.toml, systemd, user-dirs.conf, user-dirs.dirs, uwsm, zsh | D | Reconstructed by Home Manager; zcompdump is disposable and active history uses the new state path |
| mpv | E | Empty; no authoritative state observed |
| btop | P | Existing manually edited preferences and any custom themes |
| blender | P | Per-version userpref.blend, bookmarks, recent files and scripts; current 5.1/5.2 folders contain configuration only |
| gh | P | GitHub CLI authentication/configuration, private mode |
| StardewValley | P | Game saves outside the Steam library |
| dconf, Thunar, pulse | P | Desktop/file-manager/audio preferences |
| mimeapps.list | D | Observed text/markdown association with code.desktop is now reconstructed through Home Manager |
| pavucontrol.ini | E | Window geometry/filter/meter UI preferences only; audio device routes remain separately persistent |
| git | P | Global Git configuration in a writable containing directory |
| Code | M | User/global/workspace state, unsaved Backups, cookies, identity, extensions' storage retained; cache exceptions listed below |
| mozilla/firefox | M | profiles.ini, profile groups, passwords, cookies, bookmarks/history, extensions, sessions and site storage retained; cache/crash/telemetry exceptions below |
| unityhub | M | Account/storage, install-state database, project registry, preferences, Templates and resumable editor installation payloads retained; cache exceptions below |
| unity3d/Unity/config, unity3d/Unity/licenses | P | Licensing configuration/identity; sibling Licensing.Client logs discarded |
| unity3d/Preferences | P | User explicitly requests preserving editor layouts, search filters and overlay settings; protected backing identified during the final raw-persist audit |
| Unreal Engine | P | UnrealBuildTool/BuildConfiguration.xml is authoritative configuration |
| Epic | M | App-scoped parent retained for atomic account/settings/project-record updates; exact directory/file exceptions reset generated state |
| Epic/Epic Games, Epic/ProjectEditorRecords | P | Account/settings and recent project records |
| Epic/UnrealEngine | M | Engine install registry, editor layouts/preferences, Content, collections/autosaves and authentication state retained; intermediate/log/cache exceptions below |
| Epic/UnrealBuildTool, Epic root lock/analytics/generated files | E | Build logs reset via root-backed directory; known process/server/asset-registry lock files removed by boot-only rules |

## .local children

| Paths | Class | Decision |
| --- | --- | --- |
| share/Steam | M | Library/manifests, client installation, configuration, userdata, saves and compatdata retained; disposable cache children below |
| share/keyrings | P | Future desktop credential stores, private mode; absent initially |
| share/Trash | P | Potentially recoverable user files, retained conservatively |
| share/applications, share/icons/hicolor | P | User/game launchers and icons |
| share/icons/default, share/icons/Adwaita, share/dbus-1 | D | Home Manager links |
| share/gh, state/gh | P/R | CLI device identity, extensions and extension state |
| share/gvfs-metadata | P | File-manager metadata can contain user-set attributes |
| share/unity3d, share/unityhub | P/R | Licensing/preferences and helper installation |
| state/wireplumber | P | Selected audio routes/profiles and stream preferences |
| state/.copilot | P | Editor AI assistant state |
| state/zsh | P | Active atomic-save shell history |
| state/fuzzel | P | Launcher usage counts and user ordering; migrated from the misleading `.cache/fuzzel` default; private directory supports normal/atomic updates |
| share/flatpak | E | Only empty database directory; no installed Flatpak apps observed |
| share/hyprland, share/recently-used.xbel, state/lesshst | E | Nag/runtime/recent document/pager state; deliberately disposable |
| share/vulkan | D/E | Steam-generated overlay layer registration; validate regeneration with Steam |
| state/home-manager, state/.keep | D | Home Manager activation/GC metadata and declarative marker |

## Disposable children of persisted profiles

The exact directory exceptions are executable declarations in
[`ephemeral-app-state.nix`](../home/p2949/ephemeral-app-state.nix). Each is a bind
mount from the ordinary reset-root `.cache/ephemeral-app-state` tree. Profile
parents remain writable and apps can still atomically replace settings/SQLite
files. Recovery boots retain the same root-local cache tree. Hidden migration
copies below those mountpoints must be pruned after physical acceptance.

- Firefox: normal XDG `.cache/mozilla/firefox` already disappears. In-profile
  cache2, startupCache, shader-cache, thumbnails, crashes, minidumps and telemetry
  directories also disappear, as do root Crash Reports/Pending Pings/mpris data.
  The observed profile is `y34aofre.default`; new profiles require an audit and
  matching exception entries. Keep `storage`, sessionstore-backups, cookies,
  places, keys/certificates and extension data: these hold actual website/user
  state, even when a website uses the word cache. Mozilla distinguishes profile
  root and local cache paths in its [profile service documentation](https://firefox-source-docs.mozilla.org/toolkit/profile/index.html)
  and documents [HTTP cache2](https://firefox-source-docs.mozilla.org/networking/cache2/doc.html).
- VS Code: Cache, CachedData/configurations/profiles/VSIX downloads, Code Cache,
  Crashpad, Dawn/GPU caches, logs, blob buffers, Service Worker caches and shared
  dictionary cache disappear. User/workspace/globalStorage, extensions, backups,
  Local/Session Storage remain. Microsoft's [user-data copy filter](https://github.com/microsoft/vscode/blob/main/.github/skills/auto-perf-optimize/scripts/userDataProfile.mts)
  independently identifies generated cache categories; workspace storage is not
  classified as a disposable cache here.
- Codex: cache, temp directories, IPC, locks and shell snapshots disappear.
  Native boot-only tmpfiles rules discard models_cache.json and the complete
  logs_2.sqlite diagnostic bundle (main, WAL, SHM) before login. Authentication,
  queue/goals/thread/state/memory DBs and their companions remain together.
- Unity Hub: Electron render/code/GPU/crash caches, logs, sentry, graphql cache,
  video decoder statistics and service-worker/dictionary caches disappear.
  Download/install-state is retained so a reboot does not lose resumable installs.
- Unreal: Intermediate trees, per-version Saved/Logs and ShaderDebugInfo,
  Common/Analytics, and embedded-browser render/HTTP/code/dictionary caches
  disappear. Web storage/cookies in the apparent webcache directory remain;
  deleting that whole directory could lose sign-in state.
- Steam: appcache, depotcache, logs, avatars, embedded-browser render/HTTP/code
  caches, temporary downloads/install staging and message caches disappear.
  Never discard compatdata: Proton prefixes may contain saves and settings.
  Library manifests remain writable inside the retained library parent.

Deliberate `R` exceptions: Steam's 218 MiB shadercache and Unreal's approximately
831 MiB shared DDC/Zen cache plus the small per-version DDC are reconstructable
but retained to avoid shader compilation/asset rebuild delays. Both Unity project
Libraries are explicitly retained at the user's request; logs/temp reset.
Installed Unity editors, Steam binaries/games and editor extensions are also deliberate `R`.
These are explicit performance choices, not unidentified persistent state.
The user explicitly chose to keep the quantified Steam/Unreal caches persistent
when offered the option to reset them every boot on 2026-10-08.

Known disposable files and boot-only behavior are in
[`ephemeral-app-files.nix`](../home/p2949/ephemeral-app-files.nix). File-level
exceptions use native tmpfiles removal, rather than file bind mounts that would
block atomic saves. Rules are absent in `persistent-root` and ignored by live
tmpfiles reactivation because they are boot-only (`r!`).

Fuzzel history omission found on 2026-10-09: recoverable original eight records
and three post-cutover records were merged into eight IDs. Source now configures
`${xdg.stateHome}/fuzzel/history` and persists `.local/state/fuzzel` only. The user
confirmed restored usage ordering. The temporary live `.cache/fuzzel` symlink
writes into the same backing until the corrected home candidate boots. That
candidate is built/checked/installed boot-only as generation 44; the four-boot
home sequence is still required before cleanup;
legacy cache/history copies remain safety evidence until then.

## /var classification

| Paths | Class | Decision |
| --- | --- | --- |
| lib/nixos | P | Preserve uid/gid/subuid allocation and declarative account state |
| lib/systemd/random-seed | P | Entropy seed, retain protected original metadata |
| lib/NetworkManager | M | Enclosing directory retained for atomic identity/internal-settings updates; leases/timestamps/seen-bssids removed by boot-only rules in normal mode |
| lib/bluetooth | P | Pairing identity and trust, mode 0700 |
| lib/btrfs | P | Scrub progress/history |
| lib/nixos-optimization | P | Separate @optimization mount; never copied under /persist |
| lib/systemd/coredump, pstore, catalog, rfkill, timers, timesync, linger, ephemeral-trees | E/D | Diagnostics/generated runtime state; no imperative lingering users observed |
| lib/misc, lib/udisks2, lib/private, lib/machines, lib/portables | E | Empty/runtime; containers must be explicitly persisted before future use |
| lib/lastlog, lib/logrotate.status, db/sudo | E | Login/accounting/log rotation/sudo timestamp state |
| cache, tmp, spool, log, log/private, log/journal | E | Reset ordinary root-local data; journal explicitly volatile |
| empty, lock, run, .updated | D/E | System-managed directory/runtime symlinks/marker |

Upstream tmpfiles ordinarily creates machines/portables/var-tmp as Btrfs
subvolumes. Overrides preserve the upstream rules but create ordinary
directories; otherwise the strict root-reset descendant guard correctly refuses
the second boot. No reset guard is weakened or recursively broadened.

## /persist hygiene and remaining gates

`/persist/etc` holds explicit machine/repository/network state; `/persist/secrets`
holds the existing password source. `/persist/home/p2949` currently includes a
full temporary home migration copy, and `/persist/var` only selected system state.
`/persist/granular-migration` holds this migration's private evidence. Existing
backup-staging snapshots, validation receipts, alternate repository checkouts and
pretrial identity/reset artifacts are preexisting migration/recovery evidence,
not active whole-home or whole-var mounts. Inventory these and retire them only
after their separate recovery/backup gates are satisfied.

The user confirmed on 2026-10-09 that actual browser, Steam, VS Code, Git/GitHub,
relevant VCS and Unity/Unreal project workflows are working after the home cutover
on generation 42. Generation 44 normal is now live with a new root identity
after accepted recovery → recovery → normal → normal and healthy services. An earlier strict trial remains unaccepted because
Codex deleted an unknown plain shell-snapshot proof file. The installed binary
reproduces this cleanup. A corrected nested marker, seven regressions and a fresh
100-marker recovery test now supplies the first accepted recovery receipt. The
initial second recovery attempt was rejected after Firefox telemetry cleanup,
with later MPRIS artwork cleanup removing another proof. It remains unaccepted.
The specific telemetry proof fix passes eight regressions. The replacement
second recovery passed all 100 markers after immediate postboot verification.
Both normal trials pass all 100 requirements with root replaced. Independent
home acceptance and the user application recheck pass; home policy is frozen.
Corrected generation-44 physical/recovery and final-var gates still need
their own acceptance; no further synthetic app QA is required without a defect.

The first home copy/boot and offline validation passed. Codex reads its retained
login, and Firefox starts from a private offline profile copy with bookmarks
intact. Unity loads a private retained-project/profile copy, compiles scripts and
exits successfully without changing the real project. Unreal loads the retained
compiled module and default map with zero map errors/warnings and exits normally
from a private copy. These copied-state checks
do not certify full interactive or remote-service workflows. Remaining gates are
repeated physical home/recovery acceptance, remaining
application checks, var-only quiesced synchronization/cutover, the final physical
sentinel matrix, backing-store pruning and deliberate legacy retirement.

The October-8 editor fixture had incomplete IPC isolation: private PIDs were
written into host POSIX shared memory, causing an 85-second Zen startup timeout
on the user's later launch. This was corrected on October 9 by archiving/removing
the two proven-unused Zen runtime records and adding both a private IPC namespace
and private `/dev/shm` tmpfs to the fixture. The corrected copied-project check
passes with host Zen IPC unchanged. The user's actual relaunch is accepted:
Zen initialization 0.058 seconds, editor startup 12.612 seconds, zero error lines,
and user confirmation of normal startup. Zen/DDC caches remain retained; no
production persistence declarations or launch wrapper changed. Historical fixture
startup/project-integrity evidence does not certify complete host IPC isolation.

Shared mount propagation mirrors cache overlays into the apparent `/persist`
backing paths. Inventory and eventual pruning must inspect a non-recursive raw
`@persist` view in a private mount namespace; deleting through the live overlay
can affect an active cache. A read-only raw-view inventory identified 56
undeclared residue paths, 82 hidden cache directories and 5 boot-managed file
exceptions. All 49 top-level persist entries have recorded purposes. The private
inventory is `backing-pruning-inventory.json` under the migration evidence
directory. Allocated sizes include shared reflink/snapshot extents and do not
estimate reclaimed space. No backing data was deleted; physical gates still
prevent pruning.
