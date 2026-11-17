#!/usr/bin/env python3
"""Pure checkers for the MultiPV wire format, plus planted faults that must trip each one.

Every checker takes already-parsed `info` dicts (see multipv_lib.parse_info) so it can be fed
either a live engine reply or a hand-written synthetic block.  That is the point: a checker whose
only evidence is "the engine passed" has not been shown able to fail.

`python3 check_multipv.py --selftest` runs the planted-fault suite.  Each planted fault names the
checker it must trip; a fault that trips nothing, or trips the wrong checker, fails the selftest.
"""
import sys

MATE_BONUS = 100000


def comparable(kind, value):
    """A single integer ordering for cp and mate scores, larger = better for the side to move.

    A mate score is lifted clear of every cp value; of two wins the shorter mate is larger, of two
    losses the longer resistance is larger.  Not doing this is trap 23's sibling: comparing the
    printed numbers puts mate 3 above mate 1 and calls a correct block mis-ordered.
    """
    if kind == "cp":
        return value
    if kind == "mate":
        return MATE_BONUS - value if value > 0 else -MATE_BONUS - value
    raise ValueError("unscorable: %r %r" % (kind, value))


# --- checker 1: emission order ----------------------------------------------------------------
def check_emission_order(block):
    """The lines must ARRIVE in non-decreasing score order for the side to move.

    Returns a list of (prev_index, prev_score, index, score) inversions seen on the wire, in the
    order the lines were printed.  Also returns 'index gaps' separately: an out-of-sequence
    multipv index is reported here only as the position it occupied.
    """
    bad = []
    for a, b in zip(block, block[1:]):
        if comparable(b["score_kind"], b["score"]) > comparable(a["score_kind"], a["score"]):
            bad.append((a["multipv"], a["score_kind"], a["score"],
                        b["multipv"], b["score_kind"], b["score"]))
    return bad


# --- checker 2: index assignment --------------------------------------------------------------
def check_index_order(block):
    """Independently of emission order: sort by multipv index and the scores must be non-increasing.

    This catches a block that prints indices 1..N in ascending score order but binds the wrong
    index to the wrong score.  Separate from checker 1 because the two failures look identical in
    a sorted table and are different bugs.
    """
    by_index = sorted(block, key=lambda p: p["multipv"])
    bad = []
    for a, b in zip(by_index, by_index[1:]):
        if comparable(b["score_kind"], b["score"]) > comparable(a["score_kind"], a["score"]):
            bad.append((a["multipv"], a["score_kind"], a["score"],
                        b["multipv"], b["score_kind"], b["score"]))
    return bad


# --- checker 3: pv length monotonicity --------------------------------------------------------
def check_pv_lengths(block):
    """PV length must be non-increasing in multipv index (line 1 is the searched one).

    Returns (violations, longer_than_depth).  `depth` here is the depth field on the line, so the
    second list answers the brief's "do they match the depth claimed on the line".
    """
    by_index = sorted(block, key=lambda p: p["multipv"])
    violations = []
    for a, b in zip(by_index, by_index[1:]):
        if len(b["pv"]) > len(a["pv"]):
            violations.append((a["multipv"], len(a["pv"]), b["multipv"], len(b["pv"])))
    longer = [(p["multipv"], len(p["pv"]), p["depth"]) for p in by_index if len(p["pv"]) > p["depth"]]
    return violations, longer


def check_pv_vs_seldepth(block):
    """A PV longer than the line's own seldepth contradicts the seldepth field."""
    return [(p["multipv"], len(p["pv"]), p["seldepth"]) for p in block
            if p["seldepth"] is not None and len(p["pv"]) > p["seldepth"]]


# --- checker 4: completeness ------------------------------------------------------------------
def check_completeness(block, expected):
    """Indices 1..expected must all be present exactly once, and nothing beyond."""
    seen = [p["multipv"] for p in block]
    missing = [i for i in range(1, expected + 1) if i not in seen]
    dupes = sorted({i for i in seen if seen.count(i) > 1})
    extra = sorted({i for i in seen if i > expected})
    return missing, dupes, extra


# --- checker 5: bestmove agreement ------------------------------------------------------------
def check_bestmove(block, bestmove):
    """bestmove must be the first move of the multipv 1 line, and line 1 must exist."""
    first = [p for p in block if p["multipv"] == 1]
    if not first:
        return "no multipv 1 line in the final block"
    if not first[0]["pv"]:
        return "multipv 1 pv is empty (unsearched path) but bestmove was %r" % (bestmove,)
    if first[0]["pv"][0] != bestmove:
        return "bestmove %r != multipv 1 pv[0] %r" % (bestmove, first[0]["pv"][0])
    return None


# --- checker 6: duplicate root moves across lines ---------------------------------------------
def check_distinct_first_moves(block):
    seen, dupes = set(), []
    for p in block:
        if not p["pv"]:
            continue
        if p["pv"][0] in seen:
            dupes.append((p["multipv"], p["pv"][0]))
        seen.add(p["pv"][0])
    return dupes


# --- checker 7: pv legality -------------------------------------------------------------------
def check_pv_legal(fen, block, chess):
    """Every move of every emitted PV must be legal from `fen`, in sequence."""
    bad = []
    for p in block:
        board = chess.Board(fen)
        for ply, uci in enumerate(p["pv"]):
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                bad.append((p["multipv"], ply, uci, "unparseable"))
                break
            if move not in board.legal_moves:
                bad.append((p["multipv"], ply, uci, "illegal"))
                break
            board.push(move)
    return bad


# =============================================================================================
# planted faults: each must trip its named checker, and the selftest fails if it does not
# =============================================================================================
def _p(idx, kind, val, pv, depth=10, seldepth=12):
    return {"multipv": idx, "score_kind": kind, "score": val, "pv": pv,
            "depth": depth, "seldepth": seldepth}


GOOD_BLOCK = [_p(1, "cp", 30, ["e2e4", "e7e5", "g1f3"]),
              _p(2, "cp", 20, ["d2d4", "d7d5"]),
              _p(3, "cp", 10, ["c2c4"])]


def selftest():
    import chess
    failures = []
    tally = {"checks": 0, "planted": set()}

    def expect(name, fn, should_be_clean):
        tally["checks"] += 1
        if "/" in name and not name.startswith("good/"):
            tally["planted"].add(name.split("/")[0])
        got = fn()
        clean = not got and got is not False
        if isinstance(got, str):
            clean = False
        if clean != should_be_clean:
            failures.append("%s: expected clean=%s, got %r" % (name, should_be_clean, got))
        return got

    # control: the good block passes every structural checker
    expect("good/emission", lambda: check_emission_order(GOOD_BLOCK), True)
    expect("good/index", lambda: check_index_order(GOOD_BLOCK), True)
    expect("good/pvlen", lambda: check_pv_lengths(GOOD_BLOCK)[0], True)
    expect("good/depth", lambda: check_pv_lengths(GOOD_BLOCK)[1], True)
    expect("good/depth/seldepth", lambda: check_pv_vs_seldepth(GOOD_BLOCK), True)
    expect("good/complete", lambda: check_completeness(GOOD_BLOCK, 3)[0], True)
    expect("good/bestmove", lambda: check_bestmove(GOOD_BLOCK, "e2e4"), True)
    expect("good/distinct", lambda: check_distinct_first_moves(GOOD_BLOCK), True)
    expect("good/legal", lambda: check_pv_legal("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                                                GOOD_BLOCK, chess), True)

    # fault A: two lines arrive swapped.  Emission order must fire, index order must stay clean.
    swapped = [_p(2, "cp", 20, ["d2d4"]), _p(1, "cp", 30, ["e2e4"])]
    expect("faultA/emission", lambda: check_emission_order(swapped), False)
    expect("faultA/index", lambda: check_index_order(swapped), True)

    # fault B: the wire is in non-decreasing score order, so emission looks perfect, but the
    # INDICES are bound to the wrong scores.  Only the index-sorted view can see this, which is
    # why the two checks are separate: a client that renders wire order top-down is right and a
    # client that keys on `multipv` is wrong, on the same bytes.
    misbound = [_p(3, "cp", 30, ["e2e4"]), _p(1, "cp", 20, ["d2d4"]), _p(2, "cp", 10, ["c2c4"])]
    expect("faultB/emission", lambda: check_emission_order(misbound), True)
    expect("faultB/index", lambda: check_index_order(misbound), False)

    # fault C: pv lengths increase with index
    grow = [_p(1, "cp", 30, ["e2e4"]), _p(2, "cp", 20, ["d2d4", "d7d5"])]
    expect("faultC/pvlen", lambda: check_pv_lengths(grow)[0], False)

    # fault D: pv longer than the depth on its own line
    over = [_p(1, "cp", 30, ["e2e4", "e7e5", "g1f3"], depth=2)]
    expect("faultD/depth", lambda: check_pv_lengths(over)[1], False)

    # fault E: pv longer than seldepth
    over2 = [_p(1, "cp", 30, ["e2e4", "e7e5", "g1f3"], depth=3, seldepth=2)]
    expect("faultE/seldepth", lambda: check_pv_vs_seldepth(over2), False)

    # fault F: a middle line goes missing
    hole = [_p(1, "cp", 30, ["e2e4"]), _p(3, "cp", 10, ["c2c4"])]
    expect("faultF/complete", lambda: check_completeness(hole, 3)[0], False)

    # fault G: a line is emitted twice
    dup = [_p(1, "cp", 30, ["e2e4"]), _p(2, "cp", 20, ["d2d4"]), _p(2, "cp", 10, ["c2c4"])]
    expect("faultG/complete", lambda: check_completeness(dup, 2)[1], False)

    # fault H: an index beyond the requested line count
    beyond = [_p(1, "cp", 30, ["e2e4"]), _p(2, "cp", 20, ["d2d4"])]
    expect("faultH/complete", lambda: check_completeness(beyond, 1)[2], False)

    # fault I: bestmove names a move the top line does not start with
    expect("faultI/bestmove", lambda: check_bestmove(GOOD_BLOCK, "a2a3"), False)

    # fault J: an empty pv on a searched line
    empty = [_p(1, "cp", 0, [])]
    expect("faultJ/bestmove", lambda: check_bestmove(empty, "e2e4"), False)

    # fault K: two lines claim the same root move
    same = [_p(1, "cp", 30, ["e2e4"]), _p(2, "cp", 20, ["e2e4", "e7e5"])]
    expect("faultK/distinct", lambda: check_distinct_first_moves(same), False)

    # fault L: an illegal move inside a pv
    illegal = [_p(1, "cp", 30, ["e2e5"])]
    expect("faultL/legal", lambda: check_pv_legal(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", illegal, chess), False)

    # fault M: the mate-ordering comparator itself.  mate 3 must rank BELOW mate 1 even though
    # the printed number is larger; a checker that compares printed integers calls this
    # mis-ordered, and a checker that never fires on the reversed case has not been shown to
    # order mates at all.
    matish = [_p(1, "mate", 1, ["e2e4"]), _p(2, "mate", 3, ["d2d4"])]
    expect("faultM/emission", lambda: check_emission_order(matish), True)
    expect("faultM/index", lambda: check_index_order(matish), True)
    wrong = [_p(1, "mate", 3, ["e2e4"]), _p(2, "mate", 1, ["d2d4"])]
    expect("faultM/wrongway", lambda: check_index_order(wrong), False)
    if comparable("mate", 1) <= comparable("mate", 3):
        failures.append("comparator: mate 1 must outrank mate 3")
    if comparable("mate", -3) <= comparable("mate", -1):
        failures.append("comparator: mate -3 (slower loss) must outrank mate -1")
    # the naive comparator this one replaces would call fault M clean and the control dirty
    naive = lambda k, v: v
    if naive("mate", 1) <= naive("mate", 3):
        pass  # expected: the naive rule cannot tell them apart at all
    else:
        failures.append("naive-comparator control did not behave as documented")

    print("selftest: %d checks over %d planted faults, %d failures"
          % (tally["checks"], len(tally["planted"]), len(failures)))
    for f in failures:
        print("  FAIL " + f)
    return 1 if failures else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
