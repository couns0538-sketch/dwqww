#!/usr/bin/env python3
"""Planted-bug (mutant) check for tests/hist_rework_tests.cpp (UCI HistRework, Astra A1).

usage: mutation_check.py <src_root> <scratch_dir>
For the unmutated tree and then for each mutant (one planted bug each, every pattern must occur exactly once),
copy src/ include/ tests/ to <scratch_dir>/<run>/<name>/, build the test with build_test.sh (direct g++) and run
it. The baseline must pass; every mutant must make the test FAIL. Nothing is deleted; run it under nice -n 19.
Exit 0 only if the baseline passes and every mutant is caught."""
import os
import shutil
import subprocess
import sys
import time

HDR = "include/forge/hist_rework.hpp"
SRC = "src/search.cpp"

MUTANTS = [
    ("blend_divisor_3", HDR, [("return (plain * (4 - quarters) + threat * quarters) / 4;",
                               "return (plain * (4 - quarters) + threat * quarters) / 3;")]),
    ("gravity_divisor_doubled", HDR, [("const std::int32_t next = entry + step - entry * magnitude / limit;",
                                       "const std::int32_t next = entry + step - entry * magnitude / (limit * 2);")]),
    ("rook_threat_pawn_only", HDR, [("threats.by_type[static_cast<std::size_t>(Rook)] = by_minor;",
                                     "threats.by_type[static_cast<std::size_t>(Rook)] = by_pawn;")]),
    ("queen_threat_without_rooks", HDR, [("threats.by_type[static_cast<std::size_t>(Queen)] = by_rook;",
                                          "threats.by_type[static_cast<std::size_t>(Queen)] = by_minor;")]),
    ("level_clamp_off_by_one", HDR, [("(level > MaxLevel ? MaxLevel : level)",
                                      "(level > MaxLevel ? MaxLevel + 1 : level)")]),
    ("joint_weight_plus_25", HDR, [("return 25 * clamp_level(level) + 25;",
                                    "return 25 * clamp_level(level) + 50;")]),
    ("signature_shift_3", HDR, [("signature = (signature << 4U)", "signature = (signature << 3U)")]),
    ("slot_from_to_swapped", SRC, [("[hist_rework::square_bit(set, move.from)]\n                             [hist_rework::square_bit(set, move.to)]",
                                    "[hist_rework::square_bit(set, move.to)]\n                             [hist_rework::square_bit(set, move.from)]")]),
    ("read_quarters_minus_1", SRC, [("hist_rework::blend(score, threat_history_entry(board, ss, move), hist_rework::threat_quarters(level));",
                                     "hist_rework::blend(score, threat_history_entry(board, ss, move), hist_rework::threat_quarters(level) - 1);")]),
    ("threat_malus_sign", SRC, [("apply_history(threat_history_entry(board, ss, quiets[i]), -bonus);",
                                 "apply_history(threat_history_entry(board, ss, quiets[i]), bonus);")]),
    ("joint_step_doubled", SRC, [("entry = hist_rework::gravity(entry, diff * weight / 256, CorrectionLimit);",
                                  "entry = hist_rework::gravity(entry, diff * weight / 128, CorrectionLimit);")]),
    ("joint_update_when_off", SRC, [("    if (search_options::hist_rework != 0) [[unlikely]] {\n        // HistRework: the joint table learns",
                                     "    if (search_options::hist_rework >= 0) [[unlikely]] {\n        // HistRework: the joint table learns")]),
]


def copy_tree(root, dest):
    for part in ("src", "include", "tests"):
        shutil.copytree(os.path.join(root, part), os.path.join(dest, part))


def build_and_run(tools, tree, exe):
    b = subprocess.run(["bash", os.path.join(tools, "build_test.sh"), tree, exe], capture_output=True, text=True)
    if b.returncode != 0:
        return None, (b.stdout + b.stderr)[-3000:]
    r = subprocess.run([exe], capture_output=True, text=True, timeout=1800)
    return r.returncode, r.stdout


def main():
    root, scratch = sys.argv[1], sys.argv[2]
    tools = os.path.join(root, "opus_round1", "sol_A1", "tools")
    run_dir = os.path.join(scratch, "mutants_" + time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir)
    print(f"source {root}\nscratch {run_dir}", flush=True)
    ok = True
    base = os.path.join(run_dir, "baseline")
    copy_tree(root, base)
    rc, out = build_and_run(tools, base, os.path.join(base, "hist_rework_tests.exe"))
    summary = [line for line in out.splitlines() if line.startswith("SUMMARY")]
    print(f"BASELINE (unmutated): rc={rc} {summary[-1] if summary else out[-500:]}", flush=True)
    if rc != 0:
        ok = False
    for name, rel, edits in MUTANTS:
        tree = os.path.join(run_dir, name)
        copy_tree(root, tree)
        path = os.path.join(tree, rel)
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        for old, new in edits:
            count = text.count(old)
            if count != 1:
                print(f"MUTATION {name}: pattern occurs {count} times in {rel} -> HARNESS ERROR", flush=True)
                ok = False
                break
            text = text.replace(old, new)
        else:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            rc, out = build_and_run(tools, tree, os.path.join(tree, "hist_rework_tests.exe"))
            if rc is None:
                print(f"MUTATION {name} -> BUILD FAILED (not counted as caught)\n{out}", flush=True)
                ok = False
                continue
            fails = [line for line in out.splitlines() if line.startswith("FAIL")]
            caught = rc != 0
            ok &= caught
            print(f"MUTATION {name} ({rel}) -> {'caught' if caught else 'NOT CAUGHT'} rc={rc} "
                  f"failing_lines={len(fails)}", flush=True)
            for line in fails[:3]:
                print(f"    {line}", flush=True)
    print(f"mutation_check status={'0' if ok else '1'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
