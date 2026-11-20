#!/usr/bin/env python3
"""UCI harness for Grok swarm 2 seat 054. Honesty benches and the three O runs.

  python3 harness.py honesty EXE OUTPREFIX
  python3 harness.py orun EXE OUTPREFIX SWITCH|none true|false FENS
  python3 harness.py summarize DIR
"""
import hashlib
import re
import subprocess
import sys

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = (
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
    ("Threads", "1"),
    ("Hash", "16"),
)


class Stop(Exception):
    pass


class Eng:
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
        self.out = []
        self.id_name = ""

    def send(self, line):
        if self.proc.stdin is None:
            raise Stop("stdin closed")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        if self.proc.stdout is None:
            raise Stop("stdout closed")
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise Stop("engine closed stdout")
            line = line.rstrip("\n")
            self.out.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise Stop(line)
            if done(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except Stop:
            pass
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def uci(self):
        self.send("uci")
        while True:
            line = self.read_until(lambda s: s.startswith("id name ") or s == "uciok")
            if line.startswith("id name "):
                self.id_name = line
            if line == "uciok":
                return

    def setoptions(self, pairs):
        sent = []
        for name, value in pairs:
            cmd = f"setoption name {name} value {value}"
            self.send(cmd)
            sent.append(cmd)
            self.send("isready")
            self.read_until(lambda s: s == "readyok")
        return sent


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_meta(path, exe, digest, id_name, options):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write(f"sha256 {digest}\n")
        f.write(f"id {id_name}\n")
        if options:
            for line in options:
                f.write(line + "\n")
        else:
            f.write("options none\n")


def honesty(exe, prefix):
    digest = sha256_file(exe)
    jobs = ("bench 11", "bench 13", "bench 16", "go perft 5")
    for cmd in jobs:
        eng = Eng(exe)
        try:
            eng.uci()
            eng.send(cmd)
            if cmd.startswith("bench"):
                eng.read_until(lambda s: s.startswith("info string bench "))
            else:
                eng.read_until(lambda s: s.startswith("nodes "))
        finally:
            eng.close()
        tag = cmd.replace(" ", "")
        raw = prefix + "_" + tag + ".txt"
        with open(raw, "w", encoding="utf-8") as f:
            f.write("\n".join(eng.out) + "\n")
        write_meta(prefix + "_" + tag + ".meta", exe, digest, eng.id_name, [])
        print(f"honesty {cmd} -> {raw}")


def orun(exe, prefix, switch, value, fens_path):
    digest = sha256_file(exe)
    with open(fens_path, encoding="utf-8") as f:
        fens = [ln.strip() for ln in f if ln.strip()]
    eng = Eng(exe)
    options = list(S14)
    if switch != "none":
        options.append((switch, value))
    try:
        eng.uci()
        sent = eng.setoptions(options)
        for fen in fens:
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda s: s == "readyok")
            eng.send("go depth 12")
            eng.read_until(lambda s: s.startswith("bestmove "))
    finally:
        eng.close()
    with open(prefix + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(eng.out) + "\n")
    write_meta(prefix + ".meta", exe, digest, eng.id_name, sent)
    print(f"orun {len(fens)} positions -> {prefix}.txt")


def nodes_of(line):
    m = re.search(r"\bnodes (\d+)\b", line)
    return int(m.group(1)) if m else None


def honesty_nodes(path):
    text = open(path, encoding="utf-8").read().splitlines()
    for line in reversed(text):
        n = nodes_of(line)
        if n is not None and (line.startswith("info string bench ") or line.startswith("nodes ")):
            return n
    return None


def orun_rows(path):
    rows = []
    cur = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        cur.append(line)
        if line.startswith("bestmove "):
            last = None
            for item in cur:
                if item.startswith("info ") and nodes_of(item) is not None and not item.startswith("info string"):
                    last = item
            if last is None:
                raise SystemExit(f"no info nodes before bestmove in {path} game {len(rows) + 1}")
            rows.append(nodes_of(last))
            cur = []
    return rows


def summarize(directory):
    expect = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "goperft5": 4865609,
    }
    print("honesty")
    for side in ("B", "P"):
        for key, want in expect.items():
            path = f"{directory}/honesty_{side}_{key}.txt"
            got = honesty_nodes(path)
            mark = "ok" if got == want else "MISS"
            print(f"  {side} {key} {got} want {want} {mark}")
    b = orun_rows(f"{directory}/o_B.txt")
    off = orun_rows(f"{directory}/o_P_off.txt")
    on = orun_rows(f"{directory}/o_P_on.txt")
    print(f"o_B n {len(b)} sum {sum(b)} first {b[0]} {b[1]} {b[2]}")
    print(f"o_P_off n {len(off)} sum {sum(off)} first {off[0]} {off[1]} {off[2]}")
    same = sum(1 for x, y in zip(b, off) if x == y)
    differ = sum(1 for x, y in zip(b, on) if x != y)
    print(f"off_equal {same} of {len(b)}")
    print(f"o_P_on n {len(on)} sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ {differ}")


def main():
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3])
    elif mode == "orun":
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif mode == "summarize":
        summarize(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print(f"STOP {exc}", file=sys.stderr)
        raise SystemExit(1)
