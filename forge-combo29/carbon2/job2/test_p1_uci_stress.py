#!/usr/bin/env python3
"""
UCI protocol concurrency stress test for Piece P1 (persistent search thread):
Runs on normal build, ThreadSanitizer (-fsanitize=thread) build, and planted-fault build:
- Both Threads 1 and Threads 4 (with PC20 + net768 active + initial `eval` check).
- `go infinite` -> wait active depth -> `stop`
- `go ponder wtime 60000 btime 60000` -> `ponderhit` -> `stop` (and unclocked `go ponder` -> `ponderhit` -> `stop`)
- `isready` during active `go infinite` search (must reply `readyok` while searching, then `stop`)
- `setoption` during active `go infinite` search
- `ucinewgame` during active `go infinite` search
- 1,000 fast cycles of `position` + `go softnodes 200`, with `stop` sent at a random moment in every third cycle
- `quit` during an active `go infinite` search
Pass criteria:
- Strict timeout on every wait (no hang).
- Zero ThreadSanitizer diagnostics or stderr errors.
- Clean process exit code 0.
- Exact 1-to-1 bijection: total `bestmove` lines received == total `go` commands issued.
"""

import argparse
import pathlib
import queue
import random
import subprocess
import threading
import time

PC20_BASE = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("CuckooRep", "true"),
    ("HistRework", "2"),
    ("TtPruneV2", "true"),
    ("CorrHistV2", "true"),
    ("MateAlphaGuard", "true"),
    ("OwnBook", "false"),
    ("Hash", "16"),
]


class StressHarness:
    def __init__(self, exe: str, timeout_s: float = 5.0):
        self.timeout_s = timeout_s
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.out_q: queue.Queue[str | None] = queue.Queue()
        self.err_lines: list[str] = []
        self.bestmove_count = 0
        self.go_count = 0
        self._t_out = threading.Thread(target=self._pump_out, daemon=True)
        self._t_err = threading.Thread(target=self._pump_err, daemon=True)
        self._t_out.start()
        self._t_err.start()

    def _pump_out(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.out_q.put(line.rstrip("\r\n"))
        self.out_q.put(None)

    def _pump_err(self):
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.err_lines.append(line.rstrip("\r\n"))

    def send(self, text: str):
        assert self.proc.stdin is not None
        for ln in text.splitlines():
            s = ln.strip()
            if s == "go" or s.startswith("go ") and not s.startswith("go perft"):
                self.go_count += 1
        self.proc.stdin.write(text)
        self.proc.stdin.flush()

    def wait_until(self, predicate, desc: str) -> str:
        deadline = time.monotonic() + self.timeout_s
        while True:
            rem = deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError(f"Timeout ({self.timeout_s}s) waiting for {desc}")
            try:
                line = self.out_q.get(timeout=rem)
            except queue.Empty as exc:
                raise TimeoutError(f"Timeout ({self.timeout_s}s) waiting for {desc}") from exc
            if line is None:
                if predicate("__EOF__"):
                    return "__EOF__"
                raise RuntimeError(f"Unexpected EOF while waiting for {desc}; stderr={self.err_lines[:5]}")
            if line.startswith("bestmove "):
                self.bestmove_count += 1
            if any(bad in line for bad in ("unknown option", "invalid value", "ERROR")):
                raise RuntimeError(f"Engine reported error line: {line}")
            if predicate(line):
                return line

    def drain_and_wait_exit(self) -> int:
        self.wait_until(lambda ln: ln == "__EOF__", "stdout EOF after quit")
        rc = self.proc.wait(timeout=self.timeout_s)
        self._t_out.join(timeout=1.0)
        self._t_err.join(timeout=1.0)
        return rc

    def kill(self):
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=2.0)


def run_session(exe: str, net_path: str, fens: list[str], threads: int, timeout_s: float, seed: int) -> dict:
    rng = random.Random(seed + threads)
    h = StressHarness(exe, timeout_s=timeout_s)
    try:
        cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in PC20_BASE] + [
            f"setoption name Threads value {threads}\n",
            "setoption name Ponder value true\n",
            f"setoption name NNUEArchFile value {net_path}\n",
            "setoption name NNUEArch value true\n",
            "position startpos\n",
            "eval\n",
            "isready\n",
        ]
        v3_line = ""
        ev_line = ""
        h.send("".join(cfg))

        def got_ready(ln: str) -> bool:
            nonlocal v3_line, ev_line
            if "NNUE v3 active:" in ln:
                v3_line = ln
            elif ln.startswith("info string eval "):
                ev_line = ln
            return ln == "readyok"

        h.wait_until(got_ready, "initial readyok")
        assert v3_line and ev_line, "Missing v3 active or eval line"

        # 1. go infinite -> stop
        bm_before = h.bestmove_count
        h.send("position startpos moves e2e4 e7e5\ngo infinite\n")
        h.wait_until(lambda ln: ln.startswith("info depth 4 "), "go infinite depth 4")
        h.send("stop\n")
        h.wait_until(lambda ln: h.bestmove_count == bm_before + 1, "bestmove after go infinite + stop")

        # 2a. go ponder (clocked) -> ponderhit -> stop
        bm_before = h.bestmove_count
        h.send("position startpos moves d2d4 d7d5\ngo ponder wtime 60000 btime 60000\n")
        h.wait_until(lambda ln: ln.startswith("info depth 4 "), "go ponder clocked depth 4")
        h.send("ponderhit\n")
        time.sleep(0.005)
        h.send("stop\n")
        h.wait_until(lambda ln: h.bestmove_count == bm_before + 1, "bestmove after clocked ponder + ponderhit + stop")

        # 2b. go ponder (unclocked) -> ponderhit -> stop
        bm_before = h.bestmove_count
        h.send("position startpos moves c2c4 e7e6\ngo ponder\n")
        h.wait_until(lambda ln: ln.startswith("info depth 4 "), "go ponder unclocked depth 4")
        h.send("ponderhit\n")
        h.send("stop\n")
        h.wait_until(lambda ln: h.bestmove_count == bm_before + 1, "bestmove after unclocked ponder + ponderhit + stop")

        # 3. isready during active search
        bm_before = h.bestmove_count
        h.send("position startpos moves g1f3 d7d5\ngo infinite\n")
        h.wait_until(lambda ln: ln.startswith("info depth 3 "), "go infinite before mid-search isready")
        h.send("isready\n")
        h.wait_until(lambda ln: ln == "readyok", "readyok during active search")
        assert h.bestmove_count == bm_before, "isready should not stop search prematurely"
        h.send("stop\n")
        h.wait_until(lambda ln: h.bestmove_count == bm_before + 1, "bestmove after mid-search isready + stop")

        # 4. setoption during active search
        bm_before = h.bestmove_count
        h.send("position startpos moves e2e4 c7c5\ngo infinite\n")
        h.wait_until(lambda ln: ln.startswith("info depth 3 "), "go infinite before mid-search setoption")
        h.send("setoption name LmpBase value 8\nisready\n")
        h.wait_until(lambda ln: ln == "readyok", "readyok after mid-search setoption")
        assert h.bestmove_count == bm_before + 1, "setoption must implicitly stop active search and emit 1 bestmove"

        # 5. ucinewgame during active search
        bm_before = h.bestmove_count
        h.send("position startpos moves b1c3 d7d5\ngo infinite\n")
        h.wait_until(lambda ln: ln.startswith("info depth 3 "), "go infinite before mid-search ucinewgame")
        h.send("ucinewgame\nisready\n")
        h.wait_until(lambda ln: ln == "readyok", "readyok after mid-search ucinewgame")
        assert h.bestmove_count == bm_before + 1, "ucinewgame must implicitly stop active search and emit 1 bestmove"

        # 6. 1,000 fast cycles of position + go softnodes 200, with stop at random moment in every third
        for i in range(1000):
            fen = fens[i % len(fens)]
            bm_target = h.bestmove_count + 1
            h.send(f"position fen {fen}\ngo softnodes 200\n")
            if i % 3 == 0:
                delay = rng.uniform(0.0, 0.0015)
                if delay > 0:
                    time.sleep(delay)
                h.send("stop\n")
            h.wait_until(lambda ln, t=bm_target: h.bestmove_count == t, f"fast cycle {i} bestmove")
            assert h.bestmove_count == h.go_count, f"Cycle {i}: bestmoves={h.bestmove_count} != goes={h.go_count}"

        # 7. quit during an active search
        h.send("position startpos moves e2e4 e7e5 g1f3 b8c6\ngo infinite\n")
        h.wait_until(lambda ln: ln.startswith("info depth 3 "), "go infinite before mid-search quit")
        h.send("quit\n")
        rc = h.drain_and_wait_exit()
        if rc != 0:
            raise RuntimeError(f"Non-zero exit code {rc}; stderr={h.err_lines}")
        if h.err_lines:
            raise RuntimeError(f"Non-empty stderr (TSan/sanitizer report): {h.err_lines[:20]}")
        if h.bestmove_count != h.go_count:
            raise RuntimeError(f"bestmove_count ({h.bestmove_count}) != go_count ({h.go_count})")

        return {
            "threads": threads,
            "go_count": h.go_count,
            "bestmove_count": h.bestmove_count,
            "stderr_lines": len(h.err_lines),
            "v3_active": v3_line,
            "setup_eval": ev_line,
            "status": "PASS",
        }
    finally:
        h.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal-exe", required=True)
    ap.add_argument("--tsan-exe", required=True)
    ap.add_argument("--fault-exe", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--fen-file", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fens = [ln.strip() for ln in pathlib.Path(args.fen_file).read_text().splitlines() if ln.strip()]
    lines = []
    def log(msg: str):
        print(msg, flush=True)
        lines.append(msg)

    log("=== 1. Planted-Fault Verification (FORGE_TEST_P1_PLANT_NO_DONE_NOTIFY: omit done_cv.notify_all()) ===")
    fault_caught = False
    try:
        run_session(args.fault_exe, args.net, fens, threads=1, timeout_s=2.0, seed=20261117)
    except TimeoutError as exc:
        fault_caught = True
        log(f"  PLANTED FAULT CAUGHT AS EXPECTED -> FAILED with TimeoutError: {exc}")
    if not fault_caught:
        raise AssertionError("Planted fault build unexpectedly passed!")

    log("\n=== 2. Normal Release Build Stress Test (Threads 1 and Threads 4, 1,000 fast cycles + protocol interrupts) ===")
    for th in (1, 4):
        t0 = time.monotonic()
        res = run_session(args.normal_exe, args.net, fens, threads=th, timeout_s=8.0, seed=20261117)
        dt = time.monotonic() - t0
        log(f"  Normal build Threads={th} ({dt:.2f}s): {res}")

    log("\n=== 3. ThreadSanitizer (-fsanitize=thread) Stress Test (Threads 1 and Threads 4, 1,000 fast cycles + protocol interrupts) ===")
    for th in (1, 4):
        t0 = time.monotonic()
        res = run_session(args.tsan_exe, args.net, fens, threads=th, timeout_s=20.0, seed=20261117)
        dt = time.monotonic() - t0
        log(f"  TSan build Threads={th} ({dt:.2f}s): {res}")

    pathlib.Path(args.out).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
