{ ... }:
{
  # Avoid grouped expressions: this pinned NixOS also interpolates each pattern
  # into an unquoted shell conditional before passing it to grep -E.
  system.forbiddenDependenciesRegexes = [
    "-nixos-opt-cpu-"
    "-nixos-opt-lto-"
    "-nixos-opt-pgo-"
    "-nixos-opt-bolt-"
  ];
}
