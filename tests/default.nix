{
  inputs,
  pkgs,
  pkgsUnstable,
  username,
  desktopSystem,
  repoSource,
}:
{
  checks = {
    activation-safety-config = import ./workstation/activation-safety/config.nix { inherit pkgs; };
    btrfs-maintenance-config = import ./storage/btrfs-maintenance/config.nix { inherit pkgs; };
    activation-safety = import ./workstation/activation-safety/guard.nix { inherit pkgs; };
    ephemeral-root-shell = import ../modules/storage/ephemeral-btrfs-root/check.nix { inherit pkgs; };
    btrfs-maintenance-shell = import ../modules/storage/btrfs-maintenance/check.nix { inherit pkgs; };
    maintenance-guard = import ./storage/btrfs-maintenance/guard.nix {
      inherit pkgs;
    };

    commander-core-config = import ./hardware/commander-core/config.nix {
      inherit pkgs inputs;
    };

    commander-core-python = import ./hardware/commander-core/python.nix {
      inherit pkgs;
      src = inputs.liquidctl-pr886;
    };

    baseline-collector =
      pkgs.runCommand "check-baseline-collector"
        {
          nativeBuildInputs = [
            pkgs.bash
            pkgs.shellcheck
          ];
        }
        ''
          bash -n ${../scripts/nixos-baseline-info.sh}
          shellcheck ${../scripts/nixos-baseline-info.sh}
          touch "$out"
        '';

    desktop-evaluation = import ./workstation/evaluation.nix {
      inherit pkgs;
      inherit (desktopSystem) config;
      homeCutover = inputs.self.nixosConfigurations.desktop-home-cutover.config;
    };

    granular-impermanence = import ./storage/granular-impermanence.nix {
      inherit inputs pkgs;
    };

    ephemeral-root-config = import ./storage/ephemeral-root/config.nix {
      inherit pkgs;
    };

    formatting =
      pkgs.runCommand "check-nix-formatting"
        {
          src = repoSource;
          nativeBuildInputs = [
            pkgs.nixfmt-tree
          ];
        }
        ''
          cp -r "$src" source
          chmod -R u+w source
          cd source

          treefmt             --ci             --tree-root .             --walk filesystem

          touch "$out"
        '';

    statix =
      pkgs.runCommand "check-statix"
        {
          src = repoSource;
          nativeBuildInputs = [
            pkgs.statix
          ];
        }
        ''
          cd "$src"

          statix check .

          touch "$out"
        '';

    deadnix =
      pkgs.runCommand "check-deadnix"
        {
          src = repoSource;
          nativeBuildInputs = [
            pkgs.deadnix
          ];
        }
        ''
          cd "$src"

          deadnix             --fail             --exclude hosts/desktop/hardware-configuration.nix             --             .

          touch "$out"
        '';
  };

  packages = rec {
    granular-arm-cutover = import ../packages/granular-arm-cutover.nix {
      inherit pkgs username;
      inherit (desktopSystem) config;
    };
    granular-shutdown-cutover = import ../packages/granular-shutdown-cutover.nix {
      inherit pkgs username;
      inherit (desktopSystem) config;
    };
    granular-physical-check = import ../packages/granular-physical-check.nix {
      inherit pkgs username;
      inherit (desktopSystem) config;
    };
    granular-final-sync = import ../packages/granular-migration.nix {
      inherit pkgs username;
      inherit (desktopSystem) config;
    };
    granular-impermanence = import ./storage/granular-impermanence.nix {
      inherit inputs pkgs;
    };
    impermanence-home = granular-impermanence;
    impermanence-var = granular-impermanence;
    blank-disk-reconstruction = import ./storage/ephemeral-root/reconstruction.nix {
      inherit
        desktopSystem
        inputs
        pkgs
        username
        ;
    };
    activation-safety-actions = import ./workstation/activation-safety/actions.nix { inherit pkgs; };
    stock-contamination-negative = import ./workstation/stock-contamination.nix { inherit pkgs; };
    impermanence-root-test-a = reset-control;
    impermanence-root-test-b = persistent-identity;
    impermanence-root-recovery = interrupted-recovery;
    impermanence-root-fallback = persistent-fallback;
    workstation-smoke = import ./workstation/smoke.nix {
      inherit
        inputs
        pkgs
        pkgsUnstable
        username
        ;
    };

    reset-control = import ./storage/ephemeral-root/reset-control.nix {
      inherit inputs pkgs;
    };

    impermanence-root-safety = import ./storage/ephemeral-root/safety.nix {
      inherit pkgs;
    };

    interrupted-recovery = import ./storage/ephemeral-root/interrupted-recovery.nix {
      inherit inputs pkgs;
    };

    persistent-identity = import ./storage/ephemeral-root/persistent-identity.nix {
      inherit inputs pkgs;
    };

    persistent-fallback = import ./storage/ephemeral-root/persistent-fallback.nix {
      inherit inputs pkgs;
    };
  };

}
