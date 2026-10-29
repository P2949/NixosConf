# Local coding agent (Sabi-Noema + Codex)

```text
codex-sabi → Codex (profile "sabi") → Responses API :11435
→ systemd socket/proxy → llama-server :11436 (ROCm gfx1201) → Sabi-Noema Q3_K_M
```

Home Manager owns the feature ([agentic-coding](../home/p2949/development/agentic-coding/default.nix));
host GPU policy is unchanged and stays on the Daily LACT profile.

## Pins

- Model: `owao/Sabi-Noema-GGUF` revision `63c4e5c0012e5445cea31822a40f54f2628fb8f3`, `Sabi-Noema-Q3_K_M.gguf`, exactly 13,301,443,488 bytes,
  SHA-256 `7fcf50e0cc26d31655baa81a1086638b7fd5797ee7ff9eef764f3cfd02cf3e1e`.
  Repository, revision, file, size and SHA-256 form one model pin and change together.
- llama.cpp: source-only flake input `llama-cpp-src`, commit `a37cc46104eb50900d5ab4a9ba02a0abdac039db`, built with upstream's package expression for `gfx1201`.
- Codex: `pkgsUnstable.codex` 0.159.3, asserted by the evaluation test.
- Update only by explicit change of these pins, followed by requalification.

## Usage

```console
sabi-model-install   # one-time, resumable; also run automatically by codex-sabi
sabi-model-verify    # full size/SHA-256 verification of the installed bytes
codex-sabi           # probes the activation socket, then launches the full-access Sabi profile
```

For autonomous work use `/goal <objective + verification + constraints + stop condition>`.
`AGENTS.md` carries durable repository behavior; the model instructions carry global
agent behavior; `/goal` carries the current task contract.

Resume Sabi threads with `codex-sabi resume <id>`; the `codex resume <id>` hint Codex prints
lacks the profile and fails with "Model provider `llamacpp-sabi` not found". After a resume,
pick "Resume goal" (or `/goal resume`) to reactivate a paused goal.

Under the `sabi` profile Codex writes TUI settings changes, including folder trust, to the
read-only generated profile, so they fail. Trust a new folder through the base config: run
plain `codex` there once, or add `[projects."<path>"] trust_level = "trusted"` to
`~/.codex/config.toml`.

Operations:

```console
systemctl --user status sabi-noema-proxy.socket sabi-noema-proxy.service sabi-noema.service
sudo journalctl _SYSTEMD_USER_UNIT=sabi-noema.service -b
systemctl --user start sabi-noema-proxy.socket
curl -s http://127.0.0.1:11435/props # wakes the backend and counts as activity
```

## Behavior

- Weights live in `~/.local/share/local-ai/models/<model-revision>/<model-file>` (persisted, class R),
  never in the Nix store. A new revision installs beside the old one; remove stale revisions by hand.
  The installer verifies size and SHA-256 under its lock before accepting an existing
  file or atomically publishing a download. Invalid installed bytes are quarantined;
  a private size/hash/time receipt remains after successful replacement removes those
  bytes. An invalid resumed download is retried once from a clean download, then
  fails closed if verification still fails. `sabi-model-verify` always hashes the full
  file. `codex-sabi` checks existence and exact size at startup, invoking the installer
  when needed; use the explicit verifier to detect same-size corruption without
  hashing 13.3 GB on every agent launch.
- The frontend socket binds only `127.0.0.1:11435` and is armed at login. A connection
  starts `systemd-socket-proxyd` and its backend dependency on `127.0.0.1:11436`;
  neither port is exposed through the firewall. The proxy waits for backend readiness.
  After 300 s without traffic, the proxy exits and the backend's `StopWhenUnneeded`
  terminates llama-server completely. The socket remains available for automatic wake
  from an already-running Codex process. Cold starts reload the model and reprocess
  the prompt. Background Codex requests count as activity and postpone teardown.
  `Restart=on-failure` recovers a failed backend automatically.
- `~/.codex/sabi.config.toml` is generated; `~/.codex/config.toml` is not managed.
- **Temporary degraded mode** caps context at 49,152 tokens with a 40,000-token
  auto-compaction threshold and physical micro-batch `--ubatch-size 256`.
  Full GPU offload, `--fit off`, Q4_1 KV and Flash Attention remain enabled.
  The server, profile and model catalog agree; effective context remains 95%.
  Change `contextSize` and the compaction limit together.
- Codex uses `tool_mode = direct` (Code Mode emits items llama.cpp rejects).
- Earlier-turn reasoning is not replayed (`--no-reasoning-preserve`), so history does not spend
  the context window; reasoning within the current tool loop is kept. Reasoning levels are `low`,
  `medium` and `xhigh` (default), matching the template.
- The server uses a patched copy of the model's chat template ([chat-template.jinja](../home/p2949/development/agentic-coding/chat-template.jinja)): Codex sends developer messages after the first turn, which the stock Qwen template rejects with "System message must be at the beginning". The patch renders them in place. Re-derive it from the model's embedded template when the model changes.

## Known exclusions

- MCP servers and apps are not configured.
- Multi-agent is not enabled.
- Higher context and larger micro-batches are not accepted on the current gfx1201/HIP
  stack because qualification produced machine-level GPU faults. The temporary ceiling
  is 49,152 tokens and the accepted micro-batch is 256. No HSA or graph/checkpoint
  workaround is configured. Qualification covers the production Responses/chat path.

## Requalification triggers

Model, Codex, context/KV policy and chat-template changes require requalification.
Revisit this temporary degraded mode after a material change to llama.cpp's
HIP/Qwen/GDN implementation, ROCm, kernel/amdgpu or GPU firmware. A future
campaign should start with one fresh run at 49,152 context and the default ubatch 512;
only after that passes should repetitions or context increase.

## Command permissions

The profile uses `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`.
`codex-sabi` also intentionally passes `--dangerously-bypass-approvals-and-sandbox`:
Codex can restore permission state from thread history, so the CLI override is needed
when resuming threads created under the former restrictive policy. New and legacy-resumed
threads were physically tested with Git branch/ref changes, rebase, outside-workspace
writes and Nix daemon access without command approval dialogs or sandbox escalation.
Relaunch through the wrapper to acquire changed permissions; existing processes do not
update retroactively.

Normal Unix permissions and privilege authentication still apply. `AGENTS.md` and Sabi's
behavioral restrictions remain in force, including explicit authorization for commits,
pushes, activation and reboot. Hook trust is not bypassed.

## CPU and host RAM

Host prompt caching is disabled (`--cache-ram 0`) and idle-slot publication is
disabled (`--no-cache-idle-slots`). Normal live same-thread prefix reuse remains
available while the backend is warm. Full idle termination releases the backend
and proxy's process-owned RAM, CPU and model/KV VRAM; prompt state does not survive
cold teardown. `--load-mode auto` remains intentional: kernel-reclaimable mmap/GGUF
file cache may remain after the processes exit.

Upstream CPU polling and the logical batch default remain unchanged; no explicit
`--poll` or `--batch-size` is configured. There is no llama.cpp idle-sleep layer,
affinity, quota, HSA, mmap, swap or memory-locking workaround. Main/HIP thread CPU
activity during inference does not imply CPU layer fallback; all 65 layers are
offloaded to the GPU.

## Accepted temporary degraded mode

Physically qualified on 2026-10-29 at 49,152 context / 40,000-token compaction /
ubatch 256. The production socket path passed the 47,085-token sentinel and its
follow-up, reusing 47,081 of 47,116 follow-up input tokens. The sequential warm
correctness gate passed 32/32 unrelated requests without contamination.

The fixed temperature-zero benchmark uses 4,242 prompt tokens and 256 output tokens.
Three-run medians were **1,026.15 prompt tokens/s** and **32.33 decode tokens/s**,
compared with the historical 1,135 and 32.60. The approximately 10% prompt-performance
loss is intentionally accepted for stability; the temporary floors are 999 prompt
and 30.97 decode tokens/s. Cold-start latency is excluded from these active rates.

Three natural cold-wake cycles passed from one real Codex process, followed by
successful shell tool use, automatic recovery after a controlled backend SIGKILL,
and final natural idle teardown. Across 30 final idle samples, whole-card VRAM was
only 7.46 MiB above the 30-sample baseline median (limit: 256 MiB). The backend and
proxy were absent, the frontend socket remained active, and port 11436 had no listener.
Cold wake trades model reload latency for near-zero idle Sabi resources. No GPU fault
was recorded during accepted production qualification.
