{ config, pkgs, ... }:

{
  # Tools the Stutter evidence phases (W26-W30) import from or drive. They are inert on PATH:
  # nothing here starts a service, changes a kernel setting or widens a privileged surface.
  environment.systemPackages = [
    config.boot.kernelPackages.perf
    pkgs.fio
    pkgs.iperf3
    pkgs.wrk2
    pkgs.nghttp2 # h2load
    pkgs.numactl
    pkgs.llvmPackages.bolt
    pkgs.blktrace
    pkgs.bcc
    pkgs.hyperfine
  ];
}
