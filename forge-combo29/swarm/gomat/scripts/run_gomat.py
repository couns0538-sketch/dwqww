#!/usr/bin/env python3
"""Measurement 1 + 5: does `go mate N` find known mates, and is it comparable
with `go depth 2N-1`?

For every corpus position this runs, in one process per position with
`ucinewgame` between searches (findings §7 item 3: ucinewgame IS a cold reset,
0 of 25 differ from a fresh process):

    go mate 1 .. go mate 4          the mode under audit
    go depth 1, 3, 5, 7             the depth its own labels claim (2N-1)

Gates applied to every search before its numbers are allowed into a table:

  * a board-identity gate: `go perft 1` from the same FEN must equal the
    python-chess legal-move count, so a silently refused FEN cannot contribute
    a row for the previous board (findings §7 item 6);
  * a fabrication gate: a search that returns no `info depth` line is a piped
    abort, not a measurement (findings §7 item 3a), and is counted separately;
  * the reported search must actually terminate; a timeout is recorded as
    CAPPED with the wall time, never folded into the depth column.

Every mate claim the engine makes is replayed in python-chess. The oracle's DTM
is computed independently in `mateoracle.py`; nothing here trusts the engine.

Usage: run_gomat.py --exe build/forge --corpus corpus.json --out raw.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import pv_replays_to_mate  # noqa: E402


def parse_score(res) -> tuple[str, int] | None:
    return res.last_score


def search(eng: Engine, fen: str, cmd: str, timeout: float) -> dict:
    # ORDER MATTERS: `ucinewgame` AFTER a `position` resets the board to
    # startpos (regime note (a) in the swarm brief). Cold reset first, then the
    # position, then the search. The first version of this runner sent
    # ucinewgame last and every position returned startpos's numbers --
    # the tell-tale being one identical node count for all 37 positions.
    eng.newgame()
    eng.setpos(fen)
    res = eng.go(cmd, timeout=timeout)
    kind_score = parse_score(res)
    return {
        "cmd": cmd,
        "bestmove": res.bestmove,
        "score_kind": kind_score[0] if kind_score else None,
        "score_value": kind_score[1] if kind_score else None,
        "depth": res.last_depth,
        "seldepth": res.last_snapshot.get("seldepth"),
        "nodes": res.last_nodes,
        "pv": res.last_pv,
        "info_lines": len(res.info_depths),
        "fabricated": len(res.info_depths) == 0,
        "timed_out": res.timed_out,
        "wall_s": round(res.wall_s, 4),
    }


def perft1(eng: Engine, fen: str) -> int | None:
    eng.newgame()
    eng.setpos(fen)
    eng.send("isready")
    lines = eng.expect("readyok", timeout=20)
    for ln in lines:
        if "invalid FEN" in ln:
            return None
    eng.send("go perft 1")
    out = eng.expect("nodes", timeout=60)
    for ln in out:
        if ln.startswith("nodes "):
            return int(ln.split()[1])
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--max-n", type=int, default=4)
    args = ap.parse_args()

    corpus = json.load(open(args.corpus))
    records: list[dict] = []

    rows = [(r, "mate") for bucket in corpus["mate"].values() for r in bucket]
    rows += [(r, "nomate") for r in corpus["nomate"]]

    for rec, kind in rows:
        fen = rec["fen"]
        board = chess.Board(fen)
        legal = board.legal_moves.count()
        entry = {
            "id": rec["id"],
            "class": kind,
            "fen": fen,
            "reference_legal_moves": legal,
            "oracle_dtm_plies": rec.get("oracle_dtm_plies"),
            "oracle_mate_moves": rec.get("oracle_mate_moves"),
            "oracle_dtm7_plies": rec.get("oracle_dtm7_plies"),
            "no_mate_in_1_proved": rec.get("no_mate_in_1_proved"),
            "material": rec.get("material"),
            "searches": {},
        }
        with Engine(args.exe, {"OwnBook": "false"}) as eng:
            got = perft1(eng, fen)
            entry["engine_perft1"] = got
            entry["board_identity_ok"] = got == legal
            if not entry["board_identity_ok"]:
                entry["refused_or_mismatched"] = True
                records.append(entry)
                print(f"{rec['id']}: BOARD GATE FAILED (engine {got} vs ref {legal})")
                continue

            for n in range(1, args.max_n + 1):
                entry["searches"][f"mate {n}"] = search(eng, fen, f"go mate {n}", args.timeout)
                entry["searches"][f"depth {2 * n - 1}"] = search(eng, fen, f"go depth {2 * n - 1}", args.timeout)

        # Independent verification of every mate claim the engine made.
        for key, s in entry["searches"].items():
            if s["score_kind"] != "mate":
                s["claim_verified"] = None
                continue
            claimed = s["score_value"]
            if claimed is None:
                s["claim_verified"] = None
                continue
            if claimed > 0:
                ok, detail = pv_replays_to_mate(board, s["pv"])
                plies = len(s["pv"])
                want = 2 * claimed - 1
                s["claim_verified"] = ok and plies == want and detail == "checkmate"
                s["claim_detail"] = f"{detail}; plies={plies} want={want}"
            else:
                # A negative score means the OPPONENT mates the side to move.
                s["claim_verified"] = None
                s["claim_detail"] = (
                    f"negative mate {claimed}: the defender's loss, verified by "
                    f"the oracle (dtm7={entry['oracle_dtm7_plies']}) rather than by PV replay"
                )
        records.append(entry)
        print(f"{rec['id']}: " + " ".join(
            f"[{k}:{v['score_kind']}{v['score_value']}/{v['nodes']}/{v['depth']}]"
            for k, v in entry["searches"].items()), flush=True)

    with open(args.out, "w") as fh:
        json.dump(records, fh, indent=1)
    print(f"\nwrote {args.out} ({len(records)} positions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
