"""Cross-check final receipts, cutoff release and forecast without playing any games."""
import json,math,time,subprocess,sys
from pathlib import Path
from common29 import *
from plain29 import measure
base=Path(__file__).resolve().parent;work=base.parent;root=work/'games/blocks';book=work.parent/'job27work/input/L27.epd';final=base/'final'
while not (final/'independent.json').is_file():time.sleep(1)
s=json.loads((final/'independent.json').read_text());measure(s,root,book.read_text().splitlines(),final)
terms=[];n=0
def cont(a,b,z):return a<=z<=b
for name,(a,b) in {'D1':(25,140),'D2':(40,170),'E':(-45,25)}.items():
    x=s['arms'][name]['elo_lower_upper'][0];terms.append((name,a,b,x,cont(a,b,x)))
m=s['pooled_2000']['all']['mean_n'];blocks=s['blocks_complete_by_minute40'];main=len([b for b in s['block_ids_by_minute40'] if b<=9])
terms.extend([('softnodes_2000_mean',2800,4400,m,cont(2800,4400,m)),('all_blocks_by40',14,18,blocks,cont(14,18,blocks)),('primary_blocks_by40',8,9,main,cont(8,9,main))])
write_table(final/'prediction-independent.tsv',['measure','low','high','observed','inside'],terms)
for a,v in s['arms'].items():
    counts=[0]*5;outcomes=Counter();phase='main' if a in ('D1','D2','E') else 'optional'
    for block in s['complete_by_phase'][phase]:
        data=table(root/f'block{block:03d}'/a/'games.tsv');byopen=defaultdict(list)
        for g in data:
            points=1 if g['result']=='1/2-1/2' else 2 if (g['result']=='1-0')==(g['white']=='A') else 0
            outcomes[points]+=1;byopen[int(g['opening'])].append(points)
        for k,points in byopen.items():assert len(points)==2;counts[sum(points)]+=1
    assert counts==v['penta'] and [outcomes[2],outcomes[0],outcomes[1]]==v['A_WLD']
    n=sum(counts);p=sum(i*c for i,c in enumerate(counts))/(4*n);var=sum(c*(i/4-p)**2 for i,c in enumerate(counts))/n
    e=1.9599639845400536*math.sqrt(var/n)
    cv=lambda x:400*math.log10(x/(1-x));val=cv(p);w=(cv(p+e)-cv(p-e))/2
    assert all(abs(x-y)<1e-8 for x,y in zip((val,val-w,val+w),v['elo_lower_upper']))
(final/'pentanomial-check.txt').write_text(f'Independent direct recount from game results reproduced all W/L/D, all five opening-pair bins and all Elo/95% endpoints to 1e-8 across {len(s["arms"])} matches.\n')
latest=time.time()+150
while time.time()<latest:
    r=subprocess.run([sys.executable,'-B',str(base/'compare29.py'),str(final),str(work/'thresholds')],capture_output=True,text=True)
    if r.returncode==0:
        (final/'threshold-agreement.txt').write_text(r.stdout);print(r.stdout,flush=True);break
    time.sleep(2)
print('Independent final checks finished.',flush=True)
