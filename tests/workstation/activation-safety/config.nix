{ pkgs }:
let
  inherit (pkgs) lib;
  evaluate =
    includeRoot: extra:
    import "${pkgs.path}/nixos/lib/eval-config.nix" {
      inherit pkgs;
      system = pkgs.stdenv.hostPlatform.system;
      specialArgs.username = "fixture";
      modules = [
        ../../../modules/workstation/activation-safety
        {
          workstation.activationSafety = {
            enable = true;
            espReserveBytes = 256 * 1024 * 1024;
          };
          boot.initrd.systemd.enable = true;
          fileSystems."/" = {
            device = "/dev/fixture-root";
            fsType = "btrfs";
          };
          fileSystems."/boot" = {
            device = "/dev/fixture-esp";
            fsType = "vfat";
          };
          users.users.fixture = {
            isNormalUser = true;
            hashedPasswordFile = "/persist/secrets/fixture-password-hash";
          };
          system.stateVersion = "26.05";
        }
        extra
      ]
      ++ lib.optional includeRoot ../../../modules/storage/ephemeral-btrfs-root;
    };
  failures =
    system:
    map (entry: entry.message) (
      builtins.filter (
        entry: !entry.assertion && lib.hasPrefix "workstation.activationSafety requires" entry.message
      ) system.config.assertions
    );
  valid = evaluate true { boot.ephemeralBtrfsRoot.enable = true; };
  recovery = evaluate true { boot.ephemeralBtrfsRoot.enable = false; };
  refusal =
    includeRoot: extra: text:
    let
      messages = failures (evaluate includeRoot extra);
    in
    builtins.length messages == 1 && lib.hasInfix text (builtins.head messages);
in
assert failures valid == [ ];
assert failures recovery == [ ];
assert lib.all (name: builtins.hasAttr name valid.config.system.preSwitchChecks) [
  "credentials"
  "esp"
  "persistence"
  "topology"
];
assert refusal false { } "ephemeral Btrfs root contract";
assert refusal true {
  fileSystems."/".fsType = lib.mkForce "ext4";
} "ephemeral Btrfs root contract";
assert refusal true { fileSystems."/boot".device = lib.mkForce null; } "concrete vfat /boot";
assert refusal true { fileSystems."/boot".fsType = lib.mkForce "ext4"; } "concrete vfat /boot";
assert refusal true {
  users.users.fixture.hashedPasswordFile = lib.mkForce null;
} "hashedPasswordFile";
pkgs.runCommand "check-workstation-activation-config" { } ''
  echo "Activation composition: normal/recovery controls and five deliberate prerequisite refusals passed"
  touch "$out"
''
