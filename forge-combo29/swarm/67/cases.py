#!/usr/bin/env python3
"""Corpus for the protocol-boundary fuzz.

Every malformed-input case is run in BOTH harness patterns, because the placement
of the `info string` refusal -- not its presence -- is what a real front end can
actually observe:
    pattern "P_isready":  position -> isready -> go
    pattern "P_direct":   position -> go
The control corpus deliberately contains inputs whose refusal MUST be detected;
if the harness fails to flag them, the harness is broken and the run is void.

Legal positions are validated with python-chess before use.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from fuzz import Case  # noqa: E402

try:
    import chess
except ImportError:                                   # pragma: no cover
    chess = None


PATTERNS = ("P_isready", "P_direct")


def _position_steps(pos: bytes, pattern: str) -> list:
    if pattern == "P_isready":
        return [(pos, "cmd"), (b"isready\n", "wait_ready"), (b"go depth 3\n", "wait_bestmove")]
    return [(pos, "cmd"), (b"go depth 3\n", "wait_bestmove")]


def _mk(cid, cls, pos, pattern, note="", **kw):
    return Case(cid=f"{cid}[{pattern}]", cls=cls, steps=_position_steps(pos, pattern),
                pattern=pattern, note=note, **kw)


# ---------------------------------------------------------------------------
# Legal fixtures, each verified with python-chess.
# ---------------------------------------------------------------------------

FENS = {
    "start": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "mate": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
    "stalemate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
    "bare": "8/8/8/8/8/8/8/K6k w - - 0 1",
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
}


def verify_fixtures() -> dict:
    """Assert every fixture is legal per python-chess. A bad fixture voids a run."""
    if chess is None:
        return {"available": False}
    out = {}
    for name, fen in FENS.items():
        b = chess.Board(fen)
        out[name] = {"valid": b.is_valid(), "status": str(b.status()), "fen": fen}
    return {"available": True, "fixtures": out}


def _legal_500_moves() -> list[str]:
    """500 legal moves from startpos (repeats allowed past the game horizon)."""
    if chess is None:
        return []
    b = chess.Board()
    moves = []
    while len(moves) < 500:
        cand = list(b.legal_moves)
        if not cand:
            b.reset()
            cand = list(b.legal_moves)
        m = cand[len(moves) % len(cand)]
        moves.append(m.uci())
        b.push(m)
    return moves


def build_cases() -> list[Case]:
    cases: list[Case] = []

    # ---------------- class: position / FEN ---------------------------------
    # Each malformed FEN in both patterns. The 8-field case is here because it
    # is the one shape the parser does NOT refuse.
    bad_fens = {
        "empty-fields": "position fen\n",
        "3-fields": "position fen 8/8/8/8/8/8/8/K6k w -\n",
        "5-fields": "position fen 8/8/8/8/8/8/8/K6k w - - 0\n",
        "8-fields": "position fen 8/8/8/8/8/8/8/K6k w - - 0 1 extra two\n",
        "no-kings": "position fen 8/8/8/8/8/8/8/8 w - - 0 1\n",
        "two-kings": "position fen 8/8/8/8/8/8/8/KK5k w - - 0 1\n",
        "adjacent-kings": "position fen 8/8/8/8/8/8/8/Kk6 w - - 0 1\n",
        "bad-side": "position fen 8/8/8/8/8/8/8/K6k x - - 0 1\n",
        "bad-rank-count": "position fen 8/8/8/8/8/8/K6k w - - 0 1\n",
        "rank-too-long": "position fen 9/8/8/8/8/8/8/K6k w - - 0 1\n",
        "pawn-rank-8": "position fen P7/8/8/8/8/8/8/K6k w - - 0 1\n",
        "unicode-piece": "position fen 8/8/8/8/8/8/8/K6k\u265e w - - 0 1\n",
        "negative-halfmove": "position fen 8/8/8/8/8/8/8/K6k w - - -1 1\n",
        "zero-fullmove": "position fen 8/8/8/8/8/8/8/K6k w - - 0 0\n",
        "junk-token": "position fen zzzz\n",
        "nul-in-fen": "position fen 8/8/8/8/8/8/8/K6k\u0000 w - - 0 1\n",
    }
    for name, cmd in bad_fens.items():
        for pat in PATTERNS:
            cases.append(_mk(f"fen:{name}", "position_fen", cmd.encode(), pat,
                             note="malformed FEN; refusal placement is the datum"))

    # newline inside a token: the line splits into two commands
    for pat in PATTERNS:
        cases.append(Case(
            cid=f"fen:newline-in-token[{pat}]", cls="position_fen", pattern=pat,
            steps=[(b"position fen 8/8/8/8/8/8/8/K6k w\n- - 0 1\n", "cmd"),
                   (b"isready\n", "wait_ready"), (b"go depth 3\n", "wait_bestmove")],
            note="embedded newline splits one intended FEN across two lines"))

    # very long strings (>64 KiB) in three shapes
    long_fen = b"position fen " + b"8/" * 40000 + b"\n"
    long_token = b"position fen " + b"A" * 70000 + b"\n"
    long_moves = b"position startpos moves " + b"e2e4 " * 20000 + b"\n"
    for nm, payload in (("64k-placement", long_fen), ("70k-single-token", long_token),
                        ("100k-moves", long_moves)):
        for pat in PATTERNS:
            cases.append(Case(cid=f"fen:long-{nm}[{pat}]", cls="position_fen", pattern=pat,
                              steps=[(payload, "cmd"), (b"isready\n", "wait_ready"),
                                     (b"go perft 1\n", "wait_nodes")],
                              note="oversized single line"))

    # legal-but-extreme: 500 legal moves, and separator abuse
    moves500 = _legal_500_moves()
    if moves500:
        joined = " ".join(moves500).encode()
        for pat in PATTERNS:
            cases.append(Case(cid=f"fen:500-legal-moves[{pat}]", cls="position_fen", pattern=pat,
                              steps=[(b"position startpos moves " + joined + b"\n", "cmd"),
                                     (b"isready\n", "wait_ready"),
                                     (b"go depth 2\n", "wait_bestmove")],
                              note="500 verified-legal moves"))
        for nm, sep in (("multi-space", b"   "), ("tabs", b"\t\t"), ("mixed", b" \t ")):
            payload = (b"position startpos moves "
                       + sep.join(m.encode() for m in moves500[:20]) + b"\n")
            for pat in PATTERNS:
                cases.append(Case(cid=f"fen:sep-{nm}[{pat}]", cls="position_fen", pattern=pat,
                                  steps=[(payload, "cmd"), (b"isready\n", "wait_ready"),
                                         (b"go perft 1\n", "wait_nodes")],
                                  note="moves separated by runs of whitespace"))

    # illegal move in the list -> legal prefix searched (known defect)
    for pat in PATTERNS:
        cases.append(Case(cid=f"fen:illegal-move-in-list[{pat}]", cls="position_fen", pattern=pat,
                          steps=[(b"position startpos moves e2e4 e7e5 zzzz d2d4\n", "cmd"),
                                 (b"isready\n", "wait_ready"),
                                 (b"go perft 1\n", "wait_nodes")],
                          note="illegal token ends the prefix silently apart from one info line"))
        cases.append(Case(cid=f"fen:injection-after-junk[{pat}]", cls="position_fen", pattern=pat,
                          steps=[(b"position fen 8/8/8/8/8/8/8/K6k w - - 0 1 bogus moves a1a2\n", "cmd"),
                                 (b"isready\n", "wait_ready"),
                                 (b"go perft 2\n", "wait_nodes")],
                          note="tokens after the 6th FEN field reach the moves loader"))

    # empty / absent position arguments
    for nm, cmd in (("bare-position", b"position\n"), ("unknown-token", b"position foo\n"),
                    ("startpos-junk", b"position startpos junk\n")):
        for pat in PATTERNS:
            cases.append(Case(cid=f"fen:{nm}[{pat}]", cls="position_fen", pattern=pat,
                              steps=[(cmd, "cmd"), (b"isready\n", "wait_ready"),
                                     (b"go depth 3\n", "wait_bestmove")],
                              note="no usable position argument"))

    # refusal then search: does the engine use the PREVIOUS position? (known defect)
    for pat in PATTERNS:
        cases.append(Case(cid=f"fen:refused-after-good[{pat}]", cls="position_fen", pattern=pat,
                          steps=[(b"position fen " + FENS["bare"].encode() + b"\n", "cmd"),
                                 (b"position fen 8/8/8/8/8/8/8/8 w - - 0 1\n", "cmd"),
                                 (b"isready\n", "wait_ready"),
                                 (b"go perft 2\n", "wait_nodes")],
                          note="refused FEN must not silently keep the predecessor"))

    # ---------------- class: go --------------------------------------------
    go_cmds = {
        "depth-0": b"go depth 0\n",
        "depth-negative": b"go depth -5\n",
        "depth-huge": b"go depth 999999999999999999999\n",
        "nodes-0": b"go nodes 0\n",
        "nodes-huge": b"go nodes 18446744073709551616\n",
        "mate-0": b"go mate 0\n",
        "mate-negative": b"go mate -3\n",
        "mate-huge": b"go mate 99999999\n",
        "wtime-no-btime": b"go wtime 1000\n",
        "btime-no-wtime": b"go btime 1000\n",
        "movetime-0": b"go movetime 0\n",
        "movetime-negative": b"go movetime -100\n",
        "movestogo-0": b"go wtime 1000 btime 1000 movestogo 0\n",
        "unknown-tokens": b"go banana 5 foo bar\n",
        "duplicate-depth": b"go depth 2 depth 5\n",
        "duplicate-nodes": b"go nodes 10 nodes 100000\n",
        "depth-no-arg": b"go depth\n",
        "nodes-no-arg": b"go nodes\n",
        "searchmoves-no-moves": b"go depth 3 searchmoves\n",
        "searchmoves-illegal": b"go depth 3 searchmoves z9z9\n",
        "searchmoves-empty-set": b"go depth 3 searchmoves e7e5\n",
        "searchmoves-mixed": b"go depth 3 searchmoves e2e4 zzzz d2d4\n",
        "all-tokens": (b"go wtime 5000 btime 5000 winc 100 binc 100 movestogo 20 "
                       b"depth 4 nodes 100000 movetime 5000 mate 2 searchmoves e2e4\n"),
        "plus-sign-clock": b"go wtime +1000 btime +1000\n",
        "double-sign-clock": b"go wtime --1000 btime +-1000\n",
        "junk-clock": b"go wtime 12abc btime 1e5\n",
    }
    for name, cmd in go_cmds.items():
        cases.append(Case(cid=f"go:{name}", cls="go", pattern="P_isready",
                          steps=[(b"position startpos\n", "cmd"), (b"isready\n", "wait_ready"),
                                 (cmd, "wait_bestmove")],
                          note="go argument fuzz", bestmove_timeout=15.0))
    # a `go` with nothing at all runs forever; must be stopped, not waited out
    cases.append(Case(cid="go:bare-stopped", cls="go", pattern="P_isready",
                      steps=[(b"position startpos\n", "cmd"), (b"go\n", "cmd"),
                             (b"stop\n", "wait_bestmove")],
                      note="bare go == infinite", bestmove_timeout=15.0))

    # ---------------- class: setoption -------------------------------------
    so_cmds = {
        "no-value-keyword": b"setoption name Hash 64\n",
        "empty-name": b"setoption name\n",
        "name-only-space": b"setoption name \n",
        "unknown-name": b"setoption name Bogus value 5\n",
        "unicode-name": "setoption name Häsh value 64\n".encode(),
        "overflow-value": b"setoption name Hash value 99999999999999999999\n",
        "negative-value": b"setoption name Hash value -8\n",
        "value-missing": b"setoption name Hash value\n",
        "newline-in-value": b"setoption name Book File value /tmp/a\nb\n",
        "nul-in-value": b"setoption name Book File value /tmp/a\x00b\n",
        "bare-setoption": b"setoption\n",
        "nothing-after-name": b"setoption name\n",
        "unknown-with-value": b"setoption name Zzz type spin value 3\n",
        "hash-boundary-hi": b"setoption name Hash value 2048\n",
        "hash-boundary-over": b"setoption name Hash value 2049\n",
        "threads-zero": b"setoption name Threads value 0\n",
        "multipv-over": b"setoption name MultiPV value 99\n",
        "clearbuttons": b"setoption name Clear Hash\n",
        "double-apply": b"setoption name Hash value 64\nsetoption name Hash value 128\n",
    }
    for name, cmd in so_cmds.items():
        cases.append(Case(cid=f"setoption:{name}", cls="setoption", pattern="P_isready",
                          steps=[(b"isready\n", "wait_ready"), (cmd, "cmd"),
                                 (b"isready\n", "wait_ready"),
                                 (b"position startpos\ngo perft 2\n", "wait_nodes")],
                          note="setoption fuzz; usability probed by perft after"))

    # split across two writes: the partial line must not be executed as anything
    for nm, a, b in (
        ("split-name", b"setoption na", b"me Hash value 64\n"),
        ("split-value", b"setoption name Hash val", b"ue 64\n"),
        ("split-mid-word", b"setoption name Ha", b"sh value 64\n"),
        ("split-after-name", b"setoption name Hash", b" value 64\n"),
    ):
        cases.append(Case(cid=f"setoption:{nm}", cls="setoption", pattern="P_isready",
                          steps=[(b"isready\n", "wait_ready"), (a, "cmd"), (b, "cmd"),
                                 (b"isready\n", "wait_ready"),
                                 (b"position startpos\ngo perft 2\n", "wait_nodes")],
                          note="one command delivered in two writes"))

    # ---------------- class: search lifecycle ------------------------------
    life = {
        "stop-before-go": [b"stop\n", b"isready\n", b"position startpos\n", b"go depth 2\n"],
        "stop-twice": [b"position startpos\ngo infinite\n", b"stop\n", b"stop\n"],
        "stop-without-go-after-stop": [b"stop\n", b"stop\nstop\n", b"isready\n"],
        "isready-mid-search": [b"position startpos\ngo infinite\n", b"isready\n", b"stop\n"],
        "ucinewgame-mid-search": [b"position startpos\ngo infinite\n", b"ucinewgame\n", b"isready\n"],
        "two-go-no-stop": [b"position startpos\ngo infinite\n", b"go depth 2\n"],
        "ponderhit-without-ponder": [b"position startpos\n", b"ponderhit\n", b"isready\n"],
        "ponderhit-mid-normal-search": [b"position startpos\ngo infinite\n", b"ponderhit\n", b"stop\n"],
        "go-ponder-then-quit": [b"position startpos\ngo ponder\n", b"quit\n"],
        "position-mid-search": [b"position startpos\ngo infinite\n", b"position startpos moves e2e4\n", b"stop\n"],
        "setoption-mid-search": [b"position startpos\ngo infinite\n", b"setoption name Hash value 64\n", b"isready\n"],
        "quit-mid-search": [b"position startpos\ngo infinite\n", b"quit\n"],
        "eof-mid-search": [b"position startpos\ngo infinite\n"],
    }
    for name, steps in life.items():
        cases.append(Case(cid=f"lifecycle:{name}", cls="lifecycle", pattern="P_direct",
                          steps=[(s, "cmd") for s in steps] + [(b"", "settle")],
                          note="lifecycle ordering", bestmove_timeout=12.0,
                          expect_bestmove="may"))

    return cases


def build_control_cases() -> list[Case]:
    """Planted-bad inputs. Every one MUST produce a refusal the harness can see,
    or the harness is not measuring anything."""
    ctrl = []
    for pat in PATTERNS:
        ctrl.append(Case(cid=f"CONTROL:planted-bad-fen[{pat}]", cls="control", pattern=pat,
                         steps=_position_steps(b"position fen 8/8/8/8/8/8/8/8 w - - 0 1\n", pat),
                         note="must yield info string invalid FEN"))
        ctrl.append(Case(cid=f"CONTROL:planted-illegal-move[{pat}]", cls="control", pattern=pat,
                         steps=_position_steps(b"position startpos moves e2e4 zzzz\n", pat),
                         note="must yield info string illegal move"))
    ctrl.append(Case(cid="CONTROL:no-such-command", cls="control", pattern="P_isready",
                     steps=[(b"zzz-not-a-command\n", "cmd"), (b"isready\n", "wait_ready")],
                     note="silence is correct; proves absence is representable"))
    return ctrl
