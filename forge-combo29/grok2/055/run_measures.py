#!/usr/bin/env python3
"""Honesty benches and the three O runs. Written before it is run.

A fresh process for each honesty command, with no setoption.
Each O run is one process: S14, Threads 1, Hash 16, then ucinewgame
and isready before every position, go depth 12.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FENS = ROOT / "first200.fens"
EXE_B = "/tmp/builds/base/forge"
EXE_P = "/tmp/builds/work/forge"
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
HONESTY = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.q = queue.Queue()
        self.lines = []

        def reader():
            for raw in iter(self.proc.stdout.readline, b""):
                self.q.put(raw.decode("utf-8", "replace").rstrip("\r\n"))
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        got = []
        deadline = time.time() + timeout
        while True:
            remain = deadline - time.time()
            if remain <= 0:
                tail = self.lines[-4:]
                raise SystemExit(f"TIMEOUT after {timeout}s last={tail}")
            try:
                line = self.q.get(timeout=remain)
            except queue.Empty:
                tail = self.lines[-4:]
                raise SystemExit(f"TIMEOUT after {timeout}s last={tail}")
            if line is None:
                tail = self.lines[-6:]
                raise SystemExit(f"EOF last={tail}")
            self.lines.append(line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP {line}")
            if pred(line):
                return got

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def id_name_of(exe):
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda s: s == "uciok", 30)
    finally:
        eng.close()
    for line in eng.lines:
        if line.startswith("id name "):
            return line[len("id name "):]
    raise SystemExit(f"no id name from {exe}")


def write_meta(path, exe, digest, id_name, options, command):
    body = [
        f"exe: {exe}",
        f"sha256: {digest}",
        f"id name: {id_name}",
        "options:",
    ]
    if options:
        body.extend(options)
    else:
        body.append("(none)")
    body.append(f"command: {command}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def honesty_nodes(lines, command):
    if command.startswith("bench"):
        hits = [s for s in lines if s.startswith("info string bench ")]
        if len(hits) != 1:
            raise SystemExit(f"bench lines {hits}")
        parts = hits[0].split()
        return parts[parts.index("nodes") + 1]
    hits = [s for s in lines if s.startswith("nodes ")]
    if len(hits) != 1:
        raise SystemExit(f"perft node lines {hits}")
    return hits[0].split()[1]


def run_honesty(tag, exe, digest, id_name):
    print(f"honesty {tag} {exe}", flush=True)
    for name, command, expected in HONESTY:
        eng = Engine(exe)
        try:
            eng.send(command)
            timeout = 180 if "16" in command or "perft" in command else 90
            if command.startswith("bench"):
                eng.read_until(lambda s: s.startswith("info string bench "), timeout)
            else:
                eng.read_until(lambda s: s.startswith("nodes "), timeout)
        finally:
            eng.close()
        out = ROOT / f"honesty_{tag}_{name}.txt"
        out.write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
        write_meta(
            ROOT / f"honesty_{tag}_{name}.txt.meta",
            exe,
            digest,
            id_name,
            [],
            command + "  (measured process received only this command; id name is from a fresh uci probe of the same exe)",
        )
        got = honesty_nodes(eng.lines, command)
        print(f"  {command} nodes {got} expected {expected}", flush=True)
        if got != expected:
            raise SystemExit(f"HONESTY MISS {tag} {command} got {got} expected {expected}")


def option_lines(switch):
    lines = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
    ]
    lines.extend(f"setoption name {name} value {value}" for name, value in S14)
    if switch is not None:
        lines.append(f"setoption name IdeaS10 value {switch}")
    return lines


def run_o(tag, exe, digest, id_name, switch):
    print(f"O {tag} switch={switch}", flush=True)
    fens = [ln.strip() for ln in FENS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(fens) != 200:
        raise SystemExit(f"fen count {len(fens)}")
    eng = Engine(exe)
    opts = option_lines(switch)
    try:
        eng.send("uci")
        eng.read_until(lambda s: s == "uciok", 30)
        eng.send("isready")
        eng.read_until(lambda s: s == "readyok", 30)
        for line in opts:
            eng.send(line)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
        for i, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok", 30)
            t0 = time.time()
            eng.send("go depth 12")
            eng.read_until(lambda s: s.startswith("bestmove "), 180)
            if i == 1 or i % 25 == 0 or i == 200:
                print(f"  {tag} position {i} in {time.time() - t0:.2f}s", flush=True)
    finally:
        eng.close()
    out = ROOT / f"o_{tag}.txt"
    out.write_text("\n".join(eng.lines) + "\n", encoding="utf-8")
    write_meta(ROOT / f"o_{tag}.txt.meta", exe, digest, id_name, opts, "go depth 12 on first200.fens")
    print(f"  wrote {out} lines {len(eng.lines)}", flush=True)


def main():
    if sha256_file(FENS) != "ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8":
        raise SystemExit("FEN FILE SHA DIFFERS")
    digest_b = sha256_file(EXE_B)
    digest_p = sha256_file(EXE_P)
    id_b = id_name_of(EXE_B)
    id_p = id_name_of(EXE_P)
    print(f"id B {id_b}", flush=True)
    print(f"id P {id_p}", flush=True)
    print(f"sha B {digest_b}", flush=True)
    print(f"sha P {digest_p}", flush=True)
    run_honesty("B", EXE_B, digest_b, id_b)
    run_honesty("P", EXE_P, digest_p, id_p)
    run_o("B", EXE_B, digest_b, id_b, None)
    run_o("Poff", EXE_P, digest_p, id_p, "false")
    run_o("Pon", EXE_P, digest_p, id_p, "true")
    print("MEASURES DONE", flush=True)


if __name__ == "__main__":
    main()
