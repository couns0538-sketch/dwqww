#!/usr/bin/env python3
"""o_run.py EXE FENS OUT_PREFIX [SWITCH true|false]
One engine process. S14, Threads 1, Hash 16, then the switch when given.
ucinewgame + isready before every position; isready after every setoption and position.
go depth 12. Full transcript in OUT_PREFIX.raw and OUT_PREFIX.meta.
"""
import hashlib
import os
import select
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Session:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        self.fd = self.proc.stdout.fileno()
        os.set_blocking(self.fd, False)
        self.buf = b""
        self.log = []

    def send(self, line):
        self.log.append((">>", line))
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if not ready:
                raise SystemExit("STOP: timeout waiting for engine")
            chunk = os.read(self.fd, 1 << 16)
            if chunk == b"":
                raise SystemExit("STOP: unexpected EOF")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")

    def read_until(self, done, timeout):
        while True:
            text = self.readline(timeout)
            self.log.append(("<<", text))
            for stop in STOPS:
                if stop in text:
                    raise SystemExit(f"STOP: {text}")
            if done(text):
                return text

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=30)
        finally:
            if self.proc.poll() is None:
                self.proc.kill()


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: o_run.py EXE FENS OUT_PREFIX [SWITCH true|false]")
    exe, fens_path, out_prefix = sys.argv[1:4]
    switch = None
    if len(sys.argv) == 6:
        switch = (sys.argv[4], sys.argv[5])
        if switch[1] not in ("true", "false"):
            sys.exit("switch value must be true or false")
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch is not None:
        options.append(switch)
    session = Session(exe)
    id_name = ""
    try:
        session.send("uci")
        session.read_until(lambda t: t == "uciok", 30)
        for text_dir, text in session.log:
            if text_dir == "<<" and text.startswith("id name "):
                id_name = text[len("id name "):]
        for name, value in options:
            session.send(f"setoption name {name} value {value}")
            session.send("isready")
            session.read_until(lambda t: t == "readyok", 30)
        for index, fen in enumerate(fens, start=1):
            session.send("ucinewgame")
            session.send("isready")
            session.read_until(lambda t: t == "readyok", 30)
            session.send(f"position fen {fen}")
            session.send("isready")
            session.read_until(lambda t: t == "readyok", 30)
            session.send("go depth 12")
            session.read_until(lambda t: t.startswith("bestmove "), 180)
            if index % 50 == 0:
                print(f"{out_prefix} {index}/{len(fens)}", flush=True)
    finally:
        raw_path = out_prefix + ".raw"
        with open(raw_path, "w", encoding="utf-8") as f:
            for direction, text in session.log:
                f.write(f"{direction} {text}\n")
        with open(out_prefix + ".meta", "w", encoding="utf-8") as f:
            f.write(f"exe={exe}\n")
            f.write(f"sha256={sha256_file(exe)}\n")
            f.write(f"id_name={id_name}\n")
            f.write(f"fens={fens_path}\n")
            f.write(f"fens_sha256={sha256_file(fens_path)}\n")
            f.write(f"fens_count={len(fens)}\n")
            f.write("options=\n")
            for name, value in options:
                f.write(f"setoption name {name} value {value}\n")
        session.close()
    print(f"wrote {out_prefix}.raw")


if __name__ == "__main__":
    main()
