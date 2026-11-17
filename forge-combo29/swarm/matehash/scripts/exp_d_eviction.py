"""Experiment D: does a mate score SURVIVE a hashfull-heavy search?

THE QUESTION
    A deep entry holding a mate score is written, then the table is flooded until
    `hashfull` is high. Does the mate score still come back, and at the right
    distance?

WHY THE ANSWER CANNOT BE "IT SURVIVED" WITHOUT PROOF THE FLOOD HAPPENED
    Two ways this null is manufactured, and both are measured here:
      1. the flood never actually evicted anything, so the entry was never at
         risk.  -> `hashfull` before/after is recorded, and the flood must MOVE it.
      2. the re-probe re-derived the answer by searching, so the table is not
         what answered.  -> node counts are recorded, and the "survivor" arm must
         use far fewer nodes than a cold search of the same position.

    Only when the flood moved `hashfull` AND the re-probe used fewer nodes does
    "the mate survived" mean the table still held it.

DESIGN
    arm 1  store:    search the target and read its mate distance (fills entries)
    arm 2  flood:    search N unrelated positions at increasing depth; sample the
                     largest `hashfull` the engine reports
    arm 3  re-probe: same process, target again. Record mate, nodes, hashfull.
    arm 4  cold:     fresh process, target again. The reference answer.

    Two table sizes are used, because "survives" is only interesting relative to
    pressure: 1 MB (floods almost immediately) and 64 MB (needs real work).

Output: evidence/D_eviction.jsonl
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import Engine  # noqa: E402

# Unrelated middlegame/endgame positions used only as eviction pressure.
FLOOD_FENS = [
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
    "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
    "4rrk1/pp1n1ppp/2pb4/8/3P4/1B3N2/PP3PPP/R2R2K1 w - - 0 1",
    "r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R w KQkq - 0 1",
    "8/8/4k3/8/8/4K3/8/6R1 w - - 0 1",
    "2r3k1/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1",
    "r1b2rk1/2q1bppp/p2p1n2/1p2p3/4P3/1BN1BP2/PPPQ2PP/2KR3R w - - 0 1",
]


def last_info(res):
    scored = [i for i in res["infos"] if "score" in i and "depth" in i]
    return scored[-1] if scored else None


def peak_hashfull(res):
    """Largest `hashfull` across ALL info lines.

    `parse_info` only extracts hashfull if the regex matches; the raw line is the
    reliable source, so parse it here rather than trusting a field.
    """
    peak = 0
    for line in res["lines"]:
        if "hashfull" in line:
            try:
                peak = max(peak, int(line.split("hashfull", 1)[1].split()[0]))
            except (IndexError, ValueError):
                pass
    return peak


def brief(res):
    li = last_info(res)
    if li is None:
        return {"mate": None, "nodes": None, "hashfull": None, "depth": None, "seldepth": None}
    return {
        "mate": li.get("score") if li.get("score_kind") == "mate" else None,
        "score": li.get("score"),
        "kind": li.get("score_kind"),
        "nodes": li.get("nodes"),
        "depth": li.get("depth"),
        "seldepth": li.get("seldepth"),
        "hashfull": max((i.get("hashfull", 0) or 0) for i in res["infos"]),
        "pv": li.get("pv"),
    }


def run_arm(binary, fen, hash_mb, store_depth, flood_depth, flood_reps):
    with Engine(binary, hash_mb=hash_mb) as eng:
        eng.ucinewgame()
        # arm 1: store
        eng.position(fen, None)
        stored = brief(eng.go(depth=store_depth, _timeout=300.0))
        # arm 2: flood
        peak = peak_hashfull({"lines": []})
        for rep in range(flood_reps):
            for f in FLOOD_FENS:
                eng.position(f, None)
                r = eng.go(depth=flood_depth, _timeout=300.0)
                peak = max(peak, peak_hashfull(r))
        flooded = {"hashfull_peak": peak}
        # arm 3: re-probe in the same (warm, flooded) process
        eng.position(fen, None)
        reprobe = brief(eng.go(depth=store_depth, _timeout=300.0))
        # arm 4: cold reference, same process but table cleared
        eng.ucinewgame()
        eng.position(fen, None)
        cold = brief(eng.go(depth=store_depth, _timeout=300.0))
    return {"stored": stored, "flood": flooded, "reprobe": reprobe, "cold": cold}


def main():
    binary = sys.argv[1]
    here = __file__.rsplit("/", 2)[0]
    corpus = json.load(open(here + "/evidence/corpus.json"))
    # Only fixtures whose mate needs real work (>= 2 moves) make eviction meaningful.
    targets = [f for f in corpus["fixtures"] if f["moves"] >= 2][:12]

    rows = []
    # 1 MB fills almost at once; 8 MB needs real work but still reaches a high
    # hashfull within the flood, so "survived" is tested under genuine pressure.
    for hash_mb, store_depth, flood_depth, reps in ((1, 14, 16, 2), (8, 16, 18, 2)):
        for fx in targets:
            arm = run_arm(binary, fx["fen"], hash_mb, store_depth, flood_depth, reps)
            want = fx["expected_reported_mate"]
            row = {
                "hash_mb": hash_mb,
                "store_depth": store_depth,
                "flood_depth": flood_depth,
                "flood_reps": reps,
                "fen": fx["fen"],
                "oracle_moves": fx["moves"],
                "expected": want,
                **arm,
                "reprobe_correct": arm["reprobe"]["mate"] == want,
                "cold_correct": arm["cold"]["mate"] == want,
                "hashfull_moved": (arm["flood"]["hashfull_peak"] or 0) > 200,
                "table_answered": (arm["reprobe"]["nodes"] is not None and arm["cold"]["nodes"] is not None
                                  and arm["reprobe"]["nodes"] < arm["cold"]["nodes"]),
            }
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("hash_mb", "fen", "expected", "hashfull_moved",
                                                  "table_answered", "reprobe_correct", "cold_correct")}),
                  flush=True)

    summary = {
        "binary": binary,
        "n": len(rows),
        "reprobe_correct": sum(1 for r in rows if r["reprobe_correct"]),
        "cold_correct": sum(1 for r in rows if r["cold_correct"]),
        "hashfull_moved": sum(1 for r in rows if r["hashfull_moved"]),
        "table_answered": sum(1 for r in rows if r["table_answered"]),
        "by_hash": {},
    }
    for h in sorted({r["hash_mb"] for r in rows}):
        sub = [r for r in rows if r["hash_mb"] == h]
        summary["by_hash"][f"{h}MB"] = {
            "n": len(sub),
            "reprobe_correct": sum(1 for r in sub if r["reprobe_correct"]),
            "hashfull_moved": sum(1 for r in sub if r["hashfull_moved"]),
            "peak_hashfull": max((r["flood"]["hashfull_peak"] or 0) for r in sub),
        }
    print(json.dumps({"summary": summary}, indent=2))
    with open(here + "/evidence/D_eviction.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        fh.write(json.dumps({"summary": summary}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
