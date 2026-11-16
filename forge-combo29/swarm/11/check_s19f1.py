#!/usr/bin/env python3
"""check_s19f1.py EXE SRCROOT — seat 11's INDEPENDENT check of seat 19's 19-F1.

19-F1 claims (from its one sentence):
  "The compiled net is a residual net (src/nnue_weights.inc:3), so `Worker::static_evaluate`
   pays both the NNUE forward pass and the whole hand-crafted term walk on every eval."

I test this WITHOUT a profiler, which is what makes it a different check from seat 19's:
  1. the weights header declares the residual model,
  2. the source has an early `if (!residual) return network;` — i.e. a non-residual build would
     return right after the network, so the hand-crafted walk is conditional on residual,
  3. the ENGINE ITSELF reports both components for one position: the `eval` command prints
     `info string eval hce <x> nnue <y> total <z>` with z = x + y and both non-zero.
Point 3 is the empirical part: if the residual path were not taken, `hce` would not be
reported as a separate non-zero term.
Control: a position where the two numbers must differ from the first one (so the harness is
not reading a constant), and a check that changing the position changes at least one number.
"""
import re, subprocess, sys

EXE, SRC = sys.argv[1], sys.argv[2]
ok_all = True


def check(name, ok, detail=""):
    global ok_all
    ok_all = ok_all and ok
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")


print("=== 1. weights header ===")
hdr = open(f"{SRC}/src/nnue_weights.inc").read().splitlines()
line3 = hdr[2] if len(hdr) > 2 else ""
print(f"  line 3: {line3!r}")
check("line 3 declares FORGE_NNUE_RESIDUAL 1", "FORGE_NNUE_RESIDUAL 1" in line3)

print("\n=== 2. source: the residual early-return ===")
search = open(f"{SRC}/src/search.cpp").read()
has_early = "if (!residual) return network;" in search
print(f"  'if (!residual) return network;' present: {has_early}")
m = re.search(r"return std::clamp\(evaluator_\.evaluate_runtime\(board, \*psqt\) \+ network", search)
check("non-residual builds return right after the net", has_early)
check("residual builds ADD the hand-crafted walk to the net", m is not None)


def evaluate(fen=None):
    inp = "uci\n" + (f"position fen {fen}\n" if fen else "") + "isready\neval\nquit\n"
    p = subprocess.run([EXE], input=inp, capture_output=True, text=True, timeout=60)
    m = re.search(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", p.stdout)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


print("\n=== 3. the engine reports both components (empirical part) ===")
start = evaluate()
print(f"  startpos: hce, nnue, total = {start}")
if start:
    hce, nnue, total = start
    check("hce is non-zero (hand-crafted walk ran)", hce != 0, f"hce={hce}")
    check("nnue is non-zero (net ran)", nnue != 0, f"nnue={nnue}")
    check("total == hce + nnue", total == hce + nnue, f"{hce}+{nnue}={total}")
else:
    check("eval command prints hce/nnue/total", False)

print("\n=== control: a different position must change at least one number ===")
other = evaluate("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4")
print(f"  other position: {other}")
if start and other:
    check("the pair changed (harness is reading the position, not a constant)", other != start)
    if other[0] is not None:
        h2, n2, t2 = other
        check("total == hce + nnue on the second position too", t2 == h2 + n2)

print("\n=== verdict on 19-F1 ===")
if ok_all:
    print("RESULT: CONFIRMS 19-F1 — the net is residual and one static_evaluate call includes")
    print("        both the network and the hand-crafted term walk (the engine's own `eval`")
    print("        line shows both non-zero and additive).")
    print("        NOT reproduced here: seat 19's percentage shares (16.51 % / 11.84 %), which")
    print("        need their profiler; I did not measure percentages at all.")
else:
    print("RESULT: does NOT confirm 19-F1 — see the FAIL lines above.")
