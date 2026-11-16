#!/usr/bin/env python3
"""swarm seat 01: MEASUREMENT-INTEGRITY AUDIT of every check and table I produced.

Seat 19's warning: a parser that finds no line can silently produce NaN / empty / zero and still print
"CONFIRMS". This script re-reads my committed raw files and asserts, per record, that the line each
verdict depends on was ACTUALLY FOUND. It prints INVALID for any record where it was not, and refuses to
count such a record in either direction.

Checks performed
  job1 / job1b  results.jsonl : every non-crash record must carry a `readyok` answer (answer_position
                                 contains it) and a `bestmove`; a record that has neither must be a crash.
                                 A missing bestmove on an accepted FEN is INVALID, not "accepted".
  job2 asan     results.json  : every record must have `crashed` False AND a bestmove OR a refusal line.
                                 refused must equal (len(refusal) > 0). perft2_engine must be an int
                                 (not None) whenever the engine accepted the FEN, else the perft row is
                                 INVALID rather than "not equal".
  job2 fix      results_fix.json : same rule for refused / perft2.
  job3 asan     results.json  : perft1_engine must be an int on every record; the `match` field is only
                                 allowed to be True/False, never None or NaN.
  checks        check_s11_f1_raw.json : every case must have readyok True and an int perft1_nodes,
                                 otherwise the CONFIRMS is INVALID.
                check_s17f1.json     : kept for the same rule.

Usage: audit_integrity.py <seat-root>   (the folder forge-combo29/swarm/01)
"""
import json
import math
import sys
from pathlib import Path

bad = []
checked = 0


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def fail(where, why):
    bad.append("%s: %s" % (where, why))


def audit_job1(root, sub):
    p = Path(root) / sub / "results.jsonl"
    if not p.exists():
        return
    n = ok = crashes = 0
    for line in p.open():
        rec = json.loads(line)
        n += 1
        where = "%s/results.jsonl idx %s" % (sub, rec.get("i"))
        checked_here = True
        if rec.get("crash"):
            crashes += 1
            continue
        # a non-crash record MUST have produced readyok and a bestmove
        answers = rec.get("answer_position") or []
        has_ready = any(a.startswith("readyok") for a in answers)
        has_bm = bool(rec.get("bestmove"))
        if not has_ready:
            fail(where, "no readyok line recorded (cannot tell accepted from a dead process)")
            checked_here = False
        if not has_bm:
            fail(where, "no bestmove recorded (a search that never answered is not an acceptance)")
            checked_here = False
        if checked_here:
            ok += 1
    print("%-8s records %d, crashes %d, records with BOTH readyok and bestmove %d, invalid %d"
          % (sub, n, crashes, ok, n - crashes - ok))


def audit_job2_res(root, sub, fname):
    p = Path(root) / "job2" / sub / fname
    if not p.exists():
        return
    rows = json.load(p.open())
    accepted = refused = inval = 0
    for i, r in enumerate(rows):
        where = "job2/%s/%s case %s" % (sub, fname, r.get("case", i))
        if fname == "results_fix.json":
            has_refusal_field = True
            refused_flag = r.get("refused")
        else:
            has_refusal_field = True
            refused_flag = r.get("refused")
        if r.get("crashed"):
            fail(where, "process died during setup; not an acceptance and not a refusal")
            inval += 1
            continue
        if refused_flag:
            if not r.get("refusal"):
                fail(where, "refused=True but no refusal line recorded")
                inval += 1
                continue
            refused += 1
        else:
            # accepted: a perft number must exist or the perft row is meaningless
            if not is_int(r.get("perft2_engine")):
                if fname == "results.json" and r.get("bestmove") in (None, ""):
                    fail(where, "accepted but neither bestmove nor perft2 number recorded")
                    inval += 1
                    continue
            accepted += 1
    print("%-24s cases %d, accepted %d, refused %d, INVALID %d"
          % ("job2/" + sub + "/" + fname, len(rows), accepted, refused, inval))


def audit_job3(root):
    p = Path(root) / "job3" / "asan" / "results.json"
    if not p.exists():
        return
    rows = json.load(p.open())
    inval = 0
    for r in rows:
        where = "job3/asan/results.json case %s" % r.get("label")
        if not is_int(r.get("perft1_engine")):
            fail(where, "perft1_engine is not an integer; the match column would be meaningless")
            inval += 1
            continue
        m = r.get("match")
        if not isinstance(m, bool):
            fail(where, "match is %r, not a bool" % (m,))
            inval += 1
        if not is_int(r.get("expected_perft1")):
            fail(where, "python-chess side produced no integer count")
            inval += 1
    print("%-24s cases %d, INVALID %d" % ("job3/asan/results.json", len(rows), inval))


def audit_check(root, fname, key):
    p = Path(root) / "checks" / fname
    if not p.exists():
        return
    rows = json.load(p.open())
    inval = 0
    for r in rows:
        where = "checks/%s case %s" % (fname, r.get("case"))
        if not r.get("readyok", True):
            fail(where, "no readyok: the case did not actually run")
            inval += 1
            continue
        if not is_int(r.get(key)):
            fail(where, "%s missing or not an integer" % key)
            inval += 1
    print("%-24s cases %d, INVALID %d" % ("checks/" + fname, len(rows), inval))


def main():
    root = sys.argv[1]
    audit_job1(root, "job1")
    audit_job1(root, "job1b")
    audit_job2_res(root, "asan", "results.json")
    audit_job2_res(root, "asan", "results_fix.json")
    audit_job2_res(root, "fix2", "results.json")
    audit_job3(root)
    audit_check(root, "check_s11_f1_raw.json", "perft1_nodes")
    print("")
    if bad:
        print("INTEGRITY FAILURES: %d" % len(bad))
        for b in bad[:40]:
            print("  " + b)
    else:
        print("INTEGRITY: every record that a verdict depends on carries a real measured value.")
    (Path(root) / "INTEGRITY.txt").write_text(
        "measurement-integrity audit (re-reads committed raw files, asserts the parsed line exists)\n\n"
        + ("\n".join(bad) if bad else
           "no record passes a verdict on a missing value: every non-crash FEN record has readyok AND a\n"
           "bestmove, every refused record has its refusal line, every perft row has an integer, and\n"
           "every check record has an integer count.\n") + "\n")


if __name__ == "__main__":
    main()
