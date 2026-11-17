"""Selftest: prove this audit's own instruments can FAIL.

Trap 9 and trap 13: a test that cannot fire returns the same answer as one that found
nothing, and zeros are the easiest claims to leave unplanted.  Every checker used to
produce the verdicts is therefore run against a fixture it must reject, beside the real
reply it must accept.

Run: python3 selftest.py
Exit 0 means every check both fired and passed where it should.
"""
from __future__ import annotations

import sys

import chess

from client import (BAIL, BOOK, HANG, NO_MOVE_DRAW, NO_MOVE_MATE, NORMAL, UNSEARCHED,
                    Reply, parse_info)

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        PASS.append(f"{name}: {got}")
    else:
        FAIL.append(f"{name}: got {got!r}, want {want!r}")


def make(infos: list[str], bm: str, strings: list[str] | None = None) -> Reply:
    from client import Client

    parsed = [parse_info(t) for t in infos]
    cat = Client._classify(bm, parsed, strings or [])
    return Reply(category=cat, bestmove=bm, infos=parsed, strings=strings or [],
                 raw=infos + [f"bestmove {bm}"])


# -- 1. classifier -----------------------------------------------------------
NORM = make(["info depth 1 seldepth 3 score cp 70 nodes 41 nps 0 hashfull 0 time 0 pv e1g1"], "e1g1")
check("classify normal", NORM.category, NORMAL)

BOOKR = make([], "e2e4", strings=["book move e2e4"])
check("classify book", BOOKR.category, BOOK)

BAILR = make(["info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv"], "b2a1")
check("classify bail (empty pv, nodes 0)", BAILR.category, BAIL)

MATE0 = make(["info depth 1 seldepth 1 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv"], "0000")
check("classify checkmate", MATE0.category, NO_MOVE_MATE)

CP0 = make(["info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv"], "0000")
check("classify stalemate", CP0.category, NO_MOVE_DRAW)

NOLINES = make([], "a2a3")
check("classify unsearched (no info)", NOLINES.category, UNSEARCHED)


# -- 2. the verifier must FIRE on bad replies --------------------------------
def verify(reply: Reply, board: chess.Board, **kw):
    from client import Client

    cli = Client.__new__(Client)
    cli.violations = []
    cli.notes = []
    cli.assumptions_checked = {}

    def note(aid, ok, detail, fatal=False):
        cli.assumptions_checked[aid] = cli.assumptions_checked.get(aid, 0) + 1
        if not ok:
            cli.violations.append({"assumption": aid, "detail": detail, "fatal": fatal})

    cli.note = note
    return cli.verify(reply, board, **kw), cli


b = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")

illegal = Reply(category=NORMAL, bestmove="e2e5",
                infos=[parse_info("info depth 1 score cp 0 nodes 10 pv e2e5")])
v, cli = verify(illegal, b)
check("verifier rejects illegal move", (v["usable"], v["why"]), (False, "illegal"))
check("  ...and names C5", [x["assumption"] for x in cli.violations], ["C5"])

legal = Reply(category=NORMAL, bestmove="d2d4",
              infos=[parse_info("info depth 1 score cp 20 nodes 10 pv d2d4")])
v, cli = verify(legal, b)
check("verifier accepts legal move", (v["usable"], v["play"]), (True, "d2d4"))
check("  ...with no violation", cli.violations, [])

mismatch = Reply(category=NORMAL, bestmove="d2d4",
                 infos=[parse_info("info depth 1 score cp 20 nodes 10 pv b1c3")])
v, cli = verify(mismatch, b)
check("verifier reports pv/bestmove mismatch",
      [x["assumption"] for x in cli.violations], ["C10"])

null_live = Reply(category=NO_MOVE_DRAW, bestmove="0000",
                  infos=[parse_info("info depth 1 score cp 0 nodes 0 pv")])
v, cli = verify(null_live, b)
check("verifier rejects 0000 on a live board",
      (v["usable"], v["why"]), (False, "null-token-on-live-board"))

mated = chess.Board("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
null_mate = Reply(category=NO_MOVE_MATE, bestmove="0000",
                  infos=[parse_info("info depth 1 score mate 0 nodes 0 pv")])
v, cli = verify(null_mate, mated)
check("verifier ACCEPTS 0000 when mated (not a blanket rule)",
      (v["usable"], v["why"]), (True, "game_over"))

bail_board = chess.Board("8/8/8/6k1/7p/7B/1b6/4K3 b - - 0 1")
v, cli = verify(BAILR, bail_board)
check("verifier refuses bail by default", (v["usable"], v["why"]), (False, "bail"))
v, cli = verify(BAILR, bail_board, allow_bail_play=True)
check("verifier plays bail when allowed", (v["usable"], v["why"]), (True, "bail-played"))

hang = Reply(category=HANG, deadline=2.0)
v, cli = verify(hang, b)
check("verifier treats a hang as fatal", (v["usable"], v["why"]), (False, "hang"))
check("  ...and names C12", [x["assumption"] for x in cli.violations], ["C12"])


# -- 3. checks that need a real depth ladder ---------------------------------
inflated = Reply(
    category=BAIL, bestmove="e1d1",
    infos=[parse_info(f"info depth {d} seldepth {d} score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv")
           for d in range(1, 65)],
)
v, cli = verify(inflated, chess.Board("8/8/8/4k3/8/8/8/4K3 w - - 0 1"), allow_bail_play=True)
check("depth inflation is reported (C7)",
      any(x["assumption"] == "C7" for x in cli.violations), True)

real = Reply(
    category=NORMAL, bestmove="e1g1",
    infos=[parse_info(f"info depth {d} seldepth {d + 2} score cp 50 nodes {100 * d} "
                      f"nps 1000000 hashfull 0 time {d} pv e1g1") for d in range(1, 13)],
)
v, cli = verify(real, b)
check("real depth ladder is NOT reported (C7)",
      [x for x in cli.violations if x["assumption"] == "C7"], [])

backwards = Reply(
    category=NORMAL, bestmove="e1g1",
    infos=[parse_info("info depth 5 score cp 10 nodes 500 pv e1g1"),
           parse_info("info depth 3 score cp 10 nodes 600 pv e1g1")],
)
v, cli = verify(backwards, b)
check("backwards depth is reported (C20)",
      any(x["assumption"] == "C20" for x in cli.violations), True)

nps_bad = Reply(
    category=NORMAL, bestmove="e1g1",
    infos=[parse_info("info depth 1 score cp 10 nodes 0 nps 5000 pv e1g1")],
)
v, cli = verify(nps_bad, b)
check("nps with nodes 0 is reported (C21)",
      any(x["assumption"] == "C21" for x in cli.violations), True)


# -- 4. parse_info ------------------------------------------------------------
li = parse_info("info depth 12 seldepth 24 score cp -62 nodes 113145 nps 1593591 "
                "hashfull 28 time 71 multipv 2 pv e1g1 f8e7")
check("parse depth", li.depth, 12)
check("parse seldepth", li.seldepth, 24)
check("parse score", (li.score_kind, li.score), ("cp", -62))
check("parse nodes", li.nodes, 113145)
check("parse multipv", li.multipv, 2)
check("parse pv", li.pv[:2], ["e1g1", "f8e7"])
check("parse has_pv_token", li.has_pv_token, True)

empty = parse_info("info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv")
check("parse empty pv", (empty.has_pv_token, empty.pv), (True, []))

absent = parse_info("info depth 5 score cp 31 nodes 5000")
check("distinguishes ABSENT pv from empty pv", (absent.has_pv_token, absent.pv), (False, []))

mate = parse_info("info depth 1 score mate 0 nodes 0 pv")
check("parse mate 0", (mate.score_kind, mate.score), ("mate", 0))


# -- report ------------------------------------------------------------------
print(f"{len(PASS)} passed, {len(FAIL)} failed\n")
for p in PASS:
    print("  PASS ", p)
for f in FAIL:
    print("  FAIL ", f)
sys.exit(1 if FAIL else 0)
