{ pkgsUnstable, ... }:

{
  home.packages = [
    pkgsUnstable.pkgsRocm.blender
  ];
}
