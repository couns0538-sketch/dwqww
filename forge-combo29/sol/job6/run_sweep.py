#!/usr/bin/env python3
"""Replay a Job 6 PC20 sweep arm, optionally at only the 30 opening positions."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

# Import the exact readiness recorder and UCI parser used in earlier jobs.
work = Path(__file__).resolve().parent.parent
for job5_dir in (work / "job5", work / "sol-job5"):
    if (job5_dir / "run_variants.py").is_file():
        sys.path.insert(0, str(job5_dir))
        break
from run_variants import BUDGETS, VariantEngine
from run_games import read_games, reset_tables
from run_matrix import PC20, Refused, parse_row, utc_now

PROTOCOLS = {
    "warm-soft": ("soft", True),
    "cold-soft": ("soft", False),
    "warm-hard": ("hard", True),
}


def run(args):
    regime, warm = PROTOCOLS[args.protocol]
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
    meta = {
        "protocol": args.protocol,
        "regime": regime,
        "warm": warm,
        "opening_only": args.opening_only,
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "reset_commands": ["ucinewgame", "isready"],
        "reset_frequency": "once per game" if warm else "once per search",
        "position_command": "position fen <O line> [moves <preceding recorded moves>]",
        "external_net_file": None,
        "variant": dict(zip(("name", "value"), args.override)) if args.override else None,
        "variant_reply": [],
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
                if args.override:
                    name, value = args.override
                    setting = f"setoption name {name} value {value}"
                    engine.send(setting)
                    meta["settings_sent"].append(setting)
                    engine.send("isready")
                    engine.wait_for_variant(meta["variant_reply"])
                for game in games:
                    current_game, current_ply = game.index, None
                    if warm:
                        reset_tables(engine)
                    for ply in range(1 if args.opening_only else len(game.moves)):
                        current_ply = ply
                        if not warm:
                            reset_tables(engine)
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
    parser.add_argument("--set", dest="overrides", nargs=2, action="append", metavar=("NAME", "VALUE"))
    parser.add_argument("--opening-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    if args.overrides and len(args.overrides) != 1:
        parser.error("each variant changes exactly one setting")
    args.override = args.overrides[0] if args.overrides else None
    if args.override:
        name, value = args.override
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) or not re.fullmatch(r"-?[0-9]+", value):
            parser.error("set one UCI spin option by name with an integer value")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
