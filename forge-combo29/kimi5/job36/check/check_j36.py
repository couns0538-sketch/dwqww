#!/usr/bin/env python3
"""kimi5 job 36: invariants I1-I8 + the two controls + the nine hashes beside K6.
Reads runs/l0/O_A, runs/l0/G_A, runs/s3/G_* (.rows/.ledger). Prints one line per check."""
import os, hashlib
from collections import defaultdict, Counter

L0 = "/tmp/j36/runs/l0"
S3 = "/tmp/j36/runs/s3"
K6 = {"O_A": "3eac50dd8fd5297e", "G_A": "424d931234dd3ff9", "G_B": "244776b6649f2ce1",
      "G_C": "4e8210e936e59fd5", "G_A_fin": "5a85f018917c736f", "G_B_fin": "e09e0e592abf8e8d",
      "G_C_fin": "b6bb6cee6f6d99f7", "G_A_ns": "627eab46079c189a", "G_B_ns": "05db9b4b27fef38f",
      "G_C_ns": "3d7ecdfca001e093", "G_A_both": "f09dde3058bf9db7", "G_B_both": "f45ab15c0037e871",
      "G_C_both": "f6d5f31bfde05b74", "G_A_chard": "dd3691a85ab318ed", "G_A_cfloor": "9ad6c91af598d425"}
K7 = {"O_A": 54326, "G_A": 98026, "G_B": 45372, "G_C": 20715, "G_A_chard": 80174, "G_A_cfloor": 160642}
K8N = {"A": 1585152, "B": 675840, "C": 174080}
K9 = {"G_A": 7, "G_B": 6, "G_C": 6}
K10 = {"G_A_fin": 162, "G_B_fin": 163, "G_C_fin": 163, "G_A_both": 148, "G_B_both": 172, "G_C_both": 149}

def path(tag):
    return (L0 if tag in ("O_A", "G_A") else S3, tag)

def load(tag):
    d, t = path(tag)
    rows = [l.split() for l in open(f"{d}/{t}.rows") if l.strip()]
    per = defaultdict(lambda: {"iters": [], "holds": 0, "led": None})
    for l in open(f"{d}/{t}.ledger"):
        f = l.split()
        if not f: continue
        p = int(f[0])
        if f[3] == "ITER":
            per[p]["iters"].append({f[i]: f[i+1] for i in range(4, len(f)-1, 2)})
        elif f[3] == "LEDGER":
            per[p]["led"] = {f[i]: f[i+1] for i in range(4, len(f)-1, 2)}
        elif f[3] == "TmFinishIteration":
            per[p]["holds"] += 1
    return rows, per

def h16(tag):
    d, t = path(tag)
    return hashlib.sha256(open(f"{d}/{t}.rows", "rb").read()).hexdigest()[:16]

tags = ["O_A", "G_A", "G_B", "G_C", "G_A_chard", "G_A_cfloor", "G_A_fin", "G_B_fin", "G_C_fin",
        "G_A_ns", "G_B_ns", "G_C_ns", "G_A_both", "G_B_both", "G_C_both"]
have = [t for t in tags if os.path.exists(path(t)[0] + "/" + t + ".rows")]

print("== hashes beside K6 ==")
for t in have:
    mine = h16(t)
    print(f"{t:12s} {mine}  K6 {K6.get(t,'-'):16s}  {'EQUAL' if mine == K6.get(t) else 'DIFFER'}")

print("\n== I1: LEDGER elapsed == nodes//1000 ==")
for t in have:
    _, per = load(t)
    bad = [(p, v["led"]) for p, v in per.items() if v["led"] and int(v["led"]["elapsed"]) != int(v["led"]["nodes"]) // 1000]
    print(f"{t:12s} {'OK' if not bad else f'FAIL {bad[:3]}'}")

print("\n== I2: abort kinds have exactly K8's counts; no other kind has them ==")
for t in have:
    state = "chard" if "chard" in t else t.split("_")[1]
    want = 317440 if state == "chard" else K8N[state]
    rows, per = load(t)
    bad_abort, other_hit = [], []
    for p, v in per.items():
        if not v["led"]: continue
        k, n = v["led"]["kind"], int(v["led"]["nodes"])
        if k in ("ABORTKEPT", "ABORTNEW"):
            if n != want: bad_abort.append((p, k, n))
        elif n == want:
            other_hit.append((p, k, n))
    print(f"{t:12s} aborts=={want}: {'OK' if not bad_abort else f'FAIL {bad_abort[:3]}'}; other kinds with it: {'none' if not other_hit else other_hit[:3]}")

print("\n== I3: SOFT last ITER elapsed>=target; HOLD elapsed<target ==")
for t in have:
    _, per = load(t)
    bad = []
    for p, v in per.items():
        if not v["led"] or not v["iters"]: continue
        last = v["iters"][-1]
        e, tg = int(last["elapsed"]), int(last["target"])
        if v["led"]["kind"] == "SOFT" and e < tg: bad.append((p, "SOFT", e, tg))
        if v["led"]["kind"] == "HOLD" and e >= tg: bad.append((p, "HOLD", e, tg))
    print(f"{t:12s} {'OK' if not bad else f'FAIL {bad[:3]}'}")

print("\n== I4: factor1000>=450 every ITER; C-FLOOR >=1000 and no SOFT elapsed<317 ==")
for t in have:
    _, per = load(t)
    floor_min = 1000 if "cfloor" in t else 450
    bad = [(p, i["factor1000"]) for p, v in per.items() for i in v["iters"] if int(i["factor1000"]) < floor_min]
    extra = ""
    if "cfloor" in t:
        softbad = [(p, v["led"]["elapsed"]) for p, v in per.items() if v["led"] and v["led"]["kind"] == "SOFT" and int(v["led"]["elapsed"]) < 317]
        extra = f"; SOFT elapsed<317: {'none' if not softbad else softbad[:3]}"
    print(f"{t:12s} {'OK' if not bad else f'FAIL {bad[:3]}'}{extra}")

print("\n== I5: SOFT/HOLD/HARDEND/CAP LEDGER nodes == rows nodes ==")
for t in have:
    rows, per = load(t)
    rmap = {int(r[0]): int(r[2]) for r in rows}
    bad = [(p, v["led"]["nodes"], rmap[p]) for p, v in per.items()
           if v["led"] and v["led"]["kind"] in ("SOFT", "HOLD", "HARDEND", "CAP") and int(v["led"]["nodes"]) != rmap[p]]
    print(f"{t:12s} {'OK' if not bad else f'FAIL {bad[:3]}'}")

print("\n== I6: HOLD count == K10; CAP == K9 (9 cfloor); CAP depth 64; no search has two holds ==")
for t in have:
    _, per = load(t)
    holds = sum(1 for v in per.values() if v["led"] and v["led"]["kind"] == "HOLD")
    two = sum(1 for v in per.values() if v["holds"] > 1)
    caps = [v["led"] for v in per.values() if v["led"] and v["led"]["kind"] == "CAP"]
    msg = f"holds {holds}"
    if t in K10: msg += f" (K10 {K10[t]}) {'OK' if holds == K10[t] else 'FAIL'}"
    if t in K9 or "cfloor" in t:
        want = 9 if "cfloor" in t else K9[t]
        msg += f"; CAP {len(caps)} (want {want}) {'OK' if len(caps) == want else 'FAIL'}; depth64 {'OK' if all(c['depth'] == '64' for c in caps) else 'FAIL'}"
    msg += f"; searches with 2 holds: {two}"
    print(f"{t:12s} {msg}")

print("\n== I7: sum of LEDGER elapsed == K7 T ==")
for t in [x for x in have if x in K7]:
    _, per = load(t)
    s = sum(int(v["led"]["elapsed"]) for v in per.values() if v["led"])
    print(f"{t:12s} {s} (K7 {K7[t]}) {'OK' if s == K7[t] else 'FAIL'}")

print("\n== I8: fin ITERs up to hold depth equal base's, field for field ==")
for s in ("A", "B", "C"):
    bt, ft = f"G_{s}", f"G_{s}_fin"
    if bt not in have or ft not in have: continue
    _, bper = load(bt)
    _, fper = load(ft)
    bad = []
    for p, fv in fper.items():
        bv = bper.get(p)
        hd = None
        if fv["led"] and fv["led"]["kind"] == "HOLD":
            hd = int(fv["iters"][-1]["depth"])
        n = len(fv["iters"])
        for i, fi in enumerate(fv["iters"]):
            if hd is not None and int(fi["depth"]) > hd: break
            bi = bv["iters"][i] if bv and i < len(bv["iters"]) else None
            if bi != fi:
                bad.append((p, fi["depth"]))
                break
    print(f"G_{s}_fin vs G_{s}: {'OK' if not bad else f'FAIL {bad[:5]}'}")

print("\n== controls: C-HARD more aborts than base, no LEDGER elapsed>318; C-FLOOR larger T ==")
_, bper = load("G_A")
bab = sum(1 for v in bper.values() if v["led"] and v["led"]["kind"].startswith("ABORT"))
_, cper = load("G_A_chard")
cab = sum(1 for v in cper.values() if v["led"] and v["led"]["kind"].startswith("ABORT"))
over = [(p, v["led"]["elapsed"]) for p, v in cper.items() if v["led"] and int(v["led"]["elapsed"]) > 318]
print(f"C-HARD aborts {cab} vs base {bab}: {'OK' if cab > bab else 'FAIL'}; elapsed>318: {'none OK' if not over else f'FAIL {over[:3]}'}")
_, fper = load("G_A_cfloor")
t_base = sum(int(v["led"]["elapsed"]) for v in bper.values() if v["led"])
t_floor = sum(int(v["led"]["elapsed"]) for v in fper.values() if v["led"])
print(f"C-FLOOR T {t_floor} vs base {t_base}: {'OK' if t_floor > t_base else 'FAIL'}")
