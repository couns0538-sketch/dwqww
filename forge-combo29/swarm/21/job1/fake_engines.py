#!/usr/bin/env python3
"""fake_engines.py [FAKE_DIR] [OUTDIR]

Rule 1 of FABLE_TO_swarm_2: every ZERO needs a planted one, counted by the SAME harness.
This builds two fake engines (python scripts, text) and runs the real harness `run_fen.py`
against them:

  fake_a1a8.py    answers `bestmove a1a8` (illegal in any normal position) to every `go`
  fake_noready.py never answers `readyok` (a hang)

The harness must count them: fake_a1a8 -> illegal bestmoves; fake_noready -> hangs.
"""
import os
import stat
import subprocess
import sys

A1A8 = '''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w:
        continue
    if w[0] == "uci":
        print("id name fake-a1a8", flush=True)
        print("uciok", flush=True)
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        print("bestmove a1a8", flush=True)
'''

NOREADY = '''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w:
        continue
    if w[0] == "uci":
        print("id name fake-noready", flush=True)
        print("uciok", flush=True)
    elif w[0] == "go":
        print("bestmove a2a3", flush=True)
'''


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fakedir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "fakes")
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "out_fake")
    os.makedirs(fakedir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    paths = {}
    for name, body in (("fake_a1a8.py", A1A8), ("fake_noready.py", NOREADY)):
        p = os.path.join(fakedir, name)
        with open(p, "w") as fh:
            fh.write(body)
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
        paths[name] = p

    inp = os.path.join(outdir, "fake_input.tsv")
    with open(inp, "w") as fh:
        for i in range(1, 4):
            fh.write("%d\tF\tclean\tunmutated\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\t1\n" % i)

    results = []
    for name, exe in paths.items():
        label = name.replace(".py", "")
        out = os.path.join(outdir, "run_" + label)
        subprocess.run([sys.executable, os.path.join(here, "run_fen.py"), exe, inp, out, label],
                       check=False, timeout=180)
        summary = os.path.join(out, label + "_summary.txt")
        results.append((label, open(summary).read().strip() if os.path.exists(summary) else "NO SUMMARY"))

    with open(os.path.join(outdir, "summary.txt"), "w") as fh:
        for label, s in results:
            fh.write("---- %s ----\n%s\n" % (label, s))
    print(open(os.path.join(outdir, "summary.txt")).read())


if __name__ == "__main__":
    main()
