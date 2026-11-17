#!/usr/bin/env python3
"""Does the score of a WON position collapse as the halfmove clock rises?

Mechanism candidate: `rule50_damped_static` scales the static score toward 0 as
halfmove_clock approaches 100 (search.cpp:1426, 1467, 1569, 1656 call it). If that
damping reaches the ROOT score, a won KQK at clock 85 looks like a draw, and the
engine has no gradient left to make progress -- which is what shuffling looks like.

This is a direct test: same board, same everything, only the clock differs. If the
score is flat, the hypothesis is dead and the shuffling has another cause.
"""
import json
import sys

sys.path.insert(0, "/tmp/fx")
import chess
from uci import Engine, parse_info

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/build/forge"

BOARDS = {
    # a clean KQK mate-in-a-few: white to move
    "kqk_easy": "8/8/8/8/8/2k5/8/KQ6 w - - {hm} 1",
    # the shuffle position observed in play (queen a2, black king c1)
    "kqk_shuffle": "3K4/8/8/8/8/8/Q7/2k5 w - - {hm} 1",
    "krk_easy": "8/8/8/8/8/2k5/8/KR6 w - - {hm} 1",
}

e = Engine(EXE)
rows = []
for name, tmpl in BOARDS.items():
    for hm in (0, 20, 40, 60, 70, 80, 85, 90, 95, 99):
        fen = tmpl.format(hm=hm)
        e.set_position("position fen " + fen)
        ev = e.eval_line()
        r = e.search("go depth 12")
        pi = parse_info(r["last"]) if r["last"] else {}
        row = {"board": name, "hm": hm, "fen": fen, "bestmove": r["bestmove"],
               "score": pi.get("score"), "score_kind": pi.get("score_kind"),
               "depth": pi.get("depth"), "nodes": pi.get("nodes"),
               "pv": " ".join(pi.get("pv", [])[:6]), "eval_line": ev}
        rows.append(row)
        print(f"{name:12s} hm={hm:3d} eval[{ev.split('eval ')[-1] if ev else '-'}] "
              f"search score={pi.get('score_kind')} {pi.get('score')} "
              f"nodes={pi.get('nodes')} bm={r['bestmove']} pv={' '.join(pi.get('pv',[])[:4])}",
              flush=True)
e.quit()
json.dump(rows, open("/tmp/fx/rule50_probe.json", "w"), indent=1)
