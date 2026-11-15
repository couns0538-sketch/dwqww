#!/usr/bin/env python3
# Part C: parse `callgrind_annotate --show=<13 events>` function table (linear parse,
# no backtracking): CEst per function, category shares, top N functions.
import sys, re, collections

def cest(c):
    return c[0] + 10 * (c[3] + c[4] + c[5] + c[10] + c[12]) + 100 * (c[6] + c[7] + c[8])

COL = re.compile(r"\s*([\d,]+|\.)(?:\s*\([^)]*\))?\s*")

def parse_funcs(path):
    funcs = {}
    for raw in open(path, errors="replace"):
        if "annotated source:" in raw:
            break
        line = raw.rstrip("\n")
        if not line or "[" not in line or not line.rstrip().endswith("]"):
            continue
        body, _, _ = line.rpartition(" [")
        costs, pos = [], 0
        while len(costs) < 13:
            m = COL.match(body, pos)
            if not m:
                break
            try:
                costs.append(int(m.group(1).replace(",", "")) if m.group(1) != "." else 0)
            except ValueError:
                break
            pos = m.end()
        rest = body[pos:].strip()
        m2 = re.match(r"^([A-Za-z0-9_./?][^:]*):(\S.*)$", rest)
        if not costs or not m2:
            continue
        costs += [0] * (13 - len(costs))
        funcs[m2.group(1) + ":" + m2.group(2)] = costs
    return funcs

def category(name):
    n = name.lower()
    if "nnue" in n or "accumulator" in n:
        return "evaluation (net)"
    if "see_ge" in n:
        return "SEE"
    if "evaluate" in n or "eval" in n or "correction" in n or "psqt" in n or "material_key" in n:
        return "evaluation (other)"
    if "generate_pseudo_legal" in n or "attacks::" in n or "is_legal" in n or "gives_check" in n or "magics" in n or "bitboard" in n:
        return "move generation"
    if "movepicker" in n or "pick_best" in n or "sort" in n or "scored" in n:
        return "move picker/sorting"
    if "make_move" in n or "unmake" in n:
        return "make/unmake"
    if "::tt" in n or "transposition" in n or "probe" in n or "sharedsearchstate" in n or ".store" in n:
        return "TT probe/store"
    if "history" in n or "quiet_stats" in n or "capture_stats" in n or "continuation" in n or "threat" in n or "apply_history" in n:
        return "history reads/updates"
    return "everything else"

if __name__ == "__main__":
    funcs = parse_funcs(sys.argv[1])
    total = sum(cest(c) for c in funcs.values())
    shares = collections.defaultdict(int)
    for k, c in funcs.items():
        shares[category(k)] += cest(c)
    print(f"TOTAL CEst {total}")
    for cat, v in sorted(shares.items(), key=lambda x: -x[1]):
        print(f"{100*v/total:6.2f}%  {cat}")
    print("--- top functions ---")
    rows = sorted(((cest(c), k) for k, c in funcs.items()), reverse=True)[: int(sys.argv[2])]
    for v, k in rows:
        print(f"{v:13d} {100*v/total:5.2f}% {category(k):22s} {k[:100]}")
