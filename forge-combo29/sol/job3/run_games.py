#!/usr/bin/env python3
"""Play and replay the four pinned Forge PC20 arms from Job 3."""

import argparse
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import chess

# Reuse Job 2's driver in the scratch layout and in the reported layout.
script_parent = Path(__file__).resolve().parent.parent
for job2_dir in (script_parent / "job2", script_parent / "sol-job2"):
    if (job2_dir / "run_matrix.py").is_file():
        sys.path.insert(0, str(job2_dir))
        break
from run_matrix import Engine, PC20, Refused, parse_row, utc_now

MAX_PLY = 60
ARMS = {
    "A": (True, "go softnodes 2000"),
    "B": (True, "go nodes 20000"),
    "C": (False, "go softnodes 2000"),
    "D": (False, "go nodes 20000"),
}


@dataclass(frozen=True)
class Game:
    index: int
    fen: str
    moves: tuple
    reason: str

    def tsv(self):
        return f"{self.index}\t{self.fen}\t{' '.join(self.moves)}\t{self.reason}\n"


def start_board(fen):
    if "\t" in fen or len(fen.split()) != 6:
        raise ValueError(f"expected one six-field FEN without tabs: {fen}")
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError(f"invalid starting position: {fen}")
    return board


def stop_reason(board, ply):
    if not board.legal_moves:
        return "checkmate" if board.is_check() else "stalemate"
    if board.is_repetition(3):
        return "threefold_repetition"
    if board.halfmove_clock >= 100:
        return "fifty_move_rule"
    if board.is_insufficient_material():
        return "insufficient_material"
    if ply >= MAX_PLY:
        return "60_ply_limit"
    return None


def play_legal(board, move_text, game, ply):
    try:
        move = chess.Move.from_uci(move_text)
    except ValueError as error:
        raise RuntimeError(f"game {game}, ply {ply}: malformed move {move_text}") from error
    if move not in board.legal_moves:
        raise RuntimeError(f"game {game}, ply {ply}: illegal move {move_text}")
    board.push(move)


def read_games(path):
    games = []
    for expected_index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError(f"games line {expected_index}: expected four tab-separated fields")
        index, fen, moves_field, reason = fields
        if index != str(expected_index):
            raise ValueError(f"expected game index {expected_index}, got {index}")
        moves = tuple(moves_field.split())
        board = start_board(fen)
        for ply, move in enumerate(moves):
            ended = stop_reason(board, ply)
            if ended:
                raise ValueError(f"game {index} continued after ply {ply} ({ended})")
            play_legal(board, move, index, ply)
        expected_reason = stop_reason(board, len(moves))
        if expected_reason is None or reason != expected_reason:
            raise ValueError(f"game {index}: expected end reason {expected_reason!r}, got {reason!r}")
        games.append(Game(int(index), fen, moves, reason))
    if not games:
        raise ValueError("game list is empty")
    return games


def read_openings(path, limit):
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < limit:
        raise ValueError(f"expected at least {limit} openings, got {len(lines)}")
    openings = lines[:limit]
    for fen in openings:
        start_board(fen)
    return openings


def reset_tables(engine):
    engine.send("ucinewgame")
    engine.send("isready")
    engine.until("readyok")


def run(args):
    generating = args.command == "play"
    arm = "A" if generating else args.arm
    warm, search = ARMS[arm]
    executable = args.engine.resolve(strict=True)
    input_path = (args.openings if generating else args.games).resolve(strict=True)
    # Check replay legality and first terminal before starting all expensive runs.
    if generating:
        work = [Game(i, fen, (), "") for i, fen in enumerate(read_openings(input_path, args.limit), start=1)]
    else:
        work = read_games(input_path)

    outputs = [args.rows, args.rows.with_name(args.rows.name + ".meta")]
    if generating:
        outputs.append(args.games)
    if len(set(path.resolve() for path in outputs)) != len(outputs):
        raise ValueError("row, sidecar and games outputs must have different names")
    for path in outputs:
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "command": sys.argv,
        "arm": arm,
        "warm": warm,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "reset_commands": ["ucinewgame", "isready"],
        "reset_frequency": "once per game" if warm else "once per search",
        "position_command": "position fen <O line> [moves <preceding moves>]",
        "external_net_file": None,
        "input": str(input_path),
        "input_sha256": sha256(input_path.read_bytes()).hexdigest(),
        "python_chess": chess.__version__,
        "games_requested": len(work),
        "games_completed": 0,
        "positions_completed": 0,
        "last_info_nodes_sum": 0,
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    current_game, current_ply = None, None
    with ExitStack() as stack:
        rows = stack.enter_context(outputs[0].open("x", encoding="utf-8"))
        metadata = stack.enter_context(outputs[1].open("x", encoding="utf-8"))
        game_log = stack.enter_context(outputs[2].open("x", encoding="utf-8")) if generating else None
        try:
            with Engine(executable, args.timeout) as engine:
                engine.send("uci")
                meta["id_name"] = next(
                    (line for line in engine.until("uciok") if line.startswith("id name ")),
                    None,
                )
                if meta["id_name"] is None:
                    raise RuntimeError("missing engine id name")
                for name, value in (("Threads", "1"), ("Hash", "16"), *PC20):
                    setting = f"setoption name {name} value {value}"
                    engine.send(setting)
                    meta["settings_sent"].append(setting)
                engine.send("isready")
                engine.until("readyok")
                for game in work:
                    current_game, current_ply = game.index, None
                    if warm:
                        reset_tables(engine)
                    board = start_board(game.fen) if generating else None
                    moves = []
                    max_ply = MAX_PLY if generating else len(game.moves)
                    for ply in range(max_ply):
                        current_ply = ply
                        if generating and stop_reason(board, ply):
                            break
                        if not warm:
                            reset_tables(engine)
                        position = f"position fen {game.fen}"
                        if moves:
                            position += " moves " + " ".join(moves)
                        engine.send(position)
                        engine.send(search)
                        row = parse_row(
                            meta["positions_completed"] + 1, game.fen,
                            engine.until("bestmove"), require_counter=True,
                        )
                        row.update(game=game.index, ply=ply)
                        if generating:
                            move = row["bestmove"]
                            play_legal(board, move, game.index, ply)
                        else:
                            move = game.moves[ply]
                        moves.append(move)
                        rows.write(json.dumps(row, separators=(",", ":")) + "\n")
                        rows.flush()
                        meta["positions_completed"] += 1
                        meta["last_info_nodes_sum"] += row["nodes"]
                    if generating:
                        reason = stop_reason(board, len(moves))
                        if reason is None:
                            raise RuntimeError(f"game {game.index} lacks an end reason")
                        game_log.write(Game(game.index, game.fen, tuple(moves), reason).tsv())
                        game_log.flush()
                    meta["games_completed"] += 1
            meta["status"] = "complete"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error) or type(error).__name__
            meta["failure_game"] = current_game
            meta["failure_ply"] = current_ply
            print(
                f"arm {arm}: {meta['status']} at game {current_game}, ply {current_ply}: {meta['error']}",
                file=sys.stderr,
            )
        finally:
            meta["end_utc"] = utc_now()
            if generating:
                meta["games_sha256"] = sha256(outputs[2].read_bytes()).hexdigest()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    print(f"arm {arm}: {meta['status']}, {meta['games_completed']}/{len(work)} games, "
          f"{meta['positions_completed']} searches")
    return 0 if meta["status"] == "complete" else 1


def verify(args):
    openings = read_openings(args.openings, args.limit)
    games = read_games(args.games)
    if [game.fen for game in games] != openings:
        raise ValueError(f"game FENs do not match the first {args.limit} opening lines")
    counts = {}
    for game in games:
        counts[game.reason] = counts.get(game.reason, 0) + 1
    print(json.dumps({
        "games_verified": len(games),
        "legal_plies_verified": sum(len(game.moves) for game in games),
        "end_reasons": counts,
        "games_sha256": sha256(args.games.read_bytes()).hexdigest(),
    }, sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    play = commands.add_parser("play", help="generate an arm A game list and search rows")
    play.add_argument("engine", type=Path)
    play.add_argument("openings", type=Path)
    play.add_argument("games", type=Path)
    play.add_argument("rows", type=Path)
    play.add_argument("--limit", type=int, default=100)
    play.add_argument("--timeout", type=float, default=15)

    replay = commands.add_parser("replay", help="replay arm A positions on arm B, C or D")
    replay.add_argument("arm", choices=("B", "C", "D"))
    replay.add_argument("engine", type=Path)
    replay.add_argument("games", type=Path)
    replay.add_argument("rows", type=Path)
    replay.add_argument("--timeout", type=float, default=15)

    check = commands.add_parser("verify", help="verify openings, moves and end reasons without an engine")
    check.add_argument("openings", type=Path)
    check.add_argument("games", type=Path)
    check.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()
    if getattr(args, "timeout", 15) <= 0 or not 1 <= getattr(args, "limit", 100) <= 100:
        parser.error("timeout must be positive and limit must be between 1 and 100")
    return verify(args) if args.command == "verify" else run(args)


if __name__ == "__main__":
    raise SystemExit(main())
