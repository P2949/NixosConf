{ ... }:

{
  imports = [ ../../modules/storage/ephemeral-btrfs-root.nix ];

  # First adoption is boot-only and manually selected; the parent remains
  # persistent-root. Neither entry restores data discarded by a reset.
  specialisation.ephemeral-root.configuration = {
    boot.initrd.systemd.enable = true;
    boot.ephemeralBtrfsRoot.enable = true;

    environment.persistence."/persist".files = [ "/etc/machine-id" ];
  };
}
