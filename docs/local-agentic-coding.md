# Local coding agent (Sabi-Noema + Codex)

```text
codex-sabi → Codex (profile "sabi") → Responses API → llama-server (ROCm gfx1201) → Sabi-Noema Q3_K_M
```

Home Manager owns the feature ([agentic-coding](../home/p2949/development/agentic-coding/default.nix));
host GPU policy is unchanged and stays on the Daily LACT profile.

## Pins

- Model: `owao/Sabi-Noema-GGUF` revision `63c4e5c0012e5445cea31822a40f54f2628fb8f3`, `Sabi-Noema-Q3_K_M.gguf` (~13.3 GB).
- llama.cpp: source-only flake input `llama-cpp-src`, commit `a37cc46104eb50900d5ab4a9ba02a0abdac039db`, built with upstream's package expression for `gfx1201`.
- Codex: `pkgsUnstable.codex` (0.159.3 at adoption).
- Update only by explicit change of these pins, followed by requalification.

## Usage

```console
sabi-model-install   # one-time, resumable; also run automatically by codex-sabi
codex-sabi           # starts sabi-noema.service on demand, then runs codex --profile sabi
```

For autonomous work use `/goal <objective + verification + constraints + stop condition>`.
`AGENTS.md` carries durable repository behavior; the model instructions carry global
agent behavior; `/goal` carries the current task contract.

Operations:

```console
systemctl --user status sabi-noema
journalctl --user -u sabi-noema
systemctl --user restart sabi-noema
curl -s http://127.0.0.1:11435/props
```

## Behavior

- Weights live in `~/.local/share/local-ai/models/` (persisted, class R), never in the Nix store.
- The server binds `127.0.0.1:11435` only and is not started at login. After 300 s idle,
  llama.cpp sleeps and releases model/KV VRAM; the process stays and wakes on the next request.
- `~/.codex/sabi.config.toml` is generated; `~/.codex/config.toml` is not managed.
- Context is capped at 49,152 tokens with `--fit off`, Q4_1 KV and Flash Attention, so Codex's
  window matches the real allocation. Change `contextSize` and the compaction limit together.
- Codex uses `tool_mode = direct` (Code Mode emits items llama.cpp rejects).

## Known exclusions

- MCP servers and apps are not configured.
- Multi-agent is not enabled.
- Contexts above ~48K: upstream llama.cpp has a gfx1201 Flash Attention corruption bug with Qwen3.8-27B at long context. Do not raise the limit or disable Flash Attention until it is fixed and requalified.

## Requalification triggers

Change of model file, llama.cpp commit, Codex major/minor version, ROCm, or context size.
