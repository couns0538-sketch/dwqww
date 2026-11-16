#!/usr/bin/env python3
"""seat 17 area 7: max-legal-move position (218 legal moves, the known record) under
release and ASan, perft 1 and go nodes, checking the unclamped root_effort_moves_[256]
buffer whose assert is compiled out (NDEBUG).

writes max_moves.json + one log per case.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_driver import run_one

FEN = "R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 w - - 0 1"
OUT = "smove_over"


def main():
    import chess
    os.makedirs(OUT, exist_ok=True)
    legal = {m.uci() for m in chess.Board(FEN).legal_moves}
    record = {"fen": FEN, "python_chess_legal_moves": len(legal), "cases": []}
    builds = [
        ("release", "/agent/repos/base/forge-combo29/build/forge", dict(os.environ)),
        ("asan", "/agent/repos/base/forge-combo29/build-asan/forge",
         dict(os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="print_stacktrace=1")),
    ]
    for label, exe, env in builds:
        for go, timeout in (("go perft 1", 240), ("go nodes 300000", 300)):
            tag = go.replace(" ", "_")
            log = os.path.join(OUT, "%s_%s.log" % (label, tag))
            info = run_one(exe, ["uci", "isready", "position fen " + FEN, "isready", go], timeout, log, env=env)
            text = open(log).read()
            roots = [ln.split(":")[0] for ln in text.splitlines()
                     if ":" in ln and ln.split(":")[0][:1] in "abcdefgh" and len(ln.split(":")[0]) >= 4]
            nodes = [ln for ln in text.splitlines() if ln.startswith("nodes ")]
            depths = [ln for ln in text.splitlines() if ln.startswith("info depth")]
            entry = {
                "build": label, "go": go, "bestmove": info["bestmove"], "rc": info["rc"],
                "timed_out": info["timed_out"], "elapsed_s": info["elapsed_s"],
                "roots_listed": len(roots), "nodes_line": nodes[-1] if nodes else None,
                "depth_lines": len(depths),
                "sanitizer": [w for w in ("AddressSanitizer", "runtime error:", "SUMMARY:") if w in text],
                "legal_moves_match_python_chess": (len(roots) == len(legal)) if go == "go perft 1" else None,
            }
            print(json.dumps(entry), flush=True)
            record["cases"].append(entry)
            with open(os.path.join(OUT, "max_moves.json"), "w") as handle:
                json.dump(record, handle, indent=1)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
