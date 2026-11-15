#!/usr/bin/env python3
"""Reproducible UCI driver for all 10 findings in REPORT_carbon_review.md.

Usage:
    python3 run_all_tests.py /path/to/forge [/path/to/test_v3.nnue]
"""
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))


class Engine:
    def __init__(self, binary: str):
        self.p = subprocess.Popen(
            [binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.q: "queue.Queue[str | None]" = queue.Queue()
        self.raw_lines: list[str] = []
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()

    def _reader(self) -> None:
        assert self.p.stdout is not None
        for line in self.p.stdout:
            s = line.rstrip("\r\n")
            self.raw_lines.append(s)
            self.q.put(s)
        self.q.put(None)

    def send(self, cmd: str) -> None:
        assert self.p.stdin is not None
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def wait_prefix(self, prefix: str, timeout: float = 10.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            rem = deadline - time.monotonic()
            if rem <= 0:
                return False
            try:
                item = self.q.get(timeout=rem)
            except queue.Empty:
                return False
            if item is None:
                return False
            if item.startswith(prefix):
                return True

    def finish(self) -> str:
        self.send("quit")
        self.p.wait(timeout=5.0)
        return "\n".join(self.raw_lines) + ("\n" if self.raw_lines else "")


def save_out(name: str, text: str) -> None:
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {name} ({len(text.splitlines())} lines)")


def main() -> None:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/forge-build/forge"
    v3_net = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test_v3.nnue"

    # F01: Root 3-fold repetition and halfmove=100 adjudicate cp 0 and play a1b1 instead of d1d8#
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1 moves d1e2 b3c4 e2d1 c4b3 d1e2 b3c4 e2d1 c4b3")
    e.send("go depth 4")
    e.wait_prefix("bestmove ")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 100 60")
    e.send("go depth 4")
    e.wait_prefix("bestmove ")
    save_out("f01_root_drawn_mate1.out", e.finish())

    # F02: Short-clock cliff at Move Overhead + 1 ms (wtime 10 finds d1d8#, wtime 11 plays a1b1 unsearched)
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("setoption name Threads value 64")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1")
    e.send("go wtime 10 btime 1000")
    e.wait_prefix("bestmove ")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1")
    e.send("go wtime 11 btime 1000")
    e.wait_prefix("bestmove ")
    save_out("f02_short_clock_cliff.out", e.finish())

    # F03: OwnBook plays straight into 3-fold repetition draw on move 6
    e = Engine(binary)
    e.send("setoption name Book Variety value 0")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position startpos moves e2e4 e7e5 b1c3 g8f6 c3b1 f6g8 b1c3 g8f6 c3b1 f6g8")
    e.send("go wtime 60000 btime 60000")
    e.wait_prefix("bestmove ")
    save_out("f03_ownbook_repetition.out", e.finish())

    # F04: Null-move pruning in non-pawn zugzwang (depth 10 plays losing e1e5 -503 vs winning e1f1 +157 at depth 11)
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 8/8/p1p5/1p5p/1P5p/8/PPP2K1p/4R1rk w - - 0 1")
    e.send("go depth 10")
    e.wait_prefix("bestmove ")
    e.send("ucinewgame")
    e.send("position fen 8/8/p1p5/1p5p/1P5p/8/PPP2K1p/4R1rk w - - 0 1")
    e.send("go depth 11")
    e.wait_prefix("bestmove ")
    save_out("f04_zugzwang_nullmove.out", e.finish())

    # F05: Missing argument after `wtime` swallows `btime` and drops the 50 ms clock
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position startpos moves e2e4")
    e.send("go wtime btime 50")
    stopped_on_own = e.wait_prefix("bestmove ", timeout=0.5)
    if not stopped_on_own:
        e.send("stop")
        e.wait_prefix("bestmove ", timeout=2.0)
    save_out("f05_go_missing_arg_clock_loss.out", e.finish())

    # F06: Unfinished-iteration abort overwrites MultiPV winning move e1f1 (-309) with losing e1e5 (-503)
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("setoption name MultiPV value 6")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 8/8/p1p5/1p5p/1P5p/8/PPP2K1p/4R1rk w - - 0 1")
    e.send("go infinite")
    e.wait_prefix("info depth 9 multipv 6 ")
    time.sleep(0.003)
    e.send("stop")
    e.wait_prefix("bestmove ")
    save_out("f06_multipv_abort_overwrite.out", e.finish())

    # F07: MultiPV=4 + Hash=512 exceeds 60 ms clock (> 200 ms spent allocating/clearing alt_shared->tt)
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("setoption name Hash value 512")
    e.send("setoption name MultiPV value 4")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position startpos")
    t0 = time.monotonic()
    e.send("go wtime 60 btime 60")
    e.wait_prefix("bestmove ", timeout=10.0)
    elapsed_ms = int(round((time.monotonic() - t0) * 1000.0))
    raw = e.finish() + f"# wall_clock_ms_for_go_wtime_60 = {elapsed_ms}\n"
    save_out("f07_multipv_hash_timeout.out", raw)

    # F08: Threads=16 + go nodes 80 aborts before depth 1 finishes and plays a1b1 instead of d1d8#
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("setoption name Threads value 1")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1")
    e.send("go nodes 80")
    e.wait_prefix("bestmove ")
    e.send("ucinewgame")
    e.send("setoption name Threads value 16")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1")
    e.send("go nodes 80")
    e.wait_prefix("bestmove ")
    save_out("f08_smp_nodes_abort_depth1.out", e.finish())

    # F09: NNUE v3 + UseNNUE=false / DeadMaterial=true disagreement between `eval` and `go`
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("setoption name UseNNUE value false")
    e.send(f"setoption name NNUEArchFile value {v3_net}")
    e.send("setoption name NNUEArch value true")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position startpos")
    e.send("eval")
    e.send("go depth 4")
    e.wait_prefix("bestmove ")
    e.send("setoption name UseNNUE value true")
    e.send("setoption name DeadMaterial value true")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position fen 8/8/8/4k3/8/8/3K1N2/8 w - - 0 1")
    e.send("eval")
    e.send("go depth 4")
    e.wait_prefix("bestmove ")
    save_out("f09_nnue_v3_usennue_mismatch.out", e.finish())

    # F10: Malformed `go nodes -1` and `go mate 0` launch unbounded depth-64 searches
    e = Engine(binary)
    e.send("setoption name OwnBook value false")
    e.send("isready")
    e.wait_prefix("readyok")
    e.send("position startpos")
    e.send("go nodes -1")
    if not e.wait_prefix("bestmove ", timeout=0.4):
        e.send("stop")
        e.wait_prefix("bestmove ", timeout=2.0)
    e.send("ucinewgame")
    e.send("position startpos")
    e.send("go mate 0")
    if not e.wait_prefix("bestmove ", timeout=0.4):
        e.send("stop")
        e.wait_prefix("bestmove ", timeout=2.0)
    save_out("f10_go_malformed_nodes_mate.out", e.finish())


if __name__ == "__main__":
    main()
