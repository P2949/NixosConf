# External bootstrap secrets contract

The stock baseline uses an external secret model. The repository declares
`/persist/secrets/<username>-password-hash`; it contains neither the production
hash nor decryption credentials. A new secrets framework is not required.

Keep an encrypted independent copy and its recoverable access credentials.
Record date, encrypted artifact hash and storage identity privately.
On 2026-10-05 the user confirmed that the separate backup was restored during
recovery from an actual system failure. This gate is complete on user-reported
evidence; no repeat restore is required. Private artifact location, hash and
decryption method were not collected.

From trusted recovery media, identify and mount the intended persistence
subvolume. Restore into a temporary root-private directory first, compare the
restored file with the expected source without printing either file, then
install the confirmed hash at the declared path with root ownership and mode
0600. Keep the secrets directory root-owned0700. Do not replace a conflicting
existing file until its origin is understood. Unmount cleanly.

Test fixture hashes are deliberately disposable. The reconstruction VM uses
this same path contract without reading any production secret. Recovery ISO
configuration excludes workstation secrets and persistence imports.

The dedicated Ventoy home backup excludes `/persist/secrets`; its tar archive
is not evidence of a newly encrypted bootstrap-secret backup.
The separate secrets backup and successful recovery are user-confirmed;
this home archive has its own verification gate.

## Minecraft management secret contract

The deployed server uses `/persist/secrets/minecraft-management.env`
containing exactly one `MINECRAFT_MANAGEMENT_SECRET=<token>` assignment; the
token is exactly 40 ASCII alphanumeric characters. Keep the file root:root
mode 0600 and `/persist/secrets` root:root mode 0700. Never put the real token
in Git, a Nix expression, a command argument, or the Nix store. Use
`sudo minecraft-msmp ...` rather than weakening secret-directory permissions.
Physical bootstrap created the root-private environment file; it is active host state, not a qualification fixture. On a fresh installation, create this file before starting Minecraft.

The Minecraft project requires no independent or off-machine secret copy.
For a local world restore, use the current root-private environment file to
regenerate runtime properties before starting the restored server. Verify the
artifact without printing its content and preserve the ownership/modes above.

For rotation during an approved maintenance window, stop the backup timer and
Minecraft service, generate a fresh qualifying token into a root-private file,
atomically replace the environment
file. Restart the server so its runtime properties receive the new token,
verify authenticated loopback management without printing it, then resume the
timer in normal mode. Existing snapshots contain historical `server.properties`
and historical token values; rotation does not remove these copies. Preserve
root-only access to retained snapshots. See [Minecraft operations](minecraft-server.md).
