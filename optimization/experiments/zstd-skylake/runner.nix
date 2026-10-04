{
  pkgs,
  stockZstd,
  optimizedZstd,
  corpus,
  experimentSpec,
  buildManifest,
  runtimeCapture,
}:

let
  stockBin = pkgs.lib.getBin stockZstd;
  optimizedBin = pkgs.lib.getBin optimizedZstd;
in
pkgs.writeShellApplication {
  name = "nixos-optimization-zstd-skylake-benchmark";

  runtimeInputs = [
    pkgs.coreutils
    pkgs.gawk
    pkgs.jq
    pkgs.util-linux
  ];

  text = ''
    if [[ "$#" -ne 1 ]]; then
      echo "usage: nixos-optimization-zstd-skylake-benchmark OUTPUT_DIR" >&2
      exit 2
    fi

    output_dir="$1"

    if [[ -e "$output_dir" ]]; then
      echo "output path already exists: $output_dir" >&2
      exit 2
    fi

    warmup_runs=2
    measurement_runs=10
    min_seconds=3
    benchmark_cpu="''${ZSTD_BENCH_CPU:-2}"

    stock_binary="${stockBin}/bin/zstd"
    candidate_binary="${optimizedBin}/bin/zstd"
    corpus_file="${corpus}/silesia"

    mkdir -p "$output_dir/raw"

    cp ${experimentSpec} \
      "$output_dir/experiment-spec.json"

    cp ${buildManifest} \
      "$output_dir/build-manifest.json"

    cp ${corpus}/files.sha256 \
      "$output_dir/corpus-files.sha256"

    cp ${corpus}/silesia.sha256 \
      "$output_dir/corpus.sha256"

    cp ${corpus}/size-bytes \
      "$output_dir/corpus-size-bytes"

    printf '%s\n' "$stock_binary" \
      > "$output_dir/control-binary-path"

    printf '%s\n' "$candidate_binary" \
      > "$output_dir/candidate-binary-path"

    printf '%s\n' "$benchmark_cpu" \
      > "$output_dir/benchmark-cpu"

    ${runtimeCapture}/bin/nixos-optimization-runtime-capture \
      "$output_dir/runtime-before.json"

    build_system="$(
      jq -r \
        '.currentSystem.storePath' \
        "$output_dir/build-manifest.json"
    )"

    runtime_system="$(
      jq -r \
        '.system.currentSystemStorePath' \
        "$output_dir/runtime-before.json"
    )"

    build_revision="$(
      jq -r \
        '.repository.revision' \
        "$output_dir/build-manifest.json"
    )"

    runtime_revision="$(
      jq -r \
        '.collector.repositoryRevision' \
        "$output_dir/runtime-before.json"
    )"

    current_matches_booted="$(
      jq -r \
        '.system.currentMatchesBooted' \
        "$output_dir/runtime-before.json"
    )"

    if [[ "$build_system" != "$runtime_system" ]]; then
      echo "build/runtime system mismatch" >&2
      echo "build:   $build_system" >&2
      echo "runtime: $runtime_system" >&2
      exit 1
    fi

    if [[ "$build_revision" != "$runtime_revision" ]]; then
      echo "build/runtime repository revision mismatch" >&2
      echo "build:   $build_revision" >&2
      echo "runtime: $runtime_revision" >&2
      exit 1
    fi

    if [[ "$current_matches_booted" != "true" ]]; then
      echo "current system does not match booted system" >&2
      exit 1
    fi

    if ! taskset -c "$benchmark_cpu" true; then
      echo "benchmark CPU is not usable: $benchmark_cpu" >&2
      exit 1
    fi

    sha256sum \
      "$stock_binary" \
      "$candidate_binary" \
      > "$output_dir/binary-sha256"

    jq -n \
      --arg controlStorePath "${stockBin}" \
      --arg candidateStorePath "${optimizedBin}" \
      --arg controlDerivation "${stockZstd.drvPath}" \
      --arg candidateDerivation "${optimizedZstd.drvPath}" \
      --arg corpusStorePath "${corpus}" \
      --arg corpusFile "$corpus_file" \
      --argjson warmupRuns "$warmup_runs" \
      --argjson measurementRuns "$measurement_runs" \
      --argjson minimumSeconds "$min_seconds" \
      --argjson benchmarkCpu "$benchmark_cpu" \
      '{
        schemaVersion: 1,
        kind: "nixos-optimization-zstd-benchmark-configuration",

        control: {
          storePath: $controlStorePath,
          derivationPath: $controlDerivation
        },

        candidate: {
          storePath: $candidateStorePath,
          derivationPath: $candidateDerivation
        },

        corpus: {
          storePath: $corpusStorePath,
          file: $corpusFile
        },

        execution: {
          warmupRuns: $warmupRuns,
          measurementRuns: $measurementRuns,
          minimumSeconds: $minimumSeconds,
          threads: 1,
          cpu: $benchmarkCpu
        }
      }' > "$output_dir/benchmark-config.json"

    measurements="$output_dir/measurements.jsonl"
    : > "$measurements"

    run_warmup() {
      local binary="$1"
      local level="$2"

      LC_ALL=C \
        taskset -c "$benchmark_cpu" \
        "$binary" \
        "-b$level" \
        -T1 \
        "-i$min_seconds" \
        "$corpus_file" \
        >/dev/null \
        2>&1
    }

    run_measurement() {
      local variant="$1"
      local binary="$2"
      local level="$3"
      local repetition="$4"
      local order="$5"

      local raw_file
      local output
      local parsed
      local compression
      local decompression

      raw_file="$output_dir/raw/level-''${level}-rep-''${repetition}-''${variant}.txt"

      if ! output="$(
        LC_ALL=C \
          taskset -c "$benchmark_cpu" \
          "$binary" \
          "-b$level" \
          -T1 \
          "-i$min_seconds" \
          "$corpus_file" \
          2>&1
      )"; then
        printf '%s\n' "$output" > "$raw_file"
        echo "benchmark command failed: $raw_file" >&2
        exit 1
      fi

      printf '%s\n' "$output" > "$raw_file"

      parsed="$(
        printf '%s\n' "$output" \
          | tr '\r' '\n' \
          | gawk '
              match($0, /, *([0-9.]+) MB\/s, *([0-9.]+) MB\/s/, values) {
                compression = values[1]
                decompression = values[2]
                found = 1
              }

              END {
                if (!found) {
                  exit 1
                }

                print compression, decompression
              }
            '
      )"

      compression="''${parsed%% *}"
      decompression="''${parsed##* }"

      jq -nc \
        --arg variant "$variant" \
        --arg binary "$binary" \
        --argjson level "$level" \
        --argjson repetition "$repetition" \
        --argjson order "$order" \
        --argjson compressionMBps "$compression" \
        --argjson decompressionMBps "$decompression" \
        --arg capturedAtUtc "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
        '{
          variant: $variant,
          binary: $binary,
          level: $level,
          repetition: $repetition,
          orderWithinRepetition: $order,
          capturedAtUtc: $capturedAtUtc,
          compressionMBps: $compressionMBps,
          decompressionMBps: $decompressionMBps
        }' >> "$measurements"

      printf \
        'level=%d repetition=%d order=%d variant=%s compression=%s MB/s decompression=%s MB/s\n' \
        "$level" \
        "$repetition" \
        "$order" \
        "$variant" \
        "$compression" \
        "$decompression"
    }

    printf '%s\n' \
      "Running warmups on CPU $benchmark_cpu"

    for level in 1 3; do
      for (( warmup = 1; warmup <= warmup_runs; warmup++ )); do
        if (( warmup % 2 == 1 )); then
          run_warmup "$stock_binary" "$level"
          run_warmup "$candidate_binary" "$level"
        else
          run_warmup "$candidate_binary" "$level"
          run_warmup "$stock_binary" "$level"
        fi
      done
    done

    printf '%s\n' \
      "Running measured repetitions on CPU $benchmark_cpu"

    for level in 1 3; do
      for (( repetition = 1; repetition <= measurement_runs; repetition++ )); do
        if (( repetition % 2 == 1 )); then
          run_measurement \
            control \
            "$stock_binary" \
            "$level" \
            "$repetition" \
            1

          run_measurement \
            candidate \
            "$candidate_binary" \
            "$level" \
            "$repetition" \
            2
        else
          run_measurement \
            candidate \
            "$candidate_binary" \
            "$level" \
            "$repetition" \
            1

          run_measurement \
            control \
            "$stock_binary" \
            "$level" \
            "$repetition" \
            2
        fi
      done
    done

    ${runtimeCapture}/bin/nixos-optimization-runtime-capture \
      "$output_dir/runtime-after.json"

    before_boot_id="$(
      jq -r \
        '.capture.bootId' \
        "$output_dir/runtime-before.json"
    )"

    after_boot_id="$(
      jq -r \
        '.capture.bootId' \
        "$output_dir/runtime-after.json"
    )"

    before_system="$(
      jq -r \
        '.system.currentSystemStorePath' \
        "$output_dir/runtime-before.json"
    )"

    after_system="$(
      jq -r \
        '.system.currentSystemStorePath' \
        "$output_dir/runtime-after.json"
    )"

    if [[ "$before_boot_id" != "$after_boot_id" ]]; then
      echo "machine rebooted during benchmark" >&2
      exit 1
    fi

    if [[ "$before_system" != "$after_system" ]]; then
      echo "current NixOS system changed during benchmark" >&2
      exit 1
    fi

    jq -s '
      def mean($values):
        ($values | add) / ($values | length);

      def median($values):
        ($values | sort) as $sorted
        | ($sorted | length) as $count
        | if ($count % 2) == 1 then
            $sorted[($count / 2 | floor)]
          else
            (
              $sorted[($count / 2) - 1]
              + $sorted[$count / 2]
            ) / 2
          end;

      def stats($values):
        {
          count: ($values | length),
          mean: mean($values),
          median: median($values),
          min: ($values | min),
          max: ($values | max)
        };

      def pairedDeltas($rows; $level; $metric):
        [
          $rows
          | map(select(.level == $level))
          | group_by(.repetition)[]
          | . as $pair

          | (
              $pair
              | map(select(.variant == "control"))
              | .[0][$metric]
            ) as $control

          | (
              $pair
              | map(select(.variant == "candidate"))
              | .[0][$metric]
            ) as $candidate

          | (($candidate / $control) - 1) * 100
        ];

      def pairedStats($values):
        stats($values)
        + {
            wins: (
              $values
              | map(select(. > 0))
              | length
            ),

            losses: (
              $values
              | map(select(. < 0))
              | length
            ),

            ties: (
              $values
              | map(select(. == 0))
              | length
            )
          };

      def values($rows; $level; $variant; $metric):
        [
          $rows[]
          | select(
              .level == $level
              and .variant == $variant
            )
          | .[$metric]
        ];

      . as $rows

      | {
          schemaVersion: 1,
          kind: "nixos-optimization-zstd-benchmark-summary",

          workloads:
            (
              [1, 3]
              | map(
                  . as $level

                  | stats(
                      values(
                        $rows;
                        $level;
                        "control";
                        "compressionMBps"
                      )
                    ) as $controlCompression

                  | stats(
                      values(
                        $rows;
                        $level;
                        "candidate";
                        "compressionMBps"
                      )
                    ) as $candidateCompression

                  | stats(
                      values(
                        $rows;
                        $level;
                        "control";
                        "decompressionMBps"
                      )
                    ) as $controlDecompression

                  | stats(
                      values(
                        $rows;
                        $level;
                        "candidate";
                        "decompressionMBps"
                      )
                    ) as $candidateDecompression

                  | {
                      level: $level,

                      compression: {
                        control: $controlCompression,
                        candidate: $candidateCompression,

                        candidateDeltaPercent:
                          (
                            (
                              $candidateCompression.mean
                              / $controlCompression.mean
                            ) - 1
                          ) * 100,

                        pairedCandidateDeltaPercent:
                          pairedStats(
                            pairedDeltas(
                              $rows;
                              $level;
                              "compressionMBps"
                            )
                          )
                      },

                      decompression: {
                        control: $controlDecompression,
                        candidate: $candidateDecompression,

                        candidateDeltaPercent:
                          (
                            (
                              $candidateDecompression.mean
                              / $controlDecompression.mean
                            ) - 1
                          ) * 100,

                        pairedCandidateDeltaPercent:
                          pairedStats(
                            pairedDeltas(
                              $rows;
                              $level;
                              "decompressionMBps"
                            )
                          )
                      }
                    }
                )
            )
        }
    ' "$measurements" > "$output_dir/summary.json"

    printf '\n%s\n' "Benchmark complete"
    jq . "$output_dir/summary.json"
  '';
}
