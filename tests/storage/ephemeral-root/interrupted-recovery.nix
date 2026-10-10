{ inputs, pkgs }:

import ./harness.nix {
  inherit inputs pkgs;
  recovery = true;
}
