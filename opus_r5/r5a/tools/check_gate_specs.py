#!/usr/bin/env python3
"""R5A M4: validate gate_specs.json against the job rules and the measured evidence.

Checks: one option set per gate (one option each); candidate and opponent are the same exe; the opponent has no
options; both sides Threads=1 Hash=16 OwnBook=false; SPRT elo0=0 elo1=10 alpha=beta=0.05 normalized; cap_games is
the int 3000; srand and openings_start are blank; primary TC 40+0.4 for CorrExt and CorrMargins, 10+0.1 otherwise;
at most one NetScale entry; prebench cand_off = the lock pins and cand_on = the M1 ON benches in
logs/m1_bench_base.json; the exe sha256 values match the files when they exist (F:\\opus_scratch\\r5\\r5a\\exe).
usage: check_gate_specs.py <r5a dir>          exit 0 = every check passed
"""
import hashlib
import json
import os
import sys

R5A = sys.argv[1]
spec = json.load(open(os.path.join(R5A, "gate_specs.json"), encoding="utf-8"))
m1 = json.load(open(os.path.join(R5A, "logs", "m1_bench_base.json"), encoding="utf-8"))
on_pins = {f"{c['option']}={c['value']}": [c["on"][str(d)] if str(d) in c["on"] else c["on"][d] for d in (11, 13, 16)]
           for c in m1["configs"]}
problems = []


def check(ok, what):
    if not ok:
        problems.append(what)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


for path, want in ((spec["exe"]["source"], spec["exe"]["sha256"]),
                   (spec["exe_alternative"]["source"], spec["exe_alternative"]["sha256"])):
    if os.path.exists(path):
        check(sha(path) == want, f"exe sha256 mismatch: {path}")
netscale = 0
ids = set()
for g in spec["gates"]:
    gid = g["id"]
    check(gid not in ids, f"{gid}: duplicate id")
    ids.add(gid)
    opts = g["cand"]["options"]
    check(len(opts) == 1 and opts[0].startswith("option."), f"{gid}: not exactly one option ({opts})")
    name = opts[0][len("option."):] if opts else ""
    check(g["name"] == name, f"{gid}: name {g['name']} != option {name}")
    check(g["cand"]["sha256"] == g["opponent"]["sha256"] == spec["exe"]["sha256"], f"{gid}: cand/opponent exe differ")
    check(g["opponent"]["options"] == [], f"{gid}: opponent has options")
    check(g["both_sides"] == ["option.Threads=1", "option.Hash=16", "option.OwnBook=false"], f"{gid}: both_sides")
    check(g["sprt"] == {"elo0": 0, "elo1": 10, "alpha": 0.05, "beta": 0.05, "model": "normalized"}, f"{gid}: sprt")
    check(type(g["cap_games"]) is int and g["cap_games"] == 3000, f"{gid}: cap_games not the int 3000")
    check(g["srand"] == "" and g["openings_start"] == "", f"{gid}: srand/openings_start not blank")
    long_tc = name.split("=")[0] in ("CorrExt", "CorrMargins")
    check(g["tc_primary"] == ("40+0.4" if long_tc else "10+0.1"), f"{gid}: primary TC {g['tc_primary']}")
    check(g["prebench"]["cand_off"] == [312866, 862329, 3024920], f"{gid}: cand_off pins")
    check(g["prebench"]["cand_on"] == on_pins.get(name), f"{gid}: cand_on {g['prebench']['cand_on']} != M1 {on_pins.get(name)}")
    check(g["expected_echo"] == f"info string active: {name}", f"{gid}: expected echo")
    netscale += name.startswith("NetScale=")
check(netscale <= 1, f"{netscale} NetScale entries (at most one allowed)")
check([g["rank"] for g in spec["gates"]] == list(range(1, len(spec["gates"]) + 1)), "ranks are not 1..n in order")
print(f"{len(spec['gates'])} gate entries checked: " + ("OK" if not problems else "PROBLEMS"))
for p in problems:
    print("  " + p)
sys.exit(0 if not problems else 1)
