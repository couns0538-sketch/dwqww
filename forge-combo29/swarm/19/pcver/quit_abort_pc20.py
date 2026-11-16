#!/usr/bin/env python3
"""quit_abort_pc20.py EXE OUTDIR : 19-F12 with PC20 settings applied, on the PC build.

The base-tree finding (19-F12) was taken with NO setoption. File 5 says a finding is only reusable under a
named build and settings, so this repeats it under PC20 (S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/
MateAlphaGuard/OwnBook false) on the PC r15 build.

Same four cases as job1b/quit_abort.py, and a planted control per Rule 1: the aborted case must give 0 nodes
and the delayed-terminator case must give many, or the harness cannot see the difference.
"""
import os
import subprocess
import sys

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

POS = "position startpos"
GO = "go depth 12"


def head():
    lines = ["uci", "isready"]
    for k, v in S14 + PC20_EXTRA:
        lines += ["setoption name %s value %s" % (k, v), "isready"]
    return "\n".join(lines) + "\n" + POS + "\nisready\n" + GO + "\n"


def summarize(out):
    depth = [l for l in out.splitlines() if l.startswith("info depth")]
    best = [l for l in out.splitlines() if l.startswith("bestmove")]
    nodes = []
    for l in out.splitlines():
        if " nodes " in l:
            try:
                nodes.append(int(l.split("nodes ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
    refusals = [l for l in out.splitlines()
                if "unknown option" in l or "invalid value" in l or "ERROR" in l]
    return len(depth), (best[-1] if best else "(no bestmove)"), (max(nodes) if nodes else 0), refusals


def run(name, tail, wait=0.0, close_stdin=False):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    proc.stdin.write(head())
    proc.stdin.flush()
    if wait:
        import time
        time.sleep(wait)
    out = ""
    try:
        if close_stdin:
            proc.stdin.close()
            out = proc.stdout.read()
            proc.wait(timeout=120)
        else:
            proc.stdin.write(tail)
            proc.stdin.flush()
            out, _ = proc.communicate(timeout=120)
    except Exception as exc:  # noqa: BLE001
        out += "\nEXCEPTION %r" % (exc,)
        proc.kill()
    n_depth, best, nodes, refusals = summarize(out)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("PC20 settings; tail=%r wait=%.1f close_stdin=%s\n\n" % (tail, wait, close_stdin))
        fh.write(out)
    return name, n_depth, best, nodes, refusals


results = [
    run("A_quit_immediately", "quit\n"),
    run("B_quit_after_2s", "quit\n", wait=2.0),
    run("C_eof_immediately", "", close_stdin=True),
    run("D_same_as_A_repeat", "quit\n"),
]

lines = ["# 19-F12 on the PC r15 build under PC20", "",
         "| case | info depth lines | bestmove | max nodes | refusal lines |",
         "|---|---|---|---|---|"]
for name, n_depth, best, nodes, refusals in results:
    lines.append("| %s | %d | `%s` | %d | %d |" % (name, n_depth, best, nodes, len(refusals)))
aborted = [r for r in results if r[1] == 0]
plant_ok = any(r[1] > 0 and r[3] > 1000 for r in results) and any(r[3] == 0 for r in results)
lines += ["",
          "cases with no search at all: %s" % ", ".join(r[0] for r in aborted),
          "plant/control (one case 0 nodes AND one case > 1000 nodes, same harness): %s"
          % ("YES" if plant_ok else "NO"),
          "",
          "VERDICT 19-F12 %s on PC r15 under PC20"
          % ("STILL PRESENT" if aborted and plant_ok else "NOT REPRODUCED")]
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
