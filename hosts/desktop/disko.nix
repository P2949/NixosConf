{ config, lib, ... }:
let
  btrfsMountOptions = [
    "compress=zstd:1"
    "noatime"
    "discard=async"
  ];
in
{
  disko.devices = {
    disk.main = {
      type = "disk";
      device = "/dev/disk/by-id/nvme-Force_MP600_2046822900012855404A";

      content = {
        type = "gpt";

        partitions = {
          ESP = {
            priority = 1;
            size = "4G";
            type = "EF00";

            content = {
              type = "filesystem";
              format = "vfat";
              mountpoint = "/boot";
              mountOptions = [
                "umask=0077"
              ];
            };
          };

          swap = {
            priority = 2;
            size = "32G";

            content = {
              type = "swap";
              discardPolicy = "both";
            };
          };

          root = {
            priority = 3;
            size = "100%";

            content = {
              type = "btrfs";

              extraArgs = [
                "-f"
                "-L"
                "nixos"
              ];

              subvolumes = {
                "@root" = {
                  mountpoint = "/";
                  mountOptions = btrfsMountOptions;
                };

                "@nix" = {
                  mountpoint = "/nix";
                  mountOptions = btrfsMountOptions;
                };

                "@persist" = {
                  mountpoint = "/persist";
                  mountOptions = btrfsMountOptions;
                };

                "@optimization" = {
                  mountpoint = "/var/lib/nixos-optimization";
                  mountOptions = btrfsMountOptions;
                };

                "@snapshots" = {
                  mountpoint = "/.snapshots";
                  mountOptions = btrfsMountOptions;
                };
              }
              // lib.optionalAttrs config.workstation.granularMigration.keepLegacyVar {
                "@var" = {
                  mountpoint = "/var";
                  mountOptions = btrfsMountOptions;
                };
              };
            };
          };
        };
      };
    };
  };

  fileSystems."/persist".neededForBoot = true;
}
