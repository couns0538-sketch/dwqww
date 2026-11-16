#!/usr/bin/env python3
"""fhb_table.py -- print the job-3 depth-12 table from the rows files (no hand typing)."""
import sys
B={"O":9500069,"G":18466239}
META={0:"none",1:"reverse futility",2:"qsearch",3:"1+2",4:"main search end",5:"1+4",7:"all three"}
print("| value | bits | O sum | O ratio | O nodes-eq | O bm-eq | G sum | G ratio | G nodes-eq | G bm-eq |")
print("|---|---|---|---|---|---|---|---|---|---|")
def ln(p):
    return [(x.strip()) for x in open(p) if not x.startswith('#') and x.strip()]
for v in (0,1,2,4,3,5,7):
    row=[]
    for st in ("O","G"):
        f="%s_S14_%s.rows"%(st,"none" if v==0 and st=="O" else ("none" if st=="G" and v==0 else "fhb%d"%v))
        if st=="G" and v in (3,5): row.append(None); continue
        a={int(x[0]):(x[1],x[2]) for x in (l.split('|') for l in ln(f))}
        b={int(x[0]):(x[1],x[2]) for x in (l.split('|') for l in ln("%s_S14_none.rows"%st))}
        s=sum(int(k[0]) for k in a.values())
        ne=sum(1 for i in a if i in b and a[i][0]==b[i][0])
        be=sum(1 for i in a if i in b and a[i][1]==b[i][1])
        row.append((s,s/B[st],ne,be,len(a)))
    def cell(c):
        return "— | — | — | — |" if c is None else "%d | %.4f | %d of %d | %d of %d" % (c[0],c[1],c[2],c[4],c[3],c[4])
    print("| %d | %s | %s | %s |" % (v, META[v], cell(row[0]), cell(row[1])))
