#!/usr/bin/env python3
"""UCI driver for seat 24 area-4 jobs.  Written to a file first, then run from the file.

Usage: driver.py --exe EXE --fens FILE --count N --threads T --depth D --out PREFIX [--hash MB]
                 [--opts S14|none] [--extra "line"] [--timeout SEC]

Writes:
  PREFIX.meta     exe path started, its sha256, `id name`, every option line sent, env used
  PREFIX.raw      every byte the engine printed (stdout+stderr), timestamped per section
  PREFIX.results  one line per position: <idx>|<fen>|<bestmove or ->|<legal? yes/no/nolegal>|<ms>|<answers>
  PREFIX.summary  counters

Rules enforced (brief): after every setoption and every position send `isready` and read every line up to
readyok; stop the whole run on `unknown option`, `invalid value`, `invalid FEN`, `illegal move`.
"""
import argparse
import hashlib
import os
import queue
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
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()

    def _reader(self):
        for line in self.p.stdout:
            self.raw.write(line)
            self.q.put(line.decode("utf-8", "replace").rstrip("\r\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write((line + "\n").encode())
        self.p.stdin.flush()

    def read_until(self, pred, timeout):
        """collect lines until pred(line) is true; raises TimeoutError; returns lines."""
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

    def expect_ready(self, timeout):
        lines = self.read_until(lambda l: l.strip() == "readyok", timeout)
        bad = [l for l in lines if STOP_PAT.search(l)]
        return lines, bad

    def close(self, timeout=10):
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
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--out", required=True)
    ap.add_argument("--opts", default="S14")
    ap.add_argument("--extra", default="")
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--no-ucinewgame", action="store_true")
    a = ap.parse_args()

    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}

    fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]
    fens = fens[a.start:a.start + a.count]

    opt_lines = []
    if a.opts == "S14":
        opt_lines += [f"setoption name {k} value {v}" for k, v in S14.items()]
    opt_lines += [f"setoption name Hash value {a.hash}", f"setoption name Threads value {a.threads}"]
    if a.extra:
        opt_lines += [x for x in a.extra.split(";") if x.strip()]

    eng = Engine(a.exe, a.out + ".raw", env)
    meta = open(a.out + ".meta", "w")
    meta.write(f"exe_started\t{os.path.abspath(a.exe)}\n")
    meta.write(f"sha256\t{sha256(a.exe)}\n")
    meta.write(f"nm_tsan\t{os.popen('nm -C ' + a.exe + ' | grep -c __tsan_').read().strip()}\n")
    meta.write(f"env\tTSAN_OPTIONS/ASAN_OPTIONS/UBSAN_OPTIONS/LSAN_OPTIONS unset\n")
    meta.write(f"fens\t{os.path.abspath(a.fens)} count={len(fens)} start={a.start}\n")
    meta.write(f"depth\t{a.depth}\ntimeout_per_position_s\t{a.timeout}\n")
    for line in ["uci"] + opt_lines + ["ucinewgame"]:
        meta.write("sent\t" + line + "\n")
    meta.flush()

    res = open(a.out + ".results", "w")
    stats = {"positions": 0, "bestmove": 0, "missing": 0, "illegal": 0, "nolegal_ok": 0,
             "answers": 0, "stop_run": 0, "crashes": 0, "timeouts": 0, "ms_total": 0.0}

    def handshake():
        eng.send("uci")
        eng.read_until(lambda l: l.strip() == "uciok", 60)
        for line in opt_lines:
            eng.send(line)
            eng.send("isready")
            lines, bad = eng.expect_ready(120)
            if bad:
                return bad
        eng.send("ucinewgame")
        eng.send("isready")
        lines, bad = eng.expect_ready(120)
        return bad

    bad = handshake()
    if bad:
        res.write("STOP_AT_HANDSHAKE|" + " / ".join(bad) + "\n")
        stats["stop_run"] += 1
        print("STOP at handshake:", bad)
        res.close(); meta.close(); eng.close()
        return

    idx = 0
    while idx < len(fens):
        fen = fens[idx]
        board = None
        try:
            board = chess.Board(fen)
        except Exception:
            board = None
        legal_count = len(list(board.legal_moves)) if board is not None else None
        try:
            eng.send("position fen " + fen)
            eng.send("isready")
            pre_lines, bad = eng.expect_ready(120)
            if bad:
                res.write(f"{a.start + idx}|{fen}|STOP|{bad[0]}\n")
                stats["stop_run"] += 1
                print("STOP at position:", bad)
                break
            answers = [l for l in pre_lines if l.startswith("info")]
            stats["answers"] += len(answers)
            t0 = time.monotonic()
            eng.send(f"go depth {a.depth}")
            go_lines = eng.read_until(lambda l: l.startswith("bestmove"), a.timeout)
            answers += [l for l in go_lines if l.startswith("info")]
            dt = (time.monotonic() - t0) * 1000.0
            stats["ms_total"] += dt
            bm = go_lines[-1].split()[1]
            stats["bestmove"] += 1
            legality = "?"
            if board is None:
                legality = "fen-invalid-in-python"
            else:
                if bm in ("0000", "(none)"):
                    legality = "nolegal-ok" if legal_count == 0 else "ILLEGAL-0000"
                else:
                    try:
                        mv = chess.Move.from_uci(bm)
                        legality = "legal" if mv in board.legal_moves else "ILLEGAL"
                    except Exception:
                        legality = "ILLEGAL-parse"
                if legality == "legal":
                    pass
                elif legality == "nolegal-ok":
                    stats["nolegal_ok"] += 1
                else:
                    stats["illegal"] += 1
            res.write(f"{a.start + idx}|{fen}|{bm}|{legality}|{dt:.0f}|"
                      + "~".join(answers[-3:]) + "\n")
            res.flush()
            stats["positions"] += 1
        except TimeoutError:
            stats["timeouts"] += 1
            res.write(f"{a.start + idx}|{fen}|TIMEOUT|-\n"); res.flush()
            print("TIMEOUT; restarting process")
            eng.p.kill()
            eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                res.write("STOP_AFTER_RESTART|" + " / ".join(bad) + "\n"); res.flush()
                stats["stop_run"] += 1
                break
        except (EOFError, BrokenPipeError):
            stats["crashes"] += 1
            rc = eng.p.poll()
            res.write(f"{a.start + idx}|{fen}|CRASH|rc={rc}\n"); res.flush()
            print("CRASH rc=", rc, "restarting process")
            eng.close()
            eng = Engine(a.exe, a.out + ".raw", env)
            bad = handshake()
            if bad:
                res.write("STOP_AFTER_RESTART|" + " / ".join(bad) + "\n"); res.flush()
                stats["stop_run"] += 1
                break
            idx += 1
            continue
        idx += 1

    rc = eng.close()
    res.write(f"# engine_exit\t{rc}\n")
    res.close()
    with open(a.out + ".summary", "w") as f:
        f.write(f"positions\t{stats['positions']}\n")
        f.write(f"bestmove_lines\t{stats['bestmove']}\n")
        f.write(f"illegal_bestmoves\t{stats['illegal']}\n")
        f.write(f"nolegal_ok\t{stats['nolegal_ok']}\n")
        f.write(f"info_answer_lines\t{stats['answers']}\n")
        f.write(f"crashes\t{stats['crashes']}\n")
        f.write(f"timeouts\t{stats['timeouts']}\n")
        f.write(f"stop_run\t{stats['stop_run']}\n")
        f.write(f"ms_total\t{stats['ms_total']:.0f}\n")
        f.write(f"engine_exit_code\t{rc}\n")
    meta.write(f"engine_exit_code\t{rc}\n")
    meta.close()
    print(open(a.out + ".summary").read())


if __name__ == "__main__":
    main()
