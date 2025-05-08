{
nixConfig = {
    extra-substituters = [
	"https://hyprland.cachix.org/"
	"https://cache.nixos.org/"
	"https://cachix.cachix.org/"
	"https://nix-community.cachix.org/"
    ];
    extra-trusted-public-keys = [
        "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
	      "cachix.cachix.org-1:eWNHQldwUO7G2VkjpnjDbWwy4KQ/HNxht7H4SSoMckM="
	      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
	      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    envycontrol.url = "github:bayasdev/envycontrol";
    hyprland.url = "github:hyprwm/Hyprland";
  };

 outputs = { self, nixpkgs, ... }@inputs: {
    # Please replace my-nixos with your hostname
    nixosConfigurations.nixos = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";

      # Set all inputs parameters as special arguments for all submodules,
      # so you can directly use all dependencies in inputs in submodules
      specialArgs = { inherit inputs; };
      modules = [
	 {
          nix.settings = {
            substituters = [
              "https://hyprland.cachix.org/"
		          "https://cache.nixos.org/"
		          "https://cachix.cachix.org/"
		          "https://nix-community.cachix.org/"
            ];
            trusted-public-keys = [
              "hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
		          "cachix.cachix.org-1:eWNHQldwUO7G2VkjpnjDbWwy4KQ/HNxht7H4SSoMckM="
		          "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
		          "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
            ];
          };
        }	

        # Import the previous configuration.nix we used,
        # so the old configuration file still takes effect
        ./configuration.nix
	      ./hardware-configuration.nix
	      ./cachix.nix
      ];
    };
  };
}
