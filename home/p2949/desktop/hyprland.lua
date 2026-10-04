-- Clean Hyprland 0.55 configuration for the NixOS desktop.
-- Built from the previous Gentoo-era config, but intentionally removes
-- machine-state hacks that NixOS/UWSM now handles for us.
--
-- Target:
--   Hyprland 0.55.x
--   NixOS 26.05
--   programs.hyprland.withUWSM = true
--   RX 9070 XT
--   MSI MAG401QR

----------------
--- MONITORS ---
----------------

-- Use the EDID description rather than DP-3 so this survives connector
-- renumbering.  This is the proven SDR baseline:
--   3440x1440 @ 155 Hz, scale 1, 8 bpc, sRGB.
--
-- VRR is intentionally disabled here. HDR/10-bit are also intentionally
-- left out of the baseline and can be reintroduced separately.
hl.monitor({
    output = "desc:Microstep MSI MAG401QR EA5H156300816",
    mode = "3440x1440@155",
    position = "0x0",
    scale = 1,
    transform = 0,
    vrr = 0,
    bitdepth = 8,
    cm = "srgb",
})

-- Safe fallback for any newly connected or renamed output.
hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = 1,
})

-------------------
--- MY PROGRAMS ---
-------------------

local terminal = "alacritty"
local menu = "fuzzel"

---------------------------------
--- CONFIGURATION AND OPTIONS ---
---------------------------------

hl.config({
    ecosystem = {
        enforce_permissions = false,
        no_update_news = true,
        no_donation_nag = true,
    },

    general = {
        gaps_in = 0,
        gaps_out = 0,
        border_size = 0,
        resize_on_border = false,

        -- Tearing stays globally disabled. Add a narrowly matched
        -- per-game rule later only if there is a real need for it.
        allow_tearing = false,

        layout = "dwindle",
    },

    decoration = {
        rounding = 0,
        active_opacity = 1.0,
        inactive_opacity = 1.0,
        dim_inactive = false,

        shadow = {
            enabled = false,
        },

        blur = {
            enabled = false,
        },
    },

    animations = {
        enabled = false,
    },

    dwindle = {
        preserve_split = true,
    },

    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
        disable_splash_rendering = true,

        -- Disabled because this monitor/setup is being kept on the
        -- known-good fixed-refresh baseline for now.
        vrr = 0,

        enable_swallow = true,
        swallow_regex = "^(Alacritty)$",

        focus_on_activate = true,
        background_color = "rgb(000000)",

        -- Keep the old explicit reload workflow:
        -- SUPER+SHIFT+C -> hyprctl reload.
        disable_autoreload = true,

        mouse_move_enables_dpms = true,
        key_press_enables_dpms = true,
        layers_hog_keyboard_focus = true,
        always_follow_on_dnd = true,
        allow_session_lock_restore = true,
    },

    -- Keep rendering conservative while establishing the workstation
    -- baseline. HDR, FP16 and direct scanout can be tested independently.
    render = {
        direct_scanout = 0,
        cm_enabled = true,
        cm_auto_hdr = 0,
    },

    cursor = {
        hide_on_key_press = false,
        sync_gsettings_theme = true,
        enable_hyprcursor = true,
        no_warps = true,
    },

    input = {
        kb_layout = "us",
        follow_mouse = 1,
        sensitivity = 0,

        touchpad = {
            natural_scroll = false,
        },
    },
})

----------------
--- GESTURES ---
----------------

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

-------------------
--- KEYBINDINGS ---
-------------------

local mainMod = "SUPER"

-- Basics.
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + SHIFT + C", hl.dsp.exec_cmd("hyprctl reload"))

-- Under UWSM, stop the session through UWSM rather than killing Hyprland
-- directly.  This lets systemd tear down the graphical session cleanly.
hl.bind(mainMod .. " + SHIFT + E", hl.dsp.exec_cmd("uwsm stop"))

-- Focus and window movement.
local directions = {
    { vim = "H", arrow = "left",  direction = "left"  },
    { vim = "J", arrow = "down",  direction = "down"  },
    { vim = "K", arrow = "up",    direction = "up"    },
    { vim = "L", arrow = "right", direction = "right" },
}

for _, item in ipairs(directions) do
    hl.bind(mainMod .. " + " .. item.vim, hl.dsp.focus({
        direction = item.direction,
    }))

    hl.bind(mainMod .. " + " .. item.arrow, hl.dsp.focus({
        direction = item.direction,
    }))

    hl.bind(mainMod .. " + SHIFT + " .. item.vim, hl.dsp.window.move({
        direction = item.direction,
    }))

    hl.bind(mainMod .. " + SHIFT + " .. item.arrow, hl.dsp.window.move({
        direction = item.direction,
    }))
end

-- Switch workspaces and move the focused window to a workspace.
for workspace = 1, 10 do
    local key = workspace % 10

    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({
        workspace = workspace,
    }))

    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({
        workspace = workspace,
    }))
end

-- Sway-style split controls for the next tiled window.
hl.bind(mainMod .. " + B", hl.dsp.layout("preselect r"))
hl.bind(mainMod .. " + V", hl.dsp.layout("preselect d"))

-- Hyprland groups approximate Sway's tabbed containers.
hl.bind(mainMod .. " + W", hl.dsp.group.toggle())

-- Equivalent to Sway's "layout toggle split".
hl.bind(mainMod .. " + E", hl.dsp.layout("togglesplit"))

-- Fullscreen and floating.
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen())

hl.bind(mainMod .. " + SHIFT + space", hl.dsp.window.float({
    action = "toggle",
}))

-- Approximate Sway's "focus mode_toggle" by switching between a floating
-- and tiled window on the current workspace.
hl.bind(mainMod .. " + space", function()
    local activeWindow = hl.get_active_window()

    if not activeWindow then
        return
    end

    if activeWindow.floating then
        hl.dispatch(hl.dsp.window.cycle_next({ tiled = true }))
    else
        hl.dispatch(hl.dsp.window.cycle_next({ floating = true }))
    end
end)

-- SUPER+A intentionally remains unbound: Sway's "focus parent" has no
-- direct Hyprland container-tree equivalent.

-- Scratchpad equivalent using a named special workspace.
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({
    workspace = "special:magic",
}))

hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))

-- Mouse move/resize.
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), {
    mouse = true,
})

hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), {
    mouse = true,
})

-- Sway-style resize submap.
hl.bind(mainMod .. " + R", hl.dsp.submap("resize"))

hl.define_submap("resize", function()
    local resizeBinds = {
        { key = "H",     x = -10, y = 0   },
        { key = "J",     x = 0,   y = 10  },
        { key = "K",     x = 0,   y = -10 },
        { key = "L",     x = 10,  y = 0   },
        { key = "left",  x = -10, y = 0   },
        { key = "down",  x = 0,   y = 10  },
        { key = "up",    x = 0,   y = -10 },
        { key = "right", x = 10,  y = 0   },
    }

    for _, bind in ipairs(resizeBinds) do
        hl.bind(bind.key, hl.dsp.window.resize({
            x = bind.x,
            y = bind.y,
            relative = true,
        }), {
            repeating = true,
        })
    end

    hl.bind("Return", hl.dsp.submap("reset"))
    hl.bind("Escape", hl.dsp.submap("reset"))
end)

-- PipeWire/WirePlumber-native volume controls.
hl.bind("XF86AudioMute", hl.dsp.exec_cmd(
    "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"
), {
    locked = true,
})

hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd(
    "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"
), {
    locked = true,
    repeating = true,
})

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd(
    "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+"
), {
    locked = true,
    repeating = true,
})

hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd(
    "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"
), {
    locked = true,
})

-- Kept from the previous config. On this desktop these will only do
-- something when a brightnessctl-compatible backlight is present.
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(
    "brightnessctl set 5%-"
), {
    locked = true,
    repeating = true,
})

hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd(
    "brightnessctl set 5%+"
), {
    locked = true,
    repeating = true,
})

-- Screenshot the current compositor output(s) directly to the clipboard.
-- This removes the previous dependency on grimshot/sway tooling.
hl.bind("Print", hl.dsp.exec_cmd(
    "grim - | wl-copy --type image/png"
))

------------------------------
--- WINDOWS AND WORKSPACES ---
------------------------------

-- Ignore application maximize requests.
hl.window_rule({
    name = "suppress-maximize-events",
    match = {
        class = ".*",
    },
    suppress_event = "maximize",
})

-- No blanket `immediate = true` rule here.
-- The old config accidentally matched every window, despite its comment
-- saying that tearing should only be enabled for selected games.
--
-- If tearing is intentionally enabled later, first set
-- `general.allow_tearing = true`, then add an exact per-game rule such as:
--
-- hl.window_rule({
--     name = "allow-tearing-example",
--     match = {
--         class = "EXACT-GAME-CLASS",
--     },
--     immediate = true,
-- })
