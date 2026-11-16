#!/usr/bin/env python3
"""seat 17 area 7 job 1: ASan+UBSan run over a position set.

usage: run_asan.py <exe> <epd> <first> <count> <depth> <outdir> [extra-setoption-lines...]

Writes outdir/run.meta, outdir/results.json, outdir/sanitizer_lines.txt, outdir/one_<i>.log.
A crash, a timeout, a missing bestmove and every sanitizer word are collected.
"""
import hashlib
import json
import os
import subprocess
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_driver import run_one

SAN_WORDS = (
    "AddressSanitizer",
    "runtime error:",
    "UndefinedBehaviorSanitizer",
    "LeakSanitizer",
    "SEGV",
    "stack-overflow",
    "heap-buffer-overflow",
    "stack-buffer-overflow",
    "SUMMARY: ",
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe):
    try:
        proc = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=30)
        for line in proc.stdout.splitlines():
            if line.startswith("id name "):
                return line[8:]
    except Exception as exc:  # noqa: BLE001 - recorded, not raised
        return "id lookup failed: %r" % (exc,)
    return "no id name"


def sanitizer_symbol_count(exe):
    proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in proc.stdout.splitlines()
               if "__asan_" in line or "__ubsan_" in line or "__tsan_" in line)


def main():
    exe, epd, first, count, depth, outdir = sys.argv[1:7]
    extra = sys.argv[7:]
    first, count, depth = int(first), int(count), int(depth)
    os.makedirs(outdir, exist_ok=True)
    with open(epd) as handle:
        fens = [line.split(";")[0].strip() for line in handle if line.strip()]
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"
    env.pop("TSAN_OPTIONS", None)

    meta = {
        "exe": exe,
        "sha256": sha256(exe),
        "id_name": id_name(exe),
        "sanitizer_symbols": sanitizer_symbol_count(exe),
        "setoption_lines": extra,
        "epd": epd,
        "first": first,
        "count": count,
        "depth": depth,
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    results = []
    san_lines = []
    for offset in range(count):
        index = first + offset
        if index < 1 or index > len(fens):
            continue
        fen = fens[index - 1]
        commands = ["uci", "isready"] + list(extra) + ["isready", "position fen " + fen, "go depth %d" % depth]
        log_path = os.path.join(outdir, "one_%d.log" % index)
        info = run_one(exe, commands, 180, log_path, env=env)
        text = open(log_path).read()
        bad = [word for word in SAN_WORDS if word in text]
        info.update({"index": index, "fen": fen, "sanitizer_words": bad})
        results.append(info)
        if bad:
            san_lines.append("line %d: %s | %s" % (index, fen, ",".join(bad)))
        if info["rc"] != 0 and info["rc"] is not None:
            san_lines.append("line %d: exit %s | %s" % (index, info["rc"], fen))
        if info["bestmove"] is None:
            san_lines.append("line %d: NO bestmove | %s" % (index, fen))

    meta["searches"] = len(results)
    meta["sanitizer_lines"] = len(san_lines)
    meta["date_end"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(outdir, "results.json"), "w") as handle:
        json.dump(results, handle, indent=1)
    with open(os.path.join(outdir, "sanitizer_lines.txt"), "w") as handle:
        handle.write("\n".join(san_lines) + ("\n" if san_lines else ""))
    with open(os.path.join(outdir, "run.meta"), "w") as handle:
        json.dump(meta, handle, indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
