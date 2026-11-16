#!/usr/bin/env python3
"""go_parse.py OUTDIR

Probe of the PC patch's OWN new surfaces, at Threads 1. Not a re-test of the repaired
halfmove door: these are the `go`-line and option surfaces the patch itself adds or fixes.

Every case is a FRESH process on the PC build, read to bestmove (19-F12), with a monotonic
timing and an explicit note of whether the answer looked like a real search (info lines and
nodes > 0) or an instant 0-node reply.

Cases:
  go depth                depth named, NO value            (the shape FORGE_FIX_GO_PARSE names)
  go depth 5              control: a real depth limit
  go wtime btime 50       keyword where a value belongs     (r9 lost the clock here)
  go nodes abc            non-integer nodes value
  go movetime             no value
  go wtime 1000 btime 1000 control
  go depth -3             negative depth (r9 clamps to 1)
  go depth 0              zero depth (r9 clamps to 1)
  go banana               unknown keyword

Options:
  HistRework 0..3 accepted, 4 and -1 refused
  MateAlphaGuard present on the PC build, `unknown option` on the base build
"""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402

BAD = ("unknown option", "invalid value", "ERROR")
GOS = ["go depth", "go depth 5", "go wtime btime 50", "go nodes abc", "go movetime",
       "go wtime 1000 btime 1000", "go depth -3", "go depth 0", "go banana"]


def probe(exe, outdir, tag, go_line):
    raw = os.path.join(outdir, tag + "_raw.txt")
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    e.position("position startpos")
    t0 = time.monotonic()
    try:
        lines = e.go(go_line, timeout=20)
        timed_out = False
    except Timeout:
        lines = []
        timed_out = True
    dt = (time.monotonic() - t0) * 1000.0
    e.close()
    bm = bestmove_of(lines) if lines else ""
    infos = [l for l in lines if l.startswith("info depth")]
    nodes = None
    if infos:
        m = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(m.group(1)) if m else None
    return dict(go=go_line, bestmove=bm, infos=len(infos), nodes=nodes,
                ms=round(dt, 2), timed_out=timed_out,
                last=infos[-1] if infos else "")


def setopt(exe, outdir, tag, name, value):
    raw = os.path.join(outdir, tag + "_raw.txt")
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    script = "uci\nsetoption name %s value %s\nisready\nquit\n" % (name, value)
    p = subprocess.run([exe], input=script, text=True, capture_output=True, timeout=60, env=env)
    out = p.stdout + p.stderr
    with open(raw, "w") as fh:
        fh.write(">>> %s = %s\n%s\n" % (name, value, out))
    bad = [l for l in out.splitlines() if any(b in l for b in BAD)]
    return bad


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    pc = os.path.expanduser("~/b/pc_asan/forge")
    base = os.path.expanduser("~/b/asan/forge")
    R = {"go": {}, "options": {}}
    rows = ["| go line | bestmove | info lines | nodes | ms | timeout |",
            "|---|---|---|---|---|---|"]
    for g in GOS:
        r = probe(pc, outdir, "go_" + re.sub(r"[^a-z0-9]+", "_", g), g)
        R["go"][g] = r
        rows.append("| `%s` | %s | %d | %s | %.2f | %s |" % (
            g, r["bestmove"], r["infos"], r["nodes"], r["ms"], r["timed_out"]))

    opt_rows = ["| option | value | PC build | base build |", "|---|---|---|---|"]
    checks = [("HistRework", v) for v in ("0", "1", "2", "3", "4", "-1")]
    checks += [("MateAlphaGuard", "true"), ("CuckooRep", "true"), ("TtPruneV2", "true"),
               ("CorrHistV2", "true")]
    for name, val in checks:
        bad_pc = setopt(pc, outdir, "opt_pc_%s_%s" % (name, val), name, val)
        bad_base = setopt(base, outdir, "opt_base_%s_%s" % (name, val), name, val)
        R["options"]["%s=%s" % (name, val)] = dict(pc=bad_pc, base=bad_base)
        opt_rows.append("| %s | %s | %s | %s |" % (
            name, val, "refused: " + bad_pc[0] if bad_pc else "accepted",
            "refused: " + bad_base[0] if bad_base else "accepted"))

    text = "\n".join(rows) + "\n\n" + "\n".join(opt_rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()