#!/usr/bin/env python3
"""Broad sweep: mutate every header field to many values, always re-checksummed.

The hand-picked mutants test the guards I expected. This tests the space instead:
for each 4-byte header field, write a spread of values (0, 1, boundaries, random),
reseal the checksum, and ask the loader. Every case is classified by the loader's
own message, so a value that trips a guard I did not anticipate shows up as a
message with no matching hand-written case.

Two outcomes are of interest:
  * ACCEPTED for a field that must not vary -> a guard is missing
  * a crash, hang, or sanitizer line -> memory safety

Usage: header_sweep.py <probe> <pristine> <out.json> [--asan]
"""
import json
import struct
import subprocess
import sys

MASK = (1 << 64) - 1

# name -> byte offset, and the values worth trying for that field.
FIELDS = {
    "version":         (8,  [0, 1, 2, 3, 4, 0xFFFF, 0xFFFFFFFF]),
    "header_bytes":    (12, [0, 16, 191, 192, 193, 256, 4096, 0xFFFFFFFF]),
    "inputs":          (16, [0, 1, 767, 768, 769, 1536, 0xFFFFFFFF]),
    "hidden":          (20, [0, 16, 32, 31, 33, 512, 513, 544, 1024, 1023, 1056, 2048,
                             0x7FFFFFFF, 0xFFFFFFFF]),
    "king_buckets":    (24, [0, 1, 2, 8, 9, 31, 32, 33, 64, 0xFFFFFFFF]),
    "output_buckets":  (28, [0, 1, 8, 9, 15, 16, 17, 32, 0xFFFFFFFF]),
    "flags":           (32, [0, 1, 2, 3, 4, 8, 0x10, 0x80000000, 0xFFFFFFFF]),
    "qa":              (36, [0, 1, -1, 64, 254, 255, 256, 0x7FFFFFFF, -0x80000000]),
    "qb":              (40, [0, 1, -1, 32, 63, 64, 65, 0x7FFFFFFF, -0x80000000]),
    "eval_scale":      (44, [0, -1, 1, 400, 9999, 10000, 10001, 0x7FFFFFFF, -0x80000000]),
}

KING_MAP = (48, 64)      # 64 individual bytes
OUTPUT_MAP = (112, 33)   # 33 individual bytes
RESERVED = (145, 47)     # 47 individual bytes


def fnv1a(data):
    h = 14695981039346656037
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & MASK
    return h


def reseal(data):
    out = bytearray(data)
    out[-8:] = struct.pack("<Q", fnv1a(bytes(out[:-8])))
    return bytes(out)


def run(probe, path):
    proc = subprocess.run([probe, "load", path], capture_output=True, text=True, timeout=300)
    text = (proc.stdout + proc.stderr).strip()
    san = "AddressSanitizer" in text or "runtime error:" in text
    if proc.returncode == 0:
        return "ACCEPTED", text.splitlines()[-1] if text else "", san
    if proc.returncode == 1 and not san:
        detail = text.splitlines()[0].split("\t", 1)[-1] if text else ""
        return "REFUSED", detail, san
    return "OTHER(%s)" % proc.returncode, text[:200], san


def main():
    probe, pristine, outpath = sys.argv[1:4]
    raw = open(pristine, "rb").read()
    tmp = "/tmp/sweep_case.fnn3"
    results = []

    def case(field, value, offset):
        data = bytearray(raw)
        if field.endswith("[byte]"):
            data[offset] = value & 0xFF
        else:
            data[offset:offset + 4] = struct.pack("<I", value & 0xFFFFFFFF)
        path = tmp
        with open(path, "wb") as handle:
            handle.write(reseal(data))
        verdict, detail, san = run(probe, path)
        results.append({"field": field, "value": value, "offset": offset, "verdict": verdict,
                        "detail": detail, "sanitizer": san})
        return verdict

    for field, (offset, values) in FIELDS.items():
        for value in values:
            verdict = case(field, value, offset)
            if verdict == "ACCEPTED" and field not in ("flags",):
                print("!! ACCEPTED  %-16s %12d" % (field, value))

    # Byte fields: every value that could matter for each entry.
    for offset, count in (KING_MAP, OUTPUT_MAP, RESERVED):
        label = "king_map" if offset == KING_MAP[0] else ("output_map" if offset == OUTPUT_MAP[0] else "reserved")
        for index in range(count):
            for value in (0, 1, 7, 8, 15, 16, 31, 32, 33, 127, 128, 255):
                verdict = case(label + "[byte]", value, offset + index)
                if verdict == "ACCEPTED" and label != "reserved":
                    # in-range bucket entries are legal; only >= bucket count must refuse
                    pass
    print("cases", len(results))
    accepted = [r for r in results if r["verdict"] == "ACCEPTED"]
    san = [r for r in results if r["sanitizer"]]
    print("accepted", len(accepted), "sanitizer", len(san))
    for r in san[:10]:
        print("SAN", r["field"], r["value"], r["detail"][:120])
    with open(outpath, "w") as handle:
        json.dump(results, handle, indent=1)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
