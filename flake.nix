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

    impermanence = {
      url = "github:nix-community/impermanence";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    # Known-good Commander Core support used on the previous Gentoo system.
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
          ];
        };

        validation = pkgs.mkShell {
          packages = [
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

      checks.${system} = {
        desktop-evaluation = import ./tests/desktop-evaluation.nix {
          inherit pkgs;
          config = inputs.self.nixosConfigurations.desktop.config;
        };

        ephemeral-root-config = import ./tests/impermanence-root-config.nix {
          inherit pkgs;
        };

        formatting =
          pkgs.runCommand "check-nix-formatting"
            {
              src = ./.;
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
              src = ./.;
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
              src = ./.;
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

      packages.${system} = {
        recovery-iso = inputs.self.nixosConfigurations.recovery.config.system.build.isoImage;

        impermanence-root-test-a = import ./tests/impermanence-root-a.nix {
          inherit inputs pkgs;
        };

        impermanence-root-safety = import ./tests/impermanence-root-safety.nix {
          inherit pkgs;
        };

        impermanence-root-recovery = import ./tests/impermanence-root-recovery.nix {
          inherit inputs pkgs;
        };

        impermanence-root-test-b = import ./tests/impermanence-root-b.nix {
          inherit inputs pkgs;
        };

        impermanence-root-fallback = import ./tests/impermanence-root-fallback.nix {
          inherit inputs pkgs;
        };
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
        modules = [ ./hosts/recovery ];
      };
    };
}
