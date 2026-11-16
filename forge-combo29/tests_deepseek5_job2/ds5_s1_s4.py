#!/usr/bin/env python3
"""deepseek5 job2 (version B): S1 stop storm + S4 ponder, with planted faults."""
import chess
import json
import queue
import random
import statistics
import subprocess
import sys
import threading
import time

ENGINE = "/tmp/ds13_base/build/forge"
EPD = "/tmp/glmflash/UHO_Lichess_4852_v1.epd"

class Eng:
    def __init__(self, threads=1, wrapper=None):
        cmd = [wrapper, ENGINE] if wrapper else [ENGINE]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        self.expect("uciok", 10)
        self.send(f"setoption name Threads value {threads}")
        self.send("setoption name Hash value 16")
        self.send("setoption name OwnBook value false")
        self.send("setoption name Ponder value true")
        self.send("isready")
        self.expect("readyok", 10)

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def expect(self, prefix, timeout):
        while True:
            line = self.q.get(timeout=timeout)
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(prefix):
                return line

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
                break
        return got

def storm(threads, n, wait_lo, wait_hi, seed, go_line, wrapper=None, tag=""):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=threads, wrapper=wrapper)
    lat = []
    missing = 0
    doubles = 0
    illegal = 0
    for i in range(n):
        fen = fens[rng.randrange(len(fens))]
        e.send("ucinewgame")
        e.send("isready")
        e.expect("readyok", 10)
        e.send(f"position fen {fen}")
        e.send(go_line)
        time.sleep(rng.uniform(wait_lo, wait_hi) / 1000.0)
        e.send("stop")
        t0 = time.monotonic_ns()
        try:
            line = e.expect("bestmove", 5)
            lat.append((time.monotonic_ns() - t0) / 1e6)
            best = line.split()[1]
            board = chess.Board(); board.set_fen(fen)
            try:
                if chess.Move.from_uci(best) not in board.legal_moves:
                    illegal += 1
            except Exception:
                illegal += 1
            extra = e.drain(0.15)
            doubles += sum(1 for x in extra if x.startswith("bestmove"))
        except queue.Empty:
            missing += 1
    e.send("quit")
    vals = sorted(lat)
    res = {"tag": tag, "threads": threads, "n": n, "missing": missing, "doubles": doubles,
           "illegal": illegal, "median_ms": statistics.median(vals) if vals else None,
           "p95_ms": vals[int(0.95 * (len(vals) - 1))] if vals else None,
           "max_ms": vals[-1] if vals else None}
    print(json.dumps(res), flush=True)
    return res

def ponder(n, seed, wrapper=None):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=1, wrapper=wrapper)
    no_best_during_ponder = 0
    answers = 0
    missing = 0
    doubles = 0
    illegal = 0
    lat = []
    for i in range(n):
        fen = fens[i % len(fens)]
        e.send("ucinewgame")
        e.send("isready")
        e.expect("readyok", 10)
        e.send(f"position fen {fen}")
        e.send("go ponder wtime 60000 btime 60000")
        early = e.drain(0.2)
        # after 200 ms no bestmove may have come; drain must also not contain one
        if any(x.startswith("bestmove") for x in early):
            no_best_during_ponder += 1
        # ensure nothing more arrives right at the 200 ms boundary
        if i % 2 == 0:
            e.send("ponderhit")
        else:
            e.send("stop")
        t0 = time.monotonic_ns()
        try:
            line = e.expect("bestmove", 10)
            lat.append((time.monotonic_ns() - t0) / 1e6)
            answers += 1
            best = line.split()[1]
            board = chess.Board(); board.set_fen(fen)
            try:
                if chess.Move.from_uci(best) not in board.legal_moves:
                    illegal += 1
            except Exception:
                illegal += 1
            extra = e.drain(0.15)
            doubles += sum(1 for x in extra if x.startswith("bestmove"))
        except queue.Empty:
            missing += 1
    e.send("quit")
    vals = sorted(lat)
    res = {"tag": "ponder", "n": n, "bestmove_during_ponder": no_best_during_ponder,
           "answers": answers, "missing": missing, "doubles": doubles, "illegal": illegal,
           "median_ms": statistics.median(vals) if vals else None,
           "p95_ms": vals[int(0.95 * (len(vals) - 1))] if vals else None,
           "max_ms": vals[-1] if vals else None}
    print(json.dumps(res), flush=True)
    return res

def main():
    out = {}
    out["s1_t1"] = storm(1, 1000, 1, 300, 7250, "go infinite", tag="S1 infinite T1")
    out["s1_t4"] = storm(4, 500, 1, 300, 7251, "go infinite", tag="S1 infinite T4")
    out["s1_wtime"] = storm(1, 300, 1, 30, 7252, "go wtime 1000 btime 1000", tag="S1 wtime1000")
    out["s4"] = ponder(300, 7253)
    json.dump(out, open("/tmp/glmflash/ds5_s1_s4.json", "w"), indent=1)

if __name__ == "__main__":
    main()
