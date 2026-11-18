"""Run one Forge position set per fresh UCI process, or exercise its error tripwire."""

import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path


S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20 = S14 + [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]


def send(process, command):
    process.stdin.write(command + "\n")
    process.stdin.flush()


def lines(process):
    for line in process.stdout:
        line = line.rstrip("\r\n")
        folded = line.casefold()
        if "unknown option" in folded or "invalid value" in folded or "ERROR" in line:
            raise ValueError(f"engine diagnostic: {line}")
        yield line


def until(process, marker):
    for line in lines(process):
        if line == marker:
            return
    raise RuntimeError(f"engine closed while waiting for {marker}")


def identify(process):
    send(process, "uci")
    options = set()
    identity = None
    for line in lines(process):
        if line.startswith("id name "):
            identity = line
        option = re.match(r"^option name (.+?) type ", line)
        if option:
            options.add(option[1])
        if line == "uciok":
            if identity is None:
                raise RuntimeError("uciok without id name")
            return identity, options
    raise RuntimeError("engine closed before uciok")


def search(process, fen, depth):
    send(process, "ucinewgame")
    send(process, "isready")
    until(process, "readyok")
    send(process, "position fen " + fen)
    send(process, f"go depth {depth}")
    last = None
    for line in lines(process):
        if line.startswith("info "):
            info_depth = re.search(r"\bdepth (\d+)\b", line)
            nodes = re.search(r"\bnodes (\d+)\b", line)
            if info_depth and nodes:
                last = int(info_depth[1]), int(nodes[1])
        if line.startswith("bestmove "):
            if last is None:
                raise RuntimeError(f"bestmove without a depth-and-nodes info line for {fen}")
            return last[1], line.split()[1]
    raise RuntimeError(f"engine closed before bestmove for {fen}")


def run_set(args, process, identity, options):
    settings = [("Threads", "1"), ("Hash", "16"), *PC20]
    if args.singular_depth is not None:
        settings.append(("SingularDepth", str(args.singular_depth)))
    if args.fhb7:
        settings.append(("FailHighBlend", "7"))
    commands = []
    for name, value in settings:
        if name not in options:
            raise ValueError(f"option missing from engine uci list: {name}")
        commands.append(f"setoption name {name} value {value}")
    for command in commands:
        send(process, command)
    send(process, "isready")
    until(process, "readyok")
    meta = Path(str(args.rows) + ".meta")
    with args.epd.open(encoding="utf-8") as positions, args.rows.open(
        "x", encoding="utf-8", newline=""
    ) as output, meta.open("x", encoding="utf-8") as metadata:
        metadata.write(f"exe {args.exe}\nsha256 {hashlib.sha256(args.exe.read_bytes()).hexdigest()}\n")
        metadata.write(f"{identity}\ncwd {Path.cwd()}\ndepth {args.depth}\n")
        metadata.write("\n".join(commands) + "\n")
        metadata.flush()
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(["index", "fen", "nodes", "bestmove"])
        count = 0
        for count, position in enumerate(positions, 1):
            fields = position.split()
            if len(fields) < 4:
                raise ValueError(f"position {count} has fewer than four fields")
            fen = " ".join(fields[:4]) + " 0 1"
            nodes, move = search(process, fen, args.depth)
            writer.writerow([count, fen, nodes, move])
            output.flush()
        if count == 0:
            raise ValueError("empty EPD")
        send(process, "quit")
        for _ in lines(process):
            pass
        if process.wait():
            raise RuntimeError(f"engine exited with status {process.returncode}")
        metadata.write(f"completed_rows {count}\n")
        print(f"wrote {count} rows to {args.rows}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    run = actions.add_parser("run")
    check = actions.add_parser("check", help="expect the plain PC engine to reject FailHighBlend 7")
    for action in (run, check):
        action.add_argument("exe", type=Path)
    run.add_argument("epd", type=Path)
    run.add_argument("depth", type=int)
    run.add_argument("rows", type=Path)
    run.add_argument("--singular-depth", type=int)
    run.add_argument("--fhb7", action="store_true")
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    with subprocess.Popen(
        [str(args.exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1,
    ) as process:
        try:
            identity, options = identify(process)
            if args.action == "check":
                if "FailHighBlend" in options:
                    raise RuntimeError("self-check requires the plain PC build")
                command = "setoption name FailHighBlend value 7"
                print(f"{identity}\nsent: {command}", flush=True)
                send(process, command)
                send(process, "isready")
                until(process, "readyok")
                raise RuntimeError("self-check did not produce the expected engine diagnostic")
            run_set(args, process, identity, options)
        finally:
            if process.poll() is None:
                process.kill()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"STOP: {error}")
