#!/usr/bin/env python3
"""job6_run.py -- job 6's runs, driven by the parsed kimi5 table.

Usage: job6_run.py [--dead-only|--live-only]
For every setting in kimi13_table.txt:
  dead (3): S14 + (value+step) and S14 + (value-step), on O and G  -> must equal S14
  live (32): S14 + (value+step), on O                              -> must differ from S14
Writes runs/<set>_<setting>_<value>.rows and appends to table.txt:
  "claim | setting | set | value | sum | nodes-eq | bm-eq | verdict"
"""
import argparse
import os
import re
import subprocess
import sys

ROW = re.compile(r"^(\S+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(dead|live)")


def load_table(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        m = ROW.match(line)
        if m:
            rows.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dead-only", action="store_true")
    ap.add_argument("--live-only", action="store_true")
    ap.add_argument("--exe", default="/agent/repos/work/build-base/forge")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    os.makedirs("runs", exist_ok=True)
    s14 = open("s14.txt").read().strip()
    table = load_table("kimi13_table.txt")
    out = open("table.txt", "a", encoding="utf-8")

    def one(claim, setting, setname, value):
        setfile = "first200.fens" if setname == "O" else "set_G.epd"
        base = "%s_S14.rows" % setname
        rf = "runs/%s_%s_%d.rows" % (setname, setting, value)
        opts = "%s;%s=%d" % (s14, setting, value)
        subprocess.run([sys.executable, "rows.py", "--exe", args.exe, "--set", setfile,
                        "--out", rf, "--opts", opts, "--depth", "12"],
                       capture_output=True, text=True)
        s = subprocess.run([sys.executable, "sumrows.py", rf],
                           capture_output=True, text=True).stdout.strip()
        c = subprocess.run([sys.executable, "cmp2.py", base, rf],
                           capture_output=True, text=True).stdout.strip()
        summ = s.split()[-1] if s and "sum" in s else "REFUSED"
        ne = c.split("nodes-equal")[1].split("of")[0].strip() if "nodes-equal" in c else "?"
        be = c.split("bestmove-equal")[1].split("of")[0].strip() if "bestmove-equal" in c else "?"
        n = 200 if setname == "O" else 353
        if claim == "dead":
            ok = (ne == str(n))
            verdict = "claim holds" if ok else "CLAIM FAILS (differs)"
        else:
            ok = (ne != str(n))
            verdict = "claim holds" if ok else "CLAIM FAILS (identical)"
        line = "%s | %s | %s | %d | %s | %s | %s | %s" % (
            claim, setting, setname, value, summ, ne, be, verdict)
        print(line, flush=True)
        out.write(line + "\n"); out.flush()
        return ok

    for setting, value, step, claim in table:
        if claim == "dead":
            if args.live_only:
                continue
            for setname in ("O", "G"):
                for v in (value + step, value - step):
                    one(claim, setting, setname, v)
        else:
            if args.dead_only:
                continue
            one(claim, setting, "O", value + step)
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
