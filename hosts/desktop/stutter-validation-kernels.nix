{ pkgs, ... }:

{
  # Sibling boot entries that give the Stutter Core Validation kernel matrix
  # three distinct kernels. The default desktop kernel is left unchanged.
  specialisation = {
    stutter-kernel-6-12.configuration = {
      boot.kernelPackages = pkgs.linuxKernel.packages.linux_6_12;
    };
    stutter-kernel-7-2.configuration = {
      boot.kernelPackages = pkgs.linuxKernel.packages.linux_7_2;
    };
  };
}
