#!/usr/bin/env python3
"""Fixed-depth node harness.

Sends S14, then Threads 1, then Hash 16. After every setoption and every
position it sends isready and reads every line up to readyok. Stops on
"unknown option", "invalid value", "invalid FEN", or "illegal move".
One fresh process. Writes the raw transcript, one node count per position,
and a .meta file for the exe it started.
"""
import argparse
import hashlib
import signal
import subprocess
import sys

STOP_PHRASES = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
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
]


class ProtocolError(Exception):
    pass


class TimeoutError_(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutError_("timed out waiting for the engine")


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.transcript = []

    def send(self, line):
        self.transcript.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout_s):
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout_s)
        try:
            while True:
                line = self.proc.stdout.readline()
                if line == "":
                    raise ProtocolError("engine closed stdout")
                line = line.rstrip("\r\n")
                self.transcript.append("<< " + line)
                for phrase in STOP_PHRASES:
                    if phrase in line:
                        raise ProtocolError(line)
                if done(line):
                    return line
        finally:
            signal.alarm(0)

    def ready(self, timeout_s):
        self.send("isready")
        self.read_until(lambda line: line == "readyok", timeout_s)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()


def load_fens(path, limit):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            fens.append(line)
    if limit > 0:
        fens = fens[:limit]
    return fens


def last_nodes(transcript, start):
    nodes = None
    for line in transcript[start:]:
        if not line.startswith("<< info "):
            continue
        parts = line.split()
        if "nodes" in parts:
            index = parts.index("nodes")
            if index + 1 < len(parts):
                nodes = int(parts[index + 1])
    if nodes is None:
        raise ProtocolError("no info nodes line before bestmove")
    return nodes


def write_meta(path, exe, sha, id_name, option_lines):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={sha}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write("option_lines_sent:\n")
        for line in option_lines:
            handle.write(line + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--idea", choices=["absent", "false", "true"], default="absent")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    fens = load_fens(args.fens, args.limit)
    sha = hashlib.sha256(open(args.exe, "rb").read()).hexdigest()
    option_lines = []
    for name, value in S14:
        option_lines.append(f"setoption name {name} value {value}")
    option_lines.append("setoption name Threads value 1")
    option_lines.append("setoption name Hash value 16")
    if args.idea != "absent":
        option_lines.append(f"setoption name IdeaK10 value {args.idea}")
        option_lines.append("setoption name IdeaK10_MinDepth value 8")
        option_lines.append("setoption name IdeaK10_Threshold value 3072")

    engine = Engine(args.exe)
    counts = []
    id_name = ""
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok", args.timeout)
        for line in engine.transcript:
            if line.startswith("<< id name "):
                id_name = line[3:]
        for line in option_lines:
            engine.send(line)
            engine.ready(args.timeout)
        for index, fen in enumerate(fens):
            engine.send("ucinewgame")
            engine.ready(args.timeout)
            engine.send("position fen " + fen)
            engine.ready(args.timeout)
            start = len(engine.transcript)
            engine.send(f"go depth {args.depth}")
            engine.read_until(lambda line: line.startswith("bestmove "), args.timeout)
            counts.append(last_nodes(engine.transcript, start))
            print(f"{index} {counts[-1]}", flush=True)
    except (ProtocolError, TimeoutError_) as exc:
        write_meta(args.meta, args.exe, sha, id_name, option_lines)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write("\n".join(engine.transcript) + "\n")
        with open(args.nodes, "w", encoding="utf-8") as handle:
            for index, nodes in enumerate(counts):
                handle.write(f"{index} {nodes}\n")
        print(f"HARNESS_STOP {exc}", file=sys.stderr)
        engine.close()
        return 1
    engine.close()
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(engine.transcript) + "\n")
    with open(args.nodes, "w", encoding="utf-8") as handle:
        for index, nodes in enumerate(counts):
            handle.write(f"{index} {nodes}\n")
        handle.write(f"SUM {sum(counts)}\n")
        handle.write(f"COUNT {len(counts)}\n")
    write_meta(args.meta, args.exe, sha, id_name, option_lines)
    print(f"SUM {sum(counts)} COUNT {len(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
