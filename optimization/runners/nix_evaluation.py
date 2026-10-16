"""Spec-driven physical Nix evaluation experiment. Evidence stays private by default."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import resource
import signal
import time
import subprocess
import sys

import runtime
import paired_statistics
import gc_compiler
from paired_statistics import balanced_order, sample_plan, summarize


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate_corpus(path, nix):
    corpus = json.loads(path.read_text())
    if (
        corpus.get("kind") != "nixos-nix-evaluation-corpus"
        or corpus.get("schemaVersion") != 1
    ):
        raise ValueError("unsupported evaluation corpus")
    source = corpus["source"]
    root = Path(source["path"])
    lock = json.loads((root / "flake.lock").read_text())
    if digest(root / "flake.lock") != source["lockSha256"]:
        raise ValueError("corpus lock hash mismatch")
    nodes = {
        key: node["locked"] for key, node in lock["nodes"].items() if "locked" in node
    }
    if set(nodes) != set(corpus["inputs"]):
        raise ValueError("corpus input graph mismatch")
    for key, node in nodes.items():
        recorded = corpus["inputs"][key]
        if recorded["narHash"] != node["narHash"] or recorded["revision"] != node.get(
            "rev"
        ):
            raise ValueError("corpus input identity mismatch")
    for item in [source, *corpus["inputs"].values()]:
        tree = Path(item["path"])
        if tree.parent != Path("/nix/store") or not tree.is_dir():
            raise ValueError("corpus source is not a realized store tree")
        actual = command(
            [
                str(nix),
                "--extra-experimental-features",
                "nix-command",
                "hash",
                "path",
                "--type",
                "sha256",
                "--sri",
                str(tree),
            ]
        )
        if actual != item["narHash"]:
            raise ValueError("corpus source NAR hash mismatch")
    return corpus


def validate_libraries(build):
    if build.get("kind") != "nixos-nix-evaluation-build":
        raise ValueError("unsupported evaluation build manifest")
    if build.get("stage", {}).get("kind") == "gc-compiler-comparison":
        return gc_compiler.validate_measurement(build)
    if "compilerComparison" in build:
        raise ValueError("compiler comparison requires an explicit compiler stage")
    if build["collectorPolicy"] != {
        "enableLargeConfig": True,
        "initialMarkStackSize": 1048576,
    }:
        raise ValueError("collector policy mismatch")
    stock, candidate = (build["libraries"][key] for key in ("stock", "candidate"))
    for key in ("source", "version", "configureFlags", "makeFlags"):
        if stock[key] != candidate[key]:
            raise ValueError("GC policy/source changed alongside CPU targeting")
    if (
        "--enable-large-config" not in stock["configureFlags"]
        or "CFLAGS_EXTRA=-DINITIAL_MARK_STACK_SIZE=1048576" not in stock["makeFlags"]
    ):
        raise ValueError("Nix collector settings missing")
    stage = build["stage"]["parameters"]
    expected = f"-march={stage['march']} -mtune={stage['mtune']}"
    if stock["compileFlags"].strip() or candidate["compileFlags"].strip() != expected:
        raise ValueError("unexpected GC compile flags")
    if stage["packageAllowList"] != ["boehm-gc"]:
        raise ValueError("GC package allow-list mismatch")
    if any(
        Path(value["output"]).parent != Path("/nix/store")
        for value in build["libraries"].values()
    ):
        raise ValueError("GC package is not a store output")
    return {
        key: (Path(value["output"]) / "lib/libgc.so.1").resolve(strict=True)
        for key, value in build["libraries"].items()
    }


def support_modules(build):
    modules = {"runtime": runtime, "statistics": paired_statistics}
    if build.get("stage", {}).get("kind") == "gc-compiler-comparison":
        modules["gcCompiler"] = gc_compiler
    return modules


def process_binding(pid, executable, library, proc_root=Path("/proc")):
    process = proc_root / str(pid)
    observed = (process / "exe").resolve(strict=True)
    if observed != executable:
        return None  # taskset/the shell may not have exec'ed Nix yet.
    maps = (process / "maps").read_text()
    libraries = set()
    for line in maps.splitlines():
        fields = line.split()
        if len(fields) >= 6 and Path(fields[5]).name.startswith("libgc.so."):
            if len(fields) != 6:
                raise ValueError("GC mapping is deleted or ambiguous")
            libraries.add(fields[5])
    if not libraries:
        return None  # The dynamic loader has not mapped GC yet.
    if libraries != {str(library)}:
        raise ValueError("workload loaded an unexpected GC library")
    return {
        "pid": pid,
        "executable": str(observed),
        "gcMappings": sorted(libraries),
        "observedAt": now(),
    }


def execute_observation(argv, state, executable, library, raw_prefix):
    state.mkdir(mode=0o700)
    for name in ("home", "cache", "config", "state"):
        (state / name).mkdir(mode=0o700)
    env = {
        "PATH": os.environ["PATH"],
        "LC_ALL": "C",
        "TZ": "UTC",
        "HOME": str(state / "home"),
        "XDG_CACHE_HOME": str(state / "cache"),
        "XDG_CONFIG_HOME": str(state / "config"),
        "XDG_STATE_HOME": str(state / "state"),
        "NIX_USER_CONF_FILES": "/dev/null",
        "NIX_CONF_DIR": str(state / "config"),
        "NIX_CONFIG": "experimental-features = nix-command flakes\naccept-flake-config = false\n",
    }
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    receipt = {
        "startedAt": now(),
        "argv": argv,
        "stateDirectory": str(state),
        "environment": env,
        "monotonicStart": started,
        "childUsageBefore": {
            "user": usage_before.ru_utime,
            "system": usage_before.ru_stime,
        },
    }
    process = None
    try:
        with (
            raw_prefix.with_suffix(".stdout").open("w") as stdout,
            raw_prefix.with_suffix(".stderr").open("w") as stderr,
        ):
            process = subprocess.Popen(
                argv, stdout=stdout, stderr=stderr, env=env, start_new_session=True
            )
            deadline = time.monotonic() + 10
            binding = None
            while binding is None and time.monotonic() < deadline:
                if process.poll() is not None:
                    raise ValueError(
                        "workload exited before library identity was observed"
                    )
                try:
                    binding = process_binding(process.pid, executable, library)
                except FileNotFoundError:
                    pass
                if binding is None:
                    time.sleep(0.01)
            if binding is None:
                raise ValueError("workload library observation timed out")
            receipt["binding"] = binding
            process.wait(timeout=max(1, 1200 - (time.monotonic() - started)))
            if process.returncode:
                raise ValueError("Nix evaluation failed; raw output retained")
    except BaseException as error:
        receipt["error"] = str(error)
        raise
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            receipt["returncode"] = process.returncode
        usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        receipt["finishedAt"] = now()
        receipt["monotonicEnd"] = time.monotonic()
        receipt["childUsageAfter"] = {
            "user": usage_after.ru_utime,
            "system": usage_after.ru_stime,
        }
        receipt["metrics"] = {
            "wallTime": receipt["monotonicEnd"] - started,
            "cpuTime": (usage_after.ru_utime + usage_after.ru_stime)
            - (usage_before.ru_utime + usage_before.ru_stime),
        }
        raw_prefix.with_suffix(".receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        )
    if any(
        not math.isfinite(value) or value <= 0 for value in receipt["metrics"].values()
    ):
        raise ValueError("invalid evaluation timing")
    return receipt["metrics"]


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
    (output / "state").mkdir()
    status = "failed"
    snapshot_counter = 0

    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    def snapshot():
        nonlocal snapshot_counter
        value = runtime.capture()
        save(f"runtime-observed-{snapshot_counter:04d}.json", value)
        snapshot_counter += 1
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
        if (
            len(spec["workloads"]) != 1
            or spec["workloads"][0]["id"] != "repository-evaluation"
        ):
            raise ValueError("unsupported evaluation workload")
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
                "evaluation runner supports exactly stock/candidate package targets"
            )
        attributes = (
            gc_compiler.target_attributes(build)
            if build["stage"]["kind"] == "gc-compiler-comparison"
            else {
                key: value["flakeAttribute"] for key, value in build["packages"].items()
            }
        )
        if any(attributes[key] != value["attribute"] for key, value in targets.items()):
            raise ValueError("target attribute/build mismatch")
        if build.get("targetExpression") is not None:
            expression = repository / gc_compiler.expression_path(build)
            gc_compiler.validate_expression_file(build, expression)
            shutil.copyfile(expression, output / "source-expression.nix")
        binaries = {
            key: Path(value["output"]) / "bin/nix-evaluation"
            for key, value in build["packages"].items()
        }
        libraries = validate_libraries(build)
        consumer = (
            Path(build["consumer"]["output"]) / build["consumer"]["executable"]
        ).resolve(strict=True)
        corpus = Path(build["workloadCorpus"]["output"])
        corpus_identity = validate_corpus(corpus, consumer)
        if "compilerComparison" in build:
            gc_compiler.validate_benchmark(build, corpus_identity)
        shutil.copyfile(corpus, output / "corpus.json")
        measured_inputs = {
            "binaries": {
                key: {"path": str(path), "sha256": digest(path)}
                for key, path in binaries.items()
            },
            "libraries": {
                key: {"path": str(path), "sha256": digest(path)}
                for key, path in libraries.items()
            },
            "consumer": {"path": str(consumer), "sha256": digest(consumer)},
            "corpus": {
                "path": str(corpus),
                "sha256": digest(corpus),
                "identity": corpus_identity,
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
                "supportModules": {
                    name: {
                        "path": str(Path(module.__file__).resolve()),
                        "sha256": digest(Path(module.__file__)),
                    }
                    for name, module in support_modules(build).items()
                },
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
                workload["executable"] != "bin/nix-evaluation"
                or workload["corpusId"] != build["workloadCorpus"]["id"]
            ):
                raise ValueError("unsupported command/corpus contract")
            if set(x["id"] for x in workload["metrics"]) != {
                "wallTime",
                "cpuTime",
            }:
                raise ValueError("unsupported metric contract")

            def measure(variant, phase, pair, position):
                start = snapshot()
                runtime.validate_interval(before, start)
                name = f"{workload['id']}-{phase}-{pair}-{position}-{variant}"
                save("raw/" + name + "-runtime.json", {"before": start})
                expected_arguments = [
                    "flake",
                    "check",
                    "@source@",
                    "--offline",
                    "--no-build",
                    "--no-write-lock-file",
                    "--no-eval-cache",
                ]
                if workload["arguments"] != expected_arguments or any(
                    metric["direction"] != "lower-is-better"
                    for metric in workload["metrics"]
                ):
                    raise ValueError("unsupported evaluation argument/metric contract")
                argv = [
                    "taskset",
                    "-c",
                    str(workload["cpu"]),
                    str(binaries[variant]),
                    *[
                        corpus_identity["source"]["path"]
                        if item == "@source@"
                        else item
                        for item in workload["arguments"]
                    ],
                ]
                started = now()
                try:
                    metrics = execute_observation(
                        argv,
                        output / "state" / name,
                        consumer,
                        libraries[variant],
                        output / "raw" / name,
                    )
                finally:
                    end = runtime.capture()
                    save(
                        "raw/" + name + "-runtime.json", {"before": start, "after": end}
                    )
                    runtime.validate_control(
                        end,
                        build["workingStock"]["normal"],
                        spec["physicalTarget"],
                        build["workingStock"]["runtime"],
                    )
                    runtime.validate_interval(start, end)
                    runtime.validate_interval(before, end)
                if metrics["wallTime"] < workload["minimumSeconds"]:
                    raise ValueError("evaluation was shorter than the declared minimum")
                record = {
                    "workload": workload["id"],
                    "phase": phase,
                    "pair": pair,
                    "position": position,
                    "variant": variant,
                    "startedAt": started,
                    "finishedAt": now(),
                    "argv": argv,
                    "metrics": metrics,
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
            or digest(consumer) != measured_inputs["consumer"]["sha256"]
            or any(
                digest(path) != measured_inputs["libraries"][key]["sha256"]
                for key, path in libraries.items()
            )
        ):
            raise ValueError("measured input changed during measurement")
        validate_corpus(corpus, consumer)
        if "compilerComparison" in build:
            validate_libraries(build)
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
            if path.is_file() and path.relative_to(output).parts[0] != "state"
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


def verify(output):
    def read(name):
        return json.loads((output / name).read_text())

    index = read("artifact-index.json")
    if index.get("status") != "complete":
        raise ValueError("evidence run is not complete")
    actual_files = {
        str(path.relative_to(output))
        for path in output.rglob("*")
        if path.is_file()
        and path.relative_to(output).parts[0] != "state"
        and str(path.relative_to(output)) != "artifact-index.json"
    }
    if set(index["sha256"]) != actual_files:
        raise ValueError("artifact index file set mismatch")
    for name, expected in index["sha256"].items():
        path = output / name
        if not path.resolve().is_relative_to(output.resolve()) or path.is_symlink():
            raise ValueError("artifact path escapes evidence directory")
        if digest(path) != expected:
            raise ValueError("artifact hash mismatch: " + name)
    spec, build, execution, results = [
        read(name)
        for name in (
            "specification.json",
            "build-provenance.json",
            "execution.json",
            "results.json",
        )
    ]
    if (
        digest(output / "specification.json") != build["specificationSha256"]
        or digest(output / "specification.json") != execution["specificationSha256"]
    ):
        raise ValueError("specification identity mismatch")
    if digest(output / "build-provenance.json") != execution["buildProvenanceSha256"]:
        raise ValueError("build identity mismatch")
    if (
        build["source"]["dirty"]
        or execution["sourceCommit"] != build["source"]["revision"]
    ):
        raise ValueError("source identity mismatch")
    if (
        len(spec["workloads"]) != 1
        or spec["workloads"][0]["id"] != "repository-evaluation"
    ):
        raise ValueError("unsupported evaluation workload")
    if build["stage"] != spec["stage"]:
        raise ValueError("stage identity mismatch")
    if build.get("targetExpression") is not None:
        attributes = gc_compiler.target_attributes(build)
        if attributes != {
            target["id"]: target["attribute"] for target in spec["targets"]
        }:
            raise ValueError("expression target identity mismatch")
        gc_compiler.validate_expression_file(build, output / "source-expression.nix")
    if any(value["runId"] != output.name for value in (index, execution, results)):
        raise ValueError("run identity mismatch")
    if execution["runner"]["sha256"] != digest(Path(__file__)):
        raise ValueError("verification requires the recorded runner version")
    for name, module in support_modules(build).items():
        if execution["runner"]["supportModules"][name]["sha256"] != digest(
            Path(module.__file__)
        ):
            raise ValueError("verification support module identity mismatch")
    measured = execution["measuredInputs"]
    libraries = validate_libraries(build)
    consumer = (
        Path(build["consumer"]["output"]) / build["consumer"]["executable"]
    ).resolve(strict=True)
    if str(consumer) != measured["consumer"]["path"]:
        raise ValueError("consumer identity mismatch")
    for key, path in libraries.items():
        if str(path) != measured["libraries"][key]["path"]:
            raise ValueError("GC identity mismatch")
    for item in [
        measured["consumer"],
        *measured["binaries"].values(),
        *measured["libraries"].values(),
    ]:
        if digest(Path(item["path"])) != item["sha256"]:
            raise ValueError("measured executable/library hash mismatch")
    if digest(output / "corpus.json") != measured["corpus"]["sha256"]:
        raise ValueError("corpus artifact hash mismatch")
    if (
        validate_corpus(output / "corpus.json", consumer)
        != measured["corpus"]["identity"]
    ):
        raise ValueError("corpus identity mismatch")
    if "compilerComparison" in build:
        gc_compiler.validate_benchmark(build, measured["corpus"]["identity"])

    anchor = read("runtime-before.json")

    def runtime_pair(value):
        for snapshot in (value["before"], value["after"]):
            runtime.validate_control(
                snapshot,
                build["workingStock"]["normal"],
                spec["physicalTarget"],
                build["workingStock"]["runtime"],
            )
            runtime.validate_interval(anchor, snapshot)
        runtime.validate_interval(value["before"], value["after"])

    runtime_pair(
        {"before": read("runtime-before.json"), "after": read("runtime-after.json")}
    )
    observations = [
        json.loads(line)
        for line in (output / "observations.jsonl").read_text().splitlines()
    ]
    if observations != results["observations"]:
        raise ValueError("results/observations mismatch")
    workload = spec["workloads"][0]
    expected_arguments = [
        "flake",
        "check",
        "@source@",
        "--offline",
        "--no-build",
        "--no-write-lock-file",
        "--no-eval-cache",
    ]
    if (
        workload["arguments"] != expected_arguments
        or workload["executable"] != "bin/nix-evaluation"
    ):
        raise ValueError("evaluation command contract mismatch")
    if {metric["id"] for metric in workload["metrics"]} != {
        "wallTime",
        "cpuTime",
    } or any(
        metric["direction"] != "lower-is-better" for metric in workload["metrics"]
    ):
        raise ValueError("evaluation metric contract mismatch")
    cursor = 0
    previous_finished = None

    def observation(phase, pair, position, variant):
        nonlocal cursor, previous_finished
        if cursor >= len(observations):
            raise ValueError("missing complete observation")
        record = observations[cursor]
        cursor += 1
        if (
            record["workload"],
            record["phase"],
            record["pair"],
            record["position"],
            record["variant"],
        ) != (workload["id"], phase, pair, position, variant):
            raise ValueError("observation ordering mismatch")
        name = f"{workload['id']}-{phase}-{pair}-{position}-{variant}"
        receipt = read("raw/" + name + ".receipt.json")
        expected_argv = [
            "taskset",
            "-c",
            str(workload["cpu"]),
            measured["binaries"][variant]["path"],
            *[
                measured["corpus"]["identity"]["source"]["path"]
                if item == "@source@"
                else item
                for item in expected_arguments
            ],
        ]
        if record["argv"] != expected_argv or receipt["argv"] != expected_argv:
            raise ValueError("observed command identity mismatch")
        if receipt["returncode"] != 0 or "error" in receipt:
            raise ValueError("failed command entered accepted results")
        state = Path(receipt["stateDirectory"])
        environment = receipt["environment"]
        expected_environment = {
            "PATH": environment["PATH"],
            "LC_ALL": "C",
            "TZ": "UTC",
            "HOME": str(state / "home"),
            "XDG_CACHE_HOME": str(state / "cache"),
            "XDG_CONFIG_HOME": str(state / "config"),
            "XDG_STATE_HOME": str(state / "state"),
            "NIX_USER_CONF_FILES": "/dev/null",
            "NIX_CONF_DIR": str(state / "config"),
            "NIX_CONFIG": "experimental-features = nix-command flakes\naccept-flake-config = false\n",
        }
        if (
            state.name != name
            or state.parent.name != "state"
            or state.parent.parent.name != execution["runId"]
            or environment != expected_environment
        ):
            raise ValueError("observation environment identity mismatch")
        binding = receipt["binding"]
        if binding["executable"] != str(consumer) or binding["gcMappings"] != [
            str(libraries[variant])
        ]:
            raise ValueError("observed process binding mismatch")
        metrics = {
            "wallTime": receipt["monotonicEnd"] - receipt["monotonicStart"],
            "cpuTime": sum(receipt["childUsageAfter"].values())
            - sum(receipt["childUsageBefore"].values()),
        }
        if (
            metrics != record["metrics"]
            or metrics != receipt["metrics"]
            or any(not math.isfinite(value) or value <= 0 for value in metrics.values())
        ):
            raise ValueError("raw timing reconstruction mismatch")
        if metrics["wallTime"] < workload["minimumSeconds"]:
            raise ValueError("short observation")
        if previous_finished is not None and record["startedAt"] < previous_finished:
            raise ValueError("overlapping observations")
        previous_finished = record["finishedAt"]
        if not (
            record["startedAt"]
            <= receipt["startedAt"]
            <= binding["observedAt"]
            <= receipt["finishedAt"]
            <= record["finishedAt"]
        ):
            raise ValueError("observation timestamp order mismatch")
        runtime_pair(read("raw/" + name + "-runtime.json"))
        return metrics

    for pair in range(workload["warmupRuns"]):
        for position, variant in enumerate(("stock", "candidate")):
            observation("warmup", pair, position, variant)

    def pairs(phase, count, seed):
        values = {metric["id"]: [] for metric in workload["metrics"]}
        for pair, order in enumerate(balanced_order(count, seed)):
            one = {}
            for position, variant in enumerate(order):
                variant = "stock" if variant == "control" else variant
                one[variant] = observation(phase, pair, position, variant)
            for metric in values:
                values[metric].append((one["stock"][metric], one["candidate"][metric]))
        return values

    sampling = workload["sampling"]
    pilot = pairs("pilot", sampling["pilotPairs"], sampling["orderSeed"])
    plans = {
        metric["id"]: sample_plan(
            pilot[metric["id"]],
            metric["direction"],
            sampling["targetDeltaHalfWidth"],
            sampling["minimumPairs"],
            sampling["maximumPairs"],
        )
        for metric in workload["metrics"]
    }
    count = max(plan["measurementPairs"] for plan in plans.values())
    measured_pairs = pairs("measurement", count, sampling["orderSeed"] + 1)
    reconstructed = {
        workload["id"]: {
            "samplingDecision": plans,
            "pilotPairs": sampling["pilotPairs"],
            "measurementPairs": count,
            "metrics": {
                metric["id"]: summarize(
                    measured_pairs[metric["id"]],
                    metric["direction"],
                    sampling["effectThreshold"],
                    sampling["orderSeed"],
                )
                for metric in workload["metrics"]
            },
        }
    }
    if cursor != len(observations) or results["summaries"] != reconstructed:
        raise ValueError("measurement/statistics reconstruction mismatch")
    return reconstructed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    run_parser = subparsers.add_parser("run")
    for name in ("specification", "build", "output", "repository"):
        run_parser.add_argument(name, type=Path)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "run":
            run(args.specification, args.build, args.output, args.repository)
        else:
            print(json.dumps(verify(args.output), indent=2, sort_keys=True))
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Experiment refused or failed: {error}", file=sys.stderr)
        sys.exit(1)
