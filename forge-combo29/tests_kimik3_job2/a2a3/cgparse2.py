#!/usr/bin/env python3
# Parse callgrind.out (compressed IDs): per-(file,line) and per-function SELF costs.
# Skips callee cost lines (the line right after 'calls=').
import sys, collections

def parse(path):
    events = []
    totals = None
    fl_map, fn_map = {}, {}
    fl = fn = None
    lines = collections.defaultdict(lambda: [0] * 13)
    funcs = collections.defaultdict(lambda: [0] * 13)
    skip_next_cost = False
    for raw in open(path, errors="replace"):
        raw = raw.rstrip("\n")
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("events:"):
            events = raw.split()[1:]
            continue
        if raw.startswith("totals:") or raw.startswith("summary:"):
            kind, rest = raw.split(":", 1)
            if kind == "totals":
                totals = [int(x) for x in rest.split()]
            continue
        key = raw[:3]
        if key in ("fl=", "fn="):
            val = raw[3:]
            if val.startswith("("):
                close = val.index(")")
                ident = val[1:close]
                name = val[close + 1:].strip()
                if name:
                    (fl_map if key == "fl=" else fn_map)[ident] = name
                else:
                    name = (fl_map if key == "fl=" else fn_map).get(ident, "?id" + ident)
                if key == "fl=":
                    fl = name
                else:
                    fn = name
            else:
                if key == "fl=":
                    fl = val
                else:
                    fn = val
            continue
        if raw.startswith("calls="):
            skip_next_cost = True
            continue
        if raw[0].isdigit() or raw[0] in "*+":
            if skip_next_cost:
                skip_next_cost = False
                continue
            parts = raw.split()
            try:
                ln = int(parts[0].lstrip("*+"))
            except ValueError:
                ln = 0
            costs = []
            for x in parts[1:1 + 13]:
                try:
                    costs.append(int(x))
                except ValueError:
                    costs.append(0)
            costs += [0] * (13 - len(costs))
            if fl is not None and fn is not None:
                k = (fl, ln)
                lines[k] = [a + b for a, b in zip(lines[k], costs)]
                fk = (fl, fn)
                funcs[fk] = [a + b for a, b in zip(funcs[fk], costs)]
            continue
        # any other directive (ob=, cob=, cfi=, cfn=, positions:, etc.)
    return events, totals, lines, funcs

EVENTS = ["Ir", "Dr", "Dw", "I1mr", "D1mr", "D1mw", "ILmr", "DLmr", "DLmw", "Bc", "Bcm", "Bi", "Bim"]

def cest(costs):
    l1 = costs[3] + costs[4] + costs[5]
    ll = costs[6] + costs[7] + costs[8]
    mp = costs[10] + costs[12]
    return costs[0] + 10 * (l1 + mp) + 100 * ll

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "check":
        # parser total vs 'totals:' line
        ev, tot, lines, funcs = parse(sys.argv[2])
        s = [sum(c[i] for c in lines.values()) for i in range(13)]
        print("parsed Ir:", s[0], " file totals Ir:", tot[0] if tot else "?")
    elif mode == "linediff" or mode == "funcdiff":
        _, _, la, fa = parse(sys.argv[2])
        _, _, lb, fb = parse(sys.argv[3])
        ei = EVENTS.index(sys.argv[4])
        topn = int(sys.argv[5])
        srca = la if mode == "linediff" else fa
        srcb = lb if mode == "linediff" else fb
        keys = set(srca) | set(srcb)
        rows = []
        for k in keys:
            va, vb = srca.get(k, [0]*13)[ei], srcb.get(k, [0]*13)[ei]
            if va != vb:
                rows.append((va - vb, k, va, vb))
        rows.sort(reverse=True)
        for d, k, va, vb in rows[:topn]:
            print(f"{d:+14d} {k[0]}:{k[1]}  R1={va} R0={vb}" if mode == "linediff" else f"{d:+14d} {k[1]} [{k[0]}]  R1={va} R0={vb}")
    elif mode == "linecost":
        _, _, lines, _ = parse(sys.argv[2])
        ei = EVENTS.index(sys.argv[3])
        topn = int(sys.argv[4])
        rows = sorted(((c[ei], k) for k, c in lines.items()), reverse=True)[:topn]
        tot = sum(c[ei] for c in lines.values())
        for v, k in rows:
            print(f"{v:14d} {100*v/tot:5.2f}% {k[0]}:{k[1]}")
    elif mode == "funcest":
        _, _, _, funcs = parse(sys.argv[2])
        topn = int(sys.argv[3])
        rows = sorted(((cest(c), k) for k, c in funcs.items()), reverse=True)[:topn]
        tot = sum(cest(c) for c in funcs.values())
        for v, k in rows:
            print(f"{v:14d} {100*v/tot:5.2f}% {k[1]} [{k[0]}]")
    elif mode == "linecest":
        _, _, lines, _ = parse(sys.argv[2])
        topn = int(sys.argv[3])
        rows = sorted(((cest(c), k) for k, c in lines.items()), reverse=True)[:topn]
        tot = sum(cest(c) for c in lines.values())
        for v, k in rows:
            print(f"{v:14d} {100*v/tot:5.2f}% {k[0]}:{k[1]}")
