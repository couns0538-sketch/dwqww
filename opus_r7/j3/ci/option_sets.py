#!/usr/bin/env python3
"""R7 J3 CI helper: per option set, bench 13 nodes (native run) and the callgrind instruction total.
usage: option_sets.py <forge_exe> <prof_options.txt> <out_dir>
prof_options.txt: one set per line, `name|Option=value,Option2=value` (empty after | = all defaults);
lines starting with # are comments. The first set is the reference: every other set must give the same
bench 13 node count (exit 1 otherwise). Prints one line per set:
  <name> nodes <n> same_nodes <yes|no> instr <Ir> vs_ref <+-x.xx %>"""
import os
import re
import subprocess
import sys

exe, spec, out = sys.argv[1], sys.argv[2], sys.argv[3]
sets = []
for line in open(spec, encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, _, opts = line.partition("|")
    pairs = [o.split("=", 1) for o in opts.split(",") if o.strip()]
    sets.append((name.strip(), [(k.strip(), v.strip()) for k, v in pairs]))


def script(opts):
    lines = ["uci", "setoption name Hash value 16", "setoption name OwnBook value false"]
    lines += [f"setoption name {k} value {v}" for k, v in opts]
    lines += ["isready", "bench 13", "quit"]
    return "\n".join(lines) + "\n"


ok = True
ref_nodes = ref_ir = None
for name, opts in sets:
    native = subprocess.run([exe], input=script(opts), capture_output=True, text=True, timeout=600).stdout
    m = re.search(r"bench depth 13 nodes (\d+)", native)
    nodes = int(m.group(1)) if m else -1
    cg = os.path.join(out, f"callgrind_{name}.out")
    subprocess.run(["valgrind", "--tool=callgrind", f"--callgrind-out-file={cg}", exe], input=script(opts),
                   capture_output=True, text=True, timeout=3600)
    ir = -1
    for l in open(cg, encoding="utf-8", errors="replace"):
        if l.startswith("summary:") or l.startswith("totals:"):
            ir = int(l.split()[1])
    if ref_nodes is None:
        ref_nodes, ref_ir = nodes, ir
    same = nodes == ref_nodes and nodes > 0
    ok &= same
    rel = 100.0 * (ir - ref_ir) / ref_ir if ref_ir and ref_ir > 0 and ir > 0 else float("nan")
    print(f"{name} nodes {nodes} same_nodes {'yes' if same else 'no'} instr {ir} vs_ref {rel:+.2f} %", flush=True)
sys.exit(0 if ok else 1)
