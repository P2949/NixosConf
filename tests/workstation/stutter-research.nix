{
  pkgs,
  username,
  desktopSystem,
}:
let
  inherit (pkgs) lib;
  manifest = "/nix/store/00000000000000000000000000000000-proton-lab.json";
  # The module defaults with research forced off, independent of what the desktop enables.
  moduleDefault = desktopSystem.extendModules {
    modules = [
      {
        services.stutterBounded.research = {
          enable = lib.mkForce false;
          liveLaunch = lib.mkForce false;
        };
      }
    ];
  };
  configured =
    extra:
    (moduleDefault.extendModules {
      modules = [
        {
          services.stutterBounded.research = {
            enable = lib.mkOverride 40 true;
            protonManifest = manifest;
          }
          // extra;
        }
      ];
    }).config;
  config = configured { };
  live = configured { liveLaunch = lib.mkOverride 40 true; };
  liveWithoutResearch =
    (moduleDefault.extendModules {
      modules = [ { services.stutterBounded.research.liveLaunch = lib.mkOverride 40 true; } ];
    }).config;
  liveSettings = live.environment.etc."stutter/autotune-bounded-${username}.toml".text;
  liveWithoutResearchAssertion = lib.findFirst (
    entry: lib.hasInfix "research.liveLaunch requires" entry.message
  ) null liveWithoutResearch.assertions;
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
  dispatcherPlaced = evaluated: evaluated.environment.etc ? "stutter/research-dispatcher";
in
# The module itself is off by default; the desktop explicitly opts in.
assert !moduleDefault.config.services.stutterBounded.research.enable;
assert desktopSystem.config.services.stutterBounded.research.enable;
assert desktopSystem.config.services.stutterBounded.research.liveLaunch;
assert lib.hasInfix "research_live_launch = true"
  desktopSystem.config.environment.etc."stutter/autotune-bounded-${username}.toml".text;
# Live launch is off unless explicitly enabled, and is refused without research.
assert !moduleDefault.config.services.stutterBounded.research.liveLaunch;
assert !(lib.hasInfix "research_live_launch" settings);
assert lib.hasInfix "research_live_launch = true" liveSettings;
# The immutable dispatcher is placed in /etc only when live launch is enabled, and Steam's package
# set (which would restart polkit and reload dbus) stays untouched.
assert dispatcherPlaced desktopSystem.config;
assert dispatcherPlaced live;
assert !(dispatcherPlaced moduleDefault.config);
assert liveWithoutResearchAssertion != null && !liveWithoutResearchAssertion.assertion;
assert lib.hasPrefix "/nix/store/"
  desktopSystem.config.services.stutterBounded.research.protonManifest;
assert
  !(lib.hasInfix "research_socket_dir"
    moduleDefault.config.environment.etc."stutter/autotune-bounded-${username}.toml".text
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
