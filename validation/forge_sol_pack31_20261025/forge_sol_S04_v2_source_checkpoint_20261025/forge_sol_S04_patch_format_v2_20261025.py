#!/usr/bin/env python3
"""Reformat the existing S04 fix; preserve executable-source bytes on each base."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "forge_sol_S04_patchwork_v2_20261025"
PACK = Path("/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files")
BASES = {
    "L": PACK / "01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src",
    "Lp": PACK / "01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src",
    "B": PACK / "01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src",
}
OLD = Path("/workspace/dwqww/releases/forge_sol_pack31_20261025/S04/forge_sol_S04_attacksinit_fix_20261025.patch")
EXPECTED_OLD = "29ee0866e90185a6a50f8389d8792399b890338c4e10f6457459652bbb6c15e7"
EXISTING = ("CMakeLists.txt", "IDEA_SOURCE.md", "src/bitboard.cpp")
NEW = "tests/forge_sol_S04_tsan_test_20261025.cpp"
TARGETS = (*EXISTING, NEW)
CPP_CMAKE = ("CMakeLists.txt", "src/bitboard.cpp", NEW)
RECEIPT = OUT / "forge_sol_S04_patch_format_receipt_v2_20261025.json"
PATCH = OUT / "forge_sol_S04_v2_20261025.patch"
STATE: dict = {"schema": 1, "task": "S04-1", "status": "RUNNING", "native_execution": False, "commands": []}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sealed(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": digest(data), "base64": base64.b64encode(data).decode("ascii")}


def save() -> None:
    RECEIPT.write_text(json.dumps(STATE, indent=2) + "\n")


def run(label: str, argv: list[str], cwd: Path, data: bytes | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, input=data, capture_output=True, check=False)
    STATE["commands"].append({"label": label, "argv": argv, "cwd": str(cwd),
                              "stdin": sealed(data or b""), "stdout": sealed(result.stdout),
                              "stderr": sealed(result.stderr), "exit": result.returncode,
                              "stdout_eof": True, "stderr_eof": True, "child_closed": True})
    save()  # Preserve real streams before any assertion.
    return result


def require(result: subprocess.CompletedProcess, label: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(label + " failed; original command streams already preserved")


def copy_minimal(base: Path, name: str) -> Path:
    dest = OUT / name
    dest.mkdir()
    for relative in EXISTING:
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((base / relative).read_bytes())
    (dest / "tests").mkdir()
    return dest


def inventory(path: Path, names: tuple[str, ...] = TARGETS) -> dict:
    return {name: {"bytes": (path / name).stat().st_size, "sha256": digest((path / name).read_bytes())}
            for name in names if (path / name).is_file()}


def apply_patch(label: str, tree: Path, patch: Path) -> None:
    raw = patch.read_bytes()
    for suffix, args in (("dry", ["--dry-run"]), ("apply", [])):
        result = run(label + "_" + suffix,
                     ["patch", "-p1", "-F0", "--batch", "--no-backup-if-mismatch", *args], tree, raw)
        require(result, label + " " + suffix)
        if re.search(rb"\bfuzz\b|FAILED|malformed", result.stdout + result.stderr):
            raise RuntimeError(label + " unexpected patch diagnostic")


def operations(raw: bytes) -> dict[str, list[bytes]]:
    current = None
    result: dict[str, list[bytes]] = {}
    for line in raw.splitlines():
        if line.startswith(b"diff --git a/"):
            current = line.split(b" b/", 1)[1].decode()
            result[current] = []
        elif current and line[:1] in (b"+", b"-") and not line.startswith((b"+++", b"---")):
            result[current].append(line)
    return result


def main() -> None:
    if OUT.exists():
        raise SystemExit("error: output already exists: " + str(OUT))
    OUT.mkdir()
    save()
    try:
        original = OLD.read_bytes()
        assert digest(original) == EXPECTED_OLD
        STATE["original_patch"] = {"path": str(OLD), **sealed(original)}
        STATE["source_before"] = {name: {"path": str(base), "files": inventory(base, EXISTING)}
                                  for name, base in BASES.items()}
        save()
        applied: dict[str, Path] = {}
        STATE["old_controls"] = {}
        for name, base in BASES.items():
            tree = copy_minimal(base, "forge_sol_S04_old_" + name + "_v2_20261025")
            result = run("old_" + name + "_git_check", ["git", "apply", "--check", str(OLD)], tree)
            STATE["old_controls"][name] = {"git_check_exit": result.returncode}
            save()
            apply_patch("old_" + name, tree, OLD)
            applied[name] = tree
        # Reuse the exact old idea paragraph, but put it at a safe common interior
        # anchor. Historical document notes remain unchanged on each base.
        old_doc = (applied["L"] / "IDEA_SOURCE.md").read_bytes()
        source_doc = (BASES["L"] / "IDEA_SOURCE.md").read_bytes()
        start = old_doc.index(b"\n## S04 optional thread-safe")
        block = old_doc[start:]
        assert old_doc[:start] == source_doc
        assert all((applied[name] / "IDEA_SOURCE.md").read_bytes().replace(block, b"", 1)
                   == (base / "IDEA_SOURCE.md").read_bytes() for name, base in BASES.items())
        work = copy_minimal(BASES["L"], "forge_sol_S04_git_diff_v2_20261025")
        require(run("private_git_init", ["git", "init", "--quiet"], work), "git init")
        require(run("private_git_config", ["git", "config", "core.autocrlf", "false"], work), "git config")
        require(run("private_git_add_base", ["git", "add", "--", *EXISTING], work), "git add baseline")
        for relative in CPP_CMAKE:
            (work / relative).write_bytes((applied["L"] / relative).read_bytes())
        title, remainder = source_doc.split(b"\n", 1)
        (work / "IDEA_SOURCE.md").write_bytes(title + b"\n" + block + b"\n" + remainder)
        require(run("private_git_intent_new", ["git", "add", "-N", "--", NEW], work), "git add new")
        result = run("private_git_diff", ["git", "diff", "--no-ext-diff", "--full-index", "-U5", "--", *TARGETS], work)
        require(result, "git diff")
        patch = result.stdout
        PATCH.write_bytes(patch)
        assert bytes.fromhex("4f70656e4149") not in patch
        assert b"new file mode 100644\n" in patch
        assert b"--- /dev/null\n" in patch and ("+++ b/" + NEW).encode() in patch
        old_ops, new_ops = operations(original), operations(patch)
        assert set(new_ops) == set(TARGETS) == set(old_ops)
        assert all(old_ops[name] == new_ops[name] for name in CPP_CMAKE)
        assert old_ops["IDEA_SOURCE.md"] == new_ops["IDEA_SOURCE.md"]
        assert b'option(FORGE_ATTACKS_INIT_ONCE "Synchronize the first attack-table initialization" OFF)' in patch
        STATE["new_patch"] = {"path": str(PATCH), "bytes": len(patch), "sha256": digest(patch)}
        STATE["format_controls"] = {
            "old_has_new_file_mode": b"new file mode 100644\n" in original,
            "new_has_new_file_mode": True,
            "non_idea_operations_identical": True,
            "idea_added_lines_identical": True,
            "idea_placement": "same paragraph after common title; old surrounding notes untouched",
            "option_default": "OFF",
        }
        save()
        STATE["new_controls"] = {}
        for name, base in BASES.items():
            tree = copy_minimal(base, "forge_sol_S04_new_" + name + "_v2_20261025")
            require(run("new_" + name + "_git_check", ["git", "apply", "--check", str(PATCH)], tree), "new git check")
            apply_patch("new_" + name, tree, PATCH)
            exact = {relative: (tree / relative).read_bytes() == (applied[name] / relative).read_bytes()
                     for relative in CPP_CMAKE}
            assert all(exact.values())
            after_doc = (tree / "IDEA_SOURCE.md").read_bytes()
            # Account for exactly the two separators around the relocated block.
            assert after_doc.replace(block + b"\n", b"", 1) == (base / "IDEA_SOURCE.md").read_bytes()
            STATE["new_controls"][name] = {"git_check_exit": 0, "gnu_f0_dry_apply_exit": 0,
                                           "files": inventory(tree), "cpp_cmake_identical_to_old": exact,
                                           "remove_only_new_idea_block_restores_original": True}
            save()
        STATE["source_after"] = {name: {"path": str(base), "files": inventory(base, EXISTING)}
                                 for name, base in BASES.items()}
        assert STATE["source_before"] == STATE["source_after"]
        STATE["status"] = "PASS_FORMAT_AND_SOURCE_EQUIVALENCE_ONLY"
        STATE["native_validation"] = "PENDING_ROOT_LEASE; historical cold/TSan evidence not repeated"
        save()
        print(json.dumps({"status": STATE["status"], "patch": STATE["new_patch"],
                          "old_git_exits": {k: v["git_check_exit"] for k, v in STATE["old_controls"].items()}}))
    except BaseException as error:
        STATE["status"] = "FAILED_PRODUCER_ATTEMPT"
        STATE["exception"] = repr(error)
        save()
        raise


if __name__ == "__main__":
    main()
