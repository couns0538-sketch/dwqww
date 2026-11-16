#!/usr/bin/env python3
"""deepseek5 job6: storm harness that SEES sanitizer reports.
argv: <exe> <tag> <blocks>   blocks: comma list of T1,T2,T3,T4sw,T5
Outputs (folder from DS5OUT or .): <tag>_<block>.json, <tag>_<block>.stderr.txt,
<tag>_<block>.tsan.<pid> / .asan.<pid> / .ubsan.<pid> (sanitizer logs), cmd_<tag>.txt."""
import chess
import json
import os
import queue
import random
import statistics
import subprocess
import sys
import threading
import time

ENGINE = None  # set from argv
FOLDER = os.environ.get("DS5OUT", ".")
EPD = "/tmp/glmflash/UHO_Lichess_4852_v1.epd"

class Eng:
    def __init__(self, threads=1, tag="x", block="x"):
        env = dict(os.environ)
        env["TSAN_OPTIONS"] = f"log_path={FOLDER}/{tag}_{block}.tsan exitcode=66 halt_on_error=0 second_deadlock_stack=1"
        env["ASAN_OPTIONS"] = f"log_path={FOLDER}/{tag}_{block}.asan:exitcode=67 halt_on_error=0 detect_leaks=1"
        env["UBSAN_OPTIONS"] = f"print_stacktrace=1:halt_on_error=0:log_path={FOLDER}/{tag}_{block}.ubsan"
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        self.stderr_bytes = 0
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        self.expect("uciok", 120)
        self.set("Threads", threads)
        self.set("Hash", 16)
        self.set("OwnBook", "false")
        self.send("isready")
        self.expect("readyok", 120)

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def set(self, name, value):
        self.send(f"setoption name {name} value {value}")

    def expect(self, prefix, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            try:
                line = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(prefix):
                return line
        raise queue.Empty

    def drain(self, seconds):
        got = []
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            try:
                line = self.q.get(timeout=0.05)
                if line is None:
                    break
                got.append(line)
            except queue.Empty:
                continue
        return got

def finish(e, tag, block):
    try:
        e.send("quit")
    except (BrokenPipeError, OSError):
        pass
    try:
        e.p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        e.p.kill()
        e.p.wait(timeout=10)
    err = e.p.stderr.read() if e.p.stderr else ""
    with open(f"{FOLDER}/{tag}_{block}.stderr.txt", "w") as f:
        f.write(err)
    return len(err.encode())

def warnings_in(tag, block):
    n = 0
    first = None
    pats = ("WARNING: ThreadSanitizer", "ERROR: AddressSanitizer", "runtime error:",
            "ERROR: LeakSanitizer")
    cands = [f"{FOLDER}/{tag}_{block}.stderr.txt"]
    for fn in os.listdir(FOLDER):
        if fn.startswith(f"{tag}_{block}.tsan") or fn.startswith(f"{tag}_{block}.asan") or fn.startswith(f"{tag}_{block}.ubsan"):
            cands.append(f"{FOLDER}/{fn}")
    for fn in cands:
        try:
            for line in open(fn, encoding="utf-8", errors="replace"):
                if any(p in line for p in pats):
                    if first is None:
                        first = line.strip()[:200]
                    n += 1
        except FileNotFoundError:
            pass
    report_files = sum(1 for fn in os.listdir(FOLDER)
                       if (fn.startswith(f"{tag}_{block}.tsan") or fn.startswith(f"{tag}_{block}.asan")
                           or fn.startswith(f"{tag}_{block}.ubsan")))
    return n, first, report_files

def one_storm(e, fen, rng, wait_lo, wait_hi, go_line, use_stop=True):
    e.send("ucinewgame")
    e.send("isready")
    e.expect("readyok", 120)
    e.send(f"position fen {fen}")
    e.send(go_line)
    if use_stop:
        time.sleep(rng.uniform(wait_lo, wait_hi) / 1000.0)
        e.send("stop")
    t0 = time.monotonic_ns()
    line = e.expect("bestmove", 300)
    lat = (time.monotonic_ns() - t0) / 1e6
    best = line.split()[1]
    extra = e.drain(0.5)
    doubles = sum(1 for x in extra if x.startswith("bestmove"))
    board = chess.Board(); board.set_fen(fen)
    legal = True
    try:
        if chess.Move.from_uci(best) not in board.legal_moves:
            legal = False
    except Exception:
        legal = False
    return lat, legal, doubles

def block(tag, name, storms, seed, threads_init=4, wait_lo=1, wait_hi=300,
          go_line="go infinite", use_stop=True, prep=None):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=threads_init, tag=tag, block=name)
    if prep:
        prep(e)
    lat = []; missing = 0; doubles = 0; illegal = 0
    for i in range(storms):
        fen = fens[rng.randrange(len(fens))]
        try:
            l, legal, d = one_storm(e, fen, rng, wait_lo, wait_hi, go_line, use_stop)
            lat.append(l); doubles += d
            if not legal:
                illegal += 1
        except queue.Empty:
            missing += 1
        except (BrokenPipeError, RuntimeError):
            missing += 1
            break
    stderr_bytes = finish(e, tag, name)
    exit_code = e.p.returncode
    n, first, report_files = warnings_in(tag, name)
    vals = sorted(lat)
    exit_code = None
    res = {"tag": tag, "block": name, "storms": storms, "missing": missing,
           "doubles": doubles, "illegal": illegal,
           "median_ms": statistics.median(vals) if vals else None,
           "max_ms": vals[-1] if vals else None,
           "exit_code": exit_code, "report_files": report_files,
           "warnings": n, "first_report": first, "stderr_bytes": stderr_bytes}
    json.dump(res, open(f"{FOLDER}/{tag}_{name}.json", "w"), indent=1)
    print(json.dumps(res), flush=True)
    return res

def block_t5(tag, seed=7355):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=4)
    late_lat = []; late_missing = 0; late_second = 0; late_no_readyok = 0
    early_lat = []; early_missing = 0; early_doubles = 0; early_illegal = 0
    for i in range(100):
        fen = fens[rng.randrange(len(fens))]
        e.send("ucinewgame"); e.send("isready"); e.expect("readyok", 120)
        e.send(f"position fen {fen}")
        e.send("go depth 2")
        try:
            t0 = time.monotonic_ns()
            e.expect("bestmove", 300)
            late_lat.append((time.monotonic_ns() - t0) / 1e6)
            e.send("stop")
            late_second += sum(1 for x in e.drain(0.5) if x.startswith("bestmove"))
            e.send("isready")
            try:
                e.expect("readyok", 120)
            except queue.Empty:
                late_no_readyok += 1
            late_second += sum(1 for x in e.drain(0.5) if x.startswith("bestmove"))
        except queue.Empty:
            late_missing += 1
    for i in range(100):
        fen = fens[rng.randrange(len(fens))]
        e.send("ucinewgame"); e.send("isready"); e.expect("readyok", 120)
        e.send(f"position fen {fen}")
        e.send("go infinite")
        time.sleep(rng.uniform(0, 2) / 1000.0)
        e.send("stop")
        try:
            t0 = time.monotonic_ns()
            line = e.expect("bestmove", 300)
            early_lat.append((time.monotonic_ns() - t0) / 1e6)
            best = line.split()[1]
            board = chess.Board(); board.set_fen(fen)
            try:
                if chess.Move.from_uci(best) not in board.legal_moves:
                    early_illegal += 1
            except Exception:
                early_illegal += 1
            early_doubles += sum(1 for x in e.drain(0.5) if x.startswith("bestmove"))
        except queue.Empty:
            early_missing += 1
    stderr_bytes = finish(e, tag, "T5")
    n, first, report_files = warnings_in(tag, "T5")
    v = sorted(late_lat); w = sorted(early_lat)
    res = {"tag": tag, "block": "T5", "late_n": len(v), "late_missing": late_missing,
           "late_second_bestmove": late_second, "late_no_readyok": late_no_readyok,
           "late_max_ms": v[-1] if v else None,
           "early_n": len(w), "early_missing": early_missing, "early_doubles": early_doubles,
           "early_illegal": early_illegal, "early_max_ms": w[-1] if w else None,
           "exit_code": e.p.returncode, "report_files": report_files,
           "warnings": n, "first_report": first, "stderr_bytes": stderr_bytes}
    json.dump(res, open(f"{FOLDER}/{tag}_T5.json", "w"), indent=1)
    print(json.dumps(res), flush=True)
    return res

def main():
    global ENGINE
    ENGINE = sys.argv[1]
    tag = sys.argv[2]
    blocks = sys.argv[3].split(",") if len(sys.argv) > 3 else ["T1", "T2", "T3", "T4sw", "T5"]
    with open(f"{FOLDER}/cmd_{tag}.txt", "w") as f:
        f.write("engine: " + ENGINE + "\nblocks: " + ",".join(blocks) + "\n")
    if "T1" in blocks:
        block(tag, "T1", 200, 7351, threads_init=4)
    if "T2" in blocks:
        block(tag, "T2", 100, 7352, threads_init=4, prep=lambda e: e.set("MultiPV", 2))
    if "T3" in blocks:
        block(tag, "T3", 100, 7353, threads_init=4,
              go_line="go wtime 1 btime 1 winc 0 binc 0", use_stop=False)
    if "T4sw" in blocks:
        fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
        rng = random.Random(7354)
        e = Eng(threads=1, tag=tag, block="T4sw")
        lat = []; missing = 0; doubles = 0; illegal = 0; n = 0
        def do5():
            nonlocal n, missing, doubles, illegal
            for _ in range(5):
                fen = fens[rng.randrange(len(fens))]
                try:
                    l, legal, d = one_storm(e, fen, rng, 1, 300, "go infinite")
                    lat.append(l); doubles += d; n += 1
                    if not legal:
                        illegal += 1
                except queue.Empty:
                    missing += 1
                except (BrokenPipeError, RuntimeError):
                    missing += 1
                    return
        for r in range(20):
            e.set("Threads", 4); do5()
            e.set("Threads", 1); do5()
            e.set("MultiPV", 2); do5()
            e.set("MultiPV", 1)
            for h in (1, 16, 64):
                e.set("Hash", h); do5()
            e.send("ucinewgame")
            for j in (0, 5):
                e.set("DrawJitter", j); do5()
        stderr_bytes = finish(e, tag, "T4sw")
        n_rep, first, report_files = warnings_in(tag, "T4sw")
        vals = sorted(lat)
        res = {"tag": tag, "block": "T4sw", "storms": n, "missing": missing,
               "doubles": doubles, "illegal": illegal,
               "median_ms": statistics.median(vals) if vals else None,
               "max_ms": vals[-1] if vals else None,
               "exit_code": e.p.returncode, "report_files": report_files,
               "warnings": n_rep, "first_report": first, "stderr_bytes": stderr_bytes}
        json.dump(res, open(f"{FOLDER}/{tag}_T4sw.json", "w"), indent=1)
        print(json.dumps(res), flush=True)
    if "T5" in blocks:
        block_t5(tag)

if __name__ == "__main__":
    main()
