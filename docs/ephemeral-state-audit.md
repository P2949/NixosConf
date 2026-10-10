# Ephemeral state audit

Initial inventory 2026-10-08; finalized storage policy 2026-10-09 on
`feat/granular-impermanence`. This audit records categories/reasons, never secrets.
Generation46 normal has root-local home/var and a physically accepted allow-list.
Corrected normal/recovery/recovery/normal and post-pruning normal pass; Fuzzel
history, Unity editor preferences and user-selected expensive caches persist.
Raw backing pruning and deliberately certified legacy/snapshot retirement are
complete. The [granular plan](https://github.com/P2949/NixosConf/blob/nixos-26.05-pre-optimization-baseline/NixOS_Granular_Ephemeral_State_Implementation_Plan.md)
retains the complete migration chronology and private-receipt identities.

Classes: `P` authoritative state, `R` deliberately retained expensive rebuilds,
`D` declarative reconstruction, `E` disposable runtime/cache data, `M` mixed
containers whose children are classified separately. A `P` application profile
does not make its known cache children persistent.

## Evidence and migration

Privileged metadata, write traces and private receipts are retained under
`/persist/granular-migration`. Initial metadata-preserving copies and orderly
quiesced allow-list synchronizations passed before the staged home/var cutovers.
The original whole-home safety copy is transformed into declared backing with
all audited undeclared residue removed. Legacy sources and four specifically
confirmed migration snapshots are retired; small evidence remains. This is
completed historical migration, not an active whole-home/whole-var mechanism.

The 600-second write trace identifies Firefox, VS Code, Codex, Thunar and
WirePlumber. Events resolve through top-level Btrfs paths, not only `/home` and
`/var` aliases. Duplicate filesystem-watch warnings and process-exit races mean
the trace is observational evidence, not complete coverage. No-data Btrfs diffs
capture changed paths independently. Unity, Unreal, Blender and Steam functional
sessions were not established by that trace; the user subsequently confirmed
important real application workflows on 2026-10-09. Required post-trial application rechecks are accepted. The user uses all these apps; Android Studio is planned, with
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
compared without printing contents. The historical final-sync tool performed both migrations after applications
stopped, using the new path when it already existed. It is retired from current source.

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
`VR-AR-project-2` is empty except for cache mount scaffolding. The user later
intentionally cleared Trash, explicitly confirming discard of its old Library
and deleted assets/settings/git/documents before legacy retirement. This supersedes the earlier absence-of-Assets observation.
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
| share/PrismLauncher | M | Private account/settings, instances/worlds/mods and customization remain authoritative P; assets/libraries remain retained R. Observed root cache/feed and launcher logs are disposable E and have candidate reset-root exclusions; physical reboot proof is pending in the [Prism plan](prism-launcher-plan.md). Meta, translations, metacache and other children remain retained until separately classified; no launcher-managed Java directory was observed. |
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
- Prism Launcher: first real Fabric and separate vanilla26.3 worlds were joined
  and saved. Root `cache/feed/feed.xml` and launcher logs are observed disposable
  data, consistent with upstream [data locations](https://prismlauncher.org/wiki/getting-started/data-location/).
  Only root `cache` and `logs` have reset-root mounts. Instance worlds,
  mods, settings, assets/libraries and all unclassified children remain retained.
  Normal reboot proved parent persistence, reset of both root-local source
  markers and exact retained file hashes. Cache/feed and launcher logs have
  regenerated; final post-reboot interactive world acceptance remains pending.

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

Fuzzel history was restored and migrated to `.local/state/fuzzel/history`;
the user confirms usage ordering. The generation 44 home chain and final
corrected generation 46/post-pruning trials accept this dedicated state path.
No cache-backed history workaround is required in the finished configuration.

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

## /persist hygiene and acceptance scope

`/persist/etc` and `/persist/var` contain declared system backing;
`/persist/home/p2949` contains declared user backing and intentional empty cache
mountpoint scaffolds. `/persist/secrets` retains the private password source.
All 49 top-level purposes are classified. Earlier backup-staging snapshots,
validation receipts, alternate repository checkouts and forensic identity/root
artifacts are deliberately retained under separate readiness recovery gates.
Tiny archived Unity preference versions and three opaque runtime preference
files have explicit recovery-evidence purposes, not runtime persistence.

Cache mounts propagate into apparent live `/persist` paths. Pruning used a
private, non-recursive raw `@persist` view; it removed 55 verified E/D residue nodes
and emptied 82 hidden cache targets while preserving active mount identities,
every declared backing path and all nine Unity preference files. Independent
read-only re-audit found no undeclared residue or hidden cache data. Boot-managed
files remain governed by their normal boot rules. Allocation totals do not imply
reclaimed bytes because reflinks/snapshots can share extents.

The corrected final chain and post-pruning normal pass all 100 proofs. Actual
browser/Codex/VS Code/Git/Steam and Unity/Unreal state is user-confirmed; Blender
configuration/render/editing has accepted evidence. All 18 old IndexedDB blobs
are superseded and unreferenced in healthy current DBs. Old Trash discard is
explicitly confirmed. All 85,721 old-only paths are classified into 16 groups,
with no required authoritative data left only in legacy home. Legacy home 256,
var children263/264/266 and parent 261, and the four confirmed migration snapshots
326/327/328/329 are retired. Unrelated backup/forensic state remains intentional.

Android Studio is absent: audit its SDK/AVD and tool state after installation.
Existing ADB keys persist; remote-device functionality is currently unexercised.
Plastic's empty directory and future credential/data reservations are deliberate
but cannot establish a current remote workflow. Current Unity Libraries and
installed editors/runtimes are retained R state; old versions need not remain
when current accepted versions replace them. Future applications/projects need
fresh path audits rather than whole-container persistence.

The October 8 copied-editor fixture leaked Zen runtime IPC into the host. Proven
unused records were archived/removed; the fixture now isolates IPC and `/dev/shm`.
The user's actual relaunch is accepted: Zen 0.058s, editor 12.612s, no errors.
Production policy and expensive Zen/DDC retention were unchanged. Earlier
fixture evidence is not retroactively treated as proof of full IPC isolation.

The plan records exact private receipt names for pruning, physical proofs,
semantic reconciliation and deliberate retirement. Final source freeze/local
suite/CI integration remains a repository-release task, not another migration
or a reason to repeat accepted human-observation gates.
