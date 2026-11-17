"""Make two minimal, VALID v3 network files so the loader path can be tested.

Format is read straight out of src/nnue_v3.cpp:load (base 6b98f217):
  header 192 bytes: magic "FORGENN3", u32 version=3, u32 header_bytes=192,
  u32 inputs=768, u32 hidden, u32 king_buckets, u32 output_buckets, u32 flags,
  i32 qa=255, i32 qb=64, i32 eval_scale, u8 king_map[64], u8 output_map[33],
  zero to 192; then w1 (i16, king_buckets*768*hidden), b1 (i16, hidden),
  w2 (i16, output_buckets*2*hidden), b2 (i32, output_buckets); then an
  fnv1a64 over everything before it, little endian.

hidden=32, king_buckets=1, output_buckets=1 -> ~50 KB, so the file is small
enough to commit as evidence. NOT residual (bit 0 clear) because the loader
refuses residual v3 nets outright.

Two nets that differ in their weights by a large factor, so "which net did the
engine use" is answerable from a score rather than from a log line alone.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "evidence", "nets")

HEADER = 192
INPUTS = 768
HIDDEN = 32
KING_BUCKETS = 1
OUTPUT_BUCKETS = 1
QA, QB = 255, 64


def fnv1a64(data):
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def build(scale):
    """scale multiplies every weight; the accumulator guard is checked here too."""
    w1 = [max(-200, min(200, int(round(scale * (i % 17 - 8))))) for i in range(KING_BUCKETS * INPUTS * HIDDEN)]
    b1 = [int(round(scale * (i % 5 - 2))) for i in range(HIDDEN)]
    w2 = [max(-127, min(127, int(round(scale * (i % 7 - 3))))) for i in range(OUTPUT_BUCKETS * 2 * HIDDEN)]
    b2 = [int(round(scale * 4)) for _ in range(OUTPUT_BUCKETS)]
    max_w1, max_b1, max_w2 = max(map(abs, w1)), max(map(abs, b1)), max(map(abs, w2))
    assert max_w2 <= 127, max_w2
    assert max_b1 + 32 * max_w1 <= 32767, (max_b1, max_w1)
    head = bytearray(HEADER)
    head[0:8] = b"FORGENN3"
    struct.pack_into("<I", head, 8, 3)
    struct.pack_into("<I", head, 12, HEADER)
    struct.pack_into("<I", head, 16, INPUTS)
    struct.pack_into("<I", head, 20, HIDDEN)
    struct.pack_into("<I", head, 24, KING_BUCKETS)
    struct.pack_into("<I", head, 28, OUTPUT_BUCKETS)
    struct.pack_into("<I", head, 32, 0)          # flags: standalone
    struct.pack_into("<i", head, 36, QA)
    struct.pack_into("<i", head, 40, QB)
    struct.pack_into("<i", head, 44, 400)        # eval_scale
    for i in range(64):
        head[48 + i] = 0
    for i in range(33):
        head[112 + i] = 0
    body = bytes(head)
    body += struct.pack(f"<{len(w1)}h", *w1)
    body += struct.pack(f"<{len(b1)}h", *b1)
    body += struct.pack(f"<{len(w2)}h", *w2)
    body += struct.pack(f"<{len(b2)}i", *b2)
    body += struct.pack("<Q", fnv1a64(body))
    return body


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = {}
    for name, scale in (("v3a", 1.0), ("v3b", 4.0)):
        p = os.path.join(OUT, f"{name}.bin")
        with open(p, "wb") as fh:
            fh.write(build(scale))
        paths[name] = p
        print(name, os.path.getsize(p), "bytes")
    # A deliberately corrupt copy: flips one weight byte after the checksum was made.
    bad = bytearray(open(paths["v3a"], "rb").read())
    bad[HEADER + 7] ^= 0xFF
    badp = os.path.join(OUT, "v3a-corrupt.bin")
    open(badp, "wb").write(bytes(bad))
    print("corrupt", os.path.getsize(badp), "bytes")
    # A residual net: same body, flags bit 0 set, checksum recomputed, so the ONLY
    # reason it is refused is the residual rule.
    res = bytearray(open(paths["v3a"], "rb").read())
    struct.pack_into("<I", res, 32, 1)
    res[-8:] = struct.pack("<Q", fnv1a64(bytes(res[:-8])))
    resp = os.path.join(OUT, "v3a-residual.bin")
    open(resp, "wb").write(bytes(res))
    print("residual", os.path.getsize(resp), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
