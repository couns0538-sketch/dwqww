#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process. isready after every setoption and position.

Stop on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading
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
INFO_RE = re.compile(r"^info depth (\d+) .* nodes (\d+) ")
SCORE_RE = re.compile(r" score (cp|mate) (-?\d+) ")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def start_reader(proc):
    box = queue.Queue()

    def pump():
        for line in proc.stdout:
            box.put(line)
        box.put(None)

    threading.Thread(target=pump, daemon=True).start()
    return box


def read_until(box, prefix, timeout_s):
    collected = []
    deadline = time.time() + timeout_s
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError("timeout after %d lines" % len(collected))
        try:
            line = box.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("timeout after %d lines" % len(collected)) from exc
        if line is None:
            raise RuntimeError("engine exited after %d lines" % len(collected))
        collected.append(line)
        if any(bit in line for bit in STOP_BITS):
            raise RuntimeError("STOP " + line.rstrip("\n"))
        if line.startswith(prefix):
            return collected


def send(proc, command):
    proc.stdin.write(command + "\n")
    proc.stdin.flush()


def load_fens(path):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # EPD or FEN: the first six fields are a FEN. Shorter lines stay whole.
            fields = line.split()
            fen = " ".join(fields[:6]) if len(fields) >= 6 else line
            fens.append(fen)
    return fens


def main():
    if len(sys.argv) < 5:
        print("usage: measure_depth.py EXE FENS DEPTH OUTPREFIX [--switch omit|false|true] [--expect-sum N] [--expect-first a,b,c]", file=sys.stderr)
        return 2
    exe = os.path.abspath(sys.argv[1])
    fens_path = os.path.abspath(sys.argv[2])
    depth = int(sys.argv[3])
    out_prefix = os.path.abspath(sys.argv[4])
    switch = "omit"
    expect_sum = None
    expect_first = None
    args = sys.argv[5:]
    i = 0
    while i < len(args):
        if args[i] == "--switch":
            switch = args[i + 1]
            i += 2
        elif args[i] == "--expect-sum":
            expect_sum = int(args[i + 1])
            i += 2
        elif args[i] == "--expect-first":
            expect_first = [int(part) for part in args[i + 1].split(",")]
            i += 2
        else:
            print("bad arg " + args[i], file=sys.stderr)
            return 2
    if switch not in ("omit", "false", "true"):
        print("bad switch", file=sys.stderr)
        return 2
    options = list(S14)
    if switch != "omit":
        options.append(("IdeaS24", switch))
    fens = load_fens(fens_path)
    digest = sha256_file(exe)
    err_path = out_prefix + ".err"
    with open(err_path, "w", encoding="utf-8") as err_handle:
        proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err_handle,
            text=True,
            bufsize=1,
        )
        box = start_reader(proc)
        raw_lines = []
        rows = []
        id_name = ""
        try:
            send(proc, "uci")
            uci_lines = read_until(box, "uciok", 30)
            raw_lines.extend(uci_lines)
            for line in uci_lines:
                if line.startswith("id name "):
                    id_name = line[len("id name "):].rstrip("\n")
            sent_options = []
            for name, value in options:
                command = "setoption name %s value %s" % (name, value)
                sent_options.append(command)
                send(proc, command)
                send(proc, "isready")
                ready = read_until(box, "readyok", 30)
                raw_lines.extend(ready)
            for index, fen in enumerate(fens):
                send(proc, "ucinewgame")
                send(proc, "isready")
                raw_lines.extend(read_until(box, "readyok", 30))
                send(proc, "position fen " + fen)
                send(proc, "isready")
                raw_lines.extend(read_until(box, "readyok", 30))
                send(proc, "go depth %d" % depth)
                played = read_until(box, "bestmove", 120)
                raw_lines.extend(played)
                nodes = None
                shown_depth = None
                score_kind = ""
                score_value = ""
                for line in played:
                    match = INFO_RE.search(line)
                    if match:
                        shown_depth = int(match.group(1))
                        nodes = int(match.group(2))
                        score = SCORE_RE.search(line)
                        if score:
                            score_kind = score.group(1)
                            score_value = score.group(2)
                if nodes is None:
                    raise RuntimeError("no info line for position %d" % index)
                best = played[-1].split()
                bestmove = best[1] if len(best) > 1 else ""
                rows.append((index, nodes, shown_depth, score_kind, score_value, bestmove))
            send(proc, "quit")
            proc.wait(timeout=20)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    with open(out_prefix + ".txt", "w", encoding="utf-8") as handle:
        handle.writelines(raw_lines)
    with open(out_prefix + ".rows", "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write("%d\t%d\t%d\t%s\t%s\t%s\n" % row)
    with open(out_prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write("exe %s\n" % exe)
        handle.write("sha256 %s\n" % digest)
        handle.write("id name %s\n" % id_name)
        handle.write("options\n")
        for command in sent_options:
            handle.write(command + "\n")
        handle.write("fens %s\n" % fens_path)
        handle.write("depth %d\n" % depth)
        handle.write("positions %d\n" % len(fens))
    total = sum(row[1] for row in rows)
    first = [row[1] for row in rows[:3]]
    summary = "positions %d sum %d first %s\n" % (len(rows), total, " ".join(str(n) for n in first))
    ok = True
    if expect_sum is not None and total != expect_sum:
        ok = False
        summary += "FAIL sum expected %d\n" % expect_sum
    if expect_first is not None and first != expect_first:
        ok = False
        summary += "FAIL first expected %s\n" % " ".join(str(n) for n in expect_first)
    if ok and (expect_sum is not None or expect_first is not None):
        summary += "PASS\n"
    with open(out_prefix + ".sum", "w", encoding="utf-8") as handle:
        handle.write(summary)
    sys.stdout.write(summary)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
