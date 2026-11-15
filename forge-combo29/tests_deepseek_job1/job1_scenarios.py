#!/usr/bin/env python3
"""Job 1: ThreadSanitizer campaign, command thread against the search threads.

One driver for all scenarios so the command/wait/verification logic exists in one
place. Every wait comes from random.Random(20261118) drawn in a fixed order, so a
scenario can be repeated.

Design points that matter for the result to mean anything:
  * stdout and stderr are separate files per scenario (TSan writes stderr).
  * a reader THREAD consumes stdout continuously, so `info` lines that arrive
    while the driver is sleeping are captured as they happen. Without this the
    "the command arrived while the search was running" evidence is lost: lines
    would sit unread in the pipe until the process ended.
  * nothing is piped in advance: each command is written, then the driver waits
    for the reply it expects.
  * every returned move is checked for legality with python-chess.
  * per repetition the driver records the node count of the last `info` line seen
    BEFORE the interrupting command was sent, which is the evidence that the
    search was live at that moment.

Usage: job1_scenarios.py <scenario> <net-mode> <outdir>
  scenario: S1 S2 S3 S4 S5 S6 S7
  net-mode: file | builtin
"""
import json
import os
import queue
import random
import subprocess
import sys
import threading
import time

import chess

ENGINE = "/tmp/ds/build-tsan/forge"
NET = "/tmp/ds/netgen/random_h512.fnn3"
POSITIONS = "/tmp/ds_positions.txt"
SEED = 20261118
BESTMOVE_TIMEOUT = 120.0


class EngineGone(RuntimeError):
    """Raised when the engine process has gone away and cannot accept input."""


class Engine:
    """One UCI engine process; stdout is drained by a background thread."""

    def __init__(self, stdout_path, stderr_path, threads=4, hash_mb=16, net_mode="file", ponder=False):
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.out = open(stdout_path, "w")
        self.err = open(stderr_path, "w")
        self.proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.err, text=True, bufsize=1)
        self.queue = queue.Queue()
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()
        self.info_seen = 0          # total `info` lines received
        self.last_nodes = None      # nodes of the most recent info line
        self.last_info = None
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name Hash value {hash_mb}")
        if net_mode == "file":
            self.send(f"setoption name NNUEArchFile value {NET}")
            self.send("setoption name NNUEArch value true")
        elif net_mode == "builtin-nov3":
            self.send("setoption name NNUEArch value false")
        if ponder:
            self.send("setoption name Ponder value true")
        self.isready()

    def _read_loop(self):
        for line in self.proc.stdout:
            self.queue.put(line.rstrip("\n"))
            self.out.write(line)
            self.out.flush()
        self.queue.put(None)

    def send(self, command):
        try:
            self.proc.stdin.write(command + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            # The engine is gone (for example it exited on a fail-loud check).
            # Record it rather than crashing the driver.
            self.dead_on_send = f"{type(exc).__name__} while sending {command!r}"
            raise EngineGone(self.dead_on_send) from exc

    def _consume(self, line):
        if line.startswith("info"):
            self.info_seen += 1
            self.last_info = line
            nodes = nodes_of(line)
            if nodes is not None:
                self.last_nodes = nodes

    def pump(self, duration):
        """Read for `duration` seconds, updating the info counters. Returns count read."""
        deadline = time.monotonic() + duration
        count = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return count
            try:
                line = self.queue.get(timeout=remaining)
            except queue.Empty:
                return count
            if line is None:
                return count
            self._consume(line)
            count += 1

    def drain_until(self, needle, timeout):
        """Consume lines until one starts with `needle`. Returns that line or None."""
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                line = self.queue.get(timeout=remaining)
            except queue.Empty:
                return None
            if line is None:
                return None
            self._consume(line)
            if line.startswith(needle):
                return line

    def isready(self):
        self.send("isready")
        return self.drain_until("readyok", 180.0) is not None

    def is_alive(self):
        return self.proc.poll() is None

    def quit(self, timeout=120.0):
        try:
            self.send("quit")
        except EngineGone:
            pass
        try:
            self.proc.wait(timeout=timeout)
            code = self.proc.returncode
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            code = "did-not-quit"
        self.reader.join(timeout=10.0)
        self.out.close()
        self.err.close()
        return code


def load_positions():
    with open(POSITIONS) as f:
        return [line.strip() for line in f if line.strip()]


def check_move(fen, move_text):
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        return False, f"bad fen: {exc}"
    if move_text in (None, "", "(none)"):
        return False, "no move text"
    try:
        move = chess.Move.from_uci(move_text)
    except ValueError:
        return False, f"unparsable move {move_text!r}"
    if move not in board.legal_moves:
        return False, f"illegal move {move_text} in {fen}"
    return True, ""


def nodes_of(info_line):
    if not info_line:
        return None
    parts = info_line.split()
    for i, tok in enumerate(parts):
        if tok == "nodes" and i + 1 < len(parts):
            try:
                return int(parts[i + 1])
            except ValueError:
                return None
    return None


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def tail_lines(path, count):
    try:
        with open(path, errors="replace") as f:
            lines = [l.rstrip("\n") for l in f]
        return lines[-count:]
    except OSError as exc:
        return [f"<cannot read {path}: {exc}>"]


def run_s1(rng, positions, net_mode, results):
    """S1: 300 x (position, go infinite, wait 5-200 ms, stop, wait bestmove)."""
    eng = Engine(f"{results}/S1-{net_mode}.stdout.log", f"{results}/S1-{net_mode}.stderr.log", net_mode=net_mode)
    no_bestmove = 0
    illegal = 0
    done = 0
    live_at_stop = []      # (nodes_before_stop, info_lines_before_stop)
    started = time.time()
    for i in range(300):
        fen = positions[i % len(positions)]
        wait_ms = rng.randint(5, 200)
        nodes_before = eng.last_nodes
        info_before = eng.info_seen
        eng.send(f"position fen {fen}")
        eng.send("go infinite")
        eng.pump(wait_ms / 1000.0)
        nodes_at = eng.last_nodes
        info_at = eng.info_seen
        eng.send("stop")
        line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
        if line is None:
            no_bestmove += 1
            break
        done += 1
        live_at_stop.append((nodes_at, info_at - info_before))
        move_text = line.split()[1] if len(line.split()) > 1 else None
        good, _why = check_move(fen, move_text)
        if not good:
            illegal += 1
    code = eng.quit()
    nodes = [n for n, _ in live_at_stop if n is not None]
    return {
        "repetitions": done,
        "exit_code": code,
        "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove,
        "illegal_moves": illegal,
        "nodes_at_stop_min": min(nodes) if nodes else None,
        "nodes_at_stop_median": median(nodes),
        "nodes_at_stop_max": max(nodes) if nodes else None,
        "stopped_with_zero_nodes": sum(1 for n in nodes if n == 0),
        "reps_with_no_info_before_stop": sum(1 for _, c in live_at_stop if c == 0),
        "info_lines_before_stop_median": median([c for _, c in live_at_stop]),
    }


def run_s2(rng, positions, net_mode, results):
    """S2: 60 rounds of go depth 7, then one mutation, then isready."""
    eng = Engine(f"{results}/S2-{net_mode}.stdout.log", f"{results}/S2-{net_mode}.stderr.log", net_mode=net_mode)
    # NNUEArch true with no net loaded is a hard error in this engine (v3_ready()
    # fails and isready exits with code 2), so the builtin variant of this
    # scenario cannot include those mutations. net_mode "builtin-nov3" is that
    # variant; net_mode "builtin" keeps the full cycle so the fail-loud path is
    # recorded as a finding rather than silently avoided.
    mutations = (
        [f"setoption name Threads value {t}" for t in (1, 2, 8, 3, 4)]
        + [f"setoption name Hash value {h}" for h in (1, 64, 16)]
        + ["setoption name NNUEArch value false", "setoption name NNUEArch value true",
           f"setoption name NNUEArchFile value {NET}", "ucinewgame"]
    )
    if net_mode == "builtin-nov3":
        mutations = [m for m in mutations if "NNUEArch" not in m]
    no_bestmove = 0
    illegal = 0
    done = 0
    applied = []
    early_exit = None
    started = time.time()
    for i in range(60):
        fen = positions[i % len(positions)]
        eng.send(f"position fen {fen}")
        eng.send("go depth 7")
        line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
        if line is None:
            no_bestmove += 1
            break
        move_text = line.split()[1] if len(line.split()) > 1 else None
        good, _why = check_move(fen, move_text)
        if not good:
            illegal += 1
        mutation = mutations[i % len(mutations)]
        try:
            eng.send(mutation)
            applied.append(mutation)
            if not eng.isready():
                # isready produced no readyok. In this engine that is what a
                # fail-loud check looks like: the process exits(2) inside isready.
                died_at = {"round": i, "mutation": mutation,
                           "detail": "no readyok from isready",
                           "engine_exit_code": eng.proc.poll(),
                           "stdout_tail": tail_lines(f"{results}/S2-{net_mode}.stdout.log", 3)}
                with open(f"{results}/S2-{net_mode}.engine-exit.txt", "w") as f:
                    f.write(json.dumps(died_at, indent=2) + "\n")
                early_exit = died_at
                no_bestmove += 1
                break
        except EngineGone:
            # Fail-loud exit: the engine refused to continue. Record where.
            died_at = {"round": i, "mutation": mutation,
                       "detail": getattr(eng, "dead_on_send", "engine gone"),
                       "engine_exit_code": eng.proc.poll()}
            with open(f"{results}/S2-{net_mode}.engine-exit.txt", "w") as f:
                f.write(json.dumps(died_at, indent=2) + "\n")
            early_exit = died_at
            break
        done += 1
    code = eng.quit()
    return {
        "rounds": done,
        "mutation_cycle_length": len(mutations),
        "exit_code": code,
        "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove,
        "illegal_moves": illegal,
        "engine_ended_the_run_early": early_exit,
        "mutations_applied": applied,
    }


def run_s3(rng, positions, net_mode, results):
    """S3: 40 fresh processes, go infinite, wait 20-300 ms, quit."""
    per_process = []
    started = time.time()
    for i in range(40):
        stdout_path = f"{results}/S3-{net_mode}.p{i:02d}.stdout.log"
        stderr_path = f"{results}/S3-{net_mode}.p{i:02d}.stderr.log"
        eng = Engine(stdout_path, stderr_path, net_mode=net_mode)
        fen = positions[i % len(positions)]
        wait_ms = rng.randint(20, 300)
        info_before = eng.info_seen
        eng.send(f"position fen {fen}")
        eng.send("go infinite")
        eng.pump(wait_ms / 1000.0)
        nodes_before_quit = eng.last_nodes
        info_before_quit = eng.info_seen - info_before
        t_quit = time.monotonic()
        eng.send("quit")
        try:
            eng.proc.wait(timeout=10.0)
            gone_s = time.monotonic() - t_quit
            code = eng.proc.returncode
            stuck = False
        except subprocess.TimeoutExpired:
            gone_s = time.monotonic() - t_quit
            eng.proc.kill()
            eng.proc.wait()
            code = "killed-after-10s"
            stuck = True
        eng.reader.join(timeout=10.0)
        eng.out.close()
        eng.err.close()
        per_process.append({
            "i": i, "wait_ms": wait_ms, "exit_code": code,
            "gone_s": round(gone_s, 3), "stuck": stuck,
            "nodes_before_quit": nodes_before_quit,
            "info_lines_before_quit": info_before_quit,
        })
    codes = {}
    for p in per_process:
        codes[str(p["exit_code"])] = codes.get(str(p["exit_code"]), 0) + 1
    nodes = [p["nodes_before_quit"] for p in per_process if p["nodes_before_quit"] is not None]
    return {
        "processes": len(per_process),
        "exit_codes": codes,
        "wall_s": round(time.time() - started, 1),
        "max_gone_s": max(p["gone_s"] for p in per_process),
        "stuck": sum(1 for p in per_process if p["stuck"]),
        "processes_with_no_info_before_quit": sum(1 for p in per_process if p["info_lines_before_quit"] == 0),
        "nodes_before_quit_min": min(nodes) if nodes else None,
        "nodes_before_quit_median": median(nodes),
        "per_process": per_process,
    }


def run_s4(rng, positions, net_mode, results):
    """S4: 100 x (go ponder, wait, ponderhit, 50 ms, stop) then 100 x (go ponder, wait, stop)."""
    eng = Engine(f"{results}/S4-{net_mode}.stdout.log", f"{results}/S4-{net_mode}.stderr.log",
                 net_mode=net_mode, ponder=True)
    no_bestmove = 0
    illegal = 0
    phase_a = 0
    phase_b = 0
    nodes_a = []
    started = time.time()
    for i in range(100):
        fen = positions[i % len(positions)]
        wait_ms = rng.randint(20, 200)
        eng.send(f"position fen {fen}")
        eng.send("go ponder wtime 60000 btime 60000")
        eng.pump(wait_ms / 1000.0)
        pre_hit_nodes = eng.last_nodes
        eng.send("ponderhit")
        eng.pump(0.050)
        eng.send("stop")
        line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
        if line is None:
            no_bestmove += 1
            break
        phase_a += 1
        if pre_hit_nodes is not None:
            nodes_a.append(pre_hit_nodes)
        move_text = line.split()[1] if len(line.split()) > 1 else None
        good, _why = check_move(fen, move_text)
        if not good:
            illegal += 1
    if no_bestmove == 0:
        for i in range(100):
            fen = positions[(i + 100) % len(positions)]
            wait_ms = rng.randint(20, 200)
            eng.send(f"position fen {fen}")
            eng.send("go ponder wtime 60000 btime 60000")
            eng.pump(wait_ms / 1000.0)
            eng.send("stop")
            line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
            if line is None:
                no_bestmove += 1
                break
            phase_b += 1
            move_text = line.split()[1] if len(line.split()) > 1 else None
            good, _why = check_move(fen, move_text)
            if not good:
                illegal += 1
    code = eng.quit()
    return {
        "phase_a_ponderhit_then_stop": phase_a,
        "phase_b_stop_without_ponderhit": phase_b,
        "exit_code": code,
        "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove,
        "illegal_moves": illegal,
        "nodes_before_ponderhit_min": min(nodes_a) if nodes_a else None,
        "nodes_before_ponderhit_median": median(nodes_a),
    }


def run_s5(rng, positions, net_mode, results):
    """S5: 200 movetime 40, 200 nodes 20000, 200 wtime/btime."""
    eng = Engine(f"{results}/S5-{net_mode}.stdout.log", f"{results}/S5-{net_mode}.stderr.log", net_mode=net_mode)
    no_bestmove = 0
    illegal = 0
    done = 0
    started = time.time()
    per_kind = {}
    for command, count in (("go movetime 40", 200), ("go nodes 20000", 200),
                           ("go wtime 1500 btime 1500 winc 15 binc 15", 200)):
        k_no_best = 0
        k_illegal = 0
        k_done = 0
        for i in range(count):
            fen = positions[(done + i) % len(positions)]
            eng.send(f"position fen {fen}")
            eng.send(command)
            line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
            if line is None:
                k_no_best += 1
                break
            k_done += 1
            move_text = line.split()[1] if len(line.split()) > 1 else None
            good, _why = check_move(fen, move_text)
            if not good:
                k_illegal += 1
        per_kind[command] = {"done": k_done, "no_bestmove": k_no_best, "illegal_moves": k_illegal}
        done += k_done
        no_bestmove += k_no_best
        illegal += k_illegal
        if k_no_best:
            break
    code = eng.quit()
    return {
        "searches": done,
        "per_kind": per_kind,
        "exit_code": code,
        "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove,
        "illegal_moves": illegal,
    }


def run_s6(positions, net_mode, results):
    """S6: MultiPV 4, go depth 8, 100 positions."""
    eng = Engine(f"{results}/S6-{net_mode}.stdout.log", f"{results}/S6-{net_mode}.stderr.log", net_mode=net_mode)
    eng.send("setoption name MultiPV value 4")
    eng.isready()
    no_bestmove = 0
    illegal = 0
    done = 0
    started = time.time()
    for i in range(100):
        fen = positions[i % len(positions)]
        eng.send(f"position fen {fen}")
        eng.send("go depth 8")
        line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
        if line is None:
            no_bestmove += 1
            break
        move_text = line.split()[1] if len(line.split()) > 1 else None
        good, _why = check_move(fen, move_text)
        if not good:
            illegal += 1
        done += 1
    code = eng.quit()
    return {
        "searches": done, "exit_code": code, "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove, "illegal_moves": illegal,
    }


def run_s7(positions, net_mode, results):
    """S7: Threads 8 (more than the machine has processors), go depth 10, 150 positions."""
    eng = Engine(f"{results}/S7-{net_mode}.stdout.log", f"{results}/S7-{net_mode}.stderr.log",
                 net_mode=net_mode, threads=8)
    no_bestmove = 0
    illegal = 0
    done = 0
    started = time.time()
    for i in range(150):
        fen = positions[i % len(positions)]
        eng.send(f"position fen {fen}")
        eng.send("go depth 10")
        line = eng.drain_until("bestmove", BESTMOVE_TIMEOUT)
        if line is None:
            no_bestmove += 1
            break
        move_text = line.split()[1] if len(line.split()) > 1 else None
        good, _why = check_move(fen, move_text)
        if not good:
            illegal += 1
        done += 1
    code = eng.quit()
    return {
        "searches": done, "exit_code": code, "wall_s": round(time.time() - started, 1),
        "no_bestmove": no_bestmove, "illegal_moves": illegal,
    }


RUNNERS = {"S1": run_s1, "S2": run_s2, "S3": run_s3, "S4": run_s4,
           "S5": run_s5, "S6": run_s6, "S7": run_s7}


def main():
    scenario, net_mode, results = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(results, exist_ok=True)
    positions = load_positions()
    rng = random.Random(SEED)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.time()
    runner = RUNNERS[scenario]
    if scenario in ("S6", "S7"):
        r = runner(positions, net_mode, results)
    else:
        r = runner(rng, positions, net_mode, results)
    summary = {"scenario": scenario, "net": net_mode, "started_utc": started,
               "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "elapsed_s": round(time.time() - t0, 1)}
    per_process = r.pop("per_process", None)
    summary.update(r)
    with open(f"{results}/{scenario}-{net_mode}.summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    if per_process is not None:
        with open(f"{results}/{scenario}-{net_mode}.per-process.json", "w") as f:
            json.dump(per_process, f, indent=2)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
