{
  config,
  lib,
  ...
}:

let
  cfg = config.optimization;
in
{
  options.optimization = {
    enable = lib.mkEnableOption "experimental system optimization framework";
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = false;
        message = ''
          optimization.enable is not usable yet.

          The optimization framework has been imported, but no optimization
          stage has been implemented. Keep optimization.enable disabled until
          an explicit optimization stage is available.
        '';
      }
    ];
  };
}
