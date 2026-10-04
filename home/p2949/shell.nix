{ ... }:

{
  programs.zsh = {
    enable = true;

    # Zsh's real tab-completion system.
    enableCompletion = true;

    # Grey suggestions while typing, based on history/completion.
    autosuggestion = {
      enable = true;
      strategy = [
        "history"
        "completion"
      ];
    };

    # Green valid commands / red invalid commands.
    syntaxHighlighting = {
      enable = true;

      styles = {
        "command" = "fg=green";
        "builtin" = "fg=green";
        "function" = "fg=green";
        "alias" = "fg=green";
        "hashed-command" = "fg=green";
        "reserved-word" = "fg=green";
        "precommand" = "fg=green";

        "unknown-token" = "fg=red";
      };
    };

    history = {
      size = 50000;
      save = 50000;

      ignoreDups = true;
      ignoreSpace = true;
      share = true;
    };

    initContent = ''
      # ------------------------------------------------------------
      # Prefix-aware history search
      #
      # Type:
      #   blender
      #
      # then UP only searches commands beginning with "blender".
      # ------------------------------------------------------------

      bindkey -e

      bindkey "''${terminfo[kcuu1]}" history-beginning-search-backward
      bindkey "''${terminfo[kcud1]}" history-beginning-search-forward


      # ------------------------------------------------------------
      # Interactive completion menu
      #
      # Gives you the highlighted "box" around the currently
      # selected completion candidate.
      # ------------------------------------------------------------

      zmodload -i zsh/complist

      setopt AUTO_MENU
      setopt COMPLETE_IN_WORD

      zstyle ':completion:*' menu select

      # Case-insensitive completion.
      zstyle ':completion:*' matcher-list \
        'm:{a-zA-Z}={A-Za-z}'

      # Keep completion groups visually organized.
      zstyle ':completion:*' group-name ""

      # Show useful descriptions where completion provides them.
      zstyle ':completion:*' verbose yes
    '';
  };

  # Git-aware prompt.
  programs.starship = {
    enable = true;
    enableZshIntegration = true;

    settings = {
      add_newline = false;
    };
  };
}
