#!/usr/bin/env python
"""profile_eval_functions.py - JOB E: entry counts, from a PGO profile, of every function of the hand-crafted evaluator
and of the compiled-in network (own code).   profile_eval_functions.py <profile.profdata> <llvm bin dir>"""
import re
import subprocess
import sys

prof, lm = sys.argv[1], sys.argv[2]
show = subprocess.run([lm + "/llvm-profdata.exe", "show", "--all-functions", prof], capture_output=True, text=True).stdout
names, counts, name = [], [], None
for line in show.splitlines():
    m = re.match(r"^  (\S.*):$", line)
    if m:
        name = m.group(1)
        continue
    m = re.match(r"^\s+Function count: (\d+)", line)
    if m and name:
        names.append(name)
        counts.append(int(m.group(1)))
        name = None
dem = subprocess.run([lm + "/llvm-cxxfilt.exe"], input="\n".join(n.split(":")[-1] for n in names), capture_output=True, text=True).stdout.splitlines()
rows = list(zip(dem, counts))
print(f"profile {prof}: {len(rows)} functions")
for title, pat in (("hand-crafted evaluator (Evaluator::, evaluate_position, evaluate_traced)", r"Evaluator::|evaluate_position|evaluate_traced"),
                   ("compiled-in network (forge::nnue:: outside v3)", r"forge::nnue::(?!v3)"),
                   ("NNUE v3 (forge::nnue::v3:: and Worker::static_evaluate_v3)", r"nnue::v3|static_evaluate_v3")):
    sel = sorted([(k, d) for d, k in rows if re.search(pat, d)], key=lambda x: -x[0])
    print(f"\n{title}: {sum(1 for k, d in sel if k > 0)} of {len(sel)} functions entered")
    for k, d in sel:
        print(f"  {k:>10}  {d[:170]}")
