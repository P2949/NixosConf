"""Deterministic decisions from independent repeated Minecraft benchmark runs."""

import argparse
import json
import math
import random
import statistics
from pathlib import Path

SEED = 26110334
REPEATS = 5000
PRIMARY = ("server_p95_mspt", "server_p99_mspt", "ticks_over_50ms",
           "client_1pct_fps", "client_p99_ms", "worldgen_throughput")


def percentile(values, fraction):
    if not values:
        raise ValueError("empty metric")
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def frame_summary(frame_ms):
    if any(x <= 0 for x in frame_ms):
        raise ValueError("frame durations must be positive")
    p99 = percentile(frame_ms, .99)
    result = {"average_fps": 1000 / statistics.mean(frame_ms),
              "median_frame_ms": percentile(frame_ms, .5),
              "p95_frame_ms": percentile(frame_ms, .95),
              "client_p99_ms": p99, "client_1pct_fps": 1000 / p99,
              "stutters_over_50ms": sum(x > 50 for x in frame_ms),
              "stutters_over_100ms": sum(x > 100 for x in frame_ms)}
    if len(frame_ms) >= 10000:
        result["p999_frame_ms"] = percentile(frame_ms, .999)
        result["client_01pct_fps"] = 1000 / result["p999_frame_ms"]
    return result


def comparison(a, b):
    """B relative to A; confidence interval resamples runs, never frames."""
    rng = random.Random(SEED)
    base, candidate = statistics.median(a), statistics.median(b)
    if base == 0:
        delta = 0 if candidate == 0 else None
    else:
        delta = 100 * (candidate / base - 1)
    draws = []
    for _ in range(REPEATS):
        x = statistics.median(rng.choices(a, k=len(a)))
        y = statistics.median(rng.choices(b, k=len(b)))
        if x:
            draws.append(100 * (y / x - 1))
        elif y == 0:
            draws.append(0)
    return {"a_median": base, "b_median": candidate,
            "a_mean": statistics.mean(a), "b_mean": statistics.mean(b),
            "a_stdev": statistics.stdev(a), "b_stdev": statistics.stdev(b),
            "delta_pct": delta,
            "ci95": [percentile(draws, .025), percentile(draws, .975)] if draws else None}


def credible(metric, threshold, higher):
    if metric["delta_pct"] is None or metric["ci95"] is None:
        return False
    if higher:
        return metric["delta_pct"] >= threshold and metric["ci95"][0] > 0
    return metric["delta_pct"] <= -threshold and metric["ci95"][1] < 0


def decide(runs, workloads):
    by_variant = {v: [r for r in runs if r.get("variant") == v] for v in ("G1", "ZGC")}
    disqualified = {v: any(r.get("correctness") == "FAIL" or
                         any(r.get("memory_events", {}).get(k, 0) > 0
                             for k in ("oom", "oom_kill", "max")) or
                         r.get("severe_memory_high", False) for r in rows)
                    for v, rows in by_variant.items()}
    if all(disqualified.values()):
        return {"result": "FAIL", "decision": None, "rule": "both_disqualified"}
    comparisons = {}
    for workload in workloads:
        rows = {v: [r for r in by_variant[v] if r.get("workload") == workload
                    and r.get("valid") is True and r.get("correctness") == "PASS"]
                for v in by_variant}
        for variant in by_variant:
            if not disqualified[variant] and len(rows[variant]) < 5:
                return {"result": "INCONCLUSIVE", "decision": None,
                        "rule": "insufficient_valid_runs", "workload": workload, "variant": variant}
        if any(disqualified.values()):
            continue
        required = {"idle": ("cpu_pct", "rss_bytes"),
                    "steady": PRIMARY[:5],
                    "worldgen": (PRIMARY[0], PRIMARY[1], PRIMARY[2], PRIMARY[5]),
                    "contention": PRIMARY}[workload]
        comparisons[workload] = {}
        for key in required:
            if any(key not in r.get("metrics", {}) for variant in rows for r in rows[variant]):
                return {"result": "INCONCLUSIVE", "decision": None,
                        "rule": "missing_metric", "workload": workload, "metric": key}
            if any(not isinstance(r["metrics"][key], (int, float))
                   or not math.isfinite(r["metrics"][key]) or r["metrics"][key] < 0
                   for variant in rows for r in rows[variant]):
                return {"result": "INCONCLUSIVE", "decision": None,
                        "rule": "invalid_metric", "workload": workload, "metric": key}
            comparisons[workload][key] = comparison(
                [r["metrics"][key] for r in rows["G1"]],
                [r["metrics"][key] for r in rows["ZGC"]])
    if any(disqualified.values()):
        winner = "G1" if disqualified["ZGC"] else "ZGC"
        return {"result": "PASS", "decision": winner, "rule": "alternative_disqualified"}
    # Protect the local client across every measured client workload.
    for metrics in comparisons.values():
        fps = metrics.get("client_1pct_fps")
        if fps and credible(fps, 2, False):
            return {"result": "PASS", "decision": "G1", "rule": "zgc_client_regression", "comparisons": comparisons}
    g1_client_regresses = any(credible(m["client_1pct_fps"], 2, True)
                              for m in comparisons.values() if "client_1pct_fps" in m)
    latency_winners = set()
    for metrics in comparisons.values():
        if "server_p95_mspt" not in metrics:
            continue
        if credible(metrics["server_p95_mspt"], 3, False) or credible(metrics["ticks_over_50ms"], 15, False):
            latency_winners.add("ZGC")
        if not g1_client_regresses and (credible(metrics["server_p95_mspt"], 3, True) or credible(metrics["ticks_over_50ms"], 15, True)):
            latency_winners.add("G1")
    if len(latency_winners) > 1:
        return {"result": "INCONCLUSIVE", "decision": None,
                "rule": "conflicting_workload_latency_wins", "comparisons": comparisons}
    if latency_winners:
        return {"result": "PASS", "decision": latency_winners.pop(),
                "rule": "server_latency_win", "comparisons": comparisons}
    if g1_client_regresses:
        return {"result": "PASS", "decision": "ZGC", "rule": "client_performance_win", "comparisons": comparisons}
    for metrics in comparisons.values():
        throughput = metrics.get("worldgen_throughput")
        if throughput and credible(throughput, 5, True):
            return {"result": "PASS", "decision": "ZGC", "rule": "throughput_tiebreaker", "comparisons": comparisons}
    return {"result": "PASS", "decision": "G1", "rule": "baseline_tie", "comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    result = decide(data["runs"], ("idle", "steady", "worldgen", "contention"))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "analysis.md").write_text(
        f"Result: {result['result']}\n\nCollector: {result['decision']}\n\nRule: {result['rule']}\n")


if __name__ == "__main__":
    main()
