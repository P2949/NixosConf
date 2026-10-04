{ ... }:
{
  programs.waybar = {
    enable = true;
    systemd.enable = true;

    settings = {
      mainBar = {
        layer = "top";
        position = "top";
        height = 30;
        spacing = 8;

        modules-left = [
          "hyprland/workspaces"
          "hyprland/window"
        ];

        modules-center = [
          "clock"
        ];

        modules-right = [
          "cpu"
          "memory"
          "temperature"
          "pulseaudio"
          "tray"
        ];

        "hyprland/workspaces" = {
          disable-scroll = true;
          all-outputs = true;
          on-click = "activate";
        };

        "hyprland/window" = {
          max-length = 80;
        };

        clock = {
          format = "{:%H:%M}";
          format-alt = "{:%Y-%m-%d %H:%M:%S}";
          tooltip-format = "<big>{:%A, %d %B %Y}</big>";
        };

        cpu = {
          format = "CPU {usage}%";
          tooltip = false;
        };

        memory = {
          format = "RAM {percentage}%";
          tooltip = false;
        };

        temperature = {
          hwmon-path-abs = "/sys/devices/platform/coretemp.0/hwmon";
          input-filename = "temp1_input";

          interval = 2;
          critical-threshold = 90;

          format = "CPU {temperatureC}°C";
        };

        pulseaudio = {
          format = "{volume}% ";
          format-muted = "muted ";
          format-bluetooth = "{volume}% ";
          on-click = "pavucontrol";
        };

        tray = {
          spacing = 8;
        };
      };
    };

    style = ''
      * {
        border: none;
        border-radius: 0;
        min-height: 0;
      }

      window#waybar {
        background: #000000;
        color: #ffffff;
      }

      #workspaces button {
        padding: 0 8px;
        color: #aaaaaa;
        background: transparent;
      }

      #workspaces button.active {
        color: #ffffff;
      }

      #workspaces button.urgent {
        color: #ffffff;
      }

      #window,
      #clock,
      #cpu,
      #memory,
      #temperature,
      #pulseaudio,
      #tray {
        padding: 0 8px;
      }
    '';
  };
}
