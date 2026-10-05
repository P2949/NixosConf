# External bootstrap secrets contract

The stock baseline uses an external secret model. The repository declares
`/persist/secrets/<username>-password-hash`; it contains neither the production
hash nor decryption credentials. A new secrets framework is not required.

Keep an encrypted independent copy and its recoverable access credentials.
Record date, encrypted artifact hash and storage identity privately. The user's
older separate backup is reported evidence; a current restore test is still
required before the final freeze and any firmware update.

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
is not evidence of a newly encrypted bootstrap-secret backup. The existing
separate backup must be located and restore-tested independently.
