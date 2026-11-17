#!/usr/bin/env python3
"""Boundary and edge checks that the corpus run cannot see.

  E. BOUNDARY: does `go mate N` ever report a mate LONGER than N moves, and does
     it correctly abstain on a mate that is one move too far (`go mate 4` on a
     proved mate-in-5)?
  F. DETERMINISM: is `go mate N` bit-identical across repeats (score, move,
     depth, nodes)? A non-deterministic mate mode would make every table above
     a sample of one.
  G. CHECKMATED ROOT: what does the mode say when the side to move is already
     mated? `mate 0` is not a distinguishable token from a mate score of zero,
     and a consumer that parses `score mate <n>` will read it as a mate claim.
  H. PV LENGTH vs SCORE, on real positions: for every cell, is the PV length
     consistent with the score? A cp score with a full 2N-1 ply PV is the
     "mate-shaped line, non-mate score" failure the assignment asks about.

Usage: run_edges.py --exe build/forge --out edges.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, pv_replays_to_mate  # noqa: E402


def find_mate_in_k(rng_seed: int, k: int, tries: int = 4000) -> list[str]:
    """Generate positions with proved exact DTM = k moves. Same generator as the
    corpus, so a fixture here is never hand-typed."""
    import random
    rng = random.Random(rng_seed)
    sets = [
        ([chess.QUEEN, chess.ROOK], [chess.ROOK]),
        ([chess.ROOK, chess.ROOK], []),
        ([chess.QUEEN], [chess.ROOK]),
        ([chess.QUEEN], []),
    ]
    found: list[str] = []
    for _ in range(tries):
        if len(found) >= 3:
            break
        white, black = sets[rng.randrange(len(sets))]
        squares = rng.sample(range(64), 2 + len(white) + len(black))
        b = chess.Board(None)
        b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        i = 2
        for color, pieces in ((chess.WHITE, white), (chess.BLACK, black)):
            for pt in pieces:
                b.set_piece_at(squares[i], chess.Piece(pt, color))
                i += 1
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        if not b.is_valid() or b.is_check() or b.legal_moves.count() == 0:
            continue
        o = Oracle(node_budget=800_000)
        try:
            dtm = o.exact_dtm_up_to(b, k)
        except Exception:
            continue
        if dtm is not None and (dtm + 1) // 2 == k:
            found.append(b.fen(en_passant="fen"))
    return found


def part_e(exe: str) -> dict:
    print("E — boundary: `go mate 4` on a proved mate-in-5\n")
    fens = find_mate_in_k(991, 5)
    rows = []
    if not fens:
        print("  no mate-in-5 position generated inside the budget; row omitted")
    for fen in fens:
        board = chess.Board(fen)
        o = Oracle(node_budget=6_000_000)
        dtm = o.exact_dtm_up_to(board, 5)
        for n in (3, 4, 5):
            with Engine(exe, {"OwnBook": "false"}) as eng:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(f"go mate {n}", timeout=600)
            sc = res.last_score
            kind, val = (sc if sc else (None, None))
            rows.append({
                "fen": fen, "true_dtm_plies": dtm, "true_moves": (dtm + 1) // 2 if dtm else None,
                "n": n, "score_kind": kind, "score_value": val,
                "depth": res.last_depth, "nodes": res.last_nodes,
                "pv": res.last_pv, "pv_len": len(res.last_pv),
                "reports_mate": kind == "mate",
                "overclaims": kind == "mate" and val is not None and val > n,
            })
            print(f"  dtm={dtm}plies N={n}: {kind}{val} dep={res.last_depth} "
                  f"nodes={res.last_nodes} pvlen={len(res.last_pv)}", flush=True)

    # G, same run: the checkmated root.
    print("\nG — checkmated root\n")
    mated = "8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1"
    assert chess.Board(mated).is_checkmate(), "fixture is not checkmate"
    for cmd in ("go mate 1", "go mate 4", "go depth 5"):
        with Engine(exe, {"OwnBook": "false"}) as eng:
            eng.newgame()
            eng.setpos(mated)
            res = eng.go(cmd, timeout=60)
        sc = res.last_score
        rows.append({
            "checkmated_root": mated, "cmd": cmd,
            "score_kind": sc[0] if sc else None, "score_value": sc[1] if sc else None,
            "bestmove": res.bestmove, "nodes": res.last_nodes,
            "raw_last_line": res.info_depths[-1] if res.info_depths else None,
        })
        print(f"  {cmd:12s} -> {sc} bestmove={res.bestmove} nodes={res.last_nodes}")

    # E part 2: does any mate claim exceed N?
    print("\nE2 — mate claims longer than N (whole corpus + real sets)")
    return {"rows": rows}


def part_f(exe: str) -> dict:
    print("\nF — determinism: five repeats of the same request\n")
    fens = [
        ("mate-in-4", "8/8/4R3/8/3R4/8/2k3K1/8 w - - 0 1"),
        ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ]
    rows = []
    for name, fen in fens:
        for cmd in ("go mate 2", "go mate 4"):
            sigs = []
            for _ in range(5):
                with Engine(exe, {"OwnBook": "false"}) as eng:
                    eng.newgame()
                    eng.setpos(fen)
                    res = eng.go(cmd, timeout=600)
                    sigs.append((res.bestmove, res.last_score, res.last_depth, res.last_nodes))
            uniq = len(set(sigs))
            rows.append({"position": name, "cmd": cmd, "signatures": [list(s) for s in sigs],
                         "distinct": uniq})
            print(f"  {name:12s} {cmd:12s} distinct signatures {uniq}/5  {sigs[0]}")
    return {"rows": rows}


def part_h() -> dict:
    print("\nH — PV length vs score on the real sets (from compare_real.json)\n")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence",
                        "compare_real.json")
    rows = json.load(open(path))
    tallies = {"mate_mode_cp_fullline": 0, "mate_mode_cp_shortline": 0,
               "mate_mode_mate": 0, "depth_mode_cp_fullline": 0,
               "depth_mode_cp_shortline": 0, "depth_mode_mate": 0}
    for r in rows:
        for key, tag in (("mate", "mate_mode"), ("depth", "depth_mode")):
            s = r[key]
            if s["score_kind"] == "mate":
                tallies[f"{tag}_mate"] += 1
            elif len(s["pv"]) == r["label_depth"]:
                tallies[f"{tag}_cp_fullline"] += 1
            else:
                tallies[f"{tag}_cp_shortline"] += 1
    for k, v in tallies.items():
        print(f"  {k:28s} {v}")
    return tallies


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = {"e": part_e(args.exe), "f": part_f(args.exe), "h": part_h()}
    json.dump(data, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
