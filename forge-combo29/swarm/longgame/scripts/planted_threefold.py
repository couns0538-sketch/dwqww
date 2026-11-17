#!/usr/bin/env python3
"""Plant a MID-GAME threefold inside a real game and ask about the position after it.

The corpus cannot test this: every drawn game ends AT its threefold, so the replay never
searches a position reached three times (measured: max occurrence count at a searched ply
was exactly 3 and only on final plies). To reach the condition we splice a legal shuttle
onto a real game prefix, ending with the repeated position still in the history.

Two arms per fixture, five states each:
  session  one process, fixtures run back to back, no reset
  fresh    one process per query
States: nothing / ucinewgame / Clear Hash / setoption Hash same-value.

Checks per query: does it bail, is the move the generator head, and does the session arm
agree with the fresh arm.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from replay import run_search, perft_head
from checks import require

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
corpus = {g["id"]: g for g in json.load(open("evidence/games.json", encoding="utf-8"))["games"]}

# A legal 8-ply shuttle from the start position that returns to the start position 3 times
# in total: start, after 4 plies, after 8 plies.
SHUTTLE = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]


def find_cycle(board, limit=400):
    """Find a 4-ply legal cycle returning to `board`'s position, from the real position.

    The corpus games all start from a [FEN] header, so a startpos shuttle cannot be
    spliced onto them. Instead we search the game's own position for a pair of moves by
    each side whose reverse pair restores it. Deterministic: first cycle in move order.
    """
    key0 = board._transposition_key()
    n = 0
    for a in board.legal_moves:
        b1 = board.copy(); b1.push(a)
        for b in b1.legal_moves:
            b2 = b1.copy(); b2.push(b)
            for c in b2.legal_moves:
                b3 = b2.copy(); b3.push(c)
                for d in b3.legal_moves:
                    b4 = b3.copy(); b4.push(d)
                    if b4._transposition_key() == key0:
                        return [a.uci(), b.uci(), c.uci(), d.uci()]
                    n += 1
                    if n > limit:
                        return None
    return None


def fixtures():
    """Real game prefixes, each extended with a legal 4-cycle played three times.

    The final position is therefore the third occurrence of the position after the
    prefix, and it is a position the engine is actually asked about -- which the corpus
    itself never does.
    """
    import chess
    out = []
    for gid in ["g000", "g004", "g010", "g030", "g050", "g070", "g100", "g150"]:
        g = corpus[gid]
        for k in (10, 24, 40):
            if k > len(g["moves"]):
                continue
            board = chess.Board(g["start_fen"])
            pre = []
            for mv in g["moves"][:k]:
                board.push(chess.Move.from_uci(mv))
                pre.append(mv)
            cyc = find_cycle(board)
            if cyc is None:
                continue
            out.append({"id": f"{gid}_p{k}", "prefix": pre + cyc * 3, "cycle": cyc,
                        "start_fen": g["start_fen"], "occ": 3})
            # CONTROL: the same fixture with the cycle played once, so the position the
            # engine is asked about has occurred once. If this arm bailed too, the
            # fixtures would not be testing the repetition rule at all.
            out.append({"id": f"{gid}_p{k}_x1", "prefix": pre + cyc, "cycle": cyc,
                        "start_fen": g["start_fen"], "occ": 1})
    return out


def main():
    fx = fixtures()
    require(fx, "no fixture found a legal cycle")
    for f in fx:
        f["pos"] = f"position fen {f['start_fen']} moves " + " ".join(f["prefix"])
    print(f"fixtures: {len(fx)}")

    # sanity: the last position must occur exactly 3x in the sent history
    import chess
    for f in fx:
        b = chess.Board(f["start_fen"])
        counts = {b._transposition_key(): 1}
        for mv in f["prefix"]:
            b.push(chess.Move.from_uci(mv))
            counts[b._transposition_key()] = counts.get(b._transposition_key(), 0) + 1
        f["occ"] = counts[b._transposition_key()]
        # 4 is fine and is itself informative: the prefix may already have visited the
        # position once. Record the real count rather than forcing 3.
        f["occ"] = f["occ"]
        # and it must not already be terminal: a checkmate root is not a bail
        require(b.legal_moves.count() > 0, f"{f['id']} has no legal move")
        require(not b.is_insufficient_material(),
                f"{f['id']} is insufficient material, so a bail there is not the repetition arm")

    results = {"session": [], "fresh": []}
    for arm in ("session", "fresh"):
        if arm == "session":
            eng = Engine(ENG); eng.uci(); eng.sync()
        for f in fx:
            for state in ("none", "ucinewgame", "clearhash", "hashresend"):
                if arm == "fresh":
                    eng = Engine(ENG); eng.uci(); eng.sync()
                if state == "ucinewgame":
                    eng.send("ucinewgame"); eng.sync()
                elif state == "clearhash":
                    eng.send("setoption name Clear Hash")
                elif state == "hashresend":
                    eng.send("setoption name Hash value 32")
                r = run_search(eng, f["pos"])
                head = perft_head(eng, f["pos"])
                r.update(fixture=f["id"], state=state, arm=arm, occ=f["occ"], head=head,
                         is_head=(r["bm"] == head))
                results[arm].append(r)
                if arm == "fresh":
                    eng.quit()
        if arm == "session":
            eng.quit()

    json.dump(results, open("evidence/planted_threefold.json", "w", encoding="utf-8"), indent=0)

    print(f"\n{'fixture':12s} {'state':12s} {'session':>22s} {'fresh':>22s}  agree")
    for i, f in enumerate(fx):
        for j, state in enumerate(("none", "ucinewgame", "clearhash", "hashresend")):
            s = results["session"][i * 4 + j]
            fr = results["fresh"][i * 4 + j]
            def fmt(r):
                return f"{r['bm']} n={r['nodes']} {r['score']}".ljust(22)
            print(f"{f['id']:12s} {state:12s} {fmt(s)} {fmt(fr)}  "
                  f"{'YES' if s['bm'] == fr['bm'] and s['nodes'] == fr['nodes'] else 'NO'}"
                  f"  bail_s={s['bail']} bail_f={fr['bail']} head={s['is_head']}")

    print(f"\nsession arm: {sum(1 for r in results['session'] if r['bail'])}/{len(results['session'])} bailed")
    print(f"fresh arm:   {sum(1 for r in results['fresh'] if r['bail'])}/{len(results['fresh'])} bailed")
    print("all bails play the generator head:",
          all(r["is_head"] for r in results["session"] + results["fresh"] if r["bail"]))


if __name__ == "__main__":
    main()
