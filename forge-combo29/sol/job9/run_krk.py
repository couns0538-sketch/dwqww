#!/usr/bin/env python3
"""Replay the pinned Job 9 KRK fixture under FRESH, STAIN, or GAME."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
import re
import subprocess
import sys

work = Path(__file__).resolve().parent.parent
for job2 in (work / "job2", work / "sol-job2"):
    if (job2 / "run_matrix.py").is_file():
        sys.path.insert(0, str(job2))
        break
else:
    raise SystemExit("Job 2 run_matrix.py is missing from the adjacent job2 or sol-job2 directory")

from run_matrix import Engine, PC20, Refused, parse_row, utc_now

FIXTURE_SHA256 = "e6a9886c8192d2b124d7656293a3815e72b30b4b6a84bd7731c7f3de756e7391"
SEARCH = "go depth 14"
MODES = ("FRESH", "STAIN", "GAME")
DEPTH14 = re.compile(r"^info depth 14\b")
SCORE = re.compile(r"\bscore (mate|cp) (-?\d+)\b")
DTM = re.compile(r"(\d+) \(M(\d+)\)")


class RecordedEngine(Engine):
    def __init__(self, executable, timeout, commands):
        super().__init__(executable, timeout)
        self.commands = commands

    def send(self, command):
        super().send(command)
        self.commands.append(command)


def read_fixture(data):
    if sha256(data).hexdigest() != FIXTURE_SHA256:
        raise ValueError(f"fixture SHA-256 must equal {FIXTURE_SHA256}")
    positions = []
    for line in data.decode("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [field.strip() for field in line.split("|")]
        index = len(positions)
        if len(fields) != 7 or fields[0] != f"{index:02d}":
            raise ValueError(f"fixture row {index}: expected seven fields and literal index {index:02d}")
        dtm = DTM.fullmatch(fields[1])
        fen_fields = fields[-1].split()
        if dtm is None or len(fen_fields) != 6 or fen_fields[1] != "w":
            raise ValueError(f"fixture row {index}: expected a labelled DTM and a white-to-move FEN")
        positions.append({
            "position_index": index,
            "fixture_index": fields[0],
            "fixture_dtm": fields[1],
            "fixture_dtm_plies": int(dtm[1]),
            "fixture_mate_moves": int(dtm[2]),
            "fen": fields[-1],
        })
    if len(positions) != 40:
        raise ValueError(f"expected 40 KRK positions, found {len(positions)}")
    return positions


def record_row(ordinal, position, mode, pass_number, shuffle_index, output):
    row = parse_row(ordinal, position["fen"], output, require_counter=True)
    info14 = next((line for line in reversed(output) if DEPTH14.match(line)), None)
    score = SCORE.search(info14) if info14 is not None else None
    row.update(position)
    row.update(mode=mode, shuffle_index=shuffle_index, info_depth14=info14,
               score_kind=score[1] if score else None,
               score_value=int(score[2]) if score else None)
    row["pass"] = pass_number
    return row


def ready_after(engine, command):
    engine.send(command)
    engine.send("isready")
    return engine.until("readyok")


def run(args):
    executable = args.engine.resolve(strict=True)
    fixture = args.fixture.resolve(strict=True)
    fixture_bytes = fixture.read_bytes()
    positions = read_fixture(fixture_bytes)
    pass_count = 1 if args.mode == "FRESH" else 10
    sidecar = args.rows.with_name(args.rows.name + ".meta")
    if args.rows.exists() or sidecar.exists():
        raise FileExistsError(f"refusing to overwrite {args.rows} or its sidecar")
    args.rows.parent.mkdir(parents=True, exist_ok=True)

    options = (("Threads", "1"), ("Hash", "16"), *PC20, *args.overrides)
    settings = [f"setoption name {name} value {value}" for name, value in options]
    meta = {
        "mode": args.mode,
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "settings_sent": settings,
        "external_net_file": None,
        "fixture": str(fixture),
        "fixture_sha256": sha256(fixture_bytes).hexdigest(),
        "search": SEARCH,
        "passes_requested": pass_count,
        "passes_completed": 0,
        "positions_requested": pass_count * len(positions),
        "positions_completed": 0,
        "last_info_nodes_sum": 0,
        "passes": [],
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    pass_number, fixture_index = None, None
    with args.rows.open("x", encoding="utf-8") as rows, sidecar.open("x", encoding="utf-8") as metadata:
        try:
            for pass_number in range(1, pass_count + 1):
                fixture_index = None
                order = list(range(len(positions)))
                if args.mode != "FRESH":
                    random.Random(pass_number).shuffle(order)
                current = {
                    "pass": pass_number,
                    "shuffle_seed": None if args.mode == "FRESH" else pass_number,
                    "order": order,
                    "commands_sent": [],
                    "settings_ack": [],
                    "position_acks": [],
                    "start_utc": utc_now(),
                }
                meta["passes"].append(current)
                try:
                    with RecordedEngine(executable, args.timeout, current["commands_sent"]) as engine:
                        engine.send("uci")
                        current["id_name"] = next(
                            (line for line in engine.until("uciok") if line.startswith("id name ")),
                            None,
                        )
                        if current["id_name"] is None:
                            raise RuntimeError("missing engine id name")
                        if meta["id_name"] is None:
                            meta["id_name"] = current["id_name"]
                        elif current["id_name"] != meta["id_name"]:
                            raise RuntimeError("engine id name changed between passes")
                        for setting in settings:
                            engine.send(setting)
                        current["settings_ack"] = ready_after(engine, "ucinewgame")
                        for visit, fixture_index in enumerate(order):
                            if args.mode == "STAIN" or (args.mode == "FRESH" and visit > 0):
                                command = "setoption name Clear Hash" if args.mode == "STAIN" else "ucinewgame"
                                ack = ready_after(engine, command)
                                current["position_acks"].append({"position_index": fixture_index, "lines": ack})
                            position = positions[fixture_index]
                            engine.send(f"position fen {position['fen']}")
                            engine.send(SEARCH)
                            row = record_row(
                                meta["positions_completed"] + 1, position, args.mode, pass_number,
                                visit, engine.until("bestmove"),
                            )
                            rows.write(json.dumps(row, separators=(",", ":")) + "\n")
                            rows.flush()
                            meta["positions_completed"] += 1
                            meta["last_info_nodes_sum"] += row["nodes"]
                    meta["passes_completed"] += 1
                finally:
                    current["end_utc"] = utc_now()
            meta["status"] = "complete"
        except (RuntimeError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error) or type(error).__name__
            meta["failure_pass"] = pass_number
            meta["failure_position_index"] = fixture_index
            print(f"{args.mode}: {meta['status']}: {meta['error']}", file=sys.stderr)
        finally:
            meta["end_utc"] = utc_now()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")

    print(f"{args.mode}: {meta['status']}, "
          f"{meta['positions_completed']}/{meta['positions_requested']} searches, "
          f"{meta['last_info_nodes_sum']} last-info nodes")
    return 0 if meta["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", type=str.upper, choices=MODES)
    parser.add_argument("engine", type=Path)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("rows", type=Path)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--set", nargs=2, action="append", default=[],
                        dest="overrides", metavar=("NAME", "VALUE"))
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    if any("\n" in value or "\r" in value for option in args.overrides for value in option):
        parser.error("option names and values must stay on one line")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
