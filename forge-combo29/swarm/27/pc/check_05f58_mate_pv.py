#!/usr/bin/env python3
"""check_05f58_mate_pv.py <exe> <outdir> [--settings PC20]

Independent check of seat 05's S-F58 and S-F59, written from their sentences:

S-F58: position `r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40` at `go nodes 50000` reports
`score mate 11` with an 18-ply PV where 2N-1 = 21 plies are required, reproducibly; at `go nodes 250000`
it reports `mate 7` with a 13-ply PV (13 required, consistent); `go depth 20` agrees.

S-F59: the MOVE is `b3c2` at every budget, so the truncation corrupts the reported score/PV, not the play.

MY CHECK, and the part that must be exactly right: UCI `mate N` on a POSITIVE score means the side to move
mates in N MOVES, which needs 2N-1 PLIES in the PV. A PV shorter than that is "truncated" only in the
specific sense that the reported line does not prove the reported score. I count plies by splitting the pv
field, and I report N and 2N-1 and the ply count separately so the arithmetic is visible rather than asserted.

A CONTROL that makes the counting testable: take a position with a KNOWN short mate (a lone-king mate in 1,
which I verified in S-C13) and confirm the checker reports 1 ply, 2N-1 = 1, consistent. If the checker called
that truncated, the checker would be wrong, not the engine.

Threads 1, Hash 16, OwnBook false, fresh process per row.
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
         "MateAlphaGuard true", "OwnBook false" ]

TARGET = ("r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40", "05-F58 long mate")
CONTROL = ("k7/8/1K6/8/7R/8/8/8 w - - 0 1", "control: verified mate in 1 (S-C13)")
ROWS = ["go softnodes 2000", "go nodes 20000", "go nodes 50000", "go nodes 250000", "go depth 20"]


class Missing(Exception):
    pass


def run(exe, settings, fen, cmd, timeout=600):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(cmd)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove for %r" % cmd)
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth for %r" % cmd)
        last = infos[-1]
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        if not sc:
            raise Missing("no score in %r" % last)
        kind, val = sc.group(1), int(sc.group(2))
        pv = re.search(r"\bpv\b(.*)$", last)
        moves = pv.group(1).split() if pv else []
        d = re.search(r"depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        need = (2 * abs(val) - 1) if kind == "mate" else None
        return {"cmd": cmd, "kind": kind, "value": val, "plies": len(moves),
                "plies_needed": need,
                "truncated": (need is not None and len(moves) < need),
                "excess": (len(moves) > need) if need is not None else None,
                "depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None,
                "bestmove": bm, "pv_first": moves[0] if moves else None, "pv": moves}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--label", default="PCr15")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1", "OwnBook false"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "label": a.label,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "target": [], "control": []}

    # CONTROL FIRST: the checker must call a verified mate-in-1 consistent, or it is broken.
    fen, nm = CONTROL
    print("== CONTROL: %s" % nm)
    for cmd in ("go depth 8", "go nodes 50000"):
        r = run(exe, settings, fen, cmd)
        r["board"] = nm
        out["control"].append(r)
        print("   %-18s %s %d, plies %d, needed %d -> truncated=%s"
              % (cmd, r["kind"], r["value"], r["plies"], r["plies_needed"], r["truncated"]))
    if any(c["truncated"] or c["kind"] != "mate" for c in out["control"]):
        print("ABORT: the CONTROL failed, so this checker cannot be trusted")
        with open(os.path.join(a.outdir, "check_05f58_%s.json" % a.label), "w") as f:
            json.dump(out, f, indent=2)
        raise SystemExit(3)

    fen, nm = TARGET
    print("\n== TARGET: %s" % nm)
    for cmd in ROWS:
        reps = [run(exe, settings, fen, cmd) for _ in range(2)]
        det = len({(r["kind"], r["value"], r["plies"], r["bestmove"], r["nodes"]) for r in reps}) == 1
        r = reps[0]
        r.update({"board": nm, "deterministic": det, "repeat": reps[1]})
        out["target"].append(r)
        # a cp score has no plies_needed, so format it as a string rather than %d
        print("   %-20s %-5s %-5s depth %-3s nodes %-7s plies %-3s need %-3s truncated %-5s bm %-5s det=%s"
              % (cmd, r["kind"], r["value"], r["depth"], r["nodes"], r["plies"],
                 r["plies_needed"] if r["plies_needed"] is not None else "-",
                 r["truncated"], r["bestmove"], det))

    with open(os.path.join(a.outdir, "check_05f58_%s.json" % a.label), "w") as f:
        json.dump(out, f, indent=2)

    t = out["target"]
    trunc = [r for r in t if r["truncated"]]
    moves_set = {r["bestmove"] for r in t}
    print("\n-- verdict --")
    print("control consistent (mate in 1, 1 ply, needed 1): YES")
    print("truncating rows: %s" % [r["cmd"] for r in trunc])
    print("bestmove across all rows: %s -> %s"
          % (sorted(moves_set), "SAME move everywhere" if len(moves_set) == 1 else "moves differ"))


if __name__ == "__main__":
    main()
