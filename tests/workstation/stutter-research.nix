{
  pkgs,
  username,
  desktopSystem,
}:
let
  lib = pkgs.lib;
  manifest = "/nix/store/00000000000000000000000000000000-proton-lab.json";
  configured =
    extra:
    (desktopSystem.extendModules {
      modules = [
        {
          services.stutterBounded.research = {
            enable = true;
            protonManifest = manifest;
          }
          // extra;
        }
      ];
    }).config;
  config = configured { };
  unsafe = configured { studyDir = "/home/${username}/Development/../.local/share/Steam"; };
  unsafeManifest = configured { protonManifest = "/home/${username}/proton.json"; };
  unsafeOverlap = configured {
    steamappsDir = "/home/${username}/Development/StutterProtonStudies/steamapps";
  };
  unsafeRoot = configured { steamappsDir = "/"; };
  expectedMessage = "Stutter research requires absolute, confined study and Steam paths and an immutable Proton manifest";
  unsafeAssertion = lib.findFirst (entry: entry.message == expectedMessage) null unsafe.assertions;
  unsafeManifestAssertion = lib.findFirst (
    entry: entry.message == expectedMessage
  ) null unsafeManifest.assertions;
  unsafeOverlapAssertion = lib.findFirst (
    entry: entry.message == expectedMessage
  ) null unsafeOverlap.assertions;
  unsafeRootAssertion = lib.findFirst (
    entry: entry.message == expectedMessage
  ) null unsafeRoot.assertions;
  unit = config.systemd.units."stutter-autotune-bounded@.service".text;
  worker = config.systemd.units."stutter-privileged-worker@.service".text;
  settings = config.environment.etc."stutter/autotune-bounded-${username}.toml".text;
in
assert !desktopSystem.config.services.stutterBounded.research.enable;
assert lib.hasPrefix "/nix/store/"
  desktopSystem.config.services.stutterBounded.research.protonManifest;
assert
  !(lib.hasInfix "research_socket_dir"
    desktopSystem.config.environment.etc."stutter/autotune-bounded-${username}.toml".text
  );
assert lib.hasInfix "ProtectHome=read-only" unit;
assert lib.hasInfix ''ReadWritePaths="/home/${username}/Development/StutterProtonStudies"'' unit;
assert !(lib.hasInfix "StutterProtonStudies" worker);
assert lib.hasInfix ''research_socket_dir = "/run/stutter-autotune-${username}"'' settings;
assert lib.hasInfix
  ''research_campaign_dir = "/var/lib/stutter/autotune-${username}/research-campaign"''
  settings;
assert lib.hasInfix ''research_study_dir = "/home/${username}/Development/StutterProtonStudies"''
  settings;
assert lib.hasInfix ''research_steamapps_dir = "/home/${username}/.local/share/Steam/steamapps"''
  settings;
assert lib.hasInfix ''research_proton_manifest = "${manifest}"'' settings;
assert builtins.elem
  "d /var/lib/stutter/autotune-${username}/research-campaign 0700 ${username} users -"
  config.systemd.tmpfiles.rules;
assert unsafeAssertion != null && !unsafeAssertion.assertion;
assert unsafeManifestAssertion != null && !unsafeManifestAssertion.assertion;
assert unsafeOverlapAssertion != null && !unsafeOverlapAssertion.assertion;
assert unsafeRootAssertion != null && !unsafeRootAssertion.assertion;
pkgs.runCommand "check-stutter-research-config" { } ''touch "$out"''
