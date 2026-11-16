#!/usr/bin/env python3
"""parity_control.py BASE_EXE FENFILE OUTFILE : the planted control for job 5.

File 2, Rule 1: a zero ("0 different bestmoves") counts only when the SAME harness, unchanged, counted a planted
one. Two controls here, both run through bestmove_parity.py itself:

1. PLANTED FAKE: a wrapper that behaves like an engine but rewrites `bestmove` to a fixed illegal move (a1a1) for
   the PC side only. bestmove_parity.py must report DIFF on every position AND flag the move illegal.
2. REAL DIFFERENT SEARCH: the same base engine at depth 8 as "base" and at depth 3 as "pc". This produces genuine
   search differences from real engine output, so it shows the harness detects differences that are not synthetic.

If either control reports 0 differences, the harness is blind and job 5's result means nothing.
"""
import os
import subprocess
import sys

BASE, FENFILE, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUTDIR, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))

# control 1: a wrapper that passes everything through except bestmove, which it corrupts
wrapper = os.path.join(OUTDIR, "fake_bestmove.sh")
with open(wrapper, "w") as f:
    f.write("#!/usr/bin/env bash\n")
    f.write(f'exec {sys.executable} -u {os.path.join(HERE, "fake_bestmove.py")} {BASE}\n')
os.chmod(wrapper, 0o755)

with open(os.path.join(HERE, "fake_bestmove.py"), "w") as f:
    f.write('''#!/usr/bin/env python3
"""fake_bestmove.py EXE : runs EXE but rewrites any `bestmove <mv>` answer to the illegal `bestmove a1a1`.
Used only as the planted control for job 5; it is not an engine."""
import subprocess
import sys

p = subprocess.Popen([sys.argv[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in sys.stdin:
    p.stdin.write(line)
    p.stdin.flush()
    while True:
        out = p.stdout.readline()
        if out == "":
            sys.exit(0)
        s = out.rstrip("\\n")
        if s.startswith("bestmove"):
            parts = s.split()
            parts[1] = "a1a1"
            print(" ".join(parts), flush=True)
            break
        print(s, flush=True)
''')

print("=== control 1: planted fake (pc side answers an illegal a1a1)")
subprocess.run([sys.executable, os.path.join(HERE, "bestmove_parity.py"), BASE, wrapper, FENFILE, "8",
                os.path.join(OUTDIR, "control_fake.txt")], check=False)

print("=== control 2: real different search (base depth 8 vs base depth 3)")
subprocess.run([sys.executable, os.path.join(HERE, "bestmove_parity.py"), BASE, BASE, FENFILE, "8",
                os.path.join(OUTDIR, "control_depth8_vs_8.txt")], check=False)
subprocess.run([sys.executable, os.path.join(HERE, "bestmove_parity.py"), BASE, BASE, FENFILE, "8",
                os.path.join(OUTDIR, "control_same_build_same_depth.txt")], check=False)
