#!/usr/bin/env python3
"""fl_fuzz.py - Opus R14-B: feed the fast loader damaged binpack files; it must never crash or hang (own code).

usage: python -I -B fl_fuzz.py --dll forge_fastloader.dll --binpack <real .binpack> --out NEW_DIR
       [--chunks 3] [--flips 20] [--seed 20261102] [--timeout 60] [--mask 0xC]

Cuts the first --chunks chunks of a real binpack into OUT/base.binpack (read-only on the source), writes seeded damaged
copies (empty file, short header, header only, wrong magic, chunk size 0 / smaller than a record / not a multiple of a
record / over 100 MiB / past the end, truncation at random offsets, random byte flips inside records, a duplicated
chunk) and runs each through `fl_equal.py dump --loader fast` in its own process (finite stream, batch 1024, window
4096, up to 4 batches; a cyclic run for the cases that must still yield batches). Outcome per case: ok (batches),
error (exit 1 with a "fast loader:" message), CRASH (a Windows exception exit code), HANG (no exit within --timeout,
the case's own child is then terminated), or OTHER. Writes OUT/cases.tsv and OUT/summary.txt; exit 1 when any case
is CRASH / HANG / OTHER, else 0. All processes run at BelowNormal on --mask (inherited from this driver).
"""
import argparse
import ctypes
import os
import random
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = 34


def pin_self(mask):
    if os.name != "nt":
        return
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, 0x4000) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
        raise OSError(ctypes.get_last_error(), "pin")


def read_chunks(path, n):
    chunks = []
    with open(path, "rb") as fh:
        for _ in range(n):
            hdr = fh.read(8)
            if len(hdr) < 8 or hdr[:4] != b"BINP":
                break
            size = struct.unpack("<I", hdr[4:])[0]
            body = fh.read(size)
            if len(body) != size:
                break
            chunks.append(body)
    return chunks


def pack(chunks, sizes=None, magic=b"BINP"):
    out = bytearray()
    for i, c in enumerate(chunks):
        size = len(c) if sizes is None or sizes[i] is None else sizes[i]
        out += magic + struct.pack("<I", size & 0xFFFFFFFF) + c
    return bytes(out)


def cases(chunks, rng, flips):
    base = pack(chunks)
    c0 = chunks[0]
    yield "empty", b"", "error"
    yield "short_header", base[:7], "error"
    yield "header_only", base[:8], "error"
    yield "magic_first", b"BINX" + base[4:], "error"
    yield "magic_second", pack(chunks[:1]) + pack(chunks[1:], magic=b"XINP"), "error"
    yield "size_zero", pack([b""] + chunks[1:]), "error"
    yield "size_below_record", pack([c0[:10]] + chunks[1:]), "error"
    yield "size_partial_tail", pack([c0[:len(c0) - 5]] + chunks[1:]), "ok"  # documented: a partial tail is skipped
    yield "size_over_100mib", b"BINP" + struct.pack("<I", 100 * 2 ** 20 + 1) + c0, "error"
    yield "size_past_end", b"BINP" + struct.pack("<I", len(c0) + 1000) + c0, "error"
    yield "chunk_boundary_cut", pack(chunks[:1]), "ok"
    yield "duplicated_chunk", pack([c0, c0] + chunks[1:]), "ok"
    # every score = VALUE_NONE: the skip filter keeps nothing. Finite: 0 batches. Cyclic waits forever - in the old
    # loader too (checked 2026-11-02 20:51), so it is a property of the design, documented, and not run here.
    none = [bytearray(c) for c in chunks]
    for c in none:
        for off in range(0, len(c) - RECORD + 1, RECORD):
            c[off + 26:off + 28] = b"\xfa\x04"  # zigzag(32002), big-endian
    yield "all_value_none_finite", pack([bytes(c) for c in none]), "finite-ok"
    for k in range(10):
        cut = rng.randrange(9, len(base))
        yield f"truncated_{k}_at_{cut}", base[:cut], "any"
    for k in range(flips):
        b = bytearray(base)
        for _ in range(rng.choice((1, 4, 32))):
            ci = rng.randrange(len(chunks))
            start = 8 * (ci + 1) + sum(len(c) for c in chunks[:ci])
            pos = start + rng.randrange(len(chunks[ci]))
            b[pos] = rng.randrange(256)
        yield f"flip_{k}", bytes(b), "any"


def run_case(a, path, finite, out_tsv):
    # fl_equal.py needs only the standard library: run the BASE interpreter, not a venv's python.exe (a launcher that
    # starts the interpreter as its own child - a kill after a timeout would end the launcher and orphan the loader)
    py = getattr(sys, "_base_executable", None) or sys.executable
    cmd = [py, "-I", "-B", os.path.join(HERE, "fl_equal.py"), "dump", "--loader", "fast", "--dll", a.dll,
           "--workers", "3", "--data", path, "--batches", "4", "--batch", "1024", "--window", "4096", "--no-hash",
           "--out", out_tsv, "--mask", a.mask, "--priority", "BelowNormal"] + (["--finite"] if finite else [])
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        so, se = p.communicate(timeout=a.timeout)
    except subprocess.TimeoutExpired:
        p.kill()  # our own child only
        so, se = p.communicate()
        return "HANG", f"no exit within {a.timeout} s", time.monotonic() - t0
    err = se.decode("utf-8", "replace").strip().splitlines()
    rc = p.returncode
    if rc == 0:
        n = sum(1 for line in open(out_tsv, encoding="utf-8") if line[:1].isdigit()) if os.path.exists(out_tsv) else 0
        return "ok", f"{n} batches", time.monotonic() - t0
    if rc < 0 or rc >= 0xC0000000:
        return "CRASH", f"exit code 0x{rc & 0xFFFFFFFF:08X}", time.monotonic() - t0
    msg = next((line for line in reversed(err) if "fast loader:" in line), "")
    if rc == 1 and msg:
        return "error", msg[msg.find("fast loader:"):][:160], time.monotonic() - t0
    return "OTHER", f"exit {rc}: {(err[-1] if err else '')[:160]}", time.monotonic() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dll", required=True)
    ap.add_argument("--binpack", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunks", type=int, default=3)
    ap.add_argument("--flips", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--mask", default="0xC")
    a = ap.parse_args()
    if os.path.exists(a.out):
        ap.error(f"--out {a.out} exists")
    pin_self(int(a.mask, 16))
    chunks = read_chunks(a.binpack, a.chunks)
    if len(chunks) < 2:
        ap.error("need at least 2 whole chunks from --binpack")
    os.makedirs(os.path.join(a.out, "cases"))
    with open(os.path.join(a.out, "base.binpack"), "xb") as fh:
        fh.write(pack(chunks))
    rng = random.Random(a.seed)
    rows, bad = [], 0
    for name, data, expect in cases(chunks, rng, a.flips):
        path = os.path.join(a.out, "cases", name + ".binpack")
        with open(path, "xb") as fh:
            fh.write(data)
        res = []
        for finite in ((True, False) if expect == "ok" else (True,)):
            tag = "finite" if finite else "cyclic"
            outcome, detail, sec = run_case(a, path, finite, os.path.join(a.out, "cases", f"{name}.{tag}.tsv"))
            res.append((tag, outcome, detail, sec))
            want = "ok" if expect == "finite-ok" else expect
            if outcome in ("CRASH", "HANG", "OTHER") or (want != "any" and outcome != want):
                bad += 1
        for tag, outcome, detail, sec in res:
            rows.append(f"{name}\t{len(data)}\t{expect}\t{tag}\t{outcome}\t{sec:.1f}\t{detail}")
            print(f"{name:28s} {tag:6s} expect {expect:5s} -> {outcome:5s} {sec:5.1f} s  {detail}", flush=True)
    with open(os.path.join(a.out, "cases.tsv"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write("case\tbytes\texpect\tmode\toutcome\tseconds\tdetail\n" + "\n".join(rows) + "\n")
    summary = (f"fl_fuzz {time.strftime('%Y-%m-%d %H:%M:%S')}: {len(rows)} runs over the first {len(chunks)} chunks of "
               f"{a.binpack} ({sum(len(c) for c in chunks)} bytes), DLL {a.dll}; unexpected outcomes: {bad}")
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write(summary + "\n")
    print(summary)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
