#!/usr/bin/env python3
"""seat 17: on the match node path, can the engine lose a game?

Checks, at the three match budgets plus the self-play tier, on real positions:
  1. every returned move is LEGAL (python-chess)
  2. no `bestmove 0000` on a position that has legal moves
  3. no mate score reported that the PV does not deliver, and no mate score on a non-mate
  4. any position where the engine claims `mate N` is verified: play the PV and check for mate

Threads 1, Hash 16, PC20, PC r15, fresh process per line, read to bestmove.

usage: node_path_health.py <exe> <epd> <outdir> [positions]
"""
import json
import os
import subprocess
import sys

import chess

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA
GO_LINES = ["go nodes 2000", "go nodes 20000", "go nodes 50000", "go nodes 250000", "go softnodes 2000"]


def run(exe, fen, go, timeout=240):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        while True:
            reply = proc.stdout.readline()
            if reply == "":
                return None
            out.append(reply.rstrip("\n"))
            if pred(reply):
                return reply

    try:
        send("uci")
        read_until(lambda l: l.strip() == "uciok")
        for name, value in PC20:
            send("setoption name %s value %s" % (name, value))
            send("isready")
            read_until(lambda l: l.strip() == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda l: l.strip() == "readyok")
        send(go)
        read_until(lambda l: l.startswith("bestmove"))
    finally:
        try:
            send("quit")
            proc.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    return "\n".join(out) + "\n"


def check(fen, text):
    lines = text.splitlines()
    depth_lines = [l for l in lines if l.startswith("info depth")]
    best = [l for l in lines if l.startswith("bestmove")]
    result = {"legal": None, "is_0000": None, "mate_claim": None, "pv_delivers_mate": None,
              "depth_reached": None}
    board = chess.Board(fen)
    if best:
        move_txt = best[-1].split()[1]
        result["is_0000"] = move_txt == "0000"
        result["legal"] = move_txt in [m.uci() for m in board.legal_moves] if move_txt != "0000" else False
    if depth_lines:
        last = depth_lines[-1]
        try:
            result["depth_reached"] = int(last.split(" depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        if " score mate " in last:
            result["mate_claim"] = int(last.split(" score mate ")[1].split()[0])
            pv = last.split(" pv ")[1].split() if " pv " in last else []
            # play the PV and see whether it ends in mate
            probe = chess.Board(fen)
            played = 0
            for token in pv:
                try:
                    probe.push_uci(token)
                except ValueError:
                    break
                played += 1
            result["pv_delivers_mate"] = probe.is_checkmate() if played == len(pv) and pv else None
            result["pv_len"] = len(pv)
            result["pv_ply_checkmated"] = probe.is_checkmate()
    return result


def main():
    exe, epd, outdir = sys.argv[1:4]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    os.makedirs(outdir, exist_ok=True)
    fens = [line.split(";")[0].strip() for line in open(epd) if line.strip()][:count]
    rows = []
    for index, fen in enumerate(fens):
        for go in GO_LINES:
            text = run(exe, fen, go)
            log = os.path.join(outdir, "p%d_%s.log" % (index, go.replace(" ", "_")))
            open(log, "w").write(text)
            verdict = check(fen, text)
            verdict.update({"index": index, "fen": fen, "go": go})
            rows.append(verdict)
        print(json.dumps({"index": index, "done": True}), flush=True)

    illegal = [r for r in rows if r["legal"] is False and not r["is_0000"]]
    zeros = [r for r in rows if r["is_0000"]]
    mate_claims = [r for r in rows if r["mate_claim"] is not None]
    bad_mate = [r for r in mate_claims if r.get("pv_delivers_mate") is False]
    no_legal = [r for r in rows if r["legal"] is None]

    summary = {
        "lines": len(rows),
        "positions": len(fens),
        "illegal_moves": len(illegal),
        "bestmove_0000": len(zeros),
        "mate_claims": len(mate_claims),
        "mate_claims_pv_not_mate": len(bad_mate),
        "not_measured": len(no_legal),
        "depth_range": [min(r["depth_reached"] for r in rows if r["depth_reached"]),
                        max(r["depth_reached"] for r in rows if r["depth_reached"])],
    }
    json.dump({"summary": summary, "rows": rows}, open(os.path.join(outdir, "health.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    for tag, bad in (("ILLEGAL", illegal), ("ZERO", zeros), ("MATE-PV-BAD", bad_mate)):
        if bad:
            print(tag, json.dumps(bad[:5], indent=1))


if __name__ == "__main__":
    main()
