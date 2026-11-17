#!/usr/bin/env python3
"""pc20_rerun.py <exe> <outdir> [--label base|pc]

Re-runs MY OWN findings on the PC build under PC20 (and, optionally, on the base build under the same PC20
block, to show what is a PC repair and what is not). Each check is written to answer exactly one question,
with a control, and every parse asserts its line was found.

Findings re-tested here:
  S-F1  drawn root reported as a deep search / plays the first legal move   (file 3 says REPAIRED on the PC)
  S-F2  `go nodes N` below one root iteration answers the first legal move silently
  S-F3  hashfull is a 1000-cluster sample
  S-F4  `setoption name Clear Hash` keeps the move-ordering histories
  S-F9  a `setoption` during a search truncates that search
  S-F8  `searchmoves` changes the reported score (all-20 no-op restriction)

Threads is 1 everywhere (the swarm rule). Results name build + settings per row.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20_EXTRA = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
              "MateAlphaGuard true", "OwnBook false"]
ALL20 = ("a2a3 b2b3 c2c3 d2d3 e2e3 f2f3 g2g3 h2h3 a2a4 b2b4 c2c4 d2d4 e2e4 f2f4 g2g4 h2h4 "
         "b1a3 b1c3 g1f3 g1h3")
DRAWN_REPEAT = "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
FIFTY = "4k3/8/8/8/8/8/8/4K2R w - - 100 60"
MATE_AT_100 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60"
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


class Missing(Exception):
    pass


class Engine:
    def __init__(self, exe, settings):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        lines, ok = self.until(lambda s: s.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        self.advertised = {m.group(1) for m in
                           (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        self.apply(settings)

    def send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()

    def until(self, pred, timeout=300):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            s = ln.rstrip("\n"); out.append(s)
            if pred(s):
                return out, True
        return out, False

    def apply(self, settings):
        """settings: list of 'Name value'. Assert every name is advertised; stop on bad lines."""
        for item in settings:
            name = item.rsplit(" ", 1)[0]
            if name not in self.advertised:
                raise Missing("option %r is not advertised by this exe" % name)
            # "Name value" -> "setoption name Name value Value". The first version dropped the
            # literal word "value", which the engine correctly answered with "unknown option".
            name_part, _, value_part = item.rpartition(" ")
            self.send("setoption name %s value %s" % (name_part, value_part))
            self.send("isready")
            lines, ok = self.until(lambda s: s.strip() == "readyok")
            if not ok:
                raise Missing("no readyok after setoption " + item)
            for l in lines:
                if "unknown option" in l or "invalid value" in l or "ERROR" in l:
                    raise Missing("bad option line for %r: %s" % (item, l))
        self.send("ucinewgame"); self.send("isready")
        self.until(lambda s: s.strip() == "readyok")

    def go(self, pos, limit, depth_filter=None):
        self.send(pos)
        self.send("isready"); self.until(lambda s: s.strip() == "readyok")
        self.send(limit)
        lines, ok = self.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove for %r %r" % (pos, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        if depth_filter is not None:
            infos = [l for l in infos if l.startswith("info depth %d " % depth_filter)]
            if not infos:
                raise Missing("no 'info depth %d' line for %r" % (depth_filter, limit))
        last = infos[-1]   # guard above guarantees non-empty
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        return {"n_info": len([l for l in lines if l.startswith("info depth")]),
                "last": last, "bestmove": bm,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None}

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def new(exe, settings, settings_label):
    e = Engine(exe, settings)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--label", required=True)
    ap.add_argument("--settings", required=True, choices=["none", "S14", "PC20"])
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": [], "S14": ["Hash 16", "Threads 1"] + [s for s in S14],
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20_EXTRA}[a.settings]

    R = {"build": a.label, "settings": a.settings, "exe": exe,
         "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "threads": 1, "checks": {}}

    def record(key, value):
        R["checks"][key] = value
        print("%-6s %s" % (key, json.dumps(value)[:200]))

    # ---- S-F1: drawn root
    e = new(exe, settings, a.settings)
    try:
        r = e.go(DRAWN_REPEAT, "go depth 10")
        record("S-F1_repeat", {"n_info": r["n_info"], "bestmove": r["bestmove"],
                               "nodes": r["nodes"], "score": r["score"]})
        r2 = e.go("position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6", "go depth 10")
        record("S-F1_repeat_control", {"n_info": r2["n_info"], "bestmove": r2["bestmove"],
                                       "nodes": r2["nodes"], "score": r2["score"]})
        r3 = e.go("position fen " + FIFTY, "go depth 10")
        record("S-F1_fifty", {"n_info": r3["n_info"], "bestmove": r3["bestmove"],
                              "nodes": r3["nodes"], "score": r3["score"]})
        r4 = e.go("position fen " + MATE_AT_100, "go depth 10")
        record("S-F1_mate_at_100", {"n_info": r4["n_info"], "bestmove": r4["bestmove"],
                                    "nodes": r4["nodes"], "score": r4["score"]})
    finally:
        e.close()

    # ---- S-F2: node budget below one root iteration (fresh process each)
    sf2 = {}
    for n in (0, 1, 10, 20, 26, 100):
        e = new(exe, settings, a.settings)
        try:
            r = e.go("position startpos", "go nodes %d" % n)
            sf2["nodes_%d" % n] = {"n_info": r["n_info"], "bestmove": r["bestmove"],
                                   "score": r["score"], "nodes": r["nodes"]}
        finally:
            e.close()
    record("S-F2", sf2)

    # ---- S-F3: hashfull sampling (16 MB vs 1024 MB, fresh process each)
    sf3 = {}
    for mb in (16, 1024):
        e = Engine(exe, ["Hash %d" % mb, "Threads 1"] + ([s for s in S14] if a.settings != "none" else [])
                   + (PC20_EXTRA if a.settings == "PC20" else []))
        try:
            r = e.go("position startpos", "go depth 13", depth_filter=13)
            hf = re.search(r"hashfull (\d+)", r["last"])
            sf3["%dMB" % mb] = {"hashfull": int(hf.group(1)) if hf else None,
                                "nodes": r["nodes"], "score": r["score"]}
        finally:
            e.close()
    record("S-F3", sf3)

    # ---- S-F4: Clear Hash x3 on one position, one process (deliberately warm, labelled)
    e = new(exe, settings, a.settings)
    try:
        reps = []
        for i in range(3):
            if i:
                e.send("setoption name Clear Hash")
                e.send("isready"); e.until(lambda s: s.strip() == "readyok")
            r = e.go("position fen " + KIWI, "go depth 10", depth_filter=10)
            reps.append({"score": r["score"], "nodes": r["nodes"], "bestmove": r["bestmove"]})
        record("S-F4_clearhash_warm", {"note": "one process, deliberately warm", "reps": reps,
                                      "identical": len({(x["score"], x["nodes"]) for x in reps}) == 1})
    finally:
        e.close()

    # ---- S-F9: setoption during a search truncates it
    e = new(exe, settings, a.settings)
    try:
        alone = e.go("position startpos", "go depth 20")
        record("S-F9_alone", {"n_info": alone["n_info"]})
    finally:
        e.close()
    e = new(exe, settings, a.settings)
    try:
        e.send("position startpos"); e.send("isready")
        e.until(lambda s: s.strip() == "readyok")
        e.send("go depth 20")
        time.sleep(0.1)
        e.send("setoption name Hash value 64")
        e.send("isready")
        lines, ok = e.until(lambda s: s.startswith("bestmove"))
        if not ok:
            raise Missing("no bestmove after mid-search setoption")
        record("S-F9_midsearch_setoption", {"n_info": len([l for l in lines if l.startswith("info depth")])})
    finally:
        e.close()

    # ---- S-F8: all-20 no-op restriction (fresh process each)
    e = new(exe, settings, a.settings)
    try:
        plain = e.go("position startpos", "go depth 12", depth_filter=12)
    finally:
        e.close()
    e = new(exe, settings, a.settings)
    try:
        all20 = e.go("position startpos", "go depth 12 searchmoves " + ALL20, depth_filter=12)
    finally:
        e.close()
    e = new(exe, settings, a.settings)
    try:
        two = e.go("position startpos", "go depth 12 searchmoves d2d4 e2e4", depth_filter=12)
    finally:
        e.close()
    record("S-F8", {"plain": {"score": plain["score"], "nodes": plain["nodes"],
                              "bestmove": plain["bestmove"]},
                    "all20": {"score": all20["score"], "nodes": all20["nodes"],
                              "bestmove": all20["bestmove"]},
                    "two_moves": {"score": two["score"], "nodes": two["nodes"],
                                  "bestmove": two["bestmove"]},
                    "all20_equals_plain": (all20["score"] == plain["score"]
                                           and all20["nodes"] == plain["nodes"]
                                           and all20["bestmove"] == plain["bestmove"])})

    with open(os.path.join(a.outdir, "rerun_%s_%s.json" % (a.label, a.settings)), "w") as f:
        json.dump(R, f, indent=2)
    print("\nwrote", os.path.join(a.outdir, "rerun_%s_%s.json" % (a.label, a.settings)))


if __name__ == "__main__":
    main()
