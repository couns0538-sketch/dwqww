import sys, json
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/07/job39')
from fifty_deep import search, with_counter
prev=json.load(open('/agent/repos/dwqww/forge-combo29/swarm/07/job38/raw/fifty_rate.json'))
targets=[0,4,7,10,11,13,17,5,8,15]
for i in targets:
    fen=prev[i]['fen']
    out=[]
    for d in (12,16,20,24):
        r=search("/agent/repos/base/forge-combo29/build-rel/forge", with_counter(fen,0), d)
        out.append(f"d{d}={r['score']}")
    print(f"#{i:>2} " + "  ".join(out) + f"   {fen[:44]}")
