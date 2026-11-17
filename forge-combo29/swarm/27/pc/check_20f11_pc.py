#!/usr/bin/env python3
"""check_20f11_pc.py <exe> <outdir> [--settings PC20|S14|none]

Checks seat 20's S-F11 on the PC BUILD (no other seat has run it there). Their finding:
  the engine answers with its FIRST LEGAL MOVE and zero searched nodes when
    (a) the budget is `go nodes 0` or `go nodes 1`,
    (b) a `stop` arrives with 0 ms between it and `go infinite`  (20/20 on 3 positions),
    (c) `quit` arrives during a search,
  and NOT at stop delays of 1 ms or more (0/120), and not in a clock game.

I test all three on the PC build under PC20, plus the delay control. Threads 1 always.
`OwnBook false` is in PC20, which matters: with the book on, startpos replies are book moves with
`info string book move` and no `info depth` line, which LOOKS like the unsearched fallback (their S-F12).

Every go is followed by reading until bestmove; nothing closes stdin mid-search except the cases that
are explicitly ABOUT closing it (c).
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
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]
# The third field is the FIRST LEGAL MOVE IN GENERATION ORDER, taken from `go perft 1` on the PC build
# (it lists moves in generation order): startpos -> a2a3, kiwipete -> a2a3, this endgame -> e2e3.
# My first version guessed e2e4 / e1g1 / b5b6 and therefore reported first_legal=False everywhere --
# a harness error, corrected here by measuring the order rather than assuming it.
POSITIONS = [
    ("startpos", "position startpos", "a2a3"),
    ("kiwipete", "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "a2a3"),
    ("endgame", "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "e2e3"),
]


class Engine:
    def __init__(self, exe, settings):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.s("uci")
        lines, _ = self.until(lambda s: s.strip() == "uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        for item in settings:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise RuntimeError("option %r not advertised" % name)
            self.s("setoption name %s value %s" % (name, val))
        self.s("ucinewgame")
        self.s("isready")
        self.until(lambda s: s.strip() == "readyok")

    def s(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()

    def until(self, pred, timeout=120):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < timeout:
            ln = self.p.stdout.readline()
            if not ln:
                break
            x = ln.rstrip("\n"); out.append(x)
            if pred(x):
                return out, True
        return out, False

    def close(self):
        try:
            self.s("quit"); self.p.wait(timeout=15)
        except Exception:
            self.p.kill()


def summarise(lines):
    infos = [l for l in lines if l.startswith("info depth")]
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    # GUARD (S-W1): zero info lines is not a search result. summarise() is called for control rows
    # where 0 info lines IS the expected answer (the emergency path), so it reports rather than raises;
    # every CALLER that treats the row as a measurement checks zero_info first.
    last = infos[-1] if infos else ""
    n = re.search(r"nodes (\d+)", last)
    pv = re.search(r"\bpv\b", last)
    return {"info_lines": len(infos), "bestmove": bm,
            "nodes": int(n.group(1)) if n else None,
            "empty_pv": (last != "" and pv is None) or last == "",
            "last": last}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1"],
                "S14": ["Hash 16", "Threads 1"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    R = {"exe": exe, "settings": a.settings, "threads": 1,
         "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "a_nodes": {}, "b_zero_delay_stop": {}, "b_one_ms_stop": {}, "c_quit_midsearch": {}}

    # (a) go nodes 0 / 1
    for name, pos, first in POSITIONS:
        for n in (0, 1):
            e = Engine(exe, settings)
            try:
                e.s(pos); e.s("isready"); e.until(lambda s: s.strip() == "readyok")
                e.s("go nodes %d" % n)
                lines, ok = e.until(lambda s: s.startswith("bestmove"))
                r = summarise(lines)
                r["is_first_legal"] = (r["bestmove"] == first)
                R["a_nodes"]["%s_nodes%d" % (name, n)] = r
            finally:
                e.close()

    # (b) stop with 0 ms and with 1 ms
    for name, pos, _ in POSITIONS:
        for delay_ms, bucket in ((0, "b_zero_delay_stop"), (1, "b_one_ms_stop")):
            e = Engine(exe, settings)
            try:
                e.s(pos); e.s("isready"); e.until(lambda s: s.strip() == "readyok")
                e.s("go infinite")
                if delay_ms:
                    time.sleep(delay_ms / 1000.0)
                e.s("stop")
                lines, ok = e.until(lambda s: s.startswith("bestmove"), timeout=30)
                R[bucket][name] = summarise(lines) if ok else {"bestmove": None, "no_answer": True}
            finally:
                e.close()

    # (c) quit during a search: the bestmove arrives, but the search is cut at once
    for name, pos, _ in POSITIONS:
        e = Engine(exe, settings)
        try:
            e.s(pos); e.s("isready"); e.until(lambda s: s.strip() == "readyok")
            e.s("go depth 30")
            time.sleep(0.05)
            e.s("quit")
            lines, ok = e.until(lambda s: s.startswith("bestmove"), timeout=20)
            R["c_quit_midsearch"][name] = summarise(lines) if ok else {"bestmove": None, "no_answer": True}
        finally:
            e.close()

    with open(os.path.join(a.outdir, "check_20f11_%s.json" % a.settings), "w") as f:
        json.dump(R, f, indent=2)

    def row(d):
        return "info %-2s nodes %-7s bm %-5s" % (d.get("info_lines"), d.get("nodes"), d.get("bestmove"))
    print("exe", exe, a.settings, "threads 1")
    print("\n(a) go nodes 0 / 1")
    for k, v in R["a_nodes"].items():
        print("  %-18s %s first_legal=%s" % (k, row(v), v.get("is_first_legal")))
    print("\n(b) stop at 0 ms")
    for k, v in R["b_zero_delay_stop"].items():
        print("  %-10s %s" % (k, row(v)))
    print("\n(b) CONTROL stop at 1 ms")
    for k, v in R["b_one_ms_stop"].items():
        print("  %-10s %s" % (k, row(v)))
    print("\n(c) quit during a depth-30 search")
    for k, v in R["c_quit_midsearch"].items():
        print("  %-10s %s" % (k, row(v)))


if __name__ == "__main__":
    main()
