{
  programs.fuzzel = {
    enable = true;

    settings = {
      main = {
        layer = "overlay";
      };

      colors = {
        background = "1e1e1eff";
        text = "e6e6e6ff";

        prompt = "e6e6e6ff";
        placeholder = "888888ff";
        input = "ffffffff";

        match = "8aadf4ff";

        selection = "353535ff";
        "selection-text" = "ffffffff";
        "selection-match" = "8aadf4ff";

        counter = "888888ff";
        border = "555555ff";
      };

      border = {
        width = 1;
        radius = 10;
        "selection-radius" = 5;
      };
    };
  };
}