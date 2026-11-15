#!/usr/bin/env python3
"""Job 10 part C: broken table input under ASan+UBSan.

Each case: make a COPY of the table folder, damage exactly one file, point
SyzygyPath at the copy, run `bench 13` and then 20 `go nodes 20000` searches from
positions the damaged table is needed for, and record:
  exit code, sanitizer lines on stderr, whether the table was refused or used
  (the engine's own load line), and whether every bestmove was legal.

A crash, a hang, or any sanitizer line is a FINDING and is reported with the case.
"""

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time

import chess

ENGINE = sys.argv[1]
SRC = sys.argv[2]
FENS = sys.argv[3]
OUT = sys.argv[4]
TARGET = sys.argv[5] if len(sys.argv) > 5 else "KQvK.rtbw"


def run_case(name, folder, fens, wait=40):
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1"
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    outq = queue.Queue()
    errq = queue.Queue()
    threading.Thread(target=lambda: [outq.put(l.rstrip()) for l in p.stdout] + [outq.put(None)],
                     daemon=True).start()
    threading.Thread(target=lambda: [errq.put(l.rstrip()) for l in p.stderr] + [errq.put(None)],
                     daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def until(tok, lim):
        t0 = time.time()
        got = []
        while time.time() - t0 < lim:
            try:
                ln = outq.get(timeout=max(0.01, lim - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if ln.startswith(tok):
                return got, True
        return got, False

    rec = {"case": name, "folder": folder, "legal": True, "sanitizer": [],
           "load_line": None, "exit": None, "hang": False, "bestmoves": 0}
    try:
        send("uci")
        until("uciok", 15)
        send(f"setoption name SyzygyPath value {folder}")
        send("setoption name Threads value 1")
        send("setoption name Hash value 16")
        send("setoption name OwnBook value false")
        send("isready")
        got, _ = until("readyok", 60)
        for ln in got:
            if "Syzygy:" in ln:
                rec["load_line"] = ln.strip()
        alive = p.poll() is None
        if not alive:
            rec["exit"] = p.returncode
            rec["hang"] = False
        else:
            send("bench 13")
            got, ok = until("bench depth", 120)
            for ln in got:
                if "Syzygy:" in ln and not rec["load_line"]:
                    rec["load_line"] = ln.strip()
            if p.poll() is not None:
                rec["exit"] = p.returncode
            else:
                for fen in fens:
                    send("position fen " + fen)
                    send("go nodes 20000")
                    got, ok = until("bestmove", wait)
                    if not ok:
                        rec["hang"] = True
                        rec["bestmoves"] = rec.get("bestmoves", 0)
                        break
                    best = None
                    for ln in got:
                        if ln.startswith("bestmove"):
                            best = ln.split()[1]
                    rec["bestmoves"] += 1
                    if best and best != "0000":
                        b = chess.Board(fen)
                        try:
                            if chess.Move.from_uci(best) not in b.legal_moves:
                                rec["legal"] = False
                        except Exception:
                            rec["legal"] = False
                send("quit")
        # collect stderr
        errs = []
        while True:
            try:
                ln = errq.get(timeout=2.0)
            except queue.Empty:
                break
            if ln is None:
                break
            errs.append(ln)
        rec["sanitizer"] = [l for l in errs if "runtime error" in l or "AddressSanitizer" in l
                            or "LeakSanitizer" in l or "SEGV" in l]
        if p.poll() is None:
            p.kill()
        try:
            rec["exit"] = rec["exit"] if rec["exit"] is not None else p.wait(timeout=5)
        except Exception:
            p.kill()
            rec["exit"] = "killed"
    except Exception as exc:
        rec["error"] = str(exc)
        try:
            p.kill()
        except Exception:
            pass
    return rec


def fresh_copy(tag):
    d = f"/tmp/ds2/tbcases/{tag}"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(SRC, d)
    return d


def main():
    os.makedirs("/tmp/ds2/tbcases", exist_ok=True)
    fens = [l.strip() for l in open(FENS) if l.strip()][:20]
    rows = []
    # control: the unbroken folder must load and be used
    rows.append(run_case("C0 unbroken folder", SRC, fens))
    print(rows[-1]["case"], rows[-1]["load_line"], "exit", rows[-1]["exit"], flush=True)

    target_path = os.path.join(SRC, TARGET)
    orig = open(target_path, "rb").read() if os.path.exists(target_path) else b""

    # C1: 0 bytes, 100 bytes, half
    for tag, size in (("zero", 0), ("hundred", 100), ("half", max(1, len(orig) // 2))):
        d = fresh_copy("c1_" + tag)
        with open(os.path.join(d, TARGET), "wb") as f:
            f.write(orig[:size])
        rows.append(run_case(f"C1 {TARGET} cut to {size} bytes", d, fens))
        print(rows[-1]["case"], rows[-1]["load_line"], "exit", rows[-1]["exit"],
              "san", len(rows[-1]["sanitizer"]), flush=True)

    # C2: one byte flipped at 20 offsets in the first 4096
    for off in range(0, 4000, 200):
        d = fresh_copy(f"c2_{off}")
        b = bytearray(orig)
        if off < len(b):
            b[off] ^= 0xFF
        with open(os.path.join(d, TARGET), "wb") as f:
            f.write(bytes(b))
        rows.append(run_case(f"C2 flip byte at offset {off}", d, fens))
        print(rows[-1]["case"], "exit", rows[-1]["exit"], "san", len(rows[-1]["sanitizer"]), flush=True)

    # C3: another table under this name
    others = [f for f in os.listdir(SRC) if f.endswith(".rtbw") and f != TARGET]
    if others:
        d = fresh_copy("c3_swap")
        shutil.copy(os.path.join(SRC, others[0]), os.path.join(d, TARGET))
        rows.append(run_case(f"C3 {others[0]} copied over {TARGET}", d, fens))
        print(rows[-1]["case"], rows[-1]["load_line"], "exit", rows[-1]["exit"], flush=True)

    # C4: path oddities
    for tag, path in (("missing", "/tmp/ds2/tbcases/does_not_exist"),
                      ("file", "/tmp/ds2/tbcases/afile"),
                      ("empty", "/tmp/ds2/tbcases/empty_folder"),
                      ("long", "/tmp/ds2/tbcases/" + "a" * 5000)):
        if tag == "file":
            open("/tmp/ds2/tbcases/afile", "w").write("x")
        if tag == "empty":
            os.makedirs("/tmp/ds2/tbcases/empty_folder", exist_ok=True)
        rows.append(run_case("C4 path " + tag, path, fens))
        print(rows[-1]["case"], rows[-1]["load_line"], "exit", rows[-1]["exit"], flush=True)

    json.dump(rows, open(OUT, "w"), indent=1)
    bad = [r for r in rows if r["sanitizer"] or r["hang"] or r["error"] or r["exit"] not in (0, "0", None)]
    illegal = [r for r in rows if not r["legal"]]
    print(f"\ncases {len(rows)}, with sanitizer lines / hang / error / nonzero exit: {len(bad)}")
    print(f"cases with an illegal bestmove: {len(illegal)}")
    for r in bad:
        print("  BAD:", r["case"], "exit", r["exit"], "hang", r["hang"],
              "san", r["sanitizer"][:1], r.get("error"))


if __name__ == "__main__":
    main()
