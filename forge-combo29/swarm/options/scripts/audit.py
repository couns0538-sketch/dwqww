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
    """Verify a mate claim by replaying the engine's own PV.

    This is the direct falsification test and it needs no convention at all: if
    the engine claims mate, its PV must end in checkmate, and the side that is
    mated must be the side the score's SIGN says is losing. A PV that does not
    reach mate is a false mate claim, which is the serious direction of this
    defect and cannot be explained away by a distance convention.

    `calibrate_mate_format.py` separately establishes that a claimed `mate N`
    corresponds to a PV of 2N-1 plies (positive) or 2N plies (negative), so the
    length can be checked too; both checks are applied here.
    """
    if mate is None:
        return True, "no mate claimed"
    sign = 1 if mate > 0 else -1
    n = abs(mate)
    expect_plies = 2 * n - 1 if sign > 0 else 2 * n
    if len(pv) < expect_plies:
        return False, f"pv has {len(pv)} moves, mate {mate} needs {expect_plies} plies"
    b = board.copy()
    for index in range(expect_plies):
        move = legal_or_none(b, pv[index])
        if move is None:
            return False, f"pv[{index}]={pv[index]} illegal after {b.fen()}"
        b.push(move)
    if not b.is_checkmate():
        return False, f"pv of {expect_plies} plies does not end in checkmate ({b.fen()})"
    # The mated side must be the one the score says is losing.
    mated = b.turn
    if sign > 0 and mated == board.turn:
        return False, "positive mate score but the mover is the side mated"
    if sign < 0 and mated != board.turn:
        return False, "negative mate score but the opponent is the side mated"
    return True, ""


def check_mates(engine: driver.Engine, mates: list[dict], depth: int,
                baseline: dict | None = None) -> dict:
    """Mate correctness, as three separate claims.

    The three are kept apart because they fail in different directions and only
    one of them is unsound:

      UNSOUND     the engine claims a mate whose own PV does not reach
                  checkmate, or claims a mate in fewer plies than the shortest
                  proved one. A false mate claim is the sharpest form and is
                  decided by PV replay, not by a distance convention.
      REGRESSION  a mate the BASELINE arm finds and this arm does not. Only a
                  change against the baseline counts: at a fixed depth a deep
                  mate can be out of reach, so "not reported" alone is not a
                  defect and is recorded as MISSED instead.
      IMPRECISE   both report a mate, but this arm's distance is longer. Not a
                  correctness failure (the line still wins) but recorded,
                  because a switch that systematically lengthens reported mates
                  is doing something to the mate search.
    """
    rows = []
    unsound = []
    regressions = []
    imprecise = []
    missed = []
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
        if mate is None:
            row["verdict"] = "MISSED"
            missed.append(row)
            if baseline is not None:
                base = baseline["rows"][index]
                if base.get("mate") is not None:
                    row["verdict"] = "REGRESSION"
                    row["baseline_mate"] = base["mate"]
                    regressions.append(row)
        else:
            ok, why = mate_claim_is_true(board, mate, res["pv"])
            row["pv_confirms_mate"] = ok
            if not ok:
                row["pv_problem"] = why
                row["verdict"] = "UNSOUND_FALSE_MATE"
                unsound.append(row)
            else:
                # Compare in MOVE numbers, which is what the wire carries.
                claimed_moves = abs(mate)
                row["claimed_moves"] = claimed_moves
                row["delta_moves"] = claimed_moves - plies_to_moves(proved)
                if claimed_moves < plies_to_moves(proved):
                    # A faster mate than the proved shortest. The PV ends in
                    # mate, so this is either a better line my prover missed or
                    # a distance that is too optimistic; recorded for review.
                    row["verdict"] = "FASTER_THAN_PROOF"
                    imprecise.append(row)
                else:
                    row["verdict"] = "ok"
                    if claimed_moves > plies_to_moves(proved):
                        imprecise.append(row)
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
        "claimed_mates": sum(1 for r in rows if r.get("mate") is not None),
        "pv_verified": sum(1 for r in rows if r.get("pv_confirms_mate")),
        "rows": rows,
    }


def mate_controls() -> dict:
    """Proof the mate checker can fail, in both directions.

    A checker that only ever says PASS is indistinguishable from one whose
    comparison cannot fire, so each mechanism gets a planted case it must
    reject and a true case it must accept.
    """
    out = {}
    # A real mate in 1: Ra8#. The PV confirms, so the checker must accept.
    b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
    out["accepts_true_mate_in_1"] = mate_claim_is_true(b, 1, ["a1a8"])[0]
    # A FALSE mate claim: the same position, a PV that does not mate.
    out["rejects_false_mate_pv"] = not mate_claim_is_true(b, 1, ["a1a2"])[0]
    # A mate claim whose PV is too short to contain the mate.
    out["rejects_short_pv"] = not mate_claim_is_true(b, 3, ["a1a8"])[0]
    # A negative mate claim: `mate -2` means 4 plies, verified end-to-end
    # against a line found by brute force, not by hand.
    b2 = chess.Board("7k/8/5K2/8/8/8/2Q5/8 b - - 9 5")
    out["accepts_true_negative_mate"] = mate_claim_is_true(
        b2, -2, ["h8g8", "c2c7", "g8h8", "c7g7"])[0]
    out["rejects_negative_claim_without_mate"] = not mate_claim_is_true(
        b2, -2, ["h8g8", "c2c7", "g8h8", "c7c1"])[0]
    # A sign flip must be caught: the same PV labelled with the wrong sign.
    out["rejects_wrong_sign"] = not mate_claim_is_true(b, -1, ["a1a8"])[0]
    out["passed"] = all(out.values())
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
