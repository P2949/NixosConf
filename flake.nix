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

      desktop = nixpkgs.lib.nixosSystem {
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

      optimizationRuntimeCapture = import ./optimization/runtime/capture.nix {
        inherit pkgs;
        repository = inputs.self;
      };

      optimizationRuntimeManifestCheck = import ./optimization/runtime/check.nix {
        inherit pkgs;
        filter = ./optimization/runtime/manifest.jq;
      };

      optimizationExperimentModelCheck = import ./optimization/experiment/check.nix {
        inherit pkgs;
        inherit (nixpkgs) lib;
      };

      optimizationCpuCodegen = import ./optimization/stages/cpu-codegen.nix {
        inherit (nixpkgs) lib;
      };

      optimizationZstdSkylake = optimizationCpuCodegen {
        package = pkgs.zstd;
        march = "skylake";
        mtune = "skylake";
      };

      optimizationBuildManifest = import ./optimization/manifest.nix {
        inherit pkgs inputs;

        repository = inputs.self;
        systemConfig = desktop;
        baseline = import ./optimization/baseline.nix;
      };

      optimizationZstdSilesiaCorpus = import ./optimization/experiments/zstd-skylake/corpus.nix {
        inherit pkgs;
      };

      optimizationZstdSkylakeExperimentSpec = import ./optimization/experiments/zstd-skylake/spec.nix {
        inherit pkgs;
        inherit (nixpkgs) lib;

        corpus = optimizationZstdSilesiaCorpus;
      };

      optimizationZstdSkylakeBenchmark = import ./optimization/experiments/zstd-skylake/runner.nix {
        inherit pkgs;

        stockZstd = pkgs.zstd;
        optimizedZstd = optimizationZstdSkylake;
        corpus = optimizationZstdSilesiaCorpus;
        experimentSpec = optimizationZstdSkylakeExperimentSpec;
        buildManifest = optimizationBuildManifest;
        runtimeCapture = optimizationRuntimeCapture;
      };
    in
    {

      formatter.${system} = pkgs.nixfmt-tree;

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          pkgs.nixfmt
          pkgs.nixfmt-tree
          pkgs.deadnix
          pkgs.statix
        ];
      };

      checks.${system} = {
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

        runtime-capture = optimizationRuntimeCapture;
        runtime-manifest = optimizationRuntimeManifestCheck;
        experiment-model = optimizationExperimentModelCheck;
      };

      nixosConfigurations.desktop = desktop;

      packages.${system} = {
        optimization-manifest = optimizationBuildManifest;

        optimization-runtime-capture = optimizationRuntimeCapture;
        optimization-zstd-skylake = optimizationZstdSkylake;

        optimization-zstd-silesia-corpus = optimizationZstdSilesiaCorpus;

        optimization-zstd-skylake-experiment = optimizationZstdSkylakeExperimentSpec;

        optimization-zstd-skylake-benchmark = optimizationZstdSkylakeBenchmark;
      };

      apps.${system} = {
        optimization-runtime-capture = {
          type = "app";
          program = "${optimizationRuntimeCapture}/bin/nixos-optimization-runtime-capture";

          meta = {
            description = "Capture runtime state for NixOS optimization experiments";
          };
        };

        zstd-skylake-benchmark = {
          type = "app";
          program = "${optimizationZstdSkylakeBenchmark}/bin/nixos-optimization-zstd-skylake-benchmark";

          meta = {
            description = "Benchmark stock and Skylake-optimized zstd builds";
          };
        };
      };
    };
}
