"""Measure the actual footer of the fixed-node side, separate from the budget and finished-depth n."""
from common29 import *
import argparse
def measure(score,blocks,book,out):
    ids=score['complete_by_phase']['main'];rows=[];nv=[];last=[];examples=[];joint=Counter();depths=Counter();scanned=0
    for k in ids:
        p=blocks/f'block{k:03d}'/'E';games={int(r['game']):chess.Board(book[int(r['opening'])-1]) for r in table(p/'games.tsv')}
        for r in table(p/'searches.tsv'):
            i=int(r['game']);b=games[i]
            if r['side']=='A':
                scanned+=1;last.append(int(r['n']));a=r['soft_n']
                if a not in ('NA',''):
                    f=int(a);check(r['soft_line']==f'info string softnodes nodes {f}',r);nv.append(f)
                    if f!=4000:
                        kind,legal=r['score'].split()[0],b.legal_moves.count()
                        joint['forced' if legal==1 else 'multiple',kind]+=1;depths[r['depth']]+=1
                        rows.append((i,int(r['ply']),r['color'],r['bestmove'],int(r['n']),f,legal,r['score'],r['depth'],b.fen()))
                        if len(examples)<4:examples.append(rows[-1])
            b.push(chess.Move.from_uci(r['bestmove']))
    if not nv:return
    z=score['arms']['E'];cnt=z['players']['A']['searches'];check(scanned==cnt and sum(last)==z['players']['A']['n_total'],'E footer scope')
    hard_b=z['players']['B']['mean_n'];obs=sum(nv)/len(nv)
    info=dict(common_primary_blocks=ids,searches=cnt,footer_count=len(nv),missing_footer=cnt-len(nv),footer_total=sum(nv),
              mean_actual_footer=obs,min_actual_footer=min(nv),max_actual_footer=max(nv),below_4000=sum(f<4000 for f in nv),
              equal_4000=sum(f==4000 for f in nv),above_4000=sum(f>4000 for f in nv),nominal_limit=4000,mean_last_finished=sum(last)/len(last),
              mean_B_soft_2000=hard_b,actual_footer_ratio=obs/hard_b,nominal_limit_ratio=4000/hard_b,
              below_or_above_by_legal_count_and_score=[dict(legal_moves=k[0],score_type=k[1],searches=v) for k,v in sorted(joint.items())],
              non_nominal_last_depths=dict(depths),example_non_nominal=examples)
    dump(out/'E-footer.json',info);write_table(out/'E-footer-exceptions.tsv',['game','ply','color','move','last_finished_n','actual_footer_n','legal_moves_before','printed_score','completed_depth','fen_before'],rows)
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('blocks',type=Path);p.add_argument('book',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();s=measure(json.loads(a.snapshot.read_text()),a.blocks,a.book.read_text().splitlines(),a.out);print(s)
