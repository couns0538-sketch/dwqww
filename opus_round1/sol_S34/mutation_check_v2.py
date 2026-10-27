"""Planted-bug check for the S34 v2 validator: every mutant must make the test suite fail.

usage: python -I -B mutation_check_v2.py <new scratch dir>
Copies the validator, the tests and the fixtures into <scratch>/<mutant>/ (the scratch dir must not exist),
applies one source mutation to the validator copy, runs the tests there and expects a failure. The unmutated
copy must pass. The real files in this folder are never modified.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TOOL = "forge_sol_S34_validate_manifest_v2.py"
TESTS = "test_validate_manifest_v2.py"
MUTANTS = {
    "no_case_duplicate_keys": ("            if key.casefold() in folded:", "            if False:"),
    "default_concurrency_0": ('DRIVER_DEFAULTS = {"tc": "10+0.1", "concurrency": 5,', 'DRIVER_DEFAULTS = {"tc": "10+0.1", "concurrency": 0,'),
    "ownbook_not_reserved": ('DRIVER_SET_OPTIONS = frozenset({"threads", "hash", "ownbook"})', 'DRIVER_SET_OPTIONS = frozenset({"threads", "hash"})'),
    "ag_prev_fields_open": ("        _unknown_fields(prev, AG_PREV_FIELDS, pp, findings)\n", ""),
    "base_options_not_reported": ("    elif options:\n        findings.append(finding(\"BASE_OPTIONS_IGNORED\"", "    elif False:\n        findings.append(finding(\"BASE_OPTIONS_IGNORED\""),
    "control_chars_allowed": ("        if CONTROL.search(entry):", "        if False:"),
    "strict_uses_defaults": ("    defaults = not strict", "    defaults = True"),
    "bool_annotations_untyped": ("        if type(gate[field]) is not bool:", "        if False:"),
    "option_prefix_match_only": ("        match = OPTION.fullmatch(entry)", "        match = OPTION.match(entry.strip())"),
    "duplicate_options_case_sensitive": ("        elif name.casefold() in seen:", "        elif name in seen:"),
}


def run(directory):
    env = dict(os.environ, S34_FIXTURES=str(directory / "bad_manifests_v2"))
    result = subprocess.run([sys.executable, "-I", "-B", str(directory / TESTS)], cwd=directory, env=env,
                            capture_output=True, text=True, check=False)
    last = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()][-1:]
    return result.returncode, last[0] if last else ""


def main(argv):
    scratch = Path(argv[0])
    scratch.mkdir()
    failures = 0
    for name in ["unmutated", *MUTANTS]:
        directory = scratch / name
        directory.mkdir()
        shutil.copy2(HERE / TOOL, directory / TOOL)
        shutil.copy2(HERE / TESTS, directory / TESTS)
        shutil.copytree(HERE / "bad_manifests_v2", directory / "bad_manifests_v2")
        if name != "unmutated":
            old, new = MUTANTS[name]
            source = (directory / TOOL).read_text(encoding="utf-8")
            if source.count(old) != 1:
                print(f"{name}: mutation anchor not found exactly once")
                failures += 1
                continue
            (directory / TOOL).write_text(source.replace(old, new), encoding="utf-8", newline="\n")
        code, last = run(directory)
        expected_fail = name != "unmutated"
        ok = (code != 0) if expected_fail else (code == 0)
        failures += not ok
        print(f"{name:34s} tests rc {code} ({last}) -> {'CAUGHT' if expected_fail and ok else 'PASS' if ok else 'NOT CAUGHT' if expected_fail else 'FAIL'}")
    print("MUTATION CHECK:", "PASS" if not failures else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
