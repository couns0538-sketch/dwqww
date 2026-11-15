#!/usr/bin/env python3
# Raw .out parser: self cost per (file,function). Cost lines may start with
# +N / -N / * / N and may omit trailing zero events. The single cost line after
# a 'calls=' line is the callee's INCLUSIVE charge at that call site: skipped.
import sys, re, collections

EVENTS = ["Ir","Dr","Dw","I1mr","D1mr","D1mw","ILmr","DLmr","DLmw","Bc","Bcm","Bi","Bim"]
def cest(c): return c[0]+10*(c[3]+c[4]+c[5]+c[10]+c[12])+100*(c[6]+c[7]+c[8])
COST = re.compile(r"^(?:[+*-]?\d+|\*)\s")

def parse(path):
    funcs = collections.defaultdict(lambda: [0]*13)
    flmap = {}; fnmap = {}
    def resolve(val, table):
        m = re.match(r"^\((\d+)\)\s*(.*)$", val)
        if m:
            if m.group(2):
                table[m.group(1)] = m.group(2)
                return m.group(2)
            return table.get(m.group(1), val)
        return val
    fl = fn = None
    skip_next_cost = False
    official = None
    for line in open(path, errors="replace"):
        c0 = line[:1]
        if line.startswith("fl="):
            fl = resolve(line[3:].strip(), flmap)
        elif line.startswith("fn="):
            fn = resolve(line[3:].strip(), fnmap)
        elif line.startswith("cfl="):
            resolve(line[4:].strip(), flmap)
            skip_next_cost = True
        elif line.startswith("cfn="):
            resolve(line[4:].strip(), fnmap)
            skip_next_cost = True
        elif line.startswith(("cob=","calls=")):
            skip_next_cost = True
        elif COST.match(line):
            if skip_next_cost:
                skip_next_cost = False
                continue
            vals = []
            ok = True
            for tok in line.split()[1:]:
                try: vals.append(int(tok))
                except ValueError: ok = False; break
            if ok and fn is not None:
                vals += [0]*(13-len(vals))
                if len(vals) == 13:
                    acc = funcs[(fl, fn)]
                    for i, v in enumerate(vals): acc[i] += v
        elif line.startswith("summary:"):
            official = [int(x) for x in line.split()[1:]]
    return funcs, official

if __name__ == "__main__":
    funcs, official = parse(sys.argv[1])
    tot = [sum(c[i] for c in funcs.values()) for i in range(13)]
    print(f"functions: {len(funcs)}")
    ok = True
    for i, e in enumerate(EVENTS):
        mark = "OK" if tot[i] == official[i] else "MISMATCH"
        if tot[i] != official[i]: ok = False
        print(f"  {e:5s} parsed {tot[i]:>15,} official {official[i]:>15,} {mark}")
    print("VALIDATED" if ok else "FAILED")

def parse_lines(path):
    import collections, re as _re
    lines = collections.defaultdict(lambda: [0]*13)
    flmap = {}
    fl = None; skip = False; cur = 0
    for line in open(path, errors="replace"):
        if line.startswith("fl="):
            v = line[3:].strip()
            m = _re.match(r"^\((\d+)\)\s*(.*)$", v)
            if m:
                if m.group(2): flmap[m.group(1)] = m.group(2)
                fl = m.group(2) or flmap.get(m.group(1), v)
            else: fl = v
            cur = 0
        elif line.startswith(("cfl=","cfn=","cob=","calls=")): skip = True
        elif COST.match(line):
            pos = line.split()[0]
            if skip: skip = False; continue
            if pos == "*": pass
            elif pos.startswith("+"): cur += int(pos[1:])
            elif pos.startswith("-"): cur -= int(pos[1:])
            else: cur = int(pos)
            vals = []
            ok = True
            for tok in line.split()[1:]:
                try: vals.append(int(tok))
                except ValueError: ok = False; break
            if ok:
                vals += [0]*(13-len(vals))
                if len(vals) == 13:
                    acc = lines[(fl, cur)]
                    for i, v in enumerate(vals): acc[i] += v
    return lines
