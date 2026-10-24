# Local coding agent (Sabi-Noema + Codex)

```text
codex-sabi → Codex (profile "sabi") → Responses API → llama-server (ROCm gfx1201) → Sabi-Noema Q3_K_M
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
codex-sabi           # starts the server on demand, then launches the full-access Sabi profile
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
systemctl --user status sabi-noema
sudo journalctl _SYSTEMD_USER_UNIT=sabi-noema.service -b
systemctl --user restart sabi-noema
curl -s http://127.0.0.1:11435/props
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
- The server binds `127.0.0.1:11435` only and is not started at login. After 300 s idle,
  llama.cpp sleeps and releases model/KV VRAM; the process stays and wakes on the next request.
- `~/.codex/sabi.config.toml` is generated; `~/.codex/config.toml` is not managed.
- Context is capped at 61,440 tokens with a 50,000-token auto-compaction threshold,
  `--fit off`, Q4_1 KV and Flash Attention. The server, profile and model catalog agree;
  effective context remains 95%. Change `contextSize` and the compaction limit together.
- Codex uses `tool_mode = direct` (Code Mode emits items llama.cpp rejects).
- Earlier-turn reasoning is not replayed (`--no-reasoning-preserve`), so history does not spend
  the context window; reasoning within the current tool loop is kept. Reasoning levels are `low`,
  `medium` and `xhigh` (default), matching the template.
- The server uses a patched copy of the model's chat template ([chat-template.jinja](../home/p2949/development/agentic-coding/chat-template.jinja)): Codex sends developer messages after the first turn, which the stock Qwen template rejects with "System message must be at the beginning". The patch renders them in place. Re-derive it from the model's embedded template when the model changes.

## Known exclusions

- MCP servers and apps are not configured.
- Multi-agent is not enabled.
- Contexts above 61,440 are not accepted. A 65,536-token allocation started with full
  GPU offload and sufficient VRAM, but a 57.5K-token Responses request caused a GPU
  hang/reset during prefill. The same request passed at 61,440. Qualification applies
  to the Responses/chat path; raw `/completion` behavior is not a substitute. See
  [upstream long-context discussion](https://github.com/ggml-org/llama.cpp/issues/30884).

## Requalification triggers

Change of model file or revision, llama.cpp commit, any Codex version change, ROCm,
context size or other KV-relevant inference settings, or `chat-template.jinja` changes.

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

Upstream CPU polling remains unchanged. `--poll 0` was tested and removed because it
provided no measurable benefit: awake-idle CPU was already near zero, ggml workers
were inactive during the prefill probe, and active main/HIP thread CPU time was unchanged.
Main/HIP thread activity during generation does not imply CPU layer fallback; all 65
layers were confirmed GPU-offloaded. No affinity, quota or HSA workaround is configured.

The server explicitly allows an 8 GiB host prompt cache (`--cache-ram 8192`) to
preserve expensive prompt states for reuse. A direct switch-away/return probe serialized
1,277 MiB of state; the reported cache, including recurrent checkpoints, was 1,875 MiB,
and anonymous memory rose from about 1.10 to 2.64 GiB. Returning to that prompt reused
57,576 tokens and completed in 3.28 s. Host prompt state is therefore a measured
anonymous allocation owner, distinct from the 521 MiB CPU-mapped model buffer and
100 MiB host compute buffer. Recurrent checkpoints also consume host memory separately
(about 150 MiB each); the earlier 6.6–8.6 GiB long-session RSS is not a measurement of
serialized cache alone.

Same-thread A/B requests reused the GPU slot with either cache setting; after 300 s
idle sleep both settings reprocessed the prompt. The comparison did not establish a
material same-thread latency benefit or a 2 GiB anonymous-RAM saving, so the existing
8 GiB allowance is retained under the qualification fallback. In the serialization
probe about 2.48 GiB anonymous memory remained allocated during GPU sleep, although
wake/reload did not reuse the saved state. GPU idle sleep is a VRAM release mechanism,
not a promise to release all host allocations or preserve prompt reuse across wake.

`--load-mode auto` remains intentional: it uses mmap where supported, and mapped GGUF
pages may contribute reclaimable file cache. The dominant anonymous allocation is not
explained by mmap or CPU-offloaded layers. The original ~11 GiB observation was not
reproduced exactly.

At the long-context idle sample the host had about 19 GiB available, recent memory PSI
was zero, and Sabi had about 18 MiB swapped: no sustained memory pressure was observed.
Inspect `RssAnon`/`Pss_Anon`, `RssFile`/`Pss_File`, `MemAvailable`, swap activity and memory
pressure together, rather than RSS or free RAM alone:

```console
pid=$(systemctl --user show --property MainPID --value sabi-noema.service)
grep -E '^(Rss|Pss|Pss_Anon|Pss_File|Swap):' /proc/"$pid"/smaps_rollup
grep -E '^(VmRSS|RssAnon|RssFile|VmSwap):' /proc/"$pid"/status
free -h
cat /proc/pressure/memory
```

No mmap, host-buffer, swap or memory-locking workaround was added.

## Accepted configuration

Physically qualified on 2026-10-24 at 61,440 tokens / 50,000-token compaction, with
65/65 layers on the GPU. The Responses sentinel test processed 57,549 input tokens
(57,497 from `/tokenize`) and returned the exact marker. New and legacy-resumed agents
completed real inspect/edit/test loops; shell/test use also passed after manual `/compact`.

Measured whole-card awake VRAM was 14,748–14,753 MiB of 16,304 MiB (about 1.5 GiB headroom).
After the existing 300-second idle timeout, whole-card VRAM fell to 827 MiB and
sampled CPU was near zero. Host anonymous RSS still measured about 6.4 GiB while asleep;
model/KV VRAM release does not imply release of all host allocations.
The fixed temperature-zero chat benchmark used 4,242 prompt tokens and 256 output tokens,
with prompt caching disabled. Three-run medians were 1,135 prompt tokens/s and 32.60 decode
tokens/s, versus 1,142 and 32.63 at the old 49,152-token baseline (both regressions below 1%).
Long-context performance depends on prompt length; these rates describe the fixed short
benchmark, not the 57.5K-token test. Higher contexts remain outside acceptance.
