#!/usr/bin/env python3
"""r12_phase2.py - after the R12 build chain: binding check, exe-level identity, then speed. One command, resumable.

  r12_phase2.py --builds F:/opus_scratch/r12/builds --chain-log F:/opus_scratch/r12/logs/chain.log --exe-dir F:/opus_scratch/r12/exe
                --out F:/opus_scratch/r12/phase2 [--pair 0x3 --ignore-idle] [--skip-speed-nonet]

1. Waits until the chain log says 'chain done' or 'STOP chain'.
2. Binding check per variant (A = r10fix1_w2, B = r10fix1_w2pt): both SUMMARY.txt 'RESULT PASS' and the forge_ltopgo
   exe sha256 of pc1 == pc2. Only variants that pass go on (the rule: no speed run before pc1 = pc2).
3. Copies each passing pc1 exe to EXE_DIR/new_<v>_<sha8>.exe plus a byte copy (A/A) .._aa.exe.
4. r12_fens12k.py for e19 and e9: plain D8D90B68 (reference) vs every passing variant (go depth 2 on 12,000 FENs).
5. r12_speed.py with e9_best (QA's speed4 net): variants + D8D90B68 + 9E5CB644, refs D8, L9 (+ B vs A), 7 blocks,
   3 A/A blocks, d16 + d20; then no net: variants + FD3A5190, ref FD, 7 blocks, 3 A/A blocks.
All runs use one CPU of the pair (the lower one, sibling idle) at BelowNormal; every block waits for the pair and RAM.
Skips steps whose output already exists (DONE marker per step), so a rerun continues where it stopped.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(TOOLS, "..", ".."))
NET19 = r"C:\Users\Administrator\grok-pc\forge_push\bin\r11_e19_final_bf1e347c.nnue"
NET9 = r"C:\Users\Administrator\grok-pc\forge_push\bin\r11_e9_best_5380f866.nnue"
VARIANTS = (("A", "r10fix1_w2"), ("B", "r10fix1_w2pt"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--builds", required=True)
    ap.add_argument("--chain-log", required=True)
    ap.add_argument("--exe-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pair", default="0x3")
    ap.add_argument("--ignore-idle", action="store_true")
    ap.add_argument("--skip-speed-nonet", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    py = sys.executable
    logf = open(os.path.join(a.out, "phase2.log"), "a", encoding="utf-8", newline="\n")

    def log(msg):
        line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    pair = int(a.pair, 0)
    cpu = (pair & -pair).bit_length() - 1
    extra = ["--ignore-idle"] if a.ignore_idle else []
    log("phase2 start pair %s cpu %d ignore_idle %s" % (hex(pair), cpu, a.ignore_idle))
    sys.path.insert(0, TOOLS)
    import psutil
    import r12_speed

    def wait_pair():
        while True:
            hits = r12_speed.busy_masks(pair, a.ignore_idle)
            free_gb = psutil.virtual_memory().available / 2 ** 30
            if not hits and free_gb >= r12_speed.MIN_FREE_GB:
                return
            log("WAIT pair %s busy %s free RAM %.1f GB" % (hex(pair), hits[:3], free_gb))
            time.sleep(30)
    while True:
        text = open(a.chain_log, encoding="utf-8").read() if os.path.exists(a.chain_log) else ""
        if "chain done" in text or "STOP chain" in text:
            break
        time.sleep(30)
    exes = {}
    for v, stem in VARIANTS:
        shas, ok = [], True
        for pc in ("pc1", "pc2"):
            summ = os.path.join(a.builds, "%s_%s" % (stem, pc), "SUMMARY.txt")
            t = open(summ, encoding="utf-8").read() if os.path.exists(summ) else ""
            m = re.search(r"forge_ltopgo_%s_%s\.exe sha256 ([0-9A-F]{64})" % (stem, pc), t)
            ok &= ("RESULT PASS %s_%s" % (stem, pc)) in t and m is not None
            shas.append(m.group(1) if m else None)
        same = ok and shas[0] == shas[1]
        log("binding %s (%s): pc1 %s pc2 %s -> %s" % (v, stem, shas[0], shas[1], "PASS (pc1 = pc2)" if same else "FAIL"))
        if same:
            src = os.path.join(a.builds, stem + "_pc1", "src_copy", "forge_ltopgo_%s_pc1.exe" % stem)
            dst = os.path.join(a.exe_dir, "new_%s_%s.exe" % (v, shas[0][:8].lower()))
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)
                shutil.copyfile(src, dst[:-4] + "_aa.exe")
            exes[v] = dst
    if not exes:
        log("no variant passed the binding check; stop (no identity/speed runs)")
        return 1
    d8 = os.path.join(a.exe_dir, "plain_d8d90b68.exe")
    l9 = os.path.join(a.exe_dir, "lp_9e5cb644.exe")
    fd = os.path.join(a.exe_dir, "lock_fd3a5190.exe")
    fens = os.path.join(REPO, "opus_r10", "parity", "fens_12k.txt")
    for tag, net in (("e19", NET19), ("e9", NET9)):
        outd = os.path.join(a.out, "fens12k_" + tag)
        if os.path.exists(os.path.join(outd, "compare.txt")):
            continue
        cmd = [py, "-I", "-B", os.path.join(TOOLS, "r12_fens12k.py"), "--out", outd, "--cpu", str(cpu), "--net", net,
               "--fens", fens, "--depth", "2", "--exe", "D8=" + d8]
        cmd += [x for v, p in exes.items() for x in ("--exe", "%s=%s" % (v, p))]
        wait_pair()
        log("fens12k %s: %s" % (tag, " ".join(cmd)))
        rc = subprocess.call(cmd, stdout=open(os.path.join(a.out, "fens12k_%s.out" % tag), "w"), stderr=subprocess.STDOUT)
        log("fens12k %s rc %d: %s" % (tag, rc, open(os.path.join(outd, "compare.txt")).read().strip()
                                      if os.path.exists(os.path.join(outd, "compare.txt")) else "no compare.txt"))
        if rc != 0:
            log("STOP: 12k exe identity failed for %s; no speed runs" % tag)
            return 2
    order = [v for v, _ in VARIANTS if v in exes]
    speed_sets = [("speed_net_e9", NET9, [(v, exes[v]) for v in order] + [("D8", d8), ("L9", l9)],
                   ["D8", "L9"] + (["A"] if len(order) == 2 else []))]
    if not a.skip_speed_nonet:
        speed_sets.append(("speed_nonet", "", [(v, exes[v]) for v in order] + [("FD", fd)],
                           ["FD"] + (["A"] if len(order) == 2 else [])))
    for name, net, ex, refs in speed_sets:
        outd = os.path.join(a.out, name)
        if os.path.exists(os.path.join(outd, "summary.txt")):
            continue
        cmd = [py, "-I", "-B", os.path.join(TOOLS, "r12_speed.py"), "--out", outd, "--cpu", str(cpu), "--guard-mask",
               hex(pair), "--pairs", "7", "--aa-pairs", "3", "--depths", "16", "20"] + extra
        if net:
            cmd += ["--net", net]
        for t, p in ex:
            cmd += ["--exe", "%s=%s" % (t, p)]
        for r in refs:
            cmd += ["--ref", r]
        for v in order:
            cmd += ["--aa", "%s=%s" % (v, exes[v][:-4] + "_aa.exe")]
        log("%s: %s" % (name, " ".join(cmd)))
        rc = subprocess.call(cmd, stdout=open(os.path.join(a.out, name + ".out"), "w"), stderr=subprocess.STDOUT)
        log("%s rc %d" % (name, rc))
        if os.path.exists(os.path.join(outd, "summary.txt")):
            for line in open(os.path.join(outd, "summary.txt"), encoding="utf-8"):
                log("  " + line.rstrip())
        if rc != 0:
            log("STOP: %s failed" % name)
            return 3
    log("phase2 done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
