{ inputs, pkgs }:
let
  test = import ./harness.nix {
    inherit inputs pkgs;
    recovery = true;
    debugPause = true;
  };
in
# The interactive driver is a developer artifact, never an unattended check.
test.driverInteractive
