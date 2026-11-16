#!/usr/bin/env python3
"""validate_checkers.py -- prove my checkers FAIL LOUDLY when the line they parse is absent.

Seat 19's warning: a parser that finds no number can produce NaN/None, and a comparison of
None with None prints "CONFIRMS". So every checker must be run once against an engine that
PRINTS NOTHING, and once against an engine that prints a line in the wrong FORMAT, and both
times it must refuse to produce a verdict.

The stub engines are tiny shell/python scripts written here (text, committed):
  stub_silent   : reads stdin, prints nothing, exits 0
  stub_echo     : prints "uciok"/"readyok" but never a score/bestmove line
  stub_nonsense : prints "readyok" and an info line WITHOUT the fields we parse

usage: validate_checkers.py OUTDIR
"""
import json
import os
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SWARM = os.path.dirname(HERE)   # forge-combo29/swarm/30 (the checkers live in its subfolders)
STUBS = {
    "stub_silent": "#!/bin/sh\ncat > /dev/null\nexit 0\n",
    "stub_echo": textwrap.dedent("""\
        #!/usr/bin/env python3
        import sys
        for line in sys.stdin:
            c = line.strip()
            if c == "uci":
                print("id name STUB echo"); print("uciok"); sys.stdout.flush()
            elif c == "isready":
                print("readyok"); sys.stdout.flush()
            elif c == "quit":
                break
        """),
    "stub_nonsense": textwrap.dedent("""\
        #!/usr/bin/env python3
        import sys
        for line in sys.stdin:
            c = line.strip()
            if c == "uci":
                print("id name STUB nonsense"); print("uciok"); sys.stdout.flush()
            elif c == "isready":
                print("readyok"); sys.stdout.flush()
            elif c.startswith("go"):
                print("info depth 1 pv")
                print("bestmove")
                sys.stdout.flush()
            elif c == "eval":
                print("evaluation unavailable")
                sys.stdout.flush()
            elif c == "quit":
                break
        """),
}

CHECKS = [
    ("check1 (halfmove mate)", ["check1/check_s01f5.py", "{exe}", "{out}"]),
    ("check2 (fifty-move horizon)", ["check2/check_s05f3.py", "{exe}", "{out}"]),
    ("check3 (setoption)", ["check3/check_s11f8.py", "{exe}", "{out}"]),
]


def main():
    outdir = os.path.join(HERE, sys.argv[1])   # absolute: the checkers run from SWARM
    os.makedirs(outdir, exist_ok=True)
    stubpaths = {}
    for name, body in STUBS.items():
        p = os.path.join(outdir, name)
        with open(p, "w") as f:
            f.write(body)
        os.chmod(p, 0o755)
        stubpaths[name] = p

    report = []
    for label, tmpl in CHECKS:
        for stub, path in stubpaths.items():
            out = os.path.join(outdir, "out_%s_%s" % (
                os.path.basename(tmpl[0]).replace(".py", ""), stub))
            cmd = [sys.executable if tmpl[0].endswith(".py") else "bash"] + [
                t.format(exe=path, out=out) for t in tmpl]
            cmd = [sys.executable] + [t.format(exe=path, out=out) for t in tmpl]
            try:
                r = subprocess.run(cmd, cwd=SWARM, capture_output=True, text=True, timeout=180)
                rc, out_txt = r.returncode, (r.stdout or "") + (r.stderr or "")
            except subprocess.TimeoutExpired:
                rc, out_txt = "TIMEOUT", ""
            verdictish = [w for w in ("CONFIRM", "REFUTE", "changed something: True",
                                      "changed_vs_baseline", "ALL FOUR MATCH") if w in out_txt]
            actually_ran = (rc != 2) and ("can't open file" not in out_txt) \
                and ("Traceback" not in out_txt.split("\n")[0])
            entry = {"check": label, "stub": stub, "exit": rc,
                     "actually_ran": actually_ran,
                     "printed_a_verdict": bool(verdictish),
                     "verdict_words": verdictish,
                     "output_head": out_txt[:400]}
            report.append(entry)
            print("%-30s %-14s exit=%-8s verdict_words=%s" % (
                label, stub, rc, verdictish or "none"))

    with open(os.path.join(outdir, "validation.json"), "w") as f:
        json.dump(report, f, indent=1)
    notrun = [e for e in report if not e["actually_ran"]]
    print()
    if notrun:
        print("FAIL: these runs did not execute the checker at all (a pass would be meaningless):")
        for e in notrun:
            print("  ", e["check"], e["stub"], "exit", e["exit"])
        print()
    bad = [e for e in report if e["printed_a_verdict"]]
    print()
    if bad:
        print("FAIL: these runs printed something that reads like a verdict:")
        for e in bad:
            print("  ", e["check"], e["stub"], e["verdict_words"])
    elif notrun:
        print("FAIL: validation incomplete (see above).")
    else:
        print("PASS: all nine runs really executed, and none produced verdict-like output.")


if __name__ == "__main__":
    main()
