"""Cross-check every number FINDINGS.md quotes against the evidence file it cites.

Sec 6 of the audit says the mechanisable relation is "does this NUMBER agree with that
MEASUREMENT", and that a cross-document comparison is worth having.  This script extracts the
figures FINDINGS.md asserts and recomputes each from the JSON evidence, so a figure that
drifted from its measurement fails here.

It deliberately does NOT check prose.  It checks only the numbers that have a machine-readable
source, and it prints the count of checks it ran (trap 16: a check must say how many rows it
examined).

Run: python3 check_numbers.py
"""
from __future__ import annotations

from evio import load_json

import json
import sys

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        PASS.append(f"{name} = {got}")
    else:
        FAIL.append(f"{name}: FINDINGS says {want!r}, evidence says {got!r}")


def main() -> int:
    # -- 1. game arms ------------------------------------------------------
    strict = load_json("evidence/games-100-strict.json")
    naive = load_json("evidence/games-100-naive.json")
    ss, ns = strict["summary"], naive["summary"]

    check("strict games", ss["games"], 100)
    check("naive games", ns["games"], 100)
    check("strict total plies", ss["total_plies"], 13098)
    check("naive total plies", ns["total_plies"], 17588)
    check("strict protocol_failures", ss["protocol_failures"], 59)
    check("naive protocol_failures", ns["protocol_failures"], 0)
    check("strict unfinished", ss["unfinished"], 16)
    check("naive unfinished", ns["unfinished"], 42)
    check("strict BAIL plies", ss["categories"].get("BAIL", 0), 59)
    check("naive BAIL plies", ns["categories"].get("BAIL", 0), 82)
    check("strict BOOK plies", ss["categories"].get("BOOK", 0), 0)
    check("naive BOOK plies", ns["categories"].get("BOOK", 0), 0)

    # "games ended by chess 25 / 58"
    def chess_ended(d):
        return sum(1 for g in d["games"] if not g["protocol_failure"] and not g["unfinished"])

    check("strict games ended by chess", chess_ended(strict), 25)
    check("naive games ended by chess", chess_ended(naive), 58)

    def mates(d):
        return sum(1 for g in d["games"] if g["result"] == "checkmate")

    check("strict checkmates", mates(strict), 21)
    check("naive checkmates", mates(naive), 50)

    # -- 2. all strict failures were threefold -----------------------------
    vf = load_json("evidence/verify-failures.json")
    check("verify: failures examined", len(vf["rows"]), 59)
    check("verify: unjustified", len(vf["unexplained"]), 0)
    check("verify: all rep3", vf["tally"].get("bail:repetition_3fold", 0), 59)
    depths = {r["depth"] for r in vf["rows"]}
    nodes = {r["nodes"] for r in vf["rows"]}
    pvlen = {r["pv_len"] for r in vf["rows"]}
    check("verify: reported depth set", depths, {64})
    check("verify: reported node set", nodes, {0})
    check("verify: pv length set", pvlen, {0})

    # -- 3. bail move disagreement -----------------------------------------
    bc = load_json("evidence/bail-cost.json")
    check("bail-cost: sampled", bc["n"], 40)
    check("bail-cost: agreement", bc["agree"], 4)
    bh = load_json("evidence/bail-harm.json")
    check("bail-harm: roots", bh["n"], 6)
    check("bail-harm: agreement", bh["agree"], 0)

    # -- 4. the naive bails were legitimate claims -------------------------
    # recomputed from the games file directly, not from a summary
    try:
        import chess
    except ImportError:  # pragma: no cover
        chess = None
    if chess is not None:
        tally: dict[str, int] = {}
        bad = 0
        for g in naive["games"]:
            b = chess.Board()
            for mv in g["opening"]:
                b.push_uci(mv)
            for ply in g["plies"]:
                if ply["category"] == "BAIL":
                    claims = [k for k, fn in (("rep3", b.is_repetition(3)),
                                              ("fifty", b.is_fifty_moves()),
                                              ("insuff", b.is_insufficient_material()),
                                              ("stale", b.is_stalemate()),
                                              ("mate", b.is_checkmate())) if fn]
                    if not claims:
                        bad += 1
                    for c in claims:
                        tally[c] = tally.get(c, 0) + 1
                if ply["bestmove"] and ply["bestmove"] != "0000":
                    b.push_uci(ply["bestmove"])
        check("naive bails: rep3 count", tally.get("rep3", 0), 81)
        check("naive bails: fifty count", tally.get("fifty", 0), 1)
        check("naive bails: unjustified", bad, 0)

    # -- 5. pins quoted in the report --------------------------------------
    # the pins were measured by shell, recorded in STATUS.md; assert the text agrees
    with open("STATUS.md") as f:
        st = f.read()
    for pin in ("312,866", "862,329", "3,024,920", "4,865,609"):
        check(f"pin {pin} present in STATUS", pin in st, True)
    with open("FINDINGS.md") as f:
        fd = f.read()
    for pin in ("312,866", "862,329", "3,024,920", "4,865,609"):
        check(f"pin {pin} present in FINDINGS", pin in fd, True)

    print(f"{len(PASS)} numbers agree, {len(FAIL)} disagree "
          f"({len(PASS) + len(FAIL)} checks run)\n")
    for p in PASS:
        print("  OK   ", p)
    for f_ in FAIL:
        print("  FAIL ", f_)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
