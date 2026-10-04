{ pkgs, ... }:

{
  users.users.p2949 = {
    isNormalUser = true;

    extraGroups = [
      "wheel"
      "networkmanager"
      "video"
      "render"
      "audio"
      "input"
      "kvm"
    ];

    shell = pkgs.zsh;
  };

  programs.zsh.enable = true;

  security.sudo.enable = true;

  # Give large development workloads (Unreal, clangd, IDEs, etc.)
  # a practical open-file limit while retaining a finite hard ceiling.
  security.pam.loginLimits = [
    {
      domain = "p2949";
      type = "soft";
      item = "nofile";
      value = 65536;
    }
  ];

  # User systemd services do not inherit PAM limits, so configure
  # the user manager independently.
  systemd.user.extraConfig = ''
    DefaultLimitNOFILE=65536:524288
  '';
}
