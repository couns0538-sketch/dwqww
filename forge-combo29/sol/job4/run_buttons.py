#!/usr/bin/env python3
"""Replay Forge Job 3 games with the specified Job 4 table resets."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

# The scratch and recorded repository layouts use different directory names.
work = Path(__file__).resolve().parent.parent
for job3_dir in (work / "job3", work / "sol-job3"):
    if (job3_dir / "run_games.py").is_file():
        sys.path.insert(0, str(job3_dir))
        break
from run_games import read_games, reset_tables
from run_matrix import Engine, PC20, Refused, parse_row, utc_now

SOFT = "go softnodes 2000"
HARD = "go nodes 20000"
COLD = ("ucinewgame",)
HASH = ("setoption name Clear Hash",)
WORKERS = ("setoption name ClearWorkers",)
PAWNS = ("setoption name ClearPawnCache",)
ARMS = {
    "A2": (SOFT, ()),
    "B2": (HARD, ()),
    "C2": (SOFT, COLD),
    "D2": (HARD, COLD),
    "E": (SOFT, HASH),
    "F": (SOFT, WORKERS),
    "G": (SOFT, PAWNS),
    "H": (SOFT, WORKERS + HASH),
    "EH": (HARD, HASH),
    "FH": (HARD, WORKERS),
}


def run(args):
    search, buttons = ARMS[args.arm]
    executable = args.engine.resolve(strict=True)
    game_file = args.games.resolve(strict=True)
    games = read_games(game_file)
    sidecar = args.rows.with_name(args.rows.name + ".meta")
    if args.rows.exists() or sidecar.exists():
        raise FileExistsError(f"refusing to overwrite {args.rows} or its sidecar")
    args.rows.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "arm": args.arm,
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "reset_per_game": ["ucinewgame", "isready"],
        "commands_per_ply_before_position": [*buttons, "isready"],
        "position_command": "position fen <O line> [moves <preceding recorded moves>]",
        "external_net_file": None,
        "input": str(game_file),
        "input_sha256": sha256(game_file.read_bytes()).hexdigest(),
        "games_requested": len(games),
        "positions_requested": sum(len(game.moves) for game in games),
        "games_completed": 0,
        "positions_completed": 0,
        "last_info_nodes_sum": 0,
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    current_game, current_ply = None, None
    with args.rows.open("x", encoding="utf-8") as rows, sidecar.open("x", encoding="utf-8") as metadata:
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
                for game in games:
                    current_game, current_ply = game.index, None
                    reset_tables(engine)
                    for ply in range(len(game.moves)):
                        current_ply = ply
                        for command in buttons:
                            engine.send(command)
                        engine.send("isready")
                        engine.until("readyok")
                        position = f"position fen {game.fen}"
                        if ply:
                            position += " moves " + " ".join(game.moves[:ply])
                        engine.send(position)
                        engine.send(search)
                        row = parse_row(
                            meta["positions_completed"] + 1, game.fen,
                            engine.until("bestmove"), require_counter=True,
                        )
                        row.update(game=game.index, ply=ply)
                        rows.write(json.dumps(row, separators=(",", ":")) + "\n")
                        rows.flush()
                        meta["positions_completed"] += 1
                        meta["last_info_nodes_sum"] += row["nodes"]
                    meta["games_completed"] += 1
            meta["status"] = "complete"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error) or type(error).__name__
            meta["failure_game"] = current_game
            meta["failure_ply"] = current_ply
            print(
                f"arm {args.arm}: {meta['status']} at game {current_game}, ply {current_ply}: {meta['error']}",
                file=sys.stderr,
            )
        finally:
            meta["end_utc"] = utc_now()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    print(f"arm {args.arm}: {meta['status']}, {meta['games_completed']}/{len(games)} games, "
          f"{meta['positions_completed']}/{meta['positions_requested']} searches")
    return 0 if meta["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=ARMS)
    parser.add_argument("engine", type=Path)
    parser.add_argument("games", type=Path)
    parser.add_argument("rows", type=Path)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
