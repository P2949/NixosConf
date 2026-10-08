{
  inputs,
  pkgs,
  pkgsUnstable,
  username,
}:
let
  vmPkgs = import inputs.nixpkgs {
    system = pkgs.stdenv.hostPlatform.system;
    config.allowUnfree = true;
  };
in
vmPkgs.testers.runNixOSTest {
  name = "workstation-smoke";
  nodes.machine = { lib, ... }: {
    imports = [
      inputs.home-manager.nixosModules.home-manager
      ../../profiles/workstation.nix
      ../../modules/hardware/commander-core
      ../../modules/storage/ephemeral-btrfs-root
    ];
    _module.args = { inherit inputs username pkgsUnstable; };
    # Match the harness's immutable package configuration to the real profile.
    nixpkgs.config = lib.mkForce vmPkgs.config;
    # Guest storage/networking come from the NixOS test harness, never Disko
    # or the physical host. No controller, destructive reset or GPU workload.
    hardware.commanderCore.enable = lib.mkForce false;
    boot.ephemeralBtrfsRoot.enable = lib.mkForce false;
    boot.initrd.systemd.enable = true;
    users.mutableUsers = false;
    # Never collect/optimise the host-shared store from a guest.
    nix.gc.automatic = lib.mkForce false;
    nix.settings.auto-optimise-store = lib.mkForce false;
    users.users.${username} = {
      hashedPasswordFile = lib.mkForce null;
      password = "vm-test-only";
      uid = 1000;
    };
    home-manager = {
      useGlobalPkgs = true;
      useUserPackages = true;
      extraSpecialArgs = { inherit inputs username pkgsUnstable; };
      users.${username} = {
        imports = [ ../../home/p2949 ];
        # The harness shares the host store but not its per-user GC profile.
        home.activationGenerateGcRoot = false;
      };
    };
    virtualisation = {
      memorySize = 2048;
      cores = 2;
    };
    system.stateVersion = "26.05";
  };
  testScript =
    { nodes, ... }:
    assert !nodes.machine.boot.ephemeralBtrfsRoot.enable;
    assert !(nodes.machine.boot.initrd.systemd.services ? ephemeral-root-reset);
    ''
      machine.start()
      machine.wait_for_unit("multi-user.target")
      for service in ["dbus", "systemd-logind", "NetworkManager", "home-manager-${username}"]:
          machine.wait_for_unit(service + ".service")

      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Desktop")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Development")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Documents")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Downloads")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Music")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Pictures")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Public")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Templates")
      machine.succeed("runuser -u ${username} -- test -d /home/${username}/Videos")

      machine.succeed("grep -Fx 'XDG_PROJECTS_DIR=\"/home/${username}/Development\"' /home/${username}/.config/user-dirs.dirs")
      machine.succeed("grep -Fx 'XDG_DOCUMENTS_DIR=\"/home/${username}/Documents\"' /home/${username}/.config/user-dirs.dirs")

      machine.succeed("busctl --system list --no-pager")
      machine.succeed("nmcli general status")
      machine.succeed("test $(id -u ${username}) = 1000")
      machine.succeed("runuser -u ${username} -- sh -c 'pkcheck --action-id com.feralinteractive.GameMode.governor-helper --process $$'")
      machine.wait_for_unit("polkit.service")
      status, _ = machine.execute("runuser -u nobody -- sh -c 'pkcheck --action-id com.feralinteractive.GameMode.governor-helper --process $$'")
      assert status == 1, "GameMode helper authorization must not extend to an unrelated user"
      machine.succeed("runuser -u ${username} -- sh -c 'test -r ~/.config/hypr/hyprland.lua'")
      machine.succeed("test $(systemctl show commander-core.service -p LoadState --value) = not-found")
      machine.succeed("test -z \"$(systemctl --failed --no-legend --plain)\"")
      machine.log("Real workstation profile and Home Manager activated; XDG user directories present; hardware/reset services absent")
    '';
}
