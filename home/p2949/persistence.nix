{ ... }:

{
  # Impermanence's NixOS module imports the Home Manager support and turns
  # these declarations into system bind mounts before user activation/login.
  # Every entry is classified in docs/ephemeral-state-audit.md.
  home.persistence."/persist" = {
    hideMounts = true;

    directories = [
      # Authoritative user data; Downloads is deliberately retained.
      "Desktop"
      "Documents"
      "Downloads"
      "Development"
      "Music"
      "Pictures"
      "Public"
      "Templates"
      "Videos"
      "Unity user templates"
      "Unreal Projects"

      # Expensive, imperatively installed Unity editor versions.
      "Unity"

      # Credentials, application identity and profiles.
      {
        directory = ".ssh";
        mode = "0700";
      }
      {
        directory = ".gnupg";
        mode = "0700";
      }
      {
        directory = ".pki";
        mode = "0700";
      }
      {
        directory = ".android";
        mode = "0700";
      }
      {
        directory = ".codex";
        mode = "0700";
      }
      ".plastic4"
      ".dotnet/corefx/cryptography"
      ".vscode"
      ".vscode-shared/sharedStorage"

      # Split stateful application children from declarative .config files.
      # Keep atomic application updates within one mounted directory. Known
      # cache children are instead bound to reset-root storage by the host.
      ".config/Code"
      ".config/git"
      {
        directory = ".config/gh";
        mode = "0700";
      }
      ".config/mozilla/firefox"
      ".config/blender"
      ".config/btop"
      ".config/StardewValley"
      ".config/dconf"
      ".config/Thunar"
      ".config/pulse"
      ".config/unityhub"
      # User-requested editor layouts, search filters and overlay preferences.
      ".config/unity3d/Preferences"
      ".config/unity3d/Unity/config"
      ".config/unity3d/Unity/licenses"
      ".config/Unreal Engine"
      ".config/Epic"

      # .local is also split: no complete share/state container is persisted.
      ".local/share/Steam"
      {
        directory = ".local/share/keyrings";
        mode = "0700";
      }
      ".local/share/Trash"
      ".local/share/applications"
      ".local/share/icons/hicolor"
      ".local/share/gh"
      ".local/share/gvfs-metadata"
      ".local/share/unity3d"
      ".local/share/unityhub"
      ".local/state/gh"
      ".local/state/wireplumber"
      ".local/state/.copilot"
      ".local/state/zsh"
      {
        directory = ".local/state/fuzzel";
        mode = "0700";
      }
    ];

    files = [
      # Manual configuration and intentionally retained command history.
      ".zshrc"
      ".bash_history"
      ".histfile"
      ".zsh_history"
      ".pulse-cookie"
    ];
  };
}
