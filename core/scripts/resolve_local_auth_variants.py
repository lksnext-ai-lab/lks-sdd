"""Record resolved locked scaffold inventories; never install dependencies."""
import json
import tempfile
from pathlib import Path

from profile_registry import load_catalog, load_profile_bundle
from run_reference_profile_gate import _materialize
from technology_resolution import inspect_dependencies
from update_profile_locks import build_lock

ROOT = Path(__file__).resolve().parents[1]


def main():
    for entry in load_catalog()[0]["profiles"]:
        bundle = load_profile_bundle(entry["id"])
        if not bundle.driver.get("variant"):
            continue
        if bundle.profile.get("lifecycle") != "candidate":
            raise ValueError("Active variants require an explicit new certification cycle")
        with tempfile.TemporaryDirectory(prefix="lks-resolution-") as temp:
            work = Path(temp)
            _materialize(entry["id"], work)
            inventory = inspect_dependencies(work)
            if inventory["errors"]:
                raise ValueError("; ".join(inventory["errors"]))
            config = json.loads((work / "profile-runtime.json").read_text())
            resolution = {"schema_version": "1.0", "profile_id": entry["id"], "status": "resolved-not-certified",
                          "packages": inventory["resolved"], "tools": inventory["tools_declared"],
                          "runtimes": inventory["runtime_declared"], "images": config["images"],
                          "lock_input_hashes": inventory["input_hashes"], "runtime_verified": {}}
            (bundle.root / "resolved-technology.json").write_text(json.dumps(resolution, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    for entry in load_catalog()[0]["profiles"]:
        bundle = load_profile_bundle(entry["id"])
        if bundle.driver.get("variant"):
            (bundle.root / "technology-profile.lock.json").write_text(json.dumps(build_lock(entry["id"]), indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__": main()
