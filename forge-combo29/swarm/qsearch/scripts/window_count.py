#!/usr/bin/env python3
"""Model-free evidence for FINDINGS 5b.

For each halfmove clock H, count the plies until the side that wants the draw
(Black, at the bottom of this position) can first CLAIM: clock >= 100 on a BLACK
turn, assuming Black only shuffles its king and White never captures (a capture
resets the clock). No evaluation is involved anywhere in this file.

Two clocks with the same count give White the same number of moves to find a mate
or a clock-resetting capture, so a correct search must give them the same verdict.
"""
def window(h):
    clock, turn, ply = h, 'B', 0
    while ply <= 60:
        if turn == 'B' and clock >= 100:
            return ply, clock
        ply += 1; clock += 1; turn = 'W' if turn == 'B' else 'B'
    return None, None

if __name__ == "__main__":
    print(" H | plies to a Black-turn claim | White moves in that window")
    print("---|-----------------------------|-------------------------")
    for h in range(90, 101):
        p, c = window(h)
        print(f"{h:3d} | {p:>27d} | {p//2:>24d}")
    print()
    print("H=96 and H=97 are both 4 plies / 2 White moves: the SAME window size.")
    print("H=94/95 are both 6 plies; H=98/99 are both 2 plies.")
    print("NOTE: an equal window size does NOT force an equal verdict -- H=94/95 share")
    print("one and legitimately differ. It means a qualitative flip across the pair")
    print("needs a mechanism. See FINDINGS 5b for what that does and does not prove.")
