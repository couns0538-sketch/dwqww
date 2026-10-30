"""R8: does an FPOS v1 .pos file hold exactly the records of a self-play text file, in order? (read only)
usage: python -I -B check_pos_vs_text.py <file.pos> <file.txt> [--limit N]
Text line: "FEN | cp | result" (cp side to move, result White's 1.0/0.5/0.0). FPOS v1: "FPOS", u32 1, u64 n, n x 32-byte
boards (nibble per square, a1 = 0, low nibble = even square; 1..6 white P N B R Q K, 7..12 black), n x i16 score,
n x u8 meta (bit0 black to move, bits1-2 White's result * 2). Prints the record count and the mismatches per field."""
import struct
import sys

pos_path, txt_path = sys.argv[1], sys.argv[2]
limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
CODE = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}
with open(pos_path, "rb") as f:
    magic, ver, n = struct.unpack("<4sIQ", f.read(16))
    assert magic == b"FPOS" and ver == 1, (magic, ver)
    m = n if limit is None else min(n, limit)
    boards = f.read(32 * m)
    f.seek(16 + 32 * n)
    scores = struct.unpack(f"<{m}h", f.read(2 * m))
    f.seek(16 + 34 * n)
    metas = f.read(m)
bad = {"board": 0, "side": 0, "score": 0, "result": 0}
count = 0
with open(txt_path, encoding="ascii") as t:
    for i, line in enumerate(t):
        if i >= m:
            break
        fen, cp, res = (x.strip() for x in line.split("|"))
        placement, side = fen.split()[:2]
        codes = [0] * 64
        r, fcol = 7, 0
        for ch in placement:
            if ch == "/":
                r, fcol = r - 1, 0
            elif ch.isdigit():
                fcol += int(ch)
            else:
                codes[r * 8 + fcol] = CODE[ch]
                fcol += 1
        b = boards[32 * i:32 * i + 32]
        got = [(b[s >> 1] >> 4) if s & 1 else (b[s >> 1] & 15) for s in range(64)]
        bad["board"] += got != codes
        bad["side"] += (metas[i] & 1) != (side == "b")
        bad["score"] += scores[i] != int(cp)
        bad["result"] += ((metas[i] >> 1) & 3) != {"0.0": 0, "0.5": 1, "1.0": 2}[res]
        count += 1
print(f"{pos_path}: n={n}, compared {count} records with {txt_path}; mismatches {bad}")
print("POS == TEXT" if count == m and not any(bad.values()) else "MISMATCH")
