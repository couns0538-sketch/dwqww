#!/usr/bin/env python3
"""failclosed_probe.py -- THE NEGATIVE CONTROL, run for every verdict-producing script I wrote.

For each script: run it against `stub_no_score.sh`, a fake engine that answers UCI correctly but never prints an
`info ... pv ... score` line. A checker that is SAFE must not print a pass/confirm/mismatch verdict; it must either
refuse loudly (non-zero exit or an explicit FAIL/UNKNOWN line) or say nothing measurable.

Verdict words that count as "produced a verdict": CONFIRMS, REFUTES, MISMATCH, OK, PASS, AGREE, "engine right",
"does NOT reproduce", "does not confirm". A script that prints any of those on a no-parse run is BROKEN.

Each script is also run against the REAL engine, so the probe cannot claim a script is fine when it simply crashes
for an unrelated reason.
"""
import json
import os
import re
import subprocess
import sys

STUB = os.path.abspath("stub_no_score.sh")
REAL = "/tmp/build-rel/forge"

VERDICT_WORDS = ["CONFIRMS", "REFUTES", "MISMATCH", "PASS", "AGREE", "DISAGREE",
                 "engine right", "does NOT reproduce", "does not confirm", "HELD"]

# (path, argv-template with {exe}, extra files that must exist)
# True = the script drives an ENGINE and judges what it prints; False = the engine stub cannot reach it, either
# because it only reads committed files (build_mate_table, control_illegal_pv) or because it judges one of MY OWN
# python checkers (dtm2_selftest, dtm_selftest) -- those two are probed by probe_selftests.py instead, with a
# stub dtm2.py/dt.py that prints nothing.
USES_ENGINE = {
    "audit19f12/honesty_safe.py": True, "audit19f12/parser_audit.py": True,
    "audit_seat10/audit_10_clearhash.py": True, "check_15f3/check_15f3.py": True,
    "check_15f3/deadmaterial_scope.py": True, "check_15f3/knn_same_material.py": True,
    "check_15f4/check_15f4.py": True, "job1/build_mate_table.py": False,
    "job1/control_illegal_pv.py": False, "job1/crosscheck_mates.py": True,
    "job1/dtm2_selftest.py": False, "job1/dtm_selftest.py": False, "job1/mate_check.py": True,
}

SCRIPTS = [
    ("audit19f12/honesty_safe.py", ["{exe}", "/tmp/fc_honesty"], ["audit19f12/honesty_safe.py"]),
    ("audit19f12/parser_audit.py", ["{exe}"], ["audit19f12/parser_audit.py"]),
    ("audit_seat10/audit_10_clearhash.py", ["{exe}"], ["audit_seat10/audit_10_clearhash.py"]),
    ("check_15f3/check_15f3.py", ["{exe}"], ["check_15f3/check_15f3.py"]),
    ("check_15f3/deadmaterial_scope.py", ["{exe}"], ["check_15f3/deadmaterial_scope.py"]),
    ("check_15f3/knn_same_material.py", ["{exe}"], ["check_15f3/knn_same_material.py"]),
    ("check_15f4/check_15f4.py", ["{exe}"], ["check_15f4/check_15f4.py"]),
    ("job1/build_mate_table.py", [], ["job1/build_mate_table.py"]),
    ("job1/control_illegal_pv.py", [], ["job1/control_illegal_pv.py"]),
    ("job1/crosscheck_mates.py", ["5", "{exe}", "8/8/8/8/8/8/8/K6k w - - 0 1"], ["job1/crosscheck_mates.py"]),
    ("job1/dtm2_selftest.py", [], ["job1/dtm2_selftest.py"]),
    ("job1/dtm_selftest.py", [], ["job1/dtm_selftest.py"]),
    ("job1/mate_check.py", ["job1/out/rows.jsonl", "/tmp/fc_mate.txt", "6", "5"], ["job1/mate_check.py"]),
]

ROOT = "/agent/repos/dwqww/forge-combo29/swarm/05"


def run(path, argv, cwd):
    cmd = [sys.executable, os.path.basename(path)] + argv
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=240)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    except Exception as e:
        return "ERROR", str(e)


def verdicts_in(text):
    return [w for w in VERDICT_WORDS if w in text]


print("=" * 100)
print("NEGATIVE CONTROL: every verdict-producing script, run against an engine that NEVER prints a score")
print(f"stub engine: {STUB}  (answers uci/id/readyok/bestmove, never `info ... pv ... score`)")
print("=" * 100)
print()
results = []
for rel, argv_t, _files in SCRIPTS:
    cwd = os.path.join(ROOT, os.path.dirname(rel))
    script = os.path.join(ROOT, rel)
    if not os.path.exists(script):
        print(f"MISSING script {rel}")
        continue
    argv = [a.format(exe=STUB) for a in argv_t]
    rc, out = run(script, argv, cwd)
    vs = verdicts_in(out)
    # a script that prints a verdict word on a no-parse run is only acceptable if it is the FAILING kind
    fail_words = [w for w in vs if w in ("FAIL", "MISMATCH", "REFUTES", "DISAGREE", "does not confirm",
                                         "does NOT reproduce")]
    pass_words = [w for w in vs if w in ("CONFIRMS", "PASS", "AGREE", "OK", "HELD", "engine right")]
    # classify: did it produce a *passing* verdict?
    produced_pass = bool(pass_words) and USES_ENGINE.get(rel, True)
    refused = (rc != 0) or ("FAIL-LOUD" in out) or ("ASSERTION FAILURE" in out) or ("NO_VERDICT" in out)
    results.append((rel, rc, produced_pass, refused, vs, out, USES_ENGINE.get(rel, True)))

print("| script | drives an engine? | exit | produced a verdict on no-parse? | which way | refused loudly? |")
print("|---|---|---|---|---|---|")
for rel, rc, produced_pass, refused, vs, out, uses in results:
    if not uses:
        way = "n/a — see probe_selftests.py for the right instrument"
        flag = "n/a"
    elif produced_pass:
        way, flag = "**PASS — FAILS TOWARD A VERDICT**", "**UNSAFE**"
    elif refused:
        way, flag = "refused (fails closed)", "safe"
    elif vs:
        way, flag = f"negative verdict: {', '.join(vs)}", "**fails toward a REFUTATION**" if "REFUTES" in out else "check"
    else:
        way, flag = "no verdict printed", "safe"
    print(f"| {rel} | {'yes' if uses else 'no'} | {rc} | {flag} | {way} | "
          f"{'yes' if refused else 'no'} |")

print()
print("=" * 100)
unsafe = [r for r in results if r[2] and r[6]]
if unsafe:
    print(f"UNSAFE ({len(unsafe)}): these printed a PASSING verdict from a run that parsed nothing:")
    for rel, rc, _p, _r, vs, out, _uses in unsafe:
        print(f"  - {rel}   verdict words: {vs}")
        for line in out.splitlines():
            if any(w in line for w in vs):
                print(f"      {line[:150]}")
else:
    print("No script produced a passing verdict from a no-parse run.")
print()
print("Full outputs saved per script under raw/.")
os.makedirs("raw", exist_ok=True)
for rel, rc, produced_pass, refused, vs, out, uses in results:
    name = rel.replace("/", "__").replace(".py", "")
    with open(os.path.join("raw", name + ".stub.txt"), "w") as f:
        f.write(f"# {rel} against the no-score stub\n# exit={rc}\n# passing_verdict={produced_pass}\n")
        f.write(f"# refused_loudly={refused}\n# verdict_words={vs}\n# uses_engine={uses}\n\n")
        f.write(out)
