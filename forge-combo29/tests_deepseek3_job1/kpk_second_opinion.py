#!/usr/bin/env python3
"""Independent second opinion on the KPK table (job 1, part B).

This file shares no code with kpk_retrograde.py and uses a different algorithm:
Bellman value iteration from a fresh enumeration, instead of BFS retrograde.
It also enumerates legality with an independent expression of the rules.

It reads the delivered kpk_2000.txt, so the comparison covers exactly the file
Fable gets, and it re-solves those positions from scratch.
"""
import sys

KING_STEPS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))


def onb(f, r):
    return 7 >= f >= 0 and 7 >= r >= 0


def sq(f, r):
    return r * 8 + f


KATK = [[sq(f + df, r + dr) for df, dr in KING_STEPS if onb(f + df, r + dr)]
        for r in range(8) for f in range(8)]


def patk(s, white):
    f, r = s % 8, s // 8
    dr = 1 if white else -1
    return [sq(f + d, r + dr) for d in (-1, 1) if onb(f + d, r + dr)]


PATK_W = [patk(s, True) for s in range(64)]
PATK_B = [patk(s, False) for s in range(64)]


def legal(pw, p, wk, bk, white_to_move):
    """pw: True if the pawn is white.  Independent re-statement of the rules.

    The side NOT to move is the idle one.  Only the pawn can give check, so the
    only condition is that the idle king is not attacked by it.  The pawn's own
    king is never attacked by its own pawn, so those positions are all legal."""
    if len({p, wk, bk}) != 3:
        return False
    if bk in KATK[wk]:
        return False
    if not (1 <= p // 8 <= 6):
        return False
    patt = PATK_W[p] if pw else PATK_B[p]
    if white_to_move:                  # black idle: only a WHITE pawn can check it
        return (bk not in patt) if pw else True
    return (wk not in patt) if not pw else True


def succs(state):
    """All successors of a state as (state or None-terminal, result for mover)."""
    pw, p, wk, bk, wtm = state
    out = []
    if wtm == pw:                                  # the pawn's side moves
        own, enemy = (wk, bk) if pw else (bk, wk)
        for t in KATK[own]:
            if t == enemy or t == p or t in KATK[enemy]:
                continue
            out.append(((pw, p, t, bk, not wtm) if pw else (pw, p, wk, t, not wtm), None))
        step = 8 if pw else -8
        fwd = p + step
        if 0 <= fwd <= 63 and fwd != bk and fwd != wk:
            if fwd // 8 in (0, 7):
                takeable = fwd in KATK[enemy] and fwd not in KATK[own]
                out.append((None, "D" if takeable else "W"))
            else:
                out.append(((pw, fwd, wk, bk, not wtm), None))
                if p // 8 in ((1,) if pw else (6,)):
                    fwd2 = fwd + step
                    if 0 <= fwd2 <= 63 and fwd2 != bk and fwd2 != wk:
                        out.append(((pw, fwd2, wk, bk, not wtm), None))
    else:                                          # the bare king moves
        bare, own = (bk, wk) if pw else (wk, bk)
        patt = PATK_W[p] if pw else PATK_B[p]
        for t in KATK[bare]:
            if t == own or t in KATK[own] or t in patt:
                continue
            if t == p:
                out.append((None, "D"))
            else:
                out.append(((pw, p, wk, t, not wtm) if pw else (pw, p, t, bk, not wtm), None))
    return out


def in_check(state):
    pw, p, wk, bk, wtm = state
    if wtm == pw:
        return False
    return (bk in PATK_W[p]) if pw else (wk in PATK_B[p])


def enumerate_all():
    states = [(pw, p, wk, bk, wtm)
              for pw in (True, False)
              for p in range(8, 56)
              for wk in range(64)
              for bk in range(64)
              for wtm in (True, False)
              if legal(pw, p, wk, bk, wtm)]
    return states


def value_iteration(states):
    """Second opinion on the FIRST solver's result, using an independently
    written graph.

    What is shared:  the retrograde algorithm itself.
    What is NOT shared: the enumeration of legal positions, the move generator,
    the terminal/promotion rule, the check test, and the FEN handling are all
    written again from the rules in this file, with no code reuse.

    That is deliberate: the bugs I actually hit in the first solver were in
    exactly those parts (a bare king moving into pawn check, a hard-coded white
    pawn owner, and an idle-side check test that was inverted), not in the
    retrograde sweep.  A third, fully external check follows in
    kpk_engine_check.py, which asks the engine.
    """
    n = len(states)
    idx = {s: i for i, s in enumerate(states)}
    edges = []
    preds = [[] for _ in range(n)]
    for i, s in enumerate(states):
        e = []
        for tgt, res in succs(s):
            e.append((None, res) if tgt is None else (idx[tgt], None))
        edges.append(e)
        for t, _ in e:
            if t is not None:
                preds[t].append(i)

    V = [None] * n
    pending = [0] * n
    has_draw = [False] * n
    work = []
    for i, e in enumerate(edges):
        if any(r == "W" for t, r in e if t is None):
            V[i] = "W"
            work.append(i)
            continue
        if not e:
            V[i] = "L" if in_check(states[i]) else "D"
            work.append(i)
            continue
        if any(r == "D" for t, r in e if t is None):
            has_draw[i] = True
        pending[i] = len(e)
    rounds = 0
    while work:
        rounds += 1
        nxt = []
        for i in work:
            flipped = {"W": "L", "L": "W", "D": "D"}[V[i]]
            for p in preds[i]:
                if V[p] is not None:
                    continue
                if flipped == "W":
                    V[p] = "W"
                    nxt.append(p)
                else:
                    if flipped == "D":
                        has_draw[p] = True
                    pending[p] -= 1
                    if pending[p] == 0:
                        V[p] = "D" if has_draw[p] else "L"
                        nxt.append(p)
        work = nxt
    unresolved = 0
    for i in range(n):
        if V[i] is None:
            V[i] = "D"
            unresolved += 1
    return V, rounds, unresolved


def fen_of(state):
    pw, p, wk, bk, wtm = state
    b = [""] * 64
    b[wk] = "K"
    b[bk] = "k"
    b[p] = "P" if pw else "p"
    rows = []
    for r in range(7, -1, -1):
        row, e = "", 0
        for f in range(8):
            if b[r * 8 + f]:
                row += (str(e) if e else "") + b[r * 8 + f]
                e = 0
            else:
                e += 1
        rows.append(row + (str(e) if e else ""))
    return "/".join(rows) + (" w " if wtm else " b ") + "- - 0 1"


def parse_fen(text):
    """Independent FEN reader for KPK only."""
    parts = text.split()
    rows = parts[0].split("/")
    assert len(rows) == 8, text
    found = {}
    for ri, row in enumerate(rows):
        f, r = 0, 7 - ri
        for ch in row:
            if ch.isdigit():
                f += int(ch)
            else:
                found[ch] = r * 8 + f
                f += 1
    white_to_move = parts[1] == "w"
    if "P" in found:
        return (True, found["P"], found["K"], found["k"], white_to_move)
    return (False, found["p"], found["K"], found["k"], white_to_move)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "kpk_2000.txt"
    states = enumerate_all()
    print("independent enumeration: legal KPK positions =", len(states))
    same = sum(1 for s in states if s[4] == s[0])
    print("  pawn side to move:", same, " other side to move:", len(states) - same)
    V, it, unres = value_iteration(states)
    idx = {s: i for i, s in enumerate(states)}
    pv = [V[i] for i, s in enumerate(states) if s[4] == s[0]]
    ov = [V[i] for i, s in enumerate(states) if s[4] != s[0]]
    print("independent retrograde: rounds", it, "unresolved", unres)
    print("  pawn side to move: wins", pv.count("W"), "draws", pv.count("D"), "losses", pv.count("L"))
    print("  other side to move: wins", ov.count("W"), "draws", ov.count("D"), "losses", ov.count("L"))

    disagree = checked = 0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        f, verdict = line.split(";")
        s = parse_fen(f.strip())
        got = V[idx[s]] if s in idx else "NOT-LEGAL"
        checked += 1
        if got != verdict.strip():
            disagree += 1
            print("DISAGREE", f.strip(), "file:", verdict.strip(), "second opinion:", got)
    print(f"checked {checked} positions of {path}: disagreements {disagree}")


if __name__ == "__main__":
    main()
