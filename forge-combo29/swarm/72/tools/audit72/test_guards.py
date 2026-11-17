"""Prove the two guards bite before trusting any measurement.

A test harness that cannot fail is not evidence.  These checks plant inputs
whose correct outcome is already known by hand:

  A. python-chess rejects an impossible FEN  -> Probe must refuse it.
  B. The engine refuses a FEN that python-chess accepts as *text* but the
     engine rejects (halfmove/fullmove sanity, ep-square consistency), and
     the guard must catch the diagnostic in the position reply.
  C. Same refusal, but with the isready omitted so the diagnostic lands in
     the go output -> the guard must catch it there too.
  D. A stale-board trap: load a good board, then a refused board, and show
     that the perft-1 gate detects the previous board still being in place.
  E. perft-1 agreement on a known-correct position (startpos = 20).
"""

import sys

import chess

from engine import EngineError, Probe, UciSession

FAILS = []


def check(label, fn):
    try:
        fn()
        print("PASS  %s" % label)
    except Exception as exc:
        FAILS.append((label, exc))
        print("FAIL  %s: %s" % (label, exc))


# A: python-chess is the first gate.  Note that python-chess *parses* boards
# with no kings (it only reports is_valid() False), so the first gate needs a
# genuinely malformed field -- an illegal piece letter.
def case_a():
    bad = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNX w KQkq - 0 1"
    try:
        chess.Board(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("python-chess accepted a malformed placement")
    try:
        Probe(bad, name="bad-placement")
    except EngineError as exc:
        assert "python-chess rejected" in str(exc), exc
        return
    raise AssertionError("malformed FEN was accepted")


# B: engine-side refusal visible in the position reply.
# Black to move with white already in check from a black rook, plus an
# en-passant square that has no double-pushed pawn behind it: python-chess
# parses ep leniently, the engine's stricter ep consistency check rejects it.
BAD_EP = "4k3/8/8/8/8/8/4P3/4K3 b - e6 0 1"
BAD_HALFMOVE = "4k3/8/8/8/8/8/8/4K3 w - - -1 1"


def case_b():
    assert chess.Board(BAD_EP) is not None  # python-chess tolerates it
    try:
        Probe(BAD_EP, name="bad-ep")
    except EngineError as exc:
        assert "refused" in str(exc) or "python-chess" in str(exc), exc
        return
    raise AssertionError("engine-side bad ep accepted silently")


# C: refusal caught in the go stream when no isready precedes it.
def case_c():
    s = UciSession()
    try:
        s.send("position fen " + BAD_HALFMOVE)
        s.send("go depth 4")
        _, collected = s.read_until(
            lambda l: l.startswith("bestmove") or l.startswith("info string invalid"),
            what="bestmove",
        )
        found = [l for l in collected if l.startswith("info string invalid FEN")]
        assert found, "no refusal in go output: %r" % (collected[:4],)
    finally:
        s.close()


# D: stale-board trap -- the exact failure mode the brief warns about.
def case_d():
    s = UciSession()
    try:
        good = "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1"
        s.send("position fen " + good)
        s.send("isready")
        s.read_until(lambda l: l.strip() == "readyok", what="readyok")
        # Now send something the engine refuses; it must keep `good`.
        s.send("position fen " + BAD_HALFMOVE)
        s.send("isready")
        _, win = s.read_until(lambda l: l.strip() == "readyok", what="readyok")
        assert any(l.startswith("info string invalid FEN") for l in win), win
        s.send("go perft 1")
        _, coll = s.read_until(lambda l: l.startswith("nodes "), what="perft")
        stale = int(coll[-1].split()[1])
        oracle_good = len(list(chess.Board(good).legal_moves))
        oracle_bad = len(list(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1").legal_moves))
        # The engine reported the PREVIOUS board's count, not the FEN we sent.
        assert stale == oracle_good, (stale, oracle_good)
        assert stale != oracle_bad, "trap did not discriminate"
    finally:
        s.close()


# E: known-good baseline so the gate is not just always-red.
def case_e():
    p = Probe(chess.STARTING_FEN, name="startpos")
    assert p.perft1 == 20, p.perft1
    p.close()


if __name__ == "__main__":
    check("A python-chess rejects impossible FEN", case_a)
    check("B engine refusal scanned in position reply", case_b)
    check("C engine refusal scanned in go output", case_c)
    check("D stale board detected by perft-1 gate", case_d)
    check("E known-good perft-1 baseline (startpos=20)", case_e)
    if FAILS:
        print("\n%d guard check(s) failed -- measurements are not trustworthy" % len(FAILS))
        sys.exit(1)
    print("\nall guard checks passed")
