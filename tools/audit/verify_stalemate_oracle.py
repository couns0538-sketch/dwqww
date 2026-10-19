#!/usr/bin/env python3
"""Independent geometric oracle for the KQK forced-stalemate regression.

Root FEN: 7k/8/5K2/6Q1/8/8/8/8 w - - 0 1.
White plays g5g6. Black king on h8 has no legal move and is not in check.
No python-chess installation is required.
"""
def sq(s):
    return ord(s[0]) - ord("a"), int(s[1]) - 1

def qattack(q, t, blocker):
    dx, dy = t[0] - q[0], t[1] - q[1]
    if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        return False
    sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
    x, y = q[0] + sx, q[1] + sy
    while (x, y) != t:
        if (x, y) == blocker:
            return False
        x, y = x + sx, y + sy
    return True

def katt(king, t):
    return max(abs(t[0] - king[0]), abs(t[1] - king[1])) == 1

white_king, black_king, queen_before, queen_after = (sq(s) for s in ("f6", "h8", "g5", "g6"))
assert not qattack(queen_before, black_king, white_king)
assert not katt(white_king, black_king)
assert not qattack(queen_after, black_king, white_king)
assert not katt(white_king, black_king)
legal = []
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        if dx == 0 and dy == 0:
            continue
        candidate = black_king[0] + dx, black_king[1] + dy
        if not (0 <= candidate[0] < 8 and 0 <= candidate[1] < 8):
            continue
        if candidate in (white_king, queen_after):
            continue
        if not katt(white_king, candidate) and not qattack(queen_after, candidate, white_king):
            legal.append(candidate)
assert legal == [], f"Black had legal moves: {legal}"
print("PASS: after g5g6, h8 is not in check and black has no legal moves (stalemate)")
