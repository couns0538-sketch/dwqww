"""Rebuild each complete pairing from the stage PGNs, then account for a final incomplete set separately."""
from pathlib import Path
import csv
import json
import subprocess
import sys
from read_partial24 import read
from reconcile_games import load
import argparse

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('stage_directory',type=Path,help='Job 24 directory containing R1, R2, C24 and K1')
parser.add_argument('output_directory',type=Path,help='Directory for the derived TSV and JSON files')
args=parser.parse_args()
root=args.stage_directory
out=args.output_directory
out.mkdir(parents=True,exist_ok=True)
memo={}
allstats=[]; first={}
for stage in ['R1','R2','C24','K1']:
    stage_path=root/stage/'stage.tsv'
    if not stage_path.exists():
        continue
    counts={'stage':stage,'sets':0,'games':0,'plies':0,'wins':0,'losses':0,'draws':0,
            'different_games':0,'different_WLD':0,'different_results':0,'partial_games':0}
    per=[]
    with stage_path.open() as f: entries=list(csv.DictReader(f,delimiter='\t'))
    for r in entries:
        j=int(r['j'])
        if r['status']!='complete':
            part=read(root,stage,j)
            (out/f'{stage}-partial-j{j:03d}.json').write_text(json.dumps(part,indent=2)+'\n')
            counts['partial_games']=part['complete_games']
            for k,v in [('games','complete_games'),('plies','complete_plies'),('wins','wins'),('losses','losses'),('draws','draws'),('different_games','different_games')]:
                counts[k]+=part[v]
            continue
        games,wld=load(root/stage,j)
        if stage=='R1': memo[j]=(games,wld)
        base,base_wld=memo[j]
        different=outcome=0
        for i in range(1,17):
            a,b=base[i],games[i]
            assert (a.round,a.number,a.fen,a.white,a.black)==(b.round,b.number,b.fen,b.white,b.black)
            outcome+=a.result!=b.result
            if a.moves!=b.moves:
                different+=1
                if stage not in first:
                    k=0
                    while k<min(len(a.moves),len(b.moves)) and a.moves[k]==b.moves[k]: k+=1
                    first[stage]=dict(j=j,round=a.round,game=a.number,white=a.white,black=a.black,fen=a.fen,
                                      first_differing_move_from_book=k+1,R1=list(a.moves[:k+1]),test=list(b.moves[:k+1]))
        expected=[int(r[x]) for x in ['wins','losses','draws']]
        assert list(wld)==expected
        current=dict(sets=1,games=len(games),plies=sum(len(x.moves) for x in games.values()),wins=wld[0],losses=wld[1],draws=wld[2],different_games=different,different_WLD=int(wld!=base_wld),different_results=outcome)
        for k,v in current.items(): counts[k]+=v
        per.append(dict(j=j,**current))
    if per:
        with (out/(stage+'-sets.tsv')).open('w') as f:
            wr=csv.DictWriter(f,fieldnames=per[0],delimiter='\t',lineterminator='\n');wr.writeheader();wr.writerows(per)
    allstats.append(counts)
(out/'first-differences.json').write_text(json.dumps(first,indent=2)+'\n')
(out/'stages.json').write_text(json.dumps(allstats,indent=2)+'\n')
for row in allstats: print(row,flush=True)
