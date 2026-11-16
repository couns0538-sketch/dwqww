#!/usr/bin/env python3
"""make_ep_pin.py : construct en-passant-exposes-the-king positions by hand and VERIFY each.

Random legal play almost never produces these (the filter found 0 in 5000 R + 353 G positions),
so they are built by hand and then verified by python-chess: the ep capture must be pseudo-legal,
ILLEGAL, and leave our own king attacked. A case that fails verification is printed as REJECTED and
not used — nothing is assumed to be a valid construction just because it was written down.

These are board positions, not code from another engine.
"""
import chess
import json

# The board must be a legal-ish position where an ep capture exists. FEN with the ep square set,
# the pawns in place, and a slider lined up so removing both pawns opens the line to our king.
CANDIDATES = [
    # white king a5, white pawn b5, black pawn c5 (just double-pushed), black rook h5 -> the rank
    # a5-h5 is opened by b5xc6 ep (both b5 and c5 leave the rank).
    ("rank_pin_white", "8/8/8/KPp4r/8/8/8/7k w - c6 0 1"),
    # black to move, mirrored: black king a4, black pawn b4, white pawn c4, white rook h4.
    ("rank_pin_black", "8/8/8/8/kpP4R/8/8/7K b - c3 0 1"),
    # white king e5, white pawn d5, black pawn e5 just double-pushed, black rook a5.
    ("rank_pin_middle", "8/8/8/r2PpK2/8/8/8/7k w - e6 0 1"),
    # diagonal-ish: white king a4, white pawn b4, black pawn c4, black bishop h4 attacking along rank 4.
    ("rank_pin_bishop", "8/8/8/8/KPp4b/8/8/7k w - c3 0 1"),
    # knight is not a slider: this one should NOT be a pin (control that must be REJECTED).
    ("control_no_pin", "8/8/8/KPp4n/8/8/8/7k w - c6 0 1"),
]


def verify(fen):
    b = chess.Board(fen)
    if not b.is_valid():
        return None, "board invalid"
    res = []
    for move in b.generate_pseudo_legal_ep():
        legal = move in b.legal_moves
        b2 = b.copy()
        b2.push(move)
        king = b2.king(b.turn)
        exposed = king is not None and b2.is_attacked_by(not b.turn, king)
        res.append({"move": move.uci(), "legal": legal, "exposes_king": exposed})
    return res, None


kept, rejected = [], []
for name, fen in CANDIDATES:
    probes, err = verify(fen)
    if err:
        rejected.append((name, fen, err))
        print("REJECTED %-18s %-34s %s" % (name, fen, err))
        continue
    hits = [p for p in probes if (not p["legal"]) and p["exposes_king"]]
    if name.startswith("control"):
        if hits:
            rejected.append((name, fen, "control unexpectedly exposes the king"))
            print("REJECTED %-18s %-34s control fired" % (name, fen))
        else:
            rejected.append((name, fen, "control: correctly not an ep pin (kept as a negative control)"))
            print("CONTROL  %-18s %-34s probes %s (no pin, as intended)" % (name, fen, probes))
        continue
    if not hits:
        rejected.append((name, fen, "not an ep pin: probes %s" % probes))
        print("REJECTED %-18s %-34s probes %s" % (name, fen, probes))
        continue
    kept.append({"name": name, "fen": chess.Board(fen).fen(), "probes": probes})
    print("KEPT     %-18s %-34s %s" % (name, fen, hits))

with open("ep_pin_cases.json", "w") as f:
    json.dump({"kept": kept, "rejected": rejected}, f, indent=1)
with open("EP_PIN.fens", "w") as f:
    for case in kept:
        f.write(case["fen"] + "\n")
print("\nkept %d, rejected %d" % (len(kept), len(rejected)))
