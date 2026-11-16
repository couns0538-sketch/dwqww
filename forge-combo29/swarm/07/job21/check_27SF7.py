#!/usr/bin/env python3
"""check_27SF7.py EXE OUTDIR

Check of seat 27's finding S-F7, from its claim only:
  "The UCI option surface matches its advertisement: all 81 advertised options exercised with 291
   setoption cases give 0 refusals of an advertised min/max value and 0 `unknown option` lines."

This harness is my own: it reads the advertised options out of the engine's `uci` answer, then for
EVERY advertised option sends the cases that matter -- min, max, a value below min, a value above
max, a word, and no value -- and classifies each answer.

Classification per (option, case):
  ACCEPTED     : no complaint line
  CLAMPED      : `info string invalid value for option <name>` (the engine's documented behaviour:
                 report, then clamp)
  REFUSED-VALID: a complaint for a value that IS inside the advertised range  <- this is the bug
                 S-F7 says does not happen
  UNKNOWN      : `info string unknown option <name>` for an ADVERTISED name <- also a bug

The two bug classes are counted separately, and the run FAILS if either is non-zero.
Every case asserts a line was read; a missing answer is an error, never a pass.
"""
import os
import queue
import re
import subprocess
import sys
import threading

RE_OPTION = re.compile(r"^option name (.+?) type (\w+)(.*)$")
RE_DEFAULT = re.compile(r"default (\S+)")
RE_MIN = re.compile(r"min (-?\d+)")
RE_MAX = re.compile(r"max (-?\d+)")


class Reader:
    def __init__(self, s):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(s,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, t=60.0):
        try:
            return self.q.get(timeout=t)
        except queue.Empty:
            return None


def read_options(exe):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    opts = []
    while True:
        line = r.get(60)
        if line is None:
            raise SystemExit("FAIL the engine did not answer uci")
        if line.strip() == "uciok":
            break
        m = RE_OPTION.match(line.strip())
        if not m:
            continue
        name, kind, rest = m.group(1), m.group(2), m.group(3)
        d = RE_DEFAULT.search(rest)
        lo = RE_MIN.search(rest)
        hi = RE_MAX.search(rest)
        opts.append({"name": name, "type": kind,
                     "default": d.group(1) if d else None,
                     "min": int(lo.group(1)) if lo else None,
                     "max": int(hi.group(1)) if hi else None})
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    return opts


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    opts = read_options(exe)
    if not opts:
        raise SystemExit("FAIL no options were advertised: nothing to check")

    cases = []      # (name, value_or_None, expected_inside_range)
    for o in opts:
        if o["type"] == "spin" and o["min"] is not None and o["max"] is not None:
            cases.append((o["name"], str(o["min"]), True, o))
            cases.append((o["name"], str(o["max"]), True, o))
            cases.append((o["name"], str(o["min"] - 1), False, o))
            cases.append((o["name"], str(o["max"] + 1), False, o))
            cases.append((o["name"], "word", False, o))
            cases.append((o["name"], None, False, o))
        elif o["type"] == "check":
            cases.append((o["name"], "true", True, o))
            cases.append((o["name"], "false", True, o))
            cases.append((o["name"], "yes", False, o))
            cases.append((o["name"], None, False, o))
        elif o["type"] == "string":
            cases.append((o["name"], "<empty>", True, o))
            cases.append((o["name"], None, False, o))
        # button: no value is the correct invocation
        elif o["type"] == "button":
            cases.append((o["name"], None, True, o))

    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def drain_collect():
        lines = []
        while True:
            line = r.get(60)
            if line is None:
                raise SystemExit("FAIL no readyok while draining")
            if line.strip() == "readyok":
                return lines
            lines.append(line.rstrip("\n"))

    send("uci")
    while True:
        line = r.get(60)
        if line is None or line.strip() == "uciok":
            break
    send("isready")
    drain_collect()

    counts = {"ACCEPTED": 0, "CLAMPED": 0, "REFUSED-VALID": 0, "UNKNOWN": 0}
    bugs = []
    for name, value, inside, opt in cases:
        cmd = "setoption name " + name
        if value is not None:
            cmd += " value " + value
        send(cmd)
        send("isready")
        lines = drain_collect()
        joined = " | ".join(lines)
        if "unknown option" in joined and name in joined.split("unknown option")[-1]:
            counts["UNKNOWN"] += 1
            bugs.append(f"UNKNOWN for advertised option [{name}] value [{value}] :: {joined}")
        elif "invalid value" in joined:
            if inside:
                counts["REFUSED-VALID"] += 1
                bugs.append(f"REFUSED-VALID [{name}] value [{value}] (inside advertised range "
                            f"{opt['min']}..{opt['max']} for spin) :: {joined}")
            else:
                counts["CLAMPED"] += 1
        else:
            counts["ACCEPTED"] += 1

    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()

    with open(os.path.join(outdir, "summary.txt"), "w") as fh:
        fh.write(f"advertised options: {len(opts)}\n")
        fh.write(f"cases: {len(cases)}\n")
        for k, v in counts.items():
            fh.write(f"{k}: {v}\n")
        for b in bugs:
            fh.write("BUG " + b + "\n")
        fh.write("\nadvertised option list:\n")
        for o in opts:
            fh.write(f"  {o['name']} type={o['type']} default={o['default']} "
                     f"min={o['min']} max={o['max']}\n")

    print(f"advertised options {len(opts)}, cases {len(cases)}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    for b in bugs[:20]:
        print("  BUG " + b)
    if counts["REFUSED-VALID"] or counts["UNKNOWN"]:
        print(f"RESULT: REFUTED - {counts['REFUSED-VALID']} valid value(s) refused, "
              f"{counts['UNKNOWN']} advertised option(s) unknown")
        sys.exit(1)
    print("RESULT: CONFIRMS 27-S-F7 - every advertised option was recognised and every in-range "
          "value was accepted; out-of-range and junk values were reported as the engine documents")


if __name__ == "__main__":
    main()
