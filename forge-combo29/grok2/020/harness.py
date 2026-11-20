#!/usr/bin/env python3
"""UCI harness for Grok swarm 2 seat 020 arm 10.

  python3 harness.py honesty <exe> <out_prefix>
      fresh process per line, no setoption. Writes <prefix>_bench11.txt and .meta,
      and the same for bench13, bench16, perft5.
  python3 harness.py orun <exe> <raw_out> <switch>
      switch is none, false, or true (HindsightDepth). One process, S14 then
      Threads 1, Hash 16, then the switch when it is not none. 200 FENs.
"""
import hashlib
import os
import select
import subprocess
import sys
import time

FENS = os.path.expanduser("~/first200.fens")
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.pending = b""
        self.lines = []

    def send(self, text):
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def _pull(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            if b"\n" in self.pending:
                raw, self.pending = self.pending.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                self.lines.append(line)
                for bit in STOP_BITS:
                    if bit in line:
                        raise ProtocolError(line)
                return line
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError(
                    "no line within timeout; last=%r" % (self.lines[-3:],)
                )
            ready, _, _ = select.select([self.proc.stdout], [], [], min(0.5, remain))
            if not ready:
                if self.proc.poll() is not None and not self.pending:
                    raise ProtocolError("engine exited: last=%r" % (self.lines[-5:],))
                continue
            chunk = os.read(self.proc.stdout.fileno(), 1 << 16)
            if not chunk:
                if self.pending:
                    line = self.pending.decode("utf-8", "replace").rstrip("\r")
                    self.pending = b""
                    self.lines.append(line)
                    return line
                raise ProtocolError("engine closed stdout: last=%r" % (self.lines[-5:],))
            self.pending += chunk

    def read_until(self, predicate, timeout):
        start = len(self.lines)
        deadline = time.monotonic() + timeout
        while True:
            if predicate(self.lines[start:]):
                return self.lines[start:]
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError("predicate timeout; last=%r" % (self.lines[-5:],))
            self._pull(remain)

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def id_name_from(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def write_meta(path, exe, id_name, options, extra):
    with open(path, "w", encoding="utf-8") as f:
        f.write("exe %s\n" % exe)
        f.write("sha256 %s\n" % sha256_file(exe))
        f.write("id name %s\n" % id_name)
        f.write("options\n")
        if not options:
            f.write("(none)\n")
        for opt in options:
            f.write(opt + "\n")
        for line in extra:
            f.write(line + "\n")


def open_engine(exe):
    eng = Engine(exe)
    eng.send("uci")
    banner = eng.read_until(lambda ls: any(x == "uciok" for x in ls), 30)
    return eng, id_name_from(banner)


def honesty_one(exe, command, out_path, ready_pred, timeout):
    eng, id_name = open_engine(exe)
    error = None
    try:
        eng.send(command)
        eng.read_until(ready_pred, timeout)
    except (ProtocolError, TimeoutError) as exc:
        error = exc
    text = "\n".join(eng.lines) + "\n"
    eng.close()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    write_meta(out_path + ".meta", exe, id_name, [], ["command %s" % command])
    if error is not None:
        raise error
    return text


def cmd_honesty(exe, prefix):
    jobs = [
        ("bench 11", prefix + "_bench11.txt", lambda ls: any(x.startswith("info string bench ") for x in ls), 120),
        ("bench 13", prefix + "_bench13.txt", lambda ls: any(x.startswith("info string bench ") for x in ls), 180),
        ("bench 16", prefix + "_bench16.txt", lambda ls: any(x.startswith("info string bench ") for x in ls), 300),
        ("go perft 5", prefix + "_perft5.txt", lambda ls: any(x.startswith("nodes ") for x in ls), 180),
    ]
    for command, out_path, pred, timeout in jobs:
        print("honesty %s -> %s" % (command, out_path), flush=True)
        honesty_one(exe, command, out_path, pred, timeout)
        print("wrote %s" % out_path, flush=True)


def option_line(name, value):
    return "setoption name %s value %s" % (name, value)


def apply_option(eng, name, value):
    line = option_line(name, value)
    eng.send(line)
    eng.send("isready")
    eng.read_until(lambda ls: any(x == "readyok" for x in ls), 30)
    return line


def cmd_orun(exe, raw_out, switch):
    if switch not in ("none", "false", "true"):
        sys.exit("switch must be none, false, or true")
    with open(FENS, encoding="utf-8") as f:
        fens = [ln.strip() for ln in f if ln.strip()]
    if len(fens) != 200:
        sys.exit("expected 200 fens, got %d" % len(fens))
    eng, id_name = open_engine(exe)
    options = []
    error = None
    try:
        for name, value in S14:
            options.append(apply_option(eng, name, value))
        options.append(apply_option(eng, "Threads", "1"))
        options.append(apply_option(eng, "Hash", "16"))
        if switch != "none":
            options.append(apply_option(eng, "HindsightDepth", switch))
        for index, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda ls: any(x == "readyok" for x in ls), 30)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda ls: any(x == "readyok" for x in ls), 30)
            eng.send("go depth 12")
            eng.read_until(lambda ls: any(x.startswith("bestmove ") for x in ls), 180)
            if index % 20 == 0:
                print("position %d" % index, flush=True)
    except (ProtocolError, TimeoutError) as exc:
        error = exc
    text = "\n".join(eng.lines) + "\n"
    eng.close()
    with open(raw_out, "w", encoding="utf-8") as f:
        f.write(text)
    write_meta(
        raw_out + ".meta",
        exe,
        id_name,
        options,
        [
            "fens %s" % FENS,
            "fens_sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8",
            "switch %s" % switch,
            "go depth 12",
        ],
    )
    print("wrote %s" % raw_out, flush=True)
    if error is not None:
        raise error


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mode = sys.argv[1]
    if mode == "honesty":
        cmd_honesty(sys.argv[2], sys.argv[3])
    elif mode == "orun":
        cmd_orun(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except (ProtocolError, TimeoutError) as exc:
        print("STOP %s" % exc, file=sys.stderr)
        sys.exit(1)
