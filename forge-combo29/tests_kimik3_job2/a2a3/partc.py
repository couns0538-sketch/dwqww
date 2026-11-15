import sys; sys.path.insert(0,'/tmp')
from cgraw import parse, parse_lines, cest
from cgshares2 import category
for tag, path in [("R0a","/tmp/results2/R0a.out"), ("R3","/tmp/results2/R3.out")]:
    funcs, official = parse(path)
    tot = sum(cest(c) for c in funcs.values())
    cats = {}
    for (fl, fn), c in funcs.items():
        k = category(fn + " " + (fl or ""))
        cats[k] = cats.get(k, 0) + cest(c)
    out = open(f"/tmp/results2/{tag}_shares.txt","w")
    out.write(f"# {tag} (baseline_src {'no option' if tag=='R0a' else 'BundlePreset B1'}, bench 13) raw-parse shares\n")
    out.write(f"TOTAL CEst {tot:,} (official summary CEst 8,877,249,048 R0a / 8,954,464,215 R3; parser loses exactly 2 Ir)\n")
    for k, v in sorted(cats.items(), key=lambda x:-x[1]):
        out.write(f"{v/tot*100:6.2f}%  {k}\n")
    out.write("--- top 25 functions by CEst (self) ---\n")
    rows = sorted(((cest(c), c[0], fl, fn) for (fl,fn),c in funcs.items()), reverse=True)[:25]
    for ce, ir, fl, fn in rows:
        out.write(f"{ce:>14,} ({ce/tot*100:5.2f}%) Ir={ir:>13,}  {fn}  [{fl}]\n")
    lines = parse_lines(path)
    ltot = sorted(((cest(c), c[0], fl, pos) for (fl,pos),c in lines.items()), reverse=True)[:25]
    out.write("--- top 25 source lines by CEst (self) ---\n")
    for ce, ir, fl, pos in ltot:
        out.write(f"{ce:>14,} ({ce/tot*100:5.2f}%) Ir={ir:>13,}  {fl}:{pos}\n")
    out.close()
    print(tag, "written")
