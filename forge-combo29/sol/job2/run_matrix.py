#!/usr/bin/env python3
"""Run a pinned Forge PC20 search row for each line of a FEN or EPD file."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time

PC20 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("CuckooRep", "true"),
    ("HistRework", "2"),
    ("TtPruneV2", "true"),
    ("CorrHistV2", "true"),
    ("MateAlphaGuard", "true"),
    ("OwnBook", "false"),
]
COUNTER_PREFIX = "info string CNT "
INFO_DEPTH = re.compile(r"^info depth ([0-9]+)\b.*\bnodes ([0-9]+)\b")
FINAL_NODES = re.compile(r"^info string softnodes nodes ([0-9]+)$")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Refused(RuntimeError):
    """An engine command was rejected."""


class Engine:
    def __init__(self, executable, timeout):
        self.timeout = timeout
        self.unread = bytearray()
        self.process = subprocess.Popen(
            [str(executable)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.send("quit")
                exit_code = self.process.wait(timeout=self.timeout)
                if exit_code != 0:
                    raise RuntimeError(f"engine exited {exit_code} after quit")
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()
            self.selector.close()
            self.process.stdout.close()
            self.process.stdin.close()

    def send(self, command):
        self.process.stdin.write((command + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def until(self, token):
        lines = []
        deadline = time.monotonic() + self.timeout
        while True:
            newline = self.unread.find(b"\n")
            if newline == -1:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not self.selector.select(remaining):
                    raise RuntimeError(f"timeout waiting for {token}; last lines: {lines[-4:]}")
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError(
                        f"engine closed output waiting for {token}; last lines: {lines[-4:]}"
                    )
                self.unread.extend(chunk)
                continue
            line = self.unread[:newline].decode("utf-8", errors="replace").rstrip("\r")
            del self.unread[:newline + 1]
            lower = line.lower()
            if "unknown option" in lower or "invalid value" in lower or re.search(r"\bERROR\b", line):
                raise Refused(line)
            if lower.startswith(("info string invalid fen:", "info string illegal move ")):
                raise RuntimeError(line)
            lines.append(line)
            if line == token or line.startswith(token + " "):
                return lines


def parse_row(index, fen, output, require_counter):
    infos = [(line, match) for line in output if (match := INFO_DEPTH.match(line))]
    counters = [line for line in output if line.startswith(COUNTER_PREFIX)]
    final_info = next((line for line in output if FINAL_NODES.fullmatch(line)), None)
    bestmove = output[-1].split(maxsplit=2)
    if not infos or len(bestmove) < 2:
        raise RuntimeError(f"position {index}: missing info depth or bestmove; last lines: {output[-4:]}")
    if len(counters) > 1 or (require_counter and not counters):
        raise RuntimeError(f"position {index}: expected one CNT line, saw {len(counters)}")
    info, match = infos[-1]
    return {
        "index": index,
        "fen": fen,
        "depth": int(match.group(1)),
        "nodes": int(match.group(2)),
        "bestmove": bestmove[1],
        "info": info,
        "final_nodes": int(final_info.rsplit(" ", 1)[-1]) if final_info else None,
        "final_nodes_info": final_info,
        "cnt": counters[0] if counters else None,
    }


def run(args):
    executable = args.engine.resolve(strict=True)
    fixture = args.positions.resolve(strict=True)
    fixture_bytes = fixture.read_bytes()
    positions = [line.strip() for line in fixture_bytes.decode("utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        positions = positions[:args.limit]
    if not positions:
        raise ValueError("fixture contains no positions")

    options = [("Threads", "1"), ("Hash", "16"), *PC20, *args.overrides]
    settings = [f"setoption name {name} value {value}" for name, value in options]
    search = f"go {args.mode} {args.budget}"
    meta = {
        "command": sys.argv,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "positions": str(fixture),
        "positions_sha256": sha256(fixture_bytes).hexdigest(),
        "id_name": None,
        "settings_sent": [],
        "search": search,
        "setup_per_search": ["ucinewgame", "isready", "position fen <fixture row>"],
        "external_net_file": None,
        "positions_requested": len(positions),
        "positions_completed": 0,
        "nodes_sum": 0,
        "start_utc": utc_now(),
    }
    sidecar = args.output.with_name(args.output.name + ".meta")
    if args.output.exists() or sidecar.exists():
        raise FileExistsError(f"output or sidecar already exists for {args.output}")
    with args.output.open("x", encoding="utf-8") as rows, sidecar.open("x", encoding="utf-8") as metadata:
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
                for index, fen in enumerate(positions, start=1):
                    engine.send("ucinewgame")
                    engine.send("isready")
                    engine.until("readyok")
                    engine.send(f"position fen {fen}")
                    engine.send(search)
                    row = parse_row(index, fen, engine.until("bestmove"), args.require_counter)
                    rows.write(json.dumps(row, separators=(",", ":")) + "\n")
                    rows.flush()
                    meta["positions_completed"] = index
                    meta["nodes_sum"] += row["nodes"]
            meta["status"] = "complete"
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error)
            print(f"{search}: {meta['status']}: {error}", file=sys.stderr)
        finally:
            meta["end_utc"] = utc_now()
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    print(f"{args.output}: {meta['status']}, {meta['positions_completed']}/{len(positions)} positions, {meta['nodes_sum']} nodes")
    return 0 if meta["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("positions", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("mode", choices=("depth", "nodes", "softnodes"))
    parser.add_argument("budget", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=15, help="seconds per UCI response")
    parser.add_argument("--set", dest="overrides", nargs=2, metavar=("NAME", "VALUE"), action="append", default=[])
    parser.add_argument("--require-counter", action="store_true")
    args = parser.parse_args()
    if args.budget <= 0 or args.timeout <= 0 or (args.limit is not None and args.limit <= 0):
        parser.error("budget, timeout, and limit must be positive")
    if any("\n" in value or "\r" in value for pair in args.overrides for value in pair):
        parser.error("option names and values must stay on one line")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
