#!/usr/bin/env python3
"""Is the re-checksummed net's corruption REACHABLE, or merely loadable?

"Loads" and "matters" are different claims and only the first has been shown before.
This finds which (feature, lane) the flipped byte lands on -- a king bucket, a piece
colour, a piece type and a square -- then searches for legal positions that put a
piece of exactly that colour and type on exactly that square with a king in exactly
that bucket, and reports whether the evaluation changes.

If the bucket/colour/type/square is reachable and the eval moves, the accepted
corruption is a live wrong number for real positions, which is the fact a reader
needs. If it is not reachable (e.g. no position can put a piece there under that
king bucket), the accepted net is harmless in practice and that is worth saying too.

Usage: reachability.py <probe> <pristine> <rechecksummed> <out.json>
"""
import json
import struct
import subprocess
import sys

HIDDEN, KB, OB = 512, 8, 8
HEADER = 192
PIECE_NAMES = ["-", "P", "N", "B", "R", "Q", "K", "p", "n", "b", "r", "q", "k"]


def describe_flip(raw, offset):
    """Map a byte offset inside w1 to (bucket, colour, type, square, lane)."""
    element = (offset - HEADER) // 2
    lane = element % HIDDEN
    feature = element // HIDDEN
    rel = feature % 768
    return {
        "byte_offset": offset,
        "w1_element": element,
        "lane": lane,
        "feature": feature,
        "bucket": feature // 768,
        "perspective_colour_index": rel // 384,     # 0 = own piece, 1 = opponent
        "piece_type": (rel % 384) // 64 + 1,        # 1..6 = P,N,B,R,Q,K
        "relative_square": rel % 64,
    }


def eval_fen(probe, net, fen):
    proc = subprocess.run([probe, "eval", net, fen], capture_output=True, text=True, timeout=120)
    for line in proc.stdout.splitlines():
        if line.startswith("EVAL\t"):
            return int(line.split("\t")[1])
    return None


def main():
    probe, pristine, corrupt, outpath = sys.argv[1:5]
    raw = open(pristine, "rb").read()
    flipped = open(corrupt, "rb").read()

    # Locate the first differing byte -- do not assume it, read it.
    diff = next(i for i in range(min(len(raw), len(flipped))) if raw[i] != flipped[i])
    info = describe_flip(raw, diff)
    info["old_byte"] = raw[diff]
    info["new_byte"] = flipped[diff]
    info["delta"] = info["new_byte"] - info["old_byte"]
    name = PIECE_NAMES[info["piece_type"]]
    info["piece"] = name
    info["colour"] = "own" if info["perspective_colour_index"] == 0 else "opponent"

    # The corrupted lane is a hidden unit; nothing here can name it in board terms,
    # but the (bucket, colour, type, square) tells us which weights are moved.
    # Find the absolute square for the WHITE perspective (bucket 2 = the map entry
    # for kr = some square). The feature is indexed by kr, so recover kr from the map.
    king_map = list(raw[48:112])
    kr_candidates = [i for i, b in enumerate(king_map) if b == info["bucket"]]
    info["king_map_index_range"] = [min(kr_candidates), max(kr_candidates)]

    # Relative square -> absolute square for the white perspective: r = square.
    sq = info["relative_square"]
    info["white_absolute_square"] = sq
    # For the black perspective the board is flipped (square ^ 56).
    info["black_absolute_square"] = sq ^ 56

    # Build a position that reaches (bucket, colour, type, square) if one exists.
    # Piece letters for the *relative* colour index: for the WHITE perspective the
    # own colour is white. Take the first kr that carries this bucket.
    test_fens = []
    square_name = "abcdefgh"[sq % 8] + str(1 + sq // 8)
    piece_char = name if info["colour"] == "own" else name.lower()
    for kr in (min(kr_candidates), max(kr_candidates)):
        king_square = "abcdefgh"[kr % 8] + str(1 + kr // 8)
        if king_square == square_name:
            # A piece cannot share the king's square; skip.
            continue
        # Put the king on kr, a white pawn on the target square (if it is not the
        # king square), and black king far away.
        black_king = "h8" if king_square != "h8" else "a1"
        placement = {"king": king_square, "target": square_name, "black_king": black_king}
        board = [["" for _ in range(8)] for _ in range(8)]
        board[int(king_square[1]) - 1]["abcdefgh".index(king_square[0])] = "K"
        board[int(black_king[1]) - 1]["abcdefgh".index(black_king[0])] = "k"
        board[int(square_name[1]) - 1]["abcdefgh".index(square_name[0])] = piece_char
        rows = []
        for rank in range(7, -1, -1):
            empty = 0
            row = ""
            for file in range(8):
                cell = board[rank][file]
                if cell == "":
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += cell
            if empty:
                row += str(empty)
            rows.append(row)
        fen = "/".join(rows) + " w - - 0 1"
        test_fens.append({"fen": fen, "king_square": king_square, "placement": placement})

    results = []
    for item in test_fens:
        before = eval_fen(probe, pristine, item["fen"])
        after = eval_fen(probe, corrupt, item["fen"])
        results.append({**item, "eval_pristine": before, "eval_rechecksummed": after,
                        "delta": None if (before is None or after is None) else after - before})

    # A control: positions that cannot touch the flipped weights must agree exactly.
    control_fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4",
    ]
    controls = []
    for fen in control_fens:
        before = eval_fen(probe, pristine, fen)
        after = eval_fen(probe, corrupt, fen)
        controls.append({"fen": fen, "eval_pristine": before, "eval_rechecksummed": after,
                         "delta": None if (before is None or after is None) else after - before})

    payload = {"flip": info, "reachable_positions": results, "controls": controls}
    print(json.dumps(payload, indent=1))
    with open(outpath, "w") as handle:
        json.dump(payload, handle, indent=1)


if __name__ == "__main__":
    main()
