"""Prepare a source-bound diagnostic compile argv; executes no compiler/engine.

Canonical engine qualification is reused explicitly from pinned, closed S11
reference receipts. This planner does not rerun or independently authenticate
their complete historical Std chain. It verifies present source/binary identity.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

PAYLOAD = ("forge_sol_S14_picker_oracle_20261026.cpp", "forge_sol_S14_cpp_alloc_counter_20261026.hpp",
           "forge_sol_S14_expected_workload_20261026.hpp", "forge_sol_S14_workload20_20261026.tsv")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def file_record(path):
    p = Path(path).resolve()
    require(p.is_file() and p.stat().st_size <= (64 << 20), "bounded regular input file required: " + str(p))
    with p.open("rb") as stream:
        data = stream.read((64 << 20) + 1)
    require(len(data) <= (64 << 20), "input grew beyond byte bound: " + str(p))
    return {"path": str(p), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def verify_source(root, inventory):
    root = Path(root).resolve()
    require(root.is_dir(), "source directory required")
    found = set()
    for p in root.rglob("*"):
        require(not p.is_symlink(), "source symlink not allowed")
        if p.is_file():
            found.add(str(p.relative_to(root)))
            require(len(found) <= len(inventory), "source inventory has extra files")
    require(found == set(inventory), "source inventory differs")
    records = []
    for name, expected in inventory.items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "invalid source inventory path")
        row = file_record(root / relative)
        require(row["sha256"] == expected["sha256"] and row["bytes"] == expected["bytes"], "source bytes changed: " + name)
        records.append(row)
    return records


def build_plan(role, source, core, receipt, compiler, packet, expected, new_out):
    require(role in ("L", "Lprime", "B") and role in expected["bases"], "unknown source role")
    source, core, receipt, compiler, packet, new_out = (Path(x).resolve() for x in (source, core, receipt, compiler, packet, new_out))
    require(not new_out.exists(), "refuse existing build output")
    base = expected["bases"][role]
    owner = expected["bases"][base["core_owner"]]
    records = verify_source(source, base["source_inventory"])
    rr = file_record(receipt)
    require(rr["sha256"] == base["reference_receipt_sha256"], "reference receipt hash differs")
    data = json.loads(receipt.read_text())
    require(data.get("schema") == "forge.S11.baseline_release_reuse.v1" and
            data.get("status") == "PASS_ORACLE_ONLY_WITH_REUSED_STD", "closed S11 reuse receipt required")
    require(data.get("role") == "baseline" and data.get("base") == base["core_owner"], "canonical baseline receipt required")
    require(data.get("profile") == "Release" and data.get("evidence_class") == "REUSE_NOT_NEW_RUN", "explicit Release reuse required")
    require(all(data.get(k) == 0 for k in ("new_main_ELFs", "new_FIRST_runs", "new_full_Std_runs")) and
            data.get("new_JUnit") is False, "do not relabel reused qualification as new")
    owner_hashes = {k: v["sha256"] for k, v in owner["source_inventory"].items()}
    require(data["source_before"] == data["source_after"] == owner_hashes, "reference source identity differs")
    if role != base["core_owner"]:
        compiled = lambda inv: {k: v for k, v in inv.items() if k.startswith(("src/", "include/"))}
        require(role == "L" and base["core_owner"] == "Lprime" and
                compiled(base["source_inventory"]) == compiled(owner["source_inventory"]),
                "unproved production-source core alias")
    cr, cc = file_record(core), file_record(compiler)
    require(cr["sha256"] == base["core_sha256"] == data["evidence"]["core_archive"]["sha256"] and
            cr["bytes"] == data["evidence"]["core_archive"]["bytes"], "canonical core differs")
    require(cc["sha256"] == expected["compiler_sha256"] == data["compiler_sha256"], "compiler differs")
    main = Path(data["evidence"]["canonical_build"]) / "forge"
    mr = file_record(main)
    require(mr["sha256"] == base["main_sha256"] == data["evidence"]["main_sha256"], "qualified main differs")
    qualification_inputs = []
    tests = file_record(main.parent / "forge_tests")
    require(tests["sha256"] == data["evidence"]["tests_ELF_sha256"], "qualified tests ELF differs")
    qualification_inputs.append(tests)
    for wanted in data["evidence"]["artifacts"]:
        row = file_record(wanted["path"])
        require(row["sha256"] == wanted["sha256"], "qualified support artifact differs")
        qualification_inputs.append(row)
    require(data["evidence"]["canonical_flags"], "qualified flag records required")
    for wanted in data["evidence"]["canonical_flags"]:
        row = file_record(wanted["path"])
        require(row["sha256"] == wanted["sha256"], "qualified flags changed")
        qualification_inputs.append(row)
    original = file_record(data["evidence"]["original_receipt"])
    require(original["sha256"] == data["evidence"]["original_receipt_sha256"], "original qualification receipt changed")
    qualification_inputs.append(original)
    require(set(expected["packet_pins"]) == set(PAYLOAD), "required packet pin set differs")
    payload = []
    for name in PAYLOAD:
        row = file_record(packet / name)
        require(row["sha256"] == expected["packet_pins"][name], "diagnostic packet input changed: " + name)
        payload.append(row)
    for immutable_root in (source, packet, core.parent, main.parent):
        require(not new_out.is_relative_to(immutable_root), "build output must be outside frozen inputs")
    require("," not in str(new_out) and "\n" not in str(new_out), "map path cannot contain comma or newline")
    executable = new_out / "forge_sol_S14_picker_probe_20261026"
    link_map = new_out / "forge_sol_S14_picker_probe_20261026.map"
    source_sha = base["source_inventory"]["src/search.cpp"]["sha256"]
    argv = [str(compiler), "-std=c++20", "-O3", "-DNDEBUG", "-march=x86-64-v3", "-mtune=znver5",
            "-fno-fast-math", "-ffp-contract=off", "-DFORGE_NNUE_HIDDEN=256",
            '-DFORGE_PICKER_SOURCE="' + str(source / "src/search.cpp") + '"',
            '-DFORGE_S14_ROLE="' + role + '"', '-DFORGE_S14_SOURCE_SHA256="' + source_sha + '"',
            '-DFORGE_S14_CORE_SHA256="' + cr["sha256"] + '"',
            '-DFORGE_S14_WORKLOAD_SHA256="' + expected["workload_tsv_sha256"] + '"',
            "-I" + str(source / "include"), "-I" + str(packet), str(packet / PAYLOAD[0]),
            str(core), "-pthread", "-Wl,-Map," + str(link_map), "-o", str(executable)]
    records.extend([rr, cr, cc, mr] + qualification_inputs + payload)
    return {"schema": "forge.S14.build_plan.v1", "status": "READY_BUILD_PLAN_ONLY", "compiler_runs": 0,
            "engine_runs": 0, "source_role": role, "reference_core_owner": base["core_owner"],
            "source_root": str(source), "source_sha256": source_sha, "core": str(core),
            "core_sha256": cr["sha256"], "reference_receipt_sha256": rr["sha256"],
            "qualification": "REUSE_NOT_NEW_RUN; no S14 engine change or new Std",
            "L_full_Std": "NOT_CLAIMED" if role == "L" else "OWNER_ORIGINAL_QUALIFICATION_REUSED",
            "argv": argv, "executable": str(executable), "link_map": str(link_map), "inputs": records,
            "runtime_templates": [[str(executable), str(packet / PAYLOAD[3])],
                                  [str(executable), str(packet / PAYLOAD[3]), "--negative-counter-disabled"],
                                  [str(executable), str(packet / PAYLOAD[3]), "--negative-inject-allocation"]],
            "native_execution": "UNVERIFIED; root grant/supervisor/source-after checks required"}


def verify_inputs(plan):
    for wanted in plan["inputs"]:
        require(file_record(wanted["path"]) == wanted, "bound input changed: " + wanted["path"])
    return {"status": "PASS_INPUT_BYTES_ONLY"}


def verify_argv(actual, plan):
    require(isinstance(actual, list) and actual == plan["argv"], "compile argv differs from exact strict plan")
    return {"status": "PASS_ARGV_ONLY"}


def verify_link_map(text, core):
    core = str(Path(core).resolve())
    require(re.search(r"\((?:[^()\n]*/)?search\.cpp\.o\)", text) is None,
            "archive search.cpp.o duplicates included actual search source")
    require(re.search(r"^LOAD\s+" + re.escape(core) + r"\s*$", text, re.MULTILINE) is not None,
            "link map missing intended core LOAD")
    return {"status": "PASS_CORE_LINK_MAP", "scope": "map structure only; not compiler authentication"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", choices=("L", "Lprime", "B"), required=True)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--core", type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--compiler", type=Path)
    ap.add_argument("--new-out", type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    try:
        expected = json.loads((root / "forge_sol_S14_source_bindings_20261026.json").read_text())
        base = expected["bases"][args.base]
        plan = build_plan(args.base, args.source or base["source_root"], args.core or base["core_path"],
                          args.receipt or root / base["reference_receipt"], args.compiler or expected["compiler_path"],
                          root, expected, args.new_out)
        args.new_out.mkdir(parents=True, exist_ok=False)
        with (args.new_out / "forge_sol_S14_build_plan_20261026.json").open("x") as f:
            json.dump(plan, f, indent=2); f.write("\n")
        print("Build plan saved; no compiler or engine was executed")
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        ap.exit(1, "S14 build plan: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
