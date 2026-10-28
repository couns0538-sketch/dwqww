#!/usr/bin/env python3
"""R3-5: Lazy SMP stop / ponder regression over UCI (Threads 2 and 3).

usage: smp_uci_regression.py <engine> [--seed N] [--rounds N] [--threads 2,3] [--log FILE]

For each thread count, with seeded random delays (0 = back to back) and positions:
  - `go infinite`, (isready answered during the search,) `stop` -> exactly one legal bestmove, none before stop;
  - `go ponder movetime 150`, `ponderhit` -> exactly one legal bestmove (and a legal ponder move), none before
    the ponderhit;
  - `go ponder movetime 150`, `stop` -> exactly one legal bestmove;
  - `go nodes N` (N = 1 .. 50000) and `go depth 7` stop by themselves with exactly one legal bestmove;
  - a new `go`, a new `position` or `setoption Threads` while a search runs stop it: one bestmove per `go`;
  - `quit` during a search exits with status 0.
"Exactly one" = after the bestmove an `isready` is answered with no further bestmove, and none arrives in a short
grace window. Legal = in the engine's own `go perft 1` list for that position (no python-chess needed). Every
wait has a timeout (no hang). The engine's ThreadSanitizer reports (CI tsan build) end the engine at once.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_regression import Engine  # noqa: E402

TIMEOUT = 120.0  # seconds for any single answer (generous for sanitizer builds)
GRACE = 0.05     # seconds without a second bestmove after each answer
POSITIONS = [
    "position startpos",
    "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "position fen r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "position startpos moves e2e4 e7e5 g1f3 b8c6 f1b5 a7a6",
]
BESTMOVE = re.compile(r"^bestmove ([a-h][1-8][a-h][1-8][qrbn]?)(?: ponder ([a-h][1-8][a-h][1-8][qrbn]?))?$")
DELAYS = [0.0, 0.0, 0.001, 0.01, 0.05, 0.1, 0.25]


class Run:
    def __init__(self, engine: Path, seed: int):
        self.e = Engine(engine)
        self.rng = random.Random(seed)
        self.legal_cache: dict[str, set[str]] = {}
        self.stats = {"go": 0, "bestmove": 0, "max_stop_latency_s": 0.0, "max_ponderhit_latency_s": 0.0,
                      "isready_during_search": 0}
        self.passed: list[str] = []

    def sync(self, what: str):
        """isready; no bestmove may come before readyok (a second answer to an earlier go)."""
        self.e.send("isready")
        lines = self.e.until(lambda line: line == "readyok", TIMEOUT)
        extra = [line for line in lines if line.startswith("bestmove")]
        assert not extra, f"{what}: unexpected extra {extra}"

    def legal(self, position: str) -> set[str]:
        if position not in self.legal_cache:
            self.e.send(position)
            self.e.send("go perft 1")
            lines = self.e.until(lambda line: line.startswith("nodes "), TIMEOUT)
            self.legal_cache[position] = {line.split(":")[0] for line in lines
                                          if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?: \d+", line)}
        return self.legal_cache[position]

    @staticmethod
    def after(position: str, move: str) -> str:
        return position + (" " if " moves " in position else " moves ") + move

    def answer(self, position: str, what: str, since: float | None = None, latency_key: str | None = None):
        """Exactly one legal bestmove for the running go (checked after it arrives)."""
        lines = self.e.until(lambda line: line.startswith("bestmove "), TIMEOUT)
        if since is not None and latency_key:
            self.stats[latency_key] = max(self.stats[latency_key], time.monotonic() - since)
        match = BESTMOVE.match(lines[-1])
        assert match, f"{what}: malformed or null answer {lines[-1]!r}"
        self.stats["bestmove"] += 1
        self.e.assert_absent(lambda line: line.startswith("bestmove"), GRACE)
        self.sync(what)
        best, ponder = match[1], match[2]
        assert best in self.legal(position), f"{what}: illegal bestmove {best} in {position}"
        if ponder:
            assert ponder in self.legal(self.after(position, best)), f"{what}: illegal ponder move {ponder}"
        return best, ponder

    def go(self, position: str, command: str):
        self.e.send(position)
        self.e.send(command)
        self.stats["go"] += 1

    def wait_without_bestmove(self, seconds: float, what: str):
        if seconds > 0:
            self.e.assert_absent(lambda line: line.startswith("bestmove"), seconds)

    def scenarios(self, threads: int, rounds: int):
        e = self.e
        e.send(f"setoption name Threads value {threads}")
        e.send("setoption name Ponder value false")
        self.sync("setoption")
        for position in POSITIONS:
            self.legal(position)
        tag = f"Threads {threads}"
        for i in range(rounds):
            position = self.rng.choice(POSITIONS)
            delay = self.rng.choice(DELAYS)
            self.go(position, "go infinite")
            self.wait_without_bestmove(delay, f"{tag} infinite")
            if i % 3 == 0:
                e.send("isready")
                e.until(lambda line: line == "readyok", TIMEOUT)
                self.stats["isready_during_search"] += 1
            e.send("stop")
            self.answer(position, f"{tag} go infinite + stop after {delay}s", time.monotonic(), "max_stop_latency_s")
        self.passed.append(f"{tag}: {rounds} x go infinite + stop after random delays: one legal bestmove each, "
                           "none before stop; isready answered during the search")

        e.send("setoption name Ponder value true")
        self.sync("Ponder on")
        for i in range(max(2, rounds // 2)):
            position = self.rng.choice(POSITIONS)
            delay = self.rng.choice(DELAYS)
            self.go(position, "go ponder movetime 150")
            self.wait_without_bestmove(delay, f"{tag} ponder")
            e.send("ponderhit")
            self.answer(position, f"{tag} go ponder + ponderhit after {delay}s", time.monotonic(),
                        "max_ponderhit_latency_s")
            position = self.rng.choice(POSITIONS)
            delay = self.rng.choice(DELAYS)
            self.go(position, "go ponder movetime 150")
            self.wait_without_bestmove(delay, f"{tag} ponder")
            e.send("stop")
            self.answer(position, f"{tag} go ponder + stop after {delay}s", time.monotonic(), "max_stop_latency_s")
        e.send("setoption name Ponder value false")
        self.sync("Ponder off")
        self.passed.append(f"{tag}: go ponder + ponderhit and go ponder + stop: one legal bestmove (legal ponder "
                           "move), none before the ponderhit / stop")

        for nodes in (1, 500, 5000, 50000):
            position = self.rng.choice(POSITIONS)
            self.go(position, f"go nodes {nodes}")
            self.answer(position, f"{tag} go nodes {nodes}")
        position = self.rng.choice(POSITIONS)
        self.go(position, "go depth 7")
        self.answer(position, f"{tag} go depth 7")
        self.passed.append(f"{tag}: go nodes 1/500/5000/50000 and go depth 7 stop by themselves, one legal bestmove")

        # A new go, a new position or a Threads change while a search runs: one bestmove per go.
        position = self.rng.choice(POSITIONS)
        self.go(position, "go infinite")
        self.wait_without_bestmove(0.05, f"{tag} go while searching")
        e.send("go depth 3")
        self.stats["go"] += 1
        first = e.until(lambda line: line.startswith("bestmove "), TIMEOUT)[-1]
        assert BESTMOVE.match(first) and BESTMOVE.match(first)[1] in self.legal(position), first
        self.stats["bestmove"] += 1
        self.answer(position, f"{tag} second go while searching")
        searched = self.rng.choice(POSITIONS)
        self.go(searched, "go infinite")
        self.wait_without_bestmove(0.05, f"{tag} position while searching")
        e.send("position startpos")  # stops the running search; its answer belongs to `searched`
        line = e.until(lambda row: row.startswith("bestmove "), TIMEOUT)[-1]
        match = BESTMOVE.match(line)
        assert match and match[1] in self.legal(searched), (searched, line)
        self.stats["bestmove"] += 1
        self.e.assert_absent(lambda row: row.startswith("bestmove"), GRACE)
        self.sync(f"{tag} position while searching")
        position = self.rng.choice(POSITIONS)
        self.go(position, "go infinite")
        self.wait_without_bestmove(0.05, f"{tag} setoption while searching")
        e.send(f"setoption name Threads value {threads}")
        self.answer(position, f"{tag} setoption Threads while searching")
        self.passed.append(f"{tag}: a new go, position or setoption Threads stops a running search: one bestmove per go")

    def quit_while_searching(self, threads: int):
        e = self.e
        e.send(f"setoption name Threads value {threads}")
        self.sync("setoption")
        e.send(POSITIONS[1])
        e.send("go infinite")  # not counted: the engine may answer it or exit first
        self.wait_without_bestmove(0.1, "quit while searching")
        e.send("quit")
        try:
            e.process.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            e.process.kill()
            raise AssertionError("quit during a search did not end the engine")
        e.reader.join(timeout=5)
        after = []
        while not e.lines.empty():
            line = e.lines.get()
            if line is not None:
                after.append(line)
        assert sum(1 for line in after if line.startswith("bestmove")) <= 1, after
        assert e.process.returncode == 0, f"engine exited {e.process.returncode}"
        self.passed.append(f"Threads {threads}: quit during go infinite exits with status 0")


def main():
    global TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--threads", default="2,3")
    parser.add_argument("--timeout", type=float, default=TIMEOUT, help="seconds allowed for any single answer")
    parser.add_argument("--log", type=Path, help="UCI transcript")
    args = parser.parse_args()
    TIMEOUT = args.timeout
    run = Run(args.engine, args.seed)
    started = time.monotonic()
    try:
        run.e.send("uci")
        run.e.until(lambda line: line == "uciok", TIMEOUT)
        run.e.send("setoption name OwnBook value false")
        run.sync("handshake")
        counts = [int(t) for t in args.threads.split(",")]
        for threads in counts:
            run.scenarios(threads, args.rounds)
        run.quit_while_searching(counts[-1])
    finally:
        if run.e.process.poll() is None:
            run.e.process.kill()
        if args.log:
            args.log.parent.mkdir(parents=True, exist_ok=True)
            args.log.write_text("\n".join(run.e.transcript) + "\n", encoding="utf-8")
    run.stats["seconds"] = round(time.monotonic() - started, 1)
    assert run.stats["go"] == run.stats["bestmove"], run.stats
    print(json.dumps({"seed": args.seed, "passed": run.passed, "stats": run.stats}, indent=2))
    print("PASS smp_uci_regression")


if __name__ == "__main__":
    main()
