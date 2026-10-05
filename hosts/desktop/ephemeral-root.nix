{ lib, ... }:

{
  imports = [ ../../modules/storage/ephemeral-btrfs-root.nix ];

  boot.initrd.systemd.enable = true;
  boot.ephemeralBtrfsRoot.enable = true;

  # Three physical reset trials passed before adopting this default.
  # Recovery disables subsequent resets; it cannot restore discarded data.
  specialisation.persistent-root.configuration = {
    boot.ephemeralBtrfsRoot.enable = lib.mkForce false;
  };
}
