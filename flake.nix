{
  description = "Main desktop workstation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";

    # Known-good Commander Core support used on the previous Gentoo system.
    liquidctl-pr886 = {
      url = "github:indyfive11/liquidctl/48e8dd07bdc1c5dca330a844aca7fb22218e6e59";
      flake = false;
    };
  };

  outputs =
    inputs@{
      nixpkgs,
      disko,
      ...
    }:
    {
      nixosConfigurations.desktop =
        nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";

          specialArgs = {
            inherit inputs;
          };

          modules = [
            disko.nixosModules.disko
            ./hosts/desktop
          ];
        };
    };
}
