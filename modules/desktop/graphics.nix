{ pkgs, pkgsMesa, ... }:

{
  hardware.graphics = {
    enable = true;
    enable32Bit = true;
    package = pkgsMesa.mesa;
    package32 = pkgsMesa.pkgsi686Linux.mesa;
  };

  environment.systemPackages = with pkgs; [
    vulkan-tools
    mesa-demos
    amdgpu_top
  ];
}
