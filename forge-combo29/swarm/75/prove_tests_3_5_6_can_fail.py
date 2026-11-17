"""Negative controls for tests 3, 5 and 6.

Each of those tests reports a pass for the real engine. A test that cannot fail
reports a pass for anything, so each is re-run here against a stub engine that
plants the exact defect the test exists to catch.

  test 3  dead material : stub scores KBN vs K as 0 (a drawn verdict for a win)
  test 5  horizon       : stub's score diverges linearly with depth
  test 6  terminal      : stub scores checkmate as cp 0 (collapsing it into a
                          draw, which is the 5.30.0 class of bug)

The stubs are throwaway UCI processes; no measurement of the real engine uses
them.
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

import chess

import harness

HEADER = '''\
#!/usr/bin/env python3
import sys
try:
    import chess
except ImportError:
    chess = None
fen = None
'''

BODY_EVAL = {
    # test 3: claim the KBN win is a draw.
    "kbn_zero": '''
    elif c == "eval":
        b = chess.Board(fen)
        minors = len(b.pieces(2, chess.WHITE)) + len(b.pieces(3, chess.WHITE)) + \\
                 len(b.pieces(2, chess.BLACK)) + len(b.pieces(3, chess.BLACK))
        v = 0 if minors in (2, 3) else 200
        print(f"info string eval hce {v} nnue 0 total {v}", flush=True)
''',
    # test 6: score checkmate as an ordinary 0.
    "mate_as_zero": '''
    elif c == "eval":
        b = chess.Board(fen)
        v = 0 if b.is_checkmate() else 40
        flag = " incheck 1" if b.is_check() else ""
        print(f"info string eval hce {v} nnue 0 total {v}{flag}", flush=True)
''',
    # test 5: the harness verifies the board it holds through `eval`, so even a
    # diverging stub must answer it; the divergence lives in the search score.
    "diverging": '''
    elif c == "eval":
        print("info string eval hce 0 nnue 0 total 0", flush=True)
''',
}

BODY_GO = {
    # test 6: mate reported as cp 0 rather than mate 0.
    "mate_as_zero": '''
    elif c.startswith("go"):
        b = chess.Board(fen)
        if b.is_checkmate():
            print("info depth 6 score cp 0", flush=True)
            print("bestmove 0000", flush=True)
        else:
            print("info depth 6 score cp 40", flush=True)
            print("bestmove a2a3", flush=True)
''',
    # test 5: score diverges with depth instead of settling.
    "diverging": '''
    elif c.startswith("go"):
        parts = c.split()
        depth = int(parts[parts.index("depth") + 1]) if "depth" in parts else 1
        print(f"info depth {depth} score cp {100 * depth}", flush=True)
        print("bestmove a2a3", flush=True)
''',
    "kbn_zero": '''
    elif c.startswith("go"):
        b = chess.Board(fen)
        minors = len(b.pieces(2, chess.WHITE)) + len(b.pieces(3, chess.WHITE)) + \\
                 len(b.pieces(2, chess.BLACK)) + len(b.pieces(3, chess.BLACK))
        v = 0 if minors in (2, 3) else 200
        print(f"info depth 6 score cp {v}", flush=True)
        print("bestmove a2a3", flush=True)
''',
}

COMMON = '''
    elif c == "uci":
        print("id name stub"); print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("position fen "):
        f = c.split()
        fen = " ".join(f[2:8])
        print("info string stub ok", flush=True)
    elif c == "quit":
        break
'''


def make_stub(name: str, eval_body: str, go_body: str) -> str:
    # The dispatch chain must start with a real `if`: every body fragment below
    # begins with `elif`, so the uci case is emitted first.
    script = HEADER + "for line in sys.stdin:\n    c = line.strip()\n"
    script += '''    if c == "uci":
        print("id name stub"); print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("position fen "):
        f = c.split()
        fen = " ".join(f[2:8])
        print("info string stub ok", flush=True)
'''
    script += BODY_EVAL.get(eval_body, "")
    script += BODY_GO.get(go_body, "")
    script += '''    elif c == "quit":
        break
'''
    path = Path(tempfile.mkdtemp()) / f"{name}.py"
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def as_board(fen: str) -> chess.Board:
    return chess.Board(fen)


def check_test3() -> bool:
    """The dead-material test must flag a KBN-vs-K score of 0 as an error."""
    stub = make_stub("kbn_zero", "kbn_zero", "kbn_zero")
    with harness.Forge(path=stub) as f:
        board = as_board("4k3/8/8/8/8/8/8/1BN1K3 w - - 0 1")
        res = f.search(board, depth=6)
        score = res["score"]["value"]
        caught = not (score > 0)
        print(f"  test 3 control: KBN vs K stub scored cp {score} -> "
              f"{'CAUGHT' if caught else 'MISSED'}")
        return caught


def check_test5() -> bool:
    """The horizon test must see a ladder that never settles."""
    stub = make_stub("diverging", "diverging", "diverging")
    with harness.Forge(path=stub) as f:
        board = as_board(chess.STARTING_FEN)
        values = [f.search(board, depth=d)["score"]["value"] for d in (1, 5, 10)]
        # The real test calls a ladder settled when the last two steps differ by
        # <= 30; a diverging ladder must not satisfy that at any step.
        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        caught = any(abs(d) > 30 for d in diffs)
        print(f"  test 5 control: stub ladder {values} diffs {diffs} -> "
              f"{'CAUGHT' if caught else 'MISSED'}")
        return caught


def check_test6() -> bool:
    """The terminal test must reject checkmate reported as cp 0."""
    stub = make_stub("mate_as_zero", "mate_as_zero", "mate_as_zero")
    with harness.Forge(path=stub) as f:
        board = as_board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        res = f.search(board, depth=6)
        caught = res["score"]["type"] != "mate"
        print(f"  test 6 control: checkmate stub reported {res['score']['type']} "
              f"{res['score']['value']} -> {'CAUGHT' if caught else 'MISSED'}")
        return caught


def main() -> int:
    print("negative controls")
    results = [("test 3 dead material", check_test3()),
               ("test 5 horizon", check_test5()),
               ("test 6 terminal", check_test6())]
    print()
    failed = [name for name, ok in results if not ok]
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} detects its planted defect")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
