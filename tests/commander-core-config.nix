{ pkgs, inputs }:
let
  inherit (pkgs) lib;
  base = import "${pkgs.path}/nixos/lib/eval-config.nix" {
    inherit pkgs;
    system = pkgs.stdenv.hostPlatform.system;
    specialArgs = { inherit inputs; };
    modules = [
      ../modules/hardware/commander-core
      {
        boot.loader.grub.devices = [ "nodev" ];
        fileSystems."/" = {
          device = "/dev/test-root";
          fsType = "ext4";
        };
        hardware.commanderCore = {
          enable = true;
          usbId = lib.mkDefault "1b1c:0c1c";
          serial = lib.mkDefault "test-controller";
        };
        system.stateVersion = "26.05";
      }
    ];
  };
  accepted =
    settings:
    (builtins.tryEval
      (base.extendModules { modules = [ { hardware.commanderCore = settings; } ]; })
      .config.system.build.toplevel.drvPath
    ).success;
  invalid = [
    { usbId = "zzzz:0c1c"; }
    { usbId = "1b1c:0c1c:1234"; }
    { serial = ""; }
    { serial = " \t"; }
    { cooling.highFanDuty = 59; }
    { cooling.lowTemp = 65; }
    { cooling.lowTemp = -1; }
    { cooling.highTemp = 101; }
    { cooling.tempInterval = 0; }
    { cooling.wakeInterval = 0; }
    { cooling.resetDelay = 0; }
    { cooling.highDelay = -1; }
    { cooling.lowDelay = -1; }
    { cooling.tempInterval = 17.5; }
    { cooling.wakeInterval = 17.5; }
  ];
  results = map (
    settings:
    let
      inherit (base.extendModules { modules = [ { hardware.commanderCore = settings; } ]; }) config;
      failures = lib.filter (a: !a.assertion) config.assertions;
    in
    assert lib.assertMsg (
      failures != [ ] && lib.all (a: lib.hasPrefix "hardware.commanderCore" a.message) failures
    ) "Expected actionable Commander Core assertion missing";
    assert lib.assertMsg (
      !accepted settings
    ) "Invalid Commander Core configuration accepted: ${builtins.toJSON settings}";
    settings
  ) invalid;
in
assert lib.assertMsg (accepted { }) "Current Commander Core defaults rejected";
assert lib.assertMsg (accepted {
  cooling = {
    lowTemp = 0;
    highTemp = 100;
    highDelay = 0;
    wakeInterval = 17.49;
  };
}) "Valid Commander Core boundaries rejected";
assert lib.assertMsg (accepted {
  enable = lib.mkForce false;
  usbId = "invalid";
  serial = "";
}) "Disabled Commander Core module imposed hardware constraints";
pkgs.runCommand "check-commander-core-config" { cases = builtins.toJSON results; } ''
  printf '%s\n' "$cases" > "$out"
''
