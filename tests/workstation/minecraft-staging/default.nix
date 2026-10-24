{
  inputs,
  pkgs,
  desktopSystem,
}:
let
  production = desktopSystem.config.services.minecraft-servers.servers.survival;
  loader = production.package.passthru.loader;
  gamePort = production.serverProperties.server-port;
  managementPort = production.serverProperties.management-server-port;
  # Deliberately public synthetic test credential, never a production secret.
  fixtureSecret = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd";
  secretFile = "/run/minecraft-staging/management.env";
  tools = pkgs.callPackage ../../../packages/minecraft-tools { };
  python = pkgs.python3.withPackages (ps: [ ps.websockets ]);
  probeSource =
    pkgs.runCommand "minecraft-staging-probe.py"
      {
        nativeBuildInputs = [ pkgs.ruff ];
      }
      ''
        ruff format --check ${./probe.py}
        ruff check --select E4,E7,E9,F,I ${./probe.py}
        cp ${./probe.py} "$out"
      '';
  probe = pkgs.writeShellApplication {
    name = "minecraft-staging-probe";
    text = ''
      export PYTHONPATH=${tools}/${pkgs.python3.sitePackages}
      exec ${python}/bin/python3 ${probeSource} "$@"
    '';
  };
  expectedMods =
    pkgs.runCommand "minecraft-staging-expected-mods"
      {
        nativeBuildInputs = [
          pkgs.unzip
          pkgs.jq
        ];
      }
      ''
        for jar in ${production.symlinks.mods}/*.jar; do
          unzip -p "$jar" fabric.mod.json | jq -c '{id, version}'
        done > "$out"
      '';
  test = pkgs.testers.runNixOSTest {
    name = "minecraft-staging";
    nodes = {
      machine = { lib, ... }: {
        virtualisation = {
          memorySize = 4096;
          cores = 4;
          writableStore = true;
          graphics = false;
          qemu.consoles = [ "ttyS0,115200n8" ];
          qemu.options = [ "-vga none" ];
        };
        environment.systemPackages = [ probe ];
        boot.kernel.sysctl."net.ipv4.ip_forward" = lib.mkForce 0;
        networking.nat.enable = false;
        containers.minecraft-staging = {
          autoStart = false;
          ephemeral = true;
          privateNetwork = true;
          hostAddress = "10.233.77.1";
          localAddress = "10.233.77.2";
          forwardPorts = [ ];
          bindMounts = { };
          config = { ... }: {
            imports = [ inputs.nix-minecraft.nixosModules.minecraft-servers ];
            nixpkgs.overlays = [ inputs.nix-minecraft.overlay ];
            services.minecraft-servers = {
              enable = true;
              eula = true;
              openFirewall = false;
              dataDir = "/srv/minecraft-staging";
              environmentFile = secretFile;
              servers.staging = {
                enable = true;
                autoStart = true;
                inherit (production) package files;
                jvmOpts = [
                  "-Xms256M"
                  "-Xmx2G"
                  "-XX:+UseG1GC"
                  "-XX:+ExitOnOutOfMemoryError"
                ];
                symlinks.mods = production.symlinks.mods;
                serverProperties = production.serverProperties // {
                  # Offline login is confined to this disposable private network.
                  online-mode = false;
                  white-list = false;
                  enforce-whitelist = false;
                  enforce-secure-profile = false;
                  server-ip = "";
                  pause-when-empty-seconds = -1;
                  view-distance = 2;
                  simulation-distance = 2;
                  max-players = 2;
                  level-seed = "1";
                  generate-structures = false;
                  management-server-host = "127.0.0.1";
                  management-server-secret = "@MINECRAFT_MANAGEMENT_SECRET@";
                };
              };
            };
            systemd.services.staging-credential = {
              before = [ "minecraft-server-staging.service" ];
              serviceConfig = {
                Type = "oneshot";
                RemainAfterExit = true;
                RuntimeDirectory = "minecraft-staging";
                RuntimeDirectoryMode = "0700";
              };
              script = ''
                umask 077
                printf '%s\n' 'MINECRAFT_MANAGEMENT_SECRET=${fixtureSecret}' > ${secretFile}
              '';
            };
            systemd.services.minecraft-server-staging = {
              requires = [ "staging-credential.service" ];
              after = [ "staging-credential.service" ];
              serviceConfig.MemoryMax = "3G";
            };
            environment.systemPackages = [ probe ];
            networking.firewall.allowedTCPPorts = [ gamePort ];
            system.stateVersion = "26.05";
          };
        };
      };
      observer = { pkgs, ... }: {
        environment.systemPackages = [ pkgs.netcat-openbsd ];
      };
    };
    testScript = { nodes, ... }: ''
      import json
      import re
      from pathlib import Path
      from shlex import quote

      start_all()
      machine.wait_for_unit("multi-user.target")
      observer.wait_for_unit("multi-user.target")
      machine.fail("systemctl is-active --quiet container@minecraft-staging.service")
      machine.fail("test -e /srv/minecraft")
      machine.fail("test -e /persist/secrets/minecraft-management.env")
      machine.succeed("test $(cat /proc/sys/net/ipv4/ip_forward) = 0")

      def inside(command):
          return "nixos-container run minecraft-staging -- sh -c " + quote(command)

      try:
          machine.succeed("nixos-container start minecraft-staging")
          machine.wait_until_succeeds(inside("systemctl is-active --quiet minecraft-server-staging.service"))
          management = "minecraft-staging-probe management --port ${toString managementPort} --secret-file ${secretFile}"
          machine.wait_until_succeeds(inside(management), timeout=240)
          machine.succeed(inside("test ! -e /persist/secrets/minecraft-management.env"))
          machine.succeed(inside("test ! -e /srv/minecraft"))
          machine.fail(inside("systemctl cat minecraft-backup.service"))
          machine.fail(inside("systemctl cat minecraft-backup.timer"))

          # Only the host VM's private veth path reaches the game. Neither a LAN
          # address nor explicit routing through the host exposes game/management.
          observer.fail("nc -z -w 3 ${nodes.machine.networking.primaryIPAddress} ${toString gamePort}")
          observer.fail("nc -z -w 3 ${nodes.machine.networking.primaryIPAddress} ${toString managementPort}")
          observer.succeed("ip route add 10.233.77.0/24 via ${nodes.machine.networking.primaryIPAddress}")
          observer.fail("nc -z -w 3 10.233.77.2 ${toString gamePort}")
          players = ["StageProbe", "StageProbe2"]
          receipts = []
          for player in players:
              machine.succeed(f"minecraft-staging-probe game --host 10.233.77.2 --port ${toString gamePort} --expected-version ${loader.gameVersion} --player {player} --hold-seconds 90 --release-file /tmp/staging-release --ready-file /tmp/{player}-ready.json > /tmp/{player}.log 2>&1 & echo $! > /run/{player}.pid")
          for player in players:
              machine.wait_until_succeeds(f"test -s /tmp/{player}-ready.json", timeout=150)
              receipt = json.loads(machine.succeed(f"cat /tmp/{player}-ready.json"))
              assert receipt["position_acknowledged"] is True
              assert receipt["player"] == player
              receipts.append(receipt)
              machine.wait_until_succeeds(inside("cat /srv/minecraft-staging/staging/logs/latest.log") + f" | grep -F '{player} joined the game'", timeout=60)

          def both_connected():
              journal = machine.succeed(inside("cat /srv/minecraft-staging/staging/logs/latest.log"))
              for player in players:
                  machine.succeed(f"kill -0 $(cat /run/{player}.pid)")
                  machine.fail(f"grep -F '\"login\": \"passed\"' /tmp/{player}.log")
                  assert f"{player} joined the game" in journal
                  assert f"{player} left the game" not in journal

          both_connected()
          machine.succeed(inside(management + " --save"))
          both_connected()
          machine.succeed("touch /tmp/staging-release")
          for player in players:
              machine.wait_until_succeeds(f"grep -F '\"login\": \"passed\"' /tmp/{player}.log", timeout=90)
              machine.wait_until_succeeds(inside("cat /srv/minecraft-staging/staging/logs/latest.log") + f" | grep -F '{player} left the game'", timeout=60)
          assert len({receipt["uuid"] for receipt in receipts}) == 2

          journal = machine.succeed(inside("cat /srv/minecraft-staging/staging/logs/latest.log"))
          assert "Loading Minecraft ${loader.gameVersion} with Fabric Loader ${loader.loaderVersion}" in journal
          for line in Path("${expectedMods}").read_text().splitlines():
              mod = json.loads(line)
              assert re.search(r"\b" + re.escape(mod["id"]) + r"\s+" + re.escape(mod["version"]) + r"(?:\s|$)", journal), mod
          fatal_errors = r"FATAL|Exception in thread|Failed to start the minecraft server|Encountered an unexpected exception|Failed to decode packet"
          assert not re.search(fatal_errors, journal)

          machine.succeed(inside("systemctl stop minecraft-server-staging.service"))
          machine.succeed(inside("test $(systemctl show -p Result --value minecraft-server-staging.service) = success"))
          machine.succeed(inside("test -s /srv/minecraft-staging/staging/world/level.dat"))
          for receipt in receipts:
              machine.succeed(inside("test -s /srv/minecraft-staging/staging/world/players/data/" + receipt["uuid"] + ".dat"))
          # Export only the stopped world, not server.properties or credentials.
          machine.succeed(inside("tar -C /srv/minecraft-staging/staging/world -cf - .") + " > /tmp/staging-world.tar")
          machine.succeed(inside("touch /staging-disposable-proof"))
          machine.succeed("nixos-container stop minecraft-staging")
          machine.succeed("nixos-container start minecraft-staging")
          machine.wait_until_succeeds(inside("test ! -e /staging-disposable-proof"))
          machine.wait_until_succeeds(inside(management), timeout=240)
          machine.succeed(inside("systemctl stop minecraft-server-staging.service"))
          for receipt in receipts:
              machine.succeed(inside("test ! -e /srv/minecraft-staging/staging/world/players/data/" + receipt["uuid"] + ".dat"))
          machine.succeed(inside("mv /srv/minecraft-staging/staging/world /srv/minecraft-staging/staging/world.generated"))
          machine.succeed(inside("mkdir /srv/minecraft-staging/staging/world"))
          machine.succeed(inside("tar -C /srv/minecraft-staging/staging/world -xf -") + " < /tmp/staging-world.tar")
          machine.succeed(inside("chown -R minecraft:minecraft /srv/minecraft-staging/staging/world"))
          for receipt in receipts:
              machine.succeed(inside("test -s /srv/minecraft-staging/staging/world/players/data/" + receipt["uuid"] + ".dat"))
          machine.succeed(inside("systemctl start minecraft-server-staging.service"))
          machine.wait_until_succeeds(inside(management), timeout=240)
          clone = json.loads(machine.succeed("minecraft-staging-probe game --host 10.233.77.2 --port ${toString gamePort} --expected-version ${loader.gameVersion} --ready-file /tmp/staging-clone-ready.json --hold-seconds 5"))
          assert clone["login"] == "passed" and clone["uuid"] == receipts[0]["uuid"]
          assert not re.search(fatal_errors, machine.succeed(inside("cat /srv/minecraft-staging/staging/logs/latest.log")))
          machine.succeed(inside(management + " --save"))
          machine.succeed(inside("systemctl stop minecraft-server-staging.service"))
          machine.succeed(inside("test $(systemctl show -p Result --value minecraft-server-staging.service) = success"))
          machine.succeed("nixos-container stop minecraft-staging")
          machine.fail("systemctl is-active --quiet container@minecraft-staging.service")
          machine.fail("test -e /srv/minecraft")
      except Exception:
          for command in [
              "cat /tmp/StageProbe.log /tmp/StageProbe2.log",
              inside("cat /srv/minecraft-staging/staging/logs/latest.log"),
              inside("journalctl -b --no-pager -n 80"),
          ]:
              machine.log(machine.execute(command)[1])
          raise
    '';
  };
in
test
