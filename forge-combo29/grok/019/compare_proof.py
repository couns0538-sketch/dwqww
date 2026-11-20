#!/usr/bin/env python3
"""Compare depth-12 row files. Prints the proof lines."""
from pathlib import Path
S = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
d = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
d = Path(d) / "forge-combo29" / "grok" / S

def load(name):
    rows = []
    for line in (d / name).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, best, fen = line.split("\t", 3)
        rows.append((int(index), int(nodes), best, fen))
    return rows

def honesty(prefix):
    expect = {
        "bench11.txt": ("bench 11", 312866),
        "bench13.txt": ("bench 13", 862329),
        "bench16.txt": ("bench 16", 3024920),
        "perft5.txt": ("go perft 5", 4865609),
    }
    lines = []
    ok = True
    for name, (label, want) in expect.items():
        text = (d / f"{prefix}_{name}").read_text()
        nodes = None
        for line in text.splitlines():
            parts = line.replace(":", " ").split()
            if "nodes" in parts:
                i = parts.index("nodes")
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    nodes = int(parts[i + 1])
        status = "PASS" if nodes == want else "FAIL"
        ok = ok and nodes == want
        lines.append(f"{prefix} {label} nodes {nodes} expected {want} {status}")
    return lines, ok

def same(a, b):
    if len(a) != len(b):
        return 0, len(a), "length mismatch"
    differ = 0
    for x, y in zip(a, b):
        if x[1] != y[1] or x[2] != y[2] or x[3] != y[3]:
            differ += 1
    return differ, len(a), "ok"

lines = []
h, ok = honesty("honesty_p")
lines.extend(h)
Bo = load("B_O_d12.rows.tsv")
Bg = load("B_G_d12.rows.tsv")
Po = load("Poff_O_d12.rows.tsv")
Pg = load("Poff_G_d12.rows.tsv")
On = load("Pon_O_d12.rows.tsv")
do, no, _ = same(Po, Bo)
dg, ng, _ = same(Pg, Bg)
dn, nn, _ = same(On, Bo)
lines.append(f"off O differ {do} of {no} sum {sum(r[1] for r in Po)} {'PASS' if do==0 else 'FAIL'}")
lines.append(f"off G differ {dg} of {ng} sum {sum(r[1] for r in Pg)} {'PASS' if dg==0 else 'FAIL'}")
lines.append(f"on O differ {dn} of {nn} sum {sum(r[1] for r in On)}")
lines.append(f"on O first3 {On[0][1]} / {On[1][1]} / {On[2][1]}")
text = "\n".join(lines) + "\n"
(d / "PROOF_NODES.txt").write_text(text)
htext = "\n".join(h) + ("\nALL PASS\n" if ok else "\nSOME FAILED\n")
(d / "HONESTY_P.txt").write_text(htext)
print(text)
