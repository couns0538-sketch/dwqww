"""Generic self-play data generator: any UCI engine, fixed nodes per move, .plain output.

Each worker process owns one engine. Games start from the standard position (or a random book
line), a few random moves diversify the openings, then the engine plays both sides. Every searched
position is written as: fen / best move / score (side to move) / ply / game result (side to move).
Files are written per worker as *.plain.part and renamed to *_nCOUNT.plain when closed, so a crash
loses at most the games in progress. Leftover .part files are salvaged on the next start.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import random
import re
import time
from pathlib import Path

from .common import cpu_speed_pct, read_hwinfo, log, stop_requested
from .engine import EngineError, EngineSpec, UciEngine, engine_for_net, make_score_converter

_COUNT_RE = re.compile(r"_n(\d+)\.plain$")
LAST_SKIP = None        # set by play_game when it left a ply-limit game out: (last fen, last scores, records dropped)
LAST_ADJ = None         # set by play_game when it scored a drawn bare-king game as a win: (last fen, reason, result, records)
_TB = None              # this worker's Syzygy tables ([datagen] adjudicate_tablebase): None = not opened yet, False = unusable
TB_NOTE = None          # the first problem with the tables in this worker; written once to tablebase_problems.log
try:
    import msvcrt       # Windows: a lock on a log's first byte makes "seek to the end, write" one step
except ImportError:
    msvcrt = None


def _log_line(path, text: str) -> None:
    """Append one line to a log that the workers share. Windows' append mode is a seek and a write, so workers that
    append in the same moment write over each other's lines (round 85's selfgame.log lost worker 1's line on 20
    November; 16 processes at once lost 43 of 80 lines in a test): a lock on the file's first byte makes the two
    steps one. A log line is never worth a game: no lock within about 5 s, or any OSError, drops the line."""
    try:
        with open(path, "ab", buffering=0) as f:
            fd = f.fileno()
            if msvcrt is not None:
                for _ in range(500):
                    os.lseek(fd, 0, os.SEEK_SET)
                    try:
                        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.01)
                else:
                    return
            try:
                f.write(text.replace(chr(10), os.linesep).encode("utf-8"))     # the bytes text mode wrote
            finally:
                if msvcrt is not None:
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


def _book_lines(path: str) -> list[str] | None:
    if not path:
        return None
    lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                lines.append(" ".join(parts[:4]) + " 0 1")
    return lines or None


def _lone_king_lost(board, strong, exact: bool) -> bool:
    """True when the side `strong` has mating material and the other side has nothing but its king. exact = the rule
    of 17:12 ([datagen] bare_king_exact = true): exactly K+Q, K+R, K+B+N or K+B+B on both colours. Otherwise (the
    default since this patch) any material that holds a queen, a rook, a bishop and a knight, bishops on both colours
    or three knights; pawns are not counted (they can only add), so K+P(s), K+N+N, K+B+P stay draws."""
    import chess

    weak = not strong
    if board.occupied_co[weak] != board.pieces_mask(chess.KING, weak):
        return False                                      # the weak side must have nothing but its king
    bishops = board.pieces(chess.BISHOP, strong)
    colours = {(chess.square_file(sq) + chess.square_rank(sq)) & 1 for sq in bishops}
    if exact:
        own = [board.piece_type_at(sq) for sq in chess.SquareSet(board.occupied_co[strong])]
        kinds = sorted(chess.piece_symbol(t) for t in own if t != chess.KING)
        return kinds in (["q"], ["r"], ["b", "n"]) or (kinds == ["b", "b"] and len(colours) == 2)
    knights = len(board.pieces(chess.KNIGHT, strong))
    return bool(board.pieces_mask(chess.QUEEN, strong) or board.pieces_mask(chess.ROOK, strong)
                or (bishops and knights) or len(colours) == 2 or knights >= 3)


def _tb_value(tb, board) -> int:
    """+2 / -2 (side to move wins / loses) or 0 by the Syzygy tables, with the fifty-move rule exactly as
    pipeline/experiments/net_tb_slice.py line 44 has it: a cursed win or blessed loss (WDL +-1) is a draw, and so is a
    win or loss that the position's own half-move clock leaves no room for (|DTZ| + clock > 100). Raises KeyError
    (chess.syzygy.MissingTableError) when the tables do not hold the position."""
    wdl = tb.probe_wdl(board)
    if wdl not in (2, -2) or abs(tb.probe_dtz(board)) + board.halfmove_clock > 100:
        return 0
    return wdl


def tablebase_verdict(tb, board, start=None):
    """[datagen] adjudicate_tablebase: +1 / -1 (White / Black wins) or 0 for a game that ended in `board` (5 pieces or
    fewer, no castling rights); None when the tables cannot answer. `start` = the position just after the game's last
    capture or pawn move, where the fifty-move count began (found from the board's own moves when not given).
    Only a win under the fifty-move rule counts: _tb_value at `start` (its clock is 0 there, so this is the rule of
    net_tb_slice.py: a cursed win stays a draw, as self-play scores it), and still a win at the end with the count
    started again (the stronger side did not let it slip into a table draw). The end's OWN clock is not used: after a
    fifty-move draw it is 100 and would call every such game a draw, which is the engine's failure to convert at
    self-play depth, not a property of the positions; the net does not see the clock. When the moves do not reach
    back to `start` (a position set up by hand), the end is judged with its own clock (net_tb_slice.py exactly)."""
    import chess

    global TB_NOTE
    if chess.popcount(board.occupied) > 5 or board.castling_rights:
        return None
    try:
        if start is None and board.halfmove_clock <= len(board.move_stack):
            start = board.copy()
            for _ in range(board.halfmove_clock):
                start.pop()
        if start is None:
            end = _tb_value(tb, board)
            begin = end
        else:
            fresh = board.copy(stack=False)
            fresh.halfmove_clock = 0
            end = _tb_value(tb, fresh)
            begin = _tb_value(tb, start)
            begin = begin if start.turn == board.turn else -begin
    except Exception as e:  # noqa: BLE001  (a missing or damaged table: the material rule decides instead)
        if TB_NOTE is None and not isinstance(e, KeyError):
            TB_NOTE = f"tablebase probe failed ({type(e).__name__}: {e}) in {board.fen()}"
        return None
    if end == 0 or begin != end:
        return 0
    return (1 if (end > 0) == (board.turn == chess.WHITE) else -1)


def _tablebase(g: dict):
    """This worker's tables for [datagen] adjudicate_tablebase (default false; folder [datagen] tablebase_path), opened
    once, at the first drawn game that asks. None when the switch is off or the tables are not usable (TB_NOTE says
    why). python-chess only lists the folder here; it opens a table file at its first probe, read-only (os.O_RDONLY,
    mmap ACCESS_READ), and closes the file handle at once. At most 64 tables stay mapped per worker; the mapped pages
    are shared by all workers through the file cache of Windows (the 3-4-5 set is about 0.9 GB on disk)."""
    global _TB, TB_NOTE
    if not g.get("adjudicate_tablebase", False):
        return None
    if _TB is None:
        path = str(g.get("tablebase_path", "") or "")
        try:
            import chess.syzygy
            tb = chess.syzygy.open_tablebase(path, max_fds=64)
            if not tb.wdl or not tb.dtz:
                raise OSError("no .rtbw and .rtbz files there")
            _TB = tb
        except Exception as e:  # noqa: BLE001
            _TB = False
            TB_NOTE = f"tablebase not usable ({path!r}: {type(e).__name__}: {e}); the material rule alone decides"
    return None if _TB is False else _TB


def bare_king_adjudication(board, ended_by_limit: bool, draw_adjudicated: bool, exact: bool = False, tb=None,
                           material: bool = True):
    """[datagen] adjudicate_bare_king (Opus, 2026-11-15, job 9; Fable's decision of 16:45). (result for White, reason)
    when a drawn self-play game ended by the ply limit, the 50-move rule or a third occurrence and its last position is
    a lone king against mating material (_lone_king_lost; until this patch exactly K+Q, K+R, K+B+B on both colours or
    K+B+N, still so with exact=True), unless the lone king is to move and can take a piece so that no mating material
    is left. Otherwise None (also for stalemate, the draw adjudication and insufficient material). Job 8 measured why:
    at self-play depth the engine converted K+B+N against K in 21 % of the games that reached it and K+R against K in
    89 %; every record of such a game carried "draw". Round 14: 120 games K+Q+N against K drawn by the 50-move rule.
    tb = Syzygy tables ([datagen] adjudicate_tablebase): a last position with 5 pieces or fewer is judged by them
    instead (tablebase_verdict; also after the draw adjudication); material=False: the tables alone."""
    import chess

    if not any(board.generate_legal_moves()) or board.is_insufficient_material():
        return None
    if draw_adjudicated:
        reason = "draw adjudication"
    elif ended_by_limit:
        reason = "ply limit"
    elif board.halfmove_clock >= 100:
        reason = "50-move rule"
    elif board.is_repetition(3):
        reason = "third occurrence"
    else:
        return None
    if tb is not None:
        v = tablebase_verdict(tb, board)
        if v is not None:
            return None if v == 0 else (v, reason + ", tablebase")
    if draw_adjudicated or not material:
        return None
    for strong in (chess.WHITE, chess.BLACK):
        if not _lone_king_lost(board, strong, exact):
            continue
        if board.turn != strong:
            for m in board.generate_legal_moves():
                if board.is_capture(m):
                    after = board.copy(stack=False)
                    after.push(m)
                    if not _lone_king_lost(after, strong, exact):
                        return None                       # the lone king takes a piece and no mating material is left
        return (1 if strong == chess.WHITE else -1), reason
    return None


def play_game(eng: UciEngine, rng: random.Random, g: dict, convert, book):
    """Play one self-play game. Returns (plain_text, n_records, result_white, plies)."""
    import chess

    if book:
        start_fen = rng.choice(book)
        board = chess.Board(start_fen)
        pos_prefix = f"position fen {start_fen}"
    else:
        board = chess.Board()
        pos_prefix = "position startpos"
    moves: list[str] = []
    lo, hi = int(g["random_move_min_ply"]), int(g["random_move_max_ply"])
    k = min(int(g["random_move_count"]), max(0, hi - lo + 1))
    random_plies = set(rng.sample(range(lo, hi + 1), k)) if k > 0 else set()
    nodes = int(g["nodes"])
    # [datagen] soft_nodes (2026-11-14): with N > 0 the labelled searches use `go softnodes N`: the engine stops
    # after the first FINISHED iteration with at least N nodes (hard cap 4 N) instead of being cut off in the
    # middle of an iteration at `nodes`. With `go nodes 5000` the last finished iteration ended at 3,433 nodes on
    # average and the rest (31 %) was thrown away: the move and the score both come from that iteration.
    soft = int(g.get("soft_nodes", 0) or 0)
    go_cmd = f"go softnodes {soft}" if soft > 0 else f"go nodes {nodes}"
    eval_limit = int(g["eval_limit"])
    write_min_ply = int(g["write_min_ply"])
    max_ply = int(g["max_ply"])
    dr_ply, dr_score, dr_count = int(g["draw_adj_ply"]), int(g["draw_adj_score"]), int(g["draw_adj_count"])
    move_timeout = float(g.get("move_timeout_s", 60))
    rmpv = int(g.get("random_multi_pv", 0))
    rmpv_diff = int(g.get("random_multi_pv_diff", 100))
    recs = []
    ended_by_limit = False
    result = None  # +1 white wins, 0 draw, -1 black wins
    draw_run = 0
    eng.new_game()
    while True:
        ply = len(moves)
        # one legal-move generation decides both mate and stalemate
        if not any(board.generate_legal_moves()):
            result = (-1 if board.turn == chess.WHITE else 1) if board.is_check() else 0
            break
        # a third occurrence needs at least 8 reversible plies, so the repetition scan is skipped before that
        rule_draw = (board.is_insufficient_material() or board.halfmove_clock >= 100
                     or (board.halfmove_clock >= 8 and board.is_repetition(3)))
        if rule_draw or ply >= max_ply:
            result = 0
            ended_by_limit = not rule_draw      # stopped by OUR ply limit, not by a rule of chess
            break
        pos_cmd = pos_prefix + (" moves " + " ".join(moves) if moves else "")
        if ply in random_plies:
            mv = None
            if rmpv > 1:
                # random choice among the engine's best few moves that are close to the best one
                lines = eng.search_multipv(pos_cmd, f"go nodes {nodes * rmpv}", rmpv, timeout=move_timeout)
                cps = [(m, convert(v, board)) for m, (kind, v) in lines if kind == "cp"]
                if cps:
                    top = max(s for _m, s in cps)
                    pick = rng.choice([m for m, s in cps if s >= top - rmpv_diff])
                    try:
                        cand = chess.Move.from_uci(pick)
                        if board.is_legal(cand):
                            mv = cand
                    except ValueError:
                        pass
                elif lines:
                    try:
                        cand = chess.Move.from_uci(lines[0][0])
                        if board.is_legal(cand):
                            mv = cand
                    except ValueError:
                        pass
            if mv is None:
                mv = rng.choice(list(board.legal_moves))
            board.push(mv)
            moves.append(mv.uci())
            continue
        bm, sc = eng.search(pos_cmd, go_cmd, timeout=move_timeout)
        if sc is None or not bm or bm in ("(none)", "0000"):
            # the position is named so that the case can be repeated by hand (seen twice in 45 million
            # `go softnodes` searches on 2026-11-15: a move without any score line)
            raise EngineError(f"no move/score at ply {ply}: bestmove={bm} score={sc}; fen {board.fen()}; "
                              f"command {go_cmd}")
        kind, val = sc
        white_to_move = board.turn == chess.WHITE
        if kind == "mate":
            result = (1 if white_to_move else -1) * (1 if val > 0 else -1)
            break
        score = convert(val, board)
        if abs(score) >= eval_limit:
            result = (1 if white_to_move else -1) * (1 if score > 0 else -1)
            break
        try:
            mv = chess.Move.from_uci(bm)
        except ValueError:
            raise EngineError(f"unparsable bestmove {bm!r}")
        if not board.is_legal(mv):
            raise EngineError(f"illegal bestmove {bm} in {board.fen()}")
        if ply >= write_min_ply:
            recs.append((board.fen(), bm, score, ply, white_to_move))
        if ply >= dr_ply and abs(score) <= dr_score:
            draw_run += 1
            if draw_run >= dr_count:
                result = 0
                break
        else:
            draw_run = 0
        board.push(mv)
        moves.append(bm)
    return _after_game(board, recs, result, ended_by_limit, dr_count > 0 and draw_run >= dr_count, len(moves), g)


def _after_game(board, recs, result, ended_by_limit, draw_adjudicated, plies, g):
    """The end of play_game and play_game_sg (moved here unchanged from play_game on 2026-11-20): the after-game
    rules on `board` (the last position, with the game's moves), then the record text. Returns play_game's tuple."""
    # [datagen] ply_limit_skip_score (2026-11-15, Opus's rule after DeepSeek's job 6): a game that ran into the ply
    # limit while its last `ply_limit_skip_count` recorded scores all favoured the same side by at least that many
    # centipawns is written with NO positions. Its label would be "draw" although one side was clearly ahead
    # (3 of 966 games of round 11: R+B against a pawn with the score frozen at +662), and "win" would teach a result
    # the engine never reached (it may be a fortress). 0 = off. Ply-limit games with small scores stay draws.
    # [datagen] adjudicate_bare_king (Opus 2026-11-15, job 9): a drawn game whose last position is a won bare-king
    # ending (see bare_king_adjudication) is scored as a win for the side with the material; every record gets that
    # result. Such a game is not left out by the ply-limit rule below: its label is no longer "draw". false = off.
    # Since this patch: any mating material against the lone king (K+Q+N, K+R+B ...; bare_king_exact = true gives the
    # 17:12 rule), and with [datagen] adjudicate_tablebase = true (default false) a last position of 5 pieces or fewer
    # is judged by the Syzygy tables in tablebase_path instead (also after the draw adjudication).
    global LAST_ADJ
    LAST_ADJ = None
    if result == 0 and (g.get("adjudicate_bare_king", False) or g.get("adjudicate_tablebase", False)):
        adj = bare_king_adjudication(board, ended_by_limit, draw_adjudicated,
                                     exact=bool(g.get("bare_king_exact", False)), tb=_tablebase(g),
                                     material=bool(g.get("adjudicate_bare_king", False)))
        if adj is not None:
            result = adj[0]
            LAST_ADJ = (board.fen(), adj[1], adj[0], len(recs))
    global LAST_SKIP
    LAST_SKIP = None
    skip_score = int(g.get("ply_limit_skip_score", 0) or 0)
    skip_count = max(1, int(g.get("ply_limit_skip_count", 6) or 6))
    if ended_by_limit and skip_score > 0 and len(recs) >= skip_count and LAST_ADJ is None:
        tail = [(sc_ if wtm_ else -sc_) for _f, _b, sc_, _p, wtm_ in recs[-skip_count:]]     # White's view
        if all(v >= skip_score for v in tail) or all(v <= -skip_score for v in tail):
            LAST_SKIP = (recs[-1][0], tail, len(recs))
            return "", 0, result, plies
    out = []
    for fen, bm, score, ply, wtm in recs:
        res = result if wtm else -result
        out.append(f"fen {fen}\nmove {bm}\nscore {score}\nply {ply}\nresult {res}\ne\n")
    return "".join(out), len(recs), result, plies


def selfgame_ok(cfg: dict) -> str:
    """[datagen] selfgame: '' when this config may use play_game_sg, else why not (the worker then plays play_game)."""
    g, sc = cfg["datagen"], cfg["engine"].get("score", {})
    if int(g.get("soft_nodes", 0) or 0) <= 0:
        return "selfgame plays soft nodes only"
    if int(g.get("random_multi_pv", 0)) > 1:
        return "random_multi_pv > 1"
    if int(g["random_move_min_ply"]) != 0 or int(g["random_move_count"]) != int(g["random_move_max_ply"]) + 1:
        return "the random plies are not plies 0 to random_move_count - 1"
    if sc.get("unit", "raw") != "raw" or float(sc.get("multiplier", 1.0)) != 1.0:
        return "the engine's score is converted"
    return ""


def _selfgame_answers(eng: UciEngine) -> str:
    """'' when the engine knows the game loop (an exe without it says nothing to an unknown command)."""
    eng.send("position startpos")
    eng.send("sgstate")
    return "" if any(ln.startswith("sgstate ") for ln in eng.ready()) else "the engine does not answer sgstate"


def play_game_sg(eng: UciEngine, rng: random.Random, g: dict, book):
    """[datagen] selfgame (Opus 2026-11-20): play_game with the game loop inside the engine (carbon2's `selfgame`
    command, job 33, read line by line: tmp/opus_scratch/carbon2_j33_tools/READ_selfgame_patch_by_opus.md). The
    random plies are played here as play_game plays them; then ONE `selfgame` line, and the engine plays on with
    play_game's rules in play_game's order and prints every record (`sg ply score move fen`) and the end (`sgend`).
    Same tuple and text as play_game for the same rng (known answers: tmp/opus_scratch/selfgame_pc). Only where
    selfgame_ok() allows; `sgerror` is an EngineError, as a search without a score is in play_game."""
    import chess

    if book:
        start_fen = rng.choice(book)
        board = chess.Board(start_fen)
        pos_prefix = f"position fen {start_fen}"
    else:
        board = chess.Board()
        pos_prefix = "position startpos"
    moves: list[str] = []
    lo, hi = int(g["random_move_min_ply"]), int(g["random_move_max_ply"])
    k = min(int(g["random_move_count"]), max(0, hi - lo + 1))
    random_plies = set(rng.sample(range(lo, hi + 1), k)) if k > 0 else set()
    max_ply = int(g["max_ply"])
    eng.new_game()
    while len(moves) in random_plies:          # selfgame_ok(): plies 0 to k - 1, so they come first
        if not any(board.generate_legal_moves()):
            result = (-1 if board.turn == chess.WHITE else 1) if board.is_check() else 0
            return _after_game(board, [], result, False, False, len(moves), g)
        rule_draw = (board.is_insufficient_material() or board.halfmove_clock >= 100
                     or (board.halfmove_clock >= 8 and board.is_repetition(3)))
        if rule_draw or len(moves) >= max_ply:
            return _after_game(board, [], 0, not rule_draw, False, len(moves), g)
        mv = rng.choice(list(board.legal_moves))
        board.push(mv)
        moves.append(mv.uci())
    eng.send(pos_prefix + (" moves " + " ".join(moves) if moves else ""))
    eng.send(f"selfgame softnodes {int(g['soft_nodes'])} evallimit {int(g['eval_limit'])} maxply {max_ply} "
             f"writeminply {int(g['write_min_ply'])} drawply {int(g['draw_adj_ply'])} "
             f"drawscore {int(g['draw_adj_score'])} drawcount {int(g['draw_adj_count'])}")
    move_timeout = float(g.get("move_timeout_s", 60))
    recs = []
    while True:
        # line by line, play_game's timeout per search (one sg line a search): the game ends with sgend; sgerror and
        # a refused position line throw it away (after "invalid FEN" / "illegal move" the engine would play on from
        # the position before it: uci.cpp 92, 107); a line that does not parse is an EngineError, which the worker
        # catches (Fable's read FABLE-SG-READ S1 and S2, 20 November)
        line = eng._get(time.time() + move_timeout)
        if line.startswith("sg "):
            try:
                _, ply, score, bm, fen = line.split(" ", 4)
                recs.append((fen, bm, int(score), int(ply), fen.split(" ", 2)[1] == "w"))
            except (ValueError, IndexError):
                raise EngineError(f"unparsable selfgame line {line[:300]!r}") from None
        elif line.startswith("sgend "):
            break
        elif line.startswith(("sgerror ", "info string ERROR", "info string invalid FEN", "info string illegal move")):
            raise EngineError(f"{line}; command selfgame softnodes {g['soft_nodes']}")
    try:
        f = line.split()
        i = f.index("moves")
        keys = ("result", "reason", "plies", "run", "searches", "nodes")  # by name: a later field cannot shift them
        end = {f[j]: f[j + 1] for j in range(1, i - 1) if f[j] in keys}
        result, reason, plies = int(end["result"]), end["reason"], int(end["plies"])
        if result == 0 and (g.get("adjudicate_bare_king", False) or g.get("adjudicate_tablebase", False)):
            # shortcut: replays every drawn game's moves (about 1 ms); with a final position in sgend only the
            # games ending with a lone king or 5 pieces or fewer would need it
            for m in f[i + 1:]:
                mv = chess.Move.from_uci(m)
                if not board.is_legal(mv):          # as play_game: an illegal engine move throws the game away
                    raise ValueError(f"illegal move {m}")
                board.push(mv)
    except (ValueError, KeyError, IndexError) as e:
        raise EngineError(f"unparsable selfgame end ({e}): {line[:300]!r}") from None
    return _after_game(board, recs, result, reason == "plylimit",
                       reason == "drawadj" and int(g["draw_adj_count"]) > 0, plies, g)


def _worker(wid: int, spec_d: dict, cfg: dict, out_dir: str, rotate: int, seed: str,
            n_pos, n_games, n_plies, n_restarts, stop_ev, pause_ev=None, active=None) -> None:
    g = cfg["datagen"]
    rng = random.Random(seed)
    convert = make_score_converter(cfg)
    book = _book_lines(g.get("book", ""))
    spec = EngineSpec(**spec_d)
    stamp = f"{int(time.time())}_{os.getpid()}"
    out = Path(out_dir)
    idx = 0
    fh = None
    part = None
    in_file = 0
    eng = None
    fails = 0
    tb_noted = False
    sg_why = selfgame_ok(cfg) if g.get("selfgame", False) else "off"     # '' = the engine plays the game itself
    sg_noted = not g.get("selfgame", False)

    def close_file():
        nonlocal fh, part, in_file, idx
        if fh is None:
            return
        fh.close()
        if in_file > 0:
            os.replace(part, part.with_name(part.name[: -len(".plain.part")] + f"_n{in_file}.plain"))
        else:
            part.unlink(missing_ok=True)
        fh, part, in_file = None, None, 0
        idx += 1

    try:
        while not stop_ev.is_set():
            if pause_ev is not None and pause_ev.is_set():
                time.sleep(1.0)       # cooling pause asked for by the heat guard: idle between games
                continue
            if active is not None and wid >= active.value:
                time.sleep(1.0)       # the heat guard lets fewer workers play for now: this one idles between games
                continue
            try:
                if eng is None:
                    eng = UciEngine(spec)
                    if sg_why == "":
                        sg_why = _selfgame_answers(eng)
                    if not sg_noted:
                        # [datagen] selfgame: one line per worker in <round>/data/selfgame.log, used or why not
                        sg_noted = True
                        try:
                            _log_line(out.parent / "selfgame.log", f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: "
                                         + ("selfgame used" if sg_why == "" else "selfgame NOT used: " + sg_why) + chr(10))
                        except OSError:
                            pass
                if sg_why == "":
                    text, n, _result, plies = play_game_sg(eng, rng, g, book)
                else:
                    text, n, _result, plies = play_game(eng, rng, g, convert, book)
                fails = 0
            except EngineError as e:
                fails += 1
                with n_restarts.get_lock():
                    n_restarts.value += 1
                # Why the engine was restarted (2026-11-15: the first restart in about 100 million positions came
                # without a trace). One line per event in <round>/data/engine_restarts.log; the game is thrown away.
                try:
                    code = None if eng is None else eng.p.poll()
                    _log_line(out.parent / "engine_restarts.log", f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: {e}; engine exit code {code}\n")
                except OSError:
                    pass
                if eng is not None:
                    eng.quit()
                    eng = None
                if fails >= 5:
                    raise RuntimeError(f"worker {wid}: engine failed 5 times in a row: {e}")
                time.sleep(1.0)
                continue
            if LAST_SKIP is not None:
                # one line per game left out, in <round>/data/ply_limit_skipped.log (counted by the round's summary)
                try:
                    _log_line(out.parent / "ply_limit_skipped.log", f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: {LAST_SKIP[2]} positions left out; "
                                 f"last scores (White's view) {LAST_SKIP[1]}; last position {LAST_SKIP[0]}" + chr(10))
                except OSError:
                    pass
            if LAST_ADJ is not None:
                # one line per game scored as a win, in <round>/data/bare_king_adjudicated.log
                try:
                    _log_line(out.parent / "bare_king_adjudicated.log", f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: {LAST_ADJ[1]}; result -> "
                                 f"{'White' if LAST_ADJ[2] > 0 else 'Black'} wins; {LAST_ADJ[3]} positions; "
                                 f"last position {LAST_ADJ[0]}" + chr(10))
                except OSError:
                    pass
            if TB_NOTE is not None and not tb_noted:
                # [datagen] adjudicate_tablebase: why the tables did not answer, once per worker, in its own file
                # <round>/data/tablebase_problems.log (bare_king_adjudicated.log keeps one line per game)
                tb_noted = True
                try:
                    _log_line(out.parent / "tablebase_problems.log", f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: {TB_NOTE}" + chr(10))
                except OSError:
                    pass
            if n:
                if fh is None:
                    part = out / f"sp_w{wid:02d}_{stamp}_{idx:03d}.plain.part"
                    fh = open(part, "w", encoding="ascii", newline="\n")
                fh.write(text)
                fh.flush()
                in_file += n
            with n_pos.get_lock():
                n_pos.value += n
            with n_games.get_lock():
                n_games.value += 1
            with n_plies.get_lock():
                n_plies.value += plies
            if in_file >= rotate:
                close_file()
    finally:
        close_file()
        if eng is not None:
            eng.quit()


def salvage_parts(out_dir: Path) -> int:
    """Turn leftover *.plain.part files (from a crash) into finished files, keeping whole records."""
    saved = 0
    for part in sorted(out_dir.glob("*.plain.part")):
        data = part.read_bytes()
        cut = data.rfind(b"\ne\n")
        data = data[: cut + 3] if cut >= 0 else b""
        n = data.count(b"\ne\n")
        if n > 0:
            final = part.with_name(part.name[: -len(".plain.part")] + f"_n{n}.plain")
            tmp = part.with_name(part.name + ".salv")
            tmp.write_bytes(data)
            os.replace(tmp, final)
            saved += n
        part.unlink(missing_ok=True)
    return saved


def count_done(out_dir: Path) -> int:
    total = 0
    for p in out_dir.glob("*.plain"):
        m = _COUNT_RE.search(p.name)
        if m:
            total += int(m.group(1))
    return total


class StopRequested(RuntimeError):
    pass


class HeatGuard:
    """Pauses self-play when the CPU is too hot, and resumes it when it has cooled.

    Source 1: the CPU temperature in HWiNFO's log file (if the owner has that logging on).
    Source 2, when there is no fresh log: the CPU's speed. A CPU that overheats lowers its frequency,
    so a lasting drop below `speed_drop` of the speed seen at the start of this run counts as "hot".
    Config, block [limits]: cpu_temp_pause_c (default 92), cpu_temp_resume_c (default 80),
    heat_checks (default 6 checks 20 s apart must agree), cool_seconds (default 180, the shortest pause),
    heat_guard (default true).

    Since 2026-11-14 22:45 it first lets FEWER WORKERS play before it pauses all of them (heat_throttle,
    default true; only with a real temperature reading). Why: with the graphics card training in the same case
    the CPU reached 94 C with 16 workers, and the guard then cycled 2 minutes of play and 3 minutes of pause,
    so self-play ran 40 % of the time and the CPU went up and down by 8 C every five minutes. Now: at the pause
    temperature or above on 2 checks in a row, 2 workers fewer play (never fewer than heat_min_workers, default
    4); at heat_add_worker_c (default: 2 C under the pause temperature) or below on 2 checks in a row, 1 more
    plays. The CPU then stays just under the limit and self-play goes on. Only when the smallest number of
    workers is still too hot for heat_checks checks does the full pause come, as before.
    """

    def __init__(self, cfg: dict, pause_ev, active=None, n_workers: int = 0):
        lim = cfg.get("limits") or {}
        self.cfg = cfg
        self.pause_ev = pause_ev
        self.active = active            # shared number: workers 0 .. active-1 play, the others idle
        self.n_workers = int(n_workers)
        self.min_workers = max(1, min(int(lim.get("heat_min_workers", 4)), self.n_workers or 1))
        self.throttle = bool(lim.get("heat_throttle", True)) and active is not None and self.n_workers > 0
        self.t_add = float(lim.get("heat_add_worker_c", float(lim.get("cpu_temp_pause_c", 92)) - 2.0))
        self.t_throttle = None          # set by CpuShare while a reserving run is alive ([datagen] share_reserve_heat_c)
        self.up = 0
        self.down = 0
        self.min_active = self.n_workers
        self.ceiling = self.n_workers   # lowered by CpuShare ([datagen] share_cpu): the guard adds no worker above it
        self.shared = False             # True when CpuShare is on: it then reports the number of workers playing
        self.changes = 0
        self.temp_c = None
        # No temperature reading (HWiNFO not logging, as after the PC restarts of 2026-11-15): the guard cannot see
        # the owner's 92 C line, so it is careful instead of blind: after blind_checks checks in a row without a
        # reading at most blind_max_workers play until one is back ([limits]; 0 = off, all may play as before).
        bm = int(lim.get("blind_max_workers", 8))
        self.blind_max = 0 if bm <= 0 else max(self.min_workers, min(bm, self.n_workers or bm))
        self.blind_need = max(1, int(lim.get("blind_checks", 3)))
        self.blind_n = 0
        self.blind = False              # True while playing under the blind limit; CpuShare respects it
        self.on = bool(lim.get("heat_guard", True))
        self.t_pause = float(lim.get("cpu_temp_pause_c", 92))
        self.urgent_over = float(lim.get("heat_urgent_over_c", 2.0))   # finding 5; 0 = no urgent step
        self.t_resume = float(lim.get("cpu_temp_resume_c", 80))
        self.need = int(lim.get("heat_checks", 6))
        self.cool_s = float(lim.get("cool_seconds", 180))
        self.speed_drop = float(lim.get("cpu_speed_drop", 0.85))
        self.every = float(lim.get("heat_check_seconds", 20))
        self.last = 0.0
        self.hot = 0
        self.pauses = 0
        self.cpu_max = None
        self.paused_at = None
        self.speeds: list[float] = []
        self.base_speed = None
        self.text = "heat guard starting"

    def _read(self):
        """(is_hot, can_resume, text)"""
        h = read_hwinfo(self.cfg)
        fake = os.environ.get("NNLOOP_FAKE_CPU_FILE")    # test hook: a file holding a pretended temperature
        if fake:
            try:
                with open(fake, encoding="ascii") as fh:
                    h = {"cpu_c": float(fh.read().strip()), "throttle": False}
            except (OSError, ValueError):
                pass
        if h and h.get("cpu_c") is not None:
            t = h["cpu_c"]
            self.temp_c = t
            self.cpu_max = t if self.cpu_max is None else max(self.cpu_max, t)
            return (t >= self.t_pause or bool(h.get("throttle"))), t <= self.t_resume, f"CPU {t:.0f} C"
        self.temp_c = None
        sp = cpu_speed_pct(0.5)
        if sp is None:
            return False, True, "no temperature or speed reading"
        if self.paused_at is None:
            if len(self.speeds) < 9:
                self.speeds.append(sp)
                self.base_speed = sorted(self.speeds)[len(self.speeds) // 2]
        base = self.base_speed or sp
        return sp < self.speed_drop * base, True, f"no temperature log, CPU speed {sp:.0f}% (start {base:.0f}%)"

    def tick(self) -> None:
        if not self.on or time.time() - self.last < self.every:
            return
        self.last = time.time()
        try:
            hot, cool, text = self._read()
        except Exception as e:  # noqa: BLE001
            self.text = f"heat guard error {type(e).__name__}"
            return
        self.text = text
        if self.temp_c is None:
            self.blind_n += 1
            if self.blind_max > 0 and self.throttle and self.blind_n >= self.blind_need:
                now = self.active.value
                if not self.blind or now > self.blind_max:
                    new = min(now, self.blind_max)
                    if new != now:
                        self.active.value = new
                        self.changes += 1
                        self.min_active = min(self.min_active, new)
                    log(f"HEAT GUARD: NO temperature reading on {self.blind_n} checks in a row (is HWiNFO logging to "
                        f"its file?). At most {self.blind_max} of {self.n_workers} self-play workers play until a "
                        f"reading is back ({new} play now, was {now}).")
                self.blind = True
        else:
            if self.blind:
                log(f"HEAT GUARD: the temperature reading is back ({text}). The limit of {self.blind_max} workers "
                    f"for playing without a reading is lifted; workers come back one by one while it stays cool.")
            self.blind = False
            self.blind_n = 0
        if self.paused_at is None:
            if self.throttle and self.temp_c is not None:
                now = self.active.value
                if hot or (self.t_throttle is not None and self.temp_c >= self.t_throttle):
                    self.down, self.up = self.down + 1, 0
                    if now > self.min_workers:
                        self.hot = 0          # no full pause while fewer workers can still be tried
                        # 5 (Opus 2026-11-15 23:40, agent review finding 5; as MatchHeatGuard since 08:57): at
                        # heat_urgent_over_c (2) C or more over the limit act on the FIRST hot check and take 4
                        # workers off (16 -> 4 in 3 checks instead of 6 x 2). [limits] heat_urgent_over_c = 0: off.
                        urgent = self.urgent_over > 0 and self.temp_c >= self.t_pause + self.urgent_over
                        if self.down >= 2 or (urgent and self.down >= 1):
                            new = max(self.min_workers, now - (4 if urgent else 2))
                            self.active.value = new
                            self.down = 0
                            self.changes += 1
                            self.min_active = min(self.min_active, new)
                            log(f"HEAT GUARD: {text}. {new} of {self.n_workers} self-play workers play now (was {now}).")
                        return
                elif self.temp_c <= self.t_add:
                    self.up, self.down = self.up + 1, 0
                    if self.up >= 2 and now < min(self.n_workers, self.ceiling):
                        self.active.value = now + 1
                        self.up = 0
                        self.changes += 1
                        log(f"HEAT GUARD: {text}. {now + 1} of {self.n_workers} self-play workers play now (was {now}).")
                else:
                    self.up = self.down = 0
            self.hot = self.hot + 1 if hot else 0
            if self.hot >= self.need:
                self.pause_ev.set()
                self.paused_at = time.time()
                self.pauses += 1
                self.hot = 0
                log(f"HEAT GUARD: {text} for {self.need} checks in a row. Self-play pauses to cool down "
                    f"(pause number {self.pauses} of this stage).")
        else:
            waited = time.time() - self.paused_at
            if waited >= self.cool_s and cool and not hot:
                self.pause_ev.clear()
                log(f"HEAT GUARD: {text} after {waited:.0f} s of pause. Self-play goes on.")
                self.paused_at = None
            elif waited >= 20 * 60:
                self.pause_ev.clear()
                log(f"HEAT GUARD: still {text} after 20 minutes of pause. Self-play goes on anyway; "
                    f"please check the cooler, the fans and the room temperature.")
                self.paused_at = None

    def status(self) -> str:
        part = ""
        if self.throttle and not self.shared and self.active.value < self.n_workers:
            part = f", {self.active.value} of {self.n_workers} workers playing (heat)"
        blind = f" (NO TEMPERATURE READING: at most {self.blind_max} workers)" if self.blind else ""
        return self.text + part + blind + (" (PAUSED to cool)" if self.paused_at is not None else "")


def share_cap(playing: int, busy: float, own: float, n_threads: int, n_workers: int, min_workers: int) -> int:
    """How many self-play workers may play, given what the PC is doing (all figures in "threads fully used").

    busy = the whole PC, own = this loop's workers and their engines; the rest is other programs (matches, a tuning
    run, anything the owner starts). Rules:
      - other programs use less than one thread: all workers may play;
      - the PC is full (under 0.75 of a thread idle) and others are there: step down by 2, and not above what the
        others leave free (when the PC is full the others are being squeezed, so their real need is higher than
        what is measured; stepping down each check finds it);
      - otherwise: grow into the idle threads, keeping 0.75 of a thread free.
    Never under min_workers, never over n_workers."""
    others = max(0.0, busy - own)
    free = n_threads - busy
    if others < 1.0:
        cap = n_workers
    elif free < 0.75:
        cap = min(playing - 2, int(n_threads - others))
    else:
        cap = playing + int(free - 0.75)
    return max(min_workers, min(n_workers, cap))


class CpuShare:
    """[datagen] share_cpu = true (2026-11-15): self-play makes room for other programs by itself.

    Why: `workers` had to be set by hand to 4 whenever a tuning run or a big match ran beside the loop, and back to
    16 afterwards; a forgotten 4 would leave the loop at a quarter of its speed for good. Now `workers` stays at
    the PC's thread count. Every share_check_seconds (default 30) this measures, with psutil, how many threads
    the whole PC is using and how many of those are this loop's own workers and engines, and sets the number of
    workers that play by share_cap() above (never under share_min_workers, default = heat_min_workers).
    It only ever LOWERS the shared number by itself; it raises it (by 2 a check) only when the heat guard has
    nothing against it (no reading, or at heat_add_worker_c or cooler), and the heat guard never raises it above
    this cap. So the smaller of the two limits holds. No psutil: the feature is off and says so once.
    """

    def __init__(self, cfg: dict, active, n_workers: int, guard: "HeatGuard", worker_pids: list[int]):
        g, lim = cfg["datagen"], (cfg.get("limits") or {})
        self.active, self.n_workers, self.guard, self.pids = active, int(n_workers), guard, list(worker_pids)
        self.on = bool(g.get("share_cpu", False)) and self.n_workers > 0
        guard.shared = self.on
        self.every = float(g.get("share_check_seconds", 30))
        self.min_workers = max(1, min(int(g.get("share_min_workers", lim.get("heat_min_workers", 4))), self.n_workers or 1))
        self.cap = self.n_workers
        self.last = 0.0
        self.prev = None            # (time, system busy seconds, {pid: cpu seconds})
        self.changes = 0
        self.fewest = self.n_workers
        self.others = None
        self.ps = None
        # [datagen] share_reserve_threads + share_reserve_pattern (2026-11-18, the big tune; not set = off): _reserved
        self.reserve_n = int(g.get("share_reserve_threads", 0) or 0)
        pat = str(g.get("share_reserve_pattern", "") or "")
        self.reserve_re = re.compile(pat) if pat and self.reserve_n > 0 else None
        self.reserving = False
        # [datagen] share_reserve_heat_c (2026-11-18, addendum 7 of the big tune; 0 or not set = off): while a reserving
        # run is alive the heat guard takes workers off from this temperature and adds one back only 2 C under it, so
        # self-play yields before the run's own heat pause (91 C); the full pause stays at cpu_temp_pause_c, so
        # self-play still never plays fewer than its floor of workers because of the run.
        self.reserve_heat = float(g.get("share_reserve_heat_c", 0) or 0)
        self.base_add = guard.t_add
        if self.on:
            try:
                import psutil
                self.ps = psutil
                self.n_threads = int(psutil.cpu_count(logical=True) or 1)
            except Exception as e:  # noqa: BLE001
                self.on = guard.shared = False
                log(f"selfplay: share_cpu is set but psutil is not usable ({type(e).__name__}); all {n_workers} workers play")

    def _sample(self):
        ps = self.ps
        t = ps.cpu_times()
        busy = float(t.user + t.system)
        own = {}
        for pid in self.pids:
            try:
                p = ps.Process(pid)
                for q in [p, *p.children(recursive=True)]:
                    try:
                        c = q.cpu_times()
                        own[q.pid] = float(c.user + c.system)
                    except Exception:  # noqa: BLE001
                        pass
            except Exception:  # noqa: BLE001
                pass
        return time.time(), busy, own

    def _reserved(self) -> int:
        """The big tune (owner, 17 November: "the tune is the first user after the loop's own gate and yardstick
        matches: up to 8 games at once. Self-play takes what is left"): while a process whose command line matches
        [datagen] share_reserve_pattern is alive, at least share_reserve_threads threads count as used by others, also
        while that run waits (its heat pause, the loop gate), so self-play does not take them and keep the CPU too hot
        for the run to come back. When the run ends, the reservation ends at the next check."""
        if self.reserve_re is None:
            return 0
        found = any(self.reserve_re.search(" ".join(p.info.get("cmdline") or []))
                    for p in self.ps.process_iter(["cmdline"]))
        if found != self.reserving:
            self.reserving = found
            if self.reserve_heat > 0:
                self.guard.t_throttle = self.reserve_heat if found else None
                self.guard.t_add = min(self.base_add, self.reserve_heat - 2.0) if found else self.base_add
            log(f"CPU SHARE: a reserving run is {'alive' if found else 'gone'} "
                f"({self.reserve_n if found else 0} threads kept for it"
                + (f"; workers come off from {self.reserve_heat:.0f} C" if found and self.reserve_heat > 0 else "") + ")")
        return self.reserve_n if found else 0

    def tick(self) -> None:
        if not self.on or time.time() - self.last < self.every:
            return
        self.last = time.time()
        try:
            now, reserved = self._sample(), self._reserved()
        except Exception as e:  # noqa: BLE001
            log(f"selfplay: share_cpu measurement failed ({type(e).__name__}); leaving the workers as they are")
            return
        prev, self.prev = self.prev, now
        if prev is None or now[0] - prev[0] < 5:
            return
        dt = now[0] - prev[0]
        busy = max(0.0, now[1] - prev[1]) / dt
        own = sum(max(0.0, v - prev[2].get(pid, v)) for pid, v in now[2].items()) / dt
        self.others = max(0.0, busy - own)
        if reserved > self.others:          # a reserving run waits: its threads count as used (see _reserved)
            busy, self.others = own + reserved, float(reserved)
        playing = int(self.active.value)
        self.cap = share_cap(playing, busy, own, self.n_threads, self.n_workers, self.min_workers)
        self.guard.ceiling = self.cap
        # while the heat guard has no temperature reading it allows at most blind_max workers (2026-11-15)
        cap_now = min(self.cap, self.guard.blind_max) if getattr(self.guard, "blind", False) else self.cap
        cap_now = max(self.min_workers, cap_now)
        new = playing
        if playing > cap_now:
            new = cap_now
        elif playing < cap_now and self.guard.paused_at is None and (
                self.guard.temp_c is None or self.guard.temp_c <= self.guard.t_add):
            new = min(cap_now, playing + 2)
        if new != playing:
            self.active.value = new
            self.changes += 1
            self.fewest = min(self.fewest, new)
            log(f"CPU SHARE: other programs use {self.others:.1f} of {self.n_threads} threads. "
                f"{new} of {self.n_workers} self-play workers play now (was {playing}).")

    def status(self) -> str:
        if not self.on or self.others is None:
            return ""
        return f"; others {self.others:.1f} threads, {self.active.value} of {self.n_workers} workers playing"


def generate(cfg: dict, round_no: int, net_path: str | None, out_dir: Path, target: int,
             should_stop=None) -> dict:
    g = cfg["datagen"]
    out_dir.mkdir(parents=True, exist_ok=True)
    salvaged = salvage_parts(out_dir)
    have = count_done(out_dir)
    if salvaged:
        log(f"selfplay: salvaged {salvaged} positions from interrupted files")
    if have >= target:
        log(f"selfplay: already have {have} >= {target} positions")
        return {"positions": have, "backend": "uci_selfplay", "resumed_with": have}
    spec = engine_for_net(cfg, net_path)
    spec_d = {"exe": spec.exe, "options": spec.options, "cwd": spec.cwd}
    workers = int(g["workers"])
    rotate = max(2000, int(g.get("chunk_positions", 250000)) // workers)
    ctx = mp.get_context("spawn")
    n_pos, n_games, n_plies, n_restarts = (ctx.Value("q", 0) for _ in range(4))
    stop_ev = ctx.Event()
    pause_ev = ctx.Event()
    active = ctx.Value("i", workers)
    guard = HeatGuard(cfg, pause_ev, active, workers)
    need = target - have
    log(f"selfplay: round {round_no}, need {need} more positions (have {have}), {workers} workers, "
        f"{('softnodes ' + str(g['soft_nodes'])) if int(g.get('soft_nodes', 0) or 0) > 0 else str(g['nodes']) + ' nodes'}/move, engine {spec.exe}, options {spec.options}")
    procs = []
    for w in range(workers):
        seed = f"{g.get('seed', 1)}-{round_no}-{w}-{time.time_ns()}"
        p = ctx.Process(target=_worker, args=(w, spec_d, cfg, str(out_dir), rotate, seed,
                                              n_pos, n_games, n_plies, n_restarts, stop_ev, pause_ev, active),
                        daemon=True)
        p.start()
        procs.append(p)
    share = CpuShare(cfg, active, workers, guard, [p.pid for p in procs])
    t0 = time.time()
    last_log = t0
    stopped_by_user = False
    try:
        while True:
            time.sleep(2.0)
            done = n_pos.value
            if done >= need:
                break
            if stop_requested(cfg):
                stopped_by_user = True
                break
            if should_stop is not None and should_stop():   # early self-play: the loop's training has ended
                break
            guard.tick()
            share.tick()
            alive = sum(p.is_alive() for p in procs)
            if alive == 0:
                raise RuntimeError("selfplay: all workers died; see errors above")
            if time.time() - last_log >= 60:
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                eta = (need - done) / rate / 60 if rate > 0 else float("inf")
                log(f"selfplay: {have + done}/{target} positions, {n_games.value} games, {rate:.0f} pos/s, "
                    f"{alive}/{workers} workers alive, {n_restarts.value} engine restarts, ETA {eta:.1f} min; "
                    f"{guard.status()}{share.status()}")
                last_log = time.time()
    finally:
        stop_ev.set()
        deadline = time.time() + 180
        for p in procs:
            p.join(timeout=max(1, deadline - time.time()))
        for p in procs:
            if p.is_alive():
                p.terminate()
        # 10 (Opus 2026-11-15 23:40, agent review finding 10): TerminateProcess returns before the process is gone;
        # wait for each (at most 10 s) so that no worker still holds its .part file open while it is salvaged
        for p in procs:
            p.join(timeout=10)
    salvage_parts(out_dir)
    el = time.time() - t0
    total = count_done(out_dir)
    stats = {"positions": total, "new_positions": n_pos.value, "games": n_games.value,
             "plies": n_plies.value, "seconds": round(el, 1),
             "pos_per_s": round(n_pos.value / el, 1) if el > 0 else 0,
             "engine_restarts": n_restarts.value, "backend": "uci_selfplay", "workers": workers,
             "nodes": int(g["nodes"]), "soft_nodes": int(g.get("soft_nodes", 0) or 0), "net": str(net_path),
             "cooling_pauses": guard.pauses, "cpu_c_max": guard.cpu_max,
             "heat_worker_changes": guard.changes, "heat_fewest_workers": guard.min_active,
             "workers_playing_at_end": active.value,
             "share_cpu": share.on, "share_worker_changes": share.changes, "share_fewest_workers": share.fewest}
    log(f"selfplay: finished with {total} positions in {el:.0f} s ({stats['pos_per_s']} pos/s, "
        f"{n_games.value} games, {n_restarts.value} engine restarts)")
    if stopped_by_user:
        raise StopRequested("STOP file found during self-play")
    return stats


# [datagen] early_selfplay (Opus 2026-11-17; off unless true): while the loop trains round r on the card, the
# processor plays round r + 1's self-play with the best net of that moment into round r + 1's raw folder. Round
# r + 1's generate() counts those positions (salvage_parts + count_done) and plays only the rest. The child waits for
# the trainer's "data ready" line first (the data load is a heat and memory step of its own) and stops at the end of
# the train stage (its stop file), on the loop's STOP file, or after early_selfplay_max_minutes. run.py's job object
# kills the child and its workers if run.py dies.
class EarlySelfplay:
    def __init__(self, cfg: dict, round_no: int, net_path, out_dir: Path, target: int, train_log: Path):
        g = cfg["datagen"]
        self.on = bool(g.get("early_selfplay", False)) and g.get("backend") == "uci_selfplay"
        self.args = (cfg, round_no, net_path, Path(out_dir), int(target), Path(train_log))
        self.proc = None

    def __enter__(self):
        if not self.on:
            return self
        cfg, r, net, out, target, tlog = self.args
        out.mkdir(parents=True, exist_ok=True)
        self.stop = out.parent / f"early_selfplay.stop_{os.getpid()}_{time.time_ns()}"
        offset = tlog.stat().st_size if tlog.exists() else 0
        minutes = float(cfg["datagen"].get("early_selfplay_max_minutes", 150))
        self.proc = mp.get_context("spawn").Process(
            target=_early_child, args=(cfg["_config_path"], r, net, str(out), target, str(tlog), offset,
                                       str(self.stop), minutes, str(_log_path(cfg))))
        self.proc.start()
        log(f"early self-play: round {r} starts beside the training (pid {self.proc.pid}, net {net}, "
            f"after the trainer's data ready line)")
        return self

    def __exit__(self, *exc):
        if self.proc is None:
            return False
        self.stop.write_text("stop\n", encoding="ascii")
        self.proc.join(timeout=420)            # generate() joins its workers within 190 s
        if self.proc.is_alive():
            log(f"WARNING: early self-play: the child {self.proc.pid} did not end within 420 s; terminated")
            self.proc.terminate()
            self.proc.join(timeout=10)
        self.stop.unlink(missing_ok=True)
        log(f"early self-play: round {self.args[1]} stopped (exit code {self.proc.exitcode}); "
            f"{count_done(self.args[3])} positions on disk")
        return False                           # never hides the training's own error


def _log_path(cfg: dict) -> Path:
    from .common import _LOG_FILE
    return _LOG_FILE if _LOG_FILE is not None else Path(cfg["paths"]["runs"]) / "pipeline.log"


def _early_child(config_path: str, r: int, net, out: str, target: int, tlog: str, offset: int, stop: str,
                 minutes: float, log_path: str) -> None:
    import json
    from .common import load_config, set_log_file
    set_log_file(Path(log_path))
    cfg = load_config(config_path)
    t0 = time.time()
    stop_p = Path(stop)

    def should_stop() -> bool:
        return stop_p.exists() or time.time() - t0 > minutes * 60

    while True:                               # the trainer appends to train.log: read only what came after offset
        if should_stop() or stop_requested(cfg):
            log(f"early self-play: round {r} ended before the training's data was ready")
            return
        try:
            with open(tlog, "rb") as fh:
                fh.seek(offset)
                if b"data ready" in fh.read():
                    break
        except OSError:
            pass
        time.sleep(5)
    try:
        stats = generate(cfg, r, net, Path(out), target, should_stop=should_stop)
    except StopRequested:                     # the loop's STOP file: the positions so far stay for round r
        log(f"early self-play: round {r} ended by the STOP file; {count_done(Path(out))} positions on disk")
        return
    stats["early"] = True
    with open(Path(out).parent / "early_selfplay.json", "a", encoding="ascii") as fh:
        fh.write(json.dumps({"stopped": time.strftime("%Y-%m-%d %H:%M:%S"), **stats}) + "\n")
