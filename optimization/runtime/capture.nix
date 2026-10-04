{
  pkgs,
  repository,
}:

let
  repositoryRevision = repository.rev or (repository.dirtyRev or "unknown");
  repositoryNarHash = repository.narHash or "unknown";
in
pkgs.writeShellApplication {
  name = "nixos-optimization-runtime-capture";

  runtimeInputs = [
    pkgs.coreutils
    pkgs.gawk
    pkgs.gnugrep
    pkgs.jq
    pkgs.util-linux
  ];

  text = ''
    if [[ "$#" -gt 1 ]]; then
      echo "usage: nixos-optimization-runtime-capture [OUTPUT.json|-]" >&2
      exit 2
    fi

    output="''${1:--}"

    repository_revision=${pkgs.lib.escapeShellArg repositoryRevision}
    repository_nar_hash=${pkgs.lib.escapeShellArg repositoryNarHash}

    read_optional() {
      local path="$1"

      if [[ -r "$path" ]]; then
        cat "$path"
      fi
    }

    resolve_optional() {
      local path="$1"

      if [[ -e "$path" ]]; then
        readlink -f "$path"
      fi
    }

    cpu_field() {
      local wanted="$1"

      awk -F ':' -v wanted="$wanted" '
        {
          key = $1
          gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)

          if (key == wanted) {
            value = $2
            sub(/^[[:space:]]+/, "", value)
            print value
            exit
          }
        }
      ' /proc/cpuinfo
    }

    capture_cpufreq_policies() {
      local policy

      for policy in /sys/devices/system/cpu/cpufreq/policy*; do
        [[ -d "$policy" ]] || continue

        jq -n \
          --arg policy "$(basename "$policy")" \
          --arg affectedCpus "$(read_optional "$policy/affected_cpus")" \
          --arg relatedCpus "$(read_optional "$policy/related_cpus")" \
          --arg driver "$(read_optional "$policy/scaling_driver")" \
          --arg governor "$(read_optional "$policy/scaling_governor")" \
          --arg minFrequencyKHz "$(read_optional "$policy/scaling_min_freq")" \
          --arg maxFrequencyKHz "$(read_optional "$policy/scaling_max_freq")" \
          --arg hardwareMinFrequencyKHz "$(read_optional "$policy/cpuinfo_min_freq")" \
          --arg hardwareMaxFrequencyKHz "$(read_optional "$policy/cpuinfo_max_freq")" \
          --arg energyPerformancePreference "$(read_optional "$policy/energy_performance_preference")" \
          '
            def emptyToNull:
              if . == "" then null else . end;

            {
              policy: $policy,
              affectedCpus: ($affectedCpus | emptyToNull),
              relatedCpus: ($relatedCpus | emptyToNull),
              driver: ($driver | emptyToNull),
              governor: ($governor | emptyToNull),
              minFrequencyKHz: ($minFrequencyKHz | emptyToNull),
              maxFrequencyKHz: ($maxFrequencyKHz | emptyToNull),
              hardwareMinFrequencyKHz: ($hardwareMinFrequencyKHz | emptyToNull),
              hardwareMaxFrequencyKHz: ($hardwareMaxFrequencyKHz | emptyToNull),
              energyPerformancePreference:
                ($energyPerformancePreference | emptyToNull)
            }
          '
      done |
        jq -s .
    }

    capture_vulnerabilities() {
      local file
      local key
      local value
      local object='{}'

      for file in /sys/devices/system/cpu/vulnerabilities/*; do
        [[ -r "$file" ]] || continue

        key="$(basename "$file")"
        value="$(cat "$file")"

        object="$(
          jq -c \
            --arg key "$key" \
            --arg value "$value" \
            '. + {($key): $value}' \
            <<<"$object"
        )"
      done

      printf '%s\n' "$object"
    }

    captured_at_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    hostname="$(read_optional /proc/sys/kernel/hostname)"
    boot_id="$(read_optional /proc/sys/kernel/random/boot_id)"

    current_system="$(resolve_optional /run/current-system)"
    booted_system="$(resolve_optional /run/booted-system)"

    kernel_release="$(uname -r)"
    kernel_command_line="$(read_optional /proc/cmdline)"

    vendor_id="$(cpu_field vendor_id)"
    cpu_family="$(cpu_field "cpu family")"
    cpu_model="$(cpu_field model)"
    model_name="$(cpu_field "model name")"
    stepping="$(cpu_field stepping)"
    microcode="$(cpu_field microcode)"

    online_cpus="$(read_optional /sys/devices/system/cpu/online)"
    present_cpus="$(read_optional /sys/devices/system/cpu/present)"
    isolated_cpus="$(read_optional /sys/devices/system/cpu/isolated)"
    nohz_full_cpus="$(read_optional /sys/devices/system/cpu/nohz_full)"

    smt_active="$(read_optional /sys/devices/system/cpu/smt/active)"
    smt_control="$(read_optional /sys/devices/system/cpu/smt/control)"

    cpuidle_driver="$(
      read_optional /sys/devices/system/cpu/cpuidle/current_driver
    )"

    cpuidle_governor="$(
      read_optional /sys/devices/system/cpu/cpuidle/current_governor_ro
    )"

    intel_pstate_status="$(
      read_optional /sys/devices/system/cpu/intel_pstate/status
    )"

    intel_pstate_no_turbo="$(
      read_optional /sys/devices/system/cpu/intel_pstate/no_turbo
    )"

    intel_pstate_min_perf_pct="$(
      read_optional /sys/devices/system/cpu/intel_pstate/min_perf_pct
    )"

    intel_pstate_max_perf_pct="$(
      read_optional /sys/devices/system/cpu/intel_pstate/max_perf_pct
    )"

    intel_pstate_hwp_dynamic_boost="$(
      read_optional /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost
    )"

    mem_total_kib="$(
      awk '/^MemTotal:/ { print $2; exit }' /proc/meminfo
    )"

    swap_total_kib="$(
      awk '/^SwapTotal:/ { print $2; exit }' /proc/meminfo
    )"

    thp_enabled="$(
      read_optional /sys/kernel/mm/transparent_hugepage/enabled
    )"

    thp_defrag="$(
      read_optional /sys/kernel/mm/transparent_hugepage/defrag
    )"

    numa_balancing="$(
      read_optional /proc/sys/kernel/numa_balancing
    )"

    lscpu_json="$(LC_ALL=C lscpu --json)"
    cpufreq_policies="$(capture_cpufreq_policies)"
    vulnerabilities="$(capture_vulnerabilities)"

    json="$(
      jq -n \
        --arg collectorRevision "$repository_revision" \
        --arg collectorNarHash "$repository_nar_hash" \
        --arg capturedAtUtc "$captured_at_utc" \
        --arg hostname "$hostname" \
        --arg bootId "$boot_id" \
        --arg currentSystem "$current_system" \
        --arg bootedSystem "$booted_system" \
        --arg kernelRelease "$kernel_release" \
        --arg kernelCommandLine "$kernel_command_line" \
        --arg vendorId "$vendor_id" \
        --arg cpuFamily "$cpu_family" \
        --arg cpuModel "$cpu_model" \
        --arg modelName "$model_name" \
        --arg stepping "$stepping" \
        --arg microcode "$microcode" \
        --arg onlineCpus "$online_cpus" \
        --arg presentCpus "$present_cpus" \
        --arg isolatedCpus "$isolated_cpus" \
        --arg nohzFullCpus "$nohz_full_cpus" \
        --arg smtActive "$smt_active" \
        --arg smtControl "$smt_control" \
        --arg cpuidleDriver "$cpuidle_driver" \
        --arg cpuidleGovernor "$cpuidle_governor" \
        --arg intelPstateStatus "$intel_pstate_status" \
        --arg intelPstateNoTurbo "$intel_pstate_no_turbo" \
        --arg intelPstateMinPerfPct "$intel_pstate_min_perf_pct" \
        --arg intelPstateMaxPerfPct "$intel_pstate_max_perf_pct" \
        --arg intelPstateHwpDynamicBoost "$intel_pstate_hwp_dynamic_boost" \
        --arg memTotalKiB "$mem_total_kib" \
        --arg swapTotalKiB "$swap_total_kib" \
        --arg thpEnabled "$thp_enabled" \
        --arg thpDefrag "$thp_defrag" \
        --arg numaBalancing "$numa_balancing" \
        --argjson lscpu "$lscpu_json" \
        --argjson cpufreqPolicies "$cpufreq_policies" \
        --argjson vulnerabilities "$vulnerabilities" \
        -f ${./manifest.jq}
    )"

    if [[ "$output" == "-" ]]; then
      printf '%s\n' "$json"
      exit 0
    fi

    output_dir="$(dirname "$output")"
    mkdir -p "$output_dir"

    tmp="$(
      mktemp "$output_dir/.runtime-manifest.XXXXXX"
    )"

    trap 'rm -f "$tmp"' EXIT

    printf '%s\n' "$json" > "$tmp"
    mv "$tmp" "$output"

    trap - EXIT
  '';
}
