"""Q4: does the book path fire from the opponent's clock alone on the patched build?

Six clock forms on a position WITH a book entry, plus three on a position
WITHOUT one. Both builds.

Design points that make this more than a formality:

* Every position is ASSERTED against the book graph before it is used. The first
  version of this script guessed two FENs and both were wrong -- the "no book"
  position actually booked `g1f3`, and the "black to move" startpos is not a legal
  game position and is not in the book, so its row measured a search, not a book.
  A probe whose precondition is a guess measures nothing.
* A control runs FIRST and the run is VOID if it fails: the both-clocks form must
  answer inside the window. Without it, "no bestmove" could be a dead engine
  rather than a missing clock.
* Book rows and no-book rows are reported separately. A book reply returns before
  the time manager is consulted, so a row that books at 0.0 s says nothing about
  whether the search is now time-limited -- reporting it as if it did is the exact
  error the swarm-65 seat caught in its own work.
* The window is deliberately short (5 s). On the lock the one-sided rows are
  unbounded, so they must TIME OUT rather than answer slowly; a long window makes
  "unbounded" and "slow" harder to distinguish and costs 5x the runtime.
"""

from __future__ import annotations

import json
import sys
import time

import chess
import chess.polyglot

import book_graph as bg
from forge_uci import Engine

WINDOW = 5.0

# Book-bearing and book-free positions, both reached by legal play from startpos.
BOOK_LINES = {
    "white": [],                       # startpos
    "black": ["e2e4"],                 # Black to move, in book
}
NOBOOK_LINES = {
    "white": ["e2e4", "a7a6"],         # White to move, not in book
    "black": ["e2e4", "a7a6", "d2d3"], # Black to move, not in book
}


def board_for(moves: list[str]) -> chess.Board:
    b = chess.Board()
    for m in moves:
        b.push_uci(m)
    return b


def main() -> int:
    engine, out_path, book_path = sys.argv[1], sys.argv[2], sys.argv[3]
    # Variety 0 pins the book choice (see q0_rng.py). Without it this probe's
    # lock-vs-patched table compares two different RNG draws, not two builds.
    book_variety = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    entries = bg.load_book(book_path)
    keys = {k for k, _m, _w in entries}

    # --- assert the preconditions rather than assume them
    pre = {}
    for side, line in BOOK_LINES.items():
        b = board_for(line)
        k = chess.polyglot.zobrist_hash(b)
        pre[f"book_{side}"] = {"fen": b.fen(), "in_book": k in keys}
        if k not in keys:
            raise SystemExit(f"precondition failed: {side} position is not in the book")
    for side, line in NOBOOK_LINES.items():
        b = board_for(line)
        k = chess.polyglot.zobrist_hash(b)
        pre[f"nobook_{side}"] = {"fen": b.fen(), "in_book": k in keys}
        if k in keys:
            raise SystemExit(f"precondition failed: {side} no-book position IS in the book")

    forms = [
        ("book/white/both",  "white", "wtime 10000 btime 10000", True),
        ("book/white/wtime", "white", "wtime 10000", True),
        ("book/white/btime", "white", "btime 10000", True),
        ("book/black/both",  "black", "wtime 10000 btime 10000", True),
        ("book/black/btime", "black", "btime 10000", True),
        ("book/black/wtime", "black", "wtime 10000", True),
        ("nobook/white/both",  "white", "wtime 10000 btime 10000", False),
        ("nobook/white/btime", "white", "btime 10000", False),
        ("nobook/white/wtime", "white", "wtime 10000", False),
    ]

    def run(label: str, side: str, go_body: str, in_book_pos: bool) -> dict:
        lines = BOOK_LINES[side] if in_book_pos else NOBOOK_LINES[side]
        fen = board_for(lines).fen()
        eng = Engine(engine)
        try:
            eng.handshake()
            eng.newgame()
            eng.setoption("OwnBook", "true")
            # Pin the book RNG. The engine seeds it from steady_clock::now() per
            # process (uci.cpp:161-162), so at the default Book Variety of 30 the
            # SAME position returns different book moves on different runs. The
            # first version of this probe left the default in place and its
            # lock-vs-patched table showed different moves -- which is the RNG,
            # not the patch. See q0_rng.py, which measures that directly.
            eng.setoption("Book Variety", str(book_variety))
            eng.position_checked(f"fen {fen}")
            started = time.monotonic()
            reply = eng.go(go_body, WINDOW)
            elapsed = time.monotonic() - started
            return {
                "case": label, "go": go_body, "fen": fen,
                "position_in_book": in_book_pos,
                "elapsed_s": round(elapsed, 3),
                "answered": reply.bestmove() is not None,
                "booked": reply.book_move() is not None,
                "bestmove": reply.bestmove(),
                "timed_out": reply.timed_out,
            }
        finally:
            eng.quit()

    # control FIRST: both clocks must answer, or the whole run is void
    control = run("control/book/white/both", "white", "wtime 10000 btime 10000", True)
    print(f"{control['case']:24s} answered={control['answered']!s:5s} "
          f"{control['elapsed_s']:6.3f}s best={control['bestmove']}", flush=True)
    if not control["answered"]:
        report = {"engine": engine, "run_valid": False,
                  "verdict": "VOID: the control form did not answer on a book position"}
        json.dump(report, open(out_path, "w"), indent=1)
        print("VOID")
        return 1

    rows = [control]
    for label, side, go_body, in_book_pos in forms[1:]:
        row = run(label, side, go_body, in_book_pos)
        rows.append(row)
        print(f"{label:24s} answered={row['answered']!s:5s} booked={row['booked']!s:5s} "
              f"{row['elapsed_s']:6.3f}s best={row['bestmove']}", flush=True)

    report = {
        "engine": engine,
        "book_source": book_path,
        "window_s": WINDOW,
        "preconditions": pre,
        "run_valid": True,
        "rows": rows,
    }
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
