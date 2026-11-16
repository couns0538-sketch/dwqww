#!/usr/bin/env python3
"""seat 24 area 4 job 3: `go infinite` then `stop` after a random 1..200 ms, Threads 8, 1000 times, under TSan.

Written to a file first, then run from there.  Every round:
  position fen F + isready (read every line to readyok)
  go infinite
  sleep rng.uniform(1, 200) ms
  stop
  read lines until a line starts with "bestmove" (timeout 60 s)
Records per round: idx|fen|delay_ms|bestmoves_seen|bestmove|legal?|ms_after_stop|info_depth_last
Counts: rounds, missing bestmove, >1 bestmove, illegal, crashes, hangs, TSan blocks (from the raw log, by analyse).
"""
import argparse
import hashlib
import os
import queue
import random
import re
import subprocess
import threading
import time

import chess

STOP_PAT = re.compile(r"unknown option|invalid value|invalid FEN|illegal move", re.I)
S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}


class Engine:
    def __init__(self, exe, raw_path, env):
        self.raw = open(raw_path, "ab", buffering=0)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.raw.write(line)
            self.q.put(line.decode("utf-8", "replace").rstrip("\r\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def read_until(self, pred, timeout):
        out = []
        deadline = time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError("\n".join(out))
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError("\n".join(out))
            if line is None:
                raise EOFError("\n".join(out))
            out.append(line)
            if pred(line):
                return out

    def drain_for(self, seconds):
        """read whatever arrives within `seconds` (used to catch a late second bestmove)."""
        out = []
        deadline = time.monotonic() + seconds
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                return out
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                return out
            if line is None:
                return out
            out.append(line)

    def ready(self, timeout=120):
        lines = self.read_until(lambda l: l.strip() == "readyok", timeout)
        return lines, [l for l in lines if STOP_PAT.search(l)]

    def close(self, timeout=20):
        try:
            self.send("quit")
            self.p.wait(timeout=timeout)
        except Exception:
            self.p.kill()
        finally:
            self.raw.close()
        return self.p.returncode


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--rounds", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2403)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", default="")
    ap.add_argument("--drain", type=float, default=0.05)
    a = ap.parse_args()

    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    rng = random.Random(a.seed)
    fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]
    boards = {}

    opt_lines = [f"setoption name {k} value {v}" for k, v in S14.items()]
    opt_lines += [f"setoption name Hash value {a.hash}", f"setoption name Threads value {a.threads}"]
    if a.extra:
        opt_lines += [x for x in a.extra.split(";") if x.strip()]

    eng = Engine(a.exe, a.out + ".raw", env)
    meta = open(a.out + ".meta", "w")
    meta.write(f"exe_started\t{os.path.abspath(a.exe)}\n")
    meta.write(f"sha256\t{sha256(a.exe)}\n")
    meta.write("nm_tsan\t" + os.popen("nm -C " + a.exe + " | grep -c __tsan_").read().strip() + "\n")
    meta.write("env\tTSAN_OPTIONS/ASAN_OPTIONS/UBSAN_OPTIONS/LSAN_OPTIONS unset\n")
    meta.write(f"seed\t{a.seed}\nrounds\t{a.rounds}\nthreads\t{a.threads}\nhash\t{a.hash}\n")
    for line in ["uci"] + opt_lines + ["ucinewgame"]:
        meta.write("sent\t" + line + "\n")
    meta.flush()

    def handshake():
        eng.send("uci")
        eng.read_until(lambda l: l.strip() == "uciok", 60)
        for line in opt_lines:
            eng.send(line)
            eng.send("isready")
            _, bad = eng.ready(120)
            if bad:
                return bad
        eng.send("ucinewgame")
        eng.send("isready")
        _, bad = eng.ready(120)
        return bad

    bad = handshake()
    out = open(a.out + ".rounds", "w")
    stats = {"rounds": 0, "bestmove": 0, "missing": 0, "multi": 0, "illegal": 0, "zero": 0,
             "crashes": 0, "hangs": 0, "stop_run": 0}
    if bad:
        out.write("STOP_AT_HANDSHAKE|" + bad[0] + "\n"); out.close(); meta.close(); eng.close()
        print("STOP at handshake"); return

    for i in range(a.rounds):
        fen = fens[i % len(fens)]
        if fen not in boards:
            boards[fen] = chess.Board(fen)
        board = boards[fen]
        delay_ms = rng.uniform(1.0, 200.0)
        try:
            eng.send("position fen " + fen)
            eng.send("isready")
            _, bad = eng.ready(120)
            if bad:
                out.write(f"{i}|STOP|{bad[0]}\n"); stats["stop_run"] += 1; break
            eng.send("go infinite")
            time.sleep(delay_ms / 1000.0)
            t_stop = time.monotonic()
            eng.send("stop")
            lines = eng.read_until(lambda l: l.startswith("bestmove"), 60)
            ms = (time.monotonic() - t_stop) * 1000.0
            bms = [l for l in lines if l.startswith("bestmove")]
            infos = [l for l in lines if l.startswith("info depth")]
            extra = eng.drain_for(a.drain)
            extra_bm = [l for l in extra if l.startswith("bestmove")]
            if extra_bm:
                bms += extra_bm
            stats["rounds"] += 1
            stats["bestmove"] += 1
            if len(bms) > 1:
                stats["multi"] += 1
            bm = bms[0].split()[1]
            if bm == "0000":
                stats["zero"] += 1
                legal = "0000"
            else:
                legal = "legal" if chess.Move.from_uci(bm) in board.legal_moves else "ILLEGAL"
                if legal == "ILLEGAL":
                    stats["illegal"] += 1
            out.write(f"{i}|{fen}|{delay_ms:.0f}|{len(bms)}|{bm}|{legal}|{ms:.1f}|"
                      + (infos[-1] if infos else "") + "\n")
            out.flush()
        except TimeoutError:
            stats["hangs"] += 1
            out.write(f"{i}|HANG|no bestmove in 60s after stop\n"); out.flush()
            print("HANG at round", i)
            eng.p.kill(); eng.p.wait(); eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                out.write("STOP_AFTER_RESTART|" + bad[0] + "\n"); stats["stop_run"] += 1; break
        except (EOFError, BrokenPipeError):
            stats["crashes"] += 1
            rc = eng.p.poll()
            out.write(f"{i}|CRASH|rc={rc}\n"); out.flush()
            print("CRASH rc=", rc, "round", i)
            eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                out.write("STOP_AFTER_RESTART|" + bad[0] + "\n"); stats["stop_run"] += 1; break

    rc = eng.close()
    out.write(f"# engine_exit\t{rc}\n")
    out.close()
    with open(a.out + ".summary", "w") as f:
        for k, v in stats.items():
            f.write(f"{k}\t{v}\n")
        f.write(f"engine_exit_code\t{rc}\n")
    meta.write(f"engine_exit_code\t{rc}\n")
    meta.close()
    print(open(a.out + ".summary").read())


if __name__ == "__main__":
    main()
