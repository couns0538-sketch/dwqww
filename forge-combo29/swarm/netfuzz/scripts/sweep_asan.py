#!/usr/bin/env python3
"""Sanitizer arm of the header sweep.

Same field/value space as header_sweep.py, but each mutant is written ONCE to a
directory and both probes read the same bytes, so the two arms cannot diverge and
the FNV reseal is computed once per case instead of once per arm.

Reports, per case: the release verdict and message, the ASan+UBSan verdict and
message, and any sanitizer diagnostic line. A nonzero sanitizer count anywhere in
this space is a memory-safety finding; zero is the clean bill.

Usage: sweep_asan.py <probe_rel> <probe_asan> <pristine> <outdir> <out.json> [--bytes]
  --bytes   also sweep the 64 king-map + 33 output-map + 47 reserved bytes
"""
import json
import os
import struct
import subprocess
import sys

MASK = (1 << 64) - 1

FIELDS = {
    "version":         (8,  [0, 1, 2, 3, 4, 0xFFFF, 0xFFFFFFFF]),
    "header_bytes":    (12, [0, 16, 191, 192, 193, 256, 4096, 0xFFFFFFFF]),
    "inputs":          (16, [0, 1, 767, 768, 769, 1536, 0xFFFFFFFF]),
    "hidden":          (20, [0, 16, 32, 31, 33, 512, 513, 544, 1024, 1023, 1056, 2048,
                             0x7FFFFFFF, 0xFFFFFFFF]),
    "king_buckets":    (24, [0, 1, 2, 8, 9, 31, 32, 33, 64, 0xFFFFFFFF]),
    "output_buckets":  (28, [0, 1, 8, 9, 15, 16, 17, 32, 0xFFFFFFFF]),
    "flags":           (32, [0, 1, 2, 3, 4, 8, 0x10, 0x80000000, 0xFFFFFFFF]),
    "qa":              (36, [0, 1, -1, 64, 254, 255, 256, 0x7FFFFFFF]),
    "qb":              (40, [0, 1, -1, 32, 63, 64, 65, 0x7FFFFFFF]),
    "eval_scale":      (44, [0, -1, 1, 400, 9999, 10000, 10001, 0x7FFFFFFF]),
}

BYTE_FIELDS = (("king_map", 48, 64), ("output_map", 112, 33), ("reserved", 145, 47))


def fnv1a(data):
    h = 14695981039346656037
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & MASK
    return h


def reseal(data):
    out = bytearray(data)
    out[-8:] = struct.pack("<Q", fnv1a(bytes(out[:-8])))
    return bytes(out)


def probe(path_bin, path_net):
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0"
    proc = subprocess.run([path_bin, "load", path_net], capture_output=True, text=True,
                          timeout=300, env=env)
    text = proc.stdout + proc.stderr
    san = [ln for ln in text.splitlines()
           if "AddressSanitizer" in ln or "runtime error:" in ln or "SUMMARY:" in ln]
    if proc.returncode == 0:
        verdict = "ACCEPTED"
    elif proc.returncode == 1 and not san:
        verdict = "REFUSED"
    else:
        verdict = "OTHER(%s)" % proc.returncode
    detail = ""
    for line in (proc.stdout or "").splitlines():
        if line.startswith(("REFUSED\t", "ACCEPTED\t")):
            detail = line.split("\t", 1)[1]
            break
    return {"verdict": verdict, "detail": detail, "sanitizer": san, "rc": proc.returncode}


def main():
    probe_rel, probe_asan, pristine, outdir, outpath = sys.argv[1:6]
    do_bytes = "--bytes" in sys.argv[6:]
    os.makedirs(outdir, exist_ok=True)
    raw = open(pristine, "rb").read()

    cases = []
    for field, (offset, values) in FIELDS.items():
        for value in values:
            data = bytearray(raw)
            data[offset:offset + 4] = struct.pack("<I", value & 0xFFFFFFFF)
            cases.append((field, value, offset, bytes(data)))
    if do_bytes:
        for label, offset, count in BYTE_FIELDS:
            for index in range(count):
                for value in (0, 1, 7, 8, 31, 32, 255):
                    data = bytearray(raw)
                    data[offset + index] = value
                    cases.append(("%s[%d]" % (label, index), value, offset + index, bytes(data)))

    results = []
    for index, (field, value, offset, data) in enumerate(cases):
        path = os.path.join(outdir, "c%04d.fnn3" % index)
        with open(path, "wb") as handle:
            handle.write(reseal(data))
        rel = probe(probe_rel, path)
        asan = probe(probe_asan, path)
        results.append({"field": field, "value": value, "offset": offset,
                        "rel": rel, "asan": asan,
                        "disagree": rel["verdict"] != asan["verdict"]})
        if rel["verdict"] != asan["verdict"] or asan["sanitizer"]:
            print("!! %-22s %12s rel %-8s asan %-8s san %d"
                  % (field, value, rel["verdict"], asan["verdict"], len(asan["sanitizer"])))
        os.unlink(path)

    san_total = sum(len(r["asan"]["sanitizer"]) for r in results)
    disagree = [r for r in results if r["disagree"]]
    print("cases %d  sanitizer_lines %d  verdict_disagreements %d" % (len(results), san_total, len(disagree)))
    with open(outpath, "w") as handle:
        json.dump({"cases": len(results), "sanitizer_lines": san_total,
                   "verdict_disagreements": len(disagree), "results": results}, handle, indent=1)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
