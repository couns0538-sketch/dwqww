"""Post-hoc detail for a finished scan: size and fullmove range of the holdout game groups whose positions occur in
training, rebuilt with the scanner's own functions (same group rule) and its saved hit bitmap and removal list.
Read-only on the data; prints a report. Usage:
  python -I -B real_run_group_detail.py <scan out dir> <pos dir> <text dir> forge_selfplay_013 forge_selfplay_014"""
import collections,gzip,importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True
import numpy as np
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('scan',here/'forge_sol_S16_overlap_scan.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
out,pos,txt=(pathlib.Path(a) for a in sys.argv[1:4]);stems=sys.argv[4:]
S.lower_priority('idle')
summ=json.loads((out/'forge_sol_S16_overlap_summary_20261027.json').read_text(encoding='utf-8'))
fm_all=[];res_all=[];pc_all=[];offs=[0]
for st in stems:
    sh=S.Shard(pos/f'{st}.pos');metas=sh.column('metas');scores=sh.column('scores')
    fm,_=S.parse_text(txt/f'{st}.txt',sh.n,metas,scores,10**9);pc=np.empty(sh.n,np.int16)
    for a in range(0,sh.n,500000):b=min(sh.n,a+500000);pc[a:b]=S.piece_counts(sh.read(a,b)[0])
    fm_all.append(fm);res_all.append(metas>>1);pc_all.append(pc);offs.append(offs[-1]+sh.n)
fm=np.concatenate(fm_all);res=np.concatenate(res_all);pc=np.concatenate(pc_all);n=len(fm)
hits=np.unpackbits(np.load(out/'forge_sol_S16_holdout_rows_in_training_bitmap_20261027.npy'),bitorder='little')[:n].astype(bool)
gid=np.concatenate([[0],np.cumsum(S.boundaries(fm,pc,res),dtype=np.int64)]);ng=int(gid[-1])+1
size=np.bincount(gid,minlength=ng);h=np.bincount(gid,weights=hits,minlength=ng).astype(np.int64)
assert ng==summ['games']['groups'] and int(hits.sum())==summ['holdout']['rows_whose_position_is_in_training'],'does not reproduce the scan'
def hist(v):
    edges=[(1,1),(2,2),(3,5),(6,10),(11,40),(41,100),(101,10**9)];return {f'{a}-{b if b<10**9 else "max"}':int(((v>=a)&(v<=b)).sum()) for a,b in edges}
full=np.flatnonzero(h==size);anyhit=np.flatnonzero(h>0)
print('groups',ng,'| with any training position',len(anyhit),'| fully in training',len(full))
print('size of fully-in-training groups (rows):',hist(size[full]))
print('size of partly-in-training groups (rows):',hist(size[np.flatnonzero((h>0)&(h<size))]))
start=np.searchsorted(gid,np.arange(ng))  # first global row of every group
print('fully-in-training groups: first fullmove',hist(fm[start[full]].astype(np.int64)),'| pieces at start',hist(pc[start[full]].astype(np.int64)))
# which training shards hold the positions of the largest fully-in-training groups
rm=[l.split(',') for l in gzip.open(out/'forge_sol_S16_removal_list_20261027.csv.gz','rt',encoding='utf-8').read().splitlines()[1:]]
where=collections.defaultdict(set)
for stem,row,reason,hs,hr,conf in rm:
    if reason=='holdout_position':where[offs[stems.index(hs)]+int(hr)].add(stem)
for g in sorted(full,key=lambda g:-size[g])[:5]:
    a=int(start[g]);b=a+int(size[g]);k=stems[int(np.searchsorted(offs,a,side='right'))-1]
    print(f'  largest fully-in-training group {g}: {size[g]} rows, holdout {k} rows {a-offs[stems.index(k)]}..{b-1-offs[stems.index(k)]}, fullmove {fm[a]}..{fm[b-1]}, pieces {pc[a]}..{pc[b-1]}, training stems {sorted(set().union(*[where[r] for r in range(a,b)]))}')
