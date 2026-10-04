{
  pkgs,
  filter,
}:

pkgs.runCommand "check-optimization-runtime-manifest"
  {
    nativeBuildInputs = [
      pkgs.jq
    ];
  }
  ''
    jq -n \
      --arg collectorRevision "test-revision" \
      --arg collectorNarHash "sha256-test" \
      --arg capturedAtUtc "2026-01-01T00:00:00Z" \
      --arg hostname "test-host" \
      --arg bootId "test-boot-id" \
      --arg currentSystem "/nix/store/current-system" \
      --arg bootedSystem "/nix/store/current-system" \
      --arg kernelRelease "6.18.0" \
      --arg kernelCommandLine "quiet" \
      --arg vendorId "GenuineIntel" \
      --arg cpuFamily "6" \
      --arg cpuModel "165" \
      --arg modelName "Test CPU" \
      --arg stepping "5" \
      --arg microcode "0x100" \
      --arg onlineCpus "0-11" \
      --arg presentCpus "0-11" \
      --arg isolatedCpus "" \
      --arg nohzFullCpus "" \
      --arg smtActive "1" \
      --arg smtControl "on" \
      --arg cpuidleDriver "intel_idle" \
      --arg cpuidleGovernor "menu" \
      --arg intelPstateStatus "active" \
      --arg intelPstateNoTurbo "0" \
      --arg intelPstateMinPerfPct "16" \
      --arg intelPstateMaxPerfPct "100" \
      --arg intelPstateHwpDynamicBoost "0" \
      --arg memTotalKiB "32763864" \
      --arg swapTotalKiB "33554428" \
      --arg thpEnabled "always [madvise] never" \
      --arg thpDefrag "always defer defer+madvise [madvise] never" \
      --arg numaBalancing "0" \
      --argjson lscpu '{"lscpu":[]}' \
      --argjson cpufreqPolicies '[
        {
          "policy": "policy10",
          "affectedCpus": "10",
          "relatedCpus": "10",
          "driver": "intel_pstate",
          "governor": "powersave",
          "minFrequencyKHz": "800000",
          "maxFrequencyKHz": "5000000",
          "hardwareMinFrequencyKHz": "800000",
          "hardwareMaxFrequencyKHz": "5000000",
          "energyPerformancePreference": "balance_performance"
        },
        {
          "policy": "policy2",
          "affectedCpus": "2",
          "relatedCpus": "2",
          "driver": "intel_pstate",
          "governor": "powersave",
          "minFrequencyKHz": "800000",
          "maxFrequencyKHz": "5000000",
          "hardwareMinFrequencyKHz": "800000",
          "hardwareMaxFrequencyKHz": "5000000",
          "energyPerformancePreference": "balance_performance"
        }
      ]' \
      --argjson vulnerabilities '{
        "spectre_v2": "Mitigation: test"
      }' \
      -f ${filter} \
      > manifest.json

    jq -e '
      .schemaVersion == 1
      and .kind == "nixos-optimization-runtime-manifest"

      and .system.currentMatchesBooted == true

      and .cpu.identity.family == 6
      and .cpu.identity.model == 165
      and .cpu.identity.stepping == 5

      and .cpu.topology.smtActive == true

      and .cpu.frequency.policies[0].policy == "policy2"
      and .cpu.frequency.policies[1].policy == "policy10"

      and .cpu.frequency.policies[0].minFrequencyKHz == 800000
      and .cpu.frequency.policies[0].maxFrequencyKHz == 5000000

      and .cpu.frequency.intelPstate.noTurbo == false
      and .cpu.frequency.intelPstate.turboEnabled == true
      and .cpu.frequency.intelPstate.minPerfPct == 16
      and .cpu.frequency.intelPstate.maxPerfPct == 100
      and .cpu.frequency.intelPstate.hwpDynamicBoost == false

      and .memory.totalKiB == 32763864
      and .memory.swapTotalKiB == 33554428
      and .memory.numaBalancing == false
    ' manifest.json >/dev/null

    cp manifest.json "$out"
  ''
