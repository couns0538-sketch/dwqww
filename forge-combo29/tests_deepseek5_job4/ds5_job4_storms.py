#!/usr/bin/env python3
"""deepseek5 job4 step 3: the five storm blocks under the TSan exe (one process per block)."""
import chess
import json
import queue
import random
import statistics
import subprocess
import sys
import threading
import time

ENGINE = "/tmp/ds5_tsan/build/forge"
EPD = "/tmp/glmflash/UHO_Lichess_4852_v1.epd"

class Eng:
    def __init__(self, threads=1):
        self.p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        self.expect("uciok", 60)
        self.set("Threads", threads)
        self.set("Hash", 16)
        self.set("OwnBook", "false")
        self.send("isready")
        self.expect("readyok", 60)

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
        line = self.q.get(timeout=timeout)
        if line is None:
            raise RuntimeError("engine died")
        if line.startswith(prefix):
            return line
        return self.expect(prefix, max(0.0, timeout - 0.01))

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

def one_storm(e, fen, rng, wait_lo, wait_hi, go_line, use_stop=True, post=None):
    e.send("ucinewgame")
    e.send("isready")
    e.expect("readyok", 60)
    e.send(f"position fen {fen}")
    e.send(go_line)
    if use_stop:
        time.sleep(rng.uniform(wait_lo, wait_hi) / 1000.0)
        e.send("stop")
    t0 = time.monotonic_ns()
    line = e.expect("bestmove", 120)
    lat = (time.monotonic_ns() - t0) / 1e6
    best = line.split()[1]
    extra = e.drain(0.15)
    doubles = sum(1 for x in extra if x.startswith("bestmove"))
    board = chess.Board(); board.set_fen(fen)
    legal = True
    try:
        if chess.Move.from_uci(best) not in board.legal_moves:
            legal = False
    except Exception:
        legal = False
    readyoks = 0
    if post == "isready":
        e.send("isready")
        l = e.expect("readyok", 60)
        readyoks = 1
        extra2 = e.drain(0.15)
        doubles += sum(1 for x in extra2 if x.startswith("bestmove"))
    return lat, best, legal, doubles, readyoks

def block(tag, storms, seed, threads_init=4, wait_lo=1, wait_hi=300, go_line="go infinite", use_stop=True):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=threads_init)
    lat = []; missing = 0; doubles = 0; illegal = 0
    for i in range(storms):
        fen = fens[rng.randrange(len(fens))]
        try:
            l, best, legal, d, _ = one_storm(e, fen, rng, wait_lo, wait_hi, go_line)
            lat.append(l); doubles += d
            if not legal:
                illegal += 1
        except queue.Empty:
            missing += 1
    e.send("quit")
    vals = sorted(lat)
    res = {"tag": tag, "n": storms, "missing": missing, "doubles": doubles, "illegal": illegal,
           "median_ms": statistics.median(vals) if vals else None,
           "p95_ms": vals[int(0.95 * (len(vals) - 1))] if vals else None,
           "max_ms": vals[-1] if vals else None}
    print(json.dumps(res), flush=True)
    return res

def block_t4_switches(rounds=20, seed=7354):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=1)
    lat = []; missing = 0; doubles = 0; illegal = 0; n = 0
    def do5():
        nonlocal n, missing, doubles, illegal
        for _ in range(5):
            fen = fens[rng.randrange(len(fens))]
            try:
                l, best, legal, d, _ = one_storm(e, fen, rng, 1, 300, "go infinite")
                lat.append(l); doubles += d; n += 1
                if not legal:
                    illegal += 1
            except queue.Empty:
                missing += 1
    for r in range(rounds):
        e.set("Threads", 4); do5()
        e.set("Threads", 1); do5()
        e.set("MultiPV", 2); do5()
        e.set("MultiPV", 1)
        for h in (1, 16, 64):
            e.set("Hash", h); do5()
        e.send("ucinewgame")
        for j in (0, 5):
            e.set("DrawJitter", j); do5()
    e.send("quit")
    vals = sorted(lat)
    res = {"tag": "T4 switches", "n": n, "missing": missing, "doubles": doubles, "illegal": illegal,
           "median_ms": statistics.median(vals) if vals else None,
           "p95_ms": vals[int(0.95 * (len(vals) - 1))] if vals else None,
           "max_ms": vals[-1] if vals else None}
    print(json.dumps(res), flush=True)
    return res

def block_t5(seed=7355):
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(seed)
    e = Eng(threads=4)
    late_missing = 0; late_doubles = 0; late_readyok_missing = 0; late_second_best = 0; late_lat = []
    for i in range(100):
        fen = fens[rng.randrange(len(fens))]
        e.send("ucinewgame"); e.send("isready"); e.expect("readyok", 60)
        e.send(f"position fen {fen}")
        e.send("go depth 2")
        try:
            t0 = time.monotonic_ns()
            line = e.expect("bestmove", 120)
            late_lat.append((time.monotonic_ns() - t0) / 1e6)
            e.send("stop")
            extra = e.drain(0.3)
            late_second_best += sum(1 for x in extra if x.startswith("bestmove"))
            e.send("isready")
            try:
                e.expect("readyok", 60)
            except queue.Empty:
                late_readyok_missing += 1
            more = e.drain(0.2)
            late_second_best += sum(1 for x in more if x.startswith("bestmove"))
        except queue.Empty:
            late_missing += 1
    early_lat = []; early_missing = 0; early_doubles = 0; early_illegal = 0
    for i in range(100):
        fen = fens[rng.randrange(len(fens))]
        e.send("ucinewgame"); e.send("isready"); e.expect("readyok", 60)
        e.send(f"position fen {fen}")
        e.send("go infinite")
        time.sleep(rng.uniform(0, 2) / 1000.0)
        e.send("stop")
        try:
            t0 = time.monotonic_ns()
            line = e.expect("bestmove", 120)
            early_lat.append((time.monotonic_ns() - t0) / 1e6)
            best = line.split()[1]
            board = chess.Board(); board.set_fen(fen)
            try:
                if chess.Move.from_uci(best) not in board.legal_moves:
                    early_illegal += 1
            except Exception:
                early_illegal += 1
            extra = e.drain(0.15)
            early_doubles += sum(1 for x in extra if x.startswith("bestmove"))
        except queue.Empty:
            early_missing += 1
    e.send("quit")
    v = sorted(late_lat)
    w = sorted(early_lat)
    res = {"tag": "T5 late/early", "late_n": len(v), "late_missing": late_missing,
           "late_second_bestmove": late_second_best, "late_readyok_missing": late_readyok_missing,
           "late_max_ms": v[-1] if v else None,
           "early_n": len(w), "early_missing": early_missing, "early_doubles": early_doubles,
           "early_illegal": early_illegal, "early_max_ms": w[-1] if w else None}
    print(json.dumps(res), flush=True)
    return res

def main():
    out = {}
    out["T1"] = block("T1 MPV1 T4", 200, 7351, threads_init=4)
    out["T2"] = block("T2 MPV2 T4", 100, 7352, threads_init=4)
    e2 = None
    out["T2"].setdefault("note", "")
    # T2 needs MultiPV 2 set once: rerun with a prepended setoption is not possible in block(); do a dedicated block
    out.pop("T2")
    e = Eng(threads=4)
    e.set("MultiPV", 2)
    fens = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")]
    rng = random.Random(7352)
    lat = []; missing = 0; doubles = 0; illegal = 0
    for i in range(100):
        fen = fens[rng.randrange(len(fens))]
        try:
            l, best, legal, d, _ = one_storm(e, fen, rng, 1, 300, "go infinite")
            lat.append(l); doubles += d
            if not legal:
                illegal += 1
        except queue.Empty:
            missing += 1
    e.send("quit")
    vals = sorted(lat)
    out["T2"] = {"tag": "T2 MPV2 T4", "n": 100, "missing": missing, "doubles": doubles,
                 "illegal": illegal, "median_ms": statistics.median(vals) if vals else None,
                 "p95_ms": vals[int(0.95 * (len(vals) - 1))] if vals else None,
                 "max_ms": vals[-1] if vals else None}
    print(json.dumps(out["T2"]), flush=True)
    out["T3"] = block("T3 wtime1 T4", 100, 7353, threads_init=4, go_line="go wtime 1 btime 1 winc 0 binc 0", use_stop=False)
    out["T4sw"] = block_t4_switches()
    out["T5"] = block_t5()
    json.dump(out, open("/tmp/glmflash/ds5_job4_storms.json", "w"), indent=1)

if __name__ == "__main__":
    main()
