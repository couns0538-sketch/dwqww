"""Replay a job 2 row set with the job 1 UCI protocol and an optional A25C observer."""

import argparse
import csv
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True  # Keep Python caches out of the text-only evidence tree.

# A separate checkout of job1 can be supplied for running the script from scratch.
sys.path.insert(0, os.environ.get("ASTRA5_JOB1", str(Path(__file__).resolve().parent.parent / "job1")))
from harness import PC20, identify, lines, search, send, until


FHB7 = ("FailHighBlend", "7")
DEL = ("DoubleExtLimit", "-1")
SD20 = ("SingularDepth", "20")
SETTINGS = {
    "base": [], "fhb7": [FHB7],
    "del": [DEL], "del_fhb7": [DEL, FHB7],
    "sd20_base": [SD20], "sd20_fhb7": [SD20, FHB7],
    "dm12": [FHB7, ("DoubleExtMargin", "12")],
    "dm0": [FHB7, ("DoubleExtMargin", "0")],
    "sm1": [FHB7, ("SingularMargin", "1")],
}


def observe(stream, found):
    for line in stream:
        if line.split(maxsplit=1)[:1] == ["A25C"]:
            found.append(line.rstrip("\r\n"))
        yield line


def validate_counter(found, width, setting, index, blinded):
    if len(found) != 1:
        raise ValueError(f"position {index}: expected one A25C line, got {len(found)}")
    fields = found[0].split()
    if len(fields) != width + 1 or not all(value.isascii() and value.isdecimal() for value in fields[1:]):
        raise ValueError(f"position {index}: wrong A25C format (expected {width} unsigned integers)")
    if blinded:
        return
    values = list(map(int, fields[1:]))
    if values[0] != sum(values[1:7]):
        raise ValueError(f"position {index}: singular outcomes do not sum to tests: {found[0]}")
    if setting in ("del", "del_fhb7") and values[2] != 0:
        raise ValueError(f"position {index}: DoubleExtLimit -1 control failed: {found[0]}")
    if setting.startswith("sd20") and values[0] != 0:
        raise ValueError(f"position {index}: SingularDepth 20 control failed: {found[0]}")


def run(args):
    exe = args.exe.resolve(strict=True)
    epd = args.epd.resolve(strict=True)
    meta = Path(str(args.rows) + ".meta")
    full_fens = []
    for position in epd.read_text(encoding="utf-8").splitlines():
        fields = position.split()
        if len(fields) < 4:
            raise ValueError(f"{epd}: incomplete EPD line {len(full_fens) + 1}")
        full_fens.append(" ".join(fields[:4]) + " 0 1")
    fens = full_fens[:args.first]
    if not fens or (args.first is not None and len(fens) != args.first):
        raise ValueError("wrong position count")
    with subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=exe.parent, text=True, encoding="utf-8", bufsize=1,
    ) as process:
        try:
            found = []
            stream = SimpleNamespace(stdin=process.stdin, stdout=observe(process.stdout, found))
            identity, options = identify(stream)
            settings = [("Threads", "1"), ("Hash", "16"), *PC20, *SETTINGS[args.setting]]
            commands = []
            for name, value in settings:
                if name not in options:
                    raise ValueError(f"option missing from engine uci list: {name}")
                commands.append(f"setoption name {name} value {value}")
            for command in commands:
                send(stream, command)
            send(stream, "isready")
            until(stream, "readyok")
            if found:
                raise ValueError("unexpected counter before first search")
            with args.rows.open("x", encoding="utf-8", newline="") as output, meta.open(
                "x", encoding="utf-8"
            ) as metadata:
                metadata.write(f"exe {exe}\nsha256 {hashlib.sha256(exe.read_bytes()).hexdigest()}\n{identity}\n")
                metadata.write(f"cwd {exe.parent}\nepd {epd}\nepd_sha256 {hashlib.sha256(epd.read_bytes()).hexdigest()}\n")
                metadata.write(f"depth 12\n" + "\n".join(commands) + "\n")
                if args.blind_counts:
                    metadata.write("count values withheld for prediction; only line shape and A25C count checked\n")
                metadata.flush()
                writer = csv.writer(output, delimiter="\t", lineterminator="\n")
                keep = bool(args.slots) and not args.blind_counts
                header = ["index", "fen", "nodes", "bestmove"]
                writer.writerow(header + (["a25c"] if keep else []))
                for index, fen in enumerate(fens, 1):
                    nodes, move = search(stream, fen, 12)
                    if args.slots:
                        validate_counter(found, args.slots, args.setting, index, args.blind_counts)
                    elif found:
                        raise ValueError(f"position {index}: unexpected A25C in uncounted run")
                    writer.writerow([index, fen, nodes, move] + ([found[0]] if keep else []))
                    output.flush()
                    found.clear()
                send(stream, "quit")
                for _ in lines(stream):
                    pass
                if found or process.wait():
                    raise RuntimeError(f"unclean end of UCI session; status {process.returncode}")
                metadata.write(f"completed_rows {len(fens)}\n")
        finally:
            if process.poll() is None:
                process.kill()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    row = actions.add_parser("set")
    row.add_argument("exe", type=Path)
    row.add_argument("epd", type=Path)
    row.add_argument("setting", choices=SETTINGS)
    row.add_argument("rows", type=Path)
    row.add_argument("--first", type=int)
    row.add_argument("--slots", type=int, choices=(16, 17))
    row.add_argument("--blind-counts", action="store_true", help="discard counters and retain only position/node/move rows")
    args = parser.parse_args()
    if args.blind_counts and args.slots is None:
        parser.error("--blind-counts needs --slots")
    if args.first is not None and args.first < 1:
        parser.error("--first must be positive")
    run(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"STOP: {error}")
