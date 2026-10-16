"""Verify raw training identities and produce an immutable merged artifact."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = Path(os.environ["trainingDirectory"])
output = Path(os.environ["out"])
tool = os.environ["profileTool"]
receipt = json.loads((source / "receipt.json").read_text())
if receipt["variant"] != os.environ["variant"]:
    raise ValueError("training variant mismatch")
if receipt["acceptance"] != "TRAINING_ONLY_NOT_BENCHMARK":
    raise ValueError("unexpected training evidence class")
profiles = sorted((source / "raw").glob("*.profraw"))
actual = {path.name: sha256(path) for path in profiles}
if not actual or actual != receipt["rawProfiles"]:
    raise ValueError("raw profile identity mismatch")
output.mkdir()
shutil.copytree(source / "raw", output / "raw")
shutil.copyfile(source / "receipt.json", output / "training.json")
merged = output / "merged.profdata"
command = [tool, "merge", "--failure-mode=any", "--output", str(merged)]
command += [str(output / "raw" / path.name) for path in profiles]
subprocess.run(command, check=True)
summary = subprocess.run(
    [tool, "show", "--all-functions", "--counts", str(merged)],
    check=True,
    capture_output=True,
    text=True,
).stdout
marking = re.search(r"GC_mark_some:\s+Hash:.*?Function count: (\d+)", summary, re.S)
if marking is None or int(marking.group(1)) == 0:
    raise ValueError("profile does not cover the identified GC marking code")
(output / "profile-summary.txt").write_text(summary)
version = subprocess.run(
    [tool, "--version"], check=True, capture_output=True, text=True
).stdout
manifest = {
    "schemaVersion": 1,
    "kind": "boehmgc-pgo-merged-profile",
    "acceptance": "TRAINING_ONLY_NOT_BENCHMARK",
    "training": receipt,
    "trainingReceiptSha256": sha256(output / "training.json"),
    "rawProfiles": actual,
    "mergeTool": tool,
    "mergeToolVersion": version,
    "mergeCommand": command,
    "mergedProfileSha256": sha256(merged),
    "summarySha256": sha256(output / "profile-summary.txt"),
}
(output / "profile.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
