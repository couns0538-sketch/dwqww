"""Probe O: the `ponder` field of the bestmove line, which is what a runner
actually consumes to pre-set its next search.

The option's only observable effect is appending ` ponder <move>`. That makes
the suffix load-bearing, so it gets its own check: is the reported reply LEGAL
in the position after the best move? A suffix that is illegal, or that is
`0000`, silently poisons the next ponder.

Legality is decided by replaying the two moves on the board: the engine's own
`go perft 1` after applying the best move is the reference move set, so no
external chess library is trusted for the verdict.
"""

import argparse
import json
import os
import time

from uci_driver import Engine, bestmoves, parse_bestmove

POSITIONS = [
    ("middlegame_white", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("mid2", "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("mid3", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 8"),
    ("mid4", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"),
    ("endgame_black", "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1"),
    ("mate_in_one_root", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
]


def fresh(exe, ponder=True):
    e = Engine(exe)
    e.uci_handshake()
    for n, v in [("OwnBook", "false"), ("Threads", "1"), ("Hash", "32"),
                 ("Ponder", "true" if ponder else "false")]:
        e.set_option(n, v)
    return e


def legal_moves_after(exe, fen, moves):
    """The engine's own legal move list after applying `moves` to `fen`."""
    e = fresh(exe, ponder=False)
    try:
        if moves:
            e.send(f"position fen {fen} moves {' '.join(moves)}")
        else:
            e.send(f"position fen {fen}")
        mark = e.mark()
        e.send("go perft 1")
        e.wait_for(lambda s: s.startswith("nodes "), 20.0, mark)
        out = []
        for line in e.since(mark):
            t = line.text
            if ":" in t and not t.startswith("info") and not t.startswith("nodes"):
                out.append(t.split(":")[0].strip())
        return out
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="/tmp/forge-build/forge")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "evidence"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    rows = []
    illegal = 0
    missing = 0
    for name, fen in POSITIONS:
        for limit in ("depth 8", "wtime 6000 btime 6000"):
            e = fresh(args.exe, ponder=True)
            try:
                e.send(f"position fen {fen}")
                mark = e.mark()
                e.send(f"go {limit}")
                got = e.wait_for(lambda s: s.startswith("bestmove"), 40.0, mark)
                if got is None:
                    rows.append({"pos": name, "limit": limit, "verdict": "CAPPED"})
                    e.kill()
                    continue
                best, pm = parse_bestmove(got[0].text)
                entry = {"pos": name, "limit": limit, "verdict": "RETURNED",
                         "bestmove_line": got[0].text, "best": best, "ponder": pm}
                if pm is None:
                    missing += 1
                    entry["suffix"] = "ABSENT"
                elif pm == "0000":
                    entry["suffix"] = "ZERO"
                    illegal += 1
                else:
                    replies = legal_moves_after(args.exe, fen, [best])
                    entry["reply_legal"] = pm in replies
                    entry["reply_count"] = len(replies)
                    if pm not in replies:
                        illegal += 1
                        entry["suffix"] = "ILLEGAL"
                    else:
                        entry["suffix"] = "LEGAL"
                rows.append(entry)
            finally:
                e.close()

    res = {"o_ponder_suffix": rows, "illegal_or_zero": illegal,
           "suffix_absent": missing, "total": len(rows)}
    path = os.path.join(out, "probe7_results.json")
    with open(path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
    for r in rows:
        print(r.get("pos"), "|", r.get("limit"), "|", r.get("bestmove_line"),
              "|", r.get("suffix"))
    print(f"illegal_or_zero={illegal} absent={missing} total={len(rows)}")
    print("wrote", path)


if __name__ == "__main__":
    main()
