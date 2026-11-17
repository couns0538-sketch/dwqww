"""Fault proofs. Every checker in this seat must fire on a planted fault.

The brief's rule 3: "a control that silently does nothing is worse than no
control." So this plants known-bad inputs and asserts the measuring code
NOTICES. A clean run of the real measurement is only admissible if each of
these fires.

Faults:
  F1  piped `quit` into a live search -> fabricated bestmove, zero info lines.
      Proves ucih.py's n_info_depth check catches the exact fabrication the
      audit recorded, and that our driver is not the piped form.
  F2  a refused FEN -> harness must see pos_refused (engine re-searches prev).
  F3  Threads 4 -> harness must see >1 distinct score where Threads 1 sees 1.
      This is the positive control for the whole distinct-score instrument:
      if the instrument could not see Threads 4 variation, a Threads-1 zero
      would be meaningless.
  F4  OwnBook true + clock search -> harness must see a book reply (no info
      depth lines) and be able to tell it apart from a searched reply.
  F5  Book Variety 0 vs default -> proves the book RNG is what varies, so the
      OwnBook false pin is the right pin and not superstition.
  F6  injected score mutation -> the comparison function must flag score-only.
  F7  injected depth mutation -> must flag depth.
  F8  a real threefold root -> the bail detector must fire (nodes 0, bare `pv`).
  F9  a searching position -> the bail detector must stay SILENT. The negative
      control; without it a detector hard-wired to True would pass F8.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import Uci, run_one, score_key

FORGE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-stab/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "fault_proof.json"
POS = "position startpos moves h2h3 g8h6 e2e3 g7g6 f1d3 c7c6 g1f3 h6g8 d3e2 g8f6 c2c4 f8g7 d2d4 d7d5 b1c3 d5c4 e2c4 b7b5 c4d3 e8g8 e3e4 c6c5 e4e5 f6h5 d4c5 b8c6 d3e4 d8d1 e1d1 c8b7"
results = []


def rec(name, fired, detail):
    results.append({"fault": name, "fired": bool(fired), "detail": detail})
    print(f"{name:6} {'FIRED' if fired else 'MISSED'}  {detail}")


# F1: the piped form, straight through a shell pipe, exactly as the audit did it
p = subprocess.run(
    f"printf 'uci\\nisready\\n{ POS }\\ngo depth 8\\nquit\\n' | {FORGE}",
    shell=True, capture_output=True, text=True, timeout=120)
lines = p.stdout.splitlines()
best = [l for l in lines if l.startswith("bestmove")]
depths = [l for l in lines if l.startswith("info") and " depth " in l]
# A legal move does not prove a search ran; only the absence of depth lines does.
rec("F1", best and not depths,
    f"piped run: bestmove={best[0].split()[1] if best else None} "
    f"info_depth_lines={len(depths)} (fabrication signature = a bestmove with 0 depth lines)")

# F2: a refused FEN must be visible to the harness
bad_fen = "4k3/8/8/8/8/8/8/R3K2R w K - 0 0"     # fullmove 0: python-chess valid, engine refuses
r = run_one(FORGE, f"position fen {bad_fen}", "go depth 6",
            options=["setoption name OwnBook value false"])
rec("F2", r["pos_refused"], f"refused={r['pos_refused']} bestmove={r['bestmove']} "
                             f"pos_reply={r['pos_reply']}")

# F3: Threads 4 must produce more than one distinct score on this position
def distinct(threads, runs=8):
    s = set()
    for _ in range(runs):
        rr = run_one(FORGE, POS, "go depth 12",
                     options=["setoption name OwnBook value false",
                              f"setoption name Threads value {threads}",
                              "setoption name Hash value 32"])
        s.add(score_key(rr))
    return s

t1 = distinct(1)
t4 = distinct(4)
rec("F3", len(t4) > 1 and len(t1) == 1,
    f"T1 distinct={len(t1)} T4 distinct={len(t4)} (instrument must see T4 variation)")

# F4/F5: the book path, and its RNG, on a clock search
BOOK_POS = "position startpos"
def book_probe(own_book, variety, runs=8):
    outs = []
    for _ in range(runs):
        opts = ["setoption name OwnBook value " + ("true" if own_book else "false")]
        if variety is not None:
            opts.append(f"setoption name Book Variety value {variety}")
        rr = run_one(FORGE, BOOK_POS, "go movetime 300", options=opts)
        outs.append((rr["bestmove"], rr["n_info_depth"]))
    return outs

b_default = book_probe(True, None)
b_zero = book_probe(True, 0)
b_off = book_probe(False, None)
book_reply = [o for o in b_default if o[1] == 0]
distinct_default = len({o[0] for o in b_default})
distinct_zero = len({o[0] for o in b_zero})
rec("F4", bool(book_reply) and all(o[1] > 0 for o in b_off),
    f"OwnBook true: {len(book_reply)}/{len(b_default)} replies had 0 info-depth lines (book); "
    f"OwnBook false: {sum(1 for o in b_off if o[1] == 0)}/{len(b_off)} did")
rec("F5", distinct_default > distinct_zero,
    f"book moves distinct: default-variety={distinct_default}/{len(b_default)} "
    f"variety0={distinct_zero}/{len(b_zero)} -> pinning Book Variety 0 removes the RNG; "
    f"OwnBook false also removes it ({len({o[0] for o in b_off})}/{len(b_off)})")

# F6/F7: the comparison must flag injected single-field mutations
base = {"score_cp": 100, "score_mate": None, "depth": 12, "bestmove": "e2e4"}
def compare(x, y):
    return {"score": score_key(x) != score_key(y),
            "depth": x["depth"] != y["depth"],
            "bestmove": x["bestmove"] != y["bestmove"]}
m6 = compare(base, dict(base, score_cp=140))
m7 = compare(base, dict(base, depth=11))
rec("F6", m6["score"] and not m6["depth"] and not m6["bestmove"],
    f"score-only mutation -> {m6}")
rec("F7", m7["depth"] and not m7["score"] and not m7["bestmove"],
    f"depth-only mutation -> {m7}")

# F8/F9: the drawn-root (bail) detector. Both arms are required: the flag must
# fire on a real bail and stay silent on a position that searched. A detector
# that always returns True passes F8 alone, so the negative control is the half
# that makes the positive half mean anything.
THREEFOLD = "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
rb = run_one(FORGE, THREEFOLD, "go depth 12",
             options=["setoption name OwnBook value false", "setoption name Threads value 1"])
rs = run_one(FORGE, "position startpos", "go depth 8",
             options=["setoption name OwnBook value false", "setoption name Threads value 1"])
rec("F8", rb["bail"] and rb["nodes"] == 0,
    f"real threefold -> bail={rb['bail']} nodes={rb['nodes']} pv={rb['pv']!r} bestmove={rb['bestmove']}")
rec("F9", not rs["bail"] and rs["nodes"] > 0,
    f"searching position -> bail={rs['bail']} nodes={rs['nodes']} (negative control)")

fired = sum(1 for r in results if r["fired"])
with open(OUT, "w") as f:
    json.dump({"fired": fired, "total": len(results), "results": results,
               "book_default": b_default, "book_zero": b_zero, "book_off": b_off}, f, indent=1)
print(f"\n{fired}/{len(results)} fault proofs fired")
sys.exit(0 if fired == len(results) else 1)
