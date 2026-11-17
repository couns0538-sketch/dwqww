#!/usr/bin/env python3
"""Play one endgame out and record everything needed to replay it.

TWO ARMS, and the control is the reason the measurement means anything:

  oracle  -- the STRONG side plays the table-optimal move (max DTM against the
             defender's actual choice, i.e. the move that keeps the win shortest
             once the defender has moved). The engine defends.
             This arm MUST convert 20/20. If it does not, the harness, the table
             or the adjudication is wrong, and the engine numbers are not
             interpretable. It is the "can this harness detect a win at all" check.

  engine  -- BOTH sides are the engine. The strong side is the side with the extra
             material. This is the measured conversion rate.

WITHOUT the oracle arm, "the engine failed to convert" and "the position was not
winnable against this defence" are the same observation. The oracle arm separates
them by construction: the table says every start position is won, so perfect play
converts against ANY defence, and a failure is the attacking side's.

THE MOVE LIST IS ALWAYS SENT IN FULL. `position fen X moves ...` from the start
position, never a bare FEN of the current board: the engine's drawn-root predicate
includes `board.is_repetition()`, which needs the history, and a bare FEN would
manufacture a corpus that can never reach the repetition arm.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/tmp/fx")
import chess
import predicates
import solver
from uci import Engine, parse_info

MAX_PLIES = 400        # a KPK win is at most 28 moves; 400 plies cannot truncate one
DRAW_CLAIM_HM = 100    # the fifty-move counter; the engine's own bail threshold


def _position_cmd(start_fen: str, moves: list[str]) -> str:
    return "position fen " + start_fen + (" moves " + " ".join(moves) if moves else "")


def _oracle_attacker_move(board: chess.Board, table, label=None):
    """The table-optimal move for the winning side: mate first, then smallest DTM.

    OFF-TABLE CHILDREN ARE RESOLVED, not scored as unknown. A KPK promotion leaves the
    KPK table; scoring that child as "unknown" made the oracle REFUSE TO PROMOTE and
    shuffle a pawn on a7 for 100 plies, so 178 of 192 won cells "failed" through a
    harness bug rather than through the engine. Any child whose material signature is
    a solved piece table (KQK/KRK/KBK/KNK) is looked up there; anything else is a
    harness error and raises rather than silently ranking as bad.
    """
    best = None
    for mv in board.legal_moves:
        board.push(mv)
        try:
            score = _oracle_score(board, table)
        finally:
            board.pop()
        cand = (score[0], score[1], mv.uci())
        if best is None or cand < best[0]:
            best = (cand, mv)
    return best[1].uci() if best else None


# child value from the ATTACKER's point of view, as a sortable rank
_MATE, _UNKNOWN, _DRAW, _BAD = 0, 1, 2, 3


def _oracle_score(board: chess.Board, table):
    """(rank, dtm) for the attacker, on a board where the DEFENDER is to move."""
    if board.is_checkmate():
        return (_MATE, 0)                       # defender has no move and is in check
    if board.is_stalemate():
        return (_DRAW, 0)
    # Every other terminal adjudication is a draw (insufficient material on the board).
    if board.is_insufficient_material():
        return (_DRAW, 0)
    val, dtm = _child_value(board, table)
    if val is solver.LOSS:
        # the side to move (the defender) is lost -> a win for the attacker
        return (_MATE, dtm if dtm is not None and dtm >= 0 else 0)
    if val is solver.DRAW:
        return (_DRAW, 0)
    if val is solver.WIN:
        return (_BAD, 0)                        # the defender wins: never choose it
    return (_UNKNOWN, 0)


def _child_value(board: chess.Board, table):
    """Value for the side to move, from whichever exact table covers this board."""
    sig = solver.signature(board)
    key, _ = solver.canonical(board, solver.ALL_SYMS)
    # the KPK entry point: pawn present -> the KPK table with its 2 symmetries
    if any(pt == chess.PAWN for pt, _ in sig):
        key, _ = solver.canonical(board, solver.PAWN_SYMS)
        if key in table["value"]:
            return table["value"][key], table["dtm"].get(key)
        raise KeyError(f"pawn position absent from the KPK table: {board.fen()}")
    import parallel
    name = _extra_name(sig)
    # table_for() keys on the FAMILY LABEL, not the piece letter.
    other = parallel.table_for(_FAMILY_OF[name]) if name else None
    if other is None:
        raise KeyError(f"no exact table for signature {sig}: {board.fen()}")
    key, _ = solver.canonical(board, other["syms"])
    if key not in other["value"]:
        raise KeyError(f"{board.fen()} absent from the {name} table")
    return other["value"][key], other["dtm"].get(key)


_FAMILY_OF = {"Q": "KQK", "R": "KRK", "B": "KBK", "N": "KNK"}


def _extra_name(sig):
    """'K+Q vs K' -> 'Q' for the piece-table lookup; '' when it is not a bare minor/rook/queen."""
    names = {chess.QUEEN: "Q", chess.ROOK: "R", chess.BISHOP: "B", chess.KNIGHT: "N"}
    white = [pt for pt, col in sig if col]
    black = [pt for pt, col in sig if not col]
    if len(white) == 1 and not black and white[0] in names:
        return names[white[0]]
    return ""


def play(start_fen: str, go: str, arm: str, table=None, exe="/tmp/fx/build/forge",
         options=None, max_plies=MAX_PLIES, search_timeout=None):
    """Play one game. Returns a fully replayable record.

    `search_timeout` is a per-search wall clock. On expiry the driver sends UCI `stop`
    (never `quit`) and the ply is marked `timed_out`; the game then continues from
    whatever move came back. A timeout is recorded, not hidden, because a search that
    cannot finish on a THREE-PIECE board is itself a result.
    """
    board = chess.Board(start_fen)
    if not board.is_valid():
        raise ValueError("illegal start FEN " + start_fen)
    start_turn = board.turn
    strong = chess.WHITE if start_turn == chess.WHITE else chess.BLACK

    e = Engine(exe, options)
    moves: list[str] = []
    plies = []
    bails = []
    term = None

    while len(moves) < max_plies:
        if board.is_checkmate():
            term = "checkmate"; break
        if board.is_stalemate():
            term = "stalemate"; break
        # NOT `board.is_insufficient_material()` here: python-chess adjudicates KBK and
        # KNK as insufficient material the moment the material exists, so testing it
        # before the move would end every bare-minor game at ply 0 with the engine
        # never having searched. The engine still has legal moves and must play them;
        # the adjudication is recorded as an OUTCOME category at the end instead, and
        # `no legal move` is the only thing that stops play.
        if not any(True for _ in board.legal_moves):
            term = "no_legal_moves"; break
        # The fifty-move counter is a REAL stop: the engine's own drawn-root bail uses
        # halfmove_clock >= 100, and a game that reaches it is a draw by rule.
        if board.halfmove_clock >= DRAW_CLAIM_HM:
            term = "fifty_move_claim"; break

        attack_side = (arm == "oracle" and board.turn == strong)
        if attack_side:
            uci = _oracle_attacker_move(board, table)
            rec = {"bestmove": uci, "source": "oracle", "nodes": None, "pv": []}
        else:
            pos = _position_cmd(start_fen, moves)
            e.set_position(pos)
            r = e.search(go, timeout_s=search_timeout)
            pi = parse_info(r["last"]) if r["last"] else {}
            uci = r["bestmove"]
            rec = {"bestmove": uci, "source": "engine", "nodes": pi.get("nodes"),
                   "pv": pi.get("pv", []), "score": pi.get("score"),
                   "score_kind": pi.get("score_kind"),
                   "depth": pi.get("depth"), "n_info": len(r["info"]),
                   "raw_bestmove": r["raw_bestmove"],
                   "timed_out": r.get("timed_out", False)}
            predicted = predicates.clock_reason(board)
            observed = (pi.get("nodes") == 0 and not pi.get("pv"))
            rec["bail_predicted"] = predicted
            rec["bail_observed"] = observed
            if observed:
                bails.append({"ply": len(moves), "reason": predicted,
                              "fen": board.fen(), "n_moves": len(moves),
                              "halfmove": board.halfmove_clock,
                              "bestmove": uci,
                              "n_legal": board.legal_moves.count()})
            if predicted and not observed:
                rec["bail_disagreement"] = True
            if observed and not predicted:
                rec["bail_disagreement"] = True

        if not uci or uci == "(none)":
            term = "no_move"; break
        try:
            mv = chess.Move.from_uci(uci)
        except ValueError:
            term = "unparseable"; break
        if mv not in board.legal_moves:
            term = "illegal"; break

        # record the pre-move check state and the SAN for the move list
        rec["san"] = board.san(mv)
        rec["ply"] = len(moves)
        rec["side"] = "white" if board.turn == chess.WHITE else "black"
        rec["fen_before"] = board.fen()
        rec["halfmove_before"] = board.halfmove_clock
        plies.append(rec)
        board.push(mv)
        moves.append(uci)

    else:
        term = "ply_cap"

    e.quit()

    if term is None:
        term = ("checkmate" if board.is_checkmate() else
                "stalemate" if board.is_stalemate() else
                "seventyfive" if board.is_seventyfive_moves() else "unfinished")

    # A game that never finished because a search hit the wall clock is its own
    # outcome category. Folding it into "drawn" or "unfinished" would flatter the
    # conversion rate.
    n_timeouts = sum(1 for p in plies if p.get("timed_out"))
    if term in ("ply_cap", "unfinished") and n_timeouts:
        term = "search_timeout"

    # Who won, if anyone.
    if term == "checkmate":
        winner = "black" if board.turn == chess.WHITE else "white"
    elif term in ("stalemate", "insufficient", "insufficient_after_play",
                  "fifty_move_claim", "seventyfive", "no_legal_moves"):
        winner = "draw"
    else:
        winner = "unfinished"

    # Adjudication as an OUTCOME, not as a move-stopping condition: with only kings or
    # a single bare minor on the board, FIDE and python-chess call it a draw, and that
    # is the correct result -- but the engine must still be asked to play first,
    # because the question is whether IT can convert, not whether the arbiter would.
    if term not in ("fifty_move_claim", "seventyfive"):
        if board.is_insufficient_material() and not board.is_checkmate():
            term = "insufficient_after_play"

    strong_colour = "white" if strong == chess.WHITE else "black"
    if winner == strong_colour:
        result = "converted"
    elif winner == "draw":
        result = "drawn"
    elif winner == "unfinished":
        result = "unfinished"
    else:
        result = "lost"
    if term == "search_timeout" and result == "converted":
        result = "converted_after_timeout"
    return {
        "start_fen": start_fen,
        "go": go,
        "arm": arm,
        "strong": strong_colour,
        "moves": moves,
        "plies": plies,
        "n_plies": len(moves),
        "n_moves_played": (len(moves) + 1) // 2,
        "term": term,
        "result": result,
        "winner": winner,
        "final_fen": board.fen(),
        "bails": bails,
        "n_bails": len(bails),
        "n_search_timeouts": n_timeouts,
        "bail_disagreements": [p for p in plies if p.get("bail_disagreement")],
        "total_engine_nodes": sum(p.get("nodes") or 0 for p in plies
                                  if p.get("source") == "engine"),
        "sans": [p["san"] for p in plies],
    }
