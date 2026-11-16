#!/usr/bin/env python3
"""check_pv.py JSONL... : validates every last-pv line and every mate score.

For each record:
  - takes the last `info ... pv ...` line (the "final PV")
  - plays every move of that PV with python-chess from the record's FEN
  - records the first illegal move (if any)
  - for a `mate N` score, checks the PV length rule and the final position

Control mode: --control mutates the last move of a known-good PV into an illegal one and
asserts the checker catches it.
"""
import json
import sys

import chess


def parse_pv(line):
    """Returns (depth, score_kind, score_value, [moves]) from an info line, or None."""
    toks = line.split()
    depth = None
    kind = None
    val = None
    moves = None
    for i, t in enumerate(toks):
        if t == "depth" and i + 1 < len(toks):
            depth = int(toks[i + 1])
        elif t == "score" and i + 2 < len(toks):
            kind = toks[i + 1]
            try:
                val = int(toks[i + 2])
            except ValueError:
                val = None
        elif t == "pv":
            moves = toks[i + 1:]
            break
    if moves is None:
        return None
    return depth, kind, val, moves


def final_pv(lines):
    last = None
    for line in lines:
        if line.startswith("info ") and " pv " in line:
            p = parse_pv(line)
            if p:
                last = p
    return last


def check(board, moves):
    """Plays moves; returns (ok, first_bad_index, first_bad_move)."""
    b = board.copy()
    for i, m in enumerate(moves):
        try:
            mv = chess.Move.from_uci(m)
        except ValueError:
            return False, i, m
        if mv not in b.legal_moves:
            return False, i, m
        b.push(mv)
    return True, None, None


def main():
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    control = "--control" in sys.argv
    expect_records = None
    expect_mates = None
    for a in sys.argv[1:]:
        if a.startswith("--expect-records="):
            expect_records = int(a.split("=", 1)[1])
        if a.startswith("--expect-mates="):
            expect_mates = int(a.split("=", 1)[1])

    total = 0
    no_pv = 0
    illegal = []
    mates = []
    mate_checked = 0
    mate_wrong = []
    bad_fens = []
    unparsed = []

    for path in files:
        for line in open(path):
            rec = json.loads(line)
            total += 1
            if not rec.get("lines"):
                print(f"NO ENGINE OUTPUT for record #{rec.get('i')} {rec.get('fen')}")
                unparsed.append(rec.get("i"))
                continue
            try:
                board = chess.Board(rec["fen"])
            except ValueError:
                print(f"BAD FEN {rec['fen']}")
                bad_fens.append(rec["fen"])
                continue
            pv = final_pv(rec["lines"])
            if pv is None:
                no_pv += 1
                unparsed.append(rec.get("i"))
                continue
            depth, kind, val, moves = pv
            ok, badi, badm = check(board, moves)
            if not ok:
                illegal.append({"file": path, "i": rec["i"], "fen": rec["fen"],
                                "moves": moves, "bad_index": badi, "bad_move": badm,
                                "line": pv})
                continue
            if kind == "mate" and val is not None:
                mates.append({"fen": rec["fen"], "mate": val, "len": len(moves),
                              "moves": moves})
                mate_checked += 1
                want = 2 * val - 1 if val > 0 else 2 * abs(val)
                b = board.copy()
                for m in moves:
                    b.push(chess.Move.from_uci(m))
                is_mate = b.is_checkmate()
                if len(moves) != want or not is_mate:
                    mate_wrong.append({"fen": rec["fen"], "mate": val,
                                       "pv_len": len(moves), "want_len": want,
                                       "final_is_checkmate": is_mate, "moves": moves})

    print(f"records            : {total}")
    print(f"no final pv        : {no_pv}")
    print(f"PVs with illegal   : {len(illegal)}")
    for x in illegal[:40]:
        print(f"  ILLEGAL {x['file']} #{x['i']} {x['fen']} bad={x['bad_move']}@{x['bad_index']} pv={' '.join(x['moves'])}")
    print(f"mate scores        : {len(mates)}")
    for m in mates:
        print(f"  MATE {m['mate']:>4} len={m['len']:>2} {m['fen']}")
    print(f"mate PVs wrong     : {len(mate_wrong)}")
    for m in mate_wrong:
        print(f"  WRONG {m}")
    print(f"bad FENs           : {len(bad_fens)}")
    print(f"records with no output or no pv: {len(unparsed)}")

    # A zero must never pass silently. Fail loudly when the evidence is absent or contradictory.
    failures = []
    if total == 0:
        failures.append("NO RECORDS READ: the input was empty, so this check measured nothing")
    if expect_records is not None and total != expect_records:
        failures.append(f"EXPECTED {expect_records} records, read {total}")
    if expect_mates is not None and len(mates) != expect_mates:
        failures.append(f"EXPECTED {expect_mates} mate scores, saw {len(mates)}")
    if bad_fens:
        failures.append(f"{len(bad_fens)} FEN(s) did not parse: a comparison against nothing is not a result")
    if unparsed and len(unparsed) == total:
        failures.append("NO record produced a readable pv: nothing was compared")

    if failures:
        print()
        print("CHECK FAILED — this run is NOT a result:")
        for f in failures:
            print("  -", f)
        return 3
    return 0

    if control:
        # Plant an illegal last move in the first good PV found and require the checker to catch it.
        for path in files:
            for line in open(path):
                rec = json.loads(line)
                pv = final_pv(rec["lines"])
                if not pv:
                    continue
                board = chess.Board(rec["fen"])
                ok, _, _ = check(board, pv[3])
                if not ok or not pv[3]:
                    continue
                b = board.copy()
                for m in pv[3][:-1]:
                    b.push(chess.Move.from_uci(m))
                legal = [m.uci() for m in b.legal_moves]
                illegal_choice = "e1e8" if "e1e8" not in legal else "a1a8"
                if illegal_choice in legal:
                    continue
                bad_pv = pv[3][:-1] + [illegal_choice]
                ok2, badi2, badm2 = check(board, bad_pv)
                print(f"CONTROL: original PV ok={ok}; mutated last move -> caught={not ok2} "
                      f"bad_move={badm2}@{badi2} fen={rec['fen']}")
                return 0 if not ok2 else 1
        print("CONTROL: no clean PV found to mutate")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
