import sys, json
sys.path.insert(0,'.')
from mate_rich import run, pv_legal, PC20
kept=json.load(open(sys.argv[2]+"/pool2.json"))
BUDGETS=[("n20000","go nodes 20000"),("n50000","go nodes 50000"),("n250000","go nodes 250000")]
exe=sys.argv[1]; out=sys.argv[2]
rows=[]
for bname,go in BUDGETS:
    mates=0; trunc=0; det=[]
    for k in kept:
        r=run(exe,k["fen"],go)
        if r["mate"] is None: continue
        mates+=1
        n,legal,ismate=pv_legal(k["fen"],r["pv"] or [])
        need = 2*r["mate"]-1 if r["mate"]>0 else 2*abs(r["mate"])
        bad=(not legal) or (n!=need)
        if bad:
            trunc+=1
            det.append({"fen":k["fen"],"mate":r["mate"],"pv":n,"need":need,"legal":legal})
    rows.append({"budget":bname,"mates":mates,"truncated":trunc,"details":det})
    print(f"  {bname:8s}: {mates} mate scores, {trunc} truncated ({100.0*trunc/mates if mates else 0:.1f} %)")
    for d in det:
        print(f"      TRUNC {d['fen']} mate {d['mate']} pv {d['pv']} need {d['need']} legal {d['legal']}")
json.dump({"kept":len(kept),"rows":rows},open(out+"/measure2.json","w"),indent=1)
