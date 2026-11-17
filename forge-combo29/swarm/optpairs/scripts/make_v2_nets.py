"""Build two valid v2 (`FORGENET`) networks by re-scaling the shipped weights.

Format from src/nnue.cpp:load_file (base 6b98f217): magic "FORGENET", u32 version
= 1, u32 hidden = HiddenSize (256 in this build), then w1 (768*256 i16), b1 (256
i16), w2 (2*256 i16), b2 (i16). File size must equal kNetBytes, computed there as
16 + 2*(768*hidden + hidden + 2*hidden + 1).

Two nets, so "which net is loaded" is answerable from an eval:
  v2zero  every weight 0        -> the network contributes nothing
  v2double w1 doubled, w2 same  -> a different correction from the same features

The shipped net is residual (`FORGE_NNUE_RESIDUAL 1`), so eval = hand-crafted +
network; a zero net therefore pins eval to the HCE value, which is a check in it.
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "src", "nnue_weights.inc")
OUT = os.path.join(os.path.dirname(HERE), "evidence", "nets")
HID = 256


def arrays():
    text = open(SRC).read()

    def grab(name):
        m = re.search(rf"static const std::int16_t {name}\[(\d+)\] = \{{(.*?)\}};", text, re.S)
        return [int(x) for x in re.findall(r"-?\d+", m.group(2))]

    b2 = re.search(r"static const std::int16_t NnueB2 = (-?\d+);", text)
    return grab("NnueW1"), grab("NnueB1"), grab("NnueW2"), int(b2.group(1))


def write(name, w1, b1, w2, b2):
    body = bytearray()
    body += b"FORGENET"
    body += struct.pack("<I", 1)
    body += struct.pack("<I", HID)
    body += struct.pack(f"<{len(w1)}h", *w1)
    body += struct.pack(f"<{len(b1)}h", *b1)
    body += struct.pack(f"<{len(w2)}h", *w2)
    body += struct.pack("<h", b2)
    p = os.path.join(OUT, f"{name}.bin")
    with open(p, "wb") as fh:
        fh.write(bytes(body))
    print(name, len(body), "bytes")
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    w1, b1, w2, b2 = arrays()
    assert len(w1) == 768 * HID and len(b1) == HID and len(w2) == 2 * HID
    clamp = lambda v: max(-32767, min(32767, v))
    write("v2zero", [0] * len(w1), [0] * len(b1), [0] * len(w2), 0)
    write("v2double", list(w1), list(b1), [clamp(2 * v) for v in w2], b2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
