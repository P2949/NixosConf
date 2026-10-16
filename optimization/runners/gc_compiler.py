"""Verify prepared GC compiler comparisons; this does not admit timed runs."""

import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess


CPU = ["-march=skylake", "-mtune=skylake"]
LINK = ["--save-temps", "--threads=1", "--thinlto-jobs=1"]
PAIRS = {
    "clang-cpu": ([], CPU),
    "thinlto": ([], ["-flto=thin"]),
    "cpu-thinlto": (CPU, CPU + ["-flto=thin"]),
    "toolchain-bridge": ([], []),
    "pgo": ([], None),
    "cpu-pgo": (CPU, None),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def store_path(value):
    require(
        isinstance(value, str)
        and re.fullmatch(r"/nix/store/[0-9a-z]{32}-[^/]+", value) is not None,
        "invalid store identity",
    )
    return Path(value)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_profile(profile, stock, consumer, comparison):
    require(isinstance(profile, dict), "PGO profile required")
    require(
        set(profile)
        == {
            "profilePath",
            "profileNarHash",
            "variant",
            "mergedProfileSha256",
            "metadataSha256",
        },
        "unexpected profile fields",
    )
    directory = store_path(profile["profilePath"])
    expected_variant = "generic" if comparison == "pgo" else "skylake"
    require(profile["variant"] == expected_variant, "PGO CPU variant mismatch")
    actual_nar = subprocess.check_output(
        ["nix", "hash", "path", str(directory)], text=True
    ).strip()
    require(actual_nar == profile["profileNarHash"], "profile NAR mismatch")
    require(
        digest(directory / "profile.json") == profile["metadataSha256"],
        "profile metadata hash mismatch",
    )
    require(
        digest(directory / "merged.profdata") == profile["mergedProfileSha256"],
        "merged profile hash mismatch",
    )
    metadata = json.loads((directory / "profile.json").read_text())
    require(metadata["kind"] == "boehmgc-pgo-merged-profile", "unexpected profile kind")
    require(
        metadata["mergedProfileSha256"] == profile["mergedProfileSha256"],
        "profile receipt mismatch",
    )
    training = metadata["training"]
    require(training["variant"] == expected_variant, "training CPU variant mismatch")
    require(
        training["acceptance"] == "TRAINING_ONLY_NOT_BENCHMARK",
        "unexpected training evidence class",
    )
    require(
        training["consumer"] == consumer["output"]
        and training["consumerDerivation"] == consumer["derivation"],
        "training consumer mismatch",
    )
    require(
        training["artifact"]["source"] == stock["source"]["output"]
        and training["artifact"]["sourceHash"] == stock["source"]["narHash"],
        "training package source mismatch",
    )
    for tool in ("compiler", "linker"):
        require(
            training[tool] == stock["toolchain"][tool]["output"]
            and training[tool + "Derivation"] == stock["toolchain"][tool]["derivation"],
            "training toolchain mismatch",
        )
    require(
        shlex.split(training["artifact"]["compileFlags"])
        == shlex.split(stock["compileFlags"])
        + ["-fprofile-instr-generate", "-fprofile-update=atomic"],
        "training instrumentation flags mismatch",
    )
    return [
        f"-fprofile-instr-use={directory}/merged.profdata",
        "-Werror=profile-instr-out-of-date",
    ]


def validate_preparation(manifest):
    require(
        manifest.get("schemaVersion") == 1
        and manifest.get("kind") == "nixos-gc-compiler-comparison",
        "unsupported compiler comparison",
    )
    require(
        manifest.get("acceptance") == "PREPARATION_ONLY_NOT_PERFORMANCE",
        "unexpected comparison evidence class",
    )
    comparison = manifest["comparison"]
    require(comparison in PAIRS, "unsupported compiler comparison pair")
    require(manifest["packageAllowList"] == ["boehm-gc"], "package allow-list mismatch")
    require(
        manifest["collectorPolicy"]
        == {"enableLargeConfig": True, "initialMarkStackSize": 1048576},
        "collector policy mismatch",
    )
    require(
        set(manifest["libraries"]) == {"stock", "candidate"},
        "exactly two libraries required",
    )
    stock, candidate = (manifest["libraries"][key] for key in ("stock", "candidate"))
    for key in ("source", "version", "configureFlags", "makeFlags"):
        require(stock[key] == candidate[key], "package source/policy changed")
    require(
        "--enable-large-config" in stock["configureFlags"]
        and "CFLAGS_EXTRA=-DINITIAL_MARK_STACK_SIZE=1048576" in stock["makeFlags"],
        "collector build flags missing",
    )
    require(stock["output"] != candidate["output"], "comparison outputs are identical")
    if comparison != "toolchain-bridge":
        require(
            stock["toolchain"] == candidate["toolchain"],
            "toolchain changed alongside compiler stage",
        )
    expected_stock, expected_candidate = PAIRS[comparison]
    require(
        shlex.split(stock["compileFlags"]) == expected_stock,
        "unexpected control compile flags",
    )
    if expected_candidate is None:
        expected_candidate = expected_stock + validate_profile(
            manifest["profile"], stock, manifest["consumer"], comparison
        )
    else:
        require(manifest["profile"] is None, "profile supplied to non-PGO comparison")
    require(
        shlex.split(candidate["compileFlags"]) == expected_candidate,
        "unexpected candidate compile flags",
    )
    for key, library in manifest["libraries"].items():
        store_path(library["output"])
        require(
            store_path(library["derivation"]).name.endswith(".drv"),
            "invalid library derivation",
        )
        expected_link = (
            [] if comparison == "toolchain-bridge" and key == "stock" else LINK
        )
        require(
            shlex.split(library["linkFlags"]) == expected_link,
            "unexpected linker flags",
        )
        if library["audit"] is not None:
            audit = store_path(library["audit"])
            require(
                (audit / "linker-version.txt").read_text().startswith("LLD "),
                "actual LLD evidence missing",
            )
            object_format = (audit / "object-format.txt").read_text()
            thin = "-flto=thin" in shlex.split(library["compileFlags"])
            require(
                ("LLVM IR bitcode" if thin else "ELF 64-bit") in object_format,
                "actual object format mismatch",
            )
            if thin:
                require(
                    "GLOBALVAL_SUMMARY_BLOCK" in (audit / "bitcode.txt").read_text(),
                    "ThinLTO summary missing",
                )
                require(
                    bool((audit / "thin-link-indexes.txt").read_text().strip()),
                    "ThinLink indexes missing",
                )
    return {"comparison": comparison, "acceptance": manifest["acceptance"]}


def validate_measurement(build):
    """Bind prepared facts to the measurement manifest, never to an adoption verdict."""
    prepared = build["compilerComparison"]
    validate_preparation(prepared)
    profile_hash = (
        None if prepared["profile"] is None else prepared["profile"]["profileNarHash"]
    )
    require(
        build["stage"]
        == {
            "kind": "gc-compiler-comparison",
            "parameters": {
                "comparison": prepared["comparison"],
                "packageAllowList": ["boehm-gc"],
                "profileNarHash": profile_hash,
            },
        },
        "compiler comparison stage mismatch",
    )
    require(
        build["libraries"] == prepared["libraries"],
        "comparison library binding mismatch",
    )
    require(
        build["collectorPolicy"] == prepared["collectorPolicy"],
        "comparison collector binding mismatch",
    )
    for field in ("revision", "narHash", "lockSha256"):
        require(
            build["source"][field] == prepared["source"][field],
            "comparison source binding mismatch",
        )
    for field in ("output", "derivation"):
        require(
            build["consumer"][field] == prepared["consumer"][field],
            "comparison consumer binding mismatch",
        )
    require(
        build["toolchains"]
        == {key: value["toolchain"] for key, value in prepared["libraries"].items()},
        "comparison toolchain binding mismatch",
    )
    for key, library in prepared["libraries"].items():
        for field in ("output", "derivation"):
            require(
                build["packages"][key][field] == library["command"][field],
                "comparison command binding mismatch",
            )
    return {
        key: (store_path(value["output"]) / "lib/libgc.so.1").resolve(strict=True)
        for key, value in prepared["libraries"].items()
    }


def validate_benchmark(build, corpus):
    profile = build["compilerComparison"]["profile"]
    if profile is not None:
        training = json.loads(
            (store_path(profile["profilePath"]) / "profile.json").read_text()
        )["training"]
        require(
            training["trainingCorpus"]["source"]["rev"] != corpus["source"]["rev"],
            "training corpus reused as benchmark",
        )
