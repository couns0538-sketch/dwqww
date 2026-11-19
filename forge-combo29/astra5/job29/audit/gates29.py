"""Verify whole-game raw search traces and the six frozen PC first-20 checks."""
from replay29 import *
import sys
K=[('513827072a8e2e63',87781,['1 4121 d2d4','2 2482 g7g6','3 5094 e2e4']),('2c998001ce3d0422',110606,['1 4121 d2d4','2 4815 e7e6','3 2218 b1c3']),('c742bd472d34db18',48366,['1 4121 d2d4','2 1420 d7d5','3 2811 c2c4']),('b82c3404ac8ecb28',48642,['1 1740 c2c4','2 3538 e7e5','3 2934 g2g3'])]
C=('9b811eee51b6b554',60481,['1 4121 d2d4','2 2482 g7g6','3 3465 e2e4'])
root=Path(sys.argv[1]);stage_name=root.name;out=Path(sys.argv[2]);receipts=table(root/'games.tsv')
expected=4 if stage_name=='K29' else 2;check(sorted(int(r['game']) for r in receipts)==list(range(1,expected+1)),root)
sigs=[];whole=[];ident=set()
for rec in sorted(receipts,key=lambda r:int(r['game'])):
    i=int(rec['game']);d=root/f'g{i:04d}';rows=table(d/'searches.tsv');g=replay(rec,rows,chess.STARTING_FEN,d)
    elem=json.loads((d/'engines.json').read_text())
    for c,e in elem.items():
        p=(e['pid'],int(e['start_ticks']));check(p not in ident and proc_options(e['options'])==OPTIONS,(d,c));ident.add(p)
    simple=[f"{r['ply']} {r['n']} {r['bestmove']}" for r in rows]
    first=simple[:20];raw=('\n'.join(first)+'\n').encode();h=sha(raw)[:16];total=sum(int(r['n']) for r in rows[:20]);kh,kt,kfirst=K[i-1] if stage_name=='K29' else C
    check((h,total,first[:3])==(kh,kt,kfirst),(stage_name,i,h,total,first[:3]))
    path=root/f'first20-g{i:04d}.txt'
    if path.is_file():check(raw==path.read_bytes(),(d,'first20 file'))
    whole.append([(r['n'],r['depth'],r['score'],r['bestmove'],r['go'],r['soft_n'],r['info_nodes']) for r in rows])
    sigs.append((i,int(rec['opening']),h,total,kh,kt,' / '.join(first[:3]),g['ending'],g['result'],g['plies']))
if stage_name=='C29':
    check(whole[0]==whole[1] and sigs[0][7:]==sigs[1][7:] and C[0] not in [x[0] for x in K],('C29 whole semantic traces',sigs))
write_table(out/(stage_name+'-independent.tsv'),['game','opening','sha16','sum_n','known_sha16','known_sum_n','first_three','ending','result','plies'],sigs)
dump(out/(stage_name+'-independent.json'),dict(stage=stage_name,passed=True,rows=sigs,distinct_processes=len(ident),whole_control_games_identical=stage_name=='C29' and whole[0]==whole[1]))
print(stage_name,sigs)
