#!/usr/bin/env python3
"""Compare our rebuild of seat 069 with exe B and with 069's own rows."""
from pathlib import Path
seat = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
d = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
d = Path(d) / "forge-combo29" / "grok" / seat
src = d / "partner_src"

def load(path):
    rows = []
    for line in Path(path).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((int(parts[0]), int(parts[1]), parts[2], parts[3]))
    return rows

def differ(a, b):
    n = 0
    for x, y in zip(a, b):
        if x[1] != y[1] or x[2] != y[2] or x[3] != y[3]:
            n += 1
    return n

expect = {
    "partner_h_bench11.txt": 312866,
    "partner_h_bench13.txt": 862329,
    "partner_h_bench16.txt": 3024920,
    "partner_h_perft5.txt": 4865609,
}
lines = []
ok = True
for name, want in expect.items():
    text = (d / name).read_text()
    nodes = None
    for line in text.splitlines():
        parts = line.replace(":", " ").split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                nodes = int(parts[i + 1])
    status = "PASS" if nodes == want else "FAIL"
    ok = ok and nodes == want
    lines.append(f"honesty {name} nodes {nodes} expected {want} {status}")
off = load(d / "partner_off_O.rows.tsv")
on = load(d / "partner_on_O.rows.tsv")
b = load(d / "B_O_d12.rows.tsv")
theirs = load(src / "P_on_O_d12.rows.tsv")
do = differ(off, b)
dn = differ(on, theirs)
lines.append(f"off_vs_B differ {do} of {len(off)} sum {sum(r[1] for r in off)} {'PASS' if do==0 else 'FAIL'}")
lines.append(f"on_vs_partner_rows differ {dn} of {len(on)} sum {sum(r[1] for r in on)} partner_sum {sum(r[1] for r in theirs)} {'PASS' if dn==0 else 'FAIL'}")
lines.append(f"on_vs_B differ {differ(on, b)} of {len(on)}")
lines.append("honesty_all " + ("PASS" if ok else "FAIL"))
text = "\n".join(lines) + "\n"
(d / "partner_compare.txt").write_text(text)
print(text, end="")
