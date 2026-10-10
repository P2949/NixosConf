"""Paired analysis primitives; pilot data never enter the measurement estimate."""

import math
import random
import statistics


def deltas(pairs, direction):
    if direction not in ("higher-is-better", "lower-is-better"):
        raise ValueError("unsupported metric direction")
    sign = 1 if direction == "higher-is-better" else -1
    values = []
    for control, candidate in pairs:
        if not all(
            math.isfinite(value) and value > 0 for value in (control, candidate)
        ):
            raise ValueError("observations must be finite and positive")
        values.append(sign * (candidate / control - 1))
    if len(values) < 2:
        raise ValueError("at least two complete pairs required")
    return values


def sample_plan(pilot, direction, precision, minimum, maximum):
    if not (0 < precision < 1 and 2 <= minimum <= maximum):
        raise ValueError("invalid sampling policy")
    values = deltas(pilot, direction)
    estimated = math.ceil((1.96 * statistics.stdev(values) / precision) ** 2)
    return {
        "estimatedRequiredPairs": estimated,
        "measurementPairs": max(minimum, min(maximum, estimated)),
        "precisionLimitedByMaximum": estimated > maximum,
        "targetDeltaHalfWidth": precision,
    }


def sample_count(pilot, direction, precision, minimum, maximum):
    return sample_plan(pilot, direction, precision, minimum, maximum)[
        "measurementPairs"
    ]


def summarize(pairs, direction, threshold, seed, resamples=10000):
    if threshold < 0 or resamples < 1000:
        raise ValueError("invalid analysis policy")
    values = deltas(pairs, direction)
    rng = random.Random(seed)
    bootstrap = sorted(
        statistics.mean(rng.choices(values, k=len(values))) for _ in range(resamples)
    )
    interval = [bootstrap[int(0.025 * resamples)], bootstrap[int(0.975 * resamples)]]
    noise = statistics.stdev(values)
    return {
        "pairs": len(values),
        "control": {
            "mean": statistics.mean(x[0] for x in pairs),
            "median": statistics.median(x[0] for x in pairs),
            "standardDeviation": statistics.stdev(x[0] for x in pairs),
        },
        "candidate": {
            "mean": statistics.mean(x[1] for x in pairs),
            "median": statistics.median(x[1] for x in pairs),
            "standardDeviation": statistics.stdev(x[1] for x in pairs),
        },
        "pairedRelativeDeltas": values,
        "meanPairedRelativeDelta": statistics.mean(values),
        "medianPairedRelativeDelta": statistics.median(values),
        "pairedRelativeStandardDeviation": noise,
        "bootstrap95PercentInterval": interval,
        "bootstrapSeed": seed,
        "bootstrapResamples": resamples,
        "acceptanceThreshold": threshold,
        "interpretation": "improvement"
        if interval[0] > threshold
        else "regression"
        if interval[1] < -threshold
        else "inconclusive",
    }


def balanced_order(pairs, seed):
    if pairs < 2:
        raise ValueError("at least two pairs required")
    order = [index % 2 == 0 for index in range(pairs)]
    random.Random(seed).shuffle(order)
    return [
        ("control", "candidate") if control_first else ("candidate", "control")
        for control_first in order
    ]
