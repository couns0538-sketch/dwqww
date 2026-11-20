#!/usr/bin/env python3
"""orun.py: one depth-12 pass over a FEN list.

Options are sent once (they persist; ucinewgame does not clear them), then each
position is ucinewgame + isready, position + isready, go depth 12. After every
setoption and every position the harness reads every line up to readyok. It
stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import argparse
import hashlib
import subprocess
import sys

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--switch")
    ap.add_argument("--value", choices=("true", "false"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if (args.switch is None) != (args.value is None):
        sys.exit("switch and value are a pair")
    fens = [ln.strip() for ln in open(args.fens, encoding="utf-8") if ln.strip()]
    if args.limit:
        fens = fens[: args.limit]
    sha = hashlib.sha256(open(args.exe, "rb").read()).hexdigest()
    options = [("Threads", "1"), ("Hash", "16"), *S14]
    if args.switch:
        options.append((args.switch, args.value))

    proc = subprocess.Popen(
        [args.exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    logf = open(args.out, "w", encoding="utf-8")
    id_name = ""

    def send(cmd):
        logf.write(">> " + cmd + "\n")
        logf.flush()
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def read_until(done):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit("STOP: eof from engine")
            line = line.rstrip("\n")
            logf.write(line + "\n")
            logf.flush()
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
            for bad in BAD:
                if bad in line:
                    logf.close()
                    proc.kill()
                    sys.exit(f"STOP: {line}")
            if done(line):
                return

    try:
        send("uci")
        read_until(lambda line: line == "uciok")
        for name, value in options:
            send(f"setoption name {name} value {value}")
            send("isready")
            read_until(lambda line: line == "readyok")
        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line == "readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda line: line == "readyok")
            send("go depth 12")
            read_until(lambda line: line.startswith("bestmove "))
        send("quit")
    finally:
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
        if not logf.closed:
            logf.close()
        meta = args.out.rsplit(".", 1)[0] + ".meta"
        with open(meta, "w", encoding="utf-8") as m:
            m.write(f"exe: {args.exe}\n")
            m.write(f"sha256: {sha}\n")
            m.write(f"id_name: {id_name}\n")
            m.write("options:\n")
            for name, value in options:
                m.write(f"setoption name {name} value {value}\n")
        print(f"wrote {args.out} positions {len(fens)} id {id_name}", flush=True)


if __name__ == "__main__":
    main()
