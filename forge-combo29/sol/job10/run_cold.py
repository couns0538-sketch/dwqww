#!/usr/bin/env python3
"""Run an inclusive slice of Job 10's 1,800 cold replay positions."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

work = Path(__file__).resolve().parent.parent
for job3 in (work / "job3", work / "sol-job3"):
    if (job3 / "run_games.py").is_file():
        sys.path.insert(0, str(job3))
        break
else:
    raise SystemExit("Job 3 run_games.py is missing from the adjacent job3 or sol-job3 directory")
from run_games import read_games, reset_tables
from run_matrix import Engine, PC20, Refused, parse_row, utc_now


def run(args):
    executable = args.engine.resolve(strict=True)
    game_file = args.games.resolve(strict=True)
    games = read_games(game_file)[:30]
    positions = [(game, ply) for game in games for ply in range(len(game.moves))]
    if len(games) != 30 or len(positions) != 1800:
        raise ValueError("the first 30 games must contain exactly 1,800 positions")
    selected = positions[args.first - 1:args.last]
    sidecar = args.rows.with_name(args.rows.name + ".meta")
    if args.rows.exists() or sidecar.exists():
        raise FileExistsError(f"refusing to overwrite {args.rows} or its sidecar")
    args.rows.parent.mkdir(parents=True, exist_ok=True)

    search = f"go {args.kind} {args.budget}"
    regime = "hard" if args.kind == "nodes" else "soft"
    settings = [f"setoption name {name} value {value}" for name, value in
                (("Threads", "1"), ("Hash", "16"), *PC20)]
    meta = {
        "protocol": f"cold-{regime}",
        "regime": regime,
        "warm": False,
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "kind": args.kind,
        "budget": args.budget,
        "timeout_seconds": args.timeout,
        "reset_commands": ["ucinewgame", "isready"],
        "reset_frequency": "once per search",
        "position_command": "position fen <O line> [moves <preceding recorded moves>]",
        "external_net_file": None,
        "input": str(game_file),
        "input_sha256": sha256(game_file.read_bytes()).hexdigest(),
        "first": args.first,
        "last": args.last,
        "positions_requested": len(selected),
        "positions_completed": 0,
        "last_info_nodes_sum": 0,
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    current_index, current_game, current_ply = None, None, None
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
                for setting in settings:
                    engine.send(setting)
                    meta["settings_sent"].append(setting)
                engine.send("isready")
                engine.until("readyok")
                for index, (game, ply) in enumerate(selected, start=args.first):
                    current_index, current_game, current_ply = index, game.index, ply
                    reset_tables(engine)
                    position = f"position fen {game.fen}"
                    if ply:
                        position += " moves " + " ".join(game.moves[:ply])
                    engine.send(position)
                    engine.send(search)
                    row = parse_row(index, game.fen, engine.until("bestmove"), require_counter=True)
                    row.update(game=game.index, ply=ply)
                    rows.write(json.dumps(row, separators=(",", ":")) + "\n")
                    rows.flush()
                    meta["positions_completed"] += 1
                    meta["last_info_nodes_sum"] += row["nodes"]
            meta["status"] = "complete"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error) or type(error).__name__
            meta["failure_index"] = current_index
            meta["failure_game"] = current_game
            meta["failure_ply"] = current_ply
            print(f"{search}: {meta['status']} at position {current_index}: {meta['error']}", file=sys.stderr)
        finally:
            meta["end_utc"] = utc_now()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    print(f"{search}, positions {args.first}–{args.last}: {meta['status']}, "
          f"{meta['positions_completed']}/{meta['positions_requested']} searches")
    return 0 if meta["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("games", type=Path)
    parser.add_argument("rows", type=Path)
    parser.add_argument("--kind", choices=("nodes", "softnodes"), required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int, default=1800)
    parser.add_argument("--timeout", type=float, default=60, help="seconds per UCI response")
    args = parser.parse_args()
    if not 1 <= args.first <= args.last <= 1800:
        parser.error("require 1 <= first <= last <= 1800")
    if args.budget <= 0 or args.timeout <= 0:
        parser.error("budget and timeout must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
