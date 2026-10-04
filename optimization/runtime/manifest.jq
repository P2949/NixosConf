def emptyToNull:
  if . == "" then null else . end;

def numberOrNull:
  if . == null or . == "" then null else tonumber end;

def boolean01OrNull:
  if . == null or . == "" then
    null
  elif . == "1" then
    true
  elif . == "0" then
    false
  else
    error("expected 0 or 1, got: \(.)")
  end;

{
  schemaVersion: 1,
  kind: "nixos-optimization-runtime-manifest",

  collector: {
    repositoryRevision: $collectorRevision,
    repositoryNarHash: $collectorNarHash
  },

  capture: {
    capturedAtUtc: $capturedAtUtc,
    bootId: ($bootId | emptyToNull)
  },

  system: {
    hostname: ($hostname | emptyToNull),
    currentSystemStorePath: ($currentSystem | emptyToNull),
    bootedSystemStorePath: ($bootedSystem | emptyToNull),
    currentMatchesBooted:
      if $currentSystem == "" or $bootedSystem == "" then
        null
      else
        $currentSystem == $bootedSystem
      end
  },

  kernel: {
    release: $kernelRelease,
    commandLine: $kernelCommandLine
  },

  cpu: {
    identity: {
      vendorId: ($vendorId | emptyToNull),
      family: ($cpuFamily | numberOrNull),
      model: ($cpuModel | numberOrNull),
      modelName: ($modelName | emptyToNull),
      stepping: ($stepping | numberOrNull),
      microcode: ($microcode | emptyToNull)
    },

    topology: {
      onlineCpus: ($onlineCpus | emptyToNull),
      presentCpus: ($presentCpus | emptyToNull),
      isolatedCpus: ($isolatedCpus | emptyToNull),
      nohzFullCpus: ($nohzFullCpus | emptyToNull),
      smtActive: ($smtActive | boolean01OrNull),
      smtControl: ($smtControl | emptyToNull),
      lscpu: $lscpu
    },

    frequency: {
      policies:
        (
          $cpufreqPolicies
          | sort_by(.policy | sub("^policy"; "") | tonumber)
          | map(
              .minFrequencyKHz |= numberOrNull
              | .maxFrequencyKHz |= numberOrNull
              | .hardwareMinFrequencyKHz |= numberOrNull
              | .hardwareMaxFrequencyKHz |= numberOrNull
            )
        ),

      intelPstate: {
        status: ($intelPstateStatus | emptyToNull),
        noTurbo: ($intelPstateNoTurbo | boolean01OrNull),

        turboEnabled:
          if $intelPstateNoTurbo == "0" then
            true
          elif $intelPstateNoTurbo == "1" then
            false
          else
            null
          end,

        minPerfPct: ($intelPstateMinPerfPct | numberOrNull),
        maxPerfPct: ($intelPstateMaxPerfPct | numberOrNull),
        hwpDynamicBoost:
          ($intelPstateHwpDynamicBoost | boolean01OrNull)
      }
    },

    idle: {
      driver: ($cpuidleDriver | emptyToNull),
      governor: ($cpuidleGovernor | emptyToNull)
    },

    vulnerabilities: $vulnerabilities
  },

  memory: {
    totalKiB: ($memTotalKiB | numberOrNull),
    swapTotalKiB: ($swapTotalKiB | numberOrNull),

    transparentHugePages: {
      enabled: ($thpEnabled | emptyToNull),
      defrag: ($thpDefrag | emptyToNull)
    },

    numaBalancing: ($numaBalancing | boolean01OrNull)
  }
}
