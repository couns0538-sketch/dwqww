"""Search independent depths of position P with ordered UCI settings and a line-by-line transcript."""

import argparse
import csv
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get("ASTRA5_JOB1", str(Path(__file__).resolve().parent.parent / "job1")))
from harness import PC20, S14, identify, lines, search, send, until


POSITION = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
HEADER = ["requested_depth", "info_depth", "bestmove", "score_type", "score", "nodes", "mate_found", "info"]


class Commands:
    def __init__(self, pipe, log):
        self.pipe = pipe
        self.log = log

    def write(self, command):
        self.log.write("> " + command)
        self.log.flush()
        return self.pipe.write(command)

    def flush(self):
        self.pipe.flush()


def observe(stdout, log, last_info):
    for line in stdout:
        log.write("< " + line)
        log.flush()
        if line.startswith("info ") and re.search(r"\bdepth \d+\b", line) and re.search(r"\bnodes \d+\b", line):
            last_info[:] = [line.strip()]
        yield line


def parse_switches(path, label):
    if not path:
        return []
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    selected = [(r["name"], r["value"]) for r in rows if (label == "all" or label == r["label"])]
    if not selected:
        raise ValueError(f"no switches for {label} in {path}")
    conflicts = {}
    for name, value in selected:
        if name in conflicts and conflicts[name] != value:
            raise ValueError(f"conflicting {name} values in switch group {label}")
        conflicts[name] = value
    return list(conflicts.items())


def run(args):
    exe = args.exe.resolve(strict=True)
    prefix = args.output
    prefix.parent.mkdir(parents=True, exist_ok=True)
    options = [("Threads", "1"), ("Hash", "16"), *(PC20 if args.profile == "PC20" else S14)]
    options += parse_switches(args.switches, args.label)
    for opt in args.set:
        name, sep, value = opt.partition("=")
        if not sep or not name or not value:
            raise ValueError("expected --set NAME=VALUE")
        options.append((name, value))
    with Path(str(prefix) + ".raw.txt").open("x", encoding="utf-8") as raw, Path(str(prefix) + ".tsv").open(
        "x", encoding="utf-8", newline=""
    ) as result, Path(str(prefix) + ".meta").open("x", encoding="utf-8") as meta, subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=exe.parent,
        bufsize=1, encoding="utf-8", text=True,
    ) as process:
        depth = None
        completed = 0
        try:
            last_info = []
            stream = SimpleNamespace(stdin=Commands(process.stdin, raw), stdout=observe(process.stdout, raw, last_info))
            identity, declared = identify(stream)
            meta.write(f"exe {exe}\nsha256 {hashlib.sha256(exe.read_bytes()).hexdigest()}\n{identity}\ncwd {exe.parent}\n")
            meta.write(f"fen {POSITION}\nprofile {args.profile}\nrequested_depths {args.first}..{args.last}\n")
            meta.write(f"two_consecutive_stop {args.two}\nladder_budget_seconds {args.seconds}\n")
            for name, value in options:
                if name not in declared:
                    raise ValueError(f"not in actual UCI list: {name}")
                cmd = f"setoption name {name} value {value}"
                meta.write(cmd + "\n")
                send(stream, cmd)
            send(stream, "isready")
            until(stream, "readyok")
            meta.flush()
            writer = csv.writer(result, delimiter="\t", lineterminator="\n")
            writer.writerow(HEADER)
            result.flush()
            streak = 0
            reason = "requested depths complete"
            for depth in range(args.first, args.last + 1):
                last_info.clear()
                nodes, move = search(stream, POSITION, depth)
                info = last_info[0]
                score = re.search(r"\bscore (cp|mate) ([+-]?\d+)\b", info)
                info_depth = int(re.search(r"\bdepth (\d+)\b", info)[1])
                if not score:
                    raise ValueError(f"missing score: {info}")
                mate = move == "g3g6" and score[1] == "mate" and int(score[2]) > 0
                writer.writerow([depth, info_depth, move, score[1], score[2], nodes, int(mate), info])
                result.flush()
                completed += 1
                streak = streak + 1 if mate else 0
                if args.two and streak == 2:
                    reason = "two consecutive mate depths"
                    break
            send(stream, "quit")
            for _ in lines(stream):
                pass
            if process.wait():
                raise RuntimeError(f"engine exited with status {process.returncode}")
            meta.write(f"completed_rows {completed}\nend {reason}\n")
        except BaseException as error:
            meta.write(f"completed_rows {completed}\ninterrupted_at {depth}\nend {error!r}\n")
            raise
        finally:
            if process.poll() is None:
                process.kill()


def stop(signum, frame):
    raise TimeoutError(f"signal {signum} stopped the ladder")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("profile", choices=("S14", "PC20"))
    parser.add_argument("output", type=Path, help="prefix for .tsv, .meta and .raw.txt")
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int, default=20)
    parser.add_argument("--two", action="store_true", help="stop after two consecutive positive g3g6 mate depths")
    parser.add_argument("--switches", type=Path)
    parser.add_argument("--label", default="all")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--seconds", type=int, default=0, help="wall-clock budget; 0 means no budget")
    args = parser.parse_args()
    if args.first < 1 or args.last < args.first or args.seconds < 0:
        parser.error("invalid depth range or budget")
    signal.signal(signal.SIGTERM, stop)
    if args.seconds:
        signal.signal(signal.SIGALRM, stop)
        signal.alarm(args.seconds)
    run(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"STOP: {error}")
