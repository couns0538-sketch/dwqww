"""Q3: does the book reply ever disagree with the engine's own depth-18 top choice
in a way that LOSES MATERIAL, on positions a game actually reaches?

The isolation test in swarm/65 already showed 0 of 135 static-exchange flags
survive a depth-12 check. That test walked every book position in the book, but
a walk is not a game: the question here is whether a *reachable game path* ever
puts the engine in one of those positions with the book making a materially
worse choice than its own search.

Three parts, and the middle one is the one that matters:

  1. Reach. Enumerate every position a two-sided book game can present to the
     engine, from the games just played (not from the book's own walk, so a
     position the games never reached is correctly absent).
  2. Material. For each such position, compare the book reply against the
     engine's own `go depth 18` best move using a MATERIAL evaluation of the
     resulting positions, not a score comparison. A static material count is the
     only judge here that cannot be gamed by the engine's own eval preferences,
     and "loses material" is the claim being tested.
  3. Noise floor. A material comparison has no noise, but the depth-18 SEARCH
     does: two searches of the same position at depth 18 are deterministic, so
     the floor is measured by re-running a sample and requiring identical
     material, and by measuring the depth-12-vs-depth-18 material agreement on
     the same set (the "would depth 12 have told us this" question).

Why depth 18 and not 12: the brief requires it, and the reason is in the record —
the swarm-65 gap sweep found the worst offenders' gaps SHRINK at depth 18, i.e.
they were horizon artefacts. Calling a book move bad on a depth-12 dislike is
exactly the error that would produce a false defect.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time

import chess

from forge_uci import Engine

PIECE_VALUE = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
               chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board: chess.Board) -> int:
    """White minus Black material, in centipawns. No positional term."""
    total = 0
    for piece_type, value in PIECE_VALUE.items():
        total += value * (len(board.pieces(piece_type, chess.WHITE))
                          - len(board.pieces(piece_type, chess.BLACK)))
    return total


def side_material_delta(before: chess.Board, after: chess.Board) -> int:
    """Material change for the mover, in cp. Negative means the mover lost some."""
    sign = 1 if before.turn == chess.WHITE else -1
    return sign * (material(after) - material(before))


def qmaterial_white(board: chess.Board, alpha: int = -100000, beta: int = 100000,
                    depth: int = 12) -> int:
    """White-minus-Black material after every capture and recapture is resolved.

    Returned from WHITE's point of view, not the side to move. That choice removes
    a whole class of sign bug: the first version returned "value for `side`" and
    recursed with `-side`, where `side` is a python-chess Color (a bool), so
    `-True == -1` was never a colour. The result was 45 phantom material losses,
    all exactly one or three pawns, which is what a sign error looks like.

    Zero-sum negamax over captures only: both sides take the best capture, and
    the score is minimised/maximised alternately.
    """
    stand = material(board)                     # white's view, always
    if depth <= 0 or board.is_game_over(claim_draw=False):
        return stand
    captures = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
    if not captures:
        return stand
    if board.turn == chess.WHITE:
        best = stand
        if best >= beta:
            return best
        alpha = max(alpha, best)
        for mv in captures:
            child = board.copy()
            child.push(mv)
            score = qmaterial_white(child, alpha, beta, depth - 1)
            if score > best:
                best = score
                if best > alpha:
                    alpha = best
                if best >= beta:
                    break
        return best
    best = stand
    if best <= alpha:
        return best
    beta = min(beta, best)
    for mv in captures:
        child = board.copy()
        child.push(mv)
        score = qmaterial_white(child, alpha, beta, depth - 1)
        if score < best:
            best = score
            if best < beta:
                beta = best
            if best <= alpha:
                break
    return best


def settled_material(engine: Engine, board: chess.Board, move: chess.Move,
                     reply_depth: int, timeout: float) -> tuple[int | None, str | None]:
    """Material for the MOVER after `move`, with every recapture resolved.

    A single reply ply is not enough: after a move met by a capture, the recapture
    is what decides the material. Measured that way, every book move allowing any
    capture scored exactly minus a piece value, because the recapture was never
    played.

    `reply_depth` is unused for the figure (quiescence resolves it) and is kept so
    the call sites read the same; the engine is not consulted here on purpose,
    because the question is about material and the engine's eval would smuggle in
    positional judgement.
    """
    if move not in board.legal_moves:
        return None, f"illegal move {move.uci()}"
    mover = board.turn
    after = board.copy()
    after.push(move)
    if after.is_game_over(claim_draw=False):
        return side_material_delta(board, after), None
    before = material(board)
    # The figure is "material after this move once captures settle" MINUS the
    # material before the move. Not minus the post-move material: a promotion
    # changes the mover's own material on the move itself, and comparing against
    # the post-move total double-counted it (+1300 for a queen promotion instead
    # of +800). Measuring against `before` also keeps the answer in the same unit
    # for every candidate move, which is what the comparison needs.
    white_view = qmaterial_white(after)
    delta_white = white_view - before
    return delta_white if mover == chess.WHITE else -delta_white, None


def _book_moves(board: chess.Board) -> list[chess.Move]:
    """All book moves for this position, from the embedded book data.

    Uses the same decoder as the rest of the swarm, so a move is accepted here if
    and only if the book walk accepts it.
    """
    import chess.polyglot
    import book_graph as bg
    entries = BOOK_CACHE.get("entries")
    if entries is None:
        return []
    key = chess.polyglot.zobrist_hash(board)
    out = []
    for k, mov, _w in entries:
        if k != key:
            continue
        mv = bg.decode(board, mov)
        if mv is not None and board.is_legal(mv):
            out.append(mv)
    return out


BOOK_CACHE: dict = {}


def probe_position(job) -> dict:
    """One position: book reply, depth-18 best, depth-12 best, material deltas."""
    engine_path, fen, book_variety, depth_hi, depth_lo, timeout, reply_depth, forced = job
    board = chess.Board(fen)
    out = {"fen": fen, "book_move": None, "d18_move": None, "d12_move": None,
           "book_mat": None, "d18_mat": None, "d12_mat": None,
           "book_equals_d18": None, "book_worse_than_d18": None,
           "d18_equals_d12": None, "reply_plies": reply_depth, "error": None,
           "judged_move": None}

    eng = Engine(engine_path)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", str(book_variety))

        # the book reply, through the clock form that reaches the book
        eng.position_checked(f"fen {fen}")
        reply = eng.go("wtime 60000 btime 60000", timeout)
        if reply.timed_out:
            out["error"] = "book probe timed out"
            return out
        book_uci = reply.book_move()
        out["book_move"] = book_uci
        if book_uci is None:
            out["error"] = "position is not in the book"
            return out
        mv = chess.Move.from_uci(book_uci)
        if mv not in board.legal_moves:
            out["error"] = f"book move {book_uci} illegal"
            return out

        # judge the move a GAME actually played when one was supplied, because the
        # deterministic probe reply is not necessarily the move the games made
        judged = mv
        if forced is not None:
            cand = chess.Move.from_uci(forced)
            if cand not in board.legal_moves:
                out["error"] = f"played move {forced} illegal here"
                return out
            if forced != book_uci:
                # the played move must still be a book move for this position
                if forced not in {m.uci() for m in _book_moves(board)}:
                    out["error"] = f"played move {forced} is not a book move here"
                    return out
            judged = cand
        out["judged_move"] = judged.uci()

        # the engine's own choices, with OwnBook off so it actually searches
        eng.setoption("OwnBook", "false")
        chosen: dict[str, chess.Move] = {"book": judged}
        for key, depth in (("d18", depth_hi), ("d12", depth_lo)):
            eng.position_checked(f"fen {fen}")
            r = eng.go(f"depth {depth}", timeout)
            if r.timed_out or r.bestmove() is None:
                out["error"] = f"depth {depth} probe failed"
                return out
            uci = r.bestmove()
            out[f"{key}_move"] = uci
            m = chess.Move.from_uci(uci)
            if m not in board.legal_moves:
                out["error"] = f"depth {depth} returned illegal {uci}"
                return out
            chosen[key] = m

        # settled material for each of the three candidates, same reply depth
        for key in ("book", "d18", "d12"):
            mat, err = settled_material(eng, board, chosen[key], reply_depth, timeout)
            if err is not None:
                out["error"] = f"{key}: {err}"
                return out
            out[f"{key}_mat"] = mat

        out["book_equals_d18"] = out["judged_move"] == out["d18_move"]
        out["book_worse_than_d18"] = out["book_mat"] < out["d18_mat"]
        out["d18_equals_d12"] = out["d18_move"] == out["d12_move"]
        return out
    except Exception as exc:                                  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--positions", required=True, help="JSON list of FENs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth-hi", type=int, default=18)
    ap.add_argument("--depth-lo", type=int, default=12)
    ap.add_argument("--book-variety", type=int, default=0,
                    help="0 = deterministic (highest-weight) book reply")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--reply-depth", type=int, default=8,
                    help="depth of the opponent's reply used to settle material")
    ap.add_argument("--repeat", type=int, default=0,
                    help="if >0, re-probe this many positions for determinism")
    ap.add_argument("--played", default=None,
                    help="JSON of [{fen, move}] book moves games ACTUALLY played; "
                         "when given, those moves are judged instead of the "
                         "deterministic book choice")
    ap.add_argument("--book", default=None,
                    help="path to book_data.inc, required with --played so the "
                         "played move can be checked against the book")
    args = ap.parse_args()

    if args.book:
        import book_graph as bg
        BOOK_CACHE["entries"] = bg.load_book(args.book)

    played = None
    if args.played:
        raw = json.load(open(args.played))
        played = {(r["fen"], r["move"]) for r in raw}
        print(f"{len(played)} book moves actually played by the games")

    data = json.load(open(args.positions))
    items: list[tuple[str, str | None]] = []
    for d in data:
        if isinstance(d, dict):
            items.append((d["fen"], d.get("move")))
        else:
            items.append((d, None))
    print(f"{len(items)} positions to probe at depth {args.depth_hi} vs {args.depth_lo}")
    if args.played and not args.book:
        raise SystemExit("--played requires --book so the played move can be checked")
    jobs = [(args.engine, fen, args.book_variety, args.depth_hi, args.depth_lo,
             args.timeout, args.reply_depth, mv) for fen, mv in items]
    results: list[dict] = []
    started = time.monotonic()
    with mp.Pool(args.workers) as pool:
        for n, res in enumerate(pool.imap_unordered(probe_position, jobs), 1):
            results.append(res)
            if n % 10 == 0:
                print(f"  {n}/{len(jobs)} {time.monotonic()-started:.0f}s", flush=True)

    ok = [r for r in results if r["error"] is None]
    worse = [r for r in ok if r["book_worse_than_d18"]]

    determinism = None
    if args.repeat and ok:
        sample = ok[:args.repeat]
        print(f"determinism: re-probing {len(sample)} positions")
        again = [probe_position((args.engine, r["fen"], args.book_variety,
                                 args.depth_hi, args.depth_lo, args.timeout,
                                 args.reply_depth, r["judged_move"]))
                 for r in sample]
        agree_d18 = sum(1 for a, b in zip(sample, again) if a["d18_move"] == b["d18_move"])
        agree_mat = sum(1 for a, b in zip(sample, again) if a["d18_mat"] == b["d18_mat"])
        determinism = {"reprobed": len(sample), "d18_move_agrees": agree_d18,
                       "d18_material_agrees": agree_mat}

    report = {
        "engine": args.engine,
        "positions_input": len(items),
        "positions_probed_ok": len(ok),
        "errors": len(results) - len(ok),
        "error_detail": [r for r in results if r["error"]][:20],
        "book_equals_depth18": sum(1 for r in ok if r["book_equals_d18"]),
        "book_differs_from_depth18": sum(1 for r in ok if not r["book_equals_d18"]),
        "book_loses_material_vs_depth18": len(worse),
        "loss_detail": worse,
        "depth18_equals_depth12": sum(1 for r in ok if r["d18_equals_d12"]),
        "determinism": determinism,
        "judged_moves_source": ("book moves the games actually played"
                               if args.played or any(m for _f, m in items)
                               else "the deterministic (Book Variety 0) book reply"),
        "elapsed_s": round(time.monotonic() - started, 1),
    }
    json.dump(report, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("loss_detail", "error_detail")}, indent=1))
    for w in worse:
        print("  LOSS:", w["fen"], w["judged_move"], w["book_mat"],
              "vs d18", w["d18_move"], w["d18_mat"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
