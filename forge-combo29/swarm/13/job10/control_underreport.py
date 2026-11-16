#!/usr/bin/env python3
"""Rule-1 control: the under-report detector must catch a planted under-report.

The zero reported is "0 of 200 mate claims were under-reported". That counts only if the same
verdict function, unchanged, flags a claim whose PV does not deliver.
"""
import json, sys
sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location("ur","underreport.py")
# import only the helpers we need without running main()
src=open("underreport.py").read().split("def main(")[0]
ns={"__name__":"ur"}
exec(src, ns)
pv_mates_at=ns["pv_mates_at"]
judge=ns["judge"]

rows=json.load(open("out/underreport.json"))["rows"]
# pick a real delivered positive claim to mutate
# pick a claim that needs MORE than one move, so "claim too short" is a real under-report
real=[r for r in rows if r["claim"] is not None and r["claim"]>=2 and r["verdict"]=="delivered"][0]
fen=real["fen"]; pv=real["pv"]; claim=real["claim"]
print("real case:", fen, "claim mate", claim, "PV mates at", pv_mates_at(fen,pv))
print()

cases=[]
# P0: real claim must be delivered
cases.append(("P0 real claim","claim %d, real PV"%claim, judge(fen,{"mate":claim,"pv":pv})["verdict"],"delivered"))
# A: claim a SHORTER mate than the PV delivers -> must be flagged
d_real=pv_mates_at(fen,pv)
cases.append(("A claim too short","claim mate 1 (needs <=1 ply), real PV needs %s plies"%d_real,
              judge(fen,{"mate":1,"pv":pv})["verdict"],"UNDER_REPORTED_OR_WRONG"))
# B: PV truncated so it never mates -> flagged
cases.append(("B truncated PV","claim %d, PV cut to 1 ply (mates at %s)"%(claim,pv_mates_at(fen,pv[:1])),
              judge(fen,{"mate":claim,"pv":pv[:1]})["verdict"],"UNDER_REPORTED_OR_WRONG"))
# C: empty PV -> flagged
cases.append(("C empty PV","claim %d, no PV"%claim,
              judge(fen,{"mate":claim,"pv":[]})["verdict"],"UNDER_REPORTED_OR_WRONG"))
# D: PV with an illegal move -> flagged
badpv=list(pv); badpv[0]="a1a8"
cases.append(("D illegal PV move","claim %d, PV[0]=a1a8"%claim,
              judge(fen,{"mate":claim,"pv":badpv})["verdict"],"UNDER_REPORTED_OR_WRONG"))
# E: no mate claim at all is NOT an under-report
cases.append(("E cp score","no mate claim, cp 50", judge(fen,{"mate":None,"pv":pv})["verdict"],"no_mate_claim"))

ok=True
print("| plant | what it is | verdict | expected | result |")
print("|---|---|---|---|---|")
for name,desc,got,want in cases:
    good = got==want
    ok &= good
    print("| %s | %s | %s | %s | %s |"%(name,desc,got,want,"correct" if good else "WRONG"))
print()
print("Rule 1 verdict:", "every planted under-report is flagged and the real claim passes - the zero is a measurement" if ok else "FAILED")
sys.exit(0 if ok else 1)
