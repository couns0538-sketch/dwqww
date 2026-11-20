#!/usr/bin/env python3
"""One fresh engine process. Reads every line. Stops on a bad reply."""
import hashlib
import os
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 4:
        print("usage: uci_one.py EXE OUT_PREFIX CMD...", file=sys.stderr)
        return 2
    exe = os.path.abspath(sys.argv[1])
    prefix = sys.argv[2]
    commands = sys.argv[3:]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    sent = []
    out_lines = []
    id_name = ""

    def send(line):
        sent.append(line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(ok):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                err = proc.stderr.read()
                raise SystemExit("stdout closed\n" + err)
            line = line.rstrip("\r\n")
            out_lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit("STOP " + line)
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
            if ok(line):
                return line

    send("uci")
    read_until(lambda s: s == "uciok")
    send("isready")
    read_until(lambda s: s == "readyok")
    for cmd in commands:
        send(cmd)
        if cmd == "isready":
            read_until(lambda s: s == "readyok")
        elif cmd.startswith("bench"):
            read_until(lambda s: " nodes " in s and s.startswith("info string bench"))
        elif cmd.startswith("go perft"):
            read_until(lambda s: s.startswith("nodes "))
        elif cmd.startswith("go"):
            read_until(lambda s: s.startswith("bestmove "))
        elif cmd.startswith("position") or cmd.startswith("setoption") or cmd == "ucinewgame":
            send("isready")
            read_until(lambda s: s == "readyok")
        else:
            raise SystemExit("unhandled command " + cmd)
    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    err = proc.stderr.read()
    with open(prefix + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    with open(prefix + ".err", "w", encoding="utf-8") as f:
        f.write(err)
    with open(prefix + ".meta", "w", encoding="utf-8") as f:
        f.write("exe=" + exe + "\n")
        f.write("sha256=" + sha256(exe) + "\n")
        f.write("id_name=" + id_name + "\n")
        f.write("option_lines:\n")
        opts = [s for s in sent if s.startswith("setoption")]
        if not opts:
            f.write("(none)\n")
        else:
            for s in opts:
                f.write(s + "\n")
        f.write("commands:\n")
        for s in sent:
            f.write(s + "\n")
    if err.strip():
        print("STDERR none-empty", file=sys.stderr)
        print(err, file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(1)
        raise
