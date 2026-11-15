"""Part B of the Fable/Opus checks: mates in one (Opus session, 2026-11-15; Fable's job text, part B).

200 positions made by random play (seed 20261117, the playout method of positions.py with 10 to 120 plies), kept
when the side to move has at least one move that mates. The engine searches each with  go depth 4  and must play a
mating move (checked with python-chess). A position is also kept only once.

    python mates.py <engine exe> <results dir>
Exit code: 0 = all 200 found; 1 = a finding; 2 = the check itself failed.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine  # noqa: E402


def mate_positions(seed: int, count: int) -> tuple[list[str], int]:
    rng = random.Random(seed)
    out: list[str] = []
    attempts = 0
    while len(out) < count and attempts < 200000:
        attempts += 1
        b = chess.Board()
        for _ in range(rng.randint(10, 120)):
            moves = list(b.legal_moves)
            if not moves or b.is_game_over():
                break
            b.push(rng.choice(moves))
        if b.is_game_over():
            continue
        fen = b.fen()
        if fen in out:
            continue
        for m in b.legal_moves:
            b.push(m)
            mate = b.is_checkmate()
            b.pop()
            if mate:
                out.append(fen)
                break
    return out, attempts


def main() -> int:
    exe, res = sys.argv[1], sys.argv[2]
    os.makedirs(res, exist_ok=True)
    t0 = time.time()
    target = max(1, round(200 * float(os.environ.get("FORGE_CI_SCALE", "1"))))  # 200; smaller for a quick trial
    fens, attempts = mate_positions(20261117, target)
    with open(os.path.join(res, "positions_mate_in_one.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(fens) + "\n")
    eng = Engine(exe, os.path.join(res, "engine_stderr.txt"))
    if not eng.start_uci({"OwnBook": "false", "Threads": "1", "Hash": "16"}):
        print("the engine did not answer uci/isready")
        return 2
    failures, rows = [], []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send(f"position fen {fen}")
        eng.send("go depth 4")
        ok, lines = eng.wait_for("bestmove", 60.0)
        mv = lines[-1].split()[1] if ok and len(lines[-1].split()) > 1 else None
        b = chess.Board(fen)
        mates = False
        try:
            m = chess.Move.from_uci(mv) if mv else None
            if m is not None and m in b.legal_moves:
                b.push(m)
                mates = b.is_checkmate()
        except ValueError:
            pass
        rows.append({"fen": fen, "bestmove": mv, "mates": mates})
        if not mates:
            failures.append(f"{fen} | engine played {mv}")
    rc, secs = eng.quit()
    summary = [f"Part B: {len(fens)} mate-in-one positions ({attempts} playouts, seed 20261117), go depth 4",
               f"mating move played: {sum(r['mates'] for r in rows)} of {len(rows)}",
               f"engine exit code after quit {rc} ({secs:.1f} s); {(time.time() - t0) / 60:.1f} minutes",
               "", "FINDINGS: " + ("none" if not failures and len(fens) == target else str(len(failures)))]
    summary += ["  " + f for f in failures]
    if len(fens) < target:
        summary.append(f"  only {len(fens)} positions found")
    with open(os.path.join(res, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary) + "\n")
    with open(os.path.join(res, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    with open(os.path.join(res, "transcript.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(eng.transcript) + "\n")
    print("\n".join(summary))
    return 1 if failures or len(fens) < target else 0


if __name__ == "__main__":
    sys.exit(main())
