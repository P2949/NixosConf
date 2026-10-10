# Minecraft server operations

The Minecraft server and local Btrfs recovery system are deployed on the
physical desktop. Live snapshot creation, failure recovery,
retention and a playable isolated local restore have passed. Reboot persistence,
pregeneration and isolated IPv4/IPv6 host ingress passed. Ordinary calendar activation acceptance is a user-approved post-merge observation;
genuine missed-event catch-up is a user-approved post-merge observation;
the unavailable laptop path is a recommended later operational smoke test.
Permanent operating policy is recorded here; PR metadata owns exact
qualification and acceptance receipts.

## Architecture and modes

NixOS manages the server through nix-minecraft and systemd in `minecraft.slice`.
Normal mode pins Minecraft Java Edition 26.3, Fabric loader 0.19.5, OpenJDK 25 and
`-Xms1G -Xmx6G`. Fabric API, Lithium, FerriteCore, ServerCore and spark are the
normal mod set. Empty-server pause is 60 seconds. The server uses
`/srv/minecraft`, declared as the separate Btrfs `@minecraft` mount; recovery
snapshots live beneath `/.snapshots/minecraft` on the `@snapshots` mount of the
same filesystem. Disko describes intended topology, not current physical state.

`minecraft-pregen` inherits the same server, management and security baseline,
adds Chunky, and sets `pause-when-empty-seconds=-1`. Its backup timer is masked,
and has no `timers.target` link. The manual backup service remains available.
The live transition and bounded Chunky generation have passed. Inspect the selected generation's `specialisation/` directory
and use the explicitly approved specialization activation procedure. Do not
start the normal timer manually in pregen mode. Take a manual recovery point
before planned bulk generation and after completion if appropriate.

The Java service has Nice 5, MemoryHigh 8G and MemoryMax 10G; the slice has CPU
and I/O weights 50. Backup runs at Nice 10 with CPU/I/O weights 25 and a 20-minute
outer timeout, so it yields to foreground workstation work.

## Management endpoint

MSMP is WebSocket JSON-RPC at `ws://127.0.0.1:25585`. The bearer secret must be
exactly 40 ASCII alphanumeric characters and is loaded from
`/persist/secrets/minecraft-management.env`. TLS is disabled under the explicit
host-loopback-only assumption; the management port is not opened in the
firewall, allowed origins are empty, and RCON is disabled. The client rejects
non-loopback endpoints and requires capability discovery before a backup.

The real secret must be created only during physical bootstrap, never in Git,
backup metadata, screenshots or logs. The game port is TCP 25565, with online
mode and enforced whitelist enabled. Management is local; game access and the
whitelist is enforced. Local player access and IPv4/IPv6 host ingress passed;
the laptop's actual network path remains unexercised.

Official protocol references:
[Minecraft management introduction](https://feedback.minecraft.net/hc/en-us/articles/39107188599565-Minecraft-Java-Edition-Snapshot-25w35a),
[discovery and management](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9),
[26.3 release notes](https://feedback.minecraft.net/hc/en-us/articles/48913133328013-Minecraft-Java-Edition-26-3).
The repository pins a particular runtime; these links do not substitute for a
trace of that runtime's actual methods, result types and notifications.

## Snapshot transaction

One service and one timer use the same nonblocking exclusive flock. A concurrent
CLI attempt refuses overlap. The lock is `/run/minecraft-backup/backup.lock`.
An abandoned autosave recovery marker is handled before unrelated metadata or
filesystem work. Then the runner validates versioned persistent state,
checks source/snapshot mounts and filesystem identity, reconciles earlier pending
capture/deletion, and preflights the protected snapshot directory and unused
destination. It waits for read-only MSMP readiness before recording capture intent.

After readiness it atomically records the intended destination and source
filesystem UUID. The separate transaction connection rediscovers capabilities,
then reads the original autosave state. If autosave was enabled, it creates the volatile marker before disabling
it. The client performs a transport/save fence, requests a flushed save, observes
`saving` then `saved`, and creates one read-only Btrfs snapshot. It restores the
original autosave state and clears the marker only after confirmed restoration.
If autosave was already disabled, that original state is preserved.

The disabled-autosave section contains no persistent-state parsing, registration,
retention or unrelated directory work. After autosave restoration, a bounded
`btrfs filesystem sync /.snapshots` makes the durability boundary explicit.
Snapshot identity and `ro=true` are then verified. Sync failure preserves pending
capture without advancing last success; reconciliation syncs again before adoption.
The manifest is made durable before pending state is cleared and last success is updated. Retention runs afterward.

The notifications have no proven per-save correlation identifier in this
client. The fence prevents an already-unread stale pair from satisfying a new
save barrier. A delayed notification arriving after the fence remains a behavior
to verify on the real 26.3 server. Simulated tests prove the client ordering,
not stronger live consistency guarantees.

## Persistent metadata and health

| Path | Purpose | Permissions |
| --- | --- | --- |
| `/persist/minecraft-backup` | Backup control state | root:root 0700 |
| `state.json` in that directory | Pending capture/deletion, last attempt, last successful capture, last retention | root:root 0600 |
| `managed-snapshots.json` in that directory | Explicit ownership allow-list with filesystem and subvolume UUIDs | root:root 0600 |
| `/run/minecraft-backup/autosave-needs-restore` | Interrupted current-runtime autosave transaction | root:root 0600 |
| `/var/lib/systemd/timers/stamp-minecraft-backup.timer` | Last scheduled activation time | Exact file persisted through Impermanence |

Both JSON documents use `schema_version=2`. Unknown versions, duplicate keys,
invalid fields, duplicate identities, unsafe paths and unsuitable file ownership
or modes cause refusal. Missing files define the first-run empty state; losing
one established document does not silently reset its corresponding history.
Unknown snapshots are not adopted by scanning names.

JSON writes use a mode 0600 temporary file in the same directory, complete JSON
plus a newline, file fsync, atomic replacement and directory fsync. A failure
before replacement preserves the old document. A failure after replacement may
have published the new complete document; the service still reports failure,
and a later run reloads the durable state. Stale temporary files are ignored.

`pending_snapshot` is durable transaction intent. The owned mode 0700 unmounted
snapshot root is checked before inspecting the child. If its path is absent, the
attempt is recorded as aborted and pending is cleared. If it exists, the runner
requires a direct child, no symlink or separate mount, the expected filesystem
UUID, a valid subvolume UUID and `ro=true`. It registers a verified unregistered
pending snapshot, or confirms an already registered record and finishes the
interrupted state update. A mismatch preserves evidence and refuses new work.

The volatile marker remains until autosave recovery succeeds. It intentionally
lives under `/run`; pending ownership information survives reboot under
`/persist`. Tmpfiles creates the runtime directory without removing it when the
oneshot service stops. `ExecStopPost` attempts recovery after an unexpected exit
or an execution-stage startup failure. Fresh-connection recovery and save waits
are bounded. Process-termination autosave recovery passed live injection.
Abrupt power-loss testing remains unexercised and is outside the integration gate.

Status is read-only and does not connect to Minecraft, initialize files,
reconcile pending state or run retention. It prints schema/health state,
last success, pending capture, retention outcome and managed count. It returns
nonzero on malformed metadata or health requiring attention: unresolved capture
or deletion, recovery marker, failed attempt/retention, inconsistent last-success
ownership, empty established manifest, future success time, or success older
than 13 hours. Age and the six-hour expected interval are included. An empty
first-run state is reported as uninitialized with exit zero. Status does not
verify live Btrfs identity; it evaluates the stored ownership and current clock. Error strings from transports and peers are not
copied into persistent health or printed by the backup CLI; failure diagnostic fields accept only fixed, recognized values, and diagnostics use
recognized stages and fixed messages to avoid exposing a bearer secret.

Do not manually edit backup metadata while a run is active. Do not reset a
malformed manifest to empty, adopt an unknown snapshot from its name, or repair
an identity mismatch by deleting the object.

## Retention and scheduling

The policy keeps the newest **14 managed snapshots**, sorted by recorded UTC
creation time and path. At a six-hour schedule this is about 84 hours, or 3.5
days. The current successful capture and any pending path are protected too.
Missing managed paths without matching durable deletion intent are integrity failures; their manifest records are preserved.

Only manifest entries can become deletion candidates. The complete owned record
is first written as `pending_deletion` and fsynced in state. Immediately before each
deletion the runner rechecks the exact direct-child path, absence of symlinks or
mounts, filesystem UUID, subvolume UUID and read-only property. It invokes
`btrfs subvolume delete --commit-after PATH`, confirms absence and atomically
updates the manifest, then durably clears the deletion intent before continuing. It never uses recursive deletion or
`rm -rf`. An interrupted deletion followed by a failed manifest update is
reconciled on the next run without another delete of an absent path, only when
matching deletion intent exists and the snapshot root still has the recorded
filesystem UUID. An unchanged surviving object may be retried
after full identity verification. An object appearing after manifest removal
is refused. Intent cannot target the current success or pending capture.
Schema 1 is refused rather than silently migrated.

Unknown directories and snapshots are untouched, including unknown
`survival-*` objects. If a candidate fails validation, deletion stops. A new
successful capture remains registered and `last_success` is retained if
retention fails; retention health records failure and the service exits nonzero.
Some earlier verified deletions may already have completed, and their names
appear in retention health. Namespace commit does not imply immediate extent
reclamation: Btrfs cleaning runs in the background.

Normal mode uses `*-*-* 00,06,12,18:00:00 UTC`, `AccuracySec=5min` and
`Persistent=true`. The systemd parser normalizes that expression unchanged;
consecutive UTC events are six hours apart through Dublin DST changes.
Missed calendar events cause a catch-up activation rather than one replay per
missed event. The exact timer stamp is persisted because ordinary `/var` resets
on this host. The timer requires its Impermanence file service before starting.
Other timer state is not added to persistence by this module.

The stamp records an activation attempt, not successful backup health. The
backup unit's condition skips execution if the server is inactive; a skipped
or failed attempt has no automatic immediate retry. For an active server still
starting, the runner retries transient connection failures and read-only capability discovery every
second for a 90-second readiness window before persisting new capture intent.
Connection open/close are each bounded at five seconds; an in-flight final
probe may extend past the window by at most those transport bounds. No autosave
changes occur during readiness; the real transaction independently rediscovers
capabilities. A readiness timeout records a fixed failed health stage. Inspect status and take a
manual backup when needed; the next scheduled attempt is the next calendar
event. Reboot persistence and pregen switching passed. Ordinary scheduled-event
acceptance and genuine missed-event catch-up are user-approved post-merge
operational observations.

## Manual operations

These commands operate the deployed system.

```sh
sudo systemctl start minecraft-backup.service
systemctl status minecraft-backup.service
journalctl -u minecraft-backup.service
systemctl list-timers minecraft-backup.timer
sudo minecraft-backup status
```

A successful service start means capture, registration and retention completed.
A failure can still leave a useful registered capture: inspect `last_success`,
`pending_snapshot`, `last_attempt.stage` and `last_retention` separately.
Journal history is volatile on this workstation; JSON health survives reboot.

For maintenance, stop the unit through systemd:

```sh
sudo systemctl stop minecraft-backup.timer
sudo systemctl stop minecraft-server-survival.service
```

Let an active backup finish and inspect its result before planned server
maintenance. The Minecraft `/stop` command alone is insufficient for a
maintenance stop: `restart=always` would restart the Java service. In pregen the
timer is masked; keep using the manual service for planned recovery points.

## Failure diagnosis

| Observation | Action after deployment |
| --- | --- |
| Recovery marker remains | Keep it; restore management availability and run `sudo minecraft-backup recover-autosave`. Confirm success before another capture. The command also takes the exclusive lock. |
| Pending capture | A later backup reconciles it before new work. Inspect JSON and the exact recorded object read-only; do not rename, delete or force adoption. |
| Metadata/schema/permission failure | Stop new backup attempts, preserve both documents, inspect ownership/modes and the last trusted receipt. Restore known valid metadata only after proving object identities; do not replace it with empty JSON. |
| Preflight or registration failure | Inspect actual mount topology, Btrfs filesystem/subvolume UUIDs and read-only properties. An unused destination is required; colliding names are never overwritten. |
| Retention failure with a new last success | The captured recovery point remains useful. Inspect the failed candidate and retention health; fix the cause before retrying. Unknown objects remain outside automatic retention. |
| Backup unit skipped | Verify the server unit is active and mounts are correct. A timer stamp alone is not a successful snapshot receipt. |
| Lock busy | Let the existing operation finish. Do not remove or replace the lock file to bypass exclusion. |

Read-only diagnostics for a recorded path can use `findmnt`,
`btrfs filesystem show --raw`, `btrfs subvolume show`, and
`btrfs property get -t s PATH ro`. Inspect exact paths from the manifest; a
`survival-*` filename does not prove ownership or authorize deletion.

## Hardening and accepted operation

The backup runs as root initially for Btrfs snapshots/deletion, privileged
metadata queries, root-only state and recovery. `ProtectSystem=strict`,
`ProtectHome`, `PrivateTmp` and an explicit writable allow-list contain ordinary
writes. Only `/.snapshots`, `/persist/minecraft-backup` and
`/run/minecraft-backup` are writable exceptions; `/srv/minecraft` is read-only.
NoNewPrivileges, clock/kernel/control-group protections, personality locking,
realtime and SUID/SGID restrictions are enabled.

PrivateNetwork is explicitly false so the client sees host loopback. Cgroup IP
filtering denies other networks and allows localhost; address families are
limited to UNIX, IPv4 and IPv6. The client independently enforces the loopback
endpoint. No speculative capability bounding set or syscall allow-list is
introduced. Offline systemd security analysis of the qualified hardening unit
reported 6.5; that diagnostic is not functional acceptance or proof of live BPF
enforcement. Real service snapshot/retention runs passed with the actual Btrfs
ioctls and namespace mount visibility; interruption recovery exercised the
recovery hook. Isolated non-loopback peers separately verified host ingress
and management/RCON rejection. No stronger BPF-specific enforcement claim is made.

Minecraft recovery is intentionally local-only. Read-only Btrfs snapshots on this system are the complete backup scope for the server. They provide rollback and local recovery but deliberately do not cover total device loss.

They share storage and initially share extents with the world. See
[Btrfs snapshot and deletion semantics](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html).

Physical deployment prepared the separate `@minecraft` mount and management
secret, then activated the guarded candidate. Real paused and online-player
backups, protocol/save ordering, autosave interruption recovery, isolated
retention/deletion recovery and a user-verified playable local restore passed.
The normal → pregen → normal switch also passed: a 32-block-radius square
Chunky run processed 25 chunks, manual backup succeeded, and normal mode restored
pause 60 with Chunky absent and the ordinary timer active. Disposable acceptance
snapshots and the writable restore clone were removed by exact verified targets;
raw cleanup identities remain in the local receipt.

Actual reboot persistence passed: the timer stamp remained a regular bind-mounted
file with unchanged persistent inode/timestamp and the seed/server/timer started.
Host ingress was tested from isolated IPv4 and IPv6 peers; the game handshake/ping
passed and management/RCON were unavailable. The latest backup completed during
a VM build with sync 0.325 seconds and total duration about 2.1 seconds; the user
reported no stalls during that workload. Ordinary scheduled-event acceptance is
delayed; genuine missed-event catch-up is a user-approved post-merge observation.
The unavailable laptop's actual LAN/gameplay path remains a recommended later
operational smoke test. These are separate from the accepted host ingress proof.

## Reproduce the declarative gate

```sh
nix develop .#default -c python3 -m py_compile \
  hosts/desktop/minecraft-msmp.py hosts/desktop/minecraft-backup.py \
  tests/workstation/minecraft-server/test_msmp.py \
  tests/workstation/minecraft-server/test_backup.py \
  hosts/desktop/minecraft-prerequisites.py \
  tests/workstation/minecraft-server/test_prerequisites.py
nix build .#checks.x86_64-linux.minecraft-server-config --print-build-logs
nix develop .#default -c statix check .
nix develop .#default -c deadnix --fail \
  --exclude hosts/desktop/hardware-configuration.nix -- .
nix fmt -- --ci
git diff --check
git diff --cached --check
nix flake check --no-write-lock-file --print-build-logs
nix build .#nixosConfigurations.desktop.config.system.build.toplevel --print-build-logs
systemd-analyze calendar --iterations=4 '*-*-* 00,06,12,18:00:00 UTC'
```

Inspect the resulting service/timer units and the pregen timer mask in the built
closure. Do not use a successful build as permission to switch or start services.

## Secret-bearing snapshots

The runtime `server.properties` contains the substituted management bearer
secret. Whole-server snapshots therefore contain secrets. Keep
`/.snapshots/minecraft` root-owned mode 0700; historical snapshots retain old
tokens after rotation. Rotation does not erase historical copies. Local restores
must preserve these access restrictions and install the current management
secret before starting a restored server. See
[secret bootstrap and rotation](bootstrap-secrets.md) and
[backup policy](backup-restore.md).

Paused-server backup after more than 60 seconds empty and online-player backup
passed against the real endpoint. P2949 was added to the runtime whitelist and
joined successfully; no operator role was added. Generated mod policy was reviewed
and meaningful parity/profiling settings are declared in Nix. Empty-server CPU,
return to idle after backup, one-player CPU/RSS and user-reported workstation
responsiveness were measured separately; see the idle/resource observation below.


Retention removes at most four eligible managed snapshots per backup invocation,
including a recovered deletion intent. Protected capture and last-success paths
are excluded before selecting that batch. A backlog stays in the ownership
manifest and is reported as `retention-backlog` with its eligible count; subsequent
scheduled or manual runs continue cleanup toward the newest-14 target.

The backup service has a 20-minute startup ceiling. Its conservative bounded
external-operation envelope is below 1,100 seconds: startup recovery (20),
mount filesystem checks (20), pending-capture identity (30), source preflight including nested-subvolume detection
(40), readiness including final transport closure (100), transaction discovery,
autosave queries/disable/save/restore and connection closure (180), snapshot
(60), fresh-connection recovery (20), new snapshot identity (30), and four
retention transactions (400), plus pending and new capture syncs (120). Normal execution is much shorter. Filesystem
metadata reads, atomic writes and fsync can stall under storage failure; the
systemd ceiling remains the final safety bound and invokes autosave recovery.


Readiness requires discovery plus `minecraft:server/status` with boolean
`started=true`; an open management listener alone does not prove world readiness.
It retries operating-system connection errors, timeouts, dropped WebSocket
connections, `started=false`, and the exact live pre-initialization status RPC
error, within the 90-second readiness budget. Configuration errors, incompatible
or malformed discovery/status, other JSON-RPC errors, authentication/handshake
rejection and unexpected programming errors fail immediately. Every readiness failure occurs before a new capture
intent or autosave change. Diagnostics remain fixed and secret-safe in health
metadata; transport and peer text are never copied there.


Whitelist and operator lists are runtime-owned: the empty Nix `whitelist` and
`operators` attributes deliberately leave `whitelist.json` and `ops.json` on
persistent `@minecraft` under console control. Use `/whitelist add <player>` and,
only for intended administrators, `/op <player>` before granting access. Do not
add a declarative initial list while expecting console additions to survive
rebuild as authoritative state. Whitelist enforcement remains enabled.

After generating managed files, pre-start restricts `server.properties` to
`0600` so the management bearer token is readable by the Minecraft account
rather than the shared console group. Physical inspection confirmed
`minecraft minecraft 600`. After restore or regeneration, re-check with
`stat -c '%U %G %a' /srv/minecraft/survival/server.properties` without reading
the properties file into a receipt.
Console access remains privileged server administration; mode hardening narrows
ordinary file access rather than removing the console administrator's authority.

ServerCore's five known non-parity optimization switches are explicitly false
in declaratively managed `config/servercore/optimizations.yml`. The
[reviewed 1.5.20 defaults](https://github.com/Wesley1808/ServerCore/blob/91e9953e82fc58b21210b654c153b28acc5cf895/docs/config/DEFAULT.md)
leave the separate main configuration at its pinned defaults: enderpearl
chunk-loading suppression, random-tick distance changes and unloaded-chunk
movement blocking are disabled; autosave interval is 300 seconds and XP/item
merge values remain 40/0.5/0.5. Villager lobotomizing, dynamic tuning, breeding
caps and activation range are disabled, so their subordinate thresholds and
activation lists are inactive. Additional mobcap enforcement is disabled for
reinforcements, portal ticks, spawners and infested spawning; category mobcaps,
spawn intervals and despawn distances retain their documented vanilla defaults.
Command display toggles and colors are presentation policy. First-start inspection
confirmed the reviewed defaults in the generated main file; any later gameplay-policy
change or mod upgrade requires a fresh parity review and declarative ownership.

After autosave-marker recovery and successful metadata validation, attempt
failure accounting covers environment preflight and reconciliation as well as
capture and retention. Unsafe or unreadable metadata is never rewritten to
manufacture a health record; marker recovery still precedes metadata work.

Native activation runs the Minecraft pre-switch prerequisite check before any
switch: `/srv/minecraft` must be a real writable Btrfs mount at `/@minecraft`,
`/.snapshots` must be a real writable Btrfs mount at `/@snapshots`, and both must
share the live root filesystem UUID. The guard also requires `/persist/secrets`
to be root:root `0700` and the management environment file to be a nonsymlink,
regular root:root `0600` file with one hard link and exactly one valid 40-character
ASCII alphanumeric token assignment. It emits no credential content. This guard
refuses unprepared activation; it does not create subvolumes or bootstrap secrets.

First-start control: generated units in `/etc/systemd/system` take priority over
runtime masks in `/run/systemd/system`. The first physical switch started both
units despite those masks. Do not rely on `systemctl mask --runtime` for these units.
Use a staged activation candidate with server automatic startup and the backup
timer disabled, inspect the activated state, then enable/start deliberately.
For maintenance, stop the timer explicitly and verify its active state.

Filesystem identity checks retain strict UUID validation. When the Btrfs CLI
cannot query a nested snapshot or a read-only namespace, the runner uses the
read-only Linux `BTRFS_IOC_FS_INFO` query on that directory; it never enables
writes to the source or relaxes the service sandbox.

For a temporary activation mask that must override generated NixOS units, the
verified load path is `/run/systemd/system.control/<unit>` linked to `/dev/null`.
Create the parent as root mode 0755, reload systemd, and verify `LoadState=masked`
and `ActiveState=inactive` before switching and again afterward. This temporary
mask survived the tested switch. Remove only the exact mask you created and
reload systemd before deliberately enabling the unit; it will not survive reboot.

First-start configuration inspection found the declared five ServerCore
optimization flags false and its main defaults matching the reviewed policy.
The generated `config/servercore/config.yml` remains runtime-owned at those
reviewed pinned defaults; changing gameplay values requires declarative ownership
and fresh review. `ferritecore.mixin.properties` keeps the pinned memory-layout
optimizations, with the unsafe small threading detector disabled and compact fast
map disabled; it is runtime-owned at reviewed defaults. `lithium.properties` has
no overrides and remains runtime-owned at pinned defaults. `spark/config.json`
is declaratively owned with `backgroundProfiler=false`. Profiling is available
on demand through `/spark profiler start` and `/spark profiler stop`. Profiler recordings and other generated diagnostic state remain
runtime-owned. These classifications apply to the currently pinned mod versions;
mod upgrades require reviewing newly generated defaults again.

The timer stamp must be a file bind mount, not a symlink: systemd's timestamp
write updates the stamp inode without following a symlink. The backing stamp
is seeded as a root:root mode 0644 single-link regular file before impermanence
mounts it, preserving any existing timestamp. Actual reboot proved the file bind
mount and unchanged inode/timestamp. Verify stamp advancement at `/var/lib/systemd/timers/stamp-minecraft-backup.timer`
and `/persist/var/lib/systemd/timers/stamp-minecraft-backup.timer` during timer
acceptance. An absent backing file must be seeded before the file persistence
service runs; a dangling symlink does not prove timestamp persistence.

## Backup completeness and local headroom

The deployment supports exactly one enabled server, `survival`. Adding another
server requires reviewing the save transaction before changing this invariant.
The source `/srv/minecraft` must contain no nested Btrfs subvolumes: preflight
rejects them because an outer snapshot does not include their contents. Adding a
server-side mod with persistent state requires reviewing whether the Minecraft
save barrier covers that state, including independent databases or asynchronous
writes, before accepting the mod.

Inspect local pool headroom periodically and around bulk world generation:

```sh
sudo btrfs filesystem usage /srv/minecraft
```

The current count policy retains 14 recovery points, approximately 3.5 days at
four scheduled captures per day. Manual captures shorten the elapsed horizon.
The count remains unchanged until several days of real play/pregeneration
provide meaningful growth data; the tiny Chunky smoke is insufficient to
extrapolate storage cost. A later 28-entry policy can provide approximately a week.
No free-space-based deletion or quota accounting is introduced.

Interrupted deletion recovery consumes at most one deletion before fresh capture.
The remaining allowance, at most three when one deletion was recovered, applies
only after the new synchronized recovery point is registered. Failure validating
an ordinary retention candidate therefore preserves the new last success.

Disabling `services.minecraft-servers.enable` disables physical prerequisites,
backup services/timer, stamp persistence/seed, resource overrides, slice, tmpfiles
and automatic Minecraft group membership. Administrative CLI tools remain
available. The bootloader VM asserts this isolation.

`sudo minecraft-backup status --live` adds read-only source-completeness and
all-managed-snapshot verification (filesystem UUID, subvolume UUID, mount status
and read-only flag) to metadata health. Both nested mounts and nested Btrfs
subvolumes in the source are rejected. Unknown snapshots are ignored. It contacts no Minecraft endpoint and never repairs metadata or deletes
snapshots. Any missing/replaced/writable managed recovery point returns attention and a
nonzero status. Ordinary `status` remains metadata-only.

The source must also have no descendant mountpoints of any kind, including bind
mounts and foreign filesystems. The kernel mount table is checked by path ancestry;
a similarly named sibling such as `/srv/minecraft-other` is outside this rule.

Filesystem sync commits the whole shared Btrfs filesystem, including pending
writes from other workstation workloads. It remains bounded at 60 seconds and
runs after autosave restoration. Successful sync duration is logged in the
backup service journal. The accepted concurrent-build sample and user-reported
responsiveness qualify the observed workload; they do not establish latency
bounds for every future storage workload.


## Failure diagnostics

The CLI/service journal prints fixed codes such as
`failed stage=durability-sync reason=sync-timeout`. A command exit failure instead
reports `sync-command-failed`; snapshot creation distinguishes `snapshot-timeout`
from `snapshot-command-failed`. Source completeness reports `nested-mount` or
`nested-subvolume`; mount/filesystem checks report `mount-missing` or
`filesystem-mismatch`. Protocol incompatibility and unavailable management have
separate codes. Metadata validation reports `metadata-invalid`.

These are trusted local labels. Arbitrary subprocess stderr, management peer
text, exception messages and authorization data are never included in failure
output. Persistent schema 2 retains fixed stage/error/message fields; reason
codes do not require a migration. Inspect `status`, then `journalctl -u
minecraft-backup.service`, and check the named stage with read-only commands.
`unexpected-error` requires investigation of the implementation rather than
resetting state. Run live integrity inspection with the backup service idle;
a concurrent capture/retention transaction may change the set being inspected.

## Restore a recovery point into production

The accepted playable isolated restore proves world/player recovery. The
production cutover below preserves the current world in quarantine and leaves
the retained recovery snapshot read-only. Rehearse the rename/snapshot procedure
on disposable subvolumes; do not replace a healthy production world for testing.

1. Arrange a maintenance window and disconnect players. Stop the timer and server:

   ```sh
   sudo systemctl stop minecraft-backup.timer
   systemctl is-active minecraft-backup.service
   ```

   Wait for any active backup to finish before stopping Minecraft. Do not stop
   either service during a save transaction. Once the backup is inactive:

   ```sh
   sudo systemctl stop minecraft-server-survival.service
   ```
   If an autosave recovery marker remains, preserve it and diagnose recovery before
   proceeding; do not clear it by hand.

2. Run `sudo minecraft-backup status --live`. Identify the intended record from
   the root-private `managed-snapshots.json`. Verify its exact direct-child path,
   recorded filesystem UUID, subvolume UUID, and `ro=true` using `btrfs subvolume
   show`, `btrfs filesystem show` (or the helper's FSID ioctl fallback), and
   `btrfs property get -t s PATH ro`. An unrelated damaged recovery point may
   make the full audit fail: explicitly resolve that finding and verify the
   chosen record rather than resetting ownership metadata. Save the selected
   identities and matching system closure/Git revision in a root-private receipt.

3. Enter a root maintenance shell. Hold the same backup lock throughout cutover:

   ```sh
   sudo -i
   exec 9>/run/minecraft-backup/backup.lock
   flock --exclusive --nonblock 9
   ```

   An unsuccessful lock acquisition means another operation is active: stop here.
   Set `restore_snapshot` to the exact verified snapshot path and choose distinct,
   unused direct top-level names `restore_clone` and `restore_quarantine`, such
   as `@minecraft-restored-YYYYMMDDTHHMMSSZ` and
   `@minecraft-quarantine-YYYYMMDDTHHMMSSZ`. Record those names privately.

4. Verify the declared source mount's live device with
   `findmnt --mountpoint /srv/minecraft`, the corresponding persistent filesystem
   UUID, and the source's Btrfs identity. Set `restore_device` to that verified
   device. Mount its top-level tree in an empty root-private directory:

   ```sh
   install -d -m 0700 /run/minecraft-restore-top
   mount -t btrfs -o subvolid=5 "$restore_device" /run/minecraft-restore-top
   ```

   Verify `/run/minecraft-restore-top/@minecraft` is exactly the live source
   subvolume, not a similarly named object. Check that clone/quarantine targets
   are absent and are direct children of this top-level tree. Never derive the
   device or a deletion target from a historical receipt alone.

5. Create and inspect the writable clone, then unmount the production source:

   ```sh
   btrfs subvolume snapshot "$restore_snapshot" "/run/minecraft-restore-top/$restore_clone"
   btrfs property get -t s "/run/minecraft-restore-top/$restore_clone" ro
   systemctl stop srv-minecraft.mount
   findmnt --mountpoint /srv/minecraft
   ```

   The clone must be `ro=false`; the retained recovery point must still be
   `ro=true`. `findmnt` must report no remaining production mount. Check for
   remaining open users with `fuser` before changing source names.

6. Rename the old source into quarantine and the clone to the declared source:

   ```sh
   mv -- /run/minecraft-restore-top/@minecraft "/run/minecraft-restore-top/$restore_quarantine"
   mv -- "/run/minecraft-restore-top/$restore_clone" /run/minecraft-restore-top/@minecraft
   btrfs filesystem sync /run/minecraft-restore-top
   systemctl start srv-minecraft.mount
   ```

   Verify the new mounted source identity matches the recorded clone and that
   quarantine matches the recorded old source. If cutover fails, keep services
   stopped and restore the old name only after checking which rename completed.
   Never delete either side to make room. Snapshot ownership metadata under
   `/persist/minecraft-backup` remains intact: source subvolume UUID changes are
   allowed; the filesystem identity and owned retained snapshots must match.

7. Start the intended compatible NixOS/Minecraft configuration. For an upgrade
   rollback, first select its matching known-good system closure as described
   below. Normal service startup regenerates declaratively managed files and
   injects the **current** management secret from the root-private environment
   file; never reuse a historical token from the restored properties file.

   ```sh
   systemctl start minecraft-server-survival.service
   ```

   Confirm initialized `minecraft:server/status`, enabled autosave, effective
   whitelist, authenticated loopback management, and healthy live snapshot
   status. Join as a whitelisted player and verify recognizable world, inventory
   and position. The normal pause policy must still be 60 seconds.

8. Release the lock before taking a new backup:

   ```sh
   flock --unlock 9
   exec 9>&-
   minecraft-backup
   minecraft-backup status --live
   systemctl start minecraft-backup.timer
   umount /run/minecraft-restore-top
   rmdir /run/minecraft-restore-top
   exit
   ```

   Confirm the new registered read-only recovery point, autosave enabled, no
   pending transaction/marker, and normal timer active. Keep quarantine until
   player acceptance and the new recovery point are both proven. Later cleanup
   requires explicit approval of its exact current path, UUID and subvolume ID;
   use `btrfs subvolume delete --commit-after` on that single verified target.
   Never recursively delete the top-level tree or the managed snapshot directory.

## Upgrade and rollback

Before changing Minecraft, Fabric, Java or mod pins, run live integrity inspection
and take a manual pre-upgrade recovery point. In a root-private mode 0600 receipt
outside Git, map its exact snapshot path/UUID to `readlink -f /run/current-system`,
the repository Git commit, Minecraft/Fabric versions, effective mod set and
exact system profile generation (`readlink /nix/var/nix/profiles/system`).
Verify that profile generation resolves to the recorded running closure.
Keep that system generation available; do not garbage-collect its closure while
it remains the rollback target. This preserves provenance without changing the
backup metadata schema.

Qualify the updated pins with focused tests, full flake checks, desktop/VM builds
and generated-unit inspection before switching in a maintenance window. Join,
check world/player state and effective security settings, then run a backup
smoke test. Record the accepted new snapshot/configuration pairing privately.

If rollback is needed, stop timer/server and restore the **pre-upgrade world**
using the cutover above, together with its matching known-good system generation.
Verify `rollback_generation` is the recorded numeric system generation and
`rollback_system` is its exact retained closure. Check that
`readlink -f /nix/var/nix/profiles/system-${rollback_generation}-link` equals that
closure before changing the profile. Restore the persistent system profile and
invoke the matching native activation:

```sh
sudo nix-env --profile /nix/var/nix/profiles/system --switch-generation "$rollback_generation"
sudo "$rollback_system/bin/switch-to-configuration" switch
```

The native action retains physical pre-switch checks; diagnose any refusal.
Verify both `/run/current-system` and `/nix/var/nix/profiles/system` resolve to
the recorded closure, and inspect the generated boot entry/default. When the
configuration requires reboot validation, boot that recorded generation during
maintenance. Invoking an old closure alone without restoring the profile would
leave a later rebuild/boot vulnerable to selecting the upgraded version again.
Do not boot the latest upgraded server against the restored old world as an
assumed rollback. Re-check runtime managed files, current
secret injection, whitelist, player acceptance and a fresh local recovery point.
The first real version upgrade must exercise this workflow; current deployment
has not claimed a cross-version world rollback test.

## Accepted idle observation

After the user disconnected, the server logged its normal 60-second empty pause.
A 30-second service CPU sample used 0.24% of one core before a real backup and
0.29% afterward. The server stayed empty and the service invocation did not
change; live recovery integrity passed afterward. Raw measurements are retained
in a local root-private receipt. These short samples prove return to negligible
idle CPU for this run; representative multi-minute active/resource observation
remains separate from performance tuning.


## Integration acceptance policy

Ordinary, unmodified UTC calendar activation acceptance is a user-approved
post-merge observation. The temporary live observer was cancelled and removed; the production
six-hour timer remains active. This test is unexercised and does not block integration. When resumed,
verify service execution, a newly registered read-only recovery point, autosave
enabled, no pending state/marker, complete live recovery-set integrity, sane
retention and an advanced persistent timer stamp. Manual starts and artificial
stale stamps do not count as this observation.

The user explicitly moved genuine missed-event catch-up to a post-merge
operational observation. Synthetic stale-stamp catch-up and actual reboot/stamp
persistence are accepted evidence for the underlying mechanisms; they are not
claimed as an actual missed calendar event. Observe that later during a real
maintenance shutdown spanning a scheduled event. Laptop gameplay is also a
recommended later home-network smoke test. Neither requires another backup tier.
Local health visibility and optional loopback-hostname hardening are deferred;
normal management uses literal `127.0.0.1` with systemd loopback IP filtering.


A subsequent three-minute resource observation included 61.7 seconds paused and
111.3 seconds with one player connected (excluding the join interval). Paused
CPU averaged 0.246% of one core and RSS stayed around 1469 MiB. Active CPU
averaged 14.3% of one core, with 10-second samples ranging from 5.45% to 70.2%;
RSS was 1581–1648 MiB. The Minecraft slice tracked service CPU closely.
This is a small one-player sample, not a multi-player capacity benchmark.
The user reported no noticeable Minecraft stutter or desktop stalls during
this play session.
