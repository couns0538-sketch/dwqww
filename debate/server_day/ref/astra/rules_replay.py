"""Home rules reference for the frozen Forge selfgame command. Requires chess==1.11.2.

check_game verifies chess semantics using an independently obtained reservation.
A caller verifies custody, binding, score transport and duplicate ownership separately.
The CLI reads native raw records and publishes a rules-only JSONL file in a new folder.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

import chess

ENDINGS = ("mate", "stalemate", "rule", "plylimit", "matescore", "evallimit", "drawadj")
GAME = re.compile(r"[a-z0-9]{1,32}-w[0-9]{3}-g([0-9]{8})")
MOVE = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?")
NUMBER = r"(?:0|[1-9][0-9]*)"
SCORE = rf"(?:0|-?[1-9][0-9]*)"
FEN = r"\S+ [wb] \S+ \S+ [0-9]+ [0-9]+"
ROW = re.compile(rf"sg ({NUMBER}) ({SCORE}) ({MOVE.pattern}) ({FEN})")
END = re.compile(rf"sgend result (-1|0|1) reason ({'|'.join(ENDINGS)}) plies ({NUMBER}) "
                 rf"run ({NUMBER}) searches ({NUMBER}) nodes ({NUMBER}) fen ({FEN}) moves((?: {MOVE.pattern})*)")
# loop/source/src/uci.cpp with the frozen manifest's selfgame_line.
FROZEN_GAME = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
MAX_PLY, WRITE_PLY, DRAW_PLY, DRAW_SCORE, DRAW_COUNT, EVAL_LIMIT = 300, 8, 80, 5, 8, 2000


class ReplayError(ValueError):
    """The reservation or game failed a rules check."""


def require(ok, message):
    if not ok:
        raise ReplayError(message)


def game_number(gid):
    match = GAME.fullmatch(gid)
    require(match is not None and int(match[1]) > 0, "invalid game identity")
    return int(match[1])


def reserve(gid, *, seed=None, fixed=None):
    """Return the legal reserved moves and whether the opening loop reached its requested length."""
    game_number(gid)
    require((seed is None) != (fixed is None), "choose one independent reservation source")
    if seed is not None:
        require(isinstance(seed, str) and seed.isascii() and seed, "invalid root seed")
    else:
        require(len(fixed) <= MAX_PLY and all(MOVE.fullmatch(m) for m in fixed), "invalid fixed opening")
    board = chess.Board()
    moves = []
    for ply in range(8 if fixed is None else len(fixed)):
        legal = sorted(m.uci() for m in board.legal_moves)
        if not legal:
            return gid, moves, False
        if fixed is None:
            digest = hashlib.sha256(f"{seed}|{gid}|{ply}".encode("ascii")).digest()
            token = legal[int.from_bytes(digest[:8], "big") % len(legal)]
        else:
            token = fixed[ply]
            require(token in legal, "illegal move in fixed reservation")
        moves.append(token)
        board.push_uci(token)
    return gid, moves, True


def read_games(source):
    """Stream ASCII/LF native record envelopes, at most one game buffered."""
    game = None
    for number, data in enumerate(iter(lambda: source.readline(65537), b""), 1):
        require(len(data) <= 65536 and data.endswith(b"\n"), f"line {number}: long or missing LF")
        try:
            line = data[:-1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ReplayError(f"line {number}: non-ASCII data") from exc
        require(line.isprintable() and line, f"line {number}: control byte or empty line")
        kind, _, value = line.partition(" ")
        if kind == "game" and game is None:
            words = line.split(" ")
            require(len(words) >= 3 and words[2] == "opening", "invalid game header")
            game_number(words[1])
            require(len(words[3:]) <= MAX_PLY and all(MOVE.fullmatch(m) for m in words[3:]), "invalid opening tokens")
            game = {"id": words[1], "opening": words[3:], "sent": None, "rows": [], "end": None}
        elif game is not None and kind == "sent" and game["sent"] is None:
            game["sent"] = value
        elif game is not None and game["sent"] is not None and game["end"] is None and kind == "sg":
            require(len(game["rows"]) <= MAX_PLY, "too many rows")
            game["rows"].append(line)
        elif game is not None and game["sent"] is not None and game["end"] is None and kind in ("sgend", "openingend"):
            game["end"] = line
        elif game is not None and game["end"] is not None and kind == "bind":
            require(re.fullmatch(r"[a-f0-9]{64}", value), "invalid binding field")
            yield game
            game = None
        else:
            raise ReplayError(f"line {number}: unexpected {kind!r} in record")
    require(game is None, "incomplete record at EOF")


def legal_move(board, token):
    try:
        move = board.parse_uci(token)
    except ValueError as exc:
        raise ReplayError("move is illegal on the replayed board: " + token) from exc
    # python-chess also accepts Chess960 UCI spellings for standard castling.
    require(move and move.uci() == token, "noncanonical standard-chess move: " + token)
    return move


def check_game(game, reservation, *, game_line):
    """Return a rules verdict. The caller owns the exact input bytes and credit decisions."""
    require(game_line == FROZEN_GAME, "different selfgame policy requires review")
    reserved_id, moves, completed_opening = reservation
    require(game["id"] == reserved_id, "reservation belongs to another logical id")
    require(game["opening"] == moves, "record differs from independent reservation")
    board = chess.Board()
    occurrences = Counter()
    fen = board.fen()
    occurrences[fen.rsplit(" ", 2)[0]] += 1

    def advance(move):
        board.push(move)
        position = board.fen()
        occurrences[position.rsplit(" ", 2)[0]] += 1
        return position

    for opening_move in moves:
        fen = advance(legal_move(board, opening_move))
    if not completed_opening:
        require(game["sent"] == "none" and game["rows"] == []
                and game["end"] == f"openingend plies {len(moves)} reason nomoves"
                and not any(board.legal_moves), "early opening end is inconsistent")
        return {"id": game["id"], "state": "noselfgame", "reason": "nomoves", "rows": 0, "moves": 0, "searches": 0}

    sent = "position startpos" + (" moves " + " ".join(moves) if moves else "")
    require(game["sent"] == sent, "sent position differs from reservation")
    end = END.fullmatch(game["end"])
    require(end is not None, "invalid selfgame end line")
    result, reason = int(end[1]), end[2]
    plies, end_run, searches, nodes = map(int, end.group(3, 4, 5, 6))
    played = end[8].split()
    extra_search = reason in ("matescore", "evallimit", "drawadj")
    require(plies == len(moves) + len(played) and plies <= MAX_PLY, "incorrect number of plies")
    require(searches == len(played) + int(extra_search) and nodes >= searches and (searches or nodes == 0), "incorrect search count or nodes")
    written = max(0, plies - max(len(moves), WRITE_PLY)) + int(reason == "drawadj" and plies >= WRITE_PLY)
    rows = game["rows"]
    require(len(rows) == written, "incorrect number of written rows")

    def rule_draw():
        return board.halfmove_clock >= 100 or occurrences[fen.rsplit(" ", 2)[0]] >= 3 or board.is_insufficient_material()

    row_index = draw_run = 0
    for step in range(len(played) + int(reason == "drawadj")):
        ply = board.ply()
        require(ply < MAX_PLY and not rule_draw(), "game continued past a rules ending")
        terminal_decision = step == len(played)
        if ply >= WRITE_PLY:
            row = ROW.fullmatch(rows[row_index])
            require(row is not None, "invalid row")
            row_index += 1
            require(int(row[1]) == ply and row[4] == fen, "wrong row ply or FEN")
            score, token = int(row[2]), row[3]
            require(abs(score) < EVAL_LIMIT, "row emitted beyond evaluation limit")
            require(terminal_decision or token == played[step], "row move differs from played move")
            draw_run = draw_run + 1 if ply >= DRAW_PLY and abs(score) <= DRAW_SCORE else 0
            require((draw_run == DRAW_COUNT) == terminal_decision, "draw adjudication at wrong decision")
        else:
            require(not terminal_decision, "draw before writable plies")
            token = played[step]
        move = legal_move(board, token)
        if not terminal_decision:
            fen = advance(move)
    require(fen == end[7] and end_run == draw_run, "incorrect terminal FEN or draw counter")
    if not any(board.legal_moves):
        expected = "mate" if board.is_check() else "stalemate"
    elif rule_draw():
        expected = "rule"
    elif plies == MAX_PLY:
        expected = "plylimit"
    else:
        require(reason in ("drawadj", "matescore", "evallimit"), "terminal reason disagrees with the board")
        expected = reason
    require(reason == expected, "terminal reason disagrees with the board")
    if reason == "mate":
        require(result == (-1 if board.turn == chess.WHITE else 1), "wrong mate result")
    elif reason in ("matescore", "evallimit"):
        require(result in (-1, 1), "score ending claims a draw")
    else:
        require(result == 0, "draw ending claims a win")
    return {"id": game["id"], "state": "done", "reason": reason, "rows": len(rows), "moves": len(played), "searches": searches}


def unique_fields(pairs):
    fields = dict(pairs)
    require(len(fields) == len(pairs), "duplicate manifest key")
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="the qualified producing workload manifest")
    parser.add_argument("--manifest-sha256", required=True, help="digest pinned by the independent run record")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--root-seed")
    group.add_argument("--fixed-openings", type=Path)
    args = parser.parse_args()
    try:
        require(chess.__version__ == "1.11.2", "this reference was qualified with chess==1.11.2")
        manifest = args.manifest.read_bytes()
        require(hashlib.sha256(manifest).hexdigest() == args.manifest_sha256, "producing manifest digest mismatch")
        metadata = json.loads(manifest.decode("utf-8"), object_pairs_hook=unique_fields)
        require(isinstance(metadata, dict) and metadata.get("selfgame_line") == FROZEN_GAME, "different producing policy")
        args.work_dir.mkdir(exist_ok=False)
        table = None
        if args.fixed_openings:
            table = [line.split() for line in args.fixed_openings.read_text(encoding="ascii").splitlines()]
            require(table and all(table), "empty fixed opening table")
        staged = args.work_dir / "rules.inprogress"
        with args.raw.open("rb") as source, staged.open("x", encoding="ascii", newline="\n") as dest:
            count = 0
            for game in read_games(source):
                fixed = None if table is None else table[(game_number(game["id"]) - 1) % len(table)]
                reserved = reserve(game["id"], seed=args.root_seed, fixed=fixed)
                verdict = check_game(game, reserved, game_line=metadata["selfgame_line"])
                dest.write(json.dumps(verdict, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
            require(count > 0, "empty piece")
        staged.rename(args.work_dir / "rules.jsonl")
    except (ReplayError, OSError, UnicodeError, ValueError) as exc:
        print("Rules check stopped:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
