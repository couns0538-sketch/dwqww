#!/usr/bin/env python3
"""R3-1 harness self-test: runs opus_selfplay_check.py against fault_proxy.py (a real engine behind a proxy that
breaks the protocol once) for every fault, and checks that the harness reports the injected fault with the
expected error type and a non-zero exit status, and that the clean control (fault "none") gives 0 errors, exit 0.

usage: selftest_faults.py --engine EXE --out DIR [--harness opus_selfplay_check.py] [--epd forge-10000.epd]
                          [--only f1,f2] [--games 2]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECT = {   # fault -> error type the harness must report (None: clean control)
    "none": None,
    "illegal_bestmove": "illegal_bestmove",
    "illegal_ponder": "illegal_ponder",
    "double_bestmove": "extra_bestmove",
    "late_double": "extra_bestmove",
    "unsolicited": "extra_bestmove",
    "early_infinite": "bestmove_before_stop",
    "hang": "timeout_bestmove",
    "crash": "crash",
    "exit_code": "bad_exit_code",
    "bad_info": "malformed_info",
    "illegal_pv": "illegal_pv",
    "illegal_currmove": "illegal_currmove",
    "stderr": "stderr_output",
    "no_readyok": "timeout_readyok",
    "error_string": "error_info_string",
    "option_missing": "option_not_advertised",
    "reject_move": "engine_rejected_move",
    "late_info": "late_search_output",
    "expect_missing": "config_error",   # proxy fault "none" + --expect of a line the engine never prints
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--harness", default=os.path.join(HERE, "opus_selfplay_check.py"))
    ap.add_argument("--epd", default=os.path.join(HERE, "..", "..", "tools", "openings", "forge-10000.epd"))
    ap.add_argument("--only", default="")
    ap.add_argument("--games", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    faults = [f for f in EXPECT if not a.only or f in a.only.split(",")]
    results, failures = [], 0
    for fault in faults:
        name = f"st_{fault}"
        proxy_fault = "none" if fault == "expect_missing" else fault
        cmd = [sys.executable, "-I", "-B", a.harness, "--name", name, "--exe", os.path.join(HERE, "fault_proxy.py"),
               "--exe-arg", a.engine, "--exe-arg", proxy_fault, "--exe-arg", "10", "--games", str(a.games),
               "--parallel", "1", "--restart-every", "50", "--margin-ms", "2000", "--out-dir", a.out,
               "--epd", a.epd, "--seed", "7"]
        if fault == "option_missing":
            cmd += ["--opt", "CuckooRep=true"]
        if fault == "expect_missing":
            cmd += ["--expect=NoSuchFeature active"]
        t0 = time.time()
        with open(os.path.join(a.out, name + ".stdout.log"), "w", newline="\n", encoding="utf-8") as f:
            code = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
        with open(os.path.join(a.out, name + ".summary.json"), encoding="utf-8") as f:
            s = json.load(f)
        types = dict(s.get("errors_by_type", {}))
        for x in s.get("preflight_errors", []):
            types[x["type"]] = types.get(x["type"], 0) + 1
        want = EXPECT[fault]
        if want is None:
            ok = code == 0 and not types and s.get("errors") == 0
        else:
            ok = code != 0 and types.get(want, 0) > 0
        failures += not ok
        line = (f"{'PASS' if ok else 'FAIL'} {fault:18s} exit {code} expected {want} reported {types} "
                f"games {s.get('games')} ({time.time() - t0:.0f} s)")
        print(line, flush=True)
        results.append(dict(fault=fault, expected=want, exit_status=code, reported=types, ok=ok,
                            games=s.get("games"), seconds=round(time.time() - t0, 1)))
    with open(os.path.join(a.out, "selftest_summary.json"), "w", newline="\n", encoding="utf-8") as f:
        json.dump(dict(engine=a.engine, harness=a.harness, results=results, failures=failures), f, indent=1)
    print(f"{len(faults) - failures}/{len(faults)} faults handled as expected", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
