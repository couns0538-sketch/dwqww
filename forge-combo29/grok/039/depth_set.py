#!/usr/bin/env python3
"""Measured depth search. One engine process. S14, then the switch, then Threads and Hash.

After every setoption and every position the script sends isready and reads every line
up to readyok. It stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

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


def is_sanitizer(line):
    low = line.lower()
    return "sanitizer" in low or "runtime error:" in low


def args():
    out = {}
    raw = sys.argv[1:]
    i = 0
    while i < len(raw):
        key = raw[i]
        if key == "--switch":
            out["switch"] = raw[i + 1]
            i += 2
        elif key == "--limit":
            out["limit"] = int(raw[i + 1])
            i += 2
        elif key == "--depth":
            out["depth"] = int(raw[i + 1])
            i += 2
        elif key == "--exe":
            out["exe"] = Path(raw[i + 1]).resolve()
            i += 2
        elif key == "--fens":
            out["fens"] = Path(raw[i + 1]).resolve()
            i += 2
        elif key == "--prefix":
            out["prefix"] = Path(raw[i + 1]).resolve()
            i += 2
        else:
            raise SystemExit(f"unknown argument {key}")
    for need in ("exe", "fens", "prefix", "depth"):
        if need not in out:
            raise SystemExit(f"missing --{need}")
    out.setdefault("switch", "omit")
    out.setdefault("limit", 0)
    if out["switch"] not in ("omit", "true", "false"):
        raise SystemExit("switch must be omit, true, or false")
    return out


def load_fens(path, limit):
    rows = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        rows.append(text)
        if limit and len(rows) >= limit:
            break
    return rows


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.log = []
        self.err = []
        self.q = queue.Queue()

        def pump(stream, kind):
            for line in stream:
                self.q.put((kind, line))
            self.q.put((kind, None))

        threading.Thread(target=pump, args=(self.proc.stdout, "out"), daemon=True).start()
        threading.Thread(target=pump, args=(self.proc.stderr, "err"), daemon=True).start()

    def send(self, line):
        self.log.append(f">>> {line}\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def until(self, done, timeout):
        deadline = time.time() + timeout
        while True:
            left = deadline - time.time()
            if left <= 0:
                raise TimeoutError("engine silent")
            try:
                kind, line = self.q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError("engine silent") from None
            if line is None:
                if kind == "out":
                    raise EOFError("engine closed stdout")
                continue
            if kind == "err":
                self.err.append(line)
                self.log.append(f"!!! {line}")
                continue
            self.log.append(line)
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line.rstrip("\n"))
            if done(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        deadline = time.time() + 2
        while time.time() < deadline:
            try:
                kind, line = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                continue
            if kind == "err":
                self.err.append(line)
                self.log.append(f"!!! {line}")
            else:
                self.log.append(line)


def option_lines(switch):
    lines = [f"setoption name {name} value {value}" for name, value in S14]
    if switch == "true":
        lines.append("setoption name IdeaA8 value true")
    elif switch == "false":
        lines.append("setoption name IdeaA8 value false")
    lines.append("setoption name Threads value 1")
    lines.append("setoption name Hash value 16")
    return lines


def main():
    opt = args()
    fens = load_fens(opt["fens"], opt["limit"])
    exe = opt["exe"]
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()
    eng = Engine(exe)
    id_name = ""
    nodes = []
    try:
        eng.send("uci")
        eng.until(lambda line: line.startswith("uciok"), 30)
        for line in eng.log:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
        for fen_index, fen in enumerate(fens, start=1):
            for line in option_lines(opt["switch"]):
                eng.send(line)
                eng.send("isready")
                eng.until(lambda row: row.strip() == "readyok", 30)
            eng.send("ucinewgame")
            eng.send("isready")
            eng.until(lambda row: row.strip() == "readyok", 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.until(lambda row: row.strip() == "readyok", 30)
            eng.send(f"go depth {opt['depth']}")
            eng.until(lambda row: row.startswith("bestmove "), 120)
            found = None
            prefix = f"info depth {opt['depth']} "
            for line in reversed(eng.log):
                if line.startswith(prefix) and " nodes " in line:
                    parts = line.split()
                    found = int(parts[parts.index("nodes") + 1])
                    break
            if found is None:
                raise RuntimeError(f"no depth {opt['depth']} info for position {fen_index}")
            nodes.append(found)
            eng.log.append(f"# pos {fen_index} nodes {found}\n")
    finally:
        eng.close()
        prefix = opt["prefix"]
        prefix.parent.mkdir(parents=True, exist_ok=True)
        prefix.with_suffix(".txt").write_text("".join(eng.log))
        prefix.with_suffix(".nodes").write_text("".join(f"{n}\n" for n in nodes))
        prefix.with_suffix(".stderr").write_text("".join(eng.err))
        meta = [f"exe={exe}", f"sha256={sha}", f"id_name={id_name}", "options:"]
        meta.extend(option_lines(opt["switch"]))
        meta.append(f"depth={opt['depth']}")
        meta.append(f"fens={opt['fens']}")
        meta.append(f"positions={len(nodes)}")
        meta.append(f"sum={sum(nodes)}")
        sanitizer = [line.rstrip("\n") for line in eng.err if is_sanitizer(line)]
        nm = subprocess.run(
            ["bash", "-c", f"nm -C '{exe}' | grep -c __asan_ || true"],
            capture_output=True,
            text=True,
        )
        meta.append(f"nm_asan_count={nm.stdout.strip()}")
        meta.append(f"sanitizer_lines={len(sanitizer)}")
        meta.extend(sanitizer)
        prefix.with_suffix(".meta").write_text("\n".join(meta) + "\n")
        for line in sanitizer:
            print(line)
    print(f"positions {len(nodes)} sum {sum(nodes)}")
    if nodes[:3]:
        print("first3 " + " ".join(str(n) for n in nodes[:3]))
    if eng.err:
        print(f"stderr_lines {len(eng.err)}")
        for line in eng.err:
            if is_sanitizer(line):
                print(line.rstrip("\n"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"STOP {exc}", file=sys.stderr)
        raise
