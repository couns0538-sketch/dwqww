#!/usr/bin/env python3
"""Job 1, the 50-move question done where the hash table can actually bite.

Part C as written searches the SAME position at clock 0 and then at clock 97.
Both searches start at the ROOT, and the root is a PV node, so the stored
score can never be taken there (search.cpp:1638 needs !pv_node).  Measured
fact: a build with every clock guard removed still returns 100 draws at clock
97, so Part C has no power to detect the fault it targets.

This test moves the high-clock position OFF the root:

  P  = a KQ-vs-K position, white to move, shortest mate exactly 5 plies
       (from partc_find.py).  At clock 97 white cannot finish the mate.
  Q  = a position with BLACK to move, halfmove clock 96, where one legal black
       king move k leads to P with clock 97.  The strong side keeps its queen,
       so nothing resets the clock.

  step 1  `position fen P` (clock 0) + `go depth 14`     -- table gets P's mate
  step 2  `position fen Q` (clock 96) + `go depth 12 searchmoves k`
          The restricted root's only line is k -> P at clock 97, a NON-PV node
          holding a stored mate that no longer fits.  Correct value: a draw.

  fresh arm = step 2 only (no stored mate).  If fresh says draw and warm says
  mate, the stored mate hid the draw.
"""

import json
import sys

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job1")
from run_engine import Engine  # noqa: E402

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
OUT = sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 40


def with_clock(fen, clock):
    p = fen.split()
    p[4] = str(clock)
    return " ".join(p)


def build_parent(pfen):
    """A black-to-move position at clock 96 whose king move leads to pfen@97."""
    p = chess.Board(pfen)
    wk = p.king(chess.WHITE)
    bk = p.king(chess.BLACK)
    # candidate previous black king squares, one king move away from bk
    for delta_h in (-1, 0, 1):
        for delta_v in (-1, 0, 1):
            if delta_h == 0 and delta_v == 0:
                continue
            f = chess.square_file(bk) + delta_h
            r = chess.square_rank(bk) + delta_v
            if not (0 <= f < 8 and 0 <= r < 8):
                continue
            origin = chess.square(f, r)
            q = p.copy()
            q.remove_piece_at(bk)
            q.set_piece_at(origin, chess.Piece(chess.KING, chess.BLACK))
            q.turn = chess.BLACK
            q.halfmove_clock = 96
            q.fullmove_number = 49
            # the reverse move must reproduce pfen exactly, in the same spirit
            k = chess.Move(origin, bk)
            if not q.is_valid():
                continue
            if k not in q.legal_moves:
                continue
            if q.is_check():
                continue                       # black may not be in check at Q
            after = q.copy()
            after.push(k)
            if after.halfmove_clock != 97:
                continue
            if after.board_fen() != p.board_fen():
                continue
            return q.fen(), k.uci()
    return None, None


def score_of(info):
    if not info:
        return None
    t = info.split()
    if "score" not in t:
        return None
    i = t.index("score")
    return t[i + 1] + " " + t[i + 2]


def ask(eng, pos, limit):
    eng.send(pos)
    eng.send("go " + limit)
    lines = eng.until("bestmove", timeout=300)
    info = best = None
    for ln in lines:
        if ln.startswith("info") and " score " in ln:
            info = ln
        if ln.startswith("bestmove"):
            best = ln.split()[1]
    return best, info


def fresh():
    e = Engine()
    e.send("setoption name Threads value 1")
    e.send("setoption name Hash value 16")
    e.send("isready")
    e.until("readyok")
    return e


def main():
    positions = json.load(open(POSFILE))["positions"]
    rows = []
    for p in positions:
        if len(rows) >= N:
            break
        qfen, kmove = build_parent(p["fen"])
        if qfen is None:
            continue
        pos_q = "position fen " + qfen
        root = pos_q + " moves " + kmove

        e1 = fresh()
        f_best, f_info = ask(e1, root, "depth 12 searchmoves " + kmove)
        e1.quit()

        e2 = fresh()
        p_best, p_info = ask(e2, "position fen " + with_clock(p["fen"], 0), "depth 14")
        w_best, w_info = ask(e2, root, "depth 12 searchmoves " + kmove)
        e2.quit()

        rows.append({
            "p_fen": p["fen"], "q_fen": qfen, "k": kmove,
            "poison": {"score": score_of(p_info), "best": p_best},
            "fresh_root": {"score": score_of(f_info), "best": f_best},
            "warm_root": {"score": score_of(w_info), "best": w_best},
        })
        if len(rows) % 10 == 0:
            print(f"{len(rows)} done", flush=True)

    def bucket(s):
        if s is None:
            return "missing"
        if s == "cp 0":
            return "draw"
        if s.startswith("mate "):
            return "mate+" if int(s.split()[1]) > 0 else "mate-"
        return "cp+"

    summary = {}
    for key in ("poison", "fresh_root", "warm_root"):
        b = {}
        for r in rows:
            k = bucket(r[key]["score"])
            b[k] = b.get(k, 0) + 1
        summary[key] = b
    bad = [r for r in rows if bucket(r["warm_root"]["score"]) != "draw"]
    json.dump({"summary": summary, "bad": len(bad), "rows": rows},
              open(OUT, "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("warm arm NOT a draw:", len(bad))
    for r in bad[:5]:
        print("  ", r["p_fen"], "Q", r["q_fen"], "k", r["k"],
              "fresh", r["fresh_root"]["score"], "warm", r["warm_root"]["score"])


if __name__ == "__main__":
    main()
