{
  inputs,
  pkgs,
}:

let
  liquidctlPython = pkgs.python3Packages.liquidctl.overrideAttrs (_old: {
    version = "1.17.0.dev22+g48e8dd07b";
    src = inputs.liquidctl-pr886;
  });
in
{
  pythonPackage = liquidctlPython;

  application = pkgs.python3Packages.toPythonApplication liquidctlPython;
}
