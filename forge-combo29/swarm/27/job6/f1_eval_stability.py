#!/usr/bin/env python3
"""f1_eval_stability.py <exe> <outdir>

Area 7, src/eval.cpp. The `eval` command is SYNCHRONOUS in the UCI loop (uci.cpp:575-589 prints the
components directly, no worker thread), so it is not exposed to the 19-F12 fabricated-bestmove trap.
Every parse asserts the line was found.

Three questions, each with a control:
  A. Does `eval` depend on anything that was searched before it? (It should not: it is a pure function of
     the board.) Test: eval the same FEN in a fresh process, and after a deep search, and after
     setoption flips that are documented to change the search only.
  B. Is the reported total consistent with its parts? (total should be clamp(hce+nnue) per seat 06's S-F5.)
     Check |total - clamp(hce+nnue)| == 0 on every position, and REPORT any position where it is not.
  C. Does `eval` agree with what the search reports as its static eval at depth 0? Not directly observable,
     so instead: does a position evaluated in check still return the normal components and flag incheck 1?
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

EVAL_RE = re.compile(r"^info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)(?: incheck (\d))?$")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()

    def until(self, pred, timeout=180):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n"); out.append(s)
            if pred(s):
                return out, True
        return out, False

    def boot(self):
        self.send("uci"); self.until(lambda s: s.strip() == "uciok")
        self.send("isready"); self.until(lambda s: s.strip() == "readyok")

    def eval_fen(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        _, ok = self.until(lambda s: s.strip() == "readyok")
        if not ok:
            raise RuntimeError("no readyok before eval of %r" % fen)
        self.send("eval")
        lines, ok = self.until(lambda s: s.startswith("info string eval "))
        if not ok:
            raise RuntimeError("eval produced no 'info string eval' line for %r (got %r)"
                               % (fen, lines[-3:]))
        line = next((l for l in lines if l.startswith("info string eval ")), None)
        m = EVAL_RE.match(line)
        if not m:
            raise RuntimeError("eval line did not match the expected shape: %r" % line)
        return {"hce": int(m.group(1)), "nnue": int(m.group(2)), "total": int(m.group(3)),
                "incheck": m.group(4) == "1", "line": line}

    def search(self, fen, depth):
        self.send("position fen " + fen)
        self.send("isready"); self.until(lambda s: s.strip() == "readyok")
        self.send("go depth %d" % depth)
        lines, ok = self.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise RuntimeError("no bestmove")
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise RuntimeError("no info depth line — 19-F12 signature; refusing to use this run")
        return infos[-1]

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R b KQkq - 2 8",
    "8/8/8/8/8/8/8/K6k w - - 0 1",
    "4k3/8/8/8/8/8/8/4K2R w - - 100 60",
]
# a position where the side to move IS in check
IN_CHECK = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"


def main():
    exe = os.path.realpath(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []

    # A: fresh process, no search before the eval
    e = Engine(exe); e.boot()
    for fen in FENS + [IN_CHECK]:
        r = e.eval_fen(fen)
        r["fen"] = fen; r["phase"] = "fresh"
        rows.append(r)
    # A2: same process, after a deep search
    for fen in FENS:
        e.search(fen, 12)
        r = e.eval_fen(fen)
        r["fen"] = fen; r["phase"] = "after_search"
        rows.append(r)
    e.close()

    # A3: another process with search options flipped (documented as search-only)
    e2 = Engine(exe); e2.boot()
    for opt in ("UseNNUE", "DeadMaterial", "EvalRule50Damp"):
        e2.send("setoption name %s value %s" % (opt, "false" if opt == "UseNNUE" else "true"))
    e2.send("isready"); e2.until(lambda s: s.strip() == "readyok")
    for fen in FENS:
        r = e2.eval_fen(fen)
        r["fen"] = fen; r["phase"] = "options_flipped"
        rows.append(r)
    e2.close()

    # B: total vs clamp(hce+nnue)
    inconsistent = [r for r in rows if r["total"] != max(-31743, min(31743, r["hce"] + r["nnue"]))]

    # A: fresh vs after_search vs options_flipped
    by = {}
    for r in rows:
        by.setdefault(r["fen"], {})[r["phase"]] = (r["hce"], r["nnue"], r["total"])
    drift = {fen: v for fen, v in by.items()
             if len({v[p] for p in v}) > 1}

    out = {"exe": exe,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "rows": rows,
           "inconsistent_total_vs_parts": len(inconsistent),
           "drift_between_phases": drift}
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(out, f, indent=2)

    with open(os.path.join(outdir, "SUMMARY.txt"), "w") as f:
        f.write("exe %s\nsha %s\ndate %s\n\nrows %d\n" % (exe, out["sha256"], out["date_utc"], len(rows)))
        f.write("A. eval changed by a preceding search or by search-only options: %d positions\n"
                % len(drift))
        for fen, v in drift.items():
            f.write("  %s\n" % fen)
            for phase, val in v.items():
                f.write("    %-16s hce %s nnue %s total %s\n" % (phase, val[0], val[1], val[2]))
        f.write("\nB. total != clamp(hce+nnue): %d rows\n" % len(inconsistent))
        for r in inconsistent:
            f.write("  %s\ntext: %s\n" % (r["fen"], r["line"]))
        f.write("\nC. in-check position: %s\n" % next(r["line"] for r in rows if r["fen"] == IN_CHECK))
        f.write("\nall eval lines seen (first 6):\n")
        for r in rows[:6]:
            f.write("  %s\n" % r["line"])
    print(open(os.path.join(outdir, "SUMMARY.txt")).read())


if __name__ == "__main__":
    main()
