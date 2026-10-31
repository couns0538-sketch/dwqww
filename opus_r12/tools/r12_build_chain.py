#!/usr/bin/env python3
"""r12_build_chain.py - run kit v2.4 LTO+PGO builds one after another, only on a CPU pair nobody else holds.

  r12_build_chain.py --work F:/opus_scratch/r12/builds --src F:/opus_scratch/r12/src_r10fix1 --log LOG
                     --build TAG[:pt][:full] ...   [--pair auto|0x3] [--python PY]

TAG:pt adds -PartialTraining; TAG:full adds the two net -CheckOpt runs with their pins (else OFF identity only).
Before every build it waits (30 s polls) until a CPU pair is free: no gate (fastchess + engines), trainer (python)
or self-play (forge*) process may have either CPU in its affinity mask (unpinned 0xFFFF processes are ignored).
With --pair MASK --ignore-idle (only after QA freed that pair for R12) Idle-class processes (trainer, self-play)
do not block; gate and QA processes (BelowNormal and up) still do.
The kit then runs pinned to that pair at BelowNormal (its own -Affinity / priority, inherited by children).
Stops at the first build without 'RESULT PASS' in its SUMMARY.txt. Never kills or deletes anything.
"""
import argparse
import os
import subprocess
import sys
import time

import psutil

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit_v24", "build_ltopgo.ps1")
NET19 = r"C:\Users\Administrator\grok-pc\forge_push\bin\r11_e19_final_bf1e347c.nnue"
NET9 = r"C:\Users\Administrator\grok-pc\forge_push\bin\r11_e9_best_5380f866.nnue"
PINS19 = "d11=373062,d13=831975,d16=4115992,d20=17885060,d22=37006232"
PINS9 = "d11=287095,d13=693432,d16=2816047,d20=12332089,d22=25323515"
OFF_PINS = "d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354"
PERFT_PINS = "startpos=4865609,kiwipete=193690690"


def busy_mask(ignore_idle=False):
    """CPUs held by gate / trainer / self-play / QA processes (forge*, fastchess*, python*), not ours.
    ignore_idle: skip Idle-class processes (the trainer, self-play) - only when QA has freed that pair for R12."""
    m = 0
    for p in psutil.process_iter(["pid", "name"]):
        name = (p.info["name"] or "").lower()
        if not (name.startswith("forge") or name.startswith("fastchess") or name.startswith("python")):
            continue
        try:
            aff = sum(1 << c for c in p.cpu_affinity())
            cmd = " ".join(p.cmdline())
            idle = p.nice() == psutil.IDLE_PRIORITY_CLASS
        except (psutil.Error, OSError):
            continue
        if aff == 0xFFFF or "opus_scratch" in cmd or "opus_r12" in cmd or p.pid == os.getpid():
            continue
        if ignore_idle and idle:
            continue
        m |= aff
    return m


def free_pair(want, ignore_idle=False):
    busy = busy_mask(ignore_idle)
    pairs = [want] if want else [3 << (2 * i) for i in range(8)]
    for pm in pairs:
        if not busy & pm:
            return pm, busy
    return None, busy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--build", action="append", required=True)
    ap.add_argument("--pair", default="auto")
    ap.add_argument("--ignore-idle", action="store_true",
                    help="QA freed --pair for R12: Idle-class processes (trainer, self-play) do not block it")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--workload", default="v2", choices=["v2", "v2t1"], help="kit -Workload for every build")
    a = ap.parse_args()
    want = None if a.pair == "auto" else int(a.pair, 0)
    if a.ignore_idle and want is None:
        sys.exit("--ignore-idle needs an explicit --pair")
    logf = open(a.log, "a", encoding="utf-8", newline="\n")

    def log(msg):
        line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    log("chain start builds %s pair %s kit %s" % (a.build, a.pair, os.path.abspath(KIT)))
    last_wait = 0
    for spec in a.build:
        parts = spec.split(":")
        tag, pt, full = parts[0], "pt" in parts[1:], "full" in parts[1:]
        while True:
            pm, busy = free_pair(want, a.ignore_idle)
            free_gb = psutil.virtual_memory().available / 2 ** 30
            if pm and free_gb >= 5.0:  # R12: keep about 4 GB free (+1 GB margin for the LTO link)
                break
            if time.time() - last_wait > 300:
                log("WAIT no free CPU pair (busy mask %s) or free RAM %.1f GB < 5" % (hex(busy), free_gb))
                last_wait = time.time()
            time.sleep(30)
        # -Command (not -File): only -Command binds 'a','b' to the [string[]] -CheckOpt / -CheckOptPins parameters
        q = lambda s: "'" + s.replace("'", "''") + "'"
        ps = ("& %s -SrcDir %s -Tag %s -Work %s -Affinity %d -Expose -Workload %s -Python %s -Pins %s -PerftPins %s" % (
            q(os.path.abspath(KIT)), q(a.src), q(tag), q(a.work), pm, a.workload, q(a.python), q(OFF_PINS), q(PERFT_PINS)))
        if pt:
            ps += " -PartialTraining"
        if full:
            ps += " -CheckOpt %s,%s -CheckOptPins %s,%s" % (q("EvalFileHalfKA=" + NET19), q("EvalFileHalfKA=" + NET9),
                                                            q(PINS19), q(PINS9))
        ps += "; exit $LASTEXITCODE"
        cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps]
        log("command: " + ps)
        log("build %s pair %s pt %s full %s (busy mask %s)" % (tag, hex(pm), pt, full, hex(busy)))
        t0 = time.time()
        out = open(os.path.join(os.path.dirname(a.log), "build_%s.out" % tag), "w", encoding="utf-8", newline="\n")
        rc = subprocess.call(cmd, stdout=out, stderr=subprocess.STDOUT, creationflags=0x00004000)  # BelowNormal
        out.close()
        summ = os.path.join(a.work, tag, "SUMMARY.txt")
        text = open(summ, encoding="utf-8").read() if os.path.exists(summ) else ""
        log("build %s rc %d %.0fs" % (tag, rc, time.time() - t0))
        for line in text.splitlines():
            log("  " + line)
        if rc != 0 or ("RESULT PASS " + tag) not in text:
            log("STOP chain: %s did not pass" % tag)
            return 1
    log("chain done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
