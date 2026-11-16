#!/usr/bin/env python3
"""seat 24 area 4 job 2: change Threads and Hash between searches 300 times, under ThreadSanitizer.

Random choices use SEED = 2402 (SEED+1 for this job, per the brief).  Written to a file first, then run.

Every step: pick Threads in {1,2,4,8,16} and Hash in {1,4,16,64,256}, send both setoptions (each followed by
`isready`, every line read up to readyok), then a short search (depth 1..6) on a position from set_G.epd, and
sometimes `ucinewgame` before the search.  Stop the run on `unknown option` / `invalid value` / `invalid FEN` /
`illegal move`.  Writes:
  <out>.meta      exe, sha256, nm __tsan_, every option line sent (deduplicated), env note, seed
  <out>.raw       every byte both streams produced
  <out>.steps     one line per step: idx|threads|hash|ucinewgame|depth|fen|bestmove|legal?|ms|answer-line
  <out>.summary   counters
"""
import argparse
import hashlib
import os
import queue
import random
import re
import subprocess
import sys
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
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--seed", type=int, default=2402)
    ap.add_argument("--depthmax", type=int, default=6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    rng = random.Random(a.seed)
    fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]

    eng = Engine(a.exe, a.out + ".raw", env)
    meta = open(a.out + ".meta", "w")
    meta.write(f"exe_started\t{os.path.abspath(a.exe)}\n")
    meta.write(f"sha256\t{sha256(a.exe)}\n")
    meta.write("nm_tsan\t" + os.popen("nm -C " + a.exe + " | grep -c __tsan_").read().strip() + "\n")
    meta.write("env\tTSAN_OPTIONS/ASAN_OPTIONS/UBSAN_OPTIONS/LSAN_OPTIONS unset\n")
    meta.write(f"seed\t{a.seed}\nsteps\t{a.steps}\n")
    meta.write("sent\tuci\n")
    for k, v in S14.items():
        meta.write(f"sent\tsetoption name {k} value {v}\n")
    meta.flush()

    stats = {"steps": 0, "bestmoves": 0, "illegal": 0, "crashes": 0, "timeouts": 0,
             "stop_run": 0, "ucinewgame": 0, "answer_lines": 0}

    def handshake():
        eng.send("uci")
        eng.read_until(lambda l: l.strip() == "uciok", 60)
        for k, v in S14.items():
            eng.send(f"setoption name {k} value {v}")
            eng.send("isready")
            _, bad = eng.ready(120)
            if bad:
                return bad
        return []

    bad = handshake()
    steps = open(a.out + ".steps", "w")
    if bad:
        steps.write("STOP_AT_HANDSHAKE|" + " / ".join(bad) + "\n"); stats["stop_run"] += 1
        steps.close(); meta.close(); eng.close()
        print("STOP at handshake")
        return

    th_choices = [1, 2, 4, 8, 16]
    hash_choices = [1, 4, 16, 64, 256]
    for i in range(a.steps):
        th = rng.choice(th_choices)
        hs = rng.choice(hash_choices)
        newgame = rng.random() < 0.4
        depth = rng.randint(1, a.depthmax)
        fen = rng.choice(fens)
        try:
            eng.send(f"setoption name Threads value {th}")
            eng.send("isready")
            _, bad1 = eng.ready(120)
            eng.send(f"setoption name Hash value {hs}")
            eng.send("isready")
            _, bad2 = eng.ready(120)
            bad = bad1 + bad2
            if bad:
                steps.write(f"{i}|STOP|{bad[0]}\n"); stats["stop_run"] += 1
                print("STOP:", bad); break
            if newgame:
                eng.send("ucinewgame")
                eng.send("isready")
                _, bad3 = eng.ready(120)
                if bad3:
                    steps.write(f"{i}|STOP|{bad3[0]}\n"); stats["stop_run"] += 1
                    print("STOP:", bad3); break
                stats["ucinewgame"] += 1
            eng.send("position fen " + fen)
            eng.send("isready")
            pre, bad4 = eng.ready(120)
            if bad4:
                steps.write(f"{i}|STOP|{bad4[0]}\n"); stats["stop_run"] += 1
                print("STOP:", bad4); break
            t0 = time.monotonic()
            eng.send(f"go depth {depth}")
            lines = eng.read_until(lambda l: l.startswith("bestmove"), 300)
            ms = (time.monotonic() - t0) * 1000.0
            bm = lines[-1].split()[1]
            infos = [l for l in lines if l.startswith("info depth")]
            stats["answer_lines"] += len(infos)
            stats["bestmoves"] += 1
            board = chess.Board(fen)
            if bm == "0000":
                legal = "nolegal-ok" if not any(board.legal_moves) else "ILLEGAL-0000"
            else:
                try:
                    legal = "legal" if chess.Move.from_uci(bm) in board.legal_moves else "ILLEGAL"
                except Exception:
                    legal = "ILLEGAL-parse"
            if legal.startswith("ILLEGAL"):
                stats["illegal"] += 1
            steps.write(f"{i}|{th}|{hs}|{int(newgame)}|{depth}|{fen}|{bm}|{legal}|{ms:.0f}|"
                        + (infos[-1] if infos else "") + "\n")
            steps.flush()
            stats["steps"] += 1
        except TimeoutError:
            stats["timeouts"] += 1
            steps.write(f"{i}|TIMEOUT\n"); steps.flush()
            eng.p.kill(); rc = eng.p.wait()
            eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                steps.write("STOP_AFTER_RESTART|" + bad[0] + "\n"); stats["stop_run"] += 1
                break
        except (EOFError, BrokenPipeError):
            stats["crashes"] += 1
            rc = eng.p.poll()
            steps.write(f"{i}|CRASH|rc={rc}\n"); steps.flush()
            eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                steps.write("STOP_AFTER_RESTART|" + bad[0] + "\n"); stats["stop_run"] += 1
                break

    rc = eng.close()
    steps.write(f"# engine_exit\t{rc}\n")
    steps.close()
    with open(a.out + ".summary", "w") as f:
        for k, v in stats.items():
            f.write(f"{k}\t{v}\n")
        f.write(f"engine_exit_code\t{rc}\n")
    meta.write(f"engine_exit_code\t{rc}\n")
    meta.close()
    print(open(a.out + ".summary").read())


if __name__ == "__main__":
    main()
