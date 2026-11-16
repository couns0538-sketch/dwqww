#!/usr/bin/env python3
"""terminalrun.py EXE OUTDIR [--go "depth 5"] ...

Runs each position with the given `go` word sequence, reads stdout until `bestmove`,
records the transcript. Used for both the real ASan build and the PLANTED-FAULT scratch
build, through the same code path (that is the point of the proof).

A position file line is either a FEN or, when prefixed with "moves:", a
`position startpos moves ...` command.
"""
import argparse
import json
import os
import subprocess
import time


def load_positions(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("moves:"):
            out.append("position startpos moves " + line[6:].strip())
        else:
            out.append("position fen " + line)
    return out


def run_one(exe, poscmd, gocmd, timeout=60):
    t0 = time.monotonic()
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    try:
        send("uci")
        while True:
            l = proc.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("uciok"):
                break
        send("setoption name Threads value 1")
        send("setoption name Hash value 16")
        for k, v in [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
                     ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"),
                     ("NullMoveBase", "5"), ("LmpBase", "8"),
                     ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
                     ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
                     ("SingularDepth", "6"), ("IirDepth", "2"),
                     ("NonPawnCorrection", "true")]:
            send("setoption name %s value %s" % (k, v))
        send("isready")
        while True:
            l = proc.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.strip() == "readyok":
                break
        send("ucinewgame")
        send("isready")
        while True:
            l = proc.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.strip() == "readyok":
                break
        send(poscmd)
        send("isready")
        while True:
            l = proc.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.strip() == "readyok":
                break
        send("go " + gocmd)
        got_best = False
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            l = proc.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                got_best = True
                break
        send("quit")
        try:
            proc.wait(timeout=10)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = "KILLED"
    except (BrokenPipeError, OSError) as e:
        rc = "PIPE_ERROR:%s" % e
        got_best = False
    wall = time.monotonic() - t0
    return {"lines": lines, "bestmove_found": got_best, "exit": rc, "wall_ms": int(wall * 1000)}


def sanitizer_lines(lines):
    pats = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY: AddressSanitizer",
            "ERROR: UndefinedBehaviorSanitizer", "AddressSanitizer:DEADLYSIGNAL")
    return [l for l in lines if any(p in l for p in pats)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("--positions", required=True)
    ap.add_argument("--go", action="append", default=None)
    ap.add_argument("--label", default="run")
    a = ap.parse_args()
    gos = a.go or ["depth 5", "nodes 100", "movetime 50"]
    os.makedirs(a.outdir, exist_ok=True)
    positions = load_positions(a.positions)

    meta = os.path.join(a.outdir, "meta_%s.txt" % a.label)
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write("exe_started: %s\n" % os.path.abspath(a.exe))
        fh.write("sha256: %s\n" % subprocess.run(["sha256sum", os.path.abspath(a.exe)],
                                                 capture_output=True, text=True).stdout.split()[0])
        for sym in ("__asan_", "__ubsan_", "__tsan_"):
            n = subprocess.run(["bash", "-c", "nm -C %s | grep -c %s" % (os.path.abspath(a.exe), sym)],
                               capture_output=True, text=True).stdout.strip()
            fh.write("nm_count %s: %s\n" % (sym, n))
        uci = subprocess.run([a.exe], input="uci\nquit\n", capture_output=True, text=True).stdout
        if "id name " in uci:
            fh.write("id_name: %s\n" % uci.split("id name ")[1].splitlines()[0])
        fh.write("options_sent: Threads 1, Hash 16, S14\n")
        fh.write("go_kinds: %s\n" % gos)

    recs = []
    for i, pos in enumerate(positions):
        for g in gos:
            r = run_one(a.exe, pos, g)
            r.update({"idx": i, "position": pos, "go": g})
            recs.append(r)
            with open(os.path.join(a.outdir, "%s_%03d_%s.txt" % (a.label, i,
                        g.replace(" ", ""))), "w", encoding="utf-8") as fh:
                fh.write("### %s\n### go %s\n" % (pos, g))
                fh.write("\n".join(r["lines"]) + "\n")
        print("pos %d/%d" % (i + 1, len(positions)), flush=True)

    with open(os.path.join(a.outdir, "%s.jsonl" % a.label), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps({k: v for k, v in r.items() if k != "lines"}) + "\n")

    n_san = sum(1 for r in recs if sanitizer_lines(r["lines"]))
    print("runs %d  runs_with_sanitizer_lines %d" % (len(recs), n_san))


if __name__ == "__main__":
    main()
