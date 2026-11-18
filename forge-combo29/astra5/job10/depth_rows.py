"""Run job 10's six fixed-depth suites and check each against the matching job 7 row."""
import argparse
import csv
from datetime import datetime
from hashlib import file_digest
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

# counters.py is shared with the hard-node-cap suite.
sys.path.insert(0, os.environ.get("ASTRA10_PARSER", str(Path(__file__).resolve().parent)))
from counters import parse_counters

PIECES = ("p2_5", "p6_9", "p10_15", "p16_32")
DEPTHS = ("d1_6", "d7_10", "d11plus")
COUNTS = ("nm", "fh", "mate", "t1", "t2", *PIECES, *DEPTHS, *(p+"_"+d for p in PIECES for d in DEPTHS))
FIELDS = ("index", "fen", "nodes", "bestmove")


def sha(path):
    with path.open("rb") as f:
        return file_digest(f, "sha256").hexdigest()


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def send(proc, log, text):
    log.write("> " + text + "\n")
    proc.stdin.write(text + "\n")
    proc.stdin.flush()


def receive(proc, log, stop):
    response = []
    for raw in proc.stdout:
        line = raw.rstrip()
        log.write("< " + raw)
        if any(msg in line.lower() for msg in ("unknown option", "invalid value", "info string error")):
            raise ValueError("unexpected engine diagnostic " + line)
        response.append(line)
        if line == stop or (stop == "bestmove" and line.startswith("bestmove ")):
            return response
    raise ValueError("EOF before " + stop)


def run(args):
    exe = args.exe.resolve(strict=True)
    size = {"G": 353, "O": 200}[args.suite]
    ref = rows(args.reference)
    if len(ref) != size:
        raise ValueError("wrong reference row count")
    opts = args.pc20.read_text().splitlines() + [f"setoption name NullMateGuard value {args.guard}"]
    if len(opts) != 23 or len(set(opts)) != 23:
        raise ValueError("incorrect PC20/Threads/Hash plus guard option count")
    settings = f"exe {exe}\nsha256 {sha(exe)}\nreference {args.reference}\nreference_sha256 {sha(args.reference)}\n"
    (args.out/"settings.txt").write_text(settings + "built-in evaluation, depth 12\n" + "\n".join(opts) + "\n")
    total, unequal = 0, 0
    first = []
    with (args.out/"run.log").open("x") as log, (args.out/"rows.tsv").open("x") as data:
        writer = csv.DictWriter(data, (*FIELDS, *COUNTS), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        proc = subprocess.Popen([str(exe)], cwd=exe.parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            send(proc, log, "uci")
            hello = receive(proc, log, "uciok")
            if "option name NullMateGuard type spin default 0 min 0 max 2" not in hello:
                raise ValueError("guard declaration not found")
            declared = {m[1] for line in hello if (m := re.match(r"option name (.+?) type ", line))}
            for command in opts:
                if not command.split(" value ")[0].removeprefix("setoption name ") in declared:
                    raise ValueError("undeclared option in " + command)
                send(proc, log, command)
            send(proc, log, "isready")
            receive(proc, log, "readyok")
            for i, expected in enumerate(ref, 1):
                if int(expected["index"]) != i:
                    raise ValueError("reference indexed out of order")
                send(proc, log, "ucinewgame")
                send(proc, log, "isready")
                receive(proc, log, "readyok")
                send(proc, log, "position fen " + expected["fen"])
                send(proc, log, "go depth 12")
                result = receive(proc, log, "bestmove")
                info = next(line for line in reversed(result) if line.startswith("info depth ") and " nodes " in line)
                if re.search(r"\bdepth (\d+)", info)[1] != "12":
                    raise ValueError(f"row {i}: search did not complete requested depth")
                nodes = re.search(r"\bnodes (\d+)", info)[1]
                row = dict(index=str(i), fen=expected["fen"], nodes=nodes, bestmove=result[-1].split()[1])
                counters = parse_counters(result)
                writer.writerow({**row, **counters})
                data.flush()
                log.flush()
                if row != {key: expected[key] for key in FIELDS}:
                    raise ValueError(f"first difference at row {i}\nreference {expected}\nobserved {row}")
                total += int(nodes)
                unequal += counters["t1"] != counters["t2"]
                if i <= 3:
                    first.append(nodes)
            send(proc, log, "quit")
            if proc.wait(timeout=10):
                raise ValueError("nonzero engine exit")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            proc.stdin.close()
            proc.stdout.close()
    expected_sum = {"O": (8315168, 8315218, 8315218), "G": (17611204, 17848355, 17848355)}[args.suite][args.guard]
    if total != expected_sum:
        raise ValueError(f"sum {total} differs from prescribed {expected_sum}")
    return f"{args.suite} guard {args.guard} | {size}/{size} job7 node and bestmove rows equal | nodes {total} | first three {' '.join(first)} | positions with t1 != t2 {unequal}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("exe", type=Path)
    p.add_argument("pc20", type=Path)
    p.add_argument("suite", choices=("G", "O"))
    p.add_argument("guard", type=int, choices=(0, 1, 2))
    p.add_argument("reference", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--deadline", default="2026-11-18T21:32:42+00:00")
    args = p.parse_args()
    left = datetime.fromisoformat(args.deadline).timestamp() - time.time()
    if left <= 0:
        sys.exit("deadline reached")
    def stop(sig, frame):
        raise TimeoutError("deadline or termination signal received")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, left)
    args.out.mkdir(exist_ok=True, parents=True)
    with (args.out/"checks.txt").open("x") as f:
        try:
            msg = run(args)
        except Exception as error:
            print("STOP", str(error), file=f, flush=True)
            raise
        print(msg, file=f)
        print(msg, flush=True)


if __name__ == "__main__":
    main()
