"""Independently recover the PC check rows from original game protocol, then replay every gate to its ending."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from replay28 import check, replay_game, table, table_out

FIRST = {
    'a': ['1 21600 d2d4','2 39366 g8f6','3 23305 c2c4'],
    'b': ['1 28565 d2d4','2 39366 g8f6','3 34511 c2c4'],
    'c': ['1 28565 d2d4','2 95535 c7c5','3 18811 d4d5'],
}
K28 = {
    1: ('f49482fe2b9738aa',470764,'a'),
    2: ('749f902e91070fc2',507873,'b'),
    3: ('f7dc1451fef2f337',583536,'b'),
    4: ('af5f929dd8c03cc2',551293,'c'),
    5: ('fb0a79e5c1ffcd06',433827,'a'),
    6: ('749f902e91070fc2',507873,'b'),
}
C28 = {3: ('492d271d43b7ce03',485583,None)}
HISTORICAL = {1: 1, 2: 4, 6: 4}
CLOCKS = {3:(3290,4084), 5:(4661,4211)}


def gate(root,stage,old,out):
    source=root/stage
    expected=K28 if stage=='K28' else C28
    given=table(source/'games.tsv')
    check(sorted(int(x['game']) for x in given)==sorted(expected),(stage,'game membership'))
    claims=[];processes=set();clock_rows=[]
    for rec in sorted(given,key=lambda x:int(x['game'])):
        i=int(rec['game'])
        g=replay_game(source,rec,stage,[])
        for process in g['processes']:
            check(tuple(process) not in processes,(stage,i,'reused process'))
            processes.add(tuple(process))
        rows=[f'{j} {n} {move}' for j,(move,n) in enumerate(g['seq'][:20],1)]
        raw=('\n'.join(rows)+'\n').encode()
        check(raw==(source/f'first20-g{i:04d}.txt').read_bytes(),(stage,i,'saved first20 mismatch'))
        h=sha256(raw).hexdigest()[:16];ns=sum(n for _,n in g['seq'][:20]);eh,en,key=expected[i]
        check(len(rows)==20 and (h,ns)==(eh,en),(stage,i,h,ns,eh,en))
        if key:check(rows[:3]==FIRST[key],(stage,i,'first three',rows[:3],FIRST[key]))
        hist=None;diff=None
        if stage=='K28':
            if i in HISTORICAL:
                j=HISTORICAL[i]
                check(raw==(old/f'first20-g{j:04d}.txt').read_bytes(),(stage,i,'old byte mismatch',j))
                hist=j
            if i==2:
                check(raw!=(old/'first20-g0002.txt').read_bytes(),(stage,i,'profile failed to change rows'))
                diff=2
            if i in CLOCKS:
                ts=table(source/f'g{i:04d}/searches.tsv')
                actual=(int(ts[18]['clock_after']),int(ts[19]['clock_after']))
                check((ts[18]['side'],ts[19]['side'])==('W','B') and actual==CLOCKS[i],(stage,i,'clocks',actual,CLOCKS[i]))
                clock_rows.append(dict(game=i,ply19_white=actual[0],ply20_black=actual[1],known=list(CLOCKS[i])))
        else:
            check(h!=K28[3][0] and raw!=(root/'K28/first20-g0003.txt').read_bytes(),(stage,'control equality'))
        claims.append(dict(game=i,opening=g['opening'],rows=len(rows),sha16=h,node_sum=ns,first3=rows[:3],known_sha16=eh,known_sum=en,
                           historical_K27_equal_game=hist,historical_K27_unequal_game=diff,whole_result=g['result'],ending=g['ending'],plies=g['plies'],
                           white_clock=g['clocks']['W'],black_clock=g['clocks']['B'],whole_searches=sum(g['count'].values())))
    table_out(out/(stage+'-independent.tsv'),['game','pair','rows','sha16','sum_N','expected_sha16','expected_N','result','ending','applied_plies','end_W','end_B'],
              [(x['game'],x['opening'],x['rows'],x['sha16'],x['node_sum'],x['known_sha16'],x['known_sum'],x['whole_result'],x['ending'],x['plies'],x['white_clock'],x['black_clock']) for x in claims])
    info=dict(stage=stage,passes=True,games=claims,processes=len(processes),clock_checks=clock_rows)
    (out/(stage+'-independent.json')).write_text(json.dumps(info,indent=2)+'\n')
    print(stage,'PASS',[(x['sha16'],x['node_sum']) for x in claims],clock_rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('gate_root',type=Path);p.add_argument('stage',choices=['K28','C28']);p.add_argument('historical_K27',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();gate(a.gate_root,a.stage,a.historical_K27,a.out)
