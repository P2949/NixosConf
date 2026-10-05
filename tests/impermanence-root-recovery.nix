{ inputs, pkgs }:

import ./impermanence-root-a.nix {
  inherit inputs pkgs;
  recovery = true;
}
