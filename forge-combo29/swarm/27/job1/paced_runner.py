#!/usr/bin/env python3
"""paced_runner.py - feeds a UCI session line by line with a delay, so a search actually runs.

Why: if the whole session is written to stdin at once, the engine's main thread reads every
line immediately and each position/ucinewgame/setoption stops the search it just started, so
almost no search runs (that was my first stress run: 216 bestmoves, 39 info lines). This driver
writes one line, waits, and only sends the next after the engine has had time to work.

Rules kept: the exe path started and its sha256 are logged; a line naming a search is followed
by a pause long enough for that search; stdin is never closed before the session's quit.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

SAN_PATTERNS = ["ERROR: AddressSanitizer", "ERROR: LeakSanitizer",
                "WARNING: ThreadSanitizer", "runtime error:"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nm_count(exe, symbol):
    p = subprocess.run(["nm", "-C", exe], capture_output=True, text=True)
    return sum(1 for line in p.stdout.splitlines() if symbol in line)


def pause_for(line, base_pause):
    """How long to wait after this line."""
    s = line.strip()
    if s.startswith("go infinite"):
        return base_pause * 3
    if s.startswith("go "):
        return base_pause
    if s.startswith("setoption") or s.startswith("position") or s == "ucinewgame":
        return 0.02
    return 0.01


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--sessions", required=True, help="directory of .uci sessions")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tag", default="paced")
    ap.add_argument("--pause", type=float, default=0.35)
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--env", default="")
    args = ap.parse_args()

    exe = os.path.realpath(args.exe)
    os.makedirs(args.outdir, exist_ok=True)
    env = dict(os.environ)
    for pair in filter(None, args.env.split(";")):
        k, _, v = pair.partition("=")
        env[k] = v

    files = sorted(os.path.join(args.sessions, f) for f in os.listdir(args.sessions)
                   if f.endswith(".uci"))
    idname = ""
    p = subprocess.run([exe], input=b"uci\nquit\n", capture_output=True, timeout=180, env=env)
    m = re.search(rb"^id name (.*)$", p.stdout, re.M)
    if m:
        idname = m.group(1).decode(errors="replace").strip()

    totals = {"sessions": 0, "crashes": 0, "hangs": 0, "san_lines": 0, "nonzero_exit": 0,
              "bestmoves": 0, "info_lines": 0}
    by_kind = {}
    rows = []
    for path in files:
        base = os.path.basename(path)[:-4]
        with open(path) as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip()]
        outpath = os.path.join(args.outdir, base + ".out.txt")
        errpath = os.path.join(args.outdir, base + ".err.txt")
        proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env, text=True, bufsize=1)
        started = time.monotonic()
        hang = False
        try:
            for ln in lines:
                if time.monotonic() - started > args.timeout:
                    hang = True
                    break
                proc.stdin.write(ln + "\n")
                proc.stdin.flush()
                time.sleep(pause_for(ln, args.pause))
            if not hang:
                proc.stdin.close()
                proc.stdin = None
            out, errs = proc.communicate(timeout=args.timeout)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            out, errs = proc.communicate()
            rc, hang = None, True
        if hang:
            totals["hangs"] += 1
        with open(outpath, "w") as f:
            f.write(out or "")
        with open(errpath, "w") as f:
            f.write(errs or "")
        text = (out or "") + "\n" + (errs or "")
        n = 0
        kinds = {}
        for pat in SAN_PATTERNS:
            c = text.count(pat)
            if c:
                kinds[pat] = c
                n += c
        totals["san_lines"] += n
        for k, v in kinds.items():
            by_kind[k] = by_kind.get(k, 0) + v
        bm = len(re.findall(r"^bestmove", text, re.M))
        info = len(re.findall(r"^info depth", text, re.M))
        totals["bestmoves"] += bm
        totals["info_lines"] += info
        crashed = hang or (rc is not None and rc < 0)
        if crashed:
            totals["crashes"] += 1
        elif rc not in (0, None):
            totals["nonzero_exit"] += 1
        totals["sessions"] += 1
        if n or crashed:
            print("EVENT %s: san=%s crash=%s rc=%s" % (base, kinds, crashed, rc), flush=True)
            rows.append({"session": base, "rc": rc, "hang": hang, "san": n, "kinds": kinds})

    meta = {
        "tag": args.tag,
        "exe_started": exe,
        "exe_sha256": sha256(exe),
        "id_name": idname,
        "nm_asan_symbols": nm_count(exe, "__asan_"),
        "nm_ubsan_symbols": nm_count(exe, "__ubsan_"),
        "sessions_dir": os.path.abspath(args.sessions),
        "pause_s": args.pause,
        "env_extra": args.env,
        "totals": totals,
        "sanitizer_kinds": by_kind,
        "sessions_with_events": rows,
        "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                   capture_output=True, text=True).stdout.strip(),
    }
    with open(os.path.join(args.outdir, "SUMMARY_%s.json" % args.tag), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    sys.exit(main())
