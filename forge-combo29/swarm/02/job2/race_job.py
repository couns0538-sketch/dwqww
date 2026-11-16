#!/usr/bin/env python3
"""S02 AREA 2 job 2 — races: interrupt a running search 1,000 times per command.

Commands: stop, ponderhit, ucinewgame, setoption Hash, quit.
Search under interrupt: `go infinite` or `go depth 30` (chosen by the seed), one of them per run.
Delay before the interrupt: random 0..50 ms (seed 202).
After each interrupt the run sends `isready` and expects `readyok` within 20 s, and (except for quit)
then a plain `go depth 2` from the position the engine now holds, to see whether it still answers.

Every run records: exit kind, wall, sanitizer lines, whether a readyok came, whether the follow-up
search answered, whether the bestmove printed for the interrupted search was legal in the position the
engine had when `go` was sent, and whether a bestmove arrived after `quit`.

usage: race_job.py <exe> <outdir> [count]
"""
import json
import os
import random
import re
import signal
import subprocess
import sys
import threading
import time

import chess

SEED = 202
TIMEOUT_S = 20.0
SAN_RE = re.compile(r"ERROR: AddressSanitizer|runtime error:|ERROR: LeakSanitizer|"
                    r"SUMMARY: (AddressSanitizer|UndefinedBehaviorSanitizer)")

FENS = [
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
]
COMMANDS = ["stop", "ponderhit", "ucinewgame", "setoption Hash", "quit"]


class Engine:
    def __init__(self, exe):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
                                     start_new_session=True)
        self.lines = []
        self.lock = threading.Lock()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.send("uci")
        self.wait_for("uciok", 10.0)

    def _read(self):
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))

    def send(self, text):
        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
        except Exception:
            pass

    def snapshot(self):
        with self.lock:
            return list(self.lines)

    def wait_for(self, prefix, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                for i, l in enumerate(self.lines):
                    if l.startswith(prefix):
                        return True, i
            if self.proc.poll() is not None:
                break
            time.sleep(0.002)
        return False, -1

    def wait_after(self, prefix, start_index, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                for i in range(start_index, len(self.lines)):
                    if self.lines[i].startswith(prefix):
                        return True, i
            if self.proc.poll() is not None:
                break
            time.sleep(0.002)
        return False, -1

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            pass


def run_one(exe, rng, cmd, idx):
    fen = FENS[idx % len(FENS)]
    board = chess.Board(fen)
    legal = {m.uci() for m in board.legal_moves}
    search = "go infinite" if rng.random() < 0.5 else "go depth 30"
    delay_ms = rng.randint(0, 50)
    rec = {"id": idx, "command": cmd, "search": search, "delay_ms": delay_ms, "fen": fen,
           "crashed": False, "hung": False, "sanitizer_lines": 0, "sanitizer_first": [],
           "exited_after_quit": None, "readyok_after": None, "followup_answered": None,
           "interrupted_bestmove": [], "illegal": [], "bestmove_after_quit": 0,
           "continued_after_ponderhit": None,
           "output_lines": 0, "notes": []}
    eng = Engine(exe)
    try:
        eng.send("setoption name OwnBook value false")
        eng.send("position fen " + fen)
        eng.send("isready")
        ok, _ = eng.wait_for("readyok", 10.0)
        if not ok:
            rec["notes"].append("no readyok after setoption/position")
        n_before = len(eng.snapshot())
        eng.send(search)
        time.sleep(delay_ms / 1000.0)

        if cmd == "stop":
            eng.send("stop")
        elif cmd == "ponderhit":
            eng.send("ponderhit")
            # A `ponderhit` only means something for a search started with `go ponder`. These searches are
            # `go infinite` / `go depth 30`, so a correct engine treats ponderhit as a no-op and KEEPS
            # SEARCHING. That is observed and recorded (field ``continued_after_ponderhit``); we then send
            # `stop` so the run can finish, and require a bestmove after the stop.
            before = len(eng.snapshot())
            time.sleep(0.15)
            rec["continued_after_ponderhit"] = not any(
                l.startswith("bestmove") for l in eng.snapshot()[before:])
            eng.send("stop")
        elif cmd == "ucinewgame":
            eng.send("ucinewgame")
        elif cmd == "setoption Hash":
            eng.send("setoption name Hash value %d" % rng.choice([1, 8, 64, 128, 512, 2048]))
        elif cmd == "quit":
            eng.send("quit")
            try:
                eng.proc.wait(timeout=5.0)
                rec["exited_after_quit"] = True
            except subprocess.TimeoutExpired:
                rec["exited_after_quit"] = False
                eng.kill()
            final = eng.snapshot()
            with eng.lock:
                q_at = len(eng.lines)
            # a bestmove printed at or after the quit position would be in the tail we cannot index;
            # count any bestmove that arrived after the search started
            rec["bestmove_after_quit"] = sum(1 for l in final[n_before:] if l.startswith("bestmove"))
            rec["output_lines"] = len(final)
            rec["sanitizer_lines"] = len([l for l in final if SAN_RE.search(l)])
            rec["sanitizer_first"] = [l for l in final if SAN_RE.search(l)][:2]
            return rec

        # non-quit interrupts: the engine should answer the interrupted search and still be usable
        got, at = eng.wait_after("bestmove", n_before, TIMEOUT_S)
        if not got:
            if eng.proc.poll() is not None:
                rec["crashed"] = True
                rec["notes"].append("process gone without a bestmove")
            else:
                rec["hung"] = True
        else:
            rec["interrupted_bestmove"] = [eng.snapshot()[at]]
            bm = eng.snapshot()[at].split()[1] if len(eng.snapshot()[at].split()) > 1 else ""
            # after ucinewgame the engine's board is the start position; the move it was searching
            # belongs to `fen`. Judge it against the board it actually had.
            judge_legal = legal
            if bm and bm != "0000" and bm not in judge_legal:
                rec["illegal"].append({"bestmove": bm, "fen": fen})
        # readiness and a follow-up search
        n2 = len(eng.snapshot())
        eng.send("isready")
        ok, _ = eng.wait_after("readyok", n2, TIMEOUT_S)
        rec["readyok_after"] = ok
        n3 = len(eng.snapshot())
        eng.send("go depth 2")
        ok, _ = eng.wait_after("bestmove", n3, TIMEOUT_S)
        rec["followup_answered"] = ok
        if not ok:
            rec["notes"].append("follow-up search gave no bestmove")
        eng.send("quit")
        try:
            eng.proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            rec["exited_after_quit"] = False
            eng.kill()
    finally:
        if eng.proc.poll() is None:
            eng.kill()
        final = eng.snapshot()
        san = [l for l in final if SAN_RE.search(l)]
        rec["sanitizer_lines"] = len(san)
        rec["sanitizer_first"] = san[:2]
        rec["output_lines"] = len(final)
        if eng.proc.poll() not in (0, None) and rec["exited_after_quit"] is not False:
            rec["exit_code"] = eng.proc.poll()
        rc = eng.proc.poll()
        if rc is not None and rc < 0:
            rec["crashed"] = True
            rec["notes"].append("killed by signal %d" % (-rc))
    return rec


def main():
    exe = sys.argv[1]
    outdir = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    os.makedirs(outdir, exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    meta = {
        "exe": exe,
        "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
        "nm_asan": subprocess.run("nm -C %s | grep -c __asan_" % exe, shell=True,
                                  capture_output=True, text=True).stdout.strip(),
        "nm_ubsan": subprocess.run("nm -C %s | grep -c __ubsan_" % exe, shell=True,
                                   capture_output=True, text=True).stdout.strip(),
        "seed": SEED, "runs_per_command": count,
        "timeout_s": TIMEOUT_S,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "option_lines_sent": ["setoption name OwnBook value false",
                              "setoption name Hash value <random of 1,8,64,128,512,2048> (setoption Hash arm)"],
        "id_answer": subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True,
                                    env=env).stdout.splitlines()[:2],
    }
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    rng = random.Random(SEED)
    all_recs = []
    for cmd in COMMANDS:
        recs = []
        t0 = time.monotonic()
        for i in range(count):
            recs.append(run_one(exe, rng, cmd, i))
            if (i + 1) % 100 == 0:
                print("%s %d/%d  %.1fs" % (cmd, i + 1, count, time.monotonic() - t0), flush=True)
        all_recs.extend(recs)
        json.dump(recs, open(os.path.join(outdir, "runs_%s.json" % cmd.replace(" ", "_")), "w"))
        print("== %s done in %.1fs" % (cmd, time.monotonic() - t0), flush=True)
    json.dump(all_recs, open(os.path.join(outdir, "all_runs.json"), "w"))
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
