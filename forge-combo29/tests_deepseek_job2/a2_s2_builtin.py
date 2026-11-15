#!/usr/bin/env python3
"""Job 2 A2: S2 again in builtin mode, but with the net loaded while idle.

The job 1 cycle ended up sending "NNUEArch true" while no net was loaded, which is a
fail-loud exit (exit code 2) in this engine. This cycle instead sends
  NNUEArchFile <net>   (load while idle)
  NNUEArch true        (now it takes effect)
  NNUEArch false       (back to the built-in net)
so the load-while-idle path is covered and 60 rounds can complete.

Everything else matches job 1's S2: one process, Threads 4 / Hash 16 to start,
go depth 7 with a wait for bestmove before every mutation, then isready.

Usage: a2_s2_builtin.py <outdir>
"""
import json
import os
import random
import subprocess
import sys
import threading
import queue
import time

import chess

ENGINE = "/tmp/ds/build-tsan/forge"
NET = "/tmp/ds/netgen/random_h512.fnn3"
POSITIONS = "/tmp/ds_positions.txt"
SEED = 20261118
ROUNDS = 60


def nodes_of(line):
    parts = line.split()
    for i, tok in enumerate(parts):
        if tok == "nodes" and i + 1 < len(parts):
            try:
                return int(parts[i + 1])
            except ValueError:
                return None
    return None


class Engine:
    def __init__(self, out_path, err_path):
        self.out = open(out_path, "w")
        self.err = open(err_path, "w")
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.err, text=True, bufsize=1)
        self.q = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.info_seen = 0

    def _read(self):
        for line in self.proc.stdout:
            self.out.write(line)
            self.out.flush()
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, command):
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def until(self, needle, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                return None
            if line.startswith("info"):
                self.info_seen += 1
            if line.startswith(needle):
                return line

    def quit(self):
        try:
            self.send("quit")
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=60)
            code = self.proc.returncode
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            code = "did-not-quit"
        self.reader.join(timeout=10)
        self.out.close()
        self.err.close()
        return code


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    with open(POSITIONS) as f:
        positions = [l.strip() for l in f if l.strip()]
    rng = random.Random(SEED)
    stdout_path = f"{outdir}/A2-S2-builtin-fileturnedtrue.stdout.log"
    stderr_path = f"{outdir}/A2-S2-builtin-fileturnedtrue.stderr.log"

    eng = Engine(stdout_path, stderr_path)
    eng.send("setoption name Threads value 4")
    eng.send("setoption name Hash value 16")
    # Start in built-in mode on purpose: NNUEArch off, nothing loaded.
    eng.send("setoption name NNUEArch value false")
    eng.send("isready")
    eng.until("readyok", 120)

    cycle = (
        [f"setoption name Threads value {t}" for t in (1, 2, 8, 3, 4)]
        + [f"setoption name Hash value {h}" for h in (1, 64, 16)]
        + [f"setoption name NNUEArchFile value {NET}",   # load while idle
           "setoption name NNUEArch value true",         # now active
           "setoption name NNUEArch value false",        # back to built-in
           "ucinewgame"]
    )

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.time()
    done = 0
    no_bestmove = 0
    illegal = 0
    applied = []
    early_exit = None
    for i in range(ROUNDS):
        fen = positions[i % len(positions)]
        eng.send(f"position fen {fen}")
        eng.send("go depth 7")
        line = eng.until("bestmove", 180)
        if line is None:
            no_bestmove += 1
            early_exit = {"round": i, "detail": "no bestmove", "engine_exit_code": eng.proc.poll()}
            break
        move_text = line.split()[1] if len(line.split()) > 1 else None
        board = chess.Board(fen)
        try:
            ok = chess.Move.from_uci(move_text) in board.legal_moves
        except (ValueError, AttributeError):
            ok = False
        if not ok:
            illegal += 1
        mutation = cycle[i % len(cycle)]
        try:
            eng.send(mutation)
            applied.append(mutation)
            eng.send("isready")
            if eng.until("readyok", 180) is None:
                early_exit = {"round": i, "mutation": mutation, "detail": "no readyok",
                              "engine_exit_code": eng.proc.poll()}
                no_bestmove += 1
                break
        except (BrokenPipeError, ValueError):
            early_exit = {"round": i, "mutation": mutation, "detail": "engine gone",
                          "engine_exit_code": eng.proc.poll()}
            no_bestmove += 1
            break
        done += 1

    code = eng.quit()
    summary = {
        "part": "A2", "scenario": "S2-builtin-fileturnedtrue",
        "started_utc": started,
        "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "rounds": done, "target_rounds": ROUNDS,
        "cycle": cycle, "cycle_length": len(cycle),
        "no_bestmove": no_bestmove, "illegal_moves": illegal,
        "exit_code": code, "engine_ended_the_run_early": early_exit,
        "mutations_applied": applied,
    }
    with open(f"{outdir}/A2-S2-builtin-fileturnedtrue.summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("mutations_applied", "cycle")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
