{
  description = "Main desktop workstation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";

    nix-minecraft = {
      url = "github:Infinidoge/nix-minecraft";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    impermanence = {
      url = "github:nix-community/impermanence";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    # Pinned Commander Core fw2 support from upstream PR #886.
    # Remove only after the required support is released and available in Nixpkgs.
    liquidctl-pr886 = {
      url = "github:indyfive11/liquidctl/48e8dd07bdc1c5dca330a844aca7fb22218e6e59";
      flake = false;
    };
  };

  outputs =
    inputs@{
      nixpkgs,
      home-manager,
      disko,
      impermanence,
      ...
    }:
    let
      system = "x86_64-linux";
      username = "p2949";

      pkgs = nixpkgs.legacyPackages.${system};

      pkgsUnstable = import inputs.nixpkgs-unstable {
        inherit system;
        config.allowUnfree = true;
      };
      optimization = import ./optimization {
        inherit pkgs inputs;
        repository = inputs.self;
        systemConfig = inputs.self.nixosConfigurations.desktop;
        recoverySystem = inputs.self.nixosConfigurations.recovery;
      };
      validation = import ./tests {
        inherit
          inputs
          pkgs
          pkgsUnstable
          username
          ;
        desktopSystem = inputs.self.nixosConfigurations.desktop;
        repoSource = ./.;
      };
    in
    {

      formatter.${system} = pkgs.nixfmt-tree;

      devShells.${system} = {
        default = pkgs.mkShell {
          packages = [
            pkgs.nixfmt
            pkgs.nixfmt-tree
            pkgs.deadnix
            pkgs.statix
            pkgs.gcc
            pkgs.clang
            pkgs.lld
            pkgs.gdb
            pkgs.cmake
            pkgs.ninja
            pkgs.gnumake
            pkgs.pkg-config
            pkgs.python3
          ];
        };

        validation = pkgs.mkShell {
          packages = [
            pkgs.python3
            pkgs.stress-ng
            pkgs.hyperfine
            pkgs.perf
            inputs.self.nixosConfigurations.desktop.config.boot.kernelPackages.turbostat
            pkgs.hwloc
            pkgs.numactl
            pkgs.sysstat
            pkgs.lm_sensors
            pkgs.nvme-cli
            pkgs.btrfs-progs
            pkgs.pciutils
            pkgs.usbutils
            pkgs.vulkan-tools
            pkgs.mesa-demos
          ];
        };
      };

      checks.${system} = validation.checks // optimization.checks;
      packages.${system} =
        validation.packages
        // optimization.packages
        // {
          recovery-iso = inputs.self.nixosConfigurations.recovery.config.system.build.isoImage;
          module-docs =
            (pkgs.nixosOptionsDoc {
              options =
                let
                  opts = inputs.self.nixosConfigurations.desktop.options;
                in
                {
                  boot.ephemeralBtrfsRoot = opts.boot.ephemeralBtrfsRoot;
                  workstation = {
                    activationSafety = opts.workstation.activationSafety;
                    ephemeralApplicationState = opts.workstation.ephemeralApplicationState;
                  };
                  hardware = {
                    commanderCore = opts.hardware.commanderCore;
                    intelPackagePower = opts.hardware.intelPackagePower;
                  };
                };
              transformOptions =
                option:
                option
                // {
                  declarations = map (
                    declaration:
                    let
                      path =
                        nixpkgs.lib.removePrefix "${inputs.self}/" (toString declaration)
                        + nixpkgs.lib.optionalString (builtins.pathExists "${declaration}/default.nix") "/default.nix";
                    in
                    {
                      name = path;
                      url = "https://github.com/P2949/NixosConf/blob/${inputs.self.rev or "main"}/${path}";
                    }
                  ) option.declarations;
                };
            }).optionsCommonMark;
        };

      nixosConfigurations.desktop = nixpkgs.lib.nixosSystem {
        inherit system;

        specialArgs = {
          inherit inputs username pkgsUnstable;
        };

        modules = [
          disko.nixosModules.disko
          home-manager.nixosModules.home-manager
          impermanence.nixosModules.impermanence

          ./hosts/desktop

          {
            home-manager = {
              useGlobalPkgs = true;
              useUserPackages = true;

              extraSpecialArgs = {
                inherit inputs username pkgsUnstable;
              };

              users.${username} = import ./home/p2949;
            };
          }
        ];
      };

      nixosConfigurations.recovery = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [ ./images/recovery.nix ];
      };
    };
}
