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
      { directory = ".ssh"; mode = "0700"; }
      { directory = ".gnupg"; mode = "0700"; }
      { directory = ".pki"; mode = "0700"; }
      { directory = ".android"; mode = "0700"; }
      { directory = ".codex"; mode = "0700"; }
      ".plastic4"
      ".zen"
      ".dotnet/corefx/cryptography"
      ".vscode"
      ".vscode-shared/sharedStorage"

      # Split stateful application children from declarative .config files.
      ".config/Code/User"
      ".config/Code/Backups"
      ".config/Code/Local Storage"
      ".config/Code/Session Storage"
      { directory = ".config/gh"; mode = "0700"; }
      ".config/mozilla/firefox"
      ".config/blender"
      ".config/StardewValley"
      ".config/dconf"
      ".config/Thunar"
      ".config/pulse"
      ".config/unityhub"
      ".config/unity3d/Unity/config"
      ".config/unity3d/Unity/licenses"
      ".config/Unreal Engine"
      ".config/Epic/Epic Games"
      ".config/Epic/UnrealEngine/5.8/Config"
      ".config/Epic/UnrealEngine/5.8/Content"
      ".config/Epic/UnrealEngine/5.8/Saved/Config"
      ".config/Epic/UnrealEngine/5.8/Saved/Collections"
      ".config/Epic/UnrealEngine/5.8/Saved/Autosaves"
      # Derived data costs minutes to hours to regenerate; retain explicitly.
      ".config/Epic/UnrealEngine/5.8/DerivedDataCache"
      ".config/Epic/UnrealEngine/Common/DerivedDataCache"
      ".config/Epic/UnrealEngine/Common/Zen"

      # .local is also split: no complete share/state container is persisted.
      ".local/share/Steam"
      { directory = ".local/share/keyrings"; mode = "0700"; }
      ".local/share/Trash"
      ".local/share/applications"
      ".local/share/icons/hicolor"
      ".local/share/gh"
      ".local/share/unity3d"
      ".local/share/unityhub"
      ".local/state/gh"
      ".local/state/wireplumber"
      ".local/state/.copilot"
    ];

    files = [
      # Manual configuration and intentionally retained command history.
      ".gitconfig"
      ".zshrc"
      ".bash_history"
      ".histfile"
      ".zsh_history"
      ".config/zsh/.zsh_history"
      ".pulse-cookie"
      ".config/mimeapps.list"
      ".config/pavucontrol.ini"
      ".config/Code/machineid"
      ".config/Code/Preferences"
      ".config/Code/Cookies"
      ".config/Code/Cookies-journal"
      ".config/Code/languagepacks.json"
      ".config/Epic/ProjectEditorRecords"
      ".config/Epic/UnrealEngine/Install.ini"
      ".config/Epic/UnrealEngine/Editor/EditorLayout.json"
      ".config/Epic/UnrealEngine/Editor/UInteractiveToolsPresetCollectionAsset_DefaultCollection.json"
      ".config/Epic/UnrealEngine/Editor/ProjectEditorRecords.json"
      ".config/Epic/UnrealEngine/Editor/FilterBar.json"
      ".config/Epic/UnrealEngine/Editor/ContentBrowser.json"
      ".config/Epic/UnrealEngine/Editor/DetailsView.json"
    ];
  };
}
