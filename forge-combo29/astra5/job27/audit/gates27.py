"""Independent PC digest and whole-game replay of K27/C27."""
import json
import sys
from hashlib import sha256
from pathlib import Path

from replay27 import replay_game, table, table_out

GOLD=[
 ('f49482fe2b9738aa',470764),('f0130049ccd2829f',592206),('965681ae07f6c314',539887),
 ('749f902e91070fc2',507873),('93caf8323c20a6ea',529836),('6d5378c21381a5a2',604702)]
FIRST=['1 21600 d2d4\n2 39366 g8f6\n3 23305 c2c4\n','1 28565 d2d4\n2 39366 g8f6\n3 34511 c2c4\n']
def run(root, stage):
    out=root.parent.parent/'audit';data=root/stage
    claims=[];table_rows=[];pids=set()
    recs=table(data/'games.tsv');assert {int(r['game']) for r in recs}==set(range(1,7 if stage=='K27' else 2))
    for r in sorted(recs,key=lambda q:int(q['game'])):
        i=int(r['game']);g=replay_game(data,r,stage,[])
        for p in g['processes']:
            assert tuple(p) not in pids;pids.add(tuple(p))
        raw=table(data/f'g{i:04d}/searches.tsv')
        rows=''.join(f"{j} {n} {move}\n" for j,(move,n) in enumerate(g['seq'][:20],1))
        count=len(g['seq'][:20]);h=sha256(rows.encode()).hexdigest()[:16];ns=sum(n for _,n in g['seq'][:20])
        exp,en=GOLD[i-1];first=''.join(rows.splitlines(keepends=True)[:3])
        if stage=='K27':
            assert count==20 and h==exp and ns==en and first==FIRST[(i-1)%2],(i,h,ns,first)
            if i==1:assert raw[18]['side']=='W' and raw[18]['clock_after']=='4434' and raw[19]['side']=='B' and raw[19]['clock_after']=='4070'
        else:assert h!=GOLD[0][0]
        table_rows.append((i,g['opening'],r['white'],count,h,ns,exp,en,g['result'],g['ending'],g['plies'],g['clocks']['W'],g['clocks']['B']))
        claims.append(dict(game=i,opening=g['opening'],rows=count,sha16=h,node_sum=ns,first3=first.strip().splitlines(),known_sha16=exp,known_sum=en,whole_result=g['result'],ending=g['ending'],plies=g['plies']))
    table_out(out/(stage+'-independent.tsv'),['game','pair','White','rows','SHA16','sum_N','K27_expected_SHA16','K27_expected_sum','game_result','ending','plies','final_W','final_B'],table_rows)
    info=dict(stage=stage,passes=True,games=claims,processes=len(pids),K27_clocks=[4434,4070] if stage=='K27' else None)
    (out/(stage+'-independent.json')).write_text(json.dumps(info,indent=2)+'\n')
    print(stage,'PASS',[(v['sha16'],v['node_sum']) for v in claims])

if __name__=='__main__':run(Path(sys.argv[1]),sys.argv[2])
