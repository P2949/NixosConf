{ ... }:

{
  virtualisation.vmVariantWithBootLoader =
    {
      config,
      lib,
      username,
      ...
    }:
    {
      # Physical Btrfs maintenance cannot run against the guest ext4 disk.
      disabledModules = [ ../../modules/storage/btrfs-maintenance ];

      services.minecraft-servers.enable = lib.mkForce false;

      assertions = [
        {
          assertion =
            !(config.system.preSwitchChecks ? minecraft)
            && !(config.systemd.timers ? minecraft-backup)
            && !(config.systemd.services ? minecraft-backup)
            && !(config.systemd.services ? minecraft-server-survival)
            && !(config.systemd.services ? minecraft-backup-timer-stamp-seed)
            && !(config.systemd.slices ? minecraft)
            && !(config.users.users ? minecraft)
            && !(config.users.groups ? minecraft)
            && !(lib.any (rule: lib.hasInfix "minecraft" rule) config.systemd.tmpfiles.rules)
            && !(lib.elem "minecraft" config.users.users.${username}.extraGroups)
            && !(lib.any (
              file: file.filePath == "/var/lib/systemd/timers/stamp-minecraft-backup.timer"
            ) config.environment.persistence."/persist".files);
          message = "The disabled Minecraft deployment must not leak physical guards, services, timer persistence, slice or group membership into the bootloader VM.";
        }
      ];

      hardware.commanderCore.enable = lib.mkForce false;
      hardware.intelPackagePower.enable = lib.mkForce false;
      workstation.activationSafety.enable = lib.mkForce false;
      boot.ephemeralBtrfsRoot.enable = lib.mkForce false;
      boot.kernelParams = [
        "console=ttyS0,115200n8"
        "console=tty0"
      ];
      services.btrfs.autoScrub.enable = lib.mkForce false;
      disko.devices = lib.mkForce { };

      virtualisation = {
        memorySize = 8192;
        cores = 4;
        diskSize = 32768;
        resolution = {
          x = 1920;
          y = 1080;
        };
        # /persist is an ordinary directory on the persistent guest root.
        fileSystems."/".neededForBoot = true;
      };

      # The guest never consumes the workstation's private credential file.
      users.users.${username} = {
        hashedPasswordFile = lib.mkForce null;
        initialPassword = "vm";
      };
    };
}
