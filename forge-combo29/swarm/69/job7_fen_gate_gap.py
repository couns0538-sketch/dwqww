"""JOB 7: how large is the "python-chess says valid, engine says no" class?

This exists because the coordinator's standing advice to every seat has been "validate
your FENs with python-chess". That advice is necessary and NOT sufficient: the two
programs disagree on a class of boards, and on that class a harness measures the
PREVIOUS position while recording it as the intended one.

Two directions, both counted:

  DIRECTION A (the dangerous one): python-chess ACCEPTS, engine REFUSES.
      `4k3/8/8/8/8/8/8/R3K2R w K - 0 0` (fullmove 0) is the known example. A harness that
      trusts python-chess sends it, the engine keeps the previous board, and the harness
      records a reproducible node count for the wrong position.

  DIRECTION B (harmless but worth knowing): python-chess REJECTS, engine ACCEPTS.
      A harness that filters with python-chess simply drops these, so no wrong number.

Method: take real positions from sets O and G, apply one mutation each from a fixed
grammar over the six FEN fields and the placement, keep every mutant python-chess
accepts, and ask the engine about each. Deterministic: seeded.

The rate that matters to the coordinator is DIRECTION A / (mutants python-chess accepts).
"""

import json
import os
import random
import sys

import chess

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
SEED = 6917
N_MUTANTS = 2000

# Mutations that touch each of the six fields plus the placement field.
FIELD_MUTATIONS = [
    ("halfmove", lambda f: _set_field(f, 4, lambda v: str(max(0, v - 1)))),
    ("halfmove_over100", lambda f: _set_field(f, 4, lambda v: "150")),
    ("fullmove_zero", lambda f: _set_field(f, 5, lambda v: "0")),
    ("fullmove_big", lambda f: _set_field(f, 5, lambda v: "1000000000")),
    ("side_b", lambda f: _set_field(f, 1, lambda v: "b" if v == "w" else "w")),
    ("castling_drop", lambda f: _set_field(f, 2, lambda v: "-")),
    ("castling_add_kq", lambda f: _set_field(f, 2, lambda v: "KQkq")),
    ("ep_dash", lambda f: _set_field(f, 3, lambda v: "-")),
    ("ep_wrong_rank", lambda f: _set_field(f, 3, lambda v: "e4")),
    ("pawn_on_rank1", lambda f: _place_pawn_rank1(f)),
    ("pawn_on_rank8", lambda f: _place_pawn_rank8(f)),
]


def _set_field(fen, index, fn):
    parts = fen.split()
    if len(parts) <= index:
        return None
    parts[index] = fn(parts[index])
    return " ".join(parts)


def _place_pawn_rank1(fen):
    parts = fen.split()
    ranks = parts[0].split("/")
    # rank 8 is ranks[0]; put a white pawn on rank 1 = ranks[7]
    last = list(ranks[7].replace("8", "7P") if "8" in ranks[7] else ranks[7])
    ranks[7] = "".join(last) if "".join(last) != ranks[7] else "P7"
    parts[0] = "/".join(ranks)
    return " ".join(parts)


def _place_pawn_rank8(fen):
    parts = fen.split()
    ranks = parts[0].split("/")
    ranks[0] = "P7" if ranks[0] != "P7" else "1P6"
    parts[0] = "/".join(ranks)
    return " ".join(parts)


def pc_verdict(fen):
    """('valid'|'invalid'|'raises', detail)"""
    try:
        board = chess.Board(fen)
    except Exception as exc:  # noqa: BLE001
        return "raises", str(exc)[:40]
    return ("valid", "") if board.is_valid() else ("invalid", str(board.status()))


def engine_verdict(engine, fen):
    """True when the engine accepted the FEN (no `invalid FEN` diagnostic).

    One `isready` and one blocking read to `readyok`: the diagnostic, if any, is in that
    same reply because it is emitted in response to `position`, before the `readyok` that
    the `isready` produces.
    """
    engine.send("position fen %s" % fen)
    engine.send("isready")
    try:
        reply = engine.read_until("readyok", timeout=20)
    except ucih.EngineError as exc:
        # A refused FEN must not deadlock the sweep: report and resynchronise.
        return False, "sync failed: " + str(exc)[:40]
    for line in reply:
        if "invalid FEN" in line:
            return False, line.split("invalid FEN:")[-1].strip()[:48]
    return True, ""


def main():
    rng = random.Random(SEED)
    valid_o, _ = ucih.validate_fens("/tmp/O.fens")
    valid_g, _ = ucih.validate_fens("/tmp/G.epd")
    pool = valid_o + valid_g

    mutants = []
    seen = set()
    while len(mutants) < N_MUTANTS:
        base = rng.choice(pool)
        name, fn = rng.choice(FIELD_MUTATIONS)
        try:
            mutant = fn(base)
        except Exception:  # noqa: BLE001
            continue
        if not mutant or mutant == base or mutant in seen:
            continue
        seen.add(mutant)
        mutants.append((name, mutant))

    print("=== JOB 7: python-chess vs engine acceptance, one mutation per FEN ===")
    print("seed %d, mutants generated %d from %d real positions (O+G)\n"
          % (SEED, len(mutants), len(pool)))

    engine = ucih.Engine(BASE_EXE, timeout=60)
    engine.uci()
    rows = []
    try:
        for name, fen in mutants:
            pc, pcdetail = pc_verdict(fen)
            eng, engdetail = engine_verdict(engine, fen)
            rows.append({"mutation": name, "fen": fen, "python_chess": pc,
                         "pc_detail": pcdetail, "engine_accepts": eng,
                         "engine_detail": engdetail})
    finally:
        engine.close()

    both = [r for r in rows if r["python_chess"] == "valid"]
    a = [r for r in both if not r["engine_accepts"]]
    b = [r for r in rows if r["python_chess"] != "valid" and r["engine_accepts"]]

    print("mutants:                                   %d" % len(rows))
    print("python-chess VALID:                        %d" % len(both))
    print("  of those, engine REFUSES (DIRECTION A):  %d   <-- the dangerous class" % len(a))
    print("python-chess INVALID or raises:            %d" % (len(rows) - len(both)))
    print("  of those, engine ACCEPTS (DIRECTION B):  %d   <-- harmless if you filter" % len(b))
    print()
    if both:
        print("DIRECTION A rate among python-chess-valid mutants: %d / %d = %.2f%%"
              % (len(a), len(both), 100.0 * len(a) / len(both)))

    by_mut = {}
    for r in a:
        by_mut.setdefault(r["mutation"], []).append(r)
    print("\n-- DIRECTION A by mutation --")
    for name in sorted(by_mut):
        print("   %-20s %d" % (name, len(by_mut[name])))
    print("\n-- every DIRECTION A example (first 12) --")
    for r in a[:12]:
        print("   %-18s %-54s engine: %s" % (r["mutation"], r["fen"][:54], r["engine_detail"]))

    # The control: the unmutated pool must be accepted by BOTH programs.
    print("\n-- control: the real positions themselves --")
    bad_engine = 0
    engine = ucih.Engine(BASE_EXE, timeout=60)
    engine.uci()
    try:
        for fen in pool:
            ok, _ = engine_verdict(engine, fen)
            if not ok:
                bad_engine += 1
    finally:
        engine.close()
    print("   real positions where the engine refuses: %d / %d" % (bad_engine, len(pool)))

    report = {"seed": SEED, "n_mutants": len(rows), "pc_valid": len(both),
              "direction_a": len(a), "direction_b": len(b),
              "direction_a_by_mutation": {k: len(v) for k, v in by_mut.items()},
              "control_engine_refused": bad_engine, "control_n": len(pool),
              "rows": rows}
    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job7/fen_gate_gap.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
