#!/usr/bin/env python3
# Opus 2026-11-16 (file 7): deterministic FORGENN3 test net of the PC's shape. Verbatim.
import hashlib
import struct
import sys

MASK = (1 << 64) - 1
SEED = 20261116
HIDDEN, KB, OB = 512, 8, 8
KB_MAP = [0, 1, 2, 3, 3, 2, 1, 0, 4, 4, 5, 5, 5, 5, 4, 4] + [6] * 8 + [7] * 40
OB_MAP = [0] * 6 + [1] * 4 + [2] * 4 + [3] * 4 + [4] * 4 + [5] * 4 + [6] * 4 + [7] * 3


def stream(state):
    while True:
        state = (state + 0x9E3779B97F4A7C15) & MASK
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        yield z ^ (z >> 31)


def draw(g, n, lo, hi):
    span = hi - lo + 1
    return [lo + next(g) % span for _ in range(n)]


def main(out):
    assert len(KB_MAP) == 64 and len(OB_MAP) == 33
    g = stream(SEED)
    w1 = draw(g, KB * 768 * HIDDEN, -64, 64)
    b1 = draw(g, HIDDEN, -32, 96)
    w2 = draw(g, OB * 2 * HIDDEN, -16, 16)
    b2 = [0] * OB
    head = b"FORGENN3" + struct.pack("<IIIIIIIiii", 3, 192, 768, HIDDEN, KB, OB, 2, 255, 64, 400)
    head += bytes(KB_MAP) + bytes(OB_MAP) + bytes(47)
    assert len(head) == 192
    body = struct.pack("<%dh" % len(w1), *w1) + struct.pack("<%dh" % len(b1), *b1)
    body += struct.pack("<%dh" % len(w2), *w2) + struct.pack("<%di" % len(b2), *b2)
    data = head + body
    h = 14695981039346656037
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & MASK
    data += struct.pack("<Q", h)
    with open(out, "xb") as f:
        f.write(data)
    print("bytes", len(data), "fnv1a64", "%016x" % h, "sha256", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main(sys.argv[1])
