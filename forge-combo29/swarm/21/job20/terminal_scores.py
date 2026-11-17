#!/usr/bin/env python3
"""terminal_scores.py OUTDIR

21-F11 across terminal root kinds, on both builds, Threads 1, fresh process per case.

Cases (python-chess verdict in the table, computed, never assumed):
  checkmated       the side to move is checkmated
  stalemate        the side to move has no legal move and is not in check
  kvk              bare kings, legal moves exist, insufficient material
  knvk             king+minor vs king, insufficient material, legal moves exist
  mate_in_1_hm100  a mate available with the fifty-move counter at 100 (the 21-F9 case, for
                   contrast: this is NOT terminal)

For each: `go depth 3` and `go nodes 100`, both read to bestmove (19-F12), Threads 1.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

CASES = {
    "checkmated": "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60",
    "stalemate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 60",
    "kvk": "4k3/8/8/8/8/8/8/4K3 w - - 0 60",
    "knvk": "4k3/8/8/8/8/8/8/4KN2 w - - 0 60",
    "mate_in_1_hm100": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60",
}
SEARCHES = ["go depth 3", "go nodes 100"]


def verdict(fen):
    b = chess.Board(fen)
    return dict(legal=b.legal_moves.count(), check=b.is_check(),
                mate=b.is_checkmate(), stale=b.is_stalemate(),
                insuff=b.is_insufficient_material())


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("base", os.path.expanduser("~/b/asan/forge")),
              ("pc", os.path.expanduser("~/b/pc_asan/forge"))]
    R = {}
    rows = ["| build | case | python | search | bestmove | score line |", "|---|---|---|---|---|---|"]
    for bname, exe in builds:
        for case, fen in CASES.items():
            e = SafeEngine(exe, os.path.join(outdir, "%s_%s_raw.txt" % (bname, case)),
                           hash_mb=16, threads=1)
            ans = e.position("position fen " + fen)
            if any("invalid FEN" in l for l in ans):
                e.close()
                raise AssertionError("%s/%s: FEN refused" % (bname, case))
            v = verdict(fen)
            for search in SEARCHES:
                lines = e.go(search, timeout=120)
                bm = bestmove_of(lines)
                info = last_info(lines) or next(
                    (l for l in reversed(lines) if l.startswith("info")), "")
                if not bm:
                    raise AssertionError("%s/%s/%s: no bestmove" % (bname, case, search))
                R["%s|%s|%s" % (bname, case, search)] = dict(bestmove=bm, info=info, py=v)
                rows.append("| %s | %s | legal=%d mate=%s stale=%s insuff=%s | %s | %s | %s |" % (
                    bname, case, v["legal"], v["mate"], v["stale"], v["insuff"], search, bm,
                    info[-46:].replace("|", "/")))
            e.close()
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    text = "\n".join(rows)

    # the comparison that matters: does the checkmated score differ between builds?
    def score(key):
        m = re.search(r"score (cp|mate) (-?\d+)", R[key]["info"])
        return (m.group(1), int(m.group(2))) if m else None
    same = all(score("base|%s|%s" % (c, s)) == score("pc|%s|%s" % (c, s))
               for c in CASES for s in SEARCHES)
    text += "\n\nterminal-root scores identical between base and PC builds: %s\n" % same
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()