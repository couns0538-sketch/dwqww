"""Corpus scan for the abort-revision signature on the `depth` field.

The abort branch (search.cpp ~2440-2451) emits a pv from the *unfinished*
iteration under that iteration's depth, together with `result.score` -- the
score of the last COMPLETED iteration. Reachable only when the unfinished
iteration's pv head differs from the finished pv head, which is why the first
position tried did not fire.

Signature, per aborted run:
    last.depth  == prev.depth + 1
    last.score  == prev.score            (score carried over from D-1)
    last.pv     != prev.pv               (pv taken from unfinished D)

Decisive check against a completed reference run to depth TARGET:
    last.score == ref[TARGET-1].score  and  last.score != ref[TARGET].score
which proves the line labelled `depth TARGET` is scored as TARGET-1.

Controls:
  * A/A pair runs to completion and must agree on (depth, score, pv).
  * every fixture validated with python-chess AND checked for an `invalid FEN`
    refusal on the wire.
"""

import json
import os

import chess

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")

POSITIONS = [
    ("italian-giuoco", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("sicilian-najdorf", "r1bqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 2 6"),
    ("french-advance", "rnbqkbnr/ppp2ppp/4p3/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"),
    ("kings-indian", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 2 7"),
    ("rook-endgame", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("queen-endgame", "8/8/4k3/8/8/3q4/8/3QK3 w - - 0 1"),
    ("midgame-tactics", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"),
    ("sharp-attack", "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"),
    ("endgame-kp", "8/5k2/8/4P3/8/8/8/4K3 w - - 0 1"),
]

STOPS = [0.35, 0.55, 0.75, 0.95, 1.15, 1.40, 1.70, 2.00, 2.40, 2.90]
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": "default 32", "own_book": False,
       "process": "fresh process per search"}


def run(fen, go, stop_after=None):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position(fen)
    lines, bm = e.search(go, stop_after=stop_after, timeout=300)
    e.quit()
    refused = any(l.startswith("info string invalid FEN") for l in lines)
    rows = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            rows.append({"depth": int(f["depth"]), "score": f["score"],
                         "nodes": int(f["nodes"]), "pv": pv, "line": l})
    return {"rows": rows, "bestmove": bm, "refused": refused}


def main():
    report = {"settings": SET, "positions": []}
    hits = []

    for name, fen in POSITIONS:
        board = chess.Board(fen)  # refuses an illegal fixture outright
        entry = {"name": name, "fen": fen, "legal_moves": board.legal_moves.count(),
                 "refusals": [], "signatures": [], "max_completed_depth": None}

        reference = run(fen, "depth 26")
        if reference["refused"]:
            entry["refused"] = True
        ref = {r["depth"]: r for r in reference["rows"]}
        entry["max_completed_depth"] = max(ref) if ref else None
        entry["reference"] = {str(k): {"score": v["score"], "nodes": v["nodes"],
                                       "pv": v["pv"]} for k, v in ref.items()}

        for t in STOPS:
            a = run(fen, "depth 40", stop_after=t)
            if a["refused"]:
                entry["refusals"].append(t)
            rows = a["rows"]
            if len(rows) < 2:
                continue
            last, prev = rows[-1], rows[-2]
            sig = (last["depth"] == prev["depth"] + 1
                   and last["score"] == prev["score"]
                   and last["pv"] != prev["pv"])
            if not sig:
                continue
            d = last["depth"]
            ref_d = ref.get(d)
            ref_dm1 = ref.get(d - 1)
            rec = {
                "stop_after_s": t,
                "depth": d,
                "score_on_line": last["score"],
                "pv_on_line": last["pv"],
                "prev_depth": prev["depth"],
                "prev_score": prev["score"],
                "prev_pv": prev["pv"],
                "wire_line": last["line"],
                "reference_score_at_d": ref_d["score"] if ref_d else None,
                "reference_pv_at_d": ref_d["pv"] if ref_d else None,
                "reference_score_at_d_minus_1": ref_dm1["score"] if ref_dm1 else None,
                "score_matches_ref_d_minus_1": bool(ref_dm1) and last["score"] == ref_dm1["score"],
                "score_differs_from_ref_d": bool(ref_d) and last["score"] != ref_d["score"],
                "pv_differs_from_ref_d": bool(ref_d) and last["pv"] != ref_d["pv"],
            }
            rec["proven"] = rec["score_matches_ref_d_minus_1"] and rec["score_differs_from_ref_d"]
            entry["signatures"].append(rec)
            if rec["proven"]:
                hits.append(dict(rec, position=name, fen=fen))

        # A/A control on this position
        aa1, aa2 = run(fen, "depth 14"), run(fen, "depth 14")
        entry["aa_identical"] = ([(r["depth"], r["score"], r["pv"]) for r in aa1["rows"]]
                                 == [(r["depth"], r["score"], r["pv"]) for r in aa2["rows"]])
        report["positions"].append(entry)
        print("%-20s ref_to_d%-2d AA=%-5s sigs=%d proven=%d" % (
            name, entry["max_completed_depth"], entry["aa_identical"],
            len(entry["signatures"]), sum(1 for s in entry["signatures"] if s["proven"])))

    report["proven_violations"] = hits
    with open(os.path.join(OUT, "depth_abort_corpus.json"), "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)

    print("\n=== PROVEN: a line labelled `depth D` carrying the depth D-1 score ===")
    for h in hits:
        print("%s @%.2fs  d%d score %s (ref d%d = %s, ref d%d = %s)" % (
            h["position"], h["stop_after_s"], h["depth"], h["score_on_line"],
            h["depth"], h["reference_score_at_d"], h["depth"] - 1,
            h["reference_score_at_d_minus_1"]))
        print("   wire:", h["wire_line"][:230])
    print("\ntotal proven:", len(hits))


if __name__ == "__main__":
    main()
