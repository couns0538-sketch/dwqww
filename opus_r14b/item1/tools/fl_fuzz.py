#!/usr/bin/env python3
"""fl_fuzz.py - Opus R14-B: feed the fast loader damaged binpack files; it must never crash or hang, and whatever it
loads must be what the default loader loads (own code).

usage: python -I -B fl_fuzz.py --dll forge_fastloader.dll --old-dll <copy of libtraining_data_loader.dll>
       --binpack <real .binpack> --out NEW_DIR [--chunks 3] [--flips 20] [--seed 20261102] [--timeout 60]
       [--mask 0xC] [--min-free-gb 50]

Cuts the first --chunks chunks of a real binpack into OUT/base.binpack (read-only on the source), writes seeded damaged
copies (empty file, short header, header only, wrong magic, chunk size 0 / smaller than a record / not a multiple of a
record / over 100 MiB / past the end, truncation at random offsets, random byte flips inside records, a duplicated
chunk, a file whose every score is VALUE_NONE) and runs each through `fl_equal.py dump --loader fast` in its own
process (finite stream, batch 1024, window 4096, up to 4 batches, hashed; a cyclic run too for the cases that must
still yield batches). Outcome per run: ok (exit 0 with at least one batch), empty (exit 0 with no batch - a failure
except for the VALUE_NONE file, whose skip filter keeps nothing by design), error (exit 1 with a "fast loader:"
message), CRASH (a Windows exception exit code), HANG (no exit within --timeout; the run's own child is then ended),
or OTHER.
Every run the fast loader completes (ok / empty) is repeated with the default loader (`--loader old --workers 1`, the
deterministic stream the fast loader reproduces; same file, mode, batch and window) and the two dumps are compared
with `fl_equal.py compare`. Identity: same (every batch bit-identical), same-empty (no batch in either), DIFF,
incomparable (compare refused), or old-<outcome> (the default loader did not give the same kind of result).
Writes OUT/cases.tsv and OUT/summary.txt. Exit 0 = every fast run as expected and every identity same / same-empty;
1 = a fast run unexpected, an identity mismatch, or the run stopped at the disk floor; 2 = wrong arguments (checked
before anything is read, pinned or written). Disk: the drive of --out keeps --min-free-gb GiB free - checked before the
first write against the whole run's size and again before every case. --flips is capped at 1000. All processes run at
BelowNormal on --mask (set on this driver first, inherited by every child).
Code Review fixes 2026-11-03: the comparison with the default loader, the "empty" outcome, the disk floor, the --flips
cap and the argument checks are new (before: a run with exit 0 and no batch counted as "ok").
"""
import argparse
import ctypes
import os
import random
import shutil
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = 34
FLIPS_MAX = 1000  # each flip case = one copy of the base file + up to two loader runs
GIB = 1024 ** 3  # GB as the PC's disk tools count them (pc_gate.ps1 divides by 1GB = 2^30)
DUMP_BYTES = 4096  # generous size of one hashed 4-batch dump
PY = getattr(sys, "_base_executable", None) or sys.executable
# fl_equal.py needs only the standard library: run the BASE interpreter, not a venv's python.exe (a launcher that
# starts the interpreter as its own child - a kill after a timeout would end the launcher and orphan the loader)


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
    # every score = VALUE_NONE: the skip filter keeps nothing. Finite: 0 batches by design (the only "empty" case).
    # Cyclic waits forever - in the old loader too (checked 2026-11-02 20:51), so it is not run here.
    none = [bytearray(c) for c in chunks]
    for c in none:
        for off in range(0, len(c) - RECORD + 1, RECORD):
            c[off + 26:off + 28] = b"\xfa\x04"  # zigzag(32002), big-endian
    yield "all_value_none_finite", pack([bytes(c) for c in none]), "empty"
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


def classify(loader, rc, batches, err):
    """(outcome, detail) of a finished run; batches = batch rows in its dump (None: no dump). HANG is the caller's."""
    if rc == 0:
        if batches is None:
            return "OTHER", "exit 0 without a dump"
        return ("ok" if batches else "empty"), f"{batches} batches"
    if rc < 0 or rc >= 0xC0000000:
        return "CRASH", f"exit code 0x{rc & 0xFFFFFFFF:08X}"
    last = (err[-1] if err else "")[:160]
    if loader == "old":  # the default loader has no error contract: any other exit is an error with its last line
        return "error", f"exit {rc}: {last}"
    msg = next((line for line in reversed(err) if "fast loader:" in line), "")
    if rc == 1 and msg:
        return "error", msg[msg.find("fast loader:"):][:160]
    return "OTHER", f"exit {rc}: {last}"


def acceptable(expect, outcome):
    """Is the fast loader's outcome what the case expects? 'any' = ok or error; 'empty' only where expected."""
    if outcome in ("CRASH", "HANG", "OTHER"):
        return False
    return outcome in ("ok", "error") if expect == "any" else outcome == expect


def identity(fast, old, compare_rc):
    """Fast vs default loader for one completed fast run (compare_rc: fl_equal.py compare's exit, both ok only)."""
    if fast == "ok" and old == "ok":
        return {0: "same", 1: "DIFF"}.get(compare_rc, "incomparable")
    if fast == "empty" and old == "empty":
        return "same-empty"
    return f"old-{old}"


def identity_ok(verdict):
    return verdict in ("same", "same-empty")


def disk_short(path, need_bytes, floor_gb):
    """'' when the drive of path keeps floor_gb GiB free after need_bytes more, else the reason."""
    free = shutil.disk_usage(os.path.dirname(os.path.abspath(path)) or ".").free
    if free - need_bytes >= floor_gb * GIB:
        return ""
    return (f"disk floor: {free / GIB:.1f} GB free on the drive of {path}, {need_bytes / GIB:.2f} GB needed, "
            f"{floor_gb:g} GB must stay free")


def count_batches(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line[:1].isdigit())


def run_dump(a, loader, dll, workers, path, finite, out_tsv):
    """One fl_equal.py dump in its own process -> (outcome, detail, seconds)."""
    cmd = [PY, "-I", "-B", os.path.join(HERE, "fl_equal.py"), "dump", "--loader", loader, "--dll", dll,
           "--workers", str(workers), "--data", path, "--batches", "4", "--batch", "1024", "--window", "4096",
           "--out", out_tsv, "--mask", a.mask, "--priority", "BelowNormal"] + (["--finite"] if finite else [])
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _, se = p.communicate(timeout=a.timeout)
    except subprocess.TimeoutExpired:
        p.kill()  # our own child only
        p.communicate()
        return "HANG", f"no exit within {a.timeout} s", time.monotonic() - t0
    err = se.decode("utf-8", "replace").strip().splitlines()
    outcome, detail = classify(loader, p.returncode, count_batches(out_tsv) if p.returncode == 0 else None, err)
    return outcome, detail, time.monotonic() - t0


def compare(fast_tsv, old_tsv):
    p = subprocess.run([PY, "-I", "-B", os.path.join(HERE, "fl_equal.py"), "compare", fast_tsv, old_tsv],
                       capture_output=True, text=True, errors="replace")
    first = (p.stdout.strip().splitlines() or [""])[0]
    return p.returncode, first[first.find("compared"):] if "compared" in first else first[-160:]


def check_args(a):
    problems = [f"{what} {path}: file not found" for path, what in
                ((a.dll, "--dll"), (a.old_dll, "--old-dll"), (a.binpack, "--binpack")) if not os.path.isfile(path)]
    if os.path.exists(a.out) or not os.path.isdir(os.path.dirname(os.path.abspath(a.out))):
        problems.append(f"--out {a.out}: exists or its folder is missing (outputs are never overwritten)")
    if a.chunks < 2:
        problems.append(f"--chunks {a.chunks}: at least 2 (the damaged copies need a second chunk)")
    if not 0 <= a.flips <= FLIPS_MAX:
        problems.append(f"--flips {a.flips}: must be 0..{FLIPS_MAX} (each flip is a copy of the base file and up to "
                        "two loader runs)")
    if a.timeout < 1:
        problems.append("--timeout must be at least 1 second")
    if a.min_free_gb < 0:
        problems.append("--min-free-gb must not be negative")
    try:
        mask = int(a.mask, 16)
    except ValueError:
        mask = 0
    if mask <= 0:
        problems.append(f"--mask {a.mask!r} is not a hexadecimal CPU mask naming at least one CPU")
    if not problems:
        short = disk_short(a.out, 0, a.min_free_gb)  # already below the floor: nothing is written at all
        if short:
            problems.append(short)
    return problems, mask


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dll", required=True, help="the fast loader DLL under test")
    ap.add_argument("--old-dll", required=True, help="a COPY of the default loader DLL (libtraining_data_loader.dll)")
    ap.add_argument("--binpack", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunks", type=int, default=3)
    ap.add_argument("--flips", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--mask", default="0xC")
    ap.add_argument("--min-free-gb", type=float, default=50.0, help="GiB the drive of --out keeps free (PC rule)")
    a = ap.parse_args()
    problems, mask = check_args(a)
    if problems:
        print("fl_fuzz: " + "\nfl_fuzz: ".join(problems), file=sys.stderr)
        return 2
    chunks = read_chunks(a.binpack, a.chunks)
    if len(chunks) < 2:
        print(f"fl_fuzz: --binpack {a.binpack}: need at least 2 whole chunks", file=sys.stderr)
        return 2
    base = pack(chunks)
    plan = list((name, len(data), expect) for name, data, expect in cases(chunks, random.Random(a.seed), a.flips))
    runs = sum(4 if expect == "ok" else 2 for _, _, expect in plan)  # fast + old per mode
    need = len(base) + sum(size for _, size, _ in plan) + runs * DUMP_BYTES
    short = disk_short(a.out, need, a.min_free_gb)
    if short:
        print(f"fl_fuzz: {short} ({len(plan)} cases)", file=sys.stderr)
        return 2
    try:
        pin_self(mask)
    except OSError as e:  # e.g. a mask naming CPUs this PC does not have
        print(f"fl_fuzz: --mask {a.mask}: cannot pin this process ({e}); nothing was written", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(a.out, "cases"))
    with open(os.path.join(a.out, "base.binpack"), "xb") as fh:
        fh.write(base)
    rows, unexpected, mismatched, stopped = [], [], [], ""
    for name, data, expect in cases(chunks, random.Random(a.seed), a.flips):
        short = disk_short(a.out, len(data) + 4 * DUMP_BYTES, a.min_free_gb)
        if short:
            stopped = f"stopped before case {name}: {short}"
            print(stopped, flush=True)
            break
        path = os.path.join(a.out, "cases", name + ".binpack")
        with open(path, "xb") as fh:
            fh.write(data)
        for finite in ((True, False) if expect == "ok" else (True,)):
            mode = "finite" if finite else "cyclic"
            stem = os.path.join(a.out, "cases", f"{name}.{mode}")
            fast, fdet, fsec = run_dump(a, "fast", a.dll, 3, path, finite, stem + ".fast.tsv")
            old, odet, osec, ident = "-", "", 0.0, "-"
            if not acceptable(expect, fast):
                unexpected.append(f"{name} {mode} {fast}")
            if fast in ("ok", "empty"):
                old, odet, osec = run_dump(a, "old", a.old_dll, 1, path, finite, stem + ".old.tsv")
                rc, cdet = compare(stem + ".fast.tsv", stem + ".old.tsv") if fast == old == "ok" else (None, "")
                ident = identity(fast, old, rc)
                odet = cdet or odet
                if not identity_ok(ident):
                    mismatched.append(f"{name} {mode} {ident}")
            rows.append(f"{name}\t{len(data)}\t{expect}\t{mode}\t{fast}\t{fsec:.1f}\t{fdet}\t{old}\t{osec:.1f}\t"
                        f"{ident}\t{odet}")
            print(f"{name:28s} {mode:6s} expect {expect:5s} -> fast {fast:5s} {fsec:5.1f} s  {fdet[:60]:60s} | old "
                  f"{old:5s} {osec:5.1f} s  identity {ident}", flush=True)
    with open(os.path.join(a.out, "cases.tsv"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write("case\tbytes\texpect\tmode\tfast\tfast_s\tfast_detail\told\told_s\tidentity\tdetail\n"
                 + "\n".join(rows) + "\n")
    counts = {}
    for row in rows:
        f = row.split("\t")
        counts[f"fast {f[4]}"] = counts.get(f"fast {f[4]}", 0) + 1
        if f[9] != "-":
            counts[f"identity {f[9]}"] = counts.get(f"identity {f[9]}", 0) + 1
    lines = [f"fl_fuzz {time.strftime('%Y-%m-%d %H:%M:%S')}: {len(rows)} runs over the first {len(chunks)} chunks of "
             f"{a.binpack} ({sum(len(c) for c in chunks)} bytes), seed {a.seed}, flips {a.flips}",
             f"fast DLL {a.dll}; default-loader DLL {a.old_dll}",
             "counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
             f"fast runs not as expected: {len(unexpected)}" + (": " + "; ".join(unexpected) if unexpected else ""),
             f"identity not same / same-empty: {len(mismatched)}" + (": " + "; ".join(mismatched) if mismatched else "")]
    if stopped:
        lines.append(stopped)
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if unexpected or mismatched or stopped else 0


if __name__ == "__main__":
    sys.exit(main())
