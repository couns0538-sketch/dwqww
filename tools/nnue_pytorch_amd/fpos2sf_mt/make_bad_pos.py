"""R7 J2 test helper: copy the first N records of an FPOS v1 file and plant bad records.
usage: python -I -B make_bad_pos.py <in.pos> <out.pos> [N=200000]
Planted (record index: defect): 10 nibble code 13; 20 two white kings; 30 no black king; 40 result bits = 3;
55000 nibble code 15; 123456 two black kings. Prints the planted list; the converter must skip exactly these 6."""
import struct
import sys

src, dst = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 200000
with open(src, "rb") as f:
    magic, ver, total = struct.unpack("<4sIQ", f.read(16))
    assert magic == b"FPOS" and ver == 1 and n <= total
    boards = bytearray(f.read(32 * n))
    f.seek(16 + 32 * total)
    scores = f.read(2 * n)
    f.seek(16 + 34 * total)
    metas = bytearray(f.read(n))


def code(b, i, s):
    v = b[i * 32 + (s >> 1)]
    return (v >> 4) if s & 1 else (v & 15)


def setc(b, i, s, c):
    k = i * 32 + (s >> 1)
    b[k] = (b[k] & 0x0F) | (c << 4) if s & 1 else (b[k] & 0xF0) | c


def find(b, i, c):
    return [s for s in range(64) if code(b, i, s) == c]


def empty(b, i):
    return [s for s in range(64) if code(b, i, s) == 0]


planted = []
setc(boards, 10, empty(boards, 10)[0], 13); planted.append((10, "nibble 13"))
setc(boards, 20, empty(boards, 20)[0], 6); planted.append((20, "two white kings"))
setc(boards, 30, find(boards, 30, 12)[0], 0); planted.append((30, "no black king"))
metas[40] = (metas[40] & 1) | (3 << 1); planted.append((40, "result bits 3"))
if n > 55000:
    setc(boards, 55000, empty(boards, 55000)[0], 15); planted.append((55000, "nibble 15"))
if n > 123456:
    setc(boards, 123456, empty(boards, 123456)[0], 12); planted.append((123456, "two black kings"))
with open(dst, "xb") as f:
    f.write(struct.pack("<4sIQ", b"FPOS", 1, n))
    f.write(boards)
    f.write(scores)
    f.write(metas)
print(f"wrote {dst}: {n} records, planted {len(planted)} bad: {planted}")
