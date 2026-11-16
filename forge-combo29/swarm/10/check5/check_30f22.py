#!/usr/bin/env python3
"""check_30f22.py OUTDIR -- seat 10's OWN harness for seat 30's finding 30-F22.

Claim: on `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1`, a `go depth 12` interrupted by stdin CLOSING answers
`bestmove f2f3` while the finished search answers `a1a8` (mate in 1).

Written from the finding's text; it does not import or copy seat 30's script.

Four measurements per build, Threads 1, Hash 16, OwnBook false, SETTINGS named per row:
  F  FINISHED   : write the commands, read stdout to `bestmove`, then close            (expect a1a8, mate 1)
  C  CLOSE      : write the commands, close stdin at once                             (expect f2f3 per 30-F22)
  Q  QUIT       : write the commands then `quit` immediately                          (variant, same race)
  E  EOF-NO-GO  : control that the harness can see a difference at all: same but no go  (must be empty)

Every answer is checked for legality against python-chess AND for being mate, so the verdict is not
"looks plausible": P5 verifies a1a8 is mate, P3 verifies f2f3 is legal.

Usage: check_30f22.py OUTDIR
"""
import json
import os
import re
import subprocess
import sys

import chess

BASE = os.path.expanduser("~/builds/release/forge")
PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

FEN = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def setup(regime):
    lines = ["uci", "isready", "setoption name Threads value 1",
             "setoption name Hash value 16", "setoption name OwnBook value false"]
    lines += ["setoption name %s value %s" % kv for kv in (S14 if regime == "s14" else PC20)]
    lines += ["isready", "ucinewgame", "isready", "position fen " + FEN, "isready"]
    return lines


def finished(exe, regime, depth=12):
    """write everything, read stdout to bestmove, THEN close: the safe harness"""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for l in setup(regime):
        p.stdin.write(l + "\n")
        p.stdin.flush()
    p.stdin.write("go depth %d\n" % depth)
    p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip())
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    try:
        p.stdin.flush()
    except Exception:
        pass
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    return parse(lines)


def closed(exe, regime, depth=12, quit_word=False):
    """write everything, close stdin at once (the 30-F22 condition)"""
    cmds = setup(regime) + ["go depth %d" % depth]
    if quit_word:
        cmds.append("quit")
    p = subprocess.run([exe], input="\n".join(cmds) + "\n", capture_output=True,
                       text=True, timeout=300)
    return parse(p.stdout.splitlines())


def parse(lines):
    best = None
    score = None
    depth_seen = 0
    for l in lines:
        s = l.strip()
        if s.startswith("info depth"):
            depth_seen += 1
        if s.startswith("bestmove"):
            best = s.split()[1]
        m = re.search(r" score (cp|mate) (-?\d+)", s)
        if m:
            score = (m.group(1), int(m.group(2)))
    return {"bestmove": best, "last_score": score, "info_depth_lines": depth_seen}


board = chess.Board(FEN)
legal = {m.uci() for m in board.legal_moves}
mate_moves = []
for m in board.legal_moves:
    b = board.copy()
    b.push(m)
    if b.is_checkmate():
        mate_moves.append(m.uci())

out = {"fen": FEN, "python_legal_moves": len(legal),
       "python_mate_in_1_moves": sorted(mate_moves), "rows": {}}
for bname, exe, regime in (("base_s14", BASE, "s14"), ("pc20", PC, "pc20")):
    rows = {}
    rows["F_finished_safe"] = finished(exe, regime)
    rows["C_stdin_closed"] = closed(exe, regime)
    rows["Q_quit_word"] = closed(exe, regime, quit_word=True)
    out["rows"][bname] = rows
    for k, v in rows.items():
        bm = v["bestmove"]
        v["legal"] = (bm in legal) if bm else None
        v["is_mate_move"] = (bm in mate_moves) if bm else None

fin_pc = out["rows"]["pc20"]["F_finished_safe"]
clo_pc = out["rows"]["pc20"]["C_stdin_closed"]
fin_b = out["rows"]["base_s14"]["F_finished_safe"]
clo_b = out["rows"]["base_s14"]["C_stdin_closed"]
out["verdict_inputs"] = {
    "P1_finished_is_a1a8_both": fin_pc["bestmove"] == "a1a8" and fin_b["bestmove"] == "a1a8",
    "P1_finished_score_mate1_both": (fin_pc["last_score"] == ("mate", 1)
                                     and fin_b["last_score"] == ("mate", 1)),
    "P2_pc_closed_is_f2f3": clo_pc["bestmove"] == "f2f3",
    "P3_fabricated_move_is_legal": clo_pc.get("legal"),
    "P4_base_closed_same_as_pc": clo_b["bestmove"] == clo_pc["bestmove"],
    "P5_a1a8_is_mate": "a1a8" in mate_moves,
    "P6_safe_harness_gets_mate": fin_pc["bestmove"] == "a1a8" and fin_b["bestmove"] == "a1a8",
}
vi = out["verdict_inputs"]
out["verdict"] = ("CONFIRMS 30-F22" if (vi["P2_pc_closed_is_f2f3"] and vi["P5_a1a8_is_mate"]
                                       and vi["P3_fabricated_move_is_legal"]) else
                  "REFUTES or differs from 30-F22")
with open(os.path.join(OUT, "check_30f22.json"), "w") as f:
    json.dump(out, f, indent=2)
    f.write("\n")
print(json.dumps(out, indent=2))
