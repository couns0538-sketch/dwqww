#!/usr/bin/env python3
"""UCI concurrency stress for Forge's Lazy SMP (O1).

Each iteration picks a position (pool + random play-out, incl. mate/stalemate roots) and a
scenario around a running search:
  infinite_stop   go infinite, isready during the search, stop
  ponder_hit      go ponder <clock>, isready, ponderhit
  ponder_stop     go ponder <clock>, stop
  go_stop_race    go infinite and stop back to back (no delay)
  stop_threads    go infinite, stop, *immediately* setoption Threads (before reading bestmove)
  position_stop   go infinite, then a new `position` (implicitly stops the search)
  movetime / depth / nodes / clock   bounded searches
plus, between searches: setoption Threads 1-8, ucinewgame, Hash resize, Clear Hash, and (with
--toggle-options) SmpExactNodes / SmpBestThread / LocklessTT on/off.
Checks: every `go` produces exactly one bestmove; bestmove and ponder move are legal ("0000" only
when the root has no legal move); isready is answered during a search; nothing hangs (timeouts);
no crash; clean exit on quit.
usage: uci_stress.py <engine> [--iterations 500] [--seed 1] [--reference <lock exe>]
                     [--positions positions50.fen] [--threads 1,2,3,4,8] [--toggle-options]
                     [--slack 15] [--log stress.log]"""
import argparse
import random
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucilib import Engine, EngineError, LegalMoves, read_positions  # noqa: E402

TERMINAL = ["k7/8/1Q6/8/8/8/8/7K b - - 0 1",      # stalemate
            "k7/1Q6/1K6/8/8/8/8/8 b - - 0 1"]     # checkmate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--iterations", type=int, default=500)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--reference")
    ap.add_argument("--positions")
    ap.add_argument("--threads", default="1,2,3,4,8")
    ap.add_argument("--toggle-options", action="store_true")
    ap.add_argument("--slack", type=float, default=15.0, help="seconds allowed beyond a search's budget")
    ap.add_argument("--log")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    log = open(a.log, "w", encoding="utf-8") if a.log else None
    legal = LegalMoves(a.reference)
    pool = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
    if a.positions:
        pool += read_positions(a.positions)
    threads = [int(t) for t in a.threads.split(",")]
    eng = Engine(a.engine, "engine", log)
    eng.handshake([("Hash", 16), ("OwnBook", "false"), ("Threads", 1)])
    stats = {"go": 0, "bestmove": 0, "isready_during_search": 0, "threads_changes": 0, "max_stop_latency": 0.0,
             "max_isready_latency": 0.0, "illegal": 0}
    scenarios = {}
    pending = {"go": 0}

    def go(cmd, fen, moves):
        eng.send(cmd)
        stats["go"] += 1
        pending["go"] += 1
        return fen, moves

    def collect(fen, moves, timeout, what):
        line, seen = eng.expect(lambda l: l.startswith("bestmove"), timeout, what)
        extra = [l for l in seen if l.startswith("bestmove")]
        if extra:
            raise EngineError(f"more than one bestmove for one go: {extra + [line]}")
        pending["go"] -= 1
        stats["bestmove"] += 1
        parts = line.split()
        best = parts[1] if len(parts) > 1 else ""
        moves_ok = legal.legal(fen, moves)
        if best == "0000":
            if moves_ok:
                stats["illegal"] += 1
                raise EngineError(f"bestmove 0000 with legal moves available: {fen} moves {moves}")
        elif best not in moves_ok:
            stats["illegal"] += 1
            raise EngineError(f"ILLEGAL bestmove {best} in {fen} moves {' '.join(moves)}")
        if "ponder" in parts and best != "0000":
            ponder = parts[parts.index("ponder") + 1]
            if ponder not in legal.legal(fen, list(moves) + [best]):
                stats["illegal"] += 1
                raise EngineError(f"ILLEGAL ponder move {ponder} after {best} in {fen}")
        return best

    def isready_check(timeout=a.slack):
        t = eng.ready(timeout)
        stats["max_isready_latency"] = max(stats["max_isready_latency"], t)
        return t

    t_start = time.monotonic()
    try:
        for it in range(a.iterations):
            # Position: pool entry or a terminal root, plus a short random play-out.
            if rng.random() < 0.03:
                fen, moves = rng.choice(TERMINAL), []
            else:
                fen, moves = rng.choice(pool), []
                for _ in range(rng.randrange(0, 7)):
                    choices = sorted(legal.legal(fen, moves))
                    if not choices:
                        break
                    moves.append(rng.choice(choices))
            pos = f"position fen {fen}" + (" moves " + " ".join(moves) if moves else "")
            # Idle-time option changes.
            r = rng.random()
            if r < 0.25:
                eng.send(f"setoption name Threads value {rng.choice(threads)}")
                stats["threads_changes"] += 1
            elif r < 0.30:
                eng.send("ucinewgame")
            elif r < 0.33:
                eng.send(f"setoption name Hash value {rng.choice([1, 2, 8, 16, 33])}")
            elif r < 0.35:
                eng.send("setoption name Clear Hash")
            if a.toggle_options and rng.random() < 0.2:
                eng.send(f"setoption name {rng.choice(['SmpExactNodes', 'SmpBestThread', 'LocklessTT'])} value "
                         f"{rng.choice(['true', 'false'])}")
            eng.send(pos)
            scenario = rng.choice(["infinite_stop", "infinite_stop", "ponder_hit", "ponder_stop", "go_stop_race",
                                   "stop_threads", "position_stop", "movetime", "depth", "nodes", "clock"])
            scenarios[scenario] = scenarios.get(scenario, 0) + 1
            if scenario in ("infinite_stop", "go_stop_race", "stop_threads", "position_stop"):
                go("go infinite", fen, moves)
                if scenario != "go_stop_race":
                    time.sleep(rng.uniform(0, 0.08))
                    if rng.random() < 0.5:
                        isready_check()
                        stats["isready_during_search"] += 1
                t0 = time.monotonic()
                if scenario == "position_stop":
                    eng.send(pos)  # a new position stops the running search
                else:
                    eng.send("stop")
                if scenario == "stop_threads":
                    eng.send(f"setoption name Threads value {rng.choice(threads)}")
                    stats["threads_changes"] += 1
                collect(fen, moves, a.slack, "bestmove after stop")
                stats["max_stop_latency"] = max(stats["max_stop_latency"], time.monotonic() - t0)
            elif scenario in ("ponder_hit", "ponder_stop"):
                clock = rng.choice([200, 500, 1000, 3000])
                go(f"go ponder wtime {clock} btime {clock} winc 10 binc 10", fen, moves)
                time.sleep(rng.uniform(0, 0.08))
                if rng.random() < 0.5:
                    isready_check()
                    stats["isready_during_search"] += 1
                if scenario == "ponder_hit":
                    eng.send("ponderhit")
                    collect(fen, moves, clock / 1000.0 + a.slack, "bestmove after ponderhit")
                else:
                    t0 = time.monotonic()
                    eng.send("stop")
                    collect(fen, moves, a.slack, "bestmove after stop of ponder")
                    stats["max_stop_latency"] = max(stats["max_stop_latency"], time.monotonic() - t0)
            elif scenario == "movetime":
                ms = rng.randrange(1, 60)
                go(f"go movetime {ms}", fen, moves)
                collect(fen, moves, ms / 1000.0 + a.slack, "bestmove for movetime")
            elif scenario == "depth":
                go(f"go depth {rng.randrange(1, 9)}", fen, moves)
                collect(fen, moves, 120 + a.slack, "bestmove for depth")
            elif scenario == "nodes":
                go(f"go nodes {rng.randrange(1, 30000)}", fen, moves)
                collect(fen, moves, 120 + a.slack, "bestmove for nodes")
            else:
                clock = rng.choice([50, 200, 1000, 3000])
                go(f"go wtime {clock} btime {clock} winc 5 binc 5", fen, moves)
                collect(fen, moves, clock / 1000.0 + a.slack, "bestmove for clock search")
            if rng.random() < 0.3:
                isready_check()
            if pending["go"] != 0:
                raise EngineError(f"bestmove bookkeeping off by {pending['go']}")
            if (it + 1) % 50 == 0:
                print(f"iteration {it + 1}/{a.iterations} ok ({time.monotonic() - t_start:.0f}s)", flush=True)
        code = eng.quit()
        if code != 0:
            raise EngineError(f"engine exit code {code} after quit")
    except EngineError as exc:
        print(f"STRESS FAIL at iteration {it + 1}: {exc}")
        print("stats:", stats, "scenarios:", scenarios)
        sys.exit(1)
    finally:
        legal.close()
    print("legal moves from:", legal.source)
    print("scenarios:", dict(sorted(scenarios.items())))
    print("stats:", stats)
    print(f"STRESS PASS: {a.iterations} iterations, {stats['go']} go / {stats['bestmove']} bestmove, 0 illegal, "
          f"0 hangs, 0 crashes, clean quit ({time.monotonic() - t_start:.0f}s)")


if __name__ == "__main__":
    main()
