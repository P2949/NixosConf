{ ... }:
{
  imports = [ ../../modules/hardware/lact-policy ];
  hardware.amdgpu.overdrive.enable = true;
  hardware.lactPolicy = {
    enable = true;
    source = ./lact-policy.yaml;
  };
  programs.gamemode.gpuProfile.enable = true;
}
