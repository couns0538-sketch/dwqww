#!/usr/bin/env python3
"""UCI harness for seat 073. Reads and writes only text. Stops on a bad engine line."""

import argparse
import hashlib
import os
import queue
import subprocess
import threading
import time

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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = os.path.abspath(exe)
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines = []
        self.id_name = ""
        self.id_author = ""
        self.queue = queue.Queue()
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.queue.put(line)
        self.queue.put(None)

    def send(self, command):
        self.lines.append("> " + command)
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.queue.get(timeout=1.0)
            except queue.Empty:
                if self.proc.poll() is not None and self.queue.empty():
                    break
                continue
            if line is None:
                break
            text = line.rstrip("\n")
            self.lines.append(text)
            low = text.lower()
            for bad in BAD:
                if bad.lower() in low:
                    raise SystemExit("STOP " + text)
            if predicate(text):
                return text
        raise SystemExit("STOP timeout waiting for engine")

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def handshake(engine, timeout):
    engine.send("uci")
    engine.read_until(lambda line: line.strip() == "uciok", timeout)
    for line in engine.lines:
        if line.startswith("id name "):
            engine.id_name = line[len("id name ") :]
        elif line.startswith("id author "):
            engine.id_author = line[len("id author ") :]
    engine.send("isready")
    engine.read_until(lambda line: line.strip() == "readyok", timeout)


def write_meta(path, engine, options):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("exe=" + engine.exe + "\n")
        handle.write("sha256=" + sha256_file(engine.exe) + "\n")
        handle.write("id name " + engine.id_name + "\n")
        handle.write("id author " + engine.id_author + "\n")
        handle.write("options:\n")
        if not options:
            handle.write("(none)\n")
        for name, value in options:
            handle.write("setoption name " + name + " value " + value + "\n")


def write_log(path, engine):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(engine.lines) + "\n")


def parse_bench(lines):
    found = None
    for line in lines:
        if "bench depth" in line and " nodes " in line:
            parts = line.split()
            if "nodes" in parts:
                found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("STOP no bench nodes line")
    return found


def parse_perft(lines):
    found = None
    for line in lines:
        if line.startswith("nodes "):
            found = int(line.split()[1])
    if found is None:
        raise SystemExit("STOP no perft nodes line")
    return found


def last_go_nodes(lines, start):
    found = None
    for line in lines[start:]:
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            found = int(parts[parts.index("nodes") + 1])
        if line.startswith("bestmove "):
            move = line.split()[1]
            if found is None:
                raise SystemExit("STOP no nodes before bestmove")
            return found, move
    raise SystemExit("STOP no bestmove")


def load_positions(path, limit):
    positions = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if len(tokens) >= 6 and tokens[4].isdigit() and tokens[5].isdigit():
                fen = " ".join(tokens[:6])
            elif len(tokens) >= 4:
                fen = " ".join(tokens[:4]) + " 0 1"
            else:
                raise SystemExit("STOP bad position line " + line)
            positions.append(fen)
            if limit and len(positions) >= limit:
                break
    return positions


def cmd_honesty(args):
    expected = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "perft5": 4865609,
    }
    commands = {
        "bench11": "bench 11",
        "bench13": "bench 13",
        "bench16": "bench 16",
        "perft5": "go perft 5",
    }
    summary = []
    for tag in ("bench11", "bench13", "bench16", "perft5"):
        engine = Engine(args.exe)
        try:
            handshake(engine, 60)
            engine.send(commands[tag])
            if tag.startswith("bench"):
                engine.read_until(lambda line: "bench depth" in line and " nodes " in line, 180)
                nodes = parse_bench(engine.lines)
            else:
                engine.read_until(lambda line: line.startswith("nodes "), 180)
                nodes = parse_perft(engine.lines)
            write_log(os.path.join(args.outdir, "honesty_" + tag + ".txt"), engine)
            write_meta(os.path.join(args.outdir, "honesty_" + tag + ".meta"), engine, [])
        finally:
            engine.close()
        ok = "ok" if nodes == expected[tag] else "MISMATCH"
        summary.append((tag, commands[tag], nodes, expected[tag], ok))
        print(tag, nodes, ok, flush=True)
    out_path = os.path.join(args.outdir, "HONESTY_B.txt")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("tag command nodes expected status\n")
        for tag, command, nodes, want, ok in summary:
            handle.write(f"{tag} {command} {nodes} {want} {ok}\n")
    print("wrote", out_path, flush=True)


def send_options(engine, options, timeout):
    for name, value in options:
        engine.send("setoption name " + name + " value " + value)
        engine.send("isready")
        engine.read_until(lambda line: line.strip() == "readyok", timeout)


def cmd_search(args):
    positions = load_positions(args.positions, args.limit)
    options = []
    if args.s14:
        options.extend(S14)
        options.append(("Threads", "1"))
        options.append(("Hash", "16"))
    if args.switch == "on":
        options.append(("IdeaS29", "true"))
    elif args.switch == "off":
        options.append(("IdeaS29", "false"))
    elif args.switch != "omit":
        raise SystemExit("STOP bad switch")
    engine = Engine(args.exe)
    rows = []
    try:
        handshake(engine, 60)
        send_options(engine, options, 60)
        for index, fen in enumerate(positions):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line.strip() == "readyok", 60)
            engine.send("position fen " + fen)
            engine.send("isready")
            engine.read_until(lambda line: line.strip() == "readyok", 60)
            mark = len(engine.lines)
            if args.nodes:
                engine.send("go nodes " + str(args.nodes))
            else:
                engine.send("go depth " + str(args.depth))
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes, move = last_go_nodes(engine.lines, mark)
            rows.append((index, nodes, move, fen))
            if (index + 1) % 25 == 0:
                print(args.tag, index + 1, "of", len(positions), "nodes", nodes, flush=True)
        write_log(os.path.join(args.outdir, args.tag + ".txt"), engine)
        write_meta(os.path.join(args.outdir, args.tag + ".meta"), engine, options)
    finally:
        engine.close()
    rows_path = os.path.join(args.outdir, args.tag + ".rows.txt")
    with open(rows_path, "w", encoding="utf-8") as handle:
        total = 0
        for index, nodes, move, fen in rows:
            total += nodes
            handle.write(f"{index} {nodes} {move} {fen}\n")
        handle.write(f"# sum {total} count {len(rows)}\n")
    print(args.tag, "sum", sum(item[1] for item in rows), "count", len(rows), flush=True)


def cmd_uci_options(args):
    engine = Engine(args.exe)
    try:
        handshake(engine, 60)
        write_log(os.path.join(args.outdir, args.tag + ".txt"), engine)
        write_meta(os.path.join(args.outdir, args.tag + ".meta"), engine, [])
    finally:
        engine.close()
    print("wrote", args.tag, flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    honesty = sub.add_parser("honesty")
    honesty.add_argument("--exe", required=True)
    honesty.add_argument("--outdir", required=True)
    honesty.set_defaults(func=cmd_honesty)
    search = sub.add_parser("search")
    search.add_argument("--exe", required=True)
    search.add_argument("--outdir", required=True)
    search.add_argument("--tag", required=True)
    search.add_argument("--positions", required=True)
    search.add_argument("--depth", type=int, default=12)
    search.add_argument("--nodes", type=int, default=0)
    search.add_argument("--limit", type=int, default=0)
    search.add_argument("--switch", default="omit")
    search.add_argument("--s14", action="store_true")
    search.set_defaults(func=cmd_search)
    options = sub.add_parser("uci")
    options.add_argument("--exe", required=True)
    options.add_argument("--outdir", required=True)
    options.add_argument("--tag", required=True)
    options.set_defaults(func=cmd_uci_options)
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
