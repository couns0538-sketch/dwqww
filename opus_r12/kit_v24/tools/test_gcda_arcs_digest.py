#!/usr/bin/env python3
"""Unit test for gcda_arcs_digest.py (v2.1 prefix fix). Run: python3 tools/test_gcda_arcs_digest.py [BOX_RUN_DIR]
1) synthetic dumps under C:\\pc1 and C:\\pc2 (and / spellings) must digest equal; the v2 split(':',1) must not (regression).
2) real box gcov-dump output re-prefixed with Windows paths must equal its Linux digest.
3) with gcov-dump-14 on the box: the arcs manifest of BOX_RUN_DIR (default runs/al1s198_frozen_v2sh) recomputed from its
   kept profile/ with the sh's <BUILD> rewrite must have sha256 0c5ece46c8df3c47ee7b7cab002593b63c5d1d5fddbea78ae48ea300dc55ac99."""
import hashlib, os, re, shutil, subprocess, sys
sys.dont_write_bytecode = True
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import gcda_arcs_digest as g
WANT = "0c5ece46c8df3c47ee7b7cab002593b63c5d1d5fddbea78ae48ea300dc55ac99"
fails = 0
def check(name, cond):
    global fails; fails += (not cond); print(("PASS " if cond else "FAIL ") + name)

BODY = ["data:magic `gcda':version `B52*'", "stamp 123", "checksum 456",
        "  01000000:  12:FUNCTION ident=1, lineno_checksum=0x1, cfg_checksum=0x2",
        "    01a10000:  24:COUNTERS arcs 3 counts", "                   0: 5 7 9 ",
        "    01b10000:  16:COUNTERS time_profiler 1 counts", "                   0: 77 "]
def dump(path, stamp="123", tp="77"):
    return "\n".join(path + ":" + b.replace("stamp 123", "stamp " + stamp).replace("0: 77", "0: " + tp) for b in BODY)
def old_v2(text, path):   # the v2 logic, kept here to show the regression
    keep, h = False, hashlib.sha256()
    for line in text.splitlines():
        body = line.split(":", 1)[1] if line.startswith(path) else line
        if "FUNCTION ident=" in body: keep = False; h.update(body.strip().encode() + b"\n"); continue
        if "COUNTERS" in body: keep = " COUNTERS arcs " in body or body.strip().split(":COUNTERS")[-1].strip().startswith("arcs")
        if keep: h.update(re.sub(r"\s+", " ", body.strip()).encode() + b"\n")
    return h.hexdigest()

name = "#C#Users#x#Work#t#src_copy#obj_ltopgo#search.gcda"
w1 = "C:\\Users\\Administrator\\grok-pc\\forge_push\\ltopgo\\al1_pc1\\src_copy\\pgo_profile_lto\\" + name
w2 = "C:\\Users\\Administrator\\grok-pc\\forge_push\\ltopgo\\al1_pc2\\src_copy\\pgo_profile_lto\\" + name
lx = "/workspace/x/profile/" + name
d1, u1 = g.digest_dump(dump(w1), w1); d2, u2 = g.digest_dump(dump(w2, stamp="999", tp="31"), w2)
dl, ul = g.digest_dump(dump(lx), lx)
check("C:\\ pc1 vs pc2 equal (stamp + time_profiler differ, arcs same)", d1 == d2)
check("C:\\ vs Linux path equal", d1 == dl)
check("all lines matched the prefix", u1 == u2 == ul == 0)
fw = w1.replace("\\", "/"); df, uf = g.digest_dump(dump(fw), w1)
check("gcov-dump printing / while python passed \\ still equal", df == d1 and uf == 0)
bw, ub = g.digest_dump(dump(w1), fw)
check("gcov-dump printing \\ while python passed / still equal", bw == d1 and ub == 0)
check("v2 split(':',1) regression reproduced (pc1 != pc2)", old_v2(dump(w1), w1) != old_v2(dump(w2), w2))
dc, _ = g.digest_dump(dump(w1).replace("0: 5 7 9", "0: 5 7 8"), w1)
check("an arcs change changes the digest", dc != d1)

tool = shutil.which("gcov-dump-14") or shutil.which("gcov-dump")
run = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "runs", "al1s198_frozen_v2sh"))
prof = os.path.join(run, "profile")
if tool and os.path.isdir(prof):
    f0 = sorted(f for f in os.listdir(prof) if f.endswith(".gcda"))[0]; p0 = os.path.join(prof, f0)
    real = subprocess.run([tool, "-l", p0], capture_output=True, text=True, check=True).stdout
    lin, ulin = g.digest_dump(real, p0)
    for wp in ("C:\\pc1\\profile\\" + f0, "C:/pc2/profile/" + f0):
        wd, uw = g.digest_dump(real.replace(p0 + ":", wp + ":"), wp)
        check(f"real dump re-prefixed as {wp[:13]}... equals Linux digest", wd == lin and uw == 0 == ulin)
    out = subprocess.run([sys.executable, os.path.join(here, "gcda_arcs_digest.py"), prof, tool], capture_output=True, text=True, check=True)
    check("no prefix warnings on the box run", out.stderr == "")
    mb = (run + "/build_lp").replace("/", "#")
    man = out.stdout.replace(mb, "<BUILD>").encode()
    got = hashlib.sha256(man).hexdigest()
    check(f"box arcs manifest {os.path.basename(run)} = 0c5ece46 (got {got[:8]})", got == WANT)
else:
    print("SKIP real-dump checks (no gcov-dump or no kept profile)")
print("ALL PASS" if fails == 0 else f"{fails} FAILED"); sys.exit(1 if fails else 0)
