#!/usr/bin/env python3
"""HardDeadline regression (C3): many short searches where the watchdog races the search thread
(tiny grace), including ponder -> ponderhit, ponder -> stop, movetime, clock and stop races, plus
"starved" searches: the hidden test option DebugSearchDelayMs holds the search thread back so the
watchdog must answer (forced answer required, no second bestmove may follow). The hook exists only in
debug builds and in the test-only forge_debughooks target; an engine without it is refused up front.
Starved searches with `searchmoves` check that the forced answer obeys the list: a subset of the legal
moves that leaves out the engine's first legal move (the unrestricted fallback) must be answered from
the subset, and a list with no legal move must be answered "0000", as the search itself does.
Checks every go gets exactly one bestmove, legal in the position (python-chess when installed,
else a reference engine's `go perft 1`), no hang (timeouts), no crash, clean quit.
usage: hard_deadline_regression.py <engine> [--iterations 300] [--threads 2] [--grace 1] [--seed 3]
                          [--reference <lock exe>] [--slack 30]"""
import argparse
import queue
import random
import subprocess
import sys
import threading
import time

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FENS = [START,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r4q1k/p2bR1rp/2p2Q1N/5p2/5p2/2P5/PP3PPP/R5K1 w - - 0 1",
        "k7/8/1Q6/8/8/8/8/7K b - - 0 1",   # stalemate: bestmove 0000
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1"]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=lambda: [self.q.put(l.rstrip()) for l in self.p.stdout] + [self.q.put(None)],
                         daemon=True).start()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, pred, timeout, what):
        seen, end = [], time.monotonic() + timeout
        while True:
            try:
                line = self.q.get(timeout=max(0.01, end - time.monotonic()))
            except queue.Empty:
                if time.monotonic() >= end:
                    raise SystemExit(f"HANG: no {what} within {timeout}s; last {seen[-5:]}")
                continue
            if line is None:
                raise SystemExit(f"CRASH: engine exited (code {self.p.wait()}) waiting for {what}; last {seen[-5:]}")
            if pred(line):
                return line, seen
            seen.append(line)


def perft_order_factory(exe):
    """Legal moves in the engine's own generation order (`go perft 1` lists Board::legal_moves() in order)."""
    ref = Engine(exe)
    ref.send("uci")
    ref.until(lambda l: l == "uciok", 30, "uciok")
    cache = {}

    def ordered(fen):
        if fen not in cache:
            ref.send(f"position fen {fen}")
            ref.send("go perft 1")
            _, seen = ref.until(lambda l: l.startswith("nodes "), 30, "perft")
            cache[fen] = [l.split(":")[0] for l in seen if ":" in l]
        return cache[fen]
    return ordered


def legal_moves_factory(reference):
    try:
        import chess

        def legal(fen):
            return {m.uci() for m in chess.Board(fen).legal_moves}
        return legal, "python-chess"
    except ImportError:
        if not reference:
            raise SystemExit("install python-chess or pass --reference")
        ordered = perft_order_factory(reference)
        return (lambda fen: set(ordered(fen))), "reference perft"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--iterations", type=int, default=300)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--grace", type=int, default=1)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--reference")
    ap.add_argument("--slack", type=float, default=30.0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    legal, source = legal_moves_factory(a.reference)
    ordered = perft_order_factory(a.reference or a.engine)
    e = Engine(a.engine)
    e.send("uci")
    e.until(lambda l: l == "uciok", 30, "uciok")
    for o in (f"Threads value {a.threads}", "Hash value 16", "OwnBook value false", f"HardDeadline value {a.grace}",
              "Ponder value true"):
        e.send("setoption name " + o)
    e.send("isready")
    e.until(lambda l: l == "readyok", 30, "readyok")
    if a.grace > 0:
        # The starved scenarios need the DebugSearchDelayMs hook (debug builds / forge_debughooks only). The
        # probe searches no legal root move: without the hook the search answers 0000 at once, so only a held
        # search thread lets the watchdog answer (a slow build cannot pass it by winning a race).
        e.send("setoption name DebugSearchDelayMs value 150")
        e.send(f"position fen {START}")
        e.send("go movetime 20 searchmoves a1a1")
        _, seen = e.until(lambda l: l.startswith("bestmove"), a.slack, "bestmove (hook probe)")
        e.send("setoption name DebugSearchDelayMs value 0")
        e.send("isready")
        e.until(lambda l: l == "readyok", a.slack, "readyok")
        if not any(l.startswith("info string HardDeadline") for l in seen):
            raise SystemExit("engine has no DebugSearchDelayMs hook: use a debug build or the forge_debughooks target")
    counts = {}
    forced = 0
    for i in range(a.iterations):
        fen = rng.choice(FENS)
        e.send(f"position fen {fen}")
        kind = rng.choice(["movetime", "clock", "ponderhit", "ponderstop", "stoprace", "starved", "starved_ponder",
                           "starved_searchmoves", "starved_badsearchmoves"])
        allowed = None  # searchmoves scenarios: the moves the answer must come from (empty: must be 0000)
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "movetime":
            e.send(f"go movetime {rng.randrange(1, 40)}")
        elif kind == "clock":
            t = rng.choice([30, 100, 400])
            e.send(f"go wtime {t} btime {t} winc 5 binc 5")
        elif kind in ("ponderhit", "ponderstop"):
            t = rng.choice([30, 100, 400])
            e.send(f"go ponder wtime {t} btime {t} winc 5 binc 5")
            time.sleep(rng.uniform(0, 0.03))
            e.send("ponderhit" if kind == "ponderhit" else "stop")
        elif kind == "stoprace":
            e.send(f"go movetime {rng.randrange(1, 40)}")
            e.send("stop")
        else:  # starved: the search thread starts 150 ms late, the watchdog must answer
            e.send("setoption name DebugSearchDelayMs value 150")
            e.send(f"position fen {fen}")
            if kind == "starved":
                e.send("go movetime 20")
            elif kind == "starved_searchmoves":
                order = ordered(fen)
                if len(order) >= 2:
                    # leave out the engine's first legal move: an unrestricted fallback would play it
                    allowed = set(rng.sample(order[1:], min(len(order) - 1, rng.choice([1, 2, 3]))))
                    e.send("go movetime 20 searchmoves " + " ".join(sorted(allowed)))
                else:
                    e.send("go movetime 20")
            elif kind == "starved_badsearchmoves":
                allowed = set()
                e.send("go movetime 20 searchmoves a1a1")  # parses as no legal move: the search answers 0000
            else:
                e.send("go ponder wtime 100 btime 100 winc 5 binc 5")
                time.sleep(0.005)
                e.send("ponderhit")
        line, seen = e.until(lambda l: l.startswith("bestmove"), a.slack, f"bestmove ({kind})")
        was_forced = any(l.startswith("info string HardDeadline") for l in seen)
        forced += was_forced
        if kind.startswith("starved"):
            if a.grace > 0 and not was_forced:
                raise SystemExit(f"starved search ({kind}) was not answered by the watchdog")
            # setoption joins the late search thread first: a second bestmove would come before readyok.
            e.send("setoption name DebugSearchDelayMs value 0")
        best = line.split()[1]
        moves = legal(fen)
        if allowed is not None:
            want = allowed & moves
            if (best == "0000") != (not want) or (best != "0000" and best not in want):
                raise SystemExit(f"SEARCHMOVES ignored: bestmove {best} ({kind}) in {fen}, allowed {sorted(want)}")
        elif (best == "0000") != (not moves) or (best != "0000" and best not in moves):
            raise SystemExit(f"ILLEGAL bestmove {best} ({kind}) in {fen}")
        # The next readyok must not be preceded by a second bestmove.
        e.send("isready")
        _, seen = e.until(lambda l: l == "readyok", a.slack, "readyok")
        if any(l.startswith("bestmove") for l in seen):
            raise SystemExit(f"DUPLICATE bestmove after {kind} in {fen}: {seen}")
    e.send("quit")
    code = e.p.wait(timeout=60)
    if code != 0:
        raise SystemExit(f"exit code {code}")
    print(f"legal moves from {source}; scenarios {counts}; watchdog answers {forced}")
    print(f"DEADLINE STRESS PASS: {a.iterations} searches, exactly one legal bestmove each, clean quit")


if __name__ == "__main__":
    main()
