#!/usr/bin/env python3
"""uci_drive.py EXE CASEFILE OUTDIR [timeout_s]  --  drives one engine process per case.

Case file format: blocks starting with "### name", then one UCI command per line.
A line "go ..." is sent and then only waited on (no other command goes in until
`bestmove` arrives, or the timeout fires: the case is recorded as a HANG and the
process is killed). "# about-input" marks a case whose answer may legitimately be
an "invalid ..." info string.

Every `setoption` and `position` is followed by `isready`, and every line up to
`readyok` is read before the next command is sent.

Each case writes OUTDIR/<name>.json (record) and OUTDIR/<name>.err (raw stderr).
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class LineReader:
    def __init__(self, stream):
        self.q = queue.Queue()
        self.stream = stream
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        while True:
            try:
                line = self.stream.readline()
            except Exception:
                break
            if not line:
                break
            self.q.put(line)
        self.q.put(None)

    def readline(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return self.q.get(timeout=remaining)
        except queue.Empty:
            return None


def parse_cases(path):
    cases, name, lines, about = [], None, [], False
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("### "):
            if name is not None:
                cases.append((name, lines, about))
            name, lines, about = line[4:].strip().split()[0], [], False
            continue
        if line.strip() == "# about-input":
            about = True
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        lines.append(line.strip())
    if name is not None:
        cases.append((name, lines, about))
    return cases


def run_case(exe, name, lines, about_input, outdir, timeout_s):
    rec = {"case": name, "commands": lines, "violations": [], "sanitizer": [],
           "hang": False, "bestmoves": [], "last_info": None, "exit": None, "seconds": None}
    errpath = os.path.join(outdir, name + ".err")
    errfh = open(errpath, "w", encoding="utf-8")
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=errfh, text=True, bufsize=1)
    started = time.monotonic()
    reader = LineReader(proc.stdout)

    def send(cmd):
        try:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
            return True
        except Exception:
            return False

    def note(line):
        if line.startswith("info string") and any(b in line for b in BAD):
            rec["violations"].append(line.strip())
        if line.startswith("info ") and " pv" in line:
            rec["last_info"] = line.strip()

    def drain(timeout=60):
        deadline = time.monotonic() + timeout
        while True:
            line = reader.readline(deadline)
            if line is None:
                return False
            note(line)
            if line.strip() == "readyok":
                return True

    send("uci")
    deadline = time.monotonic() + 60
    while True:
        line = reader.readline(deadline)
        if line is None or line.strip() == "uciok":
            break
    send("isready")
    drain()

    hanging = False
    pending = list(lines)
    while pending and not hanging:
        cmd = pending.pop(0)
        if cmd.startswith(("setoption", "position", "ucinewgame", "isready")):
            send(cmd)
            if not cmd.startswith("isready"):
                send("isready")
            drain()
            continue
        if not send(cmd):
            break
        if cmd.startswith("go"):
            late = []
            if "infinite" in cmd or "ponder" in cmd:
                while pending and pending[0].startswith(("stop", "ponderhit")):
                    late.append(pending.pop(0))
            best = None
            # An infinite/ponder search cannot answer before its stop line arrives.
            deadline = time.monotonic() + (0.8 if late else timeout_s)
            while True:
                line = reader.readline(deadline)
                if line is None:
                    break
                note(line)
                if line.startswith("bestmove"):
                    best = line.strip()
                    break
            if best is None and late:
                for extra in late:
                    send(extra)
                deadline = time.monotonic() + timeout_s
                while True:
                    line = reader.readline(deadline)
                    if line is None:
                        break
                    note(line)
                    if line.startswith("bestmove"):
                        best = line.strip()
                        break
            if best is None:
                rec["hang"] = True
                hanging = True
                break
            rec["bestmoves"].append(best)
    if not hanging:
        send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait()
        except Exception:
            pass
    rec["exit"] = proc.returncode
    errfh.flush()
    errfh.close()
    with open(errpath, encoding="utf-8") as fh:
        for line in fh:
            if "Sanitizer" in line or "runtime error" in line or "SUMMARY:" in line:
                rec["sanitizer"].append(line.strip())
    try:
        if proc.poll() is None:
            proc.kill()
    except Exception:
        pass
    rec["seconds"] = round(time.monotonic() - started, 3)
    if about_input:
        rec["violations"] = [v for v in rec["violations"] if "invalid FEN" not in v]
    with open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    return rec


def main():
    exe, casefile, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    timeout_s = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for name, lines, about in parse_cases(casefile):
        rec = run_case(exe, name, lines, about, outdir, timeout_s)
        rows.append(rec)
        last = rec["bestmoves"][-1] if rec["bestmoves"] else "-"
        print(f"{name:28s} hang={int(rec['hang'])} san={len(rec['sanitizer'])} "
              f"viol={len(rec['violations'])} bm={last[:20]:20s} {rec['seconds']}s", flush=True)
    with open(os.path.join(outdir, "all.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
