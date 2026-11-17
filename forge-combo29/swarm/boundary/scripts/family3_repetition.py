"""Family 3: one ply from a forced repetition.

Two sub-families, both judged on the SCORE.

  A. DRAWN ROOT. The move list we send makes the searched position occur three
     times. §2 says the engine then returns `cp 0`, 0 nodes, empty pv.

  B. MUST SEARCH. Same shape but only two occurrences, so the root is not
     drawn and the engine must not return the bail shape.

CRITICAL, and the first version of this script failed here: the move list is
VERIFIED legal move by move on a python-chess board before it is sent, and the
engine's reply is checked for `info string illegal move`. The engine TRUNCATES
the move list at the first illegal token and keeps the prefix, so a single bad
token silently turns a threefold fixture into an arbitrary different position
and the row then measures the wrong board. My first attempt sent `a1a2` from a
position where White was in check (only king moves were legal) and recorded
`cp -505` as a "wrong score" -- the engine was right and the fixture was a lie.
"""
import json
import sys
import chess

from forge_drv import Forge, RefusedFen

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family3_repetition.json"

# Kings on e1/e8 with rooks on a1/a8: both sides have a free rook shuffle and
# neither starts in check.
BASE = "r3k3/8/8/8/8/8/8/R3K3 w - - 0 40"


def _key(b):
    return (b.board_fen(), b.turn, b.castling_rights, b.ep_square)


def build_shuffle(pairs, base=BASE):
    """Replay `pairs` of (white_move, black_move) shuffles on a real board.

    Every token is asserted legal as it is played, so an illegal fixture can
    never be constructed.
    """
    b = chess.Board(base)
    moves = []
    for wm, bm in pairs:
        for tok in (wm, bm):
            mv = chess.Move.from_uci(tok)
            if mv not in b.legal_moves:
                raise ValueError(
                    f"illegal move {tok} in fixture build; legal were "
                    f"{[m.uci() for m in b.legal_moves]}")
            b.push(mv)
            moves.append(tok)
    return moves, b


def occurrences_of_start(moves, base=BASE):
    """How many times the START position recurs along the move list."""
    b = chess.Board(base)
    keys = [_key(b)]
    for tok in moves:
        b.push(chess.Move.from_uci(tok))
        keys.append(_key(b))
    return sum(1 for k in keys if k == keys[0]), b


# White shuffles a1-a2-a1; Black shuffles a8-a7-a8. Four plies restore both.
FWD = ("a1a2", "a8a7")
BACK = ("a2a1", "a7a8")


def cases():
    out = []
    moves, _ = build_shuffle([FWD, BACK])
    out.append(("root_twice_CONTROL", moves, "MUST_SEARCH"))

    moves, _ = build_shuffle([FWD, BACK, FWD, BACK])
    out.append(("root_threefold", moves, "DRAWN_ROOT"))

    moves, _ = build_shuffle([FWD, BACK, FWD, BACK, FWD, BACK])
    out.append(("root_fourfold", moves, "DRAWN_ROOT"))

    alt_fwd = ("a1a3", "a8a6")
    alt_back = ("a3a1", "a6a8")
    moves, _ = build_shuffle([alt_fwd, alt_back, alt_fwd, alt_back])
    out.append(("root_threefold_alt", moves, "DRAWN_ROOT"))

    return out


def main():
    rows = []
    with Forge(EXE) as eng:
        for label, moves, expectation in cases():
            occ, final = occurrences_of_start(moves)
            try:
                rec = eng.search(BASE, "go depth 12", moves=moves)
            except RefusedFen as e:
                rows.append({"label": label, "moves": moves, "refused": True,
                             "error": str(e)})
                continue
            truncated = [s for s in rec.info_strings() if "illegal move" in s]
            sc, nodes, pv = rec.score(), rec.nodes(), rec.pv()
            if truncated:
                verdict, ok = "FIXTURE_REJECTED", False
                note = f"engine truncated the move list: {truncated}"
            elif expectation == "DRAWN_ROOT":
                if sc == ("cp", 0) and nodes == 0 and not pv:
                    verdict, ok = "BAIL_AS_DOCUMENTED", True
                elif sc == ("cp", 0):
                    verdict, ok = "DRAW_SCORE_SEARCHED", True
                else:
                    verdict, ok = "WRONG_SCORE", False
                note = f"score {sc}, nodes {nodes}, pvlen {len(pv)}"
            else:
                ok = nodes > 0
                verdict = "SEARCHED" if ok else "NO_SEARCH"
                note = f"{nodes} nodes"
            rows.append({"label": label, "base": BASE, "moves": moves,
                         "expectation": expectation,
                         "py_start_occurrences": occ,
                         "bestmove": rec.bestmove, "score": sc,
                         "nodes": nodes, "depth": rec.depth(), "pv": pv,
                         "n_infos": len(rec.infos),
                         "info_strings": rec.info_strings(),
                         "truncated": truncated,
                         "verdict": verdict, "ok": ok, "note": note})

    with open(OUT, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"{'label':22} {'occ':>4} {'score':12} {'nodes':>7} {'verdict':22} {'ok':>5}  note")
    for r in rows:
        print(f"{r['label']:22} {str(r.get('py_start_occurrences')):>4} "
              f"{str(r.get('score')):12} {str(r.get('nodes')):>7} "
              f"{str(r.get('verdict')):22} {str(r.get('ok')):>5}  {r.get('note','')}")
    print(f"\n{sum(1 for r in rows if r.get('ok'))}/{len(rows)} as expected")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
