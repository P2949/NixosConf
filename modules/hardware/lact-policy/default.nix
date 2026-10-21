{
  config,
  lib,
  pkgs,
  pkgsUnstable,
  ...
}:
let
  cfg = config.hardware.lactPolicy;
in
{
  options.hardware.lactPolicy = {
    enable = lib.mkEnableOption "declarative LACT source with a writable runtime configuration";
    source = lib.mkOption {
      type = lib.types.path;
      description = "Exact LACT YAML seeded at boot and when the source changes.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = config.services.lact.settings == { };
        message = "Writable LACT policy seeding cannot be combined with services.lact.settings.";
      }
    ];
    services.lact = {
      enable = true;
      package = import ../../../packages/lact { inherit (pkgsUnstable) lact; };
    };
    systemd.services.gpu-lact-config-seed = {
      description = "Seed the declarative LACT baseline as writable runtime state";
      before = [ "lactd.service" ];
      requiredBy = [ "lactd.service" ];
      restartTriggers = [ cfg.source ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        UMask = "0077";
      };
      path = [ pkgs.coreutils ];
      script = ''
        install -d -m 0755 /etc/lact
        temporary=$(mktemp /etc/lact/.config.yaml.XXXXXX)
        trap 'rm -f "$temporary"' EXIT
        install -m 0600 ${cfg.source} "$temporary"
        mv -Tf "$temporary" /etc/lact/config.yaml
      '';
    };
    systemd.services.lactd = {
      requires = [ "gpu-lact-config-seed.service" ];
      after = [ "gpu-lact-config-seed.service" ];
      restartTriggers = [ cfg.source ];
    };
  };
}
