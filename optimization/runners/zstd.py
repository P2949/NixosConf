"""Spec-driven physical zstd experiment. Evidence stays private by default."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import runtime
from paired_statistics import balanced_order, sample_plan, summarize


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def parse_output(text):
    matches = re.findall(r",\s*([0-9.]+) MB/s,\s*([0-9.]+) MB/s", text)
    if not matches:
        raise ValueError("zstd throughput record missing")
    values = dict(zip(("compression", "decompression"), map(float, matches[-1])))
    if any(not math.isfinite(x) or x <= 0 for x in values.values()):
        raise ValueError("invalid zstd throughput")
    return values


def command(argv, **kwargs):
    return subprocess.run(
        argv, check=True, text=True, capture_output=True, **kwargs
    ).stdout.strip()


def run(spec_path, build_path, output, repository):
    os.umask(0o077)
    if output.resolve().is_relative_to(repository.resolve()):
        raise ValueError("evidence output must be outside source repository")
    output.mkdir(mode=0o700)  # Refuse to overwrite earlier evidence.
    (output / "raw").mkdir()
    status = "failed"

    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    def snapshot():
        value = runtime.capture()
        runtime.validate_control(
            value,
            build["workingStock"]["normal"],
            spec["physicalTarget"],
            build["workingStock"]["runtime"],
        )
        return value

    try:
        shutil.copyfile(spec_path, output / "specification.json")
        shutil.copyfile(build_path, output / "build-provenance.json")
        spec = json.loads(spec_path.read_text())
        build = json.loads(build_path.read_text())
        if spec["schemaVersion"] != 2 or build["schemaVersion"] != 1:
            raise ValueError("unsupported artifact version")
        if digest(spec_path) != build["specificationSha256"]:
            raise ValueError("specification/build hash mismatch")
        if build["source"]["dirty"] or command(
            ["git", "-C", str(repository), "status", "--porcelain"]
        ):
            raise ValueError("measurement requires clean source")
        revision = command(["git", "-C", str(repository), "rev-parse", "HEAD"])
        if revision != build["source"]["revision"]:
            raise ValueError("source/build revision mismatch")
        source_tree = command(
            ["git", "-C", str(repository), "rev-parse", "HEAD^{tree}"]
        )
        if digest(repository / "flake.lock") != build["source"]["lockSha256"]:
            raise ValueError("source/build lock mismatch")
        if build["evaluatedSystem"]["output"] != build["workingStock"]["normal"]:
            raise ValueError("evaluated system differs from stock control")
        if (
            build["source"]["lockSha256"] != build["workingStock"]["lockSha256"]
            or build["selectedNixpkgsRevision"]
            != build["workingStock"]["nixpkgsRevision"]
        ):
            raise ValueError("working-stock lock/input mismatch")
        if (
            build["evaluatedPersistentRoot"]["output"]
            != build["workingStock"]["persistentRoot"]
        ):
            raise ValueError("persistent-root control mismatch")
        if build["stage"] != spec["stage"]:
            raise ValueError("spec/build stage mismatch")
        targets = {x["id"]: x for x in spec["targets"]}
        if set(targets) != {"stock", "candidate"} or any(
            x["kind"] != "package" for x in targets.values()
        ):
            raise ValueError(
                "zstd runner supports exactly stock/candidate package targets"
            )
        if any(
            build["packages"][key]["flakeAttribute"] != value["attribute"]
            for key, value in targets.items()
        ):
            raise ValueError("target attribute/build mismatch")
        binaries = {
            key: Path(value["output"]) / "bin/zstd"
            for key, value in build["packages"].items()
        }
        corpus = Path(build["workloadCorpus"]["output"]) / "silesia"
        measured_inputs = {
            "binaries": {
                key: {"path": str(path), "sha256": digest(path)}
                for key, path in binaries.items()
            },
            "corpus": {
                "path": str(corpus),
                "sha256": digest(corpus),
                "bytes": corpus.stat().st_size,
            },
        }
        run_id = output.name
        if not run_id.startswith(spec["id"] + "-") or not run_id.endswith(
            "-" + revision[:7]
        ):
            raise ValueError(
                "run directory must identify experiment, UTC time and source revision"
            )
        execution = {
            "schemaVersion": 1,
            "kind": "nixos-experiment-execution",
            "runId": run_id,
            "sourceCommit": revision,
            "sourceTree": source_tree,
            "startedAt": now(),
            "specificationSha256": digest(spec_path),
            "buildProvenanceSha256": digest(build_path),
            "runner": {
                "path": str(Path(__file__).resolve()),
                "sha256": digest(Path(__file__)),
            },
            "measuredInputs": measured_inputs,
        }
        save("execution.json", execution)
        before = snapshot()
        save("runtime-before.json", before)
        observations = []
        summaries = {}
        for workload in spec["workloads"]:
            if (
                workload["executable"] != "bin/zstd"
                or workload["corpusId"] != build["workloadCorpus"]["id"]
            ):
                raise ValueError("unsupported command/corpus contract")
            if set(x["id"] for x in workload["metrics"]) != {
                "compression",
                "decompression",
            }:
                raise ValueError("unsupported metric contract")

            def measure(variant, phase, pair, position):
                start = snapshot()
                name = f"{workload['id']}-{phase}-{pair}-{position}-{variant}"
                argv = [
                    "taskset",
                    "-c",
                    str(workload["cpu"]),
                    str(binaries[variant]),
                    *workload["arguments"],
                    f"-i{workload['minimumSeconds']}",
                    str(corpus),
                ]
                started = now()
                result = subprocess.run(
                    argv,
                    text=True,
                    capture_output=True,
                    env={**os.environ, "LC_ALL": "C"},
                    timeout=max(120, workload["minimumSeconds"] * 3 + 30),
                )
                (output / "raw" / (name + ".txt")).write_text(
                    result.stdout + result.stderr
                )
                end = snapshot()
                save("raw/" + name + "-runtime.json", {"before": start, "after": end})
                runtime.validate_interval(start, end)
                if result.returncode:
                    raise ValueError("zstd command failed; raw output retained")
                record = {
                    "workload": workload["id"],
                    "phase": phase,
                    "pair": pair,
                    "position": position,
                    "variant": variant,
                    "startedAt": started,
                    "finishedAt": now(),
                    "argv": argv,
                    "metrics": parse_output(result.stdout + result.stderr),
                }
                observations.append(record)
                with (output / "observations.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")
                return record["metrics"]

            for index in range(workload["warmupRuns"]):
                for position, variant in enumerate(("stock", "candidate")):
                    measure(variant, "warmup", index, position)
            sampling = workload["sampling"]

            def pairs(phase, count, seed):
                result = {metric["id"]: [] for metric in workload["metrics"]}
                for index, order in enumerate(balanced_order(count, seed)):
                    values = {}
                    for position, variant in enumerate(order):
                        variant = "stock" if variant == "control" else variant
                        values[variant] = measure(variant, phase, index, position)
                    for metric in result:
                        result[metric].append(
                            (values["stock"][metric], values["candidate"][metric])
                        )
                return result

            pilot = pairs("pilot", sampling["pilotPairs"], sampling["orderSeed"])
            plans = {
                m["id"]: sample_plan(
                    pilot[m["id"]],
                    m["direction"],
                    sampling["targetDeltaHalfWidth"],
                    sampling["minimumPairs"],
                    sampling["maximumPairs"],
                )
                for m in workload["metrics"]
            }
            count = max(plan["measurementPairs"] for plan in plans.values())
            measured = pairs("measurement", count, sampling["orderSeed"] + 1)
            summaries[workload["id"]] = {
                "samplingDecision": plans,
                "pilotPairs": sampling["pilotPairs"],
                "measurementPairs": count,
                "metrics": {
                    m["id"]: summarize(
                        measured[m["id"]],
                        m["direction"],
                        sampling["effectThreshold"],
                        sampling["orderSeed"],
                    )
                    for m in workload["metrics"]
                },
            }
        if (
            command(["git", "-C", str(repository), "status", "--porcelain"])
            or command(["git", "-C", str(repository), "rev-parse", "HEAD"]) != revision
        ):
            raise ValueError("source changed during measurement")
        if (
            any(
                digest(Path(value["path"])) != value["sha256"]
                for value in measured_inputs["binaries"].values()
            )
            or digest(corpus) != measured_inputs["corpus"]["sha256"]
        ):
            raise ValueError("measured input changed during measurement")
        after = snapshot()
        save("runtime-after.json", after)
        runtime.validate_interval(before, after)
        save(
            "results.json",
            {
                "schemaVersion": 1,
                "kind": "nixos-experiment-results",
                "runId": run_id,
                "finishedAt": now(),
                "summaries": summaries,
                "observations": observations,
            },
        )
        execution["finishedAt"] = now()
        save("execution.json", execution)
        status = "complete"
    finally:
        files = {
            str(path.relative_to(output)): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        }
        save(
            "artifact-index.json",
            {
                "schemaVersion": 1,
                "kind": "nixos-experiment-artifact-index",
                "runId": output.name,
                "status": status,
                "finishedAt": now(),
                "sha256": files,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("specification", "build", "output", "repository"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        run(args.specification, args.build, args.output, args.repository)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"Experiment refused or failed: {error}", file=sys.stderr)
        sys.exit(1)
