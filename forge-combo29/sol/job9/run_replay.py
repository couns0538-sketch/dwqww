#!/usr/bin/env python3
"""Replay the first 30 games for Job 9's history-mask and table controls."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

work = Path(__file__).resolve().parent.parent
for job5 in (work / "job5", work / "sol-job5"):
    if (job5 / "run_variants.py").is_file():
        sys.path.insert(0, str(job5))
        break
else:
    raise SystemExit("Job 5 run_variants.py is missing from the adjacent job5 or sol-job5 directory")
from run_variants import BUDGETS, VariantEngine
from run_games import read_games, reset_tables
from run_matrix import PC20, Refused, parse_row, utc_now

PROTOCOLS = {"warm-soft": "soft", "warm-hard": "hard"}
BUTTONS = ("Clear Hash", "ClearWorkers")


def run(args):
    regime = PROTOCOLS[args.protocol]
    search = BUDGETS[regime]
    executable = args.engine.resolve(strict=True)
    game_file = args.games.resolve(strict=True)
    games = read_games(game_file)[:30]
    if len(games) != 30 or sum(len(game.moves) for game in games) != 1800:
        raise ValueError("the first 30 games must contain exactly 1,800 positions")
    if args.opening_only and any(not game.moves for game in games):
        raise ValueError("every game must have a playable opening position")

    sidecar = args.rows.with_name(args.rows.name + ".meta")
    if args.rows.exists() or sidecar.exists():
        raise FileExistsError(f"refusing to overwrite {args.rows} or its sidecar")
    args.rows.parent.mkdir(parents=True, exist_ok=True)

    settings = [f"setoption name {name} value {value}" for name, value in
                (("Threads", "1"), ("Hash", "16"), *PC20)]
    variants = [{"name": name, "value": value} for name, value in args.options]
    button_commands = [f"setoption name {name}" for name in args.buttons]
    meta = {
        "protocol": args.protocol,
        "regime": regime,
        "warm": True,
        "opening_only": args.opening_only,
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "reset_commands": ["ucinewgame", "isready"],
        "reset_frequency": "once per game",
        "position_command": "position fen <O line> [moves <preceding recorded moves>]",
        "external_net_file": None,
        "variant": variants[0] if len(variants) == 1 else None,
        "variants": variants,
        "variant_reply": [],
        "variant_replies": [],
        "button_commands": button_commands,
        "commands_per_ply_before_position": [*button_commands, "isready"] if button_commands else [],
        "input": str(game_file),
        "input_sha256": sha256(game_file.read_bytes()).hexdigest(),
        "games_requested": 30,
        "positions_requested": 30 if args.opening_only else 1800,
        "games_completed": 0,
        "positions_completed": 0,
        "last_info_nodes_sum": 0,
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    current_game, current_ply = None, None
    with args.rows.open("x", encoding="utf-8") as rows, sidecar.open("x", encoding="utf-8") as metadata:
        try:
            with VariantEngine(executable, args.timeout) as engine:
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
                for variant in variants:
                    setting = f"setoption name {variant['name']} value {variant['value']}"
                    reply = {"command": setting, "lines": []}
                    meta["variant_replies"].append(reply)
                    engine.send(setting)
                    meta["settings_sent"].append(setting)
                    engine.send("isready")
                    try:
                        engine.wait_for_variant(reply["lines"])
                    finally:
                        meta["variant_reply"].extend(reply["lines"])
                for game in games:
                    current_game, current_ply = game.index, None
                    reset_tables(engine)
                    for ply in range(1 if args.opening_only else len(game.moves)):
                        current_ply = ply
                        if button_commands:
                            for command in button_commands:
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
            print(f"{args.protocol}: {meta['status']}: {meta['error']}", file=sys.stderr)
        finally:
            meta["end_utc"] = utc_now()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    print(f"{args.protocol}: {meta['status']}, {meta['games_completed']}/30 games, "
          f"{meta['positions_completed']}/{meta['positions_requested']} searches")
    return 0 if meta["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", choices=PROTOCOLS)
    parser.add_argument("engine", type=Path)
    parser.add_argument("games", type=Path)
    parser.add_argument("rows", type=Path)
    parser.add_argument("--set", dest="options", nargs=2, action="append", default=[], metavar=("NAME", "VALUE"))
    parser.add_argument("--button", dest="buttons", action="append", default=[], choices=BUTTONS)
    parser.add_argument("--opening-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    for name, value in args.options:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) or not re.fullmatch(r"-?[0-9]+", value):
            parser.error("set UCI spin options with an integer value")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
