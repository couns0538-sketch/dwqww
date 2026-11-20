#!/usr/bin/env python3
"""Write HONESTY_B.txt and the four honesty .meta files from the raw bench/perft logs."""
import hashlib
import os
import sys

folder = sys.argv[1]
exe = sys.argv[2]
digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
name = ""
with open(os.path.join(folder, "uci_id_B.txt")) as handle:
    for line in handle:
        if line.startswith("id name "):
            name = line[len("id name "):].rstrip("\n")

def last_nodes(path, needle):
    found = None
    with open(path) as handle:
        for line in handle:
            if needle in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "nodes" and i + 1 < len(parts):
                        found = parts[i + 1]
    if found is None:
        raise SystemExit("no nodes in " + path)
    return found

rows = [
    ("bench 11", "bench11_B.txt", "info string bench depth 11", "312866"),
    ("bench 13", "bench13_B.txt", "info string bench depth 13", "862329"),
    ("bench 16", "bench16_B.txt", "info string bench depth 16", "3024920"),
    ("go perft 5", "perft5_B.txt", "nodes ", "4865609"),
]
out = []
out.append("exe " + exe)
out.append("sha256 " + digest)
out.append("id_name " + name)
out.append("options none")
out.append("check\texpected\tgot\tfile")
for label, filename, needle, expected in rows:
    got = last_nodes(os.path.join(folder, filename), "nodes")
    # perft file has a nodes count on every move line; the signature is the final total.
    if label.startswith("go perft"):
        got = None
        with open(os.path.join(folder, filename)) as handle:
            for line in handle:
                if line.startswith("nodes "):
                    got = line.split()[1]
        if got is None:
            raise SystemExit("no perft total")
    flag = "OK" if got == expected else "MISS"
    out.append(f"{label}\t{expected}\t{got}\t{flag}\t{filename}")
    meta = os.path.join(folder, filename + ".meta")
    with open(meta, "w") as handle:
        handle.write("exe " + exe + "\n")
        handle.write("sha256 " + digest + "\n")
        handle.write("id_name " + name + "\n")
        handle.write("options none\n")
        handle.write("command " + label + "\n")
text = "\n".join(out) + "\n"
sys.stdout.write(text)
with open(os.path.join(folder, "HONESTY_B.txt"), "w") as handle:
    handle.write(text)
