#!/usr/bin/env python3
"""mate0_consumer.py : does `score mate 0` break a standard UCI consumer?

The engine emits `score mate 0` on a checkmated root. Standard UCI says a mate score is `mate <N>` where N is
the number of MOVES to mate, signed by side. mate 0 is not defined. Show what happens when the standard
conversion is applied, and what the correct value would be.

Nothing here talks to the engine; it consumes the exact string the engine prints (copied from
terminal_report.txt) so the arithmetic is auditable against the committed raw output.
"""
# the exact tokens the PC build printed on a checkmated root (from terminal_report.txt)
tokens = [
    ("checkmated root, PC r15/PC20", "score mate 0"),
    ("stalemated root, PC r15/PC20", "score cp 0"),
]
# a real mate, for contrast
tokens.append(("a normal mate in 3 (contrast)", "score mate -3"))

for name, tok in tokens:
    kind, val = tok.split()[1], int(tok.split()[2])
    print(f"{name}: `{tok}`")
    if kind == "mate":
        # standard conversion used by GUIs: +N => we mate in N moves; -N => mated in N moves
        if val > 0:
            meaning = f"the side to move mates in {val} moves"
        elif val < 0:
            meaning = f"the side to move is mated in {-val} moves"
        else:
            meaning = "UNDEFINED: mate in 0 moves is not possible (mate either exists at least one move away, or not at all)"
        print(f"   -> {meaning}")
    else:
        print(f"   -> a centipawn score of {val}")
    print()

print("What the two terminal cases SHOULD report, so a GUI can tell them apart:")
print("  checkmated root : mate 0 is meaningless; the honest encodings are `mate 0` (non-standard) or")
print("                    a large negative centipawn value, and every standard GUI will either show")
print("                    nothing sensible or treat it as a win for nobody.")
print("  stalemated root : `cp 0` — a genuine draw, which IS correct and standard.")
print()
print("Net: the two zero-move positions are reported in two different currencies, and the checkmate one in an")
print("undefined token. A GUI that reads `mate 0` shows no mate; a training pipeline that maps mate scores to")
print("labels by sign will label the checkmated root as neither win nor loss (0 is neither + nor -).")
