#!/usr/bin/env python3
"""orun.py EXE FENS RAW META SWITCH

SWITCH is none (do not send the arm option), false, or true.
One engine process. Threads 1, Hash 16, then S14, then the switch when
SWITCH is not none, before every position. isready after every setoption
and after every position command. ucinewgame before every position (it
prints nothing). Stops on unknown option, invalid value, invalid FEN, or
illegal move.
"""
import hashlib
import os
import select
import subprocess
import sys
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
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str, err_path: str) -> None:
        self.err = open(err_path, "wb")
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err,
            bufsize=0,
        )
        self.buf = b""

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            if done(lines):
                return lines
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                sys.exit(f"STOP timeout after {timeout}s tail={lines[-8:]}")
            ready_fds, _, _ = select.select([self.proc.stdout], [], [], min(0.5, remaining))
            if not ready_fds:
                if self.proc.poll() is not None:
                    sys.exit(f"STOP engine exited rc={self.proc.returncode} tail={lines[-8:]}")
                continue
            chunk = os.read(self.proc.stdout.fileno(), 1 << 16)
            if not chunk:
                sys.exit(f"STOP engine closed stdout tail={lines[-8:]}")
            self.buf += chunk
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                lines.append(line)
                for bit in STOP_BITS:
                    if bit in line:
                        sys.exit(f"STOP {bit}: {line}")
                if done(lines):
                    return lines

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.err.close()


def last_is_readyok(lines: list[str]) -> bool:
    return bool(lines) and lines[-1] == "readyok"


def last_is_uciok(lines: list[str]) -> bool:
    return bool(lines) and lines[-1] == "uciok"


def last_is_bestmove(lines: list[str]) -> bool:
    return bool(lines) and lines[-1].startswith("bestmove ")


def main() -> None:
    if len(sys.argv) != 6:
        sys.exit("usage: orun.py EXE FENS RAW META SWITCH")
    exe, fens_path, raw_path, meta_path, switch = sys.argv[1:]
    if switch not in ("none", "false", "true"):
        sys.exit(f"STOP bad switch {switch}")
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP fen count {len(fens)}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe, raw_path + ".err")
    transcript: list[str] = []
    sent: list[str] = []

    def command(line: str, timeout: float, done) -> list[str]:
        sent.append(line)
        eng.send(line)
        got = eng.read_until(done, timeout)
        transcript.extend(got)
        return got

    ident = command("uci", 30, last_is_uciok)
    id_name = ""
    for line in ident:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    if not id_name:
        sys.exit("STOP no id name")
    command("isready", 60, last_is_readyok)

    options = [("Threads", "1"), ("Hash", "16"), *S14]
    if switch != "none":
        options.append(("IdeaS32", switch))

    def send_then_ready(line: str, timeout: float = 30) -> None:
        # setoption, ucinewgame and position print nothing when they succeed.
        # isready is what produces readyok, and it flushes any refusal line first.
        sent.append(line)
        eng.send(line)
        command("isready", timeout, last_is_readyok)

    for index, fen in enumerate(fens, start=1):
        for name, value in options:
            send_then_ready(f"setoption name {name} value {value}")
        send_then_ready("ucinewgame", 60)
        send_then_ready(f"position fen {fen}")
        command("go depth 12", 180, last_is_bestmove)
        if index % 20 == 0:
            print(f"position {index}", flush=True)

    eng.close()
    with open(raw_path, "w", encoding="utf-8") as raw:
        raw.write("\n".join(transcript) + "\n")
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {sha}\n")
        meta.write(f"id name {id_name}\n")
        meta.write(f"switch {switch}\n")
        meta.write("option lines:\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
        meta.write(f"positions {len(fens)}\n")
        meta.write(f"commands_sent {len(sent)}\n")
    print(f"orun wrote {raw_path}")


if __name__ == "__main__":
    main()
