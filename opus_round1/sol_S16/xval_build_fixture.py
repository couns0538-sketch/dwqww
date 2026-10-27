"""Build the S16 cross-validation fixture from REAL PC records (read-only) into a NEW directory.
Shards (chronological order a, b, c, d), each with aligned .pos/.hce/.txt copied row for row:
  fx_a_train   = forge_selfplay_015 rows [0, 50000)
  fx_b_holdout = forge_selfplay_013 rows [0, 100000)
  fx_c_train   = forge_selfplay_013 rows [100000, 150000)   (continues the holdout's last game: a real straddle)
  fx_d_train   = forge_selfplay_016 rows [0, 50000) + forge_selfplay_013 rows [1000, 1500)  (500 planted overlaps)
Usage: python -I -B xval_build_fixture.py <pos dir> <hce dir> <text dir> <NEW out dir>"""
import itertools,json,pathlib,sys
sys.dont_write_bytecode=True

def rows(pos,hce,txt,a,b):
    with open(pos,'rb') as f:
        head=f.read(16);n=int.from_bytes(head[8:16],'little');assert head[:4]==b'FPOS' and b<=n
        f.seek(16+32*a);boards=f.read(32*(b-a));f.seek(16+32*n+2*a);scores=f.read(2*(b-a));f.seek(16+34*n+a);metas=f.read(b-a)
    with open(hce,'rb') as f:
        head=f.read(16);assert head[:4]==b'FHCE' and int.from_bytes(head[8:16],'little')==n;f.seek(16+2*a);hces=f.read(2*(b-a))
    with open(txt,'r',encoding='utf-8',newline='') as f:lines=list(itertools.islice(f,a,b))
    assert len(lines)==b-a
    return [(boards[32*i:32*i+32],scores[2*i:2*i+2],metas[i:i+1],hces[2*i:2*i+2],lines[i]) for i in range(b-a)]

def write(out,stem,rs):
    n=len(rs)
    with open(out/f'{stem}.pos','xb') as f:
        f.write(b'FPOS'+(1).to_bytes(4,'little')+n.to_bytes(8,'little'))
        for k in (0,1,2):f.write(b''.join(r[k] for r in rs))
    with open(out/f'{stem}.hce','xb') as f:f.write(b'FHCE'+(1).to_bytes(4,'little')+n.to_bytes(8,'little')+b''.join(r[3] for r in rs))
    with open(out/f'{stem}.txt','x',encoding='utf-8',newline='') as f:f.writelines(r[4] for r in rs)

def main():
    pos,hce,txt,out=(pathlib.Path(x) for x in sys.argv[1:5]);out.mkdir(parents=True,exist_ok=False)
    src=lambda s:(pos/f'{s}.pos',hce/f'{s}.hce',txt/f'{s}.txt')
    plan={'fx_a_train':[('forge_selfplay_015',0,50000)],'fx_b_holdout':[('forge_selfplay_013',0,100000)],
          'fx_c_train':[('forge_selfplay_013',100000,150000)],'fx_d_train':[('forge_selfplay_016',0,50000),('forge_selfplay_013',1000,1500)]}
    for stem,parts in plan.items():write(out,stem,[r for s,a,b in parts for r in rows(*src(s),a,b)])
    (out/'text_map.json').write_text(json.dumps({s:f'{s}.txt' for s in plan}),encoding='utf-8')
    (out/'fixture_plan.json').write_text(json.dumps(plan,indent=1),encoding='utf-8');print(json.dumps(plan))
if __name__=='__main__':main()
