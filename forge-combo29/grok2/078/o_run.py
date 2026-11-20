#!/usr/bin/env python3
"""o_run.py EXE OUT_PREFIX SWITCH [N]
SWITCH is omit, false, or true.
Reads ~/first200.fens. Writes OUT_PREFIX.raw (engine stdout) and OUT_PREFIX.meta.
S14 in the listed order, then Threads 1, then Hash 16, then IdeaK4 when SWITCH is not omit.
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
    ("Threads", "1"),
    ("Hash", "16"),
]

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def consume(proc, lines, pending, pred):
    while b"\n" in pending:
        raw, pending = pending.split(b"\n", 1)
        text = raw.decode("utf-8", "replace").rstrip("\r")
        lines.append(text)
        for bit in STOP_BITS:
            if bit in text:
                proc._pending = pending
                sys.exit("STOP " + text)
        if pred(text):
            proc._pending = pending
            return pending, True
    proc._pending = pending
    return pending, False


def read_until(proc, lines, pred, timeout):
    fd = proc.stdout.fileno()
    pending = getattr(proc, "_pending", b"")
    pending, done = consume(proc, lines, pending, pred)
    if done:
        return
    deadline = time.monotonic() + timeout
    while True:
        remain = deadline - time.monotonic()
        if remain <= 0:
            sys.exit("TIMEOUT last=" + repr(lines[-8:]))
        ready, _, _ = select.select([fd], [], [], min(1.0, remain))
        if not ready:
            if proc.poll() is not None:
                sys.exit(f"engine exited {proc.returncode} last={lines[-8:]!r}")
            continue
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            sys.exit(f"EOF last={lines[-8:]!r}")
        pending += chunk
        pending, done = consume(proc, lines, pending, pred)
        if done:
            return


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: o_run.py EXE OUT_PREFIX omit|false|true [N]")
    exe, out_prefix, switch = sys.argv[1], sys.argv[2], sys.argv[3]
    if switch not in ("omit", "false", "true"):
        sys.exit("SWITCH must be omit, false, or true")
    limit = int(sys.argv[4]) if len(sys.argv) == 5 else 200
    fens = [ln.strip() for ln in open(os.path.expanduser("~/first200.fens"), encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"expected 200 fens, got {len(fens)}")
    fens = fens[:limit]
    opts = list(S14)
    if switch != "omit":
        opts.append(("IdeaK4", switch))
    lines = []
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
    )
    proc._pending = b""

    def send(cmd):
        proc.stdin.write((cmd + "\n").encode())
        proc.stdin.flush()

    send("uci")
    read_until(proc, lines, lambda t: t == "uciok", 30)
    send("isready")
    read_until(proc, lines, lambda t: t == "readyok", 30)
    sent = []
    for name, value in opts:
        cmd = f"setoption name {name} value {value}"
        sent.append(cmd)
        send(cmd)
        send("isready")
        read_until(proc, lines, lambda t: t == "readyok", 30)
    for index, fen in enumerate(fens, 1):
        send("ucinewgame")
        send("isready")
        read_until(proc, lines, lambda t: t == "readyok", 30)
        send("position fen " + fen)
        send("isready")
        read_until(proc, lines, lambda t: t == "readyok", 30)
        send("go depth 12")
        read_until(proc, lines, lambda t: t.startswith("bestmove "), 300)
        if index % 25 == 0 or index == len(fens):
            print(f"positions {index}/{len(fens)}", flush=True)
    send("quit")
    proc.stdin.close()
    deadline = time.monotonic() + 10
    fd = proc.stdout.fileno()
    pending = proc._pending
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.5)
        if not ready:
            if proc.poll() is not None:
                break
            continue
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            break
        pending += chunk
    if pending:
        for raw in pending.split(b"\n"):
            if raw:
                lines.append(raw.decode("utf-8", "replace").rstrip("\r"))
    proc.wait(timeout=10)
    with open(out_prefix + ".raw", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    id_name = ""
    for text in lines:
        if text.startswith("id name "):
            id_name = text[len("id name "):]
            break
    with open(out_prefix + ".meta", "w", encoding="utf-8") as f:
        f.write(f"exe: {exe}\n")
        f.write(f"sha256: {sha256_file(exe)}\n")
        f.write(f"id name: {id_name}\n")
        f.write(f"switch: {switch}\n")
        f.write(f"fens: {os.path.expanduser('~/first200.fens')}\n")
        f.write("fen_sha256: ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8\n")
        f.write(f"positions: {len(fens)}\n")
        f.write("protocol: uci; isready; each setoption then isready; each position is ucinewgame, isready, position fen, isready, go depth 12, read until bestmove\n")
        f.write("options:\n")
        for cmd in sent:
            f.write(cmd + "\n")
    print(f"WROTE {out_prefix}.raw lines {len(lines)}", flush=True)


if __name__ == "__main__":
    main()
