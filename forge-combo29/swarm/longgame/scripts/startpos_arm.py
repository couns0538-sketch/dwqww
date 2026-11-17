#!/usr/bin/env python3
"""Literal `position startpos moves <prefix>` arm, from engine self-play.

Why this arm exists. Every one of the 5,689 games in the repo's PGN files carries
[SetUp "1"] + [FEN ...], so no game in the repo begins at startpos and the brief's literal
`position startpos moves <prefix>` form cannot be exercised on them. This arm generates
self-play games FROM startpos, then replays each move by move in one process -- the same
composite, with the brief's exact command form.

It also produces the population the repo corpus cannot: games that reach a MID-GAME threefold
while the replay is still asking for moves, which is where a bail in-process but not fresh
would show up.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from replay import run_search

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
OPENINGS = [  # 10 short opening prefixes, so games are not all one line
    "", "e2e4", "d2d4", "c2c4", "g1f3", "e2e4 e7e5", "d2d4 d7d5", "c2c4 e7e5",
    "e2e4 c7c5", "d2d4 g8f6",
]
NGAMES, MAXPLIES, GEN_GO = 20, 200, "go depth 6"


def selfplay(n, maxplies, go):
    """Play engine vs itself from each opening, one process per game."""
    games = []
    for i in range(n):
        op = OPENINGS[i % len(OPENINGS)]
        moves = op.split()
        eng = Engine(ENG); eng.uci(); eng.sync()
        for _ in range(maxplies):
            pos = "position startpos moves " + " ".join(moves) if moves else "position startpos"
            r = run_search(eng, pos, go)
            if r["bm"] in (None, "0000"):
                break
            moves.append(r["bm"])
            if r["bail"]:
                break
        eng.quit()
        games.append({"id": f"sp{i:02d}", "opening": op, "moves": moves})
    return games


def main():
    cache = "evidence/selfplay_games.json"
    if os.path.exists(cache):
        games = json.load(open(cache, encoding="utf-8"))
        print(f"loaded {len(games)} self-play games from cache")
    else:
        games = selfplay(NGAMES, MAXPLIES, GEN_GO)
        json.dump(games, open(cache, "w", encoding="utf-8"), indent=0)
        print(f"generated {len(games)} self-play games")

    total = sum(len(g["moves"]) for g in games)
    print(f"self-play plies: {total}, per game mean {total/len(games):.0f}")

    rows = []
    eng = Engine(ENG); eng.uci(); eng.sync()
    glb = 0
    for g in games:
        for k in range(1, len(g["moves"]) + 1):
            pos = "position startpos moves " + " ".join(g["moves"][:k])
            r = run_search(eng, pos)
            glb += 1
            r.update(game=g["id"], ply=k, glb=glb)
            rows.append(r)
    eng.quit()
    with open("evidence/startpos_session.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("startpos session plies:", glb)

    # fresh arm on the same positions
    frows = []
    for g in games:
        for k in range(1, len(g["moves"]) + 1):
            e = Engine(ENG); e.uci(); e.sync()
            pos = "position startpos moves " + " ".join(g["moves"][:k])
            r = run_search(e, pos); e.quit()
            r.update(game=g["id"], ply=k)
            frows.append(r)
    with open("evidence/startpos_fresh.jsonl", "w", encoding="utf-8") as f:
        for r in frows:
            f.write(json.dumps(r) + "\n")
    print("startpos fresh plies:", len(frows))

    S = {(r["game"], r["ply"]): r for r in rows}
    F = {(r["game"], r["ply"]): r for r in frows}
    ks = sorted(F)
    bm = sum(1 for k in ks if S[k]["bm"] != F[k]["bm"])
    bail_s = {k for k in ks if S[k]["bail"] and S[k]["bm"] != "0000"}
    bail_f = {k for k in ks if F[k]["bail"] and F[k]["bm"] != "0000"}
    print(f"\nbm divergence: {bm}/{len(ks)} ({100*bm/len(ks):.1f}%)")
    print(f"bails session {len(bail_s)}  fresh {len(bail_f)}  "
          f"bail-set disagree {len(bail_s ^ bail_f)}  (in-process only {len(bail_s-bail_f)}, "
          f"fresh only {len(bail_f-bail_s)})")
    print("bail games session:", len({k[0] for k in bail_s}), "of", len(games))
    json.dump({"plies": len(ks), "bm_diff": bm,
               "bails_session": sorted(bail_s), "bails_fresh": sorted(bail_f)},
              open("evidence/startpos_summary.json", "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    main()
