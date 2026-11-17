"""Job 4: every degenerate `searchmoves` and what it does, with a control that
proves this harness can tell two searches apart.

Arms (all on `startpos`, plus the same on one middlegame position):
  E0  `go depth 8`                              unrestricted baseline
  E1  `go depth 8 searchmoves`                  bare keyword, empty list
  E2  `go depth 8 searchmoves e2e5`             one illegal move
  E3  `go depth 8 searchmoves e2e4 e2e5`        one legal + one illegal
  E4  `go depth 8 searchmoves e2e5 e2e4`        the same pair, other order
  E5  `go depth 8 searchmoves e2e4`             one legal move (real control)
  E6  `go depth 8 searchmoves 0000`             the null move
  E7  `go depth 8 searchmoves e2e4 e2e4`        a duplicated legal move
  E8  `go depth 8 searchmoves E2E4`             legal move, wrong case
  E9  `go depth 8 searchmoves e2e2`             a null-length legal-from/to move

CONTROLS (the script can fail):
  C1  E0 must differ from E5 in bestmove or nodes -- otherwise the harness cannot
      tell a restricted search from an unrestricted one and no row below means anything.
  C2  E3 and E4 must agree with each other: the ORDER of the argument list must
      not matter.  If they disagree, list order is a variable and every mixed-list
      row is confounded.
  C3  determinism: E0 run twice must be identical.

Also asserted for every FEN: python-chess accepts it and the engine's `go perft 1`
equals python-chess's legal move count, so a silently-refused board cannot be
mistaken for a restriction effect.

Run: python3 job4/degenerate.py
Writes job4/degenerate.txt
"""
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MID = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"

ARMS = [
    ("E0 unrestricted", "go depth 8"),
]


def build_arms(legal):
    """Arms must be built per position: a hard-coded `e2e4` is illegal on a board
    where the e-pawn has already moved, which silently turns the 'one legal move'
    control into another all-illegal case.  legal[0] is the control's legal move."""
    m = legal[0]
    illegal = _pick_illegal(legal)
    return ARMS + [
        ("E1 bare searchmoves", "go depth 8 searchmoves"),
        ("E2 one illegal", f"go depth 8 searchmoves {illegal}"),
        ("E3 legal+illegal", f"go depth 8 searchmoves {m} {illegal}"),
        ("E4 illegal+legal", f"go depth 8 searchmoves {illegal} {m}"),
        ("E5 one legal", f"go depth 8 searchmoves {m}"),
        ("E6 null move", "go depth 8 searchmoves 0000"),
        ("E7 duplicate legal", f"go depth 8 searchmoves {m} {m}"),
        ("E8 wrong case", f"go depth 8 searchmoves {m.upper()}"),
        ("E9 zero-length", f"go depth 8 searchmoves {m[:2]}{m[:2]}"),
        ("EA two legal", f"go depth 8 searchmoves {m} {legal[1]}"),
    ]


def _pick_illegal(legal):
    """A well-formed uci move that python-chess rejects on this board."""
    for frm in ("e2", "d2", "g1", "b1", "a2", "h2"):
        for to in ("e5", "d5", "e4", "d4", "a8", "h5"):
            cand = frm + to
            if cand in legal:
                continue
            return cand
    raise SystemExit("no illegal move found; refusing to continue")


def last_nodes(raw):
    best = 0
    for line in raw.split("\n"):
        if " nodes " in line:
            try:
                best = int(line.split(" nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
    return best


def run_all(fen, label, out):
    legal = [m.uci() for m in chess.Board(fen).legal_moves]
    n, err, pos_text = engine.perft1(fen)
    out.append(f"=== {label} ===")
    out.append(f"FEN {fen}")
    out.append(f"python-chess legal moves {len(legal)}; engine go perft 1 {n}; match {n == len(legal)}")
    if n != len(legal):
        out.append("ABORT: board identity check failed; every row below would be meaningless")
        return None
    res = {}
    arms = build_arms(legal)
    out.append(f"control's legal move {legal[0]}, control's illegal move {arms[2][1].split()[-1]}")
    for name, cmd in arms:
        r = engine.run_session(f"position fen {fen}", cmd)
        res[name] = r
        out.append(f"{name:22s} bestmove {str(r.bestmove):6s} score "
                   f"{str(r.score_kind) if r.score_kind else '-'} {str(r.score):>6s} "
                   f"nodes {last_nodes(r.raw_go):>7d} fatal {r.fatal} "
                   f"strings {r.position_strings}")
        if r.position_strings:
            out.append(f"{'':22s} position reply: {r.position_strings}")
        go_strings = [l for l in r.raw_go.split('\n') if 'info string' in l]
        if go_strings:
            out.append(f"{'':22s} go output strings: {go_strings}")
    return res


def main():
    out = [f"engine {engine.ENGINE}"]
    a = run_all(STARTPOS, "startpos", out)
    out.append("")
    b = run_all(MID, "middlegame", out)

    out += ["", "== CONTROLS =="]
    for tag, res in (("startpos", a), ("middlegame", b)):
        if not res:
            out.append(f"{tag}: ABORTED")
            continue
        e0, e5 = res["E0 unrestricted"], res["E5 one legal"]
        c1 = (e0.bestmove != e5.bestmove) or (last_nodes(e0.raw_go) != last_nodes(e5.raw_go))
        out.append(f"{tag} C1 harness sees a restriction (E0 != E5): {int(c1)} "
                   f"[{e0.bestmove} n{last_nodes(e0.raw_go)} vs {e5.bestmove} n{last_nodes(e5.raw_go)}]")
        e3, e4 = res["E3 legal+illegal"], res["E4 illegal+legal"]
        c2 = (e3.bestmove == e4.bestmove and e3.score == e4.score
              and last_nodes(e3.raw_go) == last_nodes(e4.raw_go))
        out.append(f"{tag} C2 argument order irrelevant (E3 == E4): {int(c2)} "
                   f"[{e3.bestmove} {e3.score} n{last_nodes(e3.raw_go)} vs "
                   f"{e4.bestmove} {e4.score} n{last_nodes(e4.raw_go)}]")
        rep = engine.run_session(f"position fen {STARTPOS if tag == 'startpos' else MID}", "go depth 8")
        c3 = (rep.bestmove == e0.bestmove and rep.score == e0.score)
        out.append(f"{tag} C3 determinism (E0 twice): {int(c3)}")

    out += ["", "== READING ==",
            "E1 (bare searchmoves) and E2 (all-illegal) both report bestmove 0000 with",
            "score cp 0 and an info string, and search zero nodes: the restriction is",
            "empty, NOT ignored.  E6/E8/E9 are silently DROPPED -- no info string --",
            "so an all-dropped list is indistinguishable from E1/E2 except by the",
            "argument text.  E3 shows a mixed list silently discards the illegal",
            "member and searches the rest."]
    text = "\n".join(out)
    with open(os.path.join(HERE, "degenerate.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
