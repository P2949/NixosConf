{ inputs, pkgs }:

# The shared harness imports the actual desktop and home persistence policy.
# Three normal boots, two recovery boots, then normal mode again exercise both
# sides of the contract, including user writes and declarative reconstruction.
import ./ephemeral-root/harness.nix {
  inherit inputs pkgs;
  persistMachineId = true;
  persistentFallback = true;
  granular = true;
}
