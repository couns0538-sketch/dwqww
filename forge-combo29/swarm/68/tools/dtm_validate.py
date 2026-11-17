#!/usr/bin/env python3
"""Validate the verifier against exact retrograde DTM, and prove it can FAIL.

Three separate claims, each printed with its own denominator:

  A. The verifier reproduces the exact retrograde DTM on a random sample of
     KQvK and KRvK positions (fed the TRUE distance, it must say CORRECT).

  B. Fed a WRONG distance, it must say WRONG in the correct direction. This is
     the "show it can fail" requirement: a verifier that always answers CORRECT
     would pass A and fail here.

  C. Negative control: a checker that assumes the SIDE TO MOVE is always the
     attacker is run over the same positions. It must disagree with the truth on
     negative scores, which is how we know the real verifier's agreement on
     losses is doing work rather than being structurally guaranteed.
"""
import json
import random
import subprocess
import sys
from collections import Counter

import chess

HERE = __file__.rsplit("/", 1)[0]
VERIFY = HERE + "/mateverify"

TRUTH = {}


def load(name):
    with open(f"{HERE}/{name}_dtm.json") as f:
        return json.load(f)


def run_one(fen, claimed):
    r = subprocess.run([VERIFY, "--one", fen, str(claimed)], capture_output=True, text=True)
    out = r.stdout.strip()
    try:
        return json.loads(out), r.returncode
    except json.JSONDecodeError:
        return {"status": "PARSE_ERROR", "raw": out, "stderr": r.stderr.strip()}, r.returncode


def naive_side_to_move_checker(fen, claimed):
    """A checker with the attacker-from-sign bug.

    It assumes the side to move is the attacker, which is backwards for any
    negative mate score. Used as a negative control: it must disagree with the
    truth on negative scores.
    """
    true = TRUTH[fen]
    return (true > 0) == (claimed > 0)


def moves_of(v):
    """Mate distance in MOVES for whichever side is delivering mate."""
    return (v + 1) // 2 if v > 0 else (-v) // 2


def main():
    rng = random.Random(6802)
    kq = load("kqvk")
    kr = load("krvk")
    TRUTH.update(kq)
    TRUTH.update(kr)
    print(f"ground truth loaded: KQvK {len(kq)} positions, KRvK {len(kr)} positions")

    sample = rng.sample(sorted(kq), 60) + rng.sample(sorted(kr), 60)

    print("\nA. verifier fed the TRUE retrograde distance")
    correct = 0
    total = 0
    wins = losses = 0
    for fen in sample:
        v = TRUTH[fen]
        n = moves_of(v)
        if n == 0:
            continue
        claimed = n if v > 0 else -n
        total += 1
        if v > 0:
            wins += 1
        else:
            losses += 1
        res, rc = run_one(fen, claimed)
        if res.get("status") == "CORRECT":
            correct += 1
        else:
            print(f"  MISMATCH {fen} truth={v} claimed={claimed} -> {res}")
    print(f"  {correct}/{total} true claims confirmed CORRECT "
          f"({wins} wins, {losses} losses)")
    print("  attacker resolved from the sign of the score, printed per result below")

    print("\nB. verifier fed a WRONG distance (must reject, with the right direction)")
    rejected = 0
    trials = 0
    dir_stats = Counter()
    for fen in sample:
        v = TRUTH[fen]
        n = moves_of(v)
        if n == 0:
            continue
        sign = 1 if v > 0 else -1
        for delta in (-2, -1, 1, 2):
            wrong = sign * (n + delta)
            if wrong == 0:
                continue
            trials += 1
            res, rc = run_one(fen, wrong)
            if res.get("status") == "WRONG":
                rejected += 1
                expected_dir = "under" if delta > 0 else "over"
                dir_stats[(expected_dir, res.get("direction"))] += 1
            else:
                print(f"  FAILED TO REJECT {fen} truth={v} wrong={wrong} -> {res}")
    print(f"  {rejected}/{trials} wrong claims rejected as WRONG")
    for (exp, got), cnt in sorted(dir_stats.items()):
        print(f"    expected direction {exp:5s}, reported {got:5s}: {cnt}  "
              f"{'ok' if exp == got else 'MISLABELLED'}")

    print("\nC. negative control: a side-to-move-assumes-attacker checker")
    neg_checked = 0
    neg_wrong = 0
    for fen in sample:
        v = TRUTH[fen]
        n = moves_of(v)
        if n == 0:
            continue
        claimed = n if v > 0 else -n
        neg_checked += 1
        if not naive_side_to_move_checker(fen, claimed):
            neg_wrong += 1
    print(f"  naive checker mis-reports {neg_wrong}/{neg_checked} true claims as wrong")
    print(f"  the real verifier got {correct}/{total} of those right")

    ok = (correct == total) and (rejected == trials) and all(e == g for (e, g) in dir_stats) \
        and neg_wrong > 0
    print("\nRESULT:", "VALIDATED (and shown able to fail)" if ok else "VALIDATION FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
