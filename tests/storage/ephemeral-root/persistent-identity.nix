{ inputs, pkgs }:

import ./harness.nix {
  inherit inputs pkgs;
  persistMachineId = true;
}
