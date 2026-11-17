#!/usr/bin/env python3
"""Prove the position-identity check FIRES before trusting its clean run.

Three planted faults, each of a kind perft must see:
  1. wrong side to move
  2. ep square dropped from a position that has one (the python-chess `Board.fen()` trap)
  3. castling rights dropped
Plus a fourth: a halfmove-clock fault, which perft CANNOT see -- so it is checked with the
bail probe instead, and that is the reason the identity claim is split in two.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from position_identity import perft, force_ep_fen
import chess

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")


def main():
    # A position with an ep square available: 1.e4 c5 2.e5 d5 -> exd6 e.p. is possible
    b = chess.Board()
    for mv in ("e2e4", "c7c5", "e4e5", "d7d5"):
        b.push(chess.Move.from_uci(mv))
    good = force_ep_fen(b)
    assert b.ep_square is not None, "fixture has no ep square"
    # python-chess's own fen() drops the ep square here only when no ep capture is legal;
    # make the point explicitly with a board where it does drop it.
    b2 = chess.Board()
    for mv in ("e2e4", "a7a6"):
        b2.push(chess.Move.from_uci(mv))
    dropped = b2.fen()  # ep square e3 dropped: no black pawn can capture

    e = Engine(ENG); e.uci(); e.sync()
    pos = f"position fen {good}"
    base = perft(e, pos)
    print(f"reference position: {good}")
    print(f"  perft 3 nodes line: {base[-1]}")

    faults = {
        "wrong side to move": good.replace(" w ", " b "),
        "ep square dropped":  good.replace(f" {chess.square_name(b.ep_square)} ", " - "),
    }
    # Castling needs a fixture where castling is actually PLAYABLE within the perft depth.
    # The first version of this control planted the fault on the ep fixture, where both
    # kings have already forfeited the right, and perft correctly reported them identical --
    # which read as "the check is blind" when it was the FIXTURE that could not exercise it.
    castle = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
    cbase = perft(e, f"position fen {castle}")
    cfgot = perft(e, f"position fen {castle.replace(' KQkq ', ' - ')}")
    faults["castling dropped (castling-playable fixture)"] = None
    fired = {}
    for name, bad in faults.items():
        if bad is None:
            fired[name] = cfgot != cbase
            print(f"  PLANTED {name:38s} -> perft "
                  f"{'DIFFERS (check fires)' if fired[name] else 'IDENTICAL (check is blind)'}")
            continue
        got = perft(e, f"position fen {bad}")
        fired[name] = got != base
        print(f"  PLANTED {name:38s} -> perft "
              f"{'DIFFERS (check fires)' if fired[name] else 'IDENTICAL (check is blind)'}")

    # the python-chess Board.fen() trap, shown rather than asserted
    e2 = Engine(ENG); e2.uci(); e2.sync()
    real = force_ep_fen(b2)
    print(f"\npython-chess trap: move-list board has ep={chess.square_name(b2.ep_square) if b2.ep_square else None}")
    print(f"  force_ep_fen -> {real}")
    print(f"  Board.fen()  -> {dropped}")
    p_real = perft(e2, f"position fen {real}")
    p_drop = perft(e2, f"position fen {dropped}")
    print(f"  perft identical across that field? {p_real == p_drop} "
          f"(if True, perft does not exercise this ep square -- stated, not hidden)")
    e.quit(); e2.quit()

    # halfmove clock: invisible to perft, visible to the bail
    e3 = Engine(ENG); e3.uci(); e3.sync()
    def search(pos):
        e3.send(pos); e3.send("go depth 8")
        lines = e3.read_until(lambda l: l.startswith("bestmove"))
        nodes = [l for l in lines if l.startswith("info depth")]
        n = int(nodes[-1].split(" nodes ")[1].split()[0]) if nodes else 0
        return lines[-1].split()[1], n
    fen99 = "8/8/8/8/8/1R6/8/k1K5 w - - 99 1"
    fen100 = "8/8/8/8/8/1R6/8/k1K5 w - - 100 1"
    m99, n99 = search(f"position fen {fen99}")
    m100, n100 = search(f"position fen {fen100}")
    print("\nhalfmove clock (perft cannot see this field):")
    print(f"  clock 99  -> {m99} nodes {n99}")
    print(f"  clock 100 -> {m100} nodes {n100}")
    clock_visible = (n99 != n100) or (m99 != m100)
    print(f"  the clock CHANGES the answer: {clock_visible}  <- this is why identity is split "
          f"into 'perft-visible fields' and 'clock'")
    e3.quit()

    ok = all(fired.values()) and clock_visible
    json.dump({"faults": faults, "fired": fired, "clock_visible": clock_visible,
               "python_chess_dropped_ep": {"forced": real, "board_fen": dropped,
                                           "perft_identical": p_real == p_drop}},
              open("evidence/position_identity_control.json", "w"), indent=0)
    print(f"\nCONTROL {'FIRES on all planted faults' if all(fired.values()) else 'IS BLIND on at least one fault'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
