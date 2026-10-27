#!/usr/bin/env python3
"""Planted-bug check for the S43 v5 net-batch: an unmutated control must pass, every mutant must make the suite FAIL.
usage: python -I -B mutation_check_s43.py SCRATCH_DIR"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S43_netbatch_v5_20261027.py"
TEST = HERE / "test_forge_sol_S43_netbatch_v5_20261027.py"
MUTANTS = {
    "M1_relative_junit_path": [('"--output-junit", str(junit)]', '"--output-junit", junit.name]')],
    "M2_subprocess_cwd_ignored": [("p = subprocess.run(argv, cwd=str(cwd), env=self.env,", "p = subprocess.run(argv, cwd=None, env=self.env,")],
    "M3_bench_compare_only_d11": [('row["bench_status"] = "PASS" if all(v == "MATCH" for v in row["bench_cmp"].values()) else "PIN_MISMATCH"',
                                   'row["bench_status"] = "PASS" if row["bench_cmp"]["11"] == "MATCH" else "PIN_MISMATCH"')],
    "M4_net_not_swapped_in": [('    shutil.copyfile(net, tree / "src" / "nnue_weights.inc")\n', '    pass\n'),
                              ('    if sha256(tree / "src" / "nnue_weights.inc") != net_sha:\n', '    if False:\n')],
    "M5_out_inside_input_allowed": [('            if str(a.out).lower().startswith(', '            if False and str(a.out).lower().startswith(')],
    "M6_base_not_resolved": [("a.base = absolute(a.base);", "a.base = Path(a.base);")],
    "M7_fma_regex_broken": [('FMA_RE = re.compile(r"\\bvfn?m(?:add|sub)")', 'FMA_RE = re.compile(r"\\bvfmsub")')],
    "M8_allowlist_max_count_ignored": [("    over = [p for p, c in counts.items()", "    over = [] and [p for p, c in counts.items()")],
    "M9_ctest_exit8_not_accepted": [("timeout=a.ctest_timeout * 4, accept=(0, 8))", "timeout=a.ctest_timeout * 4, accept=(0,))")],
}


def suite(tool, tmp):
    env = dict(os.environ, FORGE_S43_TOOL=str(tool), FORGE_S43_TMP=str(tmp))
    p = subprocess.run([sys.executable, "-I", "-B", str(TEST)], env=env, capture_output=True, text=True)
    return p.returncode, [l.split(" (")[0] for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]


def main():
    scratch = Path(sys.argv[1]); scratch.mkdir(parents=True, exist_ok=True)
    src = TOOL.read_text(encoding="utf-8"); results = {}
    c = scratch / "M00_control"; c.mkdir(exist_ok=True); ctl = c / TOOL.name
    if not ctl.exists():
        ctl.write_text(src, encoding="utf-8", newline="\n")
    rc, failed = suite(ctl, c)
    print(f"M00_control: {'PASS' if rc == 0 else 'FAIL ' + str(failed)}", flush=True)
    if rc:
        return 2
    for name, edits in MUTANTS.items():
        text = src
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                sys.exit(f"{name}: pattern occurs {n} times: {old!r}")
            text = text.replace(old, new)
        d = scratch / name; d.mkdir(exist_ok=True); m = d / TOOL.name
        if not m.exists():
            m.write_text(text, encoding="utf-8", newline="\n")
        rc, failed = suite(m, d)
        results[name] = {"caught": rc != 0, "failing_tests": failed}
        print(f"{name}: {'CAUGHT' if rc else 'SURVIVED'} {failed}", flush=True)
    caught = sum(r["caught"] for r in results.values())
    print(json.dumps({"mutants": len(results), "caught": caught}))
    (scratch / "mutation_results.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
