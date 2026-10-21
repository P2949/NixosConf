{ lact }:
lact.overrideAttrs (old: {
  # Auto retains manual firmware heuristics on Navi 48. Restore mode 0 first
  # so Stock/Default work through GUI, CLI, reload and GameMode selections.
  patches = (old.patches or [ ]) ++ [ ./lact-auto-reset.patch ];
})
