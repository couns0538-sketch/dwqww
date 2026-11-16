#!/usr/bin/env python3
"""runner.py - the ONE runner used for both the planted-fault proof and the real stress runs.

Usage: runner.py --exe PATH --inputs DIR --outdir DIR [--tag NAME]

Every file in --inputs ending in .uci is one whole UCI session (text lines, ending with quit).
Each session runs in its own process. Raw stdout/stderr are saved. The runner counts
  - sanitizer lines : 'ERROR: AddressSanitizer', 'ERROR: LeakSanitizer',
                      'WARNING: ThreadSanitizer', 'runtime error:'
  - crashes         : negative return code (killed by a signal) or a timeout (hang)
  - nonzero exits
and writes SUMMARY_<tag>.json with the exe path actually started, its sha256, its id name,
nm counts of __asan_ / __ubsan_, every session's events, and a date-utc stamp.
The SAME runner is used for the planted-fault engine and for the real engine: only --exe and
--inputs differ, which is what makes "0 sanitizer lines" on the real engine mean something.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

SAN_PATTERNS = [
    "ERROR: AddressSanitizer",
    "ERROR: LeakSanitizer",
    "WARNING: ThreadSanitizer",
    "runtime error:",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_sanitizer(text):
    n = 0
    kinds = {}
    for pat in SAN_PATTERNS:
        c = text.count(pat)
        if c:
            kinds[pat] = c
            n += c
    return n, kinds


def nm_count(exe, symbol):
    p = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in p.stdout.splitlines() if symbol in line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--env", default="", help="extra KEY=VAL;KEY=VAL for the child")
    args = ap.parse_args()

    exe = os.path.realpath(args.exe)
    os.makedirs(args.outdir, exist_ok=True)
    sessions = sorted(os.path.join(args.inputs, f) for f in os.listdir(args.inputs)
                      if f.endswith(".uci"))
    env = dict(os.environ)
    for pair in filter(None, args.env.split(";")):
        k, _, v = pair.partition("=")
        env[k] = v

    idname = ""
    try:
        p = subprocess.run([exe], input=b"uci\nquit\n", capture_output=True, timeout=120, env=env)
        m = re.search(rb"^id name (.*)$", p.stdout, re.M)
        if m:
            idname = m.group(1).decode(errors="replace").strip()
    except Exception as e:  # noqa: BLE001
        idname = "(uci identity failed: %s)" % e

    totals = {"sessions": 0, "crashes": 0, "hangs": 0, "san_lines": 0, "nonzero_exit": 0}
    by_kind = {}
    rows = []
    for s in sessions:
        totals["sessions"] += 1
        base = os.path.basename(s)[:-4]
        raw = os.path.join(args.outdir, base + ".out.txt")
        err = os.path.join(args.outdir, base + ".err.txt")
        with open(s, "rb") as f:
            payload = f.read()
        try:
            p = subprocess.run([exe], input=payload, capture_output=True,
                               timeout=args.timeout, env=env)
            out, errs, rc, hang = p.stdout, p.stderr, p.returncode, False
        except subprocess.TimeoutExpired as e:
            out = e.stdout or b""
            errs = e.stderr or b""
            rc, hang = None, True
            totals["hangs"] += 1
        with open(raw, "wb") as f:
            f.write(out)
        with open(err, "wb") as f:
            f.write(errs)
        text = out.decode(errors="replace") + "\n" + errs.decode(errors="replace")
        n, kinds = count_sanitizer(text)
        totals["san_lines"] += n
        for k, v in kinds.items():
            by_kind[k] = by_kind.get(k, 0) + v
        if n:
            print("SANITIZER %s: %s" % (base, kinds), flush=True)
        crashed = hang or (rc is not None and rc < 0)
        if crashed:
            totals["crashes"] += 1
        elif rc not in (0, None):
            totals["nonzero_exit"] += 1
        if crashed or n or rc not in (0, None):
            rows.append({"session": base, "rc": rc, "hang": hang, "san": n})

    meta = {
        "tag": args.tag,
        "exe_started": exe,
        "exe_sha256": sha256(exe),
        "id_name": idname,
        "nm_asan_symbols": nm_count(exe, "__asan_"),
        "nm_ubsan_symbols": nm_count(exe, "__ubsan_"),
        "inputs_dir": os.path.abspath(args.inputs),
        "input_sessions": len(sessions),
        "env_extra": args.env,
        "timeout_s": args.timeout,
        "totals": totals,
        "sanitizer_kinds": by_kind,
        "sessions_with_events": rows,
        "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                   capture_output=True, text=True).stdout.strip(),
    }
    with open(os.path.join(args.outdir, "SUMMARY_%s.json" % args.tag), "w") as f:
        json.dump(meta, f, indent=2)
    short = {k: meta[k] for k in ("tag", "exe_started", "exe_sha256", "id_name",
                                  "nm_asan_symbols", "nm_ubsan_symbols",
                                  "input_sessions", "totals", "sanitizer_kinds", "date_utc")}
    print(json.dumps(short, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
