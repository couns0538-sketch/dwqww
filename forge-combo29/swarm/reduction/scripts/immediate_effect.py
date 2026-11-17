#!/usr/bin/env python3
"""immediate_effect.py -- separate the clamp's IMMEDIATE effect from its NET effect.

The clamp can only ever remove reduction, so at the moment two builds first disagree the
cap-ON tree should be the LARGER one. If that holds on nearly every board, then the two
counter-cases are not boards where the clamp behaves differently at all -- they are
boards where a later iteration reverses the immediate direction. That distinction is the
point of this script.

Reads the JSON written by divergence_depth.py.

Verdict for each board:
  IMMEDIATE   sign of (capON - capOFF) at the first divergence depth
  NET         sign of (capON - capOFF) at the final depth
  AGREE/FLIP  whether the two signs match

A high IMMEDIATE agreement with a lower NET agreement is the signature of a later
reversal, and it locates the second mechanism after the divergence rather than at it.

Usage: immediate_effect.py div10.json
"""
import json
import sys


def sign(x):
    return "+" if x > 0 else ("-" if x < 0 else "0")


def main():
    rows = json.load(open(sys.argv[1]))
    rows = [r for r in rows if r.get("first_div")]
    print(f"{'board':46s} {'cls':5s} {'d1st':>5s} {'dN@div':>8s} {'sign':>5s} "
          f"{'dn_net':>9s} {'sign':>5s} {'relation':>9s}")
    print("-" * 96)
    agree = 0
    for r in rows:
        a, b = r["dn_at_div"], r["dn"]
        rel = "AGREE" if sign(a) == sign(b) else "FLIP"
        agree += rel == "AGREE"
        print(f"{r['fen']:46s} {r['cls']:5s} {r['first_div']:>5d} {a:>+8d} {sign(a):>5s} "
              f"{b:>+9d} {sign(b):>5s} {rel:>9s}")

    pos_imm = [r for r in rows if r["dn_at_div"] > 0]
    print()
    print(f"cap-ON visits MORE nodes at the first divergence: {len(pos_imm)} of {len(rows)}")
    print(f"  boards where it does not: "
          f"{[(r['fen'], r['dn_at_div']) for r in rows if r['dn_at_div'] <= 0]}")
    print(f"immediate and net sign agree on {agree} of {len(rows)}")
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    print(f"counter-cases: immediate signs {[sign(r['dn_at_div']) for r in cntr]}, "
          f"net signs {[sign(r['dn']) for r in cntr]}")
    if all(r["dn_at_div"] > 0 for r in cntr):
        print()
        print("FINDING: both counter-cases have a POSITIVE immediate effect. The clamp makes")
        print("the tree larger at the point of divergence on every counter-case board, in the")
        print("same direction as the nine predicted boards. What differs is only what happens")
        print("AFTER that: the net sign reverses. So the second mechanism is downstream of the")
        print("first divergence, not a different behaviour of the clamp itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
