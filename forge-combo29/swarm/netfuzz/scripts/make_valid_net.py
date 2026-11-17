#!/usr/bin/env python3
"""A genuinely valid FORGENN3 net at chosen dimensions, for the amplification test.

The point is not to damage anything: it is to build a net whose header *and body*
agree at the largest dimensions the format allows, so we can measure

    allocated bytes / file bytes

and say whether a v3 net can be a decompression bomb on its own terms. If the
loader validates file size against the header before allocating, the ratio cannot
exceed a small constant no matter what the header claims.

Deterministic (splitmix64), so the bytes are reproducible.
Usage: make_valid_net.py <out> <hidden> <king_buckets> <output_buckets> [eval_scale]
"""
import struct
import sys

MASK = (1 << 64) - 1
SEED = 20261116


def stream(state):
    while True:
        state = (state + 0x9E3779B97F4A7C15) & MASK
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        yield z ^ (z >> 31)


def draw(gen, n, lo, hi):
    span = hi - lo + 1
    return [lo + next(gen) % span for _ in range(n)]


def main():
    out, hidden, kb, ob = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    scale = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    assert hidden % 32 == 0 and 32 <= hidden <= 1024
    assert 1 <= kb <= 32 and 1 <= ob <= 16

    # In-range bucket maps: king buckets spread over the 64 squares, output buckets
    # by piece count. Both must stay below their bucket counts or the loader refuses.
    kb_map = [min(kb - 1, i * kb // 64) for i in range(64)]
    ob_map = [min(ob - 1, i * ob // 33) for i in range(33)]

    gen = stream(SEED)
    w1 = draw(gen, kb * 768 * hidden, -64, 64)
    b1 = draw(gen, hidden, 0, 32)          # keep max|b1| + 32*max|w1| <= 32767
    w2 = draw(gen, ob * 2 * hidden, -16, 16)
    b2 = [0] * ob

    head = b"FORGENN3" + struct.pack("<IIIIIIIiii", 3, 192, 768, hidden, kb, ob, 0, 255, 64, scale)
    head += bytes(kb_map) + bytes(ob_map) + bytes(47)
    assert len(head) == 192, len(head)

    body = struct.pack("<%dh" % len(w1), *w1)
    body += struct.pack("<%dh" % len(b1), *b1)
    body += struct.pack("<%dh" % len(w2), *w2)
    body += struct.pack("<%di" % len(b2), *b2)
    data = bytearray(head + body)

    h = 14695981039346656037
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & MASK
    data += struct.pack("<Q", h)
    with open(out, "xb") as handle:
        handle.write(bytes(data))
    print("wrote %s bytes %d hidden %d king %d out %d" % (out, len(data), hidden, kb, ob))


if __name__ == "__main__":
    main()
