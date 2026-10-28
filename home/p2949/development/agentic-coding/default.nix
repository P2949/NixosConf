{
  config,
  lib,
  pkgs,
  pkgsUnstable,
  inputs,
  ...
}:

let
  llamaCpp = pkgsUnstable.callPackage "${inputs.llama-cpp-src}/.devops/nix/package.nix" {
    useRocm = true;
    # Upstream expects a semicolon-separated string, not a list.
    rocmGpuTargets = "gfx1201";
    useWebUi = false;
    llamaVersion = "git-a37cc461";
  };

  model = {
    repo = "owao/Sabi-Noema-GGUF";
    revision = "63c4e5c0012e5445cea31822a40f54f2628fb8f3";
    file = "Sabi-Noema-Q3_K_M.gguf";
    size = 13301443488;
    sha256 = "7fcf50e0cc26d31655baa81a1086638b7fd5797ee7ff9eef764f3cfd02cf3e1e";
  };
  modelDir = "${config.xdg.dataHome}/local-ai/models/${model.revision}";
  modelPath = "${modelDir}/${model.file}";

  host = "127.0.0.1";
  port = 11435;
  backendPort = 11436;
  # Codex and llama-server must agree on this window; change both together.
  contextSize = 61440;
  compactLimit = 50000;

  verifyModel = ''
    verify_model() {
      local candidate="$1" actual_size actual_hash
      if [ ! -f "$candidate" ]; then
        echo "Model file missing: $candidate" >&2
        return 1
      fi
      actual_size=$(stat -Lc '%s' -- "$candidate") || return 1
      if [ "$actual_size" != ${lib.escapeShellArg (toString model.size)} ]; then
        echo "Model size mismatch: $candidate" >&2
        return 1
      fi
      actual_hash=$(sha256sum -- "$candidate") || return 1
      if [ "''${actual_hash%% *}" != ${lib.escapeShellArg model.sha256} ]; then
        echo "Model SHA-256 mismatch: $candidate" >&2
        return 1
      fi
    }
  '';

  sabiModelVerify = pkgs.writeShellApplication {
    name = "sabi-model-verify";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      ${verifyModel}
      verify_model ${lib.escapeShellArg modelPath}
      echo "Model integrity verified."
    '';
  };

  sabiModelInstall = pkgs.writeShellApplication {
    name = "sabi-model-install";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.curl
      pkgs.util-linux
    ];
    text = ''
      ${verifyModel}
      dest=${lib.escapeShellArg modelPath}
      url=${lib.escapeShellArg "https://huggingface.co/${model.repo}/resolve/${model.revision}/${model.file}"}

      mkdir -p "$(dirname "$dest")"
      exec 9>"$dest.lock"
      flock 9

      remove_quarantined() {
        for bad in "$dest".quarantine.*; do
          if [ -f "$bad" ] || [ -L "$bad" ]; then
            rm -- "$bad"
          fi
        done
      }

      if verify_model "$dest"; then
        remove_quarantined
        echo "Model already installed and verified: $dest"
        exit 0
      fi

      if [ -e "$dest" ] || [ -L "$dest" ]; then
        receipt=$(mktemp "$dest.integrity-failure.XXXXXXXX")
        actual_size=$(stat -Lc '%s' -- "$dest")
        actual_hash=$(sha256sum -- "$dest")
        printf 'time=%s\nsize=%s\nsha256=%s\n' \
          "$(date --utc --iso-8601=seconds)" "$actual_size" "''${actual_hash%% *}" > "$receipt"
        quarantine=$(mktemp "$dest.quarantine.XXXXXXXX")
        mv -T -- "$dest" "$quarantine"
      fi

      if ! { curl --fail --location --retry 5 --retry-delay 5 --continue-at - \
        --output "$dest.part" "$url" && verify_model "$dest.part"; }; then
        rm -f -- "$dest.part"
        curl --fail --location --retry 5 --retry-delay 5 \
          --output "$dest.part" "$url"
        if ! verify_model "$dest.part"; then
          rm -f -- "$dest.part"
          echo "Clean model download failed integrity verification" >&2
          exit 1
        fi
      fi
      mv "$dest.part" "$dest"
      remove_quarantined
      echo "Installed $dest"
    '';
  };

  instructions = builtins.readFile ./instructions.md;

  modelCatalog = pkgs.writeText "sabi-model-catalog.json" (
    builtins.toJSON {
      models = [
        {
          slug = "sabi-noema";
          display_name = "Sabi-Noema";
          description = "Local Sabi-Noema Q3_K_M via llama.cpp.";
          default_reasoning_level = "xhigh";
          supported_reasoning_levels =
            map
              (effort: {
                inherit effort;
                description = effort;
              })
              [
                "low"
                "medium"
                "xhigh"
              ];
          shell_type = "unified_exec";
          visibility = "list";
          supported_in_api = true;
          priority = 1;
          additional_speed_tiers = [ ];
          service_tiers = [ ];
          availability_nux = null;
          upgrade = null;
          base_instructions = instructions;
          model_messages = {
            instructions_template = instructions;
            instructions_variables = null;
            approvals = null;
            collaboration_modes = null;
            auto_review = null;
            permissions = null;
            multi_agent = null;
          };
          include_skills_usage_instructions = false;
          include_plugin_usage_instructions = false;
          include_apps_usage_instructions = false;
          default_reasoning_summary = "none";
          support_verbosity = false;
          default_verbosity = null;
          apply_patch_tool_type = null;
          web_search_tool_type = "text";
          truncation_policy = {
            mode = "tokens";
            limit = 8000;
          };
          supports_image_detail_original = false;
          context_window = contextSize;
          max_context_window = contextSize;
          effective_context_window_percent = 95;
          experimental_supported_tools = [ ];
          input_modalities = [ "text" ];
          supports_search_tool = false;
          supports_experimental_context = false;
          use_responses_lite = false;
          supports_reasoning_effort_updates = false;
          node_repl_auto_review_required = false;
          node_repl_disabled = true;
          tool_mode = "direct";
          multi_agent_version = null;
        }
      ];
    }
  );

  providerName = "llamacpp-sabi";

  backendReady = pkgs.writeShellApplication {
    name = "sabi-noema-ready";
    runtimeInputs = [
      pkgs.curl
      pkgs.coreutils
    ];
    text = ''
      deadline=$((SECONDS + 240))
      while (( SECONDS < deadline )); do
        if curl --silent --fail --max-time 2 http://${host}:${toString backendPort}/health >/dev/null; then
          exit 0
        fi
        sleep 1
      done
      echo "sabi-noema backend did not become ready within 240 seconds" >&2
      exit 1
    '';
  };

  codexSabi = pkgs.writeShellApplication {
    name = "codex-sabi";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.curl
      pkgs.systemd
      sabiModelInstall
      pkgsUnstable.codex
    ];
    text = ''
      if [ ! -f ${lib.escapeShellArg modelPath} ] || \
        [ "$(stat -Lc '%s' -- ${lib.escapeShellArg modelPath})" != ${lib.escapeShellArg (toString model.size)} ]; then
        sabi-model-install
      fi

      systemctl --user start sabi-noema-proxy.socket

      ready=0
      for _ in $(seq 1 240); do
        if curl --silent --fail --max-time 2 http://${host}:${toString port}/props >/dev/null; then
          ready=1
          break
        fi
        if ! systemctl --user --quiet is-active sabi-noema-proxy.socket; then
          break
        fi
        sleep 1
      done

      if [ "$ready" != 1 ]; then
        systemctl --user status --no-pager sabi-noema-proxy.socket sabi-noema-proxy.service sabi-noema.service || true
        journalctl --user -u sabi-noema-proxy.service -u sabi-noema.service --no-pager -n 40 || true
        echo "sabi-noema did not become ready" >&2
        exit 1
      fi

      exec codex --profile sabi --dangerously-bypass-approvals-and-sandbox "$@"
    '';
  };
in
{
  home.packages = [
    pkgsUnstable.codex
    sabiModelInstall
    sabiModelVerify
    codexSabi
  ];

  systemd.user.services.sabi-noema = {
    Unit = {
      Description = "Sabi-Noema local inference (llama.cpp, ROCm)";
      StopWhenUnneeded = true;
    };
    Service = {
      Environment = [ "HIP_VISIBLE_DEVICES=0" ];
      ExecStart = lib.concatStringsSep " " [
        "${llamaCpp}/bin/llama-server"
        "--model ${modelPath}"
        "--alias sabi-noema"
        "--host ${host}"
        "--port ${toString backendPort}"
        "--jinja"
        "--chat-template-file ${./chat-template.jinja}"
        "--n-gpu-layers all"
        "--ctx-size ${toString contextSize}"
        "--cache-ram 0"
        "--no-cache-idle-slots"
        "--cache-type-k q4_1"
        "--cache-type-v q4_1"
        "--flash-attn on"
        "--fit off"
        "--parallel 1"
        "--no-context-shift"
        "--no-reasoning-preserve"
        "--metrics"
        "--temp 1.0"
        "--top-p 0.95"
        "--top-k 20"
        "--min-p 0"
        "--repeat-penalty 1.0"
      ];
      Restart = "on-failure";
      RestartSec = 5;
    };
  };

  systemd.user.sockets.sabi-noema-proxy = {
    Unit.Description = "Sabi-Noema loopback activation socket";
    Socket = {
      ListenStream = "${host}:${toString port}";
      Accept = false;
      NoDelay = true;
    };
    Install.WantedBy = [ "sockets.target" ];
  };

  systemd.user.services.sabi-noema-proxy = {
    Unit = {
      Description = "Sabi-Noema socket proxy";
      Requires = [
        "sabi-noema.service"
        "sabi-noema-proxy.socket"
      ];
      After = [
        "sabi-noema.service"
        "sabi-noema-proxy.socket"
      ];
    };
    Service = {
      Type = "notify";
      ExecStartPre = "${backendReady}/bin/sabi-noema-ready";
      ExecStart = "${pkgs.systemd}/lib/systemd/systemd-socket-proxyd --exit-idle-time=300s ${host}:${toString backendPort}";
      TimeoutStartSec = 250;
    };
  };

  # ~/.codex/config.toml stays unmanaged; the profile lives beside it.
  home.file.".codex/sabi.config.toml".source = (pkgs.formats.toml { }).generate "sabi.config.toml" {
    model = "sabi-noema";
    model_provider = providerName;
    model_context_window = contextSize;
    model_auto_compact_token_limit = compactLimit;
    tool_output_token_limit = 8000;
    model_reasoning_effort = "xhigh";
    approval_policy = "never";
    sandbox_mode = "danger-full-access";
    web_search = "disabled";
    model_catalog_json = "${modelCatalog}";
    model_providers.${providerName} = {
      name = "Local Sabi via llama.cpp";
      base_url = "http://${host}:${toString port}/v1";
      wire_api = "responses";
      requires_openai_auth = false;
    };
  };
}
