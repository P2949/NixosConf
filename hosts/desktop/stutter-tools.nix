{ lib, pkgs, ... }:

{
  # Tools the Stutter evidence phases (W26-W30) import from or drive. They are inert on PATH (no service of any of them is enabled):
  # nothing here starts a service, changes a kernel setting or widens a privileged surface.
  environment.systemPackages = [
    pkgs.perf
    pkgs.fio
    pkgs.iperf3
    pkgs.wrk2
    pkgs.nghttp2 # h2load
    pkgs.numactl
    pkgs.llvmPackages.bolt
    pkgs.blktrace
    pkgs.bcc
    pkgs.hyperfine
    pkgs.ananicy-cpp
    pkgs.system76-scheduler
    pkgs.tuned
    pkgs.bpftune
    pkgs.hwloc
    pkgs.scx.full
    pkgs.likwid
    pkgs.bpftrace
    pkgs.trace-cmd
    pkgs.rt-tests
    pkgs.kernelshark
    pkgs.irqbalance
    pkgs.tlp
    pkgs.power-profiles-daemon
    pkgs.auto-cpufreq
    pkgs.sysstat
    pkgs.tuna
    pkgs.stress-ng
    pkgs.sysbench
    pkgs.thermald
    pkgs.gcc
    (lib.lowPrio pkgs.clang)
  ];
}
