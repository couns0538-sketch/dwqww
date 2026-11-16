#!/usr/bin/env python3
"""san_count.py -- run ONE sequence file through a given exe and count sanitizer lines.
This is THE SAME RUNNER used for both the planted-fault proof and the real run.

Usage: san_count.py EXE SEQSFILE OUT.json
A sequence = lines between '### seq N' markers. One process per sequence; a 20 s
readyok deadline; sanitizer lines counted from stderr (AddressSanitizer /
UndefinedBehaviorSanitizer / runtime error / SUMMARY).
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import threading
import time

EXE = os.path.abspath(sys.argv[1])
SEQF = sys.argv[2]
OUTJ = sys.argv[3]

SAN = ("AddressSanitizer", "LeakSanitizer", "ThreadSanitizer",
       "UndefinedBehaviorSanitizer", "runtime error", "SUMMARY")


def parse(path):
    seqs, cur = [], None
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("### seq "):
            cur = []
            seqs.append(cur)
        elif cur is not None:
            cur.append(line)
    return seqs


def run_one(args):
    i, lines = args
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    out, err = [], []

    def rd(stream, sink):
        try:
            for l in stream:
                sink.append(l)
        except Exception:
            pass

    threading.Thread(target=rd, args=(p.stdout, out), daemon=True).start()
    threading.Thread(target=rd, args=(p.stderr, err), daemon=True).start()
    nready, hang = 0, False
    try:
        for line in lines:
            try:
                p.stdin.write(line + "\n")
                p.stdin.flush()
            except Exception:
                break
            if line == "isready":
                want = nready + 1
                t0 = time.monotonic()
                while time.monotonic() - t0 < 20:
                    if sum(1 for x in out if x.strip() == "readyok") >= want:
                        nready = want
                        break
                    time.sleep(0.02)
                else:
                    hang = True
                    p.kill()
                    break
        p.wait(timeout=30)
    except Exception:
        p.kill()
    san = [l.strip() for l in err if any(s in l for s in SAN)]
    return {"i": i, "hang": hang, "rc": p.returncode, "san": san}


def main():
    seqs = parse(SEQF)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(run_one, list(enumerate(seqs))))
    summ = {"sequences": len(res),
            "sanitizer_lines": sum(len(r["san"]) for r in res),
            "crashes": sum(1 for r in res if r["rc"] not in (0, -15, 15, -9)),
            "hangs": sum(1 for r in res if r["hang"]),
            "first_sanitizer_lines": [l for r in res for l in r["san"]][:3]}
    with open(OUTJ, "w") as f:
        json.dump(summ, f, indent=2)
        f.write("\n")
    print(json.dumps(summ, indent=2))


main()
