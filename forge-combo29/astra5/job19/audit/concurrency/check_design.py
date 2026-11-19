"""Compare source paths and independently reconstruct each scheduled setting vector."""
import ast, csv, hashlib, re, runpy, sys
from pathlib import Path

W=Path('/workspace/work'); J18=W/'astra5/forge-combo29/astra5/job18'; H=W/'j19match'; O=W/'j19review'
sys.path.insert(0,str(W/'j10fens/vendor'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tx(p):return p.read_text()
def funcs(source):
    return {node.name:node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef)}
def norm(n):return ast.dump(n,include_attributes=False)
def pin(src,key):
    found=[n for n in ast.walk(src) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id==key]
    assert len(found)==1
    return norm(found[0])

old=funcs(tx(J18/'driver/selfplay.py'))
new=funcs(tx(H/'selfplay.py'))
for name in ['random_opening','send','lines','until','configure','search']:
    assert norm(old[name])==norm(new[name]),name
for var in ['role','book_line']:
    assert pin(old['main'],var)==pin(new['main'],var)
md=runpy.run_path(str(H/'selfplay.py'),run_name='inspect_design')
assert md['HARD']>0
with (J18/'sets.txt').open() as f:
    inputs=list(csv.DictReader(f,delimiter='\t'))
with (W/'j19sets/edge-sets.tsv').open() as f:
    edges=list(csv.DictReader(f,delimiter='\t'))
offers={}
for name in ['r15d','kF']:
    pattern=r'^option name (\w+) type spin default (-?\d+) min (-?\d+) max (-?\d+)$'
    offers[name]={n:(int(lo),int(hi)) for n,default,lo,hi in re.findall(pattern,tx(J18/'step0'/name/'40-uci.txt'),re.M)}
    assert len(offers[name])==40
pc20 = dict(x[15:].rsplit(' value ',1) for x in tx(J18/'step0/pc20.txt').splitlines())
nn={'NNUEArchFile':str(W/'j7net/net768.nnue'),'NNUEArch':'true'}
def as_map(args):
    vec=md['live_settings'](*args)
    kv=dict(x[15:].rsplit(' value ',1) for x in vec)
    assert len(kv)==len(vec)
    return kv
starts={i['name']:i['start'] for i in inputs}
assert len(edges)==80
skips=[]
for arm in ['K19-1','K19-2','C19']:
    assert md['ARMS'][arm]==('r15d',3791,3792,250000,0,'F')
    kv=pc20|nn
    if arm=='C19': kv['LmrQuietBase']='60'
    assert kv==as_map([0,arm])
for b in ['r15d','kF']:
    for s,first,last,cap in [('D1',3793,3808,250000),('D2',3809,3812,1000000)]:
        arm=f'{s}-{b}'
        assert md['ARMS'][arm]==(b,first,last,cap,0,'F')
        assert pc20|nn==as_map([0,arm])
    for num,e in enumerate(edges,1):
        row=inputs[(num-1)//2]; bound='min' if num%2 else 'max'
        key=row['name']; start=int(row['start']); tab=int(row[bound])
        lo=max(range_[key][0] for range_ in offers.values())
        hi=min(range_[key][1] for range_ in offers.values())
        eff=min(hi,max(lo,tab))
        assert (e['name'],e['bound'],int(e['value']))==(key,bound,eff)
        assert (start==eff)==(e['status']=='start')
        arm=f'E{num:02}-{b}'; first=500001+10*(num-1)
        assert md['ARMS'][arm]==(b,first,first+4,2000,num,'R')
        if e['status']=='start':
            if b=='r15d': skips.append(num)
            continue
        assert pc20|starts|{key:str(eff)}|nn==as_map([num,arm]),arm
for arm in md['ARMS']:
    assert md['slot_count'](arm)==1
stage=tx(H/'stage.py')
assert 'fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)' in stage
assert "for build in ('r15d','kF')" in stage
assert 'exits=[p.wait() for p in children]' in stage
assert "subprocess.Popen([sys.executable,'-B',str(ROOT/'arm.py')" in stage
arm=tx(H/'arm.py')
assert 'for slot in range(1,slot_count(arm)+1):' in arm
out=[
'Job 19 controller and source review.',
f'Actual inputs: selfplay.py SHA-256 {sha(H/"selfplay.py")}; stage.py {sha(H/"stage.py")}; arm.py {sha(H/"arm.py")}.',
'Compared Python abstract syntax trees of job 18 and 19 for the random-opening generator, send/receive, refusal checking, configuration, search, engine role startup loop and entire per-game loop. These portions match exactly.',
'Driver R retains one engine playing both colors for an ascending edge-seed range. The total cap of 300 includes the eight random opening plies. Searched rows normally start at absolute ply 8 and end at most at 299.',
'Driver F retains separate and persistent white and black processes. Only the moving process searches, with one-based plies after the book FEN and a cap of 300 searched plies. Both drivers use the node count on the last info line, or NA when there is no info line.',
'Each build uses one slot and a slot plays one game at a time. The measured stage controller takes a nonblocking exclusive lock, launches one arm of each build, waits for both to finish and then compares. Capacity is two simultaneous games across builds. K19 repeats and C19 run in sequence.',
'Checked every declared arm and effective value map. K19 and C19 target book lines 3791–3792 at 250,000 hard nodes; only C19 changes LmrQuietBase to 60. D1 uses lines 3793–3808 at 250,000 hard nodes. D2 uses lines 3809–3812 at 1,000,000 hard nodes.',
'Each runnable edge uses softnodes 2000 over five consecutive seeds from 500001 + 10(e−1). Checked all 80 rows against the 40 job 18 inputs and both executables’ option bounds. Each active edge changes exactly one of the 40 start values and preserves PC20 switches, net768, Threads 1 and Hash 16.',
f'{len(edges)-len(skips)} runnable edges and {len(skips)} starts: {", ".join(f"E{n:02}" for n in skips)}.',
'Raw game and worker intervals must still establish actual concurrency over completed work; see concurrency.txt for the observed result.'
]
(O/'driver-review.txt').write_text('\n'.join(out)+'\n')
print('\n'.join(out[:3]))
