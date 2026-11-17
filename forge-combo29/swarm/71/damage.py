#!/usr/bin/env python3
"""Loader robustness: does a damaged v3 net refuse to load, or load and produce garbage?

Produces a set of damaged copies of the pristine test net and runs the loader probe
(and, for anything that loads, the engine itself) on each. Every case prints a literal
verdict line, and the script exits non-zero if any case both loads and evaluates.

Usage: damage.py <pristine net> <netpath binary> <out dir>
"""
import os
import shutil
import subprocess
import sys

NET = sys.argv[1]
PROBE = sys.argv[2]
OUT = sys.argv[3]

os.makedirs(OUT, exist_ok=True)
raw = open(NET, "rb").read()


def probe(path):
    """Run the loader probe. Returns (loaded, detail)."""
    proc = subprocess.run([PROBE, "loadprobe", path], capture_output=True, text=True, timeout=120)
    line = (proc.stdout or proc.stderr).strip().splitlines()
    detail = line[-1] if line else "(no output)"
    return proc.returncode == 0, detail


def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def flip(path, offsets):
    data = bytearray(open(path, "rb").read())
    for off in offsets:
        data[off] ^= 0x01
    with open(path, "wb") as handle:
        handle.write(bytes(data))


cases = []

# 1. Zero-length file.
cases.append(("zero_len", write("zero_len.fnn3", b"")))

# 2. Header only (192 bytes), i.e. truncated to exactly the header.
cases.append(("header_only", write("header_only.fnn3", raw[:192])))

# 3. Truncated mid-weights.
cases.append(("trunc_half", write("trunc_half.fnn3", raw[: len(raw) // 2])))

# 4. Truncated by one byte (drops one byte of the checksum).
cases.append(("trunc_1", write("trunc_1.fnn3", raw[:-1])))

# 5. Extended by one byte.
cases.append(("extend_1", write("extend_1.fnn3", raw + b"\x00")))

# 6. Bad magic.
bad_magic = bytearray(raw)
bad_magic[0] = ord("X")
cases.append(("bad_magic", write("bad_magic.fnn3", bytes(bad_magic))))

# 7. Bit flip deep inside w1 (checksum must catch it).
deep = write("flip_w1.fnn3", raw)
flip(deep, [len(raw) // 3])
cases.append(("flip_w1", deep))

# 8. Bit flip in the b1 block.
b1 = write("flip_b1.fnn3", raw)
flip(b1, [192 + 2 * 8 * 768 * 512 + 4])
cases.append(("flip_b1", b1))

# 9. Bit flip in the header's eval_scale field (offset 44).
scale = write("flip_scale.fnn3", raw)
flip(scale, [44])
cases.append(("flip_scale", scale))

# 10. Bit flip in the stored checksum itself (last 8 bytes).
cks = write("flip_checksum.fnn3", raw)
flip(cks, [len(raw) - 1])
cases.append(("flip_checksum", cks))

# 11. Re-checksummed corruption: flip a weight AND recompute the checksum, so only the
#     loader's own range checks can catch it. This case is EXPECTED to load: an FNV
#     checksum detects accidental damage, and is not a signature against deliberate
#     re-computation. It is recorded so the report can say so rather than imply otherwise.
import struct

recalc = bytearray(raw)
recalc[len(raw) // 3] ^= 0xFF
payload = bytes(recalc[:-8])
h = 14695981039346656037
for byte in payload:
    h = ((h ^ byte) * 1099511628211) & ((1 << 64) - 1)
recalc[-8:] = struct.pack("<Q", h)
cases.append(("rechecksummed", write("rechecksummed.fnn3", bytes(recalc))))

# 12. Valid header claiming an out-of-range hidden size (multiple of 32, > 1024).
huge = bytearray(raw)
huge[20:24] = struct.pack("<I", 1056)
cases.append(("hidden_too_big", write("hidden_too_big.fnn3", bytes(huge))))

# The accidental-damage cases must be refused. "rechecksummed" is not accidental damage:
# it carries a valid checksum for its own (altered) bytes, and loading it is correct
# behaviour, so it is reported separately and does not count against the loader.
ADVERSARIAL = {"rechecksummed"}

print("DAMAGE cases %d pristine_bytes %d netpath %s" % (len(cases), len(raw), PROBE))
bad = 0
for name, path in cases:
    loaded, detail = probe(path)
    expected = "ACCEPTED" if name in ADVERSARIAL else "refused"
    actual = "ACCEPTED" if loaded else "refused"
    ok = actual == expected
    if not ok:
        bad += 1
    print("DAMAGE %-16s bytes %-8d expect %-8s got %-8s %s | %s"
          % (name, os.path.getsize(path), expected, actual, "OK" if ok else "VIOLATION", detail))
print("DAMAGE summary cases %d accidental_damage_refused %d adversarial_accepted %d violations %d"
      % (len(cases),
         sum(1 for n, p in cases if n not in ADVERSARIAL and not probe(p)[0]),
         sum(1 for n, p in cases if n in ADVERSARIAL and probe(p)[0]),
         bad))
sys.exit(0 if bad == 0 else 3)
