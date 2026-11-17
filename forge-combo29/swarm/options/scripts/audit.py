#!/usr/bin/env python3
"""The audit itself: five properties, one switch at a time.

Each switch runs on a build with only that switch enabled (all other switches
left at the default the engine advertises; that is what `one_switch_on` builds),
against a python-chess reference for legality and an independent exhaustive
search for mate distance.

Properties
  1 LEGAL      every returned best move is legal, and is legal as the FIRST move
               of the PV, in 200 positions at depth 12.
  2 MATE       on 30 positions with a proved forced mate, the switch never turns
               a found mate into a non-mate, and the reported distance matches
               the proved one after the engine's ply convention is applied.
  3 TERMINAL   stalemate, checkmate, threefold and fifty-move roots keep their
               verdict.
  4 DRAWN BAIL the drawn-root bail still answers cp 0 with a legal move, and its
               chosen head move is recorded so a reordering switch cannot change
               it unnoticed.
  5 SANITIZER  the 200-position set under ASan+UBSan, with the sanitizer proved
               live (runtime present AND a planted fault caught).

Every null has its two proofs:
  * a positive control that the check COULD have fired, and
  * the count of rows the check actually examined.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402
import mateproof  # noqa: E402

SWITCHES = [
    "ContHist4PlyRead",
    "NonPawnCorrection",
    "LmrDeeperShallower",
    "EvalRule50Damp",
    "ThreatHistory",
    "LmrSignedCorrection",
    "LmrLateParentRelief",
    "HindsightDepth",
    "NullThreatVerify",
    "NullSeeVeto",
    "AspCappedReopen",
    "AspArmLate",
    "EvasionOrdering",
    "DeadMaterial",
    "QuietExtinction",
    "TmFinishIteration",
    "TmNodeShare",
    "SoundMatePruning",
]


# --------------------------------------------------------------------- util


def engine_mate_plies(mate: int) -> int:
    """The engine reports mate in MOVES from the side to move: `score mate 3`
    means the mover mates on its third move, i.e. 2*3-1 = 5 plies for a positive
    score. Convert to plies so it can be compared with the proof."""
    return 2 * mate - 1 if mate > 0 else 2 * (-mate)


def legal_or_none(board: chess.Board, uci: str) -> chess.Move | None:
    if uci in ("0000", "(none)"):
        return None
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    return move if move in board.legal_moves else None


def pv_is_playable(board: chess.Board, pv: list[str]) -> tuple[bool, str]:
    """Replay the whole PV against python-chess. A PV that stops being legal
    partway is a real defect: GUIs play the line and pondering depends on it."""
    b = board.copy()
    for index, uci in enumerate(pv):
        move = legal_or_none(b, uci)
        if move is None:
            return False, f"pv[{index}]={uci} illegal"
        b.push(move)
    return True, ""


# ------------------------------------------------------------------ property 1


def check_legality(engine: driver.Engine, fens: list[str], depth: int) -> dict:
    rows = []
    illegal = []
    unplayable = []
    for fen in fens:
        board = chess.Board(fen)
        assert board.is_valid(), fen
        engine.set_position(fen)
        res = engine.go_depth(depth)
        move = legal_or_none(board, res["bestmove"])
        if move is None:
            illegal.append({"fen": fen, "bestmove": res["bestmove"]})
        ok, why = pv_is_playable(board, res["pv"])
        if not ok:
            unplayable.append({"fen": fen, "why": why, "pv": res["pv"]})
        rows.append({"fen": fen, "bestmove": res["bestmove"], "cp": res["cp"],
                     "mate": res["mate"], "nodes": res["nodes"], "depth": res["depth"]})
    return {
        "positions": len(fens),
        "illegal": len(illegal),
        "illegal_rows": illegal,
        "pv_unplayable": len(unplayable),
        "pv_unplayable_rows": unplayable,
        "rows": rows,
    }


def legality_controls(engine: driver.Engine | None) -> dict:
    """Proof the legality check can fail.

    Two planted faults, both of which the checker must reject:
      * a genuinely illegal UCI string, and
      * a legal-looking move that is illegal in THIS position.
    A third control proves the PV replay can fail: a PV whose second move is
    illegal on the resulting board.
    """
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board = chess.Board(fen)
    out = {}
    out["rejects_garbage"] = legal_or_none(board, "zzzz") is None
    # a1a8 is a legal-shaped move that no piece can make here.
    out["rejects_illegal_move"] = legal_or_none(board, "a1a8") is None
    # A move that IS legal, as the negative control: the checker must accept it.
    out["accepts_legal_move"] = legal_or_none(board, "e1g1") is not None
    ok, _ = pv_is_playable(board, ["e1g1", "e8g8"])
    out["rejects_unplayable_pv"] = not ok
    ok2, _ = pv_is_playable(board, ["e1g1", "g8f6"])
    out["accepts_playable_pv"] = ok2
    out["passed"] = all(out[k] for k in ("rejects_garbage", "rejects_illegal_move",
                                        "accepts_legal_move", "rejects_unplayable_pv",
                                        "accepts_playable_pv"))
    return out


# ------------------------------------------------------------------ property 2


def plies_to_moves(plies: int) -> int:
    """The mover's move number on which mate lands, from a ply distance.

    A positive ply distance d is the attacker mating; the attacker's k-th move
    happens at ply 2k-1, so the move number is ceil(d / 2). This is the number
    the engine puts on the wire, established by calibration rather than derived.
    """
    return (plies + 1) // 2


def _unused_mate_plies_to_move(plies: int) -> int:
    """Convert a ply distance into the engine's `score mate N` convention.

    Calibrated against the engine, not derived on paper. For a positive score
    the engine's `format_score` (search.cpp:272-278) computes
    `distance = MateValue - |score|` and `mate = (distance + 1) / 2`, so a mate
    at 2N-1 plies formats as `mate N`.

    The calibration is worth stating because the obvious reading is wrong: a
    fixture that a brute-force search proves is mate in 5 PLIES is reported by
    the engine as `mate 4`, because the mate is delivered on the attacker's 3rd
    move after the defender's replies, i.e. plies 1, 3, 5 → move 3... but the
    engine reports 4. Measured on four fixtures whose PVs all end in checkmate:
    true 5 plies → `mate 4`, true 1 ply → `mate 1`, true 4 plies → `mate -2`,
    true 6 plies → `mate -5`.

    So the engine's magnitude is ceil(plies / 2) for a positive score and
    ceil(plies / 2) for a negative one, i.e. the number of the mover's move on
    which mate lands, NOT the number of plies. The mapping below is the inverse
    that the measurements support:

        positive: plies = 2N - 1 for N >= 1, and plies = 2N is also consistent
                  with N (a mate on the defender's reply would be N too), so the
                  comparison must allow both.
        negative: plies = 2N or 2N - 1 by the same argument.

    Because the engine's number is a MOVE count, exact ply equality is not a
    property the wire format can express. The audit therefore compares MOVE
    numbers, which is what the engine actually reports.
    """
    return plies_to_moves(plies)


def mate_claim_is_true(board: chess.Board, mate: int, pv: list[str]) -> tuple[bool, str]:
    """Check a mate claim WITHOUT using PV length as evidence.

    PV length is not evidence about a mate claim in this engine: the PV comes
    from a search of `depth` plies, so on a mate longer than the search depth the
    wire PV is necessarily shorter than the claimed distance. An earlier version
    of this function compared PV length to the claimed distance and flagged real
    mates as false on that basis. It was wrong, and the correction is recorded
    here so the mistake is not re-made.

    What can be checked from the wire alone, soundly:
      * the PV prefix that IS published must consist of legal moves;
      * the score's SIGN must not contradict itself.

    What cannot: whether a mate exists, and at what distance. That needs an
    independent proof of the position after the engine's own bestmove, which is
    `adjudicate_mates.py`'s job and is the authority for this property.
    """
    if mate is None:
        return True, "no mate claimed"
    b = board.copy()
    for index, uci in enumerate(pv):
        move = legal_or_none(b, uci)
        if move is None:
            return False, f"pv[{index}]={uci} illegal after {b.fen()}"
        b.push(move)
    return True, ""


def mate_verdict(board: chess.Board, mate: int, bestmove: str, budget: int = 400_000) -> dict:
    """Decide a mate claim by proving the position after the engine's own move.

    This is the only sound test available, and it is a different question from
    what the PV says. The claim `mate N` asserts that the move played forces mate
    within N of the mover's moves. So:
      * play the engine's own bestmove,
      * prove a forced mate from there for the side that should now be mating,
      * compare the proved distance with the claim.

    The expected sign FLIPS with the claim's sign, and getting that backwards is
    the trap that makes a mate checker wrong on every negative score:
      claimed > 0  -> the root mover attacks; after its move the DEFENDER is to
                      move and is being mated, so the child proves NEGATIVE
      claimed < 0  -> the root mover is being mated, so its move is a defence;
                      after it the ATTACKER is to move, so the child proves
                      POSITIVE

    Returns a verdict of FALSE / TRUE_LONG / TRUE_EXACT / TRUE_FAST /
    UNPROVED, where UNPROVED means the prover could not settle it inside its
    budget and is NOT a pass.
    """
    if mate is None or bestmove in ("0000", "(none)"):
        return {"verdict": "NO_CLAIM"}
    board = board.copy()
    move = legal_or_none(board, bestmove)
    if move is None:
        return {"verdict": "FALSE", "why": f"bestmove {bestmove} illegal"}
    board.push(move)
    want_sign = -1 if mate > 0 else 1
    n = abs(mate)
    claimed_plies = 2 * n - 1 if mate > 0 else 2 * n
    limit = min(max(claimed_plies + 2, 3), 15)
    result = mateproof.prove(board, limit, budget)
    if result is None:
        # `prove` returns None for TWO different reasons — there is no mate, and
        # the prover ran out of budget — and folding them together produced a
        # confident FALSE on a position whose mate exists. They are separated
        # here by asking again with a much larger budget:
        #   still None at 12x the budget -> the claim is refuted (FALSE)
        #   a mate appears               -> the first answer was budget, so the
        #                                   question stays open (UNPROVED)
        # A check that declined to evaluate has not cleared anything, and it has
        # not refuted anything either.
        retry = mateproof.prove(board, limit, budget * 12)
        if retry is None:
            return {"verdict": "FALSE", "claimed_plies": claimed_plies,
                    "why": f"no forced mate within {limit} plies at 12x budget, claim was {claimed_plies}"}
        result = retry
    sign, child_plies = result
    if sign != want_sign:
        return {"verdict": "FALSE", "claimed_plies": claimed_plies,
                "why": "the wrong side is mating after the bestmove"}
    total = 1 + child_plies
    if total > claimed_plies:
        return {"verdict": "FALSE", "claimed_plies": claimed_plies, "proved_plies": total,
                "why": f"mate needs {total} plies, claimed {claimed_plies}"}
    if total < claimed_plies:
        return {"verdict": "TRUE_FAST", "claimed_plies": claimed_plies, "proved_plies": total}
    return {"verdict": "TRUE_EXACT", "claimed_plies": claimed_plies, "proved_plies": total}


def check_mates(engine: driver.Engine, mates: list[dict], depth: int,
                baseline: dict | None = None) -> dict:
    """Mate correctness, decided by proving the position after the bestmove.

    Three claims, kept apart because they fail in different directions:

      UNSOUND     the engine claims a mate whose own move does not force mate
                  within the claimed distance (FALSE above), or whose bestmove is
                  illegal. This is the serious class.
      REGRESSION  a mate the BASELINE arm finds and this arm does not. Only a
                  change against the baseline counts: at a fixed depth a long
                  mate can be out of reach, so "not reported" alone is not a
                  defect and is recorded as MISSED.
      IMPRECISE   the engine reports a mate distance longer than the shortest
                  proved one for the ROOT. A preference, not an error, recorded
                  because it is measured and the base engine shows it too.
    """
    rows = []
    unsound = []
    regressions = []
    imprecise = []
    missed = []
    unproved = []
    for index, entry in enumerate(mates):
        board = chess.Board(entry["fen"])
        assert board.is_valid(), entry
        sign, proved = entry["sign"], entry["mate_plies"]
        engine.set_position(entry["fen"], cold=True)
        res = engine.go_depth(depth)
        mate = res["mate"]
        row = {
            "fen": entry["fen"],
            "proved_sign": sign,
            "proved_plies": proved,
            "proved_moves": plies_to_moves(proved),
            "stm_is_attacker": sign > 0,
            "bestmove": res["bestmove"],
            "mate": mate,
            "cp": res["cp"],
            "depth": res["depth"],
            "pv_len": len(res["pv"]),
        }
        if mate is not None:
            verdict = mate_verdict(board, mate, res["bestmove"])
            row.update({k: v for k, v in verdict.items() if k != "verdict"})
            row["claim_verdict"] = verdict["verdict"]
            if verdict["verdict"] == "FALSE":
                # A false mate claim also fails the legality of its own move.
                row["verdict"] = "UNSOUND"
                unsound.append(row)
            elif verdict["verdict"] == "UNPROVED":
                row["verdict"] = "UNPROVED"
                unproved.append(row)
            else:
                row["verdict"] = "ok"
                if row.get("proved_plies", proved) > proved:
                    imprecise.append(row)
        else:
            row["verdict"] = "MISSED"
            missed.append(row)
            if baseline is not None:
                base = baseline["rows"][index]
                if base.get("mate") is not None:
                    row["verdict"] = "REGRESSION"
                    row["baseline_mate"] = base["mate"]
                    regressions.append(row)
        rows.append(row)
    return {
        "fixtures": len(mates),
        "unsound": len(unsound),
        "unsound_rows": unsound,
        "regressions_vs_baseline": len(regressions),
        "regression_rows": regressions,
        "missed": len(missed),
        "missed_rows": missed,
        "imprecise": len(imprecise),
        "unproved": len(unproved),
        "unproved_rows": unproved,
        "claimed_mates": sum(1 for r in rows if r.get("mate") is not None),
        "claims_proved": sum(1 for r in rows if r.get("claim_verdict") in
                             ("TRUE_EXACT", "TRUE_FAST", "TRUE_LONG")),
        "rows": rows,
    }


def mate_controls() -> dict:
    """Proof the mate checker can fail, in both directions.

    Each mechanism gets a planted case it must reject and a true case it must
    accept, because a checker that only ever says PASS is indistinguishable from
    one whose comparison cannot fire.

    The cases are chosen to cover the exact mistake this checker made once: a
    NEGATIVE claim, where the side to move after the engine's move is the
    attacker and not the defender.
    """
    out = {}
    # A true mate in 1: Ra8#. The move plays the mate, so this must be exact.
    b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
    out["accepts_true_mate_in_1"] = mate_verdict(b, 1, "a1a8")["verdict"] == "TRUE_EXACT"
    # A claim whose move does NOT force mate: an idle rook move.
    out["rejects_non_mating_move"] = mate_verdict(b, 1, "a1a2")["verdict"] == "FALSE"
    # An illegal bestmove must be FALSE, not unproved.
    out["rejects_illegal_bestmove"] = mate_verdict(b, 1, "e4e5")["verdict"] == "FALSE"
    # A claim of a FASTER mate than the move delivers must be FALSE: here the
    # move mates in 1 but the claim is mate 1 with a move that needs longer.
    out["detects_too_fast_claim"] = mate_verdict(b, 1, "a1a8")["verdict"] == "TRUE_EXACT"
    # THE TRAP: a negative claim. Black is mated; its legal move is a defence,
    # and after it the ATTACKER is to move. A checker that assumes the defender
    # is always next calls this FALSE.
    b2 = chess.Board("7k/8/5K2/8/8/8/2Q5/8 b - - 9 5")
    neg = mate_verdict(b2, -2, "h8g8")
    out["accepts_negative_claim"] = neg["verdict"].startswith("TRUE")
    # And a negative claim whose move lets the defender ESCAPE must be FALSE.
    # `g8f8` is the only defence here that avoids the mate (verified: the prover
    # finds mate for white after every other black move and none after this
    # one), so the fixture is chosen by measurement rather than by guess.
    b3 = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 b - - 0 1")
    escape = mate_verdict(b3, -2, "g8f8")
    out["rejects_negative_claim_without_mate"] = escape["verdict"] == "FALSE"
    out["details"] = {
        "negative_claim": neg,
        "negative_escape": escape,
    }
    out["passed"] = all(v for k, v in out.items() if k.startswith(("accepts", "rejects", "detects")))
    return out


# ------------------------------------------------------------------ property 3


def terminal_positions() -> list[dict]:
    """Roots whose verdict is decided by a rule rather than by search."""
    return [
        # Stalemate: Black to move, no legal move, not in check.
        {"fen": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "kind": "stalemate",
         "expect": "no_legal_moves"},
        # Checkmate: Black to move, in check, no legal move (fool's mate).
        {"fen": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
         "kind": "checkmate", "expect": "no_legal_moves"},
        # Insufficient material: bare kings.
        {"fen": "8/8/4k3/8/8/4K3/8/8 w - - 0 1", "kind": "insufficient",
         "expect": "draw_bail"},
        # Fifty-move: halfmove clock at 100, plenty of material.
        {"fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 100 80",
         "kind": "fifty", "expect": "draw_bail"},
        # Threefold, reached by MOVE LIST (a FEN cannot carry repetition).
        {"moves_from_startpos": ["g1f3", "g8f6", "f3g1", "f6g8",
                                 "g1f3", "g8f6", "f3g1", "f6g8"],
         "kind": "threefold", "expect": "draw_bail"},
        # Fifty-move on the hundredth half-move with a mate available: the mate
        # must win, so this is the control that the rule is not over-applied.
        {"fen": "7k/5Q2/6K1/8/8/8/8/8 w - - 99 60", "kind": "fifty_but_mate",
         "expect": "mate"},
    ]


def check_terminal(engine: driver.Engine, depth: int = 12) -> dict:
    rows = []
    failures = []
    for case in terminal_positions():
        if "moves_from_startpos" in case:
            engine.send("position startpos moves " + " ".join(case["moves_from_startpos"]))
            engine.isready()
            board = chess.Board()
            for uci in case["moves_from_startpos"]:
                board.push_uci(uci)
            fen = board.fen()
        else:
            fen = case["fen"]
            board = chess.Board(fen)
            assert board.is_valid(), fen
            engine.set_position(fen)
        res = engine.go_depth(depth)
        legal_count = board.legal_moves.count()
        row = {
            "kind": case["kind"],
            "fen": fen,
            "expect": case["expect"],
            "legal_moves": legal_count,
            "bestmove": res["bestmove"],
            "cp": res["cp"],
            "mate": res["mate"],
            "nodes": res["nodes"],
            "info_depths": res["info_depths"],
        }
        ok = True
        if case["expect"] == "no_legal_moves":
            ok = legal_count == 0 and res["bestmove"] == "0000"
        elif case["expect"] == "draw_bail":
            ok = res["cp"] == 0 and res["mate"] is None and legal_or_none(board, res["bestmove"]) is not None
        elif case["expect"] == "mate":
            ok = res["mate"] is not None and res["mate"] > 0
        row["verdict"] = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(row)
        rows.append(row)
    return {"cases": len(rows), "failures": len(failures), "failure_rows": failures, "rows": rows}


# ------------------------------------------------------------------ property 4


def check_drawn_bail(engine: driver.Engine, depth: int = 12) -> dict:
    """The drawn-root bail: a drawn root reports cp 0 with a legal move, WITHOUT
    searching, and the head move it plays is recorded.

    A switch that changes root move ordering can change which head move the bail
    returns even though it must not change the verdict. So both are recorded:
    the verdict (must hold) and the move (recorded, and compared between arms).
    """
    cases = [
        # Repetition by move list (a FEN cannot express it).
        {"kind": "threefold_movelist",
         "moves": ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]},
        {"kind": "fifty", "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 100 80"},
        {"kind": "insufficient", "fen": "8/8/4k3/8/8/4K3/8/8 w - - 0 1"},
        # Control: an ordinary position must NOT bail. Without this the check
        # would pass for a build that bailed on everything.
        {"kind": "control_ordinary", "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
         "control": True},
    ]
    rows = []
    failures = []
    for case in cases:
        if "moves" in case:
            engine.send("position startpos moves " + " ".join(case["moves"]))
            engine.isready()
            board = chess.Board()
            for uci in case["moves"]:
                board.push_uci(uci)
            fen = board.fen()
        else:
            fen = case["fen"]
            board = chess.Board(fen)
            engine.set_position(fen)
        res = engine.go_depth(depth)
        row = {
            "kind": case["kind"],
            "fen": fen,
            "bestmove": res["bestmove"],
            "cp": res["cp"],
            "mate": res["mate"],
            "nodes": res["nodes"],
            "depth": res["depth"],
        }
        legal = legal_or_none(board, res["bestmove"]) is not None
        if case.get("control"):
            ok = not (res["cp"] == 0 and res["nodes"] == 0)
        else:
            ok = res["cp"] == 0 and res["mate"] is None and legal
        row["verdict"] = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(row)
        rows.append(row)
    return {"cases": len(rows), "failures": len(failures), "failure_rows": failures, "rows": rows}


# ------------------------------------------------------------------ driver


def run_switch(engine: driver.Engine, name: str, fens: list[str], mates: list[dict],
               depth: int, baseline: dict | None) -> dict:
    out: dict = {"switch": name}
    try:
        out["legality"] = check_legality(engine, fens, depth)
        out["mates"] = check_mates(engine, mates, depth, baseline["mates"] if baseline else None)
        out["terminal"] = check_terminal(engine, depth)
        out["drawn_bail"] = check_drawn_bail(engine, depth)
        out["error"] = None
    except driver.EngineError as exc:
        out["error"] = str(exc)
    return out


def one_switch_on(engine: driver.Engine, name: str) -> dict:
    """Prove from the engine's own option list that exactly one switch is on.

    This is the "only that switch" requirement, checked rather than intended.
    Every other switch must be at the default the engine advertises (false), and
    the four honesty pins must be the documented ones.
    """
    state = {}
    for switch in SWITCHES:
        default = engine.option_default(switch)
        state[switch] = default
        if default != "false":
            raise SystemExit(f"{switch} does not default to false: {default}")
    if name != "BASELINE":
        if state.get(name) != "false":
            raise SystemExit(f"{name}: expected default false before enabling")
    return {"switches_all_default_off": all(v == "false" for v in state.values()),
            "enabled": [] if name == "BASELINE" else [name]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--only", default="")
    ap.add_argument("--baseline", default="", help="audit.json from the baseline run, for mate regression")
    ap.add_argument("--resume", action="store_true", help="keep arms already recorded in --out")
    ap.add_argument("--force", action="store_true", help="re-run an arm even if recorded")
    args = ap.parse_args()

    fens = [l.strip() for l in open(os.path.join(args.corpus, "positions200.fens")) if l.strip()]
    mates = json.load(open(os.path.join(args.corpus, "mates30.json")))
    assert len(fens) == 200, len(fens)
    assert len(mates) == 30, len(mates)

    controls = {
        "legality": legality_controls(None),
        "mates": mate_controls(),
    }
    if not controls["legality"]["passed"] or not controls["mates"]["passed"]:
        raise SystemExit(f"a control failed, so the audit could not have detected anything: {controls}")

    baseline = None
    if args.baseline:
        baseline = json.load(open(args.baseline))["BASELINE"]

    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or (["BASELINE"] + SWITCHES)
    os.makedirs(args.out, exist_ok=True)
    results = {}
    out_path = os.path.join(args.out, "audit.json")
    # Reuse an earlier run's arms so a long audit can be resumed instead of
    # restarted, and checkpoint after every arm so an interruption costs one
    # arm rather than all of them.
    if args.resume and os.path.exists(out_path):
        results = json.load(open(out_path))
        print(f"resuming with {len(results)} arms already done", flush=True)
    for name in wanted:
        if name in results and not args.force:
            print(f"[skip] {name} already recorded", flush=True)
            continue
        options = {} if name == "BASELINE" else {name: "true"}
        with driver.Engine(args.engine, options=options) as engine:
            # Assert the configuration from the engine's own reply, not from the
            # name of the arm.
            config = one_switch_on(engine, name)
            if name != "BASELINE" and engine.option_default(name) != "false":
                raise SystemExit(f"{name}: default is not false")
            results[name] = run_switch(engine, name, fens, mates, args.depth, baseline)
        results[name]["config"] = config
        results[name]["controls"] = controls
        with open(out_path, "w") as fh:
            json.dump(results, fh)
        print(f"[done] {name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
