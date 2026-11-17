"""The realistic scenario: a drawn root that arises in an actual game.

The brief's worry is "a cost paid on every search for a condition that fires rarely".
Rare is the operative word: the scan is gated on a draw predicate, so it fires only when
the fifty-move counter, a threefold, or dead material is already on the board.

This script measures:
  * how often a drawn root occurs in random legal games (the base rate);
  * what the drawn roots look like when they do (mobility, which predicate);
  * the total scan cost over a whole game's worth of searches, so the reader can compare
    it with the search cost of that same game.

The base rate is the honest answer to "fires rarely": if drawn roots are ~1 in N searches,
the repair's cost is that share of ~10 us.
"""
import json
import random
import statistics
import sys

import chess

sys.path.insert(0, "/home/ubuntu/job")
from ucih import Engine  # noqa: E402

SEED = 63002
GAMES = 60


def play_random_game(rng, max_plies=250):
    """One random legal game. Returns the list of positions where the ENGINE would
    adjudicate drawn (its three predicates), with mobility."""
    b = chess.Board()
    drawn = []
    plies = 0
    while plies < max_plies and not b.is_game_over():
        # engine predicate as read from src/search.cpp:2252
        hm = b.halfmove_clock
        if hm >= 100 or b.is_repetition(3) or b.is_insufficient_material():
            drawn.append({"fen": b.fen(), "legal": b.legal_moves.count(),
                          "halfmove": hm,
                          "pred": ("halfmove100" if hm >= 100 else
                                   "repetition" if b.is_repetition(3) else "insufficient")})
        moves = list(b.legal_moves)
        b.push(rng.choice(moves))
        plies += 1
    return drawn, plies


def main():
    rng = random.Random(SEED)
    all_drawn = []
    total_plies = 0
    games_with_draw = 0
    for g in range(GAMES):
        d, plies = play_random_game(rng)
        total_plies += plies
        if d:
            games_with_draw += 1
            all_drawn.extend(d)

    print("== base rate of a drawn root in random legal play ==")
    print("games played            : %d" % GAMES)
    print("total plies             : %d" % total_plies)
    print("games with a drawn root : %d of %d" % (games_with_draw, GAMES))
    print("drawn-root searches     : %d of %d plies = %.3f %%" %
          (len(all_drawn), total_plies, 100.0 * len(all_drawn) / total_plies if total_plies else 0))

    if all_drawn:
        legals = [d["legal"] for d in all_drawn]
        print("mobility at drawn roots : min=%d median=%d max=%d" %
              (min(legals), statistics.median(legals), max(legals)))
        by = {}
        for d in all_drawn:
            by[d["pred"]] = by.get(d["pred"], 0) + 1
        print("by predicate            : %r" % (by,))

    # measure the scan on a sample of the drawn roots that actually occurred
    scan_ns = []
    for d in all_drawn[:40]:
        import os
        import re
        import subprocess
        env = dict(os.environ, SCANPROBE="1")
        script = ("uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo depth 8\nquit\n"
                  % d["fen"])
        p = subprocess.run(["/home/ubuntu/b_probe/forge"], input=script, capture_output=True,
                           text=True, env=env, timeout=300)
        for line in p.stderr.splitlines():
            if line.startswith("SCANPROBE"):
                kv = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", line)}
                if kv.get("roots", 0) >= 1 and kv.get("scanned_roots", 0) > 0:
                    scan_ns.append(kv.get("scan_ns", 0))

    print("\n== scan cost on drawn roots that ACTUALLY occurred ==")
    if scan_ns:
        print("measured %d of %d" % (len(scan_ns), len(all_drawn)))
        print("scan_ns: median=%d max=%d" % (statistics.median(scan_ns), max(scan_ns)))
    else:
        print("none measured (no drawn roots occurred in the sample)")

    out = {"games": GAMES, "plies": total_plies, "drawn_roots": len(all_drawn),
           "games_with_draw": games_with_draw,
           "drawn": all_drawn[:200], "scan_ns": scan_ns}
    with open("/home/ubuntu/job/out/drawn_base_rate.json", "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
