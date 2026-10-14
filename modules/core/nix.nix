{ username, ... }:

{
  nixpkgs.config = {
    allowUnfree = true;
    android_sdk.accept_license = true;
  };

  nix.settings = {
    experimental-features = [
      "nix-command"
      "flakes"
    ];

    trusted-users = [
      username
    ];

    auto-optimise-store = true;
  };
}
