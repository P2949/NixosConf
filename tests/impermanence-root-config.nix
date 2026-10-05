{ pkgs }:

let
  inherit (pkgs) lib;

  base = import "${pkgs.path}/nixos/lib/eval-config.nix" {
    inherit pkgs;
    system = pkgs.stdenv.hostPlatform.system;
    modules = [
      ../modules/storage/ephemeral-btrfs-root
      {
        boot.initrd.systemd.enable = true;
        boot.loader.grub.devices = [ "nodev" ];
        boot.ephemeralBtrfsRoot.enable = true;
        fileSystems."/" = {
          device = "/dev/disk/by-label/ephemeral-test";
          fsType = "btrfs";
          options = [ "subvol=@root" ];
        };
        system.stateVersion = "26.05";
      }
    ];
  };

  evaluate = module: (base.extendModules { modules = [ module ]; }).config;
  accepted = module: (builtins.tryEval (evaluate module).system.build.toplevel.drvPath).success;

  invalidCases = [
    {
      name = "non-systemd-initrd";
      module.boot.initrd.systemd.enable = lib.mkForce false;
      message = "boot.ephemeralBtrfsRoot requires a systemd initrd.";
    }
    {
      name = "non-btrfs-root";
      module.fileSystems."/".fsType = lib.mkForce "ext4";
      message = "boot.ephemeralBtrfsRoot requires / to use Btrfs.";
    }
    {
      name = "missing-root-device";
      module.fileSystems."/".device = lib.mkForce null;
      message = "boot.ephemeralBtrfsRoot requires a concrete root device.";
    }
  ]
  ++
    lib.concatMap
      (
        option:
        map
          (value: {
            name = "unsafe-${option}-${builtins.toJSON value}";
            module.boot.ephemeralBtrfsRoot.${option} = value;
            message = "Root, staging and persistence must be safe direct Btrfs subvolume names.";
          })
          [
            ""
            "."
            ".."
            "/@root"
            "@root/child"
            "@root\n"
            "@root next"
          ]
      )
      [
        "rootSubvolume"
        "stagingSubvolume"
        "persistenceSubvolume"
      ]
  ++
    map
      (conflict: {
        inherit (conflict) name;
        module.boot.ephemeralBtrfsRoot = conflict.settings;
        message = "The root, staging and persistence Btrfs subvolumes must all differ.";
      })
      [
        {
          name = "root-equals-staging";
          settings.stagingSubvolume = "@root";
        }
        {
          name = "root-equals-persistence";
          settings.rootSubvolume = "@persist";
        }
        {
          name = "staging-equals-persistence";
          settings.stagingSubvolume = "@persist";
        }
      ]
  ++
    map
      (options: {
        name = "root-options-${builtins.toJSON options}";
        module.fileSystems."/".options = lib.mkForce options;
        message = "The / mount must select boot.ephemeralBtrfsRoot.rootSubvolume with one matching subvol= option and no subvolid= override.";
      })
      [
        [ "defaults" ]
        [ "subvol=@other" ]
        [
          "subvol=@root"
          "subvol=@other"
        ]
        [
          "subvol=@root"
          "subvolid=256"
        ]
        [ "subvolid=256" ]
      ]
  ++
    map
      (allowedDescendants: {
        name = "unsafe-descendants-${builtins.toJSON allowedDescendants}";
        module.boot.ephemeralBtrfsRoot = { inherit allowedDescendants; };
        message = "allowedDescendants must contain direct relative subvolume names only.";
      })
      [
        [ "tmp/child" ]
        [ ".." ]
        [ "tmp\n" ]
        [ "" ]
      ]
  ++
    map
      (logFile: {
        name = "unsafe-log-${builtins.toJSON logFile}";
        module.boot.ephemeralBtrfsRoot = { inherit logFile; };
        message = "logFile must be a safe path relative to the persistence subvolume.";
      })
      [
        ""
        "/etc/machine-id"
        "../outside"
        "logs//reset.log"
        "logs/./reset.log"
        "logs/reset\n.log"
        "logs/"
      ];

  results = map (
    case:
    let
      config = evaluate case.module;
      failures = map (assertion: assertion.message) (lib.filter (a: !a.assertion) config.assertions);
    in
    assert lib.assertMsg (lib.elem case.message failures) "Missing assertion for ${case.name}";
    assert lib.assertMsg (
      !(builtins.tryEval config.system.build.toplevel.drvPath).success
    ) "Invalid configuration accepted: ${case.name}";
    case.name
  ) invalidCases;
in
assert lib.assertMsg (accepted {
  boot.ephemeralBtrfsRoot.logFile = "logs/reset.log";
}) "Nested reset log path rejected";
assert lib.assertMsg (accepted { }) "Default ephemeral root configuration rejected";
assert lib.assertMsg (accepted {
  fileSystems."/".options = lib.mkForce [ "subvol=/@root" ];
}) "Leading slash in root subvol= option rejected";
assert lib.assertMsg (accepted {
  boot.ephemeralBtrfsRoot.enable = lib.mkForce false;
  boot.initrd.systemd.enable = lib.mkForce false;
  fileSystems."/".fsType = lib.mkForce "ext4";
  fileSystems."/".options = lib.mkForce [ "defaults" ];
}) "Disabled module interfered with persistent root";
pkgs.runCommand "check-ephemeral-root-config"
  {
    cases = builtins.toJSON results;
  }
  ''
    printf '%s\n' "$cases" > "$out"
  ''
