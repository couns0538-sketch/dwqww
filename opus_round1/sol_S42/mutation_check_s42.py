#!/usr/bin/env python3
"""Planted-bug check for the S42 tools: an unmutated control must pass, every mutant must make the suite FAIL.
usage: python -I -B mutation_check_s42.py SCRATCH_DIR"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "forge_sol_S42_book_v2_20261027.py"
POWER = HERE / "forge_sol_S42_power_20261027.py"
TEST = HERE / "test_forge_sol_S42_20261027.py"
MUTANTS = {
    "M1_band_ignores_black_favoured": (BOOK, [("ok = a.lo <= abs(ev) <= a.hi", "ok = a.lo <= ev <= a.hi")]),
    "M2_book_exit_dedupe_off": (BOOK, [("            if ident in book_ids:\n", "            if False:\n")]),
    "M3_gate_points_swapped": (BOOK, [('p = pts[gm["result"]][0 if cw else 1]', 'p = pts[gm["result"]][1 if cw else 0]')]),
    "M4_pair_convolution_drops_LW": (POWER, [("d1 * d2 + w1 * l2 + l1 * w2", "d1 * d2 + w1 * l2")]),
    "M5_model_colour_sign_lost": (POWER, [("x = delta + s * ((c * e if use_eval else 0.0) + w)", "x = delta + ((c * e if use_eval else 0.0) + w)")]),
    "M6_draw_width_sign": (POWER, [("pw = F(x - d); pl = F(-x - d)", "pw = F(x - d); pl = F(-x + d)")]),
    "M7_sample_unseeded": (BOOK, [("rng = random.Random(a.seed); idx = sorted(", "rng = random.Random(); idx = sorted(")]),
    "M8_build_unseeded_order": (BOOK, [("    rng = random.Random(a.seed)\n    order = list(range(len(lines))); rng.shuffle(order)",
                                        "    rng = random.Random()\n    order = list(range(len(lines))); rng.shuffle(order)")]),
}


def suite(env_extra, tmp):
    env = dict(os.environ, FORGE_S42_TMP=str(tmp), **env_extra)
    p = subprocess.run([sys.executable, "-I", "-B", str(TEST)], env=env, capture_output=True, text=True)
    return p.returncode, [l.split(" (")[0] for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]


def main():
    scratch = Path(sys.argv[1]); scratch.mkdir(parents=True, exist_ok=True); results = {}
    c = scratch / "M00_control"; c.mkdir(exist_ok=True)
    rc, failed = suite({}, c)
    print(f"M00_control: {'PASS' if rc == 0 else 'FAIL ' + str(failed)}", flush=True)
    if rc:
        return 2
    for name, (target, edits) in MUTANTS.items():
        text = target.read_text(encoding="utf-8")
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                sys.exit(f"{name}: pattern occurs {n} times: {old!r}")
            text = text.replace(old, new)
        d = scratch / name; d.mkdir(exist_ok=True); m = d / target.name
        if not m.exists():
            m.write_text(text, encoding="utf-8", newline="\n")
        key = "FORGE_S42_TOOL" if target == BOOK else "FORGE_S42_POWER"
        rc, failed = suite({key: str(m)}, d)
        results[name] = {"caught": rc != 0, "failing_tests": failed}
        print(f"{name}: {'CAUGHT' if rc else 'SURVIVED'} {failed}", flush=True)
    caught = sum(r["caught"] for r in results.values())
    print(json.dumps({"mutants": len(results), "caught": caught}))
    (scratch / "mutation_results.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
