"""The trap-21 reader: wait for an `info depth` line, and show where it deadlocks.

This exists to make C6's cost concrete rather than asserted.  It is the reader most
GUIs and match harnesses actually write:

    send go; read lines until one carries `depth`; take the move from that line

On a book move and on `go nodes 0` that reader waits for a line that never comes.  The
control is a reader that waits for `bestmove` instead, on the SAME reply, which is what
this audit's client does.

Every wait is bounded so the script reports a deadlock as a measurement instead of hanging.

Usage: python3 reader_trap21.py ENGINE
"""
from __future__ import annotations

import sys

from engine import Engine, EngineDied, EngineTimeout

PATHS = [
    ("book_both_clocks", "position startpos", "go wtime 10000 btime 10000"),
    ("book_movetime", "position startpos", "go movetime 100"),
    ("go_nodes_0", "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
     "go nodes 0"),
    ("normal_search", "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
     "go depth 12"),
]

WAIT = 3.0


def prepare(eng: Engine, pos: str) -> None:
    eng.send("uci")
    eng.read_until(lambda w: w.text.strip() == "uciok", 20.0)
    eng.send("setoption name OwnBook value true")
    eng.send("isready")
    eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)
    eng.send(pos)
    eng.send("isready")
    eng.read_until(lambda w: w.text.strip() == "readyok", 10.0)


def naive_reader(path: str, pos: str, go: str) -> dict:
    """Wait for `info depth`; then take the move from that same line."""
    eng = Engine(path)
    try:
        prepare(eng, pos)
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("info depth"), WAIT)
        except EngineTimeout:
            drained = [w.text for w in eng.drain_now()]
            return {"reader": "info-depth", "deadlocked": True,
                    "waited": WAIT, "lines": drained,
                    "move": None}
        except EngineDied:
            return {"reader": "info-depth", "deadlocked": True, "died": True, "move": None}
        line = wires[-1].text
        p = line.split()
        move = None
        if "pv" in p:
            after = p[p.index("pv") + 1:]
            move = after[0] if after else None
        return {"reader": "info-depth", "deadlocked": False, "lines": [w.text for w in wires],
                "move": move, "source": "pv[0] of the depth line"}
    finally:
        eng.quit()


def correct_reader(path: str, pos: str, go: str) -> dict:
    """Wait for `bestmove`: the only token the protocol requires."""
    eng = Engine(path)
    try:
        prepare(eng, pos)
        eng.send(go)
        try:
            wires = eng.read_until(lambda w: w.text.startswith("bestmove"), WAIT)
        except (EngineTimeout, EngineDied) as e:
            return {"reader": "bestmove", "deadlocked": True, "error": str(e), "move": None}
        bm = next((w.text for w in wires if w.text.startswith("bestmove")), None)
        return {"reader": "bestmove", "deadlocked": False, "move": bm.replace("bestmove ", ""),
                "n_lines": len(wires)}
    finally:
        eng.quit()


def main() -> int:
    path = sys.argv[1]
    print(f"{'path':20s} {'reader':11s} {'result':34s} {'move'}")
    for name, pos, go in PATHS:
        a = naive_reader(path, pos, go)
        b = correct_reader(path, pos, go)
        ra = f"DEADLOCK ({a['waited']}s, {len(a.get('lines', []))} lines)" if a["deadlocked"] else "answered"
        rb = "DEADLOCK" if b["deadlocked"] else f"answered ({b.get('n_lines')} lines)"
        print(f"{name:20s} {'info-depth':11s} {ra:34s} {a['move']}")
        print(f"{'':20s} {'bestmove':11s} {rb:34s} {b['move']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
