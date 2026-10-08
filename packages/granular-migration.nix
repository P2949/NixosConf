{
  pkgs,
  config,
  username,
}:
let
  homePolicy = config.home-manager.users.${username}.home.persistence."/persist";
  systemPolicy = config.environment.persistence."/persist";
  policy = pkgs.writeText "granular-migration-policy.json" (
    builtins.toJSON {
      inherit username;
      home = config.users.users.${username}.home;
      directories = map (entry: entry.dirPath) (systemPolicy.directories ++ homePolicy.directories);
      files = map (entry: entry.filePath) (systemPolicy.files ++ homePolicy.files);
    }
  );
in
pkgs.writeShellApplication {
  name = "granular-final-sync";
  runtimeInputs = [
    pkgs.rsync
    pkgs.coreutils
    pkgs.jq
    pkgs.util-linux
  ];
  text = ''
    policy=${policy}
    ${builtins.readFile ../scripts/granular-final-sync.sh}
  '';
}
