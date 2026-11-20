#!/usr/bin/env python3
"""Run depth searches under a sanitizer build. Same option protocol as measure_depth.

Saves stdout, stderr, and a .meta that includes the count from
nm -C EXE | grep -c __asan_
A dead engine is recorded; the stderr is still kept.
"""
import hashlib
import os
import queue
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
    ("IdeaS24", "true"),
]
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asan_symbol_count(exe):
    proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    return sum(1 for line in proc.stdout.splitlines() if "__asan_" in line)


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
    if proc.poll() is not None:
        raise RuntimeError("engine exited before " + command)
    proc.stdin.write(command + "\n")
    proc.stdin.flush()


def load_fens(path, limit):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            fens.append(" ".join(fields[:6]) if len(fields) >= 6 else line)
            if limit and len(fens) >= limit:
                break
    return fens


def main():
    if len(sys.argv) < 5:
        print("usage: san_run.py EXE FENS DEPTH OUTPREFIX [--limit N]", file=sys.stderr)
        return 2
    exe = os.path.abspath(sys.argv[1])
    fens_path = os.path.abspath(sys.argv[2])
    depth = int(sys.argv[3])
    out_prefix = os.path.abspath(sys.argv[4])
    limit = 0
    if len(sys.argv) >= 7 and sys.argv[5] == "--limit":
        limit = int(sys.argv[6])
    fens = load_fens(fens_path, limit)
    symbol_count = asan_symbol_count(exe)
    raw_lines = []
    note = "ok"
    finished = 0
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
        try:
            send(proc, "uci")
            raw_lines.extend(read_until(box, "uciok", 60))
            for name, value in S14:
                send(proc, "setoption name %s value %s" % (name, value))
                send(proc, "isready")
                raw_lines.extend(read_until(box, "readyok", 60))
            for fen in fens:
                send(proc, "ucinewgame")
                send(proc, "isready")
                raw_lines.extend(read_until(box, "readyok", 60))
                send(proc, "position fen " + fen)
                send(proc, "isready")
                raw_lines.extend(read_until(box, "readyok", 60))
                send(proc, "go depth %d" % depth)
                raw_lines.extend(read_until(box, "bestmove", 180))
                finished += 1
            send(proc, "quit")
            proc.wait(timeout=30)
        except Exception as exc:
            note = str(exc)
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    with open(out_prefix + ".txt", "w", encoding="utf-8") as handle:
        handle.writelines(raw_lines)
        handle.write("NOTE %s\n" % note)
        handle.write("finished %d of %d\n" % (finished, len(fens)))
    err_text = open(err_path, encoding="utf-8", errors="replace").read()
    sanitizer_lines = [
        line for line in err_text.splitlines()
        if "AddressSanitizer" in line or "runtime error:" in line or "UndefinedBehaviorSanitizer" in line
    ]
    with open(out_prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write("exe %s\n" % exe)
        handle.write("sha256 %s\n" % sha256_file(exe))
        handle.write("nm -C %s | grep -c __asan_\n" % exe)
        handle.write("%d\n" % symbol_count)
        handle.write("options\n")
        for name, value in S14:
            handle.write("setoption name %s value %s\n" % (name, value))
        handle.write("fens %s\n" % fens_path)
        handle.write("depth %d\n" % depth)
        handle.write("positions %d\n" % len(fens))
        handle.write("finished %d\n" % finished)
        handle.write("note %s\n" % note)
        handle.write("sanitizer_lines %d\n" % len(sanitizer_lines))
        for line in sanitizer_lines:
            handle.write("SAN " + line + "\n")
    print("asan_symbols %d finished %d/%d sanitizer_lines %d" % (symbol_count, finished, len(fens), len(sanitizer_lines)))
    if sanitizer_lines:
        print(sanitizer_lines[0])
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
