"""Pair 7: UseNNUE x NnueFile x NNUEArch (the loader path). Which one wins?

This pair has a trap the others do not: `NNUEArch` does not exist in the default
build. The CMake recipe in the brief does not define FORGE_NNUE_V3, and
`include/forge/nnue.hpp:11` defaults it to 0, so on the audit build the engine
answers `info string unknown option NNUEArch` and there is nothing to measure.
That is recorded here as a cell rather than skipped, because "the option is not
in the build" and "the option is in the build and does nothing" are different
facts and only one of them is about the loader.

Two binaries:
  BIN_AUDIT  the brief's build (no FORGE_NNUE_V3) -- NNUEArch must be UNKNOWN
  BIN_V3     the same source with -DFORGE_NNUE_V3=1 -- NNUEArch exists

Precedence in the search (search.cpp:1073-1130):
  1. `!nnue::enabled || !nnue::available()`  -> hand-crafted eval, nothing else runs
  2. `nnue::v3::active()`                    -> v3 net
  3. otherwise                               -> v2 net (NnueFile) + residual HCE
So the predicted order is UseNNUE > NNUEArch > NnueFile, and the test is whether
the measurement agrees. Each net is built to be identifiable from `eval`, so the
"which one won" question is answered by a number and not by a log line.
"""
import json
import os
import subprocess
import sys

import grid
import uci

HERE = os.path.dirname(os.path.abspath(__file__))
NETS = os.path.join(os.path.dirname(HERE), "evidence", "nets")
AUDIT = "/tmp/build-optpairs/forge"
V3 = "/tmp/build-v3/forge"
POS = [("p05_kr_vs_k", grid.POSITIONS[4][1]),
       ("p02_italian", grid.POSITIONS[1][1]),
       ("p11_queenend", grid.POSITIONS[10][1])]
GO = "go depth 8"

V2ZERO = os.path.join(NETS, "v2zero.bin")
V2DOUBLE = os.path.join(NETS, "v2double.bin")
V3A = os.path.join(NETS, "v3a.bin")
V3B = os.path.join(NETS, "v3b.bin")
V3BAD = os.path.join(NETS, "v3a-corrupt.bin")
V3RES = os.path.join(NETS, "v3a-residual.bin")


def raw_eval(bin_path, options, fen):
    """`eval` is not a search: it prints the components, which names the evaluator."""
    p = subprocess.run([bin_path], input="\n".join(
        ["uci"] + [f"setoption name {n}" if v is None else f"setoption name {n} value {v}" for n, v in options]
        + ["isready", f"position fen {fen}", "eval", "quit"]) + "\n",
        capture_output=True, text=True, timeout=120)
    lines = [l for l in p.stdout.splitlines() if l.startswith("info string")]
    return {"exit": p.returncode, "lines": lines,
            "eval": next((l for l in lines if " eval " in l), None)}


def cell(bin_path, options):
    rows = {}
    for name, fen in POS:
        r = uci.run(options=options, position=fen, go=GO, bin_path=bin_path)
        e = raw_eval(bin_path, options, fen)
        rows[name] = {"bestmove": r["bestmove"], "score_kind": r["score_kind"], "score": r["score"],
                      "depth": r["depth"], "nodes": r["nodes"], "accepted": r["accepted"],
                      "rejected": r["rejected"], "diag": r["diag"], "eval_line": e["eval"],
                      "eval_exit": e["exit"], "search_exit": r["exit_code"],
                      "loaded_lines": [l for l in e["lines"] if "loaded" in l or "NNUE v3" in l]}
    return rows


ARMS = [
    ("audit_default", AUDIT, [("OwnBook", "false")]),
    ("audit_NNUEArch_unknown", AUDIT, [("OwnBook", "false"), ("NNUEArch", "true")]),
    ("v3_off_no_net", V3, [("OwnBook", "false")]),
    ("v3_off_NnueFile_zero", V3, [("OwnBook", "false"), ("NnueFile", V2ZERO)]),
    ("v3_off_NnueFile_double", V3, [("OwnBook", "false"), ("NnueFile", V2DOUBLE)]),
    ("useNNUE_false", V3, [("OwnBook", "false"), ("UseNNUE", "false")]),
    ("useNNUE_false_with_nets", V3, [("OwnBook", "false"), ("UseNNUE", "false"),
                                    ("NnueFile", V2DOUBLE), ("NNUEArchFile", V3B), ("NNUEArch", "true")]),
    ("v3A_only", V3, [("OwnBook", "false"), ("NNUEArchFile", V3A), ("NNUEArch", "true")]),
    ("v3B_only", V3, [("OwnBook", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true")]),
    ("v2double_then_v3B", V3, [("OwnBook", "false"), ("NnueFile", V2DOUBLE),
                               ("NNUEArchFile", V3B), ("NNUEArch", "true")]),
    ("v3B_then_v2double", V3, [("OwnBook", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true"),
                               ("NnueFile", V2DOUBLE)]),
    ("v3B_then_empty_NnueFile", V3, [("OwnBook", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true"),
                                     ("NnueFile", "<empty>")]),
    ("v3B_then_arch_off", V3, [("OwnBook", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true"),
                               ("NNUEArch", "false")]),
    ("V3B_then_NNUEArchFile_empty", V3, [("OwnBook", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true"),
                                         ("NNUEArchFile", "<empty>")]),
    ("useNNUE_false_v2double_only", V3, [("OwnBook", "false"), ("UseNNUE", "false"), ("NnueFile", V2DOUBLE)]),
    ("v3_bad_checksum", V3, [("OwnBook", "false"), ("NNUEArchFile", V3BAD), ("NNUEArch", "true")]),
    ("v3_residual_refused", V3, [("OwnBook", "false"), ("NNUEArchFile", V3RES), ("NNUEArch", "true")]),
    ("arch_on_no_file", V3, [("OwnBook", "false"), ("NNUEArch", "true")]),
]


def main():
    out = {"go": GO, "positions": [p for p, _ in POS], "arms": {}}
    for label, bin_path, options in ARMS:
        out["arms"][label] = {"bin": bin_path, "options": options, "rows": cell(bin_path, options)}
    with open(os.path.join(grid.EVID, "pair7-loader.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print(f"UseNNUE x NnueFile x NNUEArch, {GO}, {len(POS)} positions")
    print(f"  {'arm':26s} {'accept':6s} {'eval (p05)':38s} {'search p05':22s} v3-diag")
    for label, _, _ in ARMS:
        rows = out["arms"][label]["rows"]
        r = rows["p05_kr_vs_k"]
        ev = (r["eval_line"] or "-").replace("info string ", "")
        search = f"{r['bestmove']} {r['score_kind']} {r['score']} n={r['nodes']}"
        diag = next((d for d in r["diag"] if "NNUE v3" in d or "unknown option" in d or "nnue:" in d), "")
        print(f"  {label:26s} {str(r['accepted']):6s} {ev[:38]:38s} {search:22s} {diag[:70]}")
    with open(os.path.join(grid.EVID, "pair7-loader.txt"), "w") as fh:
        for label, _, _ in ARMS:
            rows = out["arms"][label]["rows"]
            fh.write(f"### {label}  bin={out['arms'][label]['bin']}\n")
            for name, r in rows.items():
                fh.write(f"  {name}: bestmove {r['bestmove']} {r['score_kind']} {r['score']} "
                         f"depth {r['depth']} nodes {r['nodes']} accepted {r['accepted']}\n")
                fh.write(f"    eval: {r['eval_line']}\n")
                for l in r["diag"]:
                    fh.write(f"    diag: {l}\n")
            fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
