#!/usr/bin/env python3
"""Fixed-depth SMP run (O1 TSan acceptance): for each thread count, `go depth D` on N positions
(fresh ucinewgame each), checking that every search returns a legal bestmove without hang or crash.
Prints per-thread-count totals (time, nodes from the last info line).
usage: smp_depth.py <engine> --positions <file> [--count 200] [--threads 2,4,8] [--depth 12]
                    [--reference <lock exe>] [--option Name=Value ...] [--timeout 600] [--progress N]"""
import argparse
import re
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucilib import Engine, EngineError, LegalMoves, read_positions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--positions", required=True)
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--threads", default="2,4,8")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--reference")
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--progress", type=int, default=0, help="print a timestamped line every N positions")
    a = ap.parse_args()
    positions = read_positions(a.positions)
    if len(positions) > a.count:  # spread the picks over the whole file
        positions = [positions[(i * len(positions)) // a.count] for i in range(a.count)]
    legal = LegalMoves(a.reference)
    options = [("Hash", 16), ("OwnBook", "false")] + [tuple(o.split("=", 1)) for o in a.option]
    eng = Engine(a.engine)
    ok = True
    try:
        eng.handshake(options)
        for t in [int(x) for x in a.threads.split(",")]:
            eng.send(f"setoption name Threads value {t}")
            eng.ready(60)
            t0 = time.monotonic()
            nodes = 0
            for i, fen in enumerate(positions):
                eng.send("ucinewgame")
                eng.send(f"position fen {fen}")
                eng.send(f"go depth {a.depth}")
                line, seen = eng.expect(lambda l: l.startswith("bestmove"), a.timeout, f"bestmove (threads {t}, pos {i})")
                best = line.split()[1]
                moves = legal.legal(fen)
                if (best == "0000" and moves) or (best != "0000" and best not in moves):
                    raise EngineError(f"ILLEGAL bestmove {best} at threads {t} in {fen}")
                infos = [l for l in seen if l.startswith("info depth ")]
                m = re.search(r" nodes (\d+)", infos[-1]) if infos else None
                nodes += int(m.group(1)) if m else 0
                if a.progress and (i + 1) % a.progress == 0:
                    print(f"{time.strftime('%H:%M:%S')} threads {t}: {i + 1}/{len(positions)} positions, {nodes} nodes, "
                          f"{time.monotonic() - t0:.1f}s", flush=True)
            print(f"threads {t}: {len(positions)} positions at depth {a.depth}: all bestmoves legal, "
                  f"{nodes} nodes, {time.monotonic() - t0:.1f}s", flush=True)
        code = eng.quit()
        if code != 0:
            raise EngineError(f"exit code {code} after quit")
    except EngineError as exc:
        print("SMP DEPTH FAIL:", exc)
        ok = False
    finally:
        legal.close()
    print("legal moves from:", legal.source)
    print("SMP DEPTH PASS" if ok else "SMP DEPTH FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
